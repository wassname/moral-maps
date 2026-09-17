"""Check dated/price/structured catalog fields quoted in the WVS family inventory."""
from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

INVENTORY = Path("slop/research/wvs/20260917_openrouter_family_inventory.md")
CATALOG = Path("slop/research/wvs/20260917_openrouter_models.json")
ROW = re.compile(
    r"^\| `(?P<id>[^`]+)` \| (?P<date>\d{4}-\d{2}-\d{2}) \| "
    r"(?P<input>[0-9.]+) \| (?P<output>[0-9.]+) \| (?P<structured>yes|no) \|"
)


def main() -> None:
    catalog = {model["id"]: model for model in json.loads(CATALOG.read_text())["data"]}
    rows = [match.groupdict() for line in INVENTORY.read_text().splitlines() if (match := ROW.match(line))]
    mismatches = []
    for row in rows:
        model = catalog[row["id"]]
        actual = {
            "date": datetime.fromtimestamp(model["created"], UTC).date().isoformat(),
            "input": Decimal(model["pricing"]["prompt"]) * 1_000_000,
            "output": Decimal(model["pricing"]["completion"]) * 1_000_000,
            "structured": "yes" if "structured_outputs" in model["supported_parameters"] else "no",
        }
        expected = {
            "date": row["date"],
            "input": Decimal(row["input"]),
            "output": Decimal(row["output"]),
            "structured": row["structured"],
        }
        if actual != expected:
            mismatches.append({"id": row["id"], "expected": expected, "actual": actual})
    if mismatches:
        raise ValueError(json.dumps(mismatches, default=str, indent=2))
    print(f"validated {len(rows)} inventory date/price/structured rows against {len(catalog)} saved catalog records: 0 mismatches")


if __name__ == "__main__":
    main()
