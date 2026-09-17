#!/usr/bin/env python3
"""Preregister a response-wording-only direct-choice control for Gemini WVS items."""
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from moralmaps.read_direct_choice import _plan, direct_choice_protocol_identity, read_items_direct_choice
from wvs_direct_choice_pilot import (
    CATALOG_PATH,
    CONCURRENCY,
    GLOBAL_STOP_USD,
    MAX_TOKENS,
    MODEL,
    PRIORITY_PHASE_STOP_USD,
    REASONING,
    REQUEST_TIMEOUT,
    STRUCTURED_OUTPUT,
    catalog_model,
    selected_items,
    usage_cost,
)

ITEM_IDS = ("Homosexuality", "Religion")
SAMPLES_PER_ORDER = 12
TEMPERATURE = 1.0
EXPECTED_INITIAL_CALLS = len(ITEM_IDS) * SAMPLES_PER_ORDER * 2
PILOT_CONSERVATIVE_RESERVE_USD = Decimal("1.50")
PREVIOUS_DIRECT_LEDGER = Path("slop/research/wvs/20260917_direct_choice/gemini37_direct_choice_requests.jsonl")
RECORDS_PATH = Path("slop/research/wvs/20260917_direct_choice/gemini37_direct_choice_anchor_requests.jsonl")
CACHE_PATH = Path("slop/research/wvs/20260917_direct_choice/gemini37_direct_choice_anchor_cache.json")
MANIFEST_PATH = Path("slop/research/wvs/20260917_direct_choice/gemini37_direct_choice_anchor_manifest.md")

ANSWER_INSTRUCTION = (
    "Respond with ONLY a JSON object with exactly one key named answer. "
    "Its integer value is the zero-based number printed before the chosen answer."
)
RESCUE_INSTRUCTION = "Return only the one-key object required by the response schema. No explanation."


def utc_date(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, UTC).date().isoformat()


def items() -> list[dict]:
    all_items = {item["id"]: item for item in selected_items()}
    assert set(ITEM_IDS) <= set(all_items)
    return [all_items[item_id] for item_id in ITEM_IDS]


def protocol_id(pilot_items: list[dict]) -> str:
    return direct_choice_protocol_identity(
        MODEL, pilot_items, samples_per_order=SAMPLES_PER_ORDER, temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS, concurrency=CONCURRENCY, request_timeout=REQUEST_TIMEOUT,
        reasoning=REASONING, structured_output=STRUCTURED_OUTPUT,
        answer_instruction=ANSWER_INSTRUCTION, rescue_instruction=RESCUE_INSTRUCTION,
    )


def preflight(pilot_items: list[dict], model: dict) -> dict:
    assert EXPECTED_INITIAL_CALLS == 48
    assert all(item["n"] >= 2 for item in pilot_items)
    rated_cost = usage_cost(Path("slop/research/wvs/20260916_openrouter/wvs_iw_requests.jsonl"))
    prior_direct_cost = usage_cost(PREVIOUS_DIRECT_LEDGER)
    anchor_cost = usage_cost(RECORDS_PATH)
    cumulative_cost = rated_cost + prior_direct_cost + anchor_cost
    assert cumulative_cost + PILOT_CONSERVATIVE_RESERVE_USD < PRIORITY_PHASE_STOP_USD
    assert cumulative_cost + PILOT_CONSERVATIVE_RESERVE_USD < GLOBAL_STOP_USD
    output_price_per_million = Decimal(model["pricing"]["completion"]) * 1_000_000
    initial_ceiling = output_price_per_million * EXPECTED_INITIAL_CALLS * MAX_TOKENS / 1_000_000
    all_rescue_ceiling = initial_ceiling + output_price_per_million * EXPECTED_INITIAL_CALLS * max(MAX_TOKENS, 2048) / 1_000_000
    return {
        "rated_cost": rated_cost,
        "prior_direct_cost": prior_direct_cost,
        "anchor_cost": anchor_cost,
        "cumulative_cost": cumulative_cost,
        "output_price_per_million": output_price_per_million,
        "initial_ceiling": initial_ceiling,
        "all_rescue_ceiling": all_rescue_ceiling,
        "protocol_id": protocol_id(pilot_items),
    }


