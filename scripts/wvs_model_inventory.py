"""Build the checked OpenRouter WVS candidate inventory from one saved catalog response."""
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

TARGET_IDS = (
    "anthropic/claude-fable-5.1",
    "openai/gpt-6-astra",
    "meta/muse-spark-1.3",
    "moonshotai/kimi-k3",
    "thinkingmachines/inkling",
    "deepseek/deepseek-v4.1-flash",
    "z-ai/glm-5.3",
    "z-ai/glm-5.3-flash",
    "google/gemini-3.7-flash",
    "x-ai/grok-4.5",
    "openai/gpt-5.6-sol",
)


def usd_per_million(value: str) -> float:
    return float(value) * 1_000_000


def model_row(model: dict) -> dict:
    pricing = model["pricing"]
    return {
        "id": model["id"],
        "name": model["name"],
        "created": datetime.fromtimestamp(model["created"], UTC).date().isoformat(),
        "input_usd_per_million": usd_per_million(pricing["prompt"]),
        "output_usd_per_million": usd_per_million(pricing["completion"]),
        "supports_temperature": "temperature" in model["supported_parameters"],
        "supports_max_tokens": "max_tokens" in model["supported_parameters"],
        "expiration_date": model["expiration_date"],
    }


def is_direct_qwen(model: dict, checked_at: str) -> bool:
    model_id = model["id"]
    expiration = model["expiration_date"]
    return (
        model_id.startswith("qwen/")
        and ":" not in model_id
        and (expiration is None or expiration >= checked_at)
        and "temperature" in model["supported_parameters"]
        and "max_tokens" in model["supported_parameters"]
    )


def markdown_table(rows: list[dict]) -> str:
    header = "| exact OpenRouter ID | name | created UTC | input USD/M | output USD/M | status |\n"
    rule = "|---|---|---:|---:|---:|---|\n"
    body = "".join(
        f"| `{row['id']}` | {row['name']} | {row['created']} | "
        f"{row['input_usd_per_million']:.6g} | {row['output_usd_per_million']:.6g} | {row['status']} |\n"
        for row in rows
    )
    return header + rule + body


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--checked-at", default="2026-09-16")
    args = parser.parse_args()

    catalog = json.loads(args.catalog.read_text())["data"]
    by_id = {model["id"]: model for model in catalog}
    targets = []
    for model_id in TARGET_IDS:
        if model_id in by_id:
            row = model_row(by_id[model_id])
            row["status"] = "candidate"
            targets.append(row)
        else:
            targets.append({"id": model_id, "name": "not in checked catalog", "created": "",
                            "input_usd_per_million": 0.0, "output_usd_per_million": 0.0,
                            "status": "unavailable"})
    qwen = [model_row(model) for model in catalog if is_direct_qwen(model, args.checked_at)]
    for row in qwen:
        row["status"] = "candidate"
    qwen.sort(key=lambda row: row["created"], reverse=True)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        "# OpenRouter WVS model inventory\n\n"
        f"Checked {args.checked_at} against `{args.catalog}`. Prices are catalog USD per million tokens. "
        "Batch and free aliases are excluded because they duplicate an underlying model. Qwen entries with "
        "an expiration date before the check date are excluded. The remaining direct `qwen/` text-capable "
        "releases are candidates, not evidence that they completed the panel.\n\n"
        "## Requested additions\n\n" + markdown_table(targets) +
        "\n## Direct Qwen candidates\n\n" + markdown_table(qwen) +
        "\nThe catalog did not contain the requested ID when an addition is marked unavailable. No similar ID "
        "was substituted. -- PI[gpt-5.6-terra]\n"
    )
    metadata = {row["id"].split("/", 1)[1]: row for row in targets + qwen if row["status"] == "candidate"}
    args.metadata.write_text(json.dumps({"checked_at": args.checked_at, "models": metadata}, indent=2) + "\n")


if __name__ == "__main__":
    main()
