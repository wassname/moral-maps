"""Render saved Qwen3-14B WVS steering artifacts without model inference.

The source of truth is the saved ``lp_gather`` values in ``outputs/wvs_steer_*.json``.
A point is connected only while its pooled answer mass remains at least 96% of that
method's pooled vanilla answer mass. Later recovered points are observations, not a
continuous dose trajectory.

uv run python scripts/plot_wvs_steer.py \
  --runs outputs \
  --out docs/img/wvs/wvs_steer_honesty_qwen3_14b.png
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
import numpy as np
from loguru import logger
from matplotlib.patches import FancyArrowPatch
from tabulate import tabulate

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from moralmaps import maps
from moralmaps.iw_axes import X_AXIS, Y_AXIS, resolve_items
from moralmaps.wvs import coord_delta_ci, human_axis_scores, load_wvs_all
from moralmaps.zones import zones_for

COLORS = {"vjp_delta": "#111111", "mean_diff": "#00838f", "pca": "#1e8449", "random": "#777777"}
MAIN_METHODS = ("vjp_delta", "mean_diff", "pca")
PMASS_RATIO_FLOOR = 0.96


def axis_means(per_item: dict, resolved: dict, drop: str | None = None) -> tuple[float, float]:
    """Return WVS coordinates from saved per-item positions."""
    values = []
    for axis in (X_AXIS, Y_AXIS):
        values.append(float(np.mean([
            per_item[item["suffix"]]["pos"]
            for item in resolved[axis]
            if item["suffix"] != drop
        ])))
    return tuple(values)


def loo_worst(dose: dict, base: dict, resolved: dict) -> tuple[str, float]:
    """Return the item whose removal reduces the saved movement most."""
    full_move = np.hypot(dose["x"] - base["x"], dose["y"] - base["y"])
    worst, smallest_move = None, full_move
    for suffix in dose["per_item"]:
        dx, dy = axis_means(dose["per_item"], resolved, drop=suffix)
        bx, by = axis_means(base["per_item"], resolved, drop=suffix)
        move = np.hypot(dx - bx, dy - by)
        if move < smallest_move:
            worst, smallest_move = suffix, move
    return worst, float(smallest_move)


def entropy_and_pmax(lp_gather: dict[str, list[list[float]]]) -> tuple[float, float]:
    """Compute allowed-answer entropy and maximum probability from full-vocabulary logprobs."""
    entropies, maxima = [], []
    for samples in lp_gather.values():
        for logprobs in samples:
            logprobs = np.asarray(logprobs)
            probs = np.exp(logprobs - np.logaddexp.reduce(logprobs))
            entropies.append(float(-np.sum(probs * np.log(probs)) / np.log(len(probs))))
            maxima.append(float(probs.max()))
    return float(np.mean(entropies)), float(np.mean(maxima))


def pool_dose(runs: list[dict], mult: float) -> dict:
    """Pool read seeds while retaining every sample needed for diagnostics."""
    doses = [next(dose for dose in run["doses"] if dose["mult"] == mult) for run in runs]
    suffixes = doses[0]["per_item"]
    lp_gather = {
        suffix: [sample for dose in doses for sample in dose["lp_gather"][suffix]]
        for suffix in doses[0]["lp_gather"]
    }
    entropy, pmax = entropy_and_pmax(lp_gather)
    return {
        "mult": mult,
        "x": float(np.mean([dose["x"] for dose in doses])),
        "y": float(np.mean([dose["y"] for dose in doses])),
        "mean_pmass": float(np.mean([dose["mean_pmass"] for dose in doses])),
        "min_pmass": float(np.min([dose["min_pmass"] for dose in doses])),
        "entropy": entropy,
        "pmax": pmax,
        "per_item": {
            suffix: {
                "axis": doses[0]["per_item"][suffix]["axis"],
                "pmass": float(np.mean([dose["per_item"][suffix]["pmass"] for dose in doses])),
                "pos": float(np.mean([dose["per_item"][suffix]["pos"] for dose in doses])),
            }
            for suffix in suffixes
        },
        "psamples": {
            suffix: np.concatenate([np.asarray(dose["psamples"][suffix]) for dose in doses]).tolist()
            for suffix in doses[0]["psamples"]
        },
    }


def pooled_by_method(groups: dict[str, list[dict]]) -> dict[str, list[dict]]:
    """Add relative answer mass, using each method's own pooled vanilla mass."""
    pooled = {}
    for method, runs in groups.items():
        doses = [pool_dose(runs, mult) for mult in sorted({d["mult"] for run in runs for d in run["doses"]})]
        base = next(dose for dose in doses if dose["mult"] == 0.0)
        for dose in doses:
            dose["pmass_ratio"] = dose["mean_pmass"] / base["mean_pmass"]
        pooled[method] = doses
    return pooled


