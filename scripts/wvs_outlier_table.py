"""How much of a cultural outlier each model is, in the SDs of a human macro-zone.

Turns the committed model coordinates (docs/img/wvs/wvs_model_ci.md, written by wvs_map.py) into
docs/img/wvs/wvs_model_outlier_sd.md. Reads the table rather than the coord cache so it reruns
offline, without re-querying seventeen models. The human coordinates are recomputed from WVS here,
the same way wvs_map.py computes them.

  uv run python scripts/wvs_outlier_table.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from loguru import logger
from tabulate import tabulate

from moralmaps.iw_axes import resolve_items
from wvs_map import cluster_outlier_sd, human_axis_scores, load_wvs_all

IMG = Path(__file__).resolve().parent.parent / "docs" / "img" / "wvs"


def read_model_coords(path: Path) -> dict[str, tuple]:
    """(x, y) per model from the pipe-table wvs_map.py writes. Columns: model, x, y, x CI, y CI."""
    models = {}
    for line in path.read_text().splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or cells[0] in ("model", "") or set(cells[1]) <= set(":- "):
            continue
        models[cells[0]] = (float(cells[1]), float(cells[2]))
    return models


def main() -> None:
    models = read_model_coords(IMG / "wvs_model_ci.md")
    countries, P = human_axis_scores(resolve_items(load_wvs_all()))
    logger.info(f"{len(models)} models against {len(countries)} human societies")

    rows = cluster_outlier_sd(countries, P, models)
    west_z = {n: z for n, zone, _, _, z, _ in rows if zone == "West"}
    rows.sort(key=lambda r: (-west_z.get(r[0], 0.0), r[0], r[1]))
    table = tabulate(rows, headers=["model", "zone", "n countries",
                                    "z self-expr", "z secular", "Mahalanobis"],
                     tablefmt="pipe", floatfmt="+.2f")
    (IMG / "wvs_model_outlier_sd.md").write_text(table + "\n")
    logger.info("model distance from human zones, in zone SDs:\n" + table)


if __name__ == "__main__":
    main()
