#!/usr/bin/env python3
"""Run the provider-locked Gemini Flash reasoning and rating-rubric pilot. -- PI[gpt-5.6-terra]"""
from __future__ import annotations

import argparse
import asyncio
import fcntl
import hashlib
import json
import os
from collections import Counter
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import httpx
import numpy as np

from moralmaps.iw_axes import X_AXIS, Y_AXIS, resolve_items
from moralmaps.read_api import (
    openrouter_request_with_metadata_once,
    rated_protocol_identity,
    read_items_rated,
)
from openrouter_wrapper.retry import is_retryable_error
from wvs_map import _sample_only_coord_se, load_wvs_all, model_coord_ci
from wvs_score_all_options_refresh import STATE as GLOBAL_BUDGET_STATE
from wvs_score_all_options_refresh import reserve, settle_external_reservation

EVAL_VERSION = "wvs-gemini-flash-rubric-v1"
MODELS = (
    "google/gemini-3-flash-preview",
    "google/gemini-3.5-flash",
    "google/gemini-3.6-flash",
    "google/gemini-3.7-flash",
    "google/gemini-3.8-flash",
)
MINIMUM_REASONING = {
    "google/gemini-3-flash-preview": "minimal",
    "google/gemini-3.5-flash": "minimal",
    "google/gemini-3.6-flash": "minimal",
    "google/gemini-3.7-flash": "low",
    "google/gemini-3.8-flash": "low",
}
PROVIDER = {"only": ["google-ai-studio"], "allow_fallbacks": False, "require_parameters": True}
CELLS = (
    ("normal_minimum", "normal", "minimum"),
    ("normal_high", "normal", "high"),
    ("reversed_minimum", "reversed", "minimum"),
    ("reversed_high", "reversed", "high"),
)
N_SAMPLES = 6
MAX_TOKENS = 2048
OUT = Path("slop/research/wvs/20260918_gemini_flash_rubric_pilot")
ENDPOINT_CATALOG = OUT / "endpoint_catalog.json"
MANIFEST = OUT / "manifest.json"
QUANTIZATION_AUDIT = OUT / "quantization_audit.json"
RESULTS = OUT / "results.json"
STATE = OUT / "budget.json"
LOCK = OUT / "budget.lock"
EXISTING_LEDGER = Path("slop/research/wvs/20260916_openrouter/wvs_iw_requests.jsonl")
CANONICAL_CACHE = Path("slop/research/wvs/20260916_openrouter/wvs_iw_rated.json")
MODEL_CATALOG = Path("slop/research/wvs/20260917_openrouter_models.json")
REQUEST_ATTEMPTS = OUT / "request_attempts.jsonl"
PILOT_CAP_USD = Decimal("20")
MAX_ATTEMPTS = 3
TRANSPORT_TIMEOUT = 120
REQUEST_TIMEOUT = 400
GLOBAL_RESERVATION = "pilot/gemini-flash-rubric"
SMOKE_RESERVATION = "pilot/gemini-flash-rubric-smoke-2048"
REVISED_SMOKE_RECORDS = OUT / "paid_smoke_2048.jsonl"
REVISED_SMOKE_SUMMARY = OUT / "paid_smoke_2048.json"


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temp.replace(path)


def reservation_id(prefix: str) -> str:
    return f"{prefix}/{datetime.now(UTC).strftime('%Y%m%dT%H%M%S.%fZ')}"


def rated_items() -> tuple[list[dict], dict]:
    resolved = resolve_items(load_wvs_all())
    items, seen = [], set()
    for axis in (X_AXIS, Y_AXIS):
        for item in resolved[axis]:
            if item["suffix"] in seen:
                continue
            seen.add(item["suffix"])
            items.append({"id": item["suffix"], "question": item["rec"]["q"],
                          "options": item["rec"]["opts"], "n": item["n"]})
    return items, resolved


def model_catalog() -> dict[str, dict]:
    return {row["id"]: row for row in json.loads(MODEL_CATALOG.read_text())["data"]}


def endpoint_catalog() -> dict[str, dict]:
    return {row["id"]: row for row in json.loads(ENDPOINT_CATALOG.read_text())["models"]}


def standard_endpoint(model: str) -> dict:
    matches = [row for row in endpoint_catalog()[model]["endpoints"]
               if row.get("tag") == "google-ai-studio"]
    if len(matches) != 1:
        raise RuntimeError(f"expected one standard google-ai-studio endpoint for {model}, got {len(matches)}")
    return matches[0]