def side_path(doses: list[dict], sign: int) -> list[dict]:
    """Traverse vanilla outward, not numeric left-to-right."""
    base = next(dose for dose in doses if dose["mult"] == 0.0)
    side = sorted((dose for dose in doses if np.sign(dose["mult"]) == sign), key=lambda dose: abs(dose["mult"]))
    return [base, *side]


def path_state(path: list[dict]) -> list[str]:
    """Classify a plotted dose without reconnecting after the first failure."""
    states = ["vanilla"]
    crossed_failure = False
    for dose in path[1:]:
        valid = dose["pmass_ratio"] >= PMASS_RATIO_FLOOR
        if not crossed_failure and valid:
            states.append("connected")
        elif not crossed_failure:
            states.append("first_failure")
            crossed_failure = True
        else:
            states.append("recovered_disconnected" if valid else "invalid_disconnected")
    return states


def paired_coordinate_ci(base: dict, dose: dict, resolved: dict) -> tuple[float, float, float, float]:
    """Return saved-sample paired coordinate movement and 95% interval inputs."""
    return coord_delta_ci(
        base["psamples"], dose["psamples"], resolved,
        np.random.default_rng(20_000 + int(100 * dose["mult"])),
    )


def add_path(ax, path: list[dict], sign: int, color: str, scale_x: float, scale_y: float, *, label: str | None,
             dose_labels: bool, resolved: dict | None = None, show_uncertainty: bool = False,
             label_offset: tuple[float, float] = (3, 3)) -> None:
    """Draw a path limited by the answer-mass condition, with signed-coefficient arrows."""
    states = path_state(path)
    if label:
        ax.plot([], [], color=color, lw=2, ls="-" if sign > 0 else "--", label=label)
    for previous, current, state in zip(path, path[1:], states[1:]):
        if state == "first_failure":
            ax.plot(
                [previous["x"] * scale_x, current["x"] * scale_x],
                [previous["y"] * scale_y, current["y"] * scale_y],
                "--", color=color, lw=1.2, alpha=0.35, zorder=3,
            )
            start, end = (previous, current) if sign > 0 else (current, previous)
            ax.add_patch(FancyArrowPatch(
                (start["x"] * scale_x, start["y"] * scale_y),
                (end["x"] * scale_x, end["y"] * scale_y),
                arrowstyle="-|>", mutation_scale=18, linewidth=1.4, linestyle="--", color=color, alpha=0.70, zorder=4,
            ))
            continue
        if state != "connected":
            continue
        start, end = (previous, current) if sign > 0 else (current, previous)
        arrow = FancyArrowPatch(
            (start["x"] * scale_x, start["y"] * scale_y),
            (end["x"] * scale_x, end["y"] * scale_y),
            arrowstyle="-|>", mutation_scale=18, linewidth=2.2, color=color, alpha=0.95, zorder=5,
        )
        ax.add_patch(arrow)
    for dose, state in zip(path, states):
        x, y = dose["x"] * scale_x, dose["y"] * scale_y
        if state in {"vanilla", "connected"}:
            ax.scatter(x, y, s=26 if state == "vanilla" else 20, color=color, zorder=6)
        elif state == "first_failure":
            ax.scatter(x, y, s=34, facecolors="none", edgecolors=color, linewidths=1.4, alpha=0.48, zorder=5)
        else:
            ax.scatter(x, y, s=28, marker="s", facecolors="none", edgecolors=color, linewidths=1.2, alpha=0.45, zorder=4)
        if dose_labels:
            text = "vanilla" if dose["mult"] == 0.0 else f"{dose['mult']:+g}C"
            ax.annotate(text, (x, y), xytext=label_offset, textcoords="offset points", fontsize=6.3, color=color)



