"""Does the WVS answer-slot readout hold on this model family, and at what think budget?

Qwen3-0.6B answers the IW battery with pmass 0.999. Qwen3.5-0.8B read 0.783 at think=1 in the
steering smoke, which would make every steered coordinate mushy. Before renting a big GPU, find out
whether that is the think budget (the model is mid-thought when we force the answer slot) or the
chat template (the prefill does not land where we think it does).

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
from moralmaps.wvs import build_instruments, load_wvs_all, model_axis_scores, read_model


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen3.5-0.8B")
    ap.add_argument("--think-budgets", default="1,16,64,256")
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


if __name__ == "__main__":
    main()
