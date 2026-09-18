"""WVS Inglehart-Welzel readout: GlobalOpinionQA items -> Instruments -> (X, Y) coordinates.

`iw_axes` picks and orients the items; this module turns them into something a model can answer
and a coordinate we can plot. Two consumers share it, so the base map and any steered run place a
model with the SAME items, legend, prefill and reduction:

  scripts/wvs_map.py          base map, human societies + API and local models
  scripts/wvs_steer_sweep.py  the same local readout under an activation steering vector

Human coordinates come from the WVS choice frequencies, model coordinates from the answer-token
distribution over the option digits. They are different measurements on one scale, a documented
proxy, see the wvs_map.py docstring.
"""
from __future__ import annotations

import ast
import re

import numpy as np

from .instrument import Instrument, InstrItem
from .iw_axes import SKIP, X_AXIS, Y_AXIS, positiveness   # noqa: F401  positiveness re-exported
from .zones import zone_of

# option labels are single digits 0..n-1 -- single-token (unlike '10' on the justifiable scale) and
# the format the answer-token reader is tuned for (a bare digit, not a letter the model ignores in
# favour of the option word).
DIGITS = "0123456789"


def load_wvs_all() -> list[dict]:
    """Every WVS question with its substantive options (DK/refusal/Missing/INAP dropped) and each
    zone-mapped country's distribution renormalized over those options."""
    from datasets import load_dataset   # optional dep: numeric-only consumers skip `datasets`

    ds = load_dataset("Anthropic/llm_global_opinions", split="train")
    out = []
    for r in ds:
        if r["source"] != "WVS" or not r["question"]:
            continue
        opts = ast.literal_eval(r["options"]) if isinstance(r["options"], str) else r["options"]
        keep = [i for i, o in enumerate(opts) if not SKIP.search(o)]
        if len(keep) < 2:
            continue
        sel = ast.literal_eval(re.search(r"\{.*\}", r["selections"], re.S).group(0))
        dist = {}
        for c, ps in sel.items():
            if not zone_of(c):
                continue
            v = np.array([ps[i] for i in keep], float)
            if v.sum() > 0:
                dist[c] = v / v.sum()
        out.append({"q": r["question"], "opts": [opts[i] for i in keep], "dist": dist})
    return out


def human_axis_scores(resolved: dict[str, list[dict]]) -> tuple[list[str], np.ndarray]:
    """Per-country (X, Y). A country is kept if it covers at least half of each axis's items; its
    axis value is the mean positiveness over the items it does cover."""
    countries = sorted({c for items in resolved.values() for it in items for c in it["rec"]["dist"]})
    rows, keep = [], []
    for c in countries:
        xy, ok = [], True
        for axis in (X_AXIS, Y_AXIS):
            vals = [positiveness(it["rec"]["dist"][c], it["pole_idx"], it["n"])
                    for it in resolved[axis] if c in it["rec"]["dist"]]
            if len(vals) < (len(resolved[axis]) + 1) // 2:
                ok = False
                break
            xy.append(float(np.mean(vals)))
        if ok:
            keep.append(c)
            rows.append(xy)
    return keep, np.array(rows)


def build_instruments(resolved: dict[str, list[dict]]) -> tuple[list[Instrument], dict[str, dict]]:
    """One nominal Instrument per distinct option-count (answer_space = single letters), covering the
    union of both axes' items. Returns the instruments + a {suffix: {pole_idx, n, axis}} index."""
    items_by_n: dict[int, list[InstrItem]] = {}
    meta: dict[str, dict] = {}
    seen: set[str] = set()
    for axis, items in resolved.items():
        for it in items:
            s = it["suffix"]
            meta[s] = {"pole_idx": it["pole_idx"], "n": it["n"], "axis": axis}
            if s in seen:
                continue
            seen.add(s)
            n, opts = it["n"], it["rec"]["opts"]
            legend = "; ".join(f"{DIGITS[k]}) {o}" for k, o in enumerate(opts))
            task = f"Answer options: {legend}. Respond with only the number."
            items_by_n.setdefault(n, []).append(
                InstrItem(id=s, prompt=it["rec"]["q"], dimension="iw", sign=1,
                          frame="forward", meta={"task": task}))
    instrs = [Instrument(name=f"wvs_iw_n{n}", construct="opinion", kind="nominal",
                         answer_space=list(DIGITS[:n]), dimensions=["iw"], items=its,
                         prefill="(", display="WVS-IW")
              for n, its in sorted(items_by_n.items())]
    return instrs, meta


def model_axis_scores(vecs: dict[str, np.ndarray], meta: dict[str, dict],
                      resolved: dict[str, list[dict]]) -> tuple[float, float]:
    """(X, Y) for one model from its per-item p vectors (suffix -> p over options)."""
    xy = []
    for axis in (X_AXIS, Y_AXIS):
        vals = [positiveness(vecs[it["suffix"]], it["pole_idx"], it["n"]) for it in resolved[axis]]
        xy.append(float(np.mean(vals)))
    return xy[0], xy[1]


def read_model(rows: list[dict], meta: dict[str, dict]) -> dict[str, np.ndarray]:
    """rows from read_items -> {suffix: p over that item's options}. NaN p (read collapse) fails loud
    later via positiveness rather than being imputed."""
    return {r["id"]: np.asarray(r["p"], float)[: meta[r["id"]]["n"]] for r in rows}