def matched_random(groups: dict[str, list[dict]]) -> dict[float, tuple[float, int]]:
    """Apply the answer-mass condition to each random seed before calculating the null."""
    values: dict[float, list[float]] = {}
    for run in groups.get("random", []):
        base = next(dose for dose in run["doses"] if dose["mult"] == 0.0)
        for dose in run["doses"]:
            if dose["mult"] == 0.0 or dose["mean_pmass"] / base["mean_pmass"] < PMASS_RATIO_FLOOR:
                continue
            values.setdefault(dose["mult"], []).append(float(np.hypot(dose["x"] - base["x"], dose["y"] - base["y"])))
    return {mult: (float(np.quantile(moves, 0.95)), len(moves)) for mult, moves in values.items()}


def dose_row(method: str, dose: dict, base: dict, resolved: dict, null: dict[float, tuple[float, int]],
             order: int, state: str) -> list[str]:
    """Compute a complete, saved-artifact-only table row."""
    dx, dy, dx_se, dy_se = coord_delta_ci(
        base["psamples"], dose["psamples"], resolved, np.random.default_rng(20_000 + int(100 * dose["mult"]))
    )
    worst, loo_move = loo_worst(dose, base, resolved)
    move = float(np.hypot(dx, dy))
    random_p95, random_n = null.get(dose["mult"], (np.nan, 0))
    comparison = "-" if random_n == 0 or state != "connected" else ("yes" if move > random_p95 else "no")
    return [
        method, str(order), f"{dose['mult']:+g}C", state.replace("_", " "),
        f"{dose['pmass_ratio']:.3f}", f"{dose['entropy']:.3f}", f"{dose['pmax']:.3f}",
        f"{dx:+.3f} +/- {1.96 * dx_se:.3f}", f"{dy:+.3f} +/- {1.96 * dy_se:.3f}",
        f"{move:.3f}", f"{loo_move:.3f}", f"{random_p95:.3f}" if random_n else "-",
        str(random_n) if random_n else "-", comparison, worst or "-",
    ]


def render_table(pooled: dict[str, list[dict]], groups: dict[str, list[dict]], resolved: dict) -> str:
    """Write all shown observations, including failed and disconnected ones."""
    null = matched_random(groups)
    headers = [
        "method", "order", "dose", "path state", "pmass/base", "entropy", "max p",
        "dx (95%)", "dy (95%)", "move", "LOO move", "random p95", "random n", "beats matched random?", "worst item",
    ]
    sections = [
        "# Qwen3-14B saved WVS steering replot",
        "",
        "Filled path points satisfy pooled `pmass(dose) / pmass(vanilla) >= 0.96`. The first failure is hollow and reached by a faint dashed segment. Later observations can recover answer mass, but remain disconnected from that signed path.",
        "",
        "`entropy` is normalized entropy over allowed answer tokens. `max p` is the mean maximum allowed-answer probability. Coordinate intervals pair vanilla and dose samples. Random p95 uses only random directions whose own answer mass passes the same relative rule; `-` means no matched random control passed.",
    ]
    for method in MAIN_METHODS:
        if method not in pooled:
            continue
        rows = []
        base = next(dose for dose in pooled[method] if dose["mult"] == 0.0)
        for sign, title in ((1, "intended honest-persona direction (+)"), (-1, "intended dishonest-persona direction (-)")):
            path = side_path(pooled[method], sign)
            signed_order = {id(dose): order for order, dose in enumerate(path if sign > 0 else reversed(path))}
            for dose, state in zip(path[1:], path_state(path)[1:]):
                rows.append(dose_row(method, dose, base, resolved, null, signed_order[id(dose)], state))
            sections.extend(["", f"## {method}: {title}", "", tabulate(rows[-(len(path) - 1):], headers=headers, tablefmt="pipe", disable_numparse=True)])
    random_rows = []
    for mult, (p95, n) in sorted(null.items()):
        random_rows.append([f"{mult:+g}C", f"{p95:.3f}", n])
    sections.extend(["", "## Dose-matched random controls", "", tabulate(random_rows, headers=["dose", "movement p95", "coherent n"], tablefmt="pipe")])
    per_seed_rows = []
    for method in MAIN_METHODS:
        for run in groups[method]:
            base = next(dose for dose in run["doses"] if dose["mult"] == 0.0)
            for dose in sorted((dose for dose in run["doses"] if dose["mult"] != 0.0), key=lambda dose: dose["mult"]):
                ratio = dose["mean_pmass"] / base["mean_pmass"]
                per_seed_rows.append([method, run["seed"], f"{dose['mult']:+g}C", f"{ratio:.3f}", "pass" if ratio >= PMASS_RATIO_FLOOR else "fail"])
    sections.extend([
        "", "## Per-seed answer-mass evidence", "",
        "The figure follows the specified pooled condition. This audit table retains each saved seed so a pooled pass cannot hide disagreement.", "",
        tabulate(per_seed_rows, headers=["method", "seed", "dose", "pmass/base", "per-seed result"], tablefmt="pipe"),
    ])
    return "\n".join(sections) + "\n"


