"""Draw the honesty steer as a path across the WVS culture map, one path per method.

Reads the JSONs from scripts/wvs_steer_sweep.py and puts them on the same map as the base model,
so the question "where does honesty steering move this model, culturally" has a picture.

Three things the figure has to keep honest:
  - the random control's reach is drawn as a grey null region. A method inside it has shown nothing.
  - doses below the preregistered answer-mass gate stay visible as faint hollow points, but are
    excluded from the result table. A path that wanders because the model stopped answering is not
    a cultural move.
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
from moralmaps.wvs import coord_delta_ci, human_axis_scores, load_wvs_all
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


def pool_dose(runs: list[dict], mult: float) -> dict:
    """Pool independent read seeds for one method and dose."""
    doses = [next(d for d in r["doses"] if d["mult"] == mult) for r in runs]
    suffixes = doses[0]["per_item"]
    return {
        "mult": mult,
        "x": float(np.mean([d["x"] for d in doses])),
        "y": float(np.mean([d["y"] for d in doses])),
        "mean_pmass": float(np.mean([d["mean_pmass"] for d in doses])),
        "min_pmass": float(np.min([d["min_pmass"] for d in doses])),
        "per_item": {
            s: {"axis": doses[0]["per_item"][s]["axis"],
                "pmass": float(np.mean([d["per_item"][s]["pmass"] for d in doses])),
                "pos": float(np.mean([d["per_item"][s]["pos"] for d in doses]))}
            for s in suffixes
        },
        "psamples": {
            s: np.concatenate([np.asarray(d["psamples"][s]) for d in doses]).tolist()
            for s in doses[0]["psamples"]
        },
    }


def draw_path(ax, doses: list[dict], color: str, sgx: float, sgy: float,
              min_pmass: float, *, random: bool = False, label: str | None = None) -> None:
    """Draw failed-coherence segments faint and hollow rather than hiding them."""
    doses = sorted(doses, key=lambda d: d["mult"])
    ok = [d["mean_pmass"] >= min_pmass for d in doses]
    for a, b, pass_a, pass_b in zip(doses, doses[1:], ok, ok[1:]):
        ax.plot([a["x"] * sgx, b["x"] * sgx], [a["y"] * sgy, b["y"] * sgy],
                "--" if random else "-", color=color, lw=1.2 if random else 2.0,
                alpha=0.65 if pass_a and pass_b else 0.18, zorder=4)
    passed = [d for d, keep in zip(doses, ok) if keep]
    failed = [d for d, keep in zip(doses, ok) if not keep]
    if label:
        ax.plot([], [], "--" if random else "-", color=color, lw=1.5, label=label)
    if passed:
        ax.scatter([d["x"] * sgx for d in passed], [d["y"] * sgy for d in passed],
                   s=14, color=color, alpha=0.85, zorder=5)
    if failed:
        ax.scatter([d["x"] * sgx for d in failed], [d["y"] * sgy for d in failed],
                   s=14, facecolors="none", edgecolors=color, alpha=0.25, zorder=3)


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
    groups = {m: sorted([r for r in runs if r["method"] == m], key=lambda r: r["seed"])
              for m in sorted({r["method"] for r in runs})}
    primary = next((rs for m, rs in groups.items() if m != "random"), runs[:1])
    base = pool_dose(primary, 0.0)
    fig = maps.plot_value_map(
        "WVS Inglehart-Welzel", countries, P,
        ("Survival", "Self-expression", "Traditional", "Secular-Rational"),
        models={f"{model.split('/')[-1]} (base)": (base["x"], base["y"])}, emphasize=emph,
        title=f"Honesty steering on the culture map\n{model.split('/')[-1]}",
        note="Filled: pmass >= 0.90 | hollow: failed coherence gate",
        title_y=0.115, note_y=0.04)
    ax = fig.axes[0]

    random_runs = groups.get("random", [])
    null_move: dict[float, list[float]] = {}
    for r in random_runs:
        b = r["doses"][0]
        for d in r["doses"][1:]:
            if d["mean_pmass"] >= args.min_pmass:
                null_move.setdefault(d["mult"], []).append(
                    float(np.hypot(d["x"] - b["x"], d["y"] - b["y"])))

    failed, rows, null_pts = 0, [], []
    for method, method_runs in groups.items():
        color = METHOD_COLORS[method]
        mults = sorted({d["mult"] for r in method_runs for d in r["doses"]})
        if method == "random":
            for i, r in enumerate(method_runs):
                draw_path(ax, r["doses"], color, sgx, sgy, args.min_pmass,
                          random=True, label="random controls" if i == 0 else None)
                null_pts += [(d["x"] * sgx, d["y"] * sgy) for d in r["doses"]
                             if d["mult"] and d["mean_pmass"] >= args.min_pmass]
                failed += sum(d["mean_pmass"] < args.min_pmass for d in r["doses"])
            continue

        pooled = [pool_dose(method_runs, m) for m in mults]
        draw_path(ax, pooled, color, sgx, sgy, args.min_pmass, label=method)
        failed += sum(d["mean_pmass"] < args.min_pmass for d in pooled)
        pooled_base = next(d for d in pooled if d["mult"] == 0)
        for sign in (+1, -1):
            side = [d for d in pooled if np.sign(d["mult"]) == sign
                    and d["mean_pmass"] >= args.min_pmass]
            if not side:
                continue
            far = max(side, key=lambda d: abs(d["mult"]))
            dx, dy, dx_se, dy_se = coord_delta_ci(
                pooled_base["psamples"], far["psamples"], resolved,
                np.random.default_rng(20_000 + sign))
            worst, loo_len = loo_worst(far, pooled_base, resolved)
            move = float(np.hypot(dx, dy))
            null = null_move.get(far["mult"], [])
            null_p95 = float(np.quantile(null, 0.95)) if null else np.nan
            rows.append([method, len(method_runs), f"{far['mult']:+.1f}",
                         f"{dx:+.4f}+-{1.96 * dx_se:.3f}",
                         f"{dy:+.4f}+-{1.96 * dy_se:.3f}",
                         f"{move:.4f}", f"{loo_len:.4f}",
                         f"{null_p95:.4f}" if null else "-", len(null),
                         "yes" if null and move > null_p95 else "no",
                         worst or "-", f"{far['mean_pmass']:.3f}"])
            ax.annotate(f"{far['mult']:+g}C", (far["x"] * sgx, far["y"] * sgy),
                        xytext=(3, 3), textcoords="offset points", fontsize=6, color=color)

    if len(null_pts) >= 3:
        from scipy.spatial import ConvexHull
        pts = np.array(null_pts)
        hull = pts[ConvexHull(pts).vertices]
        ax.fill(hull[:, 0], hull[:, 1], color="#777777", alpha=0.10, zorder=1,
                label="random reach (all doses)")
    else:
        logger.warning(f"only {len(null_pts)} coherent random points, null region not drawn")
    ax.legend(loc="upper right", fontsize=7, framealpha=0.9)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=200, bbox_inches="tight")
    fig.savefig(args.out.with_suffix(".svg"), bbox_inches="tight")

    rows.sort(key=lambda r: -float(r[5]))
    print(tabulate(rows, tablefmt="pipe", headers=[
        "method", "read seeds", "dose", "dx (95%)", "dy (95%)", "|move|",
        "|move| less worst item", "random p95", "random n", "beats random?",
        "worst item", "pmass"]))

    random_effects = [r["manipulation_check"]["scored"]["effect_logodds"]
                      for r in random_runs]
    random_effect_p95 = float(np.quantile(random_effects, 0.95)) if random_effects else np.nan
    check_rows = []
    for method, method_runs in groups.items():
        if method == "random":
            continue
        effects = [r["manipulation_check"]["scored"]["effect_logodds"] for r in method_runs]
        effect = float(np.mean(effects))
        check_rows.append([method, f"{effect:+.3f}",
                           f"{random_effect_p95:+.3f}" if random_effects else "-",
                           len(random_effects), "yes" if random_effects and effect > random_effect_p95 else "no"])
    print("\nHeld-out honesty manipulation (true-vs-welcome log-odds):")
    print(tabulate(check_rows, tablefmt="pipe", headers=[
        "method", "effect", "random p95", "random n", "honesty-specific?"]))
    print("\ndx/dy intervals pool independent read seeds and pair base versus dose on the same\n"
          "items and sampled think streams. Hollow points remain visible but fail pmass >= 0.90.")
    logger.info(f"wrote {args.out} ({failed} method-dose paths/points failed pmass {args.min_pmass})")


if __name__ == "__main__":
    main()
