"""Steer an open model along an honesty axis and watch it move on the WVS culture map.

The base map (scripts/wvs_map.py) places models among human societies on the two Inglehart-Welzel
axes. This script keeps that readout fixed and varies one thing: an activation steering vector,
applied at a range of doses, with several extraction methods compared at the SAME intervention
strength (iso-KL calibration, so a weak method is not just a small dose).

  base          c = 0
  +C honest     says what it believes is true even when unwelcome
  -C            says what will be well received even when it believes it is false

Per dose we save the coordinate, its bootstrap CI, the per-item positions, and the coherence
check. Per-item positions are saved so any leave-one-out holdout is a post-processing question:
if one item carries the whole move, that is lexical overlap with the persona, not a cultural move.

  uv run python scripts/wvs_steer_sweep.py --model Qwen/Qwen3-0.6B --methods mean_diff --smoke
  modal run --detach scripts/run_modal_wvs.py     # the real fan-out
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch
from loguru import logger
from transformers import AutoModelForCausalLM, AutoTokenizer

import steering_lite as sl
from steering_lite.data import make_persona_pairs, load_suffixes

from moralmaps.iw_axes import X_AXIS, Y_AXIS, positiveness, resolve_items
from moralmaps.read import read_items, resolve_answer_ids
from moralmaps.wvs import build_instruments, load_wvs_all, model_coord_ci

# Mirrored poles in one domain (what you say about what you believe), no negation-only pole, both
# enactable. Written this way to avoid extracting "blunt vs polite", which is the style direction
# the bluntness/sycophancy pairs in vjp-steering pick up.
HONESTY_PAIR = (
    "someone who says what they believe is true, even when it is unwelcome",
    "someone who says what will be well received, even when they believe it is false",
)
HONESTY_TEMPLATE = "You think and act like {persona}."

METHODS = {
    "mean_diff": sl.MeanDiffC,
    "pca": sl.PCAC,
    "vjp_delta": sl.VjpDeltaC,
    "random": sl.RandomC,     # control: the null region a direction must beat to mean anything
}


def calib_prompts(n: int = 8, seed: int = 0) -> list[str]:
    """Distinct user messages from the branching-suffix pool, the iso-KL calibration set."""
    import random
    rng = random.Random(seed)
    entries = load_suffixes(thinking=True)
    rng.shuffle(entries)
    seen, out = set(), []
    for e in entries:
        if e["user_msg"] in seen:
            continue
        seen.add(e["user_msg"])
        out.append(e["user_msg"])
        if len(out) >= n:
            break
    return out


def read_coords(model, tok, instrs, meta, resolved, rng, *, think: int, batch_size: int,
                n_samples: int, temperature: float) -> dict:
    """One WVS readout -> coordinate, bootstrap CI, per-item positions, coherence."""
    rows = []
    for instr in instrs:
        rows += read_items(model, tok, instr, instr.items,
                           resolve_answer_ids(tok, instr.answer_space),
                           max_think_tokens=think, batch_size=batch_size,
                           n_samples=n_samples, temperature=temperature)
    psamples, pmass = {}, {}
    for r in rows:
        n = meta[r["id"]]["n"]
        p = np.exp(np.asarray(r["sample_lp"], float))[:, :n]
        psamples[r["id"]] = p / p.sum(1, keepdims=True)   # NaN at collapse, on purpose
        pmass[r["id"]] = float(np.mean(r["sample_pmass_allowed"]))
    x, y, x_se, y_se = model_coord_ci(psamples, resolved, rng)
    per_item = {}
    for axis in (X_AXIS, Y_AXIS):
        for it in resolved[axis]:
            s = it["suffix"]
            per_item[s] = {"axis": axis, "pmass": pmass[s],
                           "pos": positiveness(psamples[s].mean(0), it["pole_idx"], it["n"])}
    return {"x": x, "y": y, "x_se": x_se, "y_se": y_se,
            "mean_pmass": float(np.mean(list(pmass.values()))),
            "min_pmass": float(np.min(list(pmass.values()))),
            "per_item": per_item}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen3-0.6B")
    ap.add_argument("--methods", default="mean_diff,pca,vjp_delta,random")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--layers", default="mid", help="'mid' = the middle 60% of blocks, or a comma list")
    ap.add_argument("--n-pairs", type=int, default=256)
    ap.add_argument("--extract-batch-size", type=int, default=8,
                    help="vjp_delta holds a backward graph, so it needs a smaller batch than the others")
    ap.add_argument("--read-batch-size", type=int, default=12)
    ap.add_argument("--max-length", type=int, default=384)
    ap.add_argument("--target-kl", type=float, default=0.5)
    ap.add_argument("--c-grid", default="-2,-1,-0.5,0.5,1,2",
                    help="signed multipliers of the iso-KL calibrated C; c=0 is always read once")
    ap.add_argument("--think-tokens", type=int, default=64)
    ap.add_argument("--n-samples", type=int, default=4,
                    help="think trajectories per item; >1 needs --temperature > 0 and feeds the CI")
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--device-map", default=None,
                    help="'auto' shards a large model over the container's GPUs; default is one device")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--dtype", default="bfloat16")
    ap.add_argument("--smoke", action="store_true",
                    help="tiny settings: 4 pairs, 1 think token, 1 dose, for the correctness gate")
    ap.add_argument("--out", type=Path, default=Path("outputs"))
    args = ap.parse_args()

    if args.smoke:
        args.n_pairs, args.think_tokens, args.n_samples = 4, 1, 1
        args.temperature, args.c_grid, args.max_length = 0.0, "1", 128
        args.extract_batch_size = 2

    args.out.mkdir(parents=True, exist_ok=True)
    dtype = getattr(torch, args.dtype)
    tok = AutoTokenizer.from_pretrained(args.model)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    tok.padding_side = "left"
    if args.device_map:
        model = AutoModelForCausalLM.from_pretrained(args.model, dtype=dtype,
                                                     device_map=args.device_map).eval()
    else:
        model = AutoModelForCausalLM.from_pretrained(args.model, dtype=dtype).to(args.device).eval()

    n_blocks = model.config.num_hidden_layers
    if args.layers == "mid":
        layers = tuple(range(max(2, int(n_blocks * 0.2)), min(n_blocks - 2, int(n_blocks * 0.8))))
    else:
        layers = tuple(int(x) for x in args.layers.split(","))
    logger.info(f"BLUF: model={args.model} methods={args.methods} layers={len(layers)}/{n_blocks} "
                f"target_kl={args.target_kl} c_grid={args.c_grid}")

    resolved = resolve_items(load_wvs_all())
    instrs, meta = build_instruments(resolved)
    logger.info(f"WVS-IW battery: {sum(len(i.items) for i in instrs)} items in {len(instrs)} instruments")

    pos_prompts, neg_prompts = make_persona_pairs(
        tok, n_pairs=args.n_pairs, thinking=True,
        persona_pairs=[HONESTY_PAIR], template=HONESTY_TEMPLATE)

    read_kw = dict(think=args.think_tokens, batch_size=args.read_batch_size,
                   n_samples=args.n_samples, temperature=args.temperature)
    base = read_coords(model, tok, instrs, meta, resolved, np.random.default_rng(0), **read_kw)
    logger.info(f"base x={base['x']:.4f} y={base['y']:.4f} pmass={base['mean_pmass']:.3f}\n"
                f"SHOULD: pmass near 1.0 and the coordinate near the published base point for this "
                f"model. ELSE the prefill or chat template is off and no steered point is comparable.")

    mults = [float(m) for m in args.c_grid.split(",")]
    for method in args.methods.split(","):
        cfg = METHODS[method](layers=layers, coeff=1.0, dtype=dtype, seed=args.seed)
        t0 = time.time()
        v = sl.train(model, tok, pos_prompts, neg_prompts, cfg,
                     batch_size=args.extract_batch_size, max_length=args.max_length)
        C, _hist = sl.calibrate_iso_kl(v, model, tok, calib_prompts(), target_kl=args.target_kl,
                                       device=str(next(model.parameters()).device))
        C = float(C)
        logger.info(f"{method}: calibrated C={C:+.4f} extract+calib={time.time() - t0:.0f}s")

        doses = [{"mult": 0.0, "c": 0.0, **base}]
        for m in mults:
            with v(model, C=m * C):
                d = read_coords(model, tok, instrs, meta, resolved,
                                np.random.default_rng(0), **read_kw)
            doses.append({"mult": m, "c": m * C, **d})
            logger.info(f"{method} c={m * C:+.4f} (x{m:+.1f}): x={d['x']:.4f} y={d['y']:.4f} "
                        f"dx={d['x'] - base['x']:+.4f} dy={d['y'] - base['y']:+.4f} "
                        f"pmass={d['mean_pmass']:.3f}")

        out = args.out / f"wvs_steer_{method}_s{args.seed}.json"
        out.write_text(json.dumps({
            "model": args.model, "method": method, "seed": args.seed,
            "axis": "honesty", "pos_pole": HONESTY_PAIR[0], "neg_pole": HONESTY_PAIR[1],
            "template": HONESTY_TEMPLATE, "layers": list(layers), "n_pairs": args.n_pairs,
            "target_kl": args.target_kl, "calibrated_C": C,
            "think_tokens": args.think_tokens, "n_samples": args.n_samples,
            "temperature": args.temperature, "doses": doses,
        }, indent=1))
        logger.info(f"wrote {out}")


if __name__ == "__main__":
    main()