def random_passing_points(groups: dict[str, list[dict]]) -> tuple[np.ndarray, np.ndarray]:
    """Return saved random observations that individually pass their own 0.96 mass condition."""
    xs, ys = [], []
    for run in groups["random"]:
        base = next(dose for dose in run["doses"] if dose["mult"] == 0.0)
        for dose in run["doses"]:
            if dose["mult"] and dose["mean_pmass"] / base["mean_pmass"] >= PMASS_RATIO_FLOOR:
                xs.append(dose["x"])
                ys.append(dose["y"])
    return np.asarray(xs), np.asarray(ys)


def add_random_zone(ax, groups: dict[str, list[dict]], scale_x: float, scale_y: float) -> None:
    """Show the saved random reference observations without implying a matched-dose null."""
    xs, ys = random_passing_points(groups)
    ax.scatter(xs * scale_x, ys * scale_y, s=15, color="#777777", alpha=0.12, marker="s", zorder=1,
               label="saved random directions, individual pmass-passing doses")


def map_axes(runs: list[dict], pooled: dict[str, list[dict]], *, title: str, note: str):
    """Create the culture map and include all saved plotted observations in its limits."""
    resolved = resolve_items(load_wvs_all())
    countries, positions = human_axis_scores(resolved)
    zones, emphasize = zones_for(countries)
    scale_x, scale_y = maps.orient_geographic(positions, countries, zones)
    base = next(dose for dose in pooled["vjp_delta"] if dose["mult"] == 0.0)
    figure = maps.plot_value_map(
        "WVS Inglehart-Welzel", countries, positions,
        ("Survival", "Self-expression", "Traditional", "Secular-Rational"),
        models={"Qwen3-14B vanilla": (base["x"], base["y"])}, emphasize=emphasize,
        title=title, note=note, title_y=0.115, note_y=0.04,
    )
    ax = figure.axes[0]
    all_x = [*list(positions[:, 0] * scale_x)]
    all_y = [*list(positions[:, 1] * scale_y)]
    for doses in pooled.values():
        all_x.extend(dose["x"] * scale_x for dose in doses)
        all_y.extend(dose["y"] * scale_y for dose in doses)
    pad_x = max(0.15, 0.15 * (max(all_x) - min(all_x)))
    pad_y = max(0.15, 0.15 * (max(all_y) - min(all_y)))
    ax.set_xlim(min(all_x) - pad_x, max(all_x) + pad_x)
    ax.set_ylim(min(all_y) - pad_y, max(all_y) + pad_y)
    return figure, ax, resolved, scale_x, scale_y


def save_figure(figure, out: Path) -> None:
    """Write stable PNG/SVG outputs, removing renderer-only trailing spaces from SVG."""
    figure.savefig(out, dpi=200)
    svg = out.with_suffix(".svg")
    figure.savefig(svg)
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")


