"""Summarize durable WVS request records without discarding provider billing fields."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

USAGE_FIELDS = (
    "prompt_tokens",
    "completion_tokens",
    "reasoning_tokens",
    "cache_read_input_tokens",
    "cache_write_input_tokens",
    "total_tokens",
    "cost",
)


def sum_usage(records: list[dict]) -> dict[str, float | None]:
    totals: dict[str, float | None] = {}
    for field in USAGE_FIELDS:
        values = [record["usage"][field] for record in records if record["usage"] is not None and field in record["usage"]]
        totals[field] = sum(values) if values else None
    return totals


def format_value(value: float | None) -> str:
    return "unknown" if value is None else f"{value:g}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--model")
    parser.add_argument("--run-id")
    args = parser.parse_args()

    rows = [json.loads(line) for line in args.records.read_text().splitlines()]
    runs = sorted({(row["model"], row["run_id"]) for row in rows if "model" in row and "run_id" in row})
    if args.model is not None:
        runs = [run for run in runs if run[0] == args.model]
    if args.run_id is not None:
        runs = [run for run in runs if run[1] == args.run_id]
    lines = ["# WVS request-ledger audit", "", f"Source: `{args.records}`.", ""]
    for model, run_id in runs:
        records = [row for row in rows if row.get("model") == model and row.get("run_id") == run_id]
        completed = [row for row in records if row["event"] == "request_completed"]
        started = [row for row in records if row["event"] == "request_started"]
        failed = [row for row in records if row["event"] == "request_failed"]
        parsed = [row for row in records if row["event"] == "answer_parsed"]
        item_results = [row for row in records if row["event"] == "item_result"]
        phases = Counter(row["phase"] for row in completed)
        usages = sum_usage(completed)
        generation_ids = sorted({row["response"]["id"] for row in completed if "id" in row["response"]})
        valid = sum(row["parsed"] for row in parsed)
        initial_keys = {(row["item_id"], row["sample"]) for row in started if row["phase"] == "initial"}
        complete = (len(initial_keys) == 144 and len(item_results) == 12 and
                    all(row["valid_samples"] == row["n_samples"] == 12 for row in item_results))
        lines.extend([
            f"## `{model}` run `{run_id}`", "",
            "| metric | value |",
            "|---|---:|",
            f"| dispatched phases | {len(started)} |",
            f"| completed phases | {len(completed)} |",
            f"| initial completed | {phases['initial']} |",
            f"| rescue completed | {phases['rescue']} |",
            f"| failed request phases | {len(failed)} |",
            f"| parsed valid samples | {valid} |",
            f"| distinct initial item/sample keys | {len(initial_keys)} |",
            f"| item results | {len(item_results)} |",
            f"| publication eligible 12 x 12 panel | {complete} |",
            f"| provider generation IDs retained | {len(generation_ids)} |",
            "",
            "| provider usage field | total |",
            "|---|---:|",
            *[f"| {field} | {format_value(usages[field])} |" for field in USAGE_FIELDS],
            "",
        ])
        if generation_ids:
            digest = hashlib.sha256("\n".join(generation_ids).encode()).hexdigest()
            lines.extend([
                "Generation IDs are retained verbatim in the source ledger.", "",
                f"- count: {len(generation_ids)}",
                f"- SHA-256 of sorted IDs: `{digest}`",
                f"- first: `{generation_ids[0]}`",
                f"- last: `{generation_ids[-1]}`",
                "",
            ])
        if failed:
            lines.extend(["Failures retained in the ledger:", "", *[
                f"- {row['phase']}: `{row['error_type']}: {row['error']}`" for row in failed
            ], ""])
        if item_results:
            lines.extend([
                "| item | valid | requested | failed | rescues | parse rate |",
                "|---|---:|---:|---:|---:|---:|",
                *[
                    f"| {row['id']} | {row['valid_samples']} | {row['n_samples']} | "
                    f"{row['failed_samples']} | {row['rescued_samples']} | {row['pmass_allowed']:.3f} |"
                    for row in item_results
                ],
                "",
            ])
    lines.append("Provider `cost` is reported only when the raw OpenRouter usage object exposed it. Missing usage fields are unknown, not zero. -- PI[gpt-5.6-terra]")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