def write_manifest(pilot_items: list[dict], model: dict, checks: dict) -> None:
    names = ", ".join(f"`{item['id']}`" for item in pilot_items)
    lines = [
        "# Gemini 3.7 Flash direct-choice response-wording control",
        "",
        "This separate construct pilot changes only the response wording from task 1628. It is not a map panel and cannot alter rated coordinates.",
        "",
        "## Exact identity",
        "",
        f"- model: `{MODEL}`; saved-catalog created UTC: {utc_date(model['created'])}",
        f"- protocol ID: `{checks['protocol_id']}`",
        f"- cache: `{CACHE_PATH}`",
        f"- append-only request ledger: `{RECORDS_PATH}`",
        f"- items: {names}",
        f"- {SAMPLES_PER_ORDER} canonical + {SAMPLES_PER_ORDER} reversed orders per item, interleaved canonical then reversed within each repetition",
        f"- expected initial calls and parsed choices: {EXPECTED_INITIAL_CALLS}",
        f"- temperature: {TEMPERATURE}; max tokens: {MAX_TOKENS}; concurrency: {CONCURRENCY}; timeout: {REQUEST_TIMEOUT}s; reasoning: `{json.dumps(REASONING)}`",
        "- strict schema: one required integer key named answer, bounded to the zero-based presented-option range",
        "",
        "## Only changed prompt text",
        "",
        "The question, answer text, order schedule, model, temperature, low reasoning, strict schema, token limit, timeout and rescue accounting match task 1628 for these two items. The initial response wording is now:",
        "",
        f"> {ANSWER_INSTRUCTION}",
        "",
        "The text contains no literal answer value or JSON example. If a rescue is needed, it says only:",
        "",
        f"> {RESCUE_INSTRUCTION}",
        "",
        "## Preregistered operational screen",
        "",
        "For each item, map selected presented indices back to canonical indices. Report canonical and reversed empirical distributions, order total variation, and each half's modal option set. Order TV <=0.25 plus matching modal set for both items is evidence against a large order effect, not proof that direct choice measures a stable personal attitude. Compare each result directly with task 1628's corresponding order-half table. An incomplete item or failed request exits nonzero and leaves no cache entry.",
        "",
        "## Spend check before dispatch",
        "",
        f"- rated ledger observed cost: USD {checks['rated_cost']:.10f}",
        f"- task 1628 direct-choice observed cost: USD {checks['prior_direct_cost']:.10f}",
        f"- this pilot prior observed cost: USD {checks['anchor_cost']:.10f}",
        f"- cumulative observed cost: USD {checks['cumulative_cost']:.10f}",
        f"- current output price: USD {checks['output_price_per_million']:g}/M",
        f"- 48 initial 1024-token completion-only ceiling: USD {checks['initial_ceiling']:.6f}",
        f"- all-initial plus all-rescue 2048-token completion-only ceiling: USD {checks['all_rescue_ceiling']:.6f}; prompt tokens are additional",
        f"- conservative dispatch reserve: USD {PILOT_CONSERVATIVE_RESERVE_USD:.2f}, below USD {PRIORITY_PHASE_STOP_USD} priority and USD {GLOBAL_STOP_USD} global stops",
        "- this manifest authorizes no wider model dispatch.",
        "",
        "-- PI[gpt-5.6-terra]",
        "",
    ]
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text("\n".join(lines))


def smoke(pilot_items: list[dict], checks: dict) -> None:
    old_plan = _plan(pilot_items, SAMPLES_PER_ORDER)
    new_plan = _plan(pilot_items, SAMPLES_PER_ORDER, ANSWER_INSTRUCTION)
    assert len(old_plan) == len(new_plan) == 48
    for old, new in zip(old_plan, new_plan):
        assert old["item_id"] == new["item_id"]
        assert old["sample"] == new["sample"]
        assert old["order_name"] == new["order_name"]
        assert old["presented_order"] == new["presented_order"]
        old_prefix = old["prompt"].split("Respond with ONLY", 1)[0]
        new_prefix = new["prompt"].split("Respond with ONLY", 1)[0]
        assert old_prefix == new_prefix
        assert '{"answer": 0}' not in new["prompt"]
        assert "0 through" not in new["prompt"]
    assert checks["protocol_id"] == protocol_id(pilot_items)
    print("smoke: 2 items x 12 canonical x 12 reversed = 48 requests")
    print("smoke: only response wording differs from task 1628; no literal answer value/example")
    print(f"smoke: distinct protocol {checks['protocol_id']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true", help="make the preregistered paid control calls")
    parser.add_argument("--smoke", action="store_true", help="validate plan and manifest without API calls")
    args = parser.parse_args()
    pilot_items = items()
    model = catalog_model()
    checks = preflight(pilot_items, model)
    if args.run:
        registered = MANIFEST_PATH.read_text()
        assert f"- protocol ID: `{checks['protocol_id']}`" in registered
    else:
        write_manifest(pilot_items, model, checks)
    if args.smoke:
        smoke(pilot_items, checks)
    if not args.run:
        return
    result = read_items_direct_choice(
        MODEL, pilot_items, samples_per_order=SAMPLES_PER_ORDER, temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS, concurrency=CONCURRENCY, request_timeout=REQUEST_TIMEOUT,
        reasoning=REASONING, structured_output=STRUCTURED_OUTPUT,
        records_path=RECORDS_PATH, cache_path=CACHE_PATH,
        answer_instruction=ANSWER_INSTRUCTION, rescue_instruction=RESCUE_INSTRUCTION,
    )
    if result["cached"]:
        print(f"anchor-wording cache hit: protocol={result['protocol_id'][:12]}")
        return
    if not result["complete"]:
        raise RuntimeError(f"incomplete response-wording control: {result['run_id']}; raw evidence is {RECORDS_PATH}")
    print(f"complete response-wording control: {result['run_id']}, protocol={result['protocol_id'][:12]}")


if __name__ == "__main__":
    main()
