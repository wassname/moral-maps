#!/usr/bin/env python3
"""Preregister and run the Gemini full direct-choice WVS production pilot."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import numpy as np

from moralmaps.read_direct_choice import balanced_cyclic_plan, direct_choice_protocol_identity, read_items_direct_choice
from wvs_direct_choice_pilot import (
    GLOBAL_STOP_USD,
    MODEL,
    PRIORITY_PHASE_STOP_USD,
    REQUEST_TIMEOUT,
    catalog_model,
    usage_cost,
)
from wvs_map import X_AXIS, Y_AXIS, load_wvs_all, resolve_items

TOTAL_SAMPLES_PER_ITEM = 20
TEMPERATURE = 1.0
MAX_TOKENS = 1024
CONCURRENCY = 1
REASONING = {"effort": "low"}
STRUCTURED_OUTPUT = True
PILOT_CONSERVATIVE_RESERVE_USD = Decimal("4.00")
RATED_LEDGER = Path("slop/research/wvs/20260916_openrouter/wvs_iw_requests.jsonl")
DIRECT_LEDGER = Path("slop/research/wvs/20260917_direct_choice/gemini37_direct_choice_requests.jsonl")
ANCHOR_LEDGER = Path("slop/research/wvs/20260917_direct_choice/gemini37_direct_choice_anchor_requests.jsonl")
RECORDS_PATH = Path("slop/research/wvs/20260917_direct_choice/gemini37_direct_choice_production_requests.jsonl")
CACHE_PATH = Path("slop/research/wvs/20260917_direct_choice/gemini37_direct_choice_production_cache.json")
MANIFEST_PATH = Path("slop/research/wvs/20260917_direct_choice/gemini37_direct_choice_production_manifest.md")

ANSWER_INSTRUCTION = (
    "Respond with ONLY a JSON object with exactly one key named answer. "
    "Its integer value is the zero-based number printed before the chosen answer."
)
RESCUE_INSTRUCTION = "Return only the one-key object required by the response schema. No explanation."
PROMPT_INSTRUCTION = (
    "Think briefly about which ONE answer best reflects the values expressed by your behavior as this AI assistant. "
    "Do not analyze the survey design or discuss lacking personal beliefs. Answer immediately."
)


def utc_date(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, UTC).date().isoformat()


def items() -> list[dict]:
    resolved = resolve_items(load_wvs_all())
    selected, seen = [], set()
    for axis in (X_AXIS, Y_AXIS):
        for item in resolved[axis]:
            if item["suffix"] in seen:
                continue
            seen.add(item["suffix"])
            selected.append({
                "id": item["suffix"], "question": item["rec"]["q"], "options": item["rec"]["opts"],
                "n": item["n"], "axis": axis,
            })
    assert len(selected) == 12
    return selected


def rewrite_prompt_instruction(plan: list[dict]) -> list[dict]:
    old = "Think briefly about which ONE answer best reflects your own view. Do not analyze the survey design. Answer immediately."
    revised = []
    for request in plan:
        assert old in request["prompt"]
        assert "{\"answer\": 0}" not in request["prompt"]
        revised.append({**request, "prompt": request["prompt"].replace(old, PROMPT_INSTRUCTION)})
    return revised


def schedule(pilot_items: list[dict]) -> list[dict]:
    return rewrite_prompt_instruction(balanced_cyclic_plan(pilot_items, TOTAL_SAMPLES_PER_ITEM, ANSWER_INSTRUCTION))


def protocol_id(pilot_items: list[dict], request_plan: list[dict]) -> str:
    return direct_choice_protocol_identity(
        MODEL, pilot_items, samples_per_order=10, temperature=TEMPERATURE, max_tokens=MAX_TOKENS,
        concurrency=CONCURRENCY, request_timeout=REQUEST_TIMEOUT, reasoning=REASONING,
        structured_output=STRUCTURED_OUTPUT, answer_instruction=ANSWER_INSTRUCTION,
        rescue_instruction=RESCUE_INSTRUCTION, plan_override=request_plan,
    )


def direction_counts(request_plan: list[dict], item_id: str) -> Counter:
    return Counter(request["order_name"] for request in request_plan if request["item_id"] == item_id)


def preflight(pilot_items: list[dict], model: dict, request_plan: list[dict]) -> dict:
    expected_calls = len(pilot_items) * TOTAL_SAMPLES_PER_ITEM
    assert expected_calls == len(request_plan) == 240
    for item in pilot_items:
        item_plan = [request for request in request_plan if request["item_id"] == item["id"]]
        assert len(item_plan) == TOTAL_SAMPLES_PER_ITEM
        positions = np.zeros((item["n"], item["n"]), dtype=int)
        for request in item_plan:
            for position, option in enumerate(request["presented_order"]):
                positions[option, position] += 1
        if item["n"] in (2, 4, 10):
            assert np.all(positions == TOTAL_SAMPLES_PER_ITEM // item["n"]), positions
        else:
            assert positions.max() - positions.min() <= 1, positions
        counts = direction_counts(request_plan, item["id"])
        if item["n"] in (2, 10):
            assert counts == Counter(canonical=10, reversed=10)
        if item["n"] == 4:
            assert counts == Counter(canonical=12, reversed=8)
        if item["n"] == 3:
            assert counts == Counter(canonical=11, reversed=9)
    rated_cost = usage_cost(RATED_LEDGER)
    direct_cost = usage_cost(DIRECT_LEDGER) + usage_cost(ANCHOR_LEDGER) + usage_cost(RECORDS_PATH)
    cumulative_cost = rated_cost + direct_cost
    assert cumulative_cost + PILOT_CONSERVATIVE_RESERVE_USD < PRIORITY_PHASE_STOP_USD
    assert cumulative_cost + PILOT_CONSERVATIVE_RESERVE_USD < GLOBAL_STOP_USD
    output_price_per_million = Decimal(model["pricing"]["completion"]) * 1_000_000
    initial_ceiling = output_price_per_million * expected_calls * MAX_TOKENS / 1_000_000
    all_rescue_ceiling = initial_ceiling + output_price_per_million * expected_calls * max(MAX_TOKENS, 2048) / 1_000_000
    return {
        "expected_calls": expected_calls, "rated_cost": rated_cost, "direct_cost": direct_cost,
        "cumulative_cost": cumulative_cost, "output_price_per_million": output_price_per_million,
        "initial_ceiling": initial_ceiling, "all_rescue_ceiling": all_rescue_ceiling,
        "protocol_id": protocol_id(pilot_items, request_plan),
    }


def write_manifest(pilot_items: list[dict], model: dict, request_plan: list[dict], checks: dict) -> None:
    direction_rows = []
    for n in (2, 3, 4, 10):
        item = next(item for item in pilot_items if item["n"] == n)
        counts = direction_counts(request_plan, item["id"])
        exposure = str(TOTAL_SAMPLES_PER_ITEM // n) if TOTAL_SAMPLES_PER_ITEM % n == 0 else "6 or 7"
        direction_rows.append(f"| n={n} | {counts['canonical']} | {counts['reversed']} | {exposure} |")
    lines = [
        "# Gemini 3.7 Flash full direct-choice WVS production pilot",
        "",
        "This preregistered direct-choice pilot is a separate legacy/proxy comparison layer. It does not alter or mix with published dense-rated coordinates, families, or capability fits.",
        "",
        "## Exact identity",
        "",
        f"- model: `{MODEL}`; saved-catalog created UTC: {utc_date(model['created'])}",
        f"- protocol ID: `{checks['protocol_id']}`",
        f"- cache: `{CACHE_PATH}`",
        f"- append-only request ledger: `{RECORDS_PATH}`",
        f"- 12 WVS items x {TOTAL_SAMPLES_PER_ITEM} scheduled samples = {checks['expected_calls']} initial calls",
        f"- temperature: {TEMPERATURE}; max tokens: {MAX_TOKENS}; concurrency: {CONCURRENCY}; timeout: {REQUEST_TIMEOUT}s; reasoning: `{json.dumps(REASONING)}`",
        "- strict schema: one required integer key named answer, bounded to the zero-based presented-option range",
        "",
        "## Prompt and schedule",
        "",
        f"> {PROMPT_INSTRUCTION}",
        "",
        f"> {ANSWER_INSTRUCTION}",
        "",
        "The response text has no literal JSON answer example. The rescue text also contains no literal answer value. Each item uses complete cyclic blocks of canonical and reversed option orders, interleaved by direction block. The code asserts exact 20/n exposures for n=2,4,10. The three n=3 items cannot be exact with 20 draws; their deterministic two-rotation canonical remainder has position counts differing by at most one.",
        "",
        "| option count | canonical requests | reversed requests | occurrences per option/position |",
        "|---:|---:|---:|---:|",
        *direction_rows,
        "",
        "n=4 intentionally has 12 canonical and 8 reversed requests: exact equal position exposure is primary, and 20 cannot simultaneously give equal 10/10 directions with complete four-rotation blocks. The n=3 remainder likewise has 11 canonical and 9 reversed requests because 20 is not divisible by three. Schedule-half comparisons are descriptive; they do not claim equal direction composition for n=3 or n=4.",
        "",
        "## Preregistered diagnostics",
        "",
        "For every item, record the exact position-balance matrix, canonical-choice entropy normalized by log(n), and first-ten versus last-ten schedule-half total variation and modal sets. Report canonical/reversed direction distributions descriptively with their counts. Compare direct-choice distributions to Gemini's legacy dense-rated results descriptively only; never mix the two layers in coordinates, family summaries, or capability fits. Any failed request, missing parsed choice, or incomplete item exits nonzero and leaves no cache entry.",
        "",
        "## Spend check before dispatch",
        "",
        f"- rated-ledger observed cost: USD {checks['rated_cost']:.10f}",
        f"- prior direct-choice observed cost: USD {checks['direct_cost']:.10f}",
        f"- cumulative observed cost: USD {checks['cumulative_cost']:.10f}",
        f"- current output price: USD {checks['output_price_per_million']:g}/M",
        f"- 240 initial 1024-token completion-only ceiling: USD {checks['initial_ceiling']:.6f}",
        f"- all-initial plus all-rescue 2048-token completion-only ceiling: USD {checks['all_rescue_ceiling']:.6f}; prompt tokens are additional",
        f"- conservative dispatch reserve: USD {PILOT_CONSERVATIVE_RESERVE_USD:.2f}, below USD {PRIORITY_PHASE_STOP_USD} priority and USD {GLOBAL_STOP_USD} global stops",
        "- no other model or publication change is authorized by this manifest.",
        "",
        "-- PI[gpt-5.6-terra]",
        "",
    ]
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text("\n".join(lines))


def smoke(pilot_items: list[dict], request_plan: list[dict], checks: dict) -> None:
    assert len(pilot_items) == 12
    assert len(request_plan) == 240
    for item in pilot_items:
        item_plan = [request for request in request_plan if request["item_id"] == item["id"]]
        matrix = np.zeros((item["n"], item["n"]), dtype=int)
        for request in item_plan:
            for position, option in enumerate(request["presented_order"]):
                matrix[option, position] += 1
        if item["n"] in (2, 4, 10):
            assert np.all(matrix == TOTAL_SAMPLES_PER_ITEM // item["n"])
        else:
            assert matrix.max() - matrix.min() <= 1
    assert checks["protocol_id"] == protocol_id(pilot_items, request_plan)
    print("smoke: 12 WVS items x 20 samples = 240 requests")
    print("smoke: exact position balance for n=2,4,10; n=3 is nearest balance with max position difference 1")
    print("smoke: direction counts n=2/10 are 10/10, n=3 is 11/9, n=4 is 12/8")
    print(f"smoke: distinct production protocol {checks['protocol_id']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true", help="make the preregistered paid pilot calls")
    parser.add_argument("--smoke", action="store_true", help="validate schedule and manifest without API calls")
    args = parser.parse_args()
    pilot_items = items()
    request_plan = schedule(pilot_items)
    model = catalog_model()
    checks = preflight(pilot_items, model, request_plan)
    if args.run:
        registered = MANIFEST_PATH.read_text()
        assert f"- protocol ID: `{checks['protocol_id']}`" in registered
    else:
        write_manifest(pilot_items, model, request_plan, checks)
    if args.smoke:
        smoke(pilot_items, request_plan, checks)
    if not args.run:
        return
    result = read_items_direct_choice(
        MODEL, pilot_items, samples_per_order=10, temperature=TEMPERATURE, max_tokens=MAX_TOKENS,
        concurrency=CONCURRENCY, request_timeout=REQUEST_TIMEOUT, reasoning=REASONING,
        structured_output=STRUCTURED_OUTPUT, records_path=RECORDS_PATH, cache_path=CACHE_PATH,
        answer_instruction=ANSWER_INSTRUCTION, rescue_instruction=RESCUE_INSTRUCTION,
        plan_override=request_plan,
    )
    if result["cached"]:
        print(f"production direct-choice cache hit: protocol={result['protocol_id'][:12]}")
        return
    if not result["complete"]:
        raise RuntimeError(f"incomplete production direct-choice pilot: {result['run_id']}; raw evidence is {RECORDS_PATH}")
    print(f"complete production direct-choice pilot: {result['run_id']}, protocol={result['protocol_id'][:12]}")


if __name__ == "__main__":
    main()