def read_coords(model, tok, instrs, meta, resolved, rng, *, think: int, batch_size: int,
                n_samples: int, temperature: float) -> dict:
    """One live-model WVS readout -> coordinate, bootstrap CI, per-item positions, coherence.

    n_samples > 1 (with temperature > 0) averages the answer distribution over independent think
    traces. The battery is 12 items, so a single trace that flips one item moves an axis by up to
    1/5, which is why the CI here is not decoration.
    """
    from .read import read_items, resolve_answer_ids   # torch import stays out of the module import

    rows = []
    for instr in instrs:
        rows += read_items(model, tok, instr, instr.items,
                           resolve_answer_ids(tok, instr.answer_space),
                           max_think_tokens=think, batch_size=batch_size,
                           n_samples=n_samples, temperature=temperature)
    lp_gather, psamples, pmass = {}, {}, {}
    for r in rows:
        n = meta[r["id"]]["n"]
        lp_gather[r["id"]] = np.asarray(r["sample_lp"], float)[:, :n]
        p = np.exp(lp_gather[r["id"]])
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
            "per_item": per_item,
            # Full-vocabulary logprobs gathered at the allowed answer tokens, before renormalization.
            "lp_gather": {k: v.tolist() for k, v in lp_gather.items()},
            "psamples": {k: v.tolist() for k, v in psamples.items()}}


def coord_delta_ci(psamples_a: dict, psamples_b: dict, resolved: dict, rng: np.random.Generator,
                   B: int = 2000) -> tuple[float, float, float, float]:
    """(dx, dy, dx_se, dy_se) for b minus a, each replicate resampling the SAME items in both.

    Pairing removes the item-set variance the two readouts share (+-0.07 on X for this battery).
    """
    a = {k: np.asarray(v, float) for k, v in psamples_a.items()}
    b = {k: np.asarray(v, float) for k, v in psamples_b.items()}

    def coords(ps: dict, draw: dict) -> tuple[float, float]:
        xy = []
        for axis in (X_AXIS, Y_AXIS):
            vals = []
            for j, srows in draw[axis]:
                it = resolved[axis][j]
                vals.append(positiveness(ps[it["suffix"]][srows].mean(0), it["pole_idx"], it["n"]))
            xy.append(float(np.mean(vals)))
        return xy[0], xy[1]

    point = {axis: [(j, np.arange(len(a[resolved[axis][j]["suffix"]])))
                    for j in range(len(resolved[axis]))] for axis in (X_AXIS, Y_AXIS)}
    ax_, ay_ = coords(a, point)
    bx_, by_ = coords(b, point)
    dxs, dys = [], []
    for _ in range(B):
        # one item draw and one trace draw per replicate, reused for BOTH readouts: that is what
        # makes it paired
        draw = {}
        for axis in (X_AXIS, Y_AXIS):
            items = resolved[axis]
            picks = rng.integers(0, len(items), len(items))
            draw[axis] = [(int(j), rng.integers(0, len(a[items[j]["suffix"]]),
                                                len(a[items[j]["suffix"]]))) for j in picks]
        rx, ry = coords(a, draw)
        sx, sy = coords(b, draw)
        dxs.append(sx - rx)
        dys.append(sy - ry)
    return bx_ - ax_, by_ - ay_, float(np.std(dxs)), float(np.std(dys))


def _sample_only_coord_se(psamples: dict[str, np.ndarray], resolved: dict[str, list[dict]],
                          rng: np.random.Generator, n_draws: int, B: int = 500) -> tuple[float, float]:
    """Response-mean bootstrap SE with the WVS item set held fixed."""
    samples = []
    for _ in range(B):
        xy = []
        for axis in (X_AXIS, Y_AXIS):
            vals = []
            for it in resolved[axis]:
                ps = psamples[it["suffix"]]
                mean_p = ps[rng.integers(0, len(ps), n_draws)].mean(0)
                vals.append(positiveness(mean_p, it["pole_idx"], it["n"]))
            xy.append(float(np.mean(vals)))
        samples.append(xy)
    return tuple(np.std(samples, axis=0))


def model_coord_ci(psamples: dict[str, np.ndarray], resolved: dict[str, list[dict]],
                   rng: np.random.Generator, B: int = 500) -> tuple[float, float, float, float]:
    """(x, y, x_se, y_se), combined item-and-response-mean bootstrap uncertainty.

    The point uses each item's mean over its N ratings. Each replicate resamples items and, for every
    selected item, resamples N ratings then averages them. This estimates uncertainty of the N-sample
    mean rather than uncertainty of a single response. The separate `_sample_only_coord_se` keeps the
    fixed-item response component available for diagnostics.
    """
    def axis_coords(getp) -> list[float]:
        return [float(np.mean([positiveness(getp(it), it["pole_idx"], it["n"]) for it in resolved[axis]]))
                for axis in (X_AXIS, Y_AXIS)]
    x, y = axis_coords(lambda it: psamples[it["suffix"]].mean(0))
    bx, by = [], []
    for _ in range(B):
        xy = []
        for axis in (X_AXIS, Y_AXIS):
            items = resolved[axis]
            vals = []
            for j in rng.integers(0, len(items), len(items)):
                it = items[j]
                ps = psamples[it["suffix"]]
                mean_p = ps[rng.integers(0, len(ps), len(ps))].mean(0)
                vals.append(positiveness(mean_p, it["pole_idx"], it["n"]))
            xy.append(float(np.mean(vals)))
        bx.append(xy[0]); by.append(xy[1])
    return x, y, float(np.std(bx)), float(np.std(by))