def render_main(runs: list[dict], pooled: dict[str, list[dict]], groups: dict[str, list[dict]], out: Path) -> None:
    """Render all saved real methods with separately traversed signed paths."""
    figure, ax, resolved, scale_x, scale_y = map_axes(
        runs, pooled, title="Saved WVS steering paths, Qwen3-14B",
        note="",
    )
    offsets = {"vjp_delta": (3, 4), "mean_diff": (3, -8), "pca": (3, 10)}
    add_random_zone(ax, groups, scale_x, scale_y)
    for method in MAIN_METHODS:
        if method not in pooled:
            continue
        for sign, name in ((1, "intended honest-persona direction"), (-1, "intended dishonest-persona direction")):
            label = f"{method}: {name} ({'+' if sign == 1 else '-'})"
            add_path(ax, side_path(pooled[method], sign), sign, COLORS[method], scale_x, scale_y,
                     label=label, dose_labels=method == "vjp_delta", resolved=resolved,
                     show_uncertainty=False, label_offset=offsets[method])
    ax.set_position([0.06, 0.10, 0.88, 0.82])
    ax.legend(loc="upper right", bbox_to_anchor=(0.99, 0.99), fontsize=6.3, framealpha=0.88)
    out.parent.mkdir(parents=True, exist_ok=True)
    save_figure(figure, out)
    plt.close(figure)


def metric_path(ax, path: list[dict], sign: int, value: str, color: str, *, label: str | None) -> None:
    """Plot diagnostics with the same answer-mass condition and signed-coefficient arrows."""
    states = path_state(path)
    for previous, current, state in zip(path, path[1:], states[1:]):
        if state == "first_failure":
            ax.plot([previous["mult"], current["mult"]], [previous[value], current[value]], "--", color=color, alpha=0.35)
            start, end = (previous, current) if sign > 0 else (current, previous)
            ax.add_patch(FancyArrowPatch(
                (start["mult"], start[value]), (end["mult"], end[value]),
                arrowstyle="-|>", mutation_scale=8, linewidth=1.0, linestyle="--", color=color, alpha=0.45,
            ))
        elif state == "connected":
            start, end = (previous, current) if sign > 0 else (current, previous)
            ax.add_patch(FancyArrowPatch(
                (start["mult"], start[value]), (end["mult"], end[value]),
                arrowstyle="-|>", mutation_scale=10, linewidth=1.7, color=color,
            ))
    for dose, state in zip(path, states):
        if state in {"vanilla", "connected"}:
            ax.scatter(dose["mult"], dose[value], color=color, s=28, zorder=3)
        elif state == "first_failure":
            ax.scatter(dose["mult"], dose[value], facecolors="none", edgecolors=color, s=38, alpha=0.55, zorder=3)
        else:
            ax.scatter(dose["mult"], dose[value], marker="s", facecolors="none", edgecolors=color, s=31, alpha=0.55, zorder=3)
    ax.plot([], [], color=color, label=label)


