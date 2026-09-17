#!/usr/bin/env python3
"""Prepare or run one preregistered direct-choice WVS priority panel."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from moralmaps.read_direct_choice import direct_choice_protocol_identity, read_items_direct_choice
from wvs_direct_choice_pilot import usage_cost
from wvs_direct_choice_production_pilot import (
    ANSWER_INSTRUCTION,
    CONCURRENCY,
    MAX_TOKENS,
    PROMPT_INSTRUCTION,
    REQUEST_TIMEOUT,
    RESCUE_INSTRUCTION,
    TEMPERATURE,
    TOTAL_SAMPLES_PER_ITEM,
    items,
    schedule,
)

CATALOG_PATH = Path("slop/research/wvs/20260917_openrouter_models.json")
MANIFEST_PATH = Path("slop/research/wvs/20260917_direct_choice/priority_direct_choice_manifest.md")
MANIFEST_JSON_PATH = Path("slop/research/wvs/20260917_direct_choice/priority_direct_choice_manifest.json")
DIRECT_DIR = Path("slop/research/wvs/20260917_direct_choice/priority")
RATED_LEDGER = Path("slop/research/wvs/20260916_openrouter/wvs_iw_requests.jsonl")
PHASE_STOP_USD = Decimal("35")
GLOBAL_STOP_USD = Decimal("80")
PROMPT_TOKEN_RESERVE = Decimal("512")

GROUPS = {
    "Grok": ("x-ai/grok-4.6", "x-ai/grok-4.5"),
    "OpenAI": (
        "openai/gpt-5.6-luna", "openai/gpt-5.6-terra", "openai/gpt-5.4-nano",
        "openai/gpt-5.4-mini", "openai/gpt-5.2-chat", "openai/gpt-5.2", "openai/gpt-5.1",
        "openai/gpt-5", "openai/gpt-5-mini", "openai/gpt-oss-120b", "openai/gpt-oss-20b",
        "openai/o3", "openai/o4-mini", "openai/gpt-4.1", "openai/gpt-4.1-mini",
        "openai/gpt-4.1-nano", "openai/o3-mini",
        "openai/gpt-4o-2024-11-20", "openai/gpt-4o-2024-08-06", "openai/gpt-4o-mini",
        "openai/gpt-4o", "openai/gpt-3.5-turbo-0613", "openai/gpt-3.5-turbo-instruct",
        "openai/gpt-3.5-turbo-16k", "openai/gpt-3.5-turbo",
    ),
    "Google": (
        "google/gemini-3.8-flash", "google/gemini-3.6-flash", "google/gemini-3.5-flash-lite",
        "google/gemini-3.5-flash", "google/gemini-3.1-flash-lite", "google/gemma-4-26b-a4b-it",
        "google/gemini-3.1-flash-lite-preview", "google/gemini-3-flash-preview",
        "google/gemini-2.5-flash-lite", "google/gemini-2.5-flash",
    ),
    "Muse": ("meta/muse-spark-1.2", "meta/muse-spark-1.1"),
}


def utc_date(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, UTC).date().isoformat()


def rate_per_million(model: dict, field: str) -> Decimal:
    return Decimal(model["pricing"][field]) * 1_000_000


def reasoning_setting(model: dict) -> tuple[dict | None, str]:
    metadata = model.get("reasoning")
    if metadata is None:
        return None, "not advertised"
    efforts = set(metadata.get("supported_efforts", []))
    if "minimal" in efforts:
        return {"effort": "minimal"}, "minimal"
    if "low" in efforts:
        return {"effort": "low"}, "low"
    if not metadata.get("mandatory") and "none" in efforts:
        return {"enabled": False}, "disabled (optional, none advertised)"
    if not metadata.get("mandatory") and not efforts:
        return None, "not advertised (optional; omitted)"
    raise ValueError(f"no allowed minimal/low reasoning setting for {model['id']}: {metadata}")


def catalog() -> dict[str, dict]:
    return {model["id"]: model for model in json.loads(CATALOG_PATH.read_text())["data"]}


def cache_paths(model_id: str) -> tuple[Path, Path]:
    stem = model_id.replace("/", "__")
    return DIRECT_DIR / f"{stem}_requests.jsonl", DIRECT_DIR / f"{stem}_cache.json"


def observed_cost() -> Decimal:
    paths = [RATED_LEDGER, *Path("slop/research/wvs/20260917_direct_choice").glob("**/*requests.jsonl")]
    return sum((usage_cost(path) for path in paths), Decimal())


def entry(model: dict, pilot_items: list[dict], request_plan: list[dict]) -> dict:
    reasoning, reasoning_label = reasoning_setting(model)
    protocol = direct_choice_protocol_identity(
        model["id"], pilot_items, samples_per_order=10, temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS, concurrency=CONCURRENCY, request_timeout=REQUEST_TIMEOUT,
        reasoning=reasoning, structured_output=True, prompt_instruction=PROMPT_INSTRUCTION,
        answer_instruction=ANSWER_INSTRUCTION, rescue_instruction=RESCUE_INSTRUCTION,
        plan_override=request_plan,
    )
    input_rate = rate_per_million(model, "prompt")
    output_rate = rate_per_million(model, "completion")
    completion_ceiling = output_rate * len(request_plan) * MAX_TOKENS / 1_000_000
    conservative_reserve = (
        len(request_plan)
        * (PROMPT_TOKEN_RESERVE * 2 * input_rate + (MAX_TOKENS + 2048) * output_rate)
        / 1_000_000
    )
    ledger, cache = cache_paths(model["id"])
    return {
        "id": model["id"], "created_utc": utc_date(model["created"]),
        "input_usd_per_million": str(input_rate), "output_usd_per_million": str(output_rate),
        "reasoning": reasoning, "reasoning_label": reasoning_label,
        "structured_output": "structured_outputs" in model["supported_parameters"],
        "protocol_id": protocol, "initial_calls": len(request_plan),
        "completion_only_ceiling_usd": str(completion_ceiling),
        "conservative_reserve_usd": str(conservative_reserve),
        "records_path": str(ledger), "cache_path": str(cache),
    }


def entries() -> list[dict]:
    models = catalog()
    pilot_items = items()
    request_plan = schedule(pilot_items)
    assert len(request_plan) == 240
    output = []
    for group, ids in GROUPS.items():
        for model_id in ids:
            model = models[model_id]
            assert "structured_outputs" in model["supported_parameters"]
            assert rate_per_million(model, "completion") <= Decimal("15")
            output.append({"group": group, **entry(model, pilot_items, request_plan)})
    assert len({row["id"] for row in output}) == len(output)
    assert len({row["protocol_id"] for row in output}) == len(output)
    return output


def write_manifest(priority: list[dict]) -> None:
    catalog_sha = hashlib.sha256(CATALOG_PATH.read_bytes()).hexdigest()
    current_cost = observed_cost()
    manifest = {
        "schema": 1,
        "catalog_path": str(CATALOG_PATH),
        "catalog_sha256": catalog_sha,
        "design": {
            "construct": "direct_choice", "items": 12, "samples_per_item": TOTAL_SAMPLES_PER_ITEM,
            "initial_calls_per_model": 240, "schedule": "balanced_cyclic_rotations",
            "prompt_instruction": PROMPT_INSTRUCTION, "answer_instruction": ANSWER_INSTRUCTION,
            "rescue_instruction": RESCUE_INSTRUCTION, "strict_structured_output": True,
        },
        "stop_usd": {"priority_phase": str(PHASE_STOP_USD), "global": str(GLOBAL_STOP_USD)},
        "current_observed_cost_usd": str(current_cost),
        "prompt_token_reserve_per_phase": str(PROMPT_TOKEN_RESERVE),
        "models": priority,
    }
    MANIFEST_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_JSON_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Direct-choice priority manifest, prepared but not dispatched",
        "",
        "This manifest prepares the reviewed direct-choice protocol for future panels. It queues and authorizes no API request. Dense-rated panels remain a separate legacy/proxy layer and cannot be mixed with these outputs in coordinates, family summaries, or capability fits.",
        "",
        "## Shared direct-choice identity",
        "",
        f"- saved catalog: `{CATALOG_PATH}`, SHA-256 `{catalog_sha}`",
        "- 12 WVS items x 20 samples/item = 240 initial requests/model",
        "- deterministic balanced cyclic rotations: exact option-position balance for n=2,4,10 and registered nearest 6/7 balance for n=3",
        f"- prompt: `{PROMPT_INSTRUCTION}`",
        f"- final response: `{ANSWER_INSTRUCTION}`",
        f"- rescue response: `{RESCUE_INSTRUCTION}`",
        "- strict structured output; each model has an isolated append-only ledger, cache, and model-specific protocol ID",
        "",
        "## Spend checks before any later dispatch",
        "",
        f"- observed provider cost across current rated and direct-choice ledgers: USD {current_cost:.11f}",
        f"- priority phase hard stop: USD {PHASE_STOP_USD}; global hard stop: USD {GLOBAL_STOP_USD}",
        f"- per-model reserve assumes 240 initial 1024-token completions plus 240 possible 2048-token rescues and {PROMPT_TOKEN_RESERVE} prompt tokens per phase; it is a pre-dispatch limit, not an observed cost",
        "- the runner refuses a new model if current observed ledger cost plus its reserve reaches either stop",
        "- no model below is dispatched by this commit",
        "",
        "## Ordered panels",
        "",
        "The order is Grok, OpenAI, Google, then Muse. `minimal` is used when catalog metadata advertises it; otherwise `low`; disabled is used only when the catalog says reasoning is optional and accepts `none`.",
        "",
        "| family | exact ID | created UTC | input USD/M | output USD/M | reasoning | structured | protocol ID | calls | completion-only ceiling | conservative reserve | isolated ledger |",
        "|---|---|---:|---:|---:|---|---|---|---:|---:|---:|---|",
    ]
    for row in priority:
        lines.append(
            f"| {row['group']} | `{row['id']}` | {row['created_utc']} | {Decimal(row['input_usd_per_million']):g} | "
            f"{Decimal(row['output_usd_per_million']):g} | `{json.dumps(row['reasoning'])}` ({row['reasoning_label']}) | "
            f"{'yes' if row['structured_output'] else 'no'} | `{row['protocol_id']}` | {row['initial_calls']} | "
            f"USD {Decimal(row['completion_only_ceiling_usd']):.4f} | USD {Decimal(row['conservative_reserve_usd']):.4f} | `{row['records_path']}` |"
        )
    lines.extend([
        "",
        "## Exclusions",
        "",
        "- Already plotted dense-rated IDs are not repeated in this prepared direct-choice list, including Grok 4.3/4.20, GPT-6 Astra, GPT-5.6 Sol, GPT-5.5, GPT-5.4, GPT-5.3 Chat, Gemini 3.7 Flash, Gemini 2.5 Pro, and Muse 1.3.",
        "- GPT-5 Nano is retained as a completed dense-rated protocol diagnostic, not silently relabelled as a direct-choice panel.",
        "- Pro/Fast, batch/free aliases, output price above USD 15/M, and code/image/audio/safeguard/multi-agent entries remain excluded. `Flash` is included where it is a general chat model.",
        "- `openai/o4-mini-high` and `openai/o3-mini-high` are excluded because their catalog entries advertise only `high` reasoning, not the registered minimal/low policy.",
        "- The deferred Qwen/GLM/Mistral shortlist remains outside this priority manifest until a direct-choice expansion decision is made.",
        "",
        "## Later execution only after review",
        "",
        "`scripts/wvs_direct_choice_priority.py --model <exact-id> --smoke` validates one saved entry without network requests. The corresponding `--run` is intentionally not invoked or queued here; it requires a reviewed manifest match and the spend checks above.",
        "",
        "-- PI[gpt-5.6-terra]",
        "",
    ])
    MANIFEST_PATH.write_text("\n".join(lines))


def preflight(model_id: str) -> dict:
    priority = {row["id"]: row for row in entries()}
    row = priority[model_id]
    saved = json.loads(MANIFEST_JSON_PATH.read_text())
    saved_row = next(entry for entry in saved["models"] if entry["id"] == model_id)
    assert saved_row == row
    assert saved["catalog_sha256"] == hashlib.sha256(CATALOG_PATH.read_bytes()).hexdigest()
    current_cost = observed_cost()
    reserve = Decimal(row["conservative_reserve_usd"])
    assert current_cost + reserve < PHASE_STOP_USD
    assert current_cost + reserve < GLOBAL_STOP_USD
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-manifest", action="store_true")
    parser.add_argument("--model", choices=[model_id for ids in GROUPS.values() for model_id in ids])
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--run", action="store_true", help="make paid calls only after a separate review")
    args = parser.parse_args()
    if args.write_manifest:
        write_manifest(entries())
        print(f"wrote {MANIFEST_PATH} and {MANIFEST_JSON_PATH}")
    if args.model is None:
        assert not args.smoke and not args.run
        return
    row = preflight(args.model)
    if args.smoke:
        print(f"smoke: {row['id']}, 240 direct-choice requests, protocol={row['protocol_id']}")
        print(f"smoke: reasoning={row['reasoning']}, reserve=USD {row['conservative_reserve_usd']}")
    if not args.run:
        return
    request_plan = schedule(items())
    records_path, cache_path = cache_paths(args.model)
    result = read_items_direct_choice(
        args.model, items(), samples_per_order=10, temperature=TEMPERATURE, max_tokens=MAX_TOKENS,
        concurrency=CONCURRENCY, request_timeout=REQUEST_TIMEOUT, reasoning=row["reasoning"],
        structured_output=True, records_path=records_path, cache_path=cache_path,
        prompt_instruction=PROMPT_INSTRUCTION, answer_instruction=ANSWER_INSTRUCTION,
        rescue_instruction=RESCUE_INSTRUCTION, plan_override=request_plan,
    )
    if result["cached"]:
        print(f"priority direct-choice cache hit: {args.model}, protocol={result['protocol_id'][:12]}")
        return
    if not result["complete"]:
        raise RuntimeError(f"incomplete priority direct-choice panel: {result['run_id']}; evidence is {records_path}")
    print(f"complete priority direct-choice panel: {args.model}, run={result['run_id']}")


if __name__ == "__main__":
    main()