def validate_route(response: dict, model: str) -> dict:
    endpoint = standard_endpoint(model)
    if "quantization" not in endpoint:
        raise RuntimeError(f"standard endpoint omitted advertised quantization: {model}")
    prefix = f"{endpoint['provider_name']} | "
    if not endpoint["name"].startswith(prefix):
        raise RuntimeError(f"cannot recover exact release slug from endpoint name: {endpoint['name']}")
    exact_release_slug = endpoint["name"].removeprefix(prefix)
    metadata = response.get("openrouter_metadata")
    if not isinstance(metadata, dict):
        raise RuntimeError("response omitted openrouter_metadata")
    available = metadata.get("endpoints", {}).get("available", [])
    selected = [row for row in available if row.get("selected") is True]
    if len(selected) != 1:
        raise RuntimeError(f"expected one selected metadata endpoint, got {len(selected)}")
    route = selected[0]
    expected = {
        "requested_model": model,
        "response_model": model,
        "selected_provider": endpoint["provider_name"],
        "selected_release_slug": exact_release_slug,
    }
    observed = {
        "requested_model": metadata.get("requested"),
        "response_model": response.get("model"),
        "selected_provider": route.get("provider"),
        "selected_release_slug": route.get("model"),
    }
    if observed != expected:
        raise RuntimeError(f"route mismatch: expected={expected} observed={observed}")
    return {
        **observed,
        "endpoint_tag": endpoint["tag"],
        "advertised_quantization": endpoint["quantization"],
    }


def deterministic_seeds(model: str, count: int) -> list[int]:
    seeds = []
    for sequence in range(count):
        digest = hashlib.sha256(f"{EVAL_VERSION}|{model}|paired|{sequence}".encode()).digest()
        seeds.append(int.from_bytes(digest[:4], "big") & 0x7FFF_FFFF)
    if len(set(seeds)) != len(seeds):
        raise RuntimeError(f"seed collision for {model}")
    return seeds


def reasoning(model: str, level: str) -> dict:
    effort = MINIMUM_REASONING[model] if level == "minimum" else "high"
    return {"effort": effort}


def records_path(model: str, cell: str) -> Path:
    return OUT / "records" / model.replace("/", "__") / f"{cell}.jsonl"


