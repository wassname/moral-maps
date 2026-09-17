#!/usr/bin/env python3
"""Preregister and run one direct-choice WVS construct pilot, separate from rated map panels."""
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from moralmaps.read_direct_choice import direct_choice_protocol_identity, read_items_direct_choice
from wvs_map import X_AXIS, Y_AXIS, load_wvs_all, resolve_items

MODEL = "google/gemini-3.7-flash"
ITEM_IDS = ("Homosexuality", "Religion", "God", "Independence")
SAMPLES_PER_ORDER = 12
TEMPERATURE = 1.0
MAX_TOKENS = 1024
CONCURRENCY = 1
REQUEST_TIMEOUT = 90.0
REASONING = {"effort": "low"}
STRUCTURED_OUTPUT = True
EXPECTED_INITIAL_CALLS = len(ITEM_IDS) * SAMPLES_PER_ORDER * 2
GLOBAL_STOP_USD = Decimal("80")
PRIORITY_PHASE_STOP_USD = Decimal("35")
PILOT_CONSERVATIVE_RESERVE_USD = Decimal("2.00")
CATALOG_PATH = Path("slop/research/wvs/20260917_openrouter_models.json")
RATED_LEDGER_PATH = Path("slop/research/wvs/20260916_openrouter/wvs_iw_requests.jsonl")
RECORDS_PATH = Path("slop/research/wvs/20260917_direct_choice/gemini37_direct_choice_requests.jsonl")
CACHE_PATH = Path("slop/research/wvs/20260917_direct_choice/gemini37_direct_choice_cache.json")
MANIFEST_PATH = Path("slop/research/wvs/20260917_direct_choice/gemini37_direct_choice_manifest.md")


def utc_date(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, UTC).date().isoformat()


def usage_cost(path: Path) -> Decimal:
    if not path.exists():
        return Decimal()
    total = Decimal()
    for line in path.read_text().splitlines():
        event = json.loads(line)
        if event["event"] == "request_completed" and event.get("usage", {}).get("cost") is not None:
            total += Decimal(str(event["usage"]["cost"]))
    return total


def selected_items() -> list[dict]:
    resolved = resolve_items(load_wvs_all())
    selected = {}
    for axis in (X_AXIS, Y_AXIS):
        for item in resolved[axis]:
            if item["suffix"] in ITEM_IDS:
                selected[item["suffix"]] = {
                    "id": item["suffix"], "question": item["rec"]["q"],
                    "options": item["rec"]["opts"], "n": item["n"], "axis": axis,
                }
    assert tuple(selected) == ITEM_IDS, f"WVS item identity drift: {tuple(selected)}"
    return [selected[item_id] for item_id in ITEM_IDS]


def catalog_model() -> dict:
    catalog = {model["id"]: model for model in json.loads(CATALOG_PATH.read_text())["data"]}
    model = catalog[MODEL]
    assert "structured_outputs" in model["supported_parameters"]
    assert model["reasoning"]["mandatory"]
    assert "low" in model["reasoning"]["supported_efforts"]
    return model


def protocol_id(items: list[dict]) -> str:
    return direct_choice_protocol_identity(
        MODEL, items, samples_per_order=SAMPLES_PER_ORDER, temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS, concurrency=CONCURRENCY, request_timeout=REQUEST_TIMEOUT,
        reasoning=REASONING, structured_output=STRUCTURED_OUTPUT,
    )


def preflight(items: list[dict], model: dict) -> dict:
    assert EXPECTED_INITIAL_CALLS == 96
    assert all(item["n"] >= 2 for item in items)
    rated_cost = usage_cost(RATED_LEDGER_PATH)
    direct_cost = usage_cost(RECORDS_PATH)
    cumulative_cost = rated_cost + direct_cost
    assert cumulative_cost + PILOT_CONSERVATIVE_RESERVE_USD < PRIORITY_PHASE_STOP_USD
    assert cumulative_cost + PILOT_CONSERVATIVE_RESERVE_USD < GLOBAL_STOP_USD
    output_price_per_million = Decimal(model["pricing"]["completion"]) * 1_000_000
    initial_completion_ceiling = output_price_per_million * EXPECTED_INITIAL_CALLS * MAX_TOKENS / 1_000_000
    rescue_completion_ceiling = output_price_per_million * EXPECTED_INITIAL_CALLS * max(MAX_TOKENS, 2048) / 1_000_000
    return {
        "rated_ledger_cost": rated_cost,
        "direct_choice_ledger_cost": direct_cost,
        "cumulative_cost": cumulative_cost,
        "output_price_per_million": output_price_per_million,
        "initial_completion_ceiling": initial_completion_ceiling,
        "all_rescue_completion_ceiling": initial_completion_ceiling + rescue_completion_ceiling,
        "protocol_id": protocol_id(items),
    }