def render_vjp(runs: list[dict], pooled: dict[str, list[dict]], groups: dict[str, list[dict]], out: Path) -> None:
    """Render a readable VJP-only map plus answer-mass and saturation diagnostics."""
    figure, ax, resolved, scale_x, scale_y = map_axes(
        runs, pooled, title="VJP delta, saved Qwen3-14B WVS observations", note="",
    )
    figure.set_size_inches(16, 8)
    ax.set_position([0.04, 0.12, 0.56, 0.79])
    positive = side_path(pooled["vjp_delta"], 1)
    negative = side_path(pooled["vjp_delta"], -1)
    add_random_zone(ax, groups, scale_x, scale_y)
    positive_color, negative_color = "#147d64", "#a13a3a"
    add_path(ax, positive, 1, positive_color, scale_x, scale_y, label="intended honest-persona direction (+)",
             dose_labels=True, resolved=resolved, show_uncertainty=False)
    add_path(ax, negative, -1, negative_color, scale_x, scale_y, label="intended dishonest-persona direction (-)",
             dose_labels=True, resolved=resolved, show_uncertainty=False, label_offset=(4, -9))
    ax.annotate("first negative failure: -0.5C", xy=(negative[1]["x"] * scale_x, negative[1]["y"] * scale_y),
                xytext=(18, -20), textcoords="offset points", fontsize=7, arrowprops={"arrowstyle": "-", "color": "#555555"})
    ax.annotate("later recovery observations\n(disconnected)", xy=(negative[-1]["x"] * scale_x, negative[-1]["y"] * scale_y),
                xytext=(8, 18), textcoords="offset points", fontsize=7, arrowprops={"arrowstyle": "-", "color": "#555555"})
    ax.legend(loc="lower left", bbox_to_anchor=(0.01, 0.01), fontsize=6.2, framealpha=0.88)

    pmass_ax = figure.add_axes([0.68, 0.58, 0.28, 0.28])
    metric_path(pmass_ax, positive, 1, "pmass_ratio", positive_color, label="intended honest (+)")
    metric_path(pmass_ax, negative, -1, "pmass_ratio", negative_color, label="intended dishonest (-)")
    pmass_ax.axhline(PMASS_RATIO_FLOOR, color="#aa3333", ls="--", lw=1, label="0.96 threshold")
    pmass_ax.set(title="Relative answer mass", xlabel="signed dose (C)", ylabel="pmass / vanilla", ylim=(0.55, 1.05))
    pmass_ax.legend(fontsize=6, loc="lower right")
    pmass_ax.annotate("-0.5C fails", xy=(-0.5, negative[1]["pmass_ratio"]), xytext=(-1.9, 0.66), fontsize=6.5,
                      arrowprops={"arrowstyle": "->", "color": "#555555"})

    saturation_ax = figure.add_axes([0.68, 0.16, 0.28, 0.28])
    metric_path(saturation_ax, positive, 1, "entropy", "#4c78a8", label="entropy")
    metric_path(saturation_ax, negative, -1, "entropy", "#4c78a8", label=None)
    max_ax = saturation_ax.twinx()
    metric_path(max_ax, positive, 1, "pmax", "#e45756", label="max p")
    metric_path(max_ax, negative, -1, "pmax", "#e45756", label=None)
    saturation_ax.set(title="Allowed-answer saturation", xlabel="signed dose (C)", ylabel="normalized entropy", ylim=(-0.02, 1.05))
    max_ax.set(ylabel="mean maximum answer probability", ylim=(-0.02, 1.05))
    saturation_ax.annotate("-2C: low entropy, high max p", xy=(-2, negative[-1]["entropy"]), xytext=(-1.9, 0.42), fontsize=6.5,
                           arrowprops={"arrowstyle": "->", "color": "#555555"})

    out.parent.mkdir(parents=True, exist_ok=True)
    save_figure(figure, out)
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=Path, default=Path("outputs"))
    parser.add_argument("--out", type=Path, default=Path("docs/img/wvs/wvs_steer_honesty_qwen3_14b.png"))
    parser.add_argument("--table", type=Path, default=None)
    args = parser.parse_args()

    runs = [json.loads(path.read_text()) for path in sorted(args.runs.glob("wvs_steer_*.json"))]
    assert runs, f"no wvs_steer_*.json below {args.runs}"
    assert {run["model"] for run in runs} == {"Qwen/Qwen3-14B"}, "saved replot must not mix models"
    groups = {method: sorted([run for run in runs if run["method"] == method], key=lambda run: run["seed"])
              for method in sorted({run["method"] for run in runs})}
    assert all(method in groups for method in MAIN_METHODS), f"missing expected methods: {set(MAIN_METHODS) - set(groups)}"
    assert "random" in groups, "missing random control artifacts"
    pooled = pooled_by_method(groups)
    table_path = args.table or args.out.with_suffix(".md")
    resolved = resolve_items(load_wvs_all())
    table_path.parent.mkdir(parents=True, exist_ok=True)
    table_path.write_text(render_table(pooled, groups, resolved))
    render_main(runs, pooled, groups, args.out)
    render_vjp(runs, pooled, groups, args.out.with_name(args.out.stem + "_vjp.png"))
    logger.info(f"wrote {args.out}, {args.out.with_suffix('.svg')}, {table_path}")
    logger.info(f"wrote {args.out.with_name(args.out.stem + '_vjp.png')}")


if __name__ == "__main__":
    main()
