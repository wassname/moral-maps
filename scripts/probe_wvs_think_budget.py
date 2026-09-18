"""Can this model's WVS coordinate resolve a steering effect at all?

Two questions, both asked before renting a big GPU.

1. Is the answer slot readable? Qwen3-0.6B answers the IW battery with pmass 0.999, Qwen3.5-0.8B
   reads 0.61-0.84, and the leak goes to the option WORD, not gibberish. The think-budget sweep
   separates "the model is mid-thought when we force the slot" from "the format prior is weak".
2. Is the coordinate stable? The battery is 12 items, 5 on X. One item flipping moves X by up to
   0.2, which would swamp any steering effect. The resample pass reports the bootstrap CI over
   items and think traces, so we can compare it against the move we hope to see.

  uv run --extra steer python scripts/probe_wvs_think_budget.py --model Qwen/Qwen3.5-0.8B
"""
from __future__ import annotations

import argparse

import numpy as np
import torch
from loguru import logger
from tabulate import tabulate
from transformers import AutoModelForCausalLM, AutoTokenizer

from moralmaps.iw_axes import resolve_items
from moralmaps.read import read_items, resolve_answer_ids
from moralmaps.wvs import build_instruments, load_wvs_all, model_axis_scores, read_coords, read_model


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen3.5-0.8B")
    ap.add_argument("--think-budgets", default="1,16,64,256")
    ap.add_argument("--ci-think", type=int, default=64, help="think budget for the resample pass")
    ap.add_argument("--ci-samples", type=int, default=8, help="think traces averaged per item")
    ap.add_argument("--ci-temperature", type=float, default=1.0)
    ap.add_argument("--batch-size", type=int, default=12)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--device-map", default=None, help="'auto' shards a large model over the GPUs")
    args = ap.parse_args()

    tok = AutoTokenizer.from_pretrained(args.model)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    tok.padding_side = "left"
    if args.device_map:
        model = AutoModelForCausalLM.from_pretrained(args.model, dtype=torch.bfloat16,
                                                     device_map=args.device_map).eval()
    else:
        model = AutoModelForCausalLM.from_pretrained(args.model, dtype=torch.bfloat16).to(args.device).eval()

    resolved = resolve_items(load_wvs_all())
    instrs, meta = build_instruments(resolved)

    rows = []
    for think in [int(t) for t in args.think_budgets.split(",")]:
        read = []
        for k, instr in enumerate(instrs):
            read += read_items(model, tok, instr, instr.items,
                               resolve_answer_ids(tok, instr.answer_space),
                               max_think_tokens=think, batch_size=args.batch_size,
                               verbose_first=(k == 0 and think == 1))
        pm = [r["pmass_allowed"] for r in read]
        x, y = model_axis_scores(read_model(read, meta), meta, resolved)
        closed = sum(r["emitted_close"] for r in read)
        rows.append([think, f"{np.mean(pm):.3f}", f"{np.min(pm):.3f}", f"{closed}/{len(read)}",
                     f"{x:.4f}", f"{y:.4f}"])
        logger.info(f"think={think}: mean pmass {np.mean(pm):.3f}")

    print(tabulate(rows, tablefmt="pipe", headers=[
        "think tokens", "mean pmass", "min pmass", "closed think", "x", "y"]))
    print("\nSHOULD: pmass climbs toward ~1.0 as the think budget grows, and the coordinate settles.\n"
          "ELSE, if pmass stays low at every budget, the prefill or chat template is wrong for this\n"
          "family and no steered coordinate from it is comparable to the published map.")

    c = read_coords(model, tok, instrs, meta, resolved, np.random.default_rng(0),
                    think=args.ci_think, batch_size=args.batch_size,
                    n_samples=args.ci_samples, temperature=args.ci_temperature)
    print(f"\nresample pass: think={args.ci_think} n_samples={args.ci_samples} "
          f"T={args.ci_temperature}\n"
          f"  x = {c['x']:.4f} +- {1.96 * c['x_se']:.4f} (95%)\n"
          f"  y = {c['y']:.4f} +- {1.96 * c['y_se']:.4f} (95%)\n"
          f"  pmass mean {c['mean_pmass']:.3f} min {c['min_pmass']:.3f}\n"
          f"SHOULD: the 95% interval is small next to the move we want to detect. The published\n"
          f"Qwen3-4B Authority steer moved MFQ-2 factors by a few tenths of a scale point; on this\n"
          f"0-1 axis a usable effect is ~0.05 or more, so a CI wider than that means the 12-item\n"
          f"battery cannot resolve the steer and the plot would be noise.")


if __name__ == "__main__":
    main()