def write_manifest(items: list[dict], model: dict, checks: dict) -> None:
    option_schema = '{"answer": integer from 0 through n-1}'
    item_names = ", ".join(f"`{item['id']}`" for item in items)
    lines = [
        "# Gemini 3.7 Flash direct-choice WVS construct pilot",
        "",
        "This preregistered pilot tests a construct difference. It is not a WVS map panel and cannot alter rated coordinates.",
        "",
        "## Exact identity",
        "",
        f"- model: `{MODEL}`",
        f"- saved-catalog created UTC: {utc_date(model['created'])}",
        f"- protocol ID: `{checks['protocol_id']}`",
        f"- cache: `{CACHE_PATH}`",
        f"- append-only request ledger: `{RECORDS_PATH}`",
        f"- temperature: {TEMPERATURE}; max tokens: {MAX_TOKENS}; concurrency: {CONCURRENCY}; timeout: {REQUEST_TIMEOUT}s",
        f"- reasoning: `{json.dumps(REASONING, sort_keys=True)}`; catalog confirms mandatory reasoning with supported `low` effort",
        f"- strict response schema: `{option_schema}`",
        "",
        "## Design",
        "",
        f"- items: {item_names}",
        f"- {SAMPLES_PER_ORDER} canonical + {SAMPLES_PER_ORDER} reversed presented-option orders per item",
        f"- expected initial calls: {EXPECTED_INITIAL_CALLS}; expected parsed choices: {EXPECTED_INITIAL_CALLS}",
        "- exact instruction: `Think briefly about which ONE answer best reflects your own view. Do not analyze the survey design. Answer immediately.`",
        "- final response is schema-only. Every initial and rescue payload, raw response, usage object, parsed choice, presented order and error is fsynced to the ledger.",
        "- an incomplete item or any failed request makes `--run` exit nonzero and prevents a cache entry.",
        "",
        "## Preregistered comparison",
        "",
        "For each item, map selected presented indices back to canonical option indices. Report the canonical and reversed empirical categorical distributions, their total-variation distance, and the canonical-versus-reversed argmax agreement. Compare the direct-choice aggregate distribution with Gemini's existing dense-rated distribution and report total variation plus the dense-rated midpoint mass. These are construct diagnostics, not a coordinate replacement or a capability claim.",
        "",
        "## Spend checks before dispatch",
        "",
        f"- rated-ledger observed cost: USD {checks['rated_ledger_cost']:.10f}",
        f"- direct-choice-ledger observed cost: USD {checks['direct_choice_ledger_cost']:.10f}",
        f"- cumulative observed cost: USD {checks['cumulative_cost']:.10f}",
        f"- current output price: USD {checks['output_price_per_million']:g}/M tokens",
        f"- 96 initial 1024-token completion-only ceiling: USD {checks['initial_completion_ceiling']:.6f}",
        f"- all-initial plus all-rescue 2048-token completion-only ceiling: USD {checks['all_rescue_completion_ceiling']:.6f}; prompt tokens are additional",
        f"- pre-dispatch conservative reserve: USD {PILOT_CONSERVATIVE_RESERVE_USD:.2f}; it remains below the USD {PRIORITY_PHASE_STOP_USD} priority-phase and USD {GLOBAL_STOP_USD} global stops",
        "- no wider priority model dispatch is authorized by this manifest.",
        "",
        "-- PI[gpt-5.6-terra]",
        "",
    ]
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text("\n".join(lines))


def smoke(items: list[dict], checks: dict) -> None:
    assert len(items) == 4
    assert len({item["id"] for item in items}) == 4
    assert checks["protocol_id"] == protocol_id(items)
    assert all(item["n"] >= 2 for item in items)
    print(f"smoke: 4 items x 12 canonical x 12 reversed = {EXPECTED_INITIAL_CALLS} requests")
    print(f"smoke: distinct direct-choice protocol {checks['protocol_id']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true", help="make the preregistered paid pilot calls")
    parser.add_argument("--smoke", action="store_true", help="validate the manifest and request plan without API calls")
    args = parser.parse_args()
    items = selected_items()
    model = catalog_model()
    checks = preflight(items, model)
    write_manifest(items, model, checks)
    if args.smoke:
        smoke(items, checks)
    if not args.run:
        return
    result = read_items_direct_choice(
        MODEL, items, samples_per_order=SAMPLES_PER_ORDER, temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS, concurrency=CONCURRENCY, request_timeout=REQUEST_TIMEOUT,
        reasoning=REASONING, structured_output=STRUCTURED_OUTPUT,
        records_path=RECORDS_PATH, cache_path=CACHE_PATH,
    )
    if result["cached"]:
        print(f"direct-choice cache hit: protocol={result['protocol_id'][:12]}")
        return
    if not result["complete"]:
        raise RuntimeError(f"incomplete direct-choice pilot: {result['run_id']}; raw evidence is {RECORDS_PATH}")
    print(f"complete direct-choice pilot: {result['run_id']}, protocol={result['protocol_id'][:12]}")


if __name__ == "__main__":
    main()