def explicit_quantizations(value: object) -> list[str]:
    found = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() == "quantization" and child not in (None, "unknown"):
                found.append(str(child))
            found.extend(explicit_quantizations(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(explicit_quantizations(child))
    return found


def quantization_audit() -> dict:
    cache = json.loads(CANONICAL_CACHE.read_text())["completed"]
    canonical_models = sorted({entry["model"] for entry in cache.values()
                               if entry.get("eval_version") == "wvs-score-all-options-v1"})
    endpoints_by_model = endpoint_catalog()
    counts = {model: Counter() for model in canonical_models}
    providers = {model: Counter() for model in canonical_models}
    for line in EXISTING_LEDGER.read_text().splitlines():
        record = json.loads(line)
        model = record.get("model")
        if model not in counts or record.get("event") != "request_completed":
            continue
        response = record.get("response") or {}
        provider = record.get("provider") or response.get("provider")
        providers[model][str(provider)] += 1
        exact = explicit_quantizations(response)
        if exact:
            counts[model]["exact_response_quantization"] += 1
            continue
        if not provider:
            counts[model]["unknown_missing_provider"] += 1
            continue
        matches = [endpoint for endpoint in endpoints_by_model[model]["endpoints"]
                   if endpoint.get("provider_name") == provider]
        known = {endpoint.get("quantization") for endpoint in matches
                 if endpoint.get("quantization") not in (None, "unknown")}
        if known:
            counts[model]["ambiguous_current_snapshot_join"] += 1
        elif matches:
            counts[model]["unknown_current_quantization"] += 1
        else:
            counts[model]["unknown_no_current_provider_join"] += 1
    rows = [{
        "model": model,
        "saved_provider_counts": dict(providers[model]),
        "classification_counts": dict(counts[model]),
        "current_endpoint_quantizations": sorted({
            str(endpoint.get("quantization"))
            for endpoint in endpoints_by_model[model]["endpoints"]
        }),
    } for model in canonical_models]
    exact = sum(row["classification_counts"].get("exact_response_quantization", 0) for row in rows)
    ambiguous = sum(row["classification_counts"].get("ambiguous_current_snapshot_join", 0) for row in rows)
    unknown = sum(sum(count for key, count in row["classification_counts"].items()
                      if key.startswith("unknown_")) for row in rows)
    total = exact + ambiguous + unknown
    return {
        "schema": 2,
        "source_ledger": str(EXISTING_LEDGER),
        "canonical_cache": str(CANONICAL_CACHE),
        "endpoint_catalog": str(ENDPOINT_CATALOG),
        "endpoint_snapshot_scope": "all exact model IDs in the canonical v1 cache",
        "endpoint_snapshot_is_historical_route_evidence": False,
        "canonical_models": len(canonical_models),
        "completed_request_phases": total,
        "classification_counts": {"exact": exact, "ambiguous": ambiguous, "unknown": unknown},
        "rows": rows,
        "conclusion": ("No quantization-stratified variance is identifiable. Exact requires an explicit saved "
                       "response quantization; current endpoint joins are ambiguous rather than historical route evidence."),
    }


def write_manifest() -> dict:
    items, _ = rated_items()
    catalog = model_catalog()
    rows = []
    for model in MODELS:
        endpoint = standard_endpoint(model)
        advertised = set(endpoint["supported_parameters"])
        efforts = set(catalog[model]["reasoning"]["supported_efforts"])
        minimum = MINIMUM_REASONING[model]
        if not {"reasoning_effort", "structured_outputs", "seed"} <= advertised:
            raise RuntimeError(f"endpoint lacks required parameters: {model}")
        if not {minimum, "high"} <= efforts:
            raise RuntimeError(f"catalog lacks required reasoning efforts: {model}")
        seeds = deterministic_seeds(model, len(items) * N_SAMPLES)
        cells = []
        for cell, rubric, level in CELLS:
            protocol_id = rated_protocol_identity(
                model, items, n_samples=N_SAMPLES, temperature=1.0, max_tokens=MAX_TOKENS,
                concurrency=1, req_timeout=REQUEST_TIMEOUT, reasoning=reasoning(model, level),
                structured_output=True, provider=PROVIDER, eval_version=EVAL_VERSION,
                seed_schedule=seeds, rating_rubric=rubric, request_metadata=True,
            )
            cells.append({"name": cell, "rating_rubric": rubric,
                          "reasoning": reasoning(model, level), "max_tokens": MAX_TOKENS,
                          "protocol_id": protocol_id, "records": str(records_path(model, cell))})
        prompt_price = Decimal(endpoint["pricing"]["prompt"]) * Decimal(1_000_000)
        completion_price = Decimal(endpoint["pricing"]["completion"]) * Decimal(1_000_000)
        calls = Decimal(len(cells) * len(items) * N_SAMPLES)
        bound = calls * (Decimal(2048) * prompt_price + Decimal(MAX_TOKENS) * completion_price) / Decimal(1_000_000)
        rows.append({
            "id": model,
            "created": catalog[model]["created"],
            "minimum_reasoning": minimum,
            "paired_seed_schedule": seeds,
            "provider_endpoint": endpoint["tag"],
            "advertised_quantization": endpoint.get("quantization"),
            "input_usd_per_million": str(prompt_price),
            "output_usd_per_million": str(completion_price),
            "cells": cells,
            "calls": int(calls),
            "runtime_initial_request_bound_usd": str(bound),
        })
    audit = quantization_audit()
    panel_bound = sum(Decimal(row["runtime_initial_request_bound_usd"]) for row in rows)
    smoke_endpoint = standard_endpoint(MODELS[0])
    smoke_bound = (Decimal(2048) * Decimal(smoke_endpoint["pricing"]["prompt"])
                   + Decimal(MAX_TOKENS) * Decimal(smoke_endpoint["pricing"]["completion"]))
    payload = {
        "schema": 1,
        "eval_version": EVAL_VERSION,
        "created_utc": datetime.now(UTC).isoformat(),
        "models": rows,
        "items": len(items),
        "samples_per_item_per_cell": N_SAMPLES,
        "cells_per_model": len(CELLS),
        "panel_calls": sum(row["calls"] for row in rows),
        "paid_smoke_calls": 1,
        "provider": PROVIDER,
        "temperature": 1.0,
        "structured_output": True,
        "request_metadata": True,
        "max_attempts_per_request": MAX_ATTEMPTS,
        "transport_timeout_seconds": TRANSPORT_TIMEOUT,
        "request_timeout_seconds": REQUEST_TIMEOUT,
        "reverse_transform": "6 - rating; raw and transformed samples retained separately",
        "merge_reversed_into_primary": False,
        "z_scaling": False,
        "runtime_input_token_reserve_per_initial_request": 2048,
        "panel_initial_request_bound_usd": str(panel_bound),
        "paid_smoke_bound_usd": str(smoke_bound),
        "panel_plus_smoke_bound_usd": str(panel_bound + smoke_bound),
        "headroom_below_hard_stop_usd": str(PILOT_CAP_USD - panel_bound - smoke_bound),
        "hard_pilot_stop_usd": str(PILOT_CAP_USD),
        "catalog_sha256": hashlib.sha256(MODEL_CATALOG.read_bytes()).hexdigest(),
        "endpoint_catalog_sha256": hashlib.sha256(ENDPOINT_CATALOG.read_bytes()).hexdigest(),
        "not_published": True,
        "quantization_audit": audit["conclusion"],
    }
    atomic_json(QUANTIZATION_AUDIT, audit)
    atomic_json(MANIFEST, payload)
    return payload


def update_state(update) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    with LOCK.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = json.loads(STATE.read_text()) if STATE.exists() else {
            "schema": 1,
            "hard_cap_usd": str(PILOT_CAP_USD),
            "provider_reported_spent_usd": "0",
            "conservative_spent_usd": "0",
            "reserved_usd": "0",
            "completed_phases": 0,
            "completed_phases_without_provider_cost": 0,
            "failed_phases_charged_at_bound": 0,
        }
        state["hard_cap_usd"] = str(PILOT_CAP_USD)
        update(state)
        atomic_json(STATE, state)
        fcntl.flock(lock, fcntl.LOCK_UN)
    return state


def request_bound(payload: dict) -> Decimal:
    endpoint = standard_endpoint(payload["model"])
    prompt_price = Decimal(endpoint["pricing"]["prompt"])
    completion_price = Decimal(endpoint["pricing"]["completion"])
    input_token_bound = Decimal(2048)
    return input_token_bound * prompt_price + Decimal(payload["max_tokens"]) * completion_price


def reserve_request(payload: dict) -> Decimal:
    bound = request_bound(payload)
    def update(state: dict) -> None:
        spent = Decimal(state["conservative_spent_usd"])
        held = Decimal(state["reserved_usd"])
        if spent + held + bound > PILOT_CAP_USD:
            raise RuntimeError(f"pilot hard stop: spent={spent} held={held} next={bound} cap={PILOT_CAP_USD}")
        state["reserved_usd"] = str(held + bound)
    update_state(update)
    return bound


def append_attempt(record: dict) -> None:
    record["recorded_at_utc"] = datetime.now(UTC).isoformat()
    REQUEST_ATTEMPTS.parent.mkdir(parents=True, exist_ok=True)
    with REQUEST_ATTEMPTS.open("a") as file:
        file.write(json.dumps(record, sort_keys=True) + "\n")
        file.flush()
        os.fsync(file.fileno())


def settle_request(bound: Decimal, response: dict | None) -> None:
    reported = None if response is None else (response.get("usage") or {}).get("cost")
    charged = bound if reported is None else Decimal(str(reported))
    def update(state: dict) -> None:
        state["reserved_usd"] = str(Decimal(state["reserved_usd"]) - bound)
        state["conservative_spent_usd"] = str(Decimal(state["conservative_spent_usd"]) + charged)
        if response is None:
            state["failed_phases_charged_at_bound"] += 1
            return
        state["completed_phases"] += 1
        if reported is None:
            state["completed_phases_without_provider_cost"] += 1
        else:
            state["provider_reported_spent_usd"] = str(
                Decimal(state["provider_reported_spent_usd"]) + Decimal(str(reported)))
    update_state(update)


async def budgeted_request(payload: dict) -> dict:
    payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    for attempt in range(1, MAX_ATTEMPTS + 1):
        bound = reserve_request(payload)
        try:
            response = await openrouter_request_with_metadata_once(payload, timeout=TRANSPORT_TIMEOUT)
        except Exception as error:
            settle_request(bound, None)
            response_text = None
            status_code = None
            if isinstance(error, httpx.HTTPStatusError):
                response_text = error.response.text
                status_code = error.response.status_code
            append_attempt({"event": "request_attempt_failed", "model": payload["model"],
                            "payload_sha256": payload_hash, "attempt": attempt,
                            "reserved_bound_usd": str(bound), "error_type": type(error).__name__,
                            "error": str(error), "error_data": getattr(error, "data", None),
                            "status_code": status_code, "response_text": response_text})
            if attempt == MAX_ATTEMPTS or not is_retryable_error(error, response_text or ""):
                raise
            await asyncio.sleep(2 ** (attempt - 1))
            continue
        try:
            route = validate_route(response, payload["model"])
        except Exception as error:
            settle_request(bound, response)
            append_attempt({"event": "request_attempt_route_invalid", "model": payload["model"],
                            "payload_sha256": payload_hash, "attempt": attempt,
                            "reserved_bound_usd": str(bound),
                            "provider_reported_cost_usd": (response.get("usage") or {}).get("cost"),
                            "response_id": response.get("id"), "response": response,
                            "error_type": type(error).__name__, "error": str(error)})
            raise
        settle_request(bound, response)
        append_attempt({"event": "request_attempt_completed", "model": payload["model"],
                        "payload_sha256": payload_hash, "attempt": attempt,
                        "reserved_bound_usd": str(bound),
                        "provider_reported_cost_usd": (response.get("usage") or {}).get("cost"),
                        "response_id": response.get("id"), "route": route,
                        "openrouter_metadata": response.get("openrouter_metadata")})
        return response
    raise AssertionError("unreachable")


def cell_result(model: str, cell: dict, items: list[dict], resolved: dict) -> dict | None:
    path = Path(cell["records"])
    events = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    finished = [event for event in events if event.get("event") == "run_finished"
                and event.get("protocol_id") == cell["protocol_id"]]
    if not finished:
        return None
    final = finished[-1]
    rows = {event["id"]: event for event in events
            if event.get("event") == "item_result" and event.get("run_id") == final["run_id"]}
    result = {
        "name": cell["name"], "protocol_id": cell["protocol_id"], "run_id": final["run_id"],
        "records": str(path), "valid_samples": final["valid_samples"],
        "failed_samples": final["failed_samples"], "rescued_samples": final["rescued_samples"],
    }
    complete = (len(rows) == len(items) and final["valid_samples"] == len(items) * N_SAMPLES
                and final["failed_samples"] == 0
                and all(row["valid_samples"] == N_SAMPLES for row in rows.values()))
    if not complete:
        return result | {"status": "incomplete"}
    psamples = {item["id"]: np.asarray(rows[item["id"]]["p_samples"]) for item in items}
    coords = model_coord_ci(psamples, resolved, np.random.default_rng(0))
    response_se = _sample_only_coord_se(psamples, resolved, np.random.default_rng(1), n_draws=N_SAMPLES)
    metadata = [event["response"].get("openrouter_metadata") for event in events
                if event.get("event") == "request_completed" and event.get("run_id") == final["run_id"]]
    return result | {"status": "complete", "coords": list(coords),
                     "response_mean_se": list(response_se),
                     "routing_metadata_records": len([row for row in metadata if row is not None])}


def run_cell(model: dict, cell: dict, items: list[dict], resolved: dict) -> dict:
    prior = cell_result(model["id"], cell, items, resolved)
    if prior is not None and prior["status"] == "complete":
        return prior
    rows = read_items_rated(
        model["id"], items, n_samples=N_SAMPLES, temperature=1.0, max_tokens=cell["max_tokens"],
        concurrency=1, req_timeout=REQUEST_TIMEOUT, reasoning=cell["reasoning"], structured_output=True,
        records_path=cell["records"], verbose_first=True, provider=PROVIDER, probe_first=True,
        eval_version=EVAL_VERSION, identity_eval_version=EVAL_VERSION,
        seed_schedule=model["paired_seed_schedule"], rating_rubric=cell["rating_rubric"],
        request_metadata=True, reuse_valid_records=True, request_fn=budgeted_request,
    )
    if sum(row["valid_samples"] for row in rows) == 0:
        raise RuntimeError(f"cell produced no valid samples: {model['id']} {cell['name']}")
    result = cell_result(model["id"], cell, items, resolved)
    if result is None:
        raise RuntimeError(f"cell did not write run_finished: {model['id']} {cell['name']}")
    return result


def run() -> None:
    data = json.loads(MANIFEST.read_text())
    items, resolved = rated_items()
    global_reservation = reservation_id(GLOBAL_RESERVATION)
    if not reserve({"id": global_reservation, "lane": "google", "reserve_usd": str(PILOT_CAP_USD)}):
        raise RuntimeError("global repository cap rejected Gemini pilot reservation")
    before = Decimal(update_state(lambda state: state)["conservative_spent_usd"])
    results = {"schema": 1, "eval_version": EVAL_VERSION, "models": [], "not_published": True}
    try:
        for model in data["models"]:
            cells = []
            for cell in model["cells"]:
                cells.append(run_cell(model, cell, items, resolved))
                atomic_json(RESULTS, results | {"models": results["models"] + [
                    {"id": model["id"], "cells": cells}]})
            results["models"].append({"id": model["id"], "cells": cells})
            atomic_json(RESULTS, results)
    finally:
        after = Decimal(update_state(lambda state: state)["conservative_spent_usd"])
        settle_external_reservation(global_reservation, after - before)
        state = update_state(lambda value: value.update({"finished_utc": datetime.now(UTC).isoformat()}))
        if RESULTS.exists():
            saved = json.loads(RESULTS.read_text())
            atomic_json(RESULTS, saved | {"budget": {
                "provider_reported_spent_usd": state["provider_reported_spent_usd"],
                "conservative_spent_usd": state["conservative_spent_usd"],
                "completed_phases_without_provider_cost": state["completed_phases_without_provider_cost"],
                "failed_phases_charged_at_bound": state["failed_phases_charged_at_bound"],
            }})


def metadata_smoke() -> None:
    global openrouter_request_with_metadata_once
    body = {
        "id": "fake", "model": "fake", "provider": "Google AI Studio",
        "choices": [{"finish_reason": "stop", "message": {"content": '{"0": 1, "1": 5}'}}],
        "usage": {"cost": 0},
        "openrouter_metadata": {
            "requested": "fake",
            "endpoints": {"available": [
                {"provider": "Google AI Studio", "model": "fake-release", "selected": True}
            ]},
        },
    }
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-OpenRouter-Metadata"] == "enabled"
        assert request.headers["Authorization"] == "Bearer test-key"
        return httpx.Response(200, json=body)
    response = asyncio.run(openrouter_request_with_metadata_once(
        {"model": "fake", "messages": [{"role": "user", "content": "test"}]},
        api_key="test-key", transport=httpx.MockTransport(handler)))
    assert response["openrouter_metadata"] == body["openrouter_metadata"]
    model = MODELS[0]
    endpoint = standard_endpoint(model)
    exact_release_slug = endpoint["name"].removeprefix(f"{endpoint['provider_name']} | ")
    route_response = {
        "model": model,
        "openrouter_metadata": {
            "requested": model,
            "endpoints": {"available": [{
                "provider": endpoint["provider_name"], "model": exact_release_slug, "selected": True,
            }]},
        },
    }
    assert validate_route(route_response, model)["advertised_quantization"] == "unknown"
    route_body = body | route_response | {"provider": endpoint["provider_name"]}

    record = OUT / "metadata_capture_smoke.jsonl"
    record.unlink(missing_ok=True)
    request_count = 0
    async def fake_request(payload: dict) -> dict:
        nonlocal request_count
        request_count += 1
        return body
    kwargs = dict(
        n_samples=1, records_path=record, reasoning={"effort": "minimal"}, structured_output=True,
        provider=PROVIDER, eval_version=EVAL_VERSION, identity_eval_version=EVAL_VERSION,
        seed_schedule=[1], rating_rubric="reversed", request_metadata=True,
    )
    items = [{"id": "test", "question": "test", "options": ["a", "b"], "n": 2}]
    rows = read_items_rated("fake", items, request_fn=fake_request, **kwargs)
    async def must_not_request(payload: dict) -> dict:
        raise AssertionError("resume repeated a completed request")
    read_items_rated("fake", items, request_fn=must_not_request, reuse_valid_records=True, **kwargs)
    events = [json.loads(line) for line in record.read_text().splitlines()]
    completed = next(event for event in events if event["event"] == "request_completed")
    assert completed["response"]["openrouter_metadata"] == body["openrouter_metadata"]
    assert rows[0]["rating_samples_raw"] == [[1.0, 5.0]]
    assert rows[0]["rating_samples_transformed"] == [[5.0, 1.0]]
    assert request_count == 1
    assert sum(event["event"] == "request_reused" for event in events) == 1

    rescue_record = OUT / "rescue_seed_capture_smoke.jsonl"
    rescue_record.unlink(missing_ok=True)
    rescue_payloads = []
    async def fake_rescue_request(payload: dict) -> dict:
        rescue_payloads.append(payload)
        reply = json.loads(json.dumps(body))
        if len(rescue_payloads) == 1:
            reply["choices"][0]["finish_reason"] = "length"
            reply["choices"][0]["message"]["content"] = '{"0": 1'
        return reply
    read_items_rated(
        "fake", items, n_samples=1, max_tokens=MAX_TOKENS,
        records_path=rescue_record, reasoning={"effort": "high"}, structured_output=True,
        provider=PROVIDER, eval_version=EVAL_VERSION, identity_eval_version=EVAL_VERSION,
        seed_schedule=[23], rating_rubric="normal", request_metadata=True,
        request_fn=fake_rescue_request,
    )
    assert len(rescue_payloads) == 2
    assert [payload["seed"] for payload in rescue_payloads] == [23, 23]
    rescue_events = [json.loads(line) for line in rescue_record.read_text().splitlines()]
    started = [event for event in rescue_events if event["event"] == "request_started"]
    assert [event["payload"]["seed"] for event in started] == [23, 23]

    state_before = STATE.read_bytes() if STATE.exists() else None
    attempts_before = REQUEST_ATTEMPTS.read_bytes() if REQUEST_ATTEMPTS.exists() else None
    initial_state = json.loads(state_before) if state_before is not None else {
        "conservative_spent_usd": "0", "provider_reported_spent_usd": "0",
        "failed_phases_charged_at_bound": 0,
    }
    real_request = openrouter_request_with_metadata_once
    retry_count = 0
    async def flaky_request(payload: dict, timeout: float = 60.0) -> dict:
        nonlocal retry_count
        retry_count += 1
        if retry_count == 1:
            raise httpx.ReadTimeout("temporary", request=httpx.Request("POST", "https://openrouter.ai"))
        return route_body
    try:
        openrouter_request_with_metadata_once = flaky_request
        retry_payload = {"model": MODELS[0], "messages": [{"role": "user", "content": "test"}],
                         "max_tokens": MAX_TOKENS}
        asyncio.run(budgeted_request(retry_payload))
        assert retry_count == 2
        retry_state = json.loads(STATE.read_text())
        spent_delta = (Decimal(retry_state["conservative_spent_usd"])
                       - Decimal(initial_state["conservative_spent_usd"]))
        assert spent_delta == request_bound(retry_payload)
        assert Decimal(retry_state["provider_reported_spent_usd"]) == Decimal(
            initial_state["provider_reported_spent_usd"])
        assert retry_state["failed_phases_charged_at_bound"] == (
            initial_state["failed_phases_charged_at_bound"] + 1)
        attempt_events = [json.loads(line) for line in REQUEST_ATTEMPTS.read_text().splitlines()]
        assert [event["event"] for event in attempt_events[-2:]] == [
            "request_attempt_failed", "request_attempt_completed"]

        invalid_body = json.loads(json.dumps(route_body))
        invalid_body["usage"]["cost"] = 0.001
        invalid_body["openrouter_metadata"]["endpoints"]["available"][0]["provider"] = "Wrong"
        async def invalid_route_request(payload: dict, timeout: float = 60.0) -> dict:
            return invalid_body
        openrouter_request_with_metadata_once = invalid_route_request
        before_invalid = Decimal(json.loads(STATE.read_text())["conservative_spent_usd"])
        try:
            asyncio.run(budgeted_request(retry_payload))
        except RuntimeError as error:
            assert "route mismatch" in str(error)
        else:
            raise AssertionError("route mismatch did not fail")
        invalid_state = json.loads(STATE.read_text())
        assert Decimal(invalid_state["conservative_spent_usd"]) - before_invalid == Decimal("0.001")
        invalid_event = json.loads(REQUEST_ATTEMPTS.read_text().splitlines()[-1])
        assert invalid_event["event"] == "request_attempt_route_invalid"
        assert invalid_event["response"] == invalid_body
        atomic_json(OUT / "route_mismatch_capture_smoke.json", invalid_event)
    finally:
        openrouter_request_with_metadata_once = real_request
        if state_before is None:
            STATE.unlink(missing_ok=True)
        else:
            STATE.write_bytes(state_before)
        if attempts_before is None:
            REQUEST_ATTEMPTS.unlink(missing_ok=True)
        else:
            REQUEST_ATTEMPTS.write_bytes(attempts_before)

    atomic_json(OUT / "metadata_capture_smoke.json", {
        "status": "passed", "request_header": "X-OpenRouter-Metadata: enabled",
        "durable_response_field": completed["response"]["openrouter_metadata"],
        "reverse_transform": {"raw": [1.0, 5.0], "transformed": [5.0, 1.0]},
        "resume": "one completed request reused without another call",
        "retry": "one retryable timeout preserved, charged conservatively, then completed",
        "route_mismatch": "failed inline after charging actual cost and saving the full response",
        "route_mismatch_record": str(OUT / "route_mismatch_capture_smoke.json"),
        "rescue_seed": "seed 23 present in both initial and rescue payloads",
        "rescue_seed_records": str(rescue_record),
        "failed_retry_conservative_charge_usd": str(request_bound({"model": MODELS[0], "max_tokens": MAX_TOKENS})),
    })


def paid_smoke() -> None:
    data = json.loads(MANIFEST.read_text())
    model = data["models"][0]
    cell = next(row for row in model["cells"] if row["name"] == "normal_high")
    items, _ = rated_items()
    smoke_records = REVISED_SMOKE_RECORDS
    existing = [json.loads(line) for line in smoke_records.read_text().splitlines()] if smoke_records.exists() else []
    high_runs = {event["run_id"] for event in existing if event.get("event") == "run_started"
                 and event["settings"]["reasoning"] == {"effort": "high"}
                 and event["settings"]["max_tokens"] == cell["max_tokens"]}
    finished = [event for event in existing if event.get("event") == "run_finished"
                and event["run_id"] in high_runs and event["valid_samples"] == 1]
    if not finished:
        smoke_reservation = reservation_id(SMOKE_RESERVATION)
        if not reserve({"id": smoke_reservation, "lane": "google", "reserve_usd": "0.05"}):
            raise RuntimeError("global repository cap rejected paid smoke reservation")
        before = Decimal(update_state(lambda state: state)["conservative_spent_usd"])
        try:
            read_items_rated(
                model["id"], [items[0]], n_samples=1, temperature=1.0, max_tokens=cell["max_tokens"],
                concurrency=1, req_timeout=REQUEST_TIMEOUT, reasoning=cell["reasoning"], structured_output=True,
                records_path=smoke_records, verbose_first=True, provider=PROVIDER, probe_first=True,
                eval_version=EVAL_VERSION, identity_eval_version=f"{EVAL_VERSION}-smoke",
                seed_schedule=[model["paired_seed_schedule"][0]], rating_rubric="normal",
                request_metadata=True, request_fn=budgeted_request,
            )
        finally:
            after = Decimal(update_state(lambda state: state)["conservative_spent_usd"])
            settle_external_reservation(smoke_reservation, after - before)
    events = [json.loads(line) for line in smoke_records.read_text().splitlines()]
    high_runs = {event["run_id"] for event in events if event.get("event") == "run_started"
                 and event["settings"]["reasoning"] == {"effort": "high"}
                 and event["settings"]["max_tokens"] == cell["max_tokens"]}
    finished = [event for event in events if event.get("event") == "run_finished"
                and event["run_id"] in high_runs][-1]
    run_id = finished["run_id"]
    completed = [event for event in events if event.get("event") == "request_completed"
                 and event["run_id"] == run_id]
    parsed = [event for event in events if event.get("event") == "answer_parsed"
              and event["run_id"] == run_id][-1]
    if finished["valid_samples"] != 1 or finished["failed_samples"] != 0 or parsed["parsed"] is not True:
        raise RuntimeError(f"paid smoke was not parse-valid: finished={finished} parsed={parsed}")
    phases = []
    for event in completed:
        response = event["response"]
        message = response["choices"][0]["message"]
        phases.append({
            "phase": event["phase"], "route": validate_route(response, model["id"]),
            "response_id": response.get("id"),
            "finish_reason": response["choices"][0]["finish_reason"],
            "content": message.get("content"), "reasoning_text": message.get("reasoning"),
            "reasoning_details": message.get("reasoning_details"),
            "usage": event.get("usage"), "response": response,
        })
    usage_totals = {
        "prompt_tokens": sum((event.get("usage") or {})["prompt_tokens"] for event in completed),
        "completion_tokens": sum((event.get("usage") or {})["completion_tokens"] for event in completed),
        "reasoning_tokens": sum((event.get("usage") or {})["completion_tokens_details"]["reasoning_tokens"]
                                for event in completed),
        "total_tokens": sum((event.get("usage") or {})["total_tokens"] for event in completed),
        "provider_reported_cost_usd": str(sum(
            (Decimal(str((event.get("usage") or {})["cost"])) for event in completed), Decimal())),
    }
    state = update_state(lambda value: value)
    global_state = json.loads(GLOBAL_BUDGET_STATE.read_text())
    global_external = {key: value for key, value in global_state["external_observed_usd"].items()
                       if key.startswith(f"{SMOKE_RESERVATION}/")}
    global_reservations = {key: value for key, value in global_state["reservations"].items()
                           if key.startswith(f"{SMOKE_RESERVATION}/")}
    atomic_json(REVISED_SMOKE_SUMMARY, {
        "status": "passed", "model": model["id"], "cell": cell["name"],
        "reasoning": cell["reasoning"], "run_id": run_id,
        "protocol_id": finished["protocol_id"], "parse_valid": parsed["parsed"],
        "rescued_samples": finished["rescued_samples"], "phases": phases,
        "usage_totals": usage_totals,
        "budget": {
            "provider_reported_spent_usd": state["provider_reported_spent_usd"],
            "conservative_spent_usd": state["conservative_spent_usd"],
            "reserved_usd": state["reserved_usd"],
            "failed_phases_charged_at_bound": state["failed_phases_charged_at_bound"],
        },
        "global_accounting": {
            "external_observed_usd": global_external,
            "matching_reservations": global_reservations,
            "total_external_observed_usd": str(sum(
                (Decimal(value) for value in global_external.values()), Decimal())),
        },
        "records": str(smoke_records),
    })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-manifest", action="store_true")
    parser.add_argument("--metadata-smoke", action="store_true")
    parser.add_argument("--paid-smoke", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.write_manifest:
        write_manifest()
    if args.metadata_smoke:
        metadata_smoke()
    if args.paid_smoke:
        paid_smoke()
    if args.run:
        run()


if __name__ == "__main__":
    main()
