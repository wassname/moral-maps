"""Plot a 2D honesty-c x credulity-c steering grid.

Consumes a `run_2d_grid_showcase.py` output dir (a combined orthogonalized vector
administered over a 5x5 honesty-c x credulity-c grid across all instruments) and
renders the dream artifact: a grid of small ipsative culture maps, one per (hc, cc)
cell, showing how the model's profile moves as you steer honesty (x-axis) and
credulity (y-axis) independently.

Also renders:
  - a 2D heatmap of per-foundation profile values (one heatmap per foundation)
  - the two single-axis paths (honesty-only and credulity-only) as line plots

  uv run python scripts/plot_2d_grid.py \
    --run-dir ../steering-lite/outputs/20260705_honesty_x_credulity_2d_grid_sspace_allinstr_n8 \
    --out docs/img/showcase/2d_grid \
    --vec-label "Honesty x Credulity"
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import tinymfv as T
from tinymfv.zones import zones_for

ORDINAL = ["mfq2", "big5", "humor_styles"]
FOUNDATION_ORDER = ["care", "fairness", "loyalty", "authority", "sanctity", "liberty"]
_MFV_INSTR = "mfv"
_MFV_YLABEL = "MFV: logit violation (nat, base-relative)"


def _read_grid_csv(path: Path) -> list[dict]:
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def _grid_values(rows: list[dict], value_key: str, foundations: list[str]) -> dict[str, np.ndarray]:
    """{foundation: 2D array [n_hc, n_cc]} of value_key values."""
    hc_vals = sorted(set(float(r["honesty_c"]) for r in rows))
    cc_vals = sorted(set(float(r["credulity_c"]) for r in rows))
    out = {}
    for f in foundations:
        grid = np.full((len(hc_vals), len(cc_vals)), np.nan)
        for r in rows:
            if r["foundation"] != f:
                continue
            hi = hc_vals.index(float(r["honesty_c"]))
            ci = cc_vals.index(float(r["credulity_c"]))
            grid[hi, ci] = float(r[value_key])
        out[f] = grid
    return out, hc_vals, cc_vals


def plot_mfv_grid_maps(run_dir: Path, out: Path, vec_label: str) -> list[Path]:
    """5x5 grid of ipsative culture maps, one per (hc, cc) cell."""
    rows = _read_grid_csv(run_dir / "mfv_profiles.csv")
    # build profile per cell: {foundation: mean} (using dlogit relative to base)
    hc_vals = sorted(set(float(r["honesty_c"]) for r in rows))
    cc_vals = sorted(set(float(r["credulity_c"]) for r in rows))
    founds = sorted(set(r["foundation"] for r in rows))
    profiles = {}
    pmass = {}
    for hc in hc_vals:
        for cc in cc_vals:
            cell_rows = [r for r in rows if float(r["honesty_c"]) == hc and float(r["credulity_c"]) == cc]
            profiles[(hc, cc)] = {r["foundation"]: float(r["mean"]) for r in cell_rows}
            pmass[(hc, cc)] = float(cell_rows[0]["pmass"]) if cell_rows else 0.0

    # base profile for centering
    base_prof = profiles.get((0.0, 0.0), {f: 0.0 for f in founds})

    fig, axes = plt.subplots(len(hc_vals), len(cc_vals), figsize=(3 * len(cc_vals), 3 * len(hc_vals)),
                             squeeze=False)
    for i, hc in enumerate(hc_vals):
        for j, cc in enumerate(cc_vals):
            ax = axes[i][j]
            prof = profiles.get((hc, cc), base_prof)
            vec = np.array([prof.get(f, 0.0) for f in founds])
            # simple bar chart of the profile in this cell
            colors = ["#d44", "#4d4", "#44d", "#dd4", "#d4d", "#4dd"][:len(founds)]
            ax.bar(range(len(founds)), vec, color=colors)
            ax.set_xticks(range(len(founds)))
            ax.set_xticklabels([f[:3] for f in founds], fontsize=7)
            ax.set_title(f"hc={hc:+.1f} cc={cc:+.1f}\npmass={pmass.get((hc,cc),0):.2f}", fontsize=8)
            if i == len(hc_vals) - 1:
                ax.set_xlabel("honesty ->", fontsize=8)
            if j == 0:
                ax.set_ylabel("credulity ^", fontsize=8)
    fig.suptitle(f"MFV profile grid: {vec_label} (dlogit per foundation, base-relative)", fontsize=12)
    fig.tight_layout()
    path = out / "mfv_grid_bars.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return [path]


def plot_ordinal_heatmaps(run_dir: Path, out: Path, name: str, vec_label: str) -> list[Path]:
    """2D heatmaps of per-factor C (logit contrast), one per factor."""
    rows = _read_grid_csv(run_dir / f"{name}_profiles.csv")
    instr = T.get_instrument(name)
    dims = instr.dimensions
    grids, hc_vals, cc_vals = _grid_values(rows, "C", dims)
    n = len(dims)
    ncols = min(4, n)
    nrows = (n + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(4 * ncols, 3.5 * nrows), squeeze=False)
    for idx, dim in enumerate(dims):
        ax = axes[idx // ncols][idx % ncols]
        im = ax.imshow(grids[dim], aspect="auto", origin="lower",
                       extent=[cc_vals[0] - 0.25, cc_vals[-1] + 0.25,
                               hc_vals[0] - 0.25, hc_vals[-1] + 0.25],
                       cmap="RdBu_r", vmin=-abs(grids[dim]).max(), vmax=abs(grids[dim]).max())
        ax.set_title(f"{dim} (C: logit contrast)", fontsize=9)
        ax.set_xlabel("credulity-c", fontsize=8)
        ax.set_ylabel("honesty-c", fontsize=8)
        plt.colorbar(im, ax=ax, shrink=0.8)
    for idx in range(len(dims), nrows * ncols):
        axes[idx // ncols][idx % ncols].set_visible(False)
    fig.suptitle(f"{instr.display}: {vec_label} 2D steer grid", fontsize=11)
    fig.tight_layout()
    path = out / f"{name}_heatmap.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return [path]


def plot_mfv_heatmaps(run_dir: Path, out: Path, vec_label: str) -> list[Path]:
    """2D heatmaps of MFV dlogit per foundation."""
    rows = _read_grid_csv(run_dir / "mfv_profiles.csv")
    founds = FOUNDATION_ORDER
    grids, hc_vals, cc_vals = _grid_values(rows, "dlogit", founds)
    n = len(founds)
    ncols = 3
    nrows = (n + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(4 * ncols, 3.5 * nrows), squeeze=False)
    for idx, f in enumerate(founds):
        ax = axes[idx // ncols][idx % ncols]
        g = grids[f]
        vmax = max(abs(np.nanmin(g)), abs(np.nanmax(g)), 0.1)
        im = ax.imshow(g, aspect="auto", origin="lower",
                       extent=[cc_vals[0] - 0.25, cc_vals[-1] + 0.25,
                               hc_vals[0] - 0.25, hc_vals[-1] + 0.25],
                       cmap="RdBu_r", vmin=-vmax, vmax=vmax)
        ax.set_title(f"{f} (dlogit)", fontsize=9)
        ax.set_xlabel("credulity-c", fontsize=8)
        ax.set_ylabel("honesty-c", fontsize=8)
        plt.colorbar(im, ax=ax, shrink=0.8)
    for idx in range(len(founds), nrows * ncols):
        axes[idx // ncols][idx % ncols].set_visible(False)
    fig.suptitle(f"MFV: {vec_label} 2D steer grid (dlogit per foundation)", fontsize=11)
    fig.tight_layout()
    path = out / "mfv_heatmap.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return [path]


def plot_coherence_grid(run_dir: Path, out: Path, vec_label: str) -> list[Path]:
    """2D heatmap of pmass (coherence) across the grid."""
    rows = _read_grid_csv(run_dir / "mfv_profiles.csv")
    hc_vals = sorted(set(float(r["honesty_c"]) for r in rows))
    cc_vals = sorted(set(float(r["credulity_c"]) for r in rows))
    grid = np.full((len(hc_vals), len(cc_vals)), np.nan)
    for r in rows:
        hi = hc_vals.index(float(r["honesty_c"]))
        ci = cc_vals.index(float(r["credulity_c"]))
        if r["foundation"] == FOUNDATION_ORDER[0]:
            grid[hi, ci] = float(r["pmass"])
    fig, ax = plt.subplots(1, 1, figsize=(5, 4))
    im = ax.imshow(grid, aspect="auto", origin="lower",
                   extent=[cc_vals[0] - 0.25, cc_vals[-1] + 0.25,
                           hc_vals[0] - 0.25, hc_vals[-1] + 0.25],
                   cmap="RdYlGn", vmin=0, vmax=1)
    ax.set_title(f"MFV pmass (coherence): {vec_label}", fontsize=10)
    ax.set_xlabel("credulity-c", fontsize=9)
    ax.set_ylabel("honesty-c", fontsize=9)
    plt.colorbar(im, ax=ax, shrink=0.8)
    fig.tight_layout()
    path = out / "coherence_heatmap.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return [path]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("docs/img/showcase/2d_grid"))
    ap.add_argument("--vec-label", default="Honesty x Credulity")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    summary = json.loads((args.run_dir / "summary.json").read_text())
    cos = summary.get("cosine_before_orth", "?")
    print(f"cosine_before_orth: {cos}")
    print(f"C_a={summary.get('C_a')}, C_b={summary.get('C_b')}")

    written = []
    if (args.run_dir / "mfv_profiles.csv").exists():
        written += [str(p) for p in plot_mfv_grid_maps(args.run_dir, args.out, args.vec_label)]
        written += [str(p) for p in plot_mfv_heatmaps(args.run_dir, args.out, args.vec_label)]
        written += [str(p) for p in plot_coherence_grid(args.run_dir, args.out, args.vec_label)]
    for name in ORDINAL:
        if (args.run_dir / f"{name}_profiles.csv").exists():
            written += [str(p) for p in plot_ordinal_heatmaps(args.run_dir, args.out, name, args.vec_label)]
    print(f"wrote {len(written)} figures under {args.out}:")
    for w in written:
        print(" ", w)


if __name__ == "__main__":
    main()
