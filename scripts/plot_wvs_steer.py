"""Draw the honesty steer as a path across the WVS culture map, one path per method.

Reads the JSONs from scripts/wvs_steer_sweep.py and puts them on the same map as the base model,
so the question "where does honesty steering move this model, culturally" has a picture.

Three things the figure has to keep honest:
  - the random control's reach is drawn as a grey null region. A method inside it has shown nothing.
  - doses whose answer mass collapsed are dropped, and counted in the caption. A path that wanders
    because the model stopped answering is not a cultural move.
  - the leave-one-out column in the table says how much of the move survives dropping the single
    most influential item, so a one-item lexical effect cannot pass as a shift of the whole profile.

  uv run python scripts/plot_wvs_steer.py --runs outputs --out docs/img/wvs/wvs_steer_honesty.png
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from loguru import logger
from tabulate import tabulate

import matplotlib
matplotlib.use("Agg")

from moralmaps import maps
from moralmaps.iw_axes import X_AXIS, Y_AXIS, positiveness, resolve_items
from moralmaps.wvs import human_axis_scores, load_wvs_all
from moralmaps.zones import zones_for

# Deliberately none of the zone-hull colours (West blue, East Asia red, Latin America orange,
# African-Islamic brown) or the model-star purple, so a path is never mistaken for a human region.
METHOD_COLORS = {"vjp_delta": "#111111", "mean_diff": "#00838f", "pca": "#1e8449", "random": "#777777"}


def axis_means(per_item: dict, resolved: dict, drop: str | None = None) -> tuple[float, float]:
    """(X, Y) from saved per-item positions, optionally dropping one item (leave-one-out)."""
    xy = []
    for axis in (X_AXIS, Y_AXIS):
        vals = [per_item[it["suffix"]]["pos"] for it in resolved[axis] if it["suffix"] != drop]
        xy.append(float(np.mean(vals)))
    return xy[0], xy[1]


def loo_worst(dose: dict, base: dict, resolved: dict) -> tuple[str, float]:
    """The item whose removal shrinks the move most, and the move length without it."""
    full = np.hypot(dose["x"] - base["x"], dose["y"] - base["y"])
    worst, best_len = None, full
    for suffix in dose["per_item"]:
        dx_, dy_ = axis_means(dose["per_item"], resolved, drop=suffix)
        bx_, by_ = axis_means(base["per_item"], resolved, drop=suffix)
        length = np.hypot(dx_ - bx_, dy_ - by_)
        if length < best_len:
            worst, best_len = suffix, length
    return worst, float(best_len)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=Path, default=Path("outputs"))
    ap.add_argument("--out", type=Path, default=Path("docs/img/wvs/wvs_steer_honesty.png"))
    ap.add_argument("--min-pmass", type=float, default=0.9,
                    help="drop any dose whose mean answer-token mass fell below this")
    args = ap.parse_args()

    runs = [json.loads(p.read_text()) for p in sorted(args.runs.glob("wvs_steer_*.json"))]
    assert runs, f"no wvs_steer_*.json under {args.runs}"
    resolved = resolve_items(load_wvs_all())
    countries, P = human_axis_scores(resolved)
    zones_all, emph = zones_for(countries)
    sgx, sgy = maps.orient_geographic(P, countries, zones_all)   # plot_value_map's own flip

    model = runs[0]["model"]
    assert all(r["model"] == model for r in runs), "mixing models in one figure"
    base = runs[0]["doses"][0]
    fig = maps.plot_value_map(
        "WVS Inglehart-Welzel", countries, P,
        ("Survival", "Self-expression", "Traditional", "Secular-Rational"),
        models={f"{model.split('/')[-1]} (base)": (base["x"], base["y"])}, emphasize=emph,
        title=f"Honesty steering on the culture map\n{model.split('/')[-1]}",
        note="World Values Survey | source: github.com/wassname/moral-maps",
        title_y=0.115, note_y=0.04)
    ax = fig.axes[0]

    dropped, rows, null_pts = 0, [], []
    for r in runs:
        kept = [d for d in r["doses"] if d["mean_pmass"] >= args.min_pmass]
        dropped += len(r["doses"]) - len(kept)
        kept.sort(key=lambda d: d["mult"])
        xs = [d["x"] * sgx for d in kept]
        ys = [d["y"] * sgy for d in kept]
        color = METHOD_COLORS[r["method"]]
        if r["method"] == "random":
            null_pts += list(zip(xs, ys))
        ax.plot(xs, ys, "--o" if r["method"] == "random" else "-o", color=color, lw=2.0, ms=3.5,
                alpha=0.85, zorder=5, label=f"{r['method']} s{r['seed']}")
        # both directions: the honest score is the weaker one, so never let +C hide a dead -C
        for sign in (+1, -1):
            side = [d for d in kept if np.sign(d["mult"]) == sign]
            if not side:
                continue
            far = max(side, key=lambda d: abs(d["mult"]))
            worst, loo_len = loo_worst(far, r["doses"][0], resolved)
            rows.append([r["method"], r["seed"], f"{r['calibrated_C']:+.3f}", f"{far['mult']:+.1f}",
                         f"{far['x'] - base['x']:+.4f}", f"{far['y'] - base['y']:+.4f}",
                         f"{np.hypot(far['x'] - base['x'], far['y'] - base['y']):.4f}",
                         f"{loo_len:.4f}", worst or "-", f"{far['mean_pmass']:.3f}"])

    # the reach of random directions at the same iso-KL dose: anything inside this has shown nothing.
    # Needs a real cloud, one random seed gives a degenerate box that would overstate the null.
    if len(null_pts) >= 3:
        from scipy.spatial import ConvexHull
        pts = np.array(null_pts)
        hull = pts[ConvexHull(pts).vertices]
        ax.fill(hull[:, 0], hull[:, 1], color="#777777", alpha=0.15, zorder=1,
                label="random null region")
    else:
        logger.warning(f"only {len(null_pts)} random points, null region not drawn")
    ax.legend(loc="upper right", fontsize=7, framealpha=0.9)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=200, bbox_inches="tight")
    fig.savefig(args.out.with_suffix(".svg"), bbox_inches="tight")

    rows.sort(key=lambda r: -float(r[6]))
    print(tabulate(rows, tablefmt="pipe", headers=[
        "method", "seed", "C", "dose", "dx", "dy", "|move|", "|move| less worst item",
        "worst item", "pmass"]))
    logger.info(f"wrote {args.out} ({dropped} doses dropped below pmass {args.min_pmass})")


if __name__ == "__main__":
    main()
