#!/usr/bin/env python3
"""wvs-respondent-packet-v1: ONE API call = ONE coherent pseudo-respondent answering the complete
selected WVS battery (8 ordinary single-choice questions + the 11-quality choose-up-to-five child
list) in canonical order. -- PI[gpt-5.6-terra]

Instrument status: the child-quality list is a GlobalOpinionQA-compatible APPROXIMATION -- the saved
source has 10 of the standard 11 qualities; "Religious faith" (standard WVS, absent from the saved
source) is appended as the 11th item, and the saved source does not record the human card order, so
list order is the saved source order plus that documented append. Ordinary questions show only
substantive options; refusal is a separate per-question status inside the schema, never displayed as
an option and never scored as neutral. eval_version is stamped on every record, row, and identity.
Paid paths refuse to run without the explicit opt-in (see PaidCallsNotAuthorized docs).
"""
from __future__ import annotations

import argparse
import asyncio
import fcntl
import hashlib
import json
import os
import re
from datetime import UTC, datetime, timezone
from decimal import Decimal
from pathlib import Path

import httpx
import numpy as np

import moralmaps.iw_axes as iw
from moralmaps.read_api import openrouter_request_with_metadata_once
from openrouter_wrapper.retry import is_retryable_error

sys_parent = Path(__file__).parent
import sys
sys.path.insert(0, str(sys_parent))

from wvs_original_choice_pilot import (  # noqa: E402
    NONSUBSTANTIVE,
    ORDINARY_SUFFIXES,
    PANEL_QUALITIES,
    POSTHOC_MISSING,
    build_items,
)

EVAL_VERSION = "wvs-respondent-packet-v1"
MODELS = ("qwen/qwen3.5-plus-02-15", "qwen/qwen3.6-plus",
          "qwen/qwen3.5-plus-20260420", "qwen/qwen3.7-plus")
PROVIDER = {"only": ["Alibaba"], "allow_fallbacks": False, "require_parameters": True}
N_PACKETS = 128
MAX_TOKENS = 2048
REQUEST_TIMEOUT = 600
TRANSPORT_TIMEOUT = 240
MAX_ATTEMPTS = 3
STAGE_CAP_USD = Decimal("5")
REFUSED = "refused"
RELIGIOUS_FAITH = "Religious faith"
OUT = Path("slop/research/wvs/20260919_respondent_packet")
ENDPOINT_CATALOG = Path("slop/research/wvs/20260918_gemini_flash_rubric_pilot/endpoint_catalog.json")
MODEL_CATALOG = Path("slop/research/wvs/20260917_openrouter_models.json")
DENSE_CACHE = Path("slop/research/wvs/20260916_openrouter/wvs_iw_rated.json")
MANIFEST = OUT / "manifest.json"
RESULTS = OUT / "results.json"
STATE = OUT / "budget.json"
LOCK = OUT / "budget.lock"
REQUEST_ATTEMPTS = OUT / "request_attempts.jsonl"
RESPONDENT_ROWS = OUT / "respondent_rows.jsonl"
PAID_OPTIN_ENV = "WVS_PAID_CALLS_AUTHORIZED"


class PaidCallsNotAuthorized(RuntimeError):
    """Paid request attempted without the explicit opt-in. Root cause of the 2026-09-19 accident:
    `from ... import` binds the request function into this module's namespace at import time, so a
    read_api-level monkeypatch never rebinds it. The guard is an independent second line of
    defense: even an unpatched or mis-patched path refuses without the opt-in."""


def paid_calls_authorized() -> bool:
    return os.environ.get(PAID_OPTIN_ENV) == "1"


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temp.replace(path)


def standard_endpoint(model: str) -> dict:
    catalog = {r["id"]: r for r in json.loads(ENDPOINT_CATALOG.read_text())["models"]}
    matches = [row for row in catalog[model]["endpoints"]
               if row.get("provider_name") == "Alibaba"]
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one Alibaba endpoint for {model}, got {len(matches)}")
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
        "requested_model": model, "response_model": model,
        "selected_provider": endpoint["provider_name"], "selected_release_slug": exact_release_slug,
    }
    observed = {
        "requested_model": metadata.get("requested"), "response_model": response.get("model"),
        "selected_provider": route.get("provider"), "selected_release_slug": route.get("model"),
    }
    if observed != expected:
        raise RuntimeError(f"route mismatch: expected={expected} observed={observed}")
    return {**observed, "endpoint_tag": endpoint.get("tag"),
            "advertised_quantization": endpoint.get("quantization")}


def build_battery() -> tuple[list[dict], list[dict]]:
    """9 question blocks in canonical order: the 8 ordinary items (saved source order), then the
    child-quality list with the 11th standard quality appended (documented approximation)."""
    items, child_rows = build_items()
    battery = []
    for item in items:
        if item["is_list"]:
            continue
        battery.append({"id": item["id"], "question": item["question"],
                        "options": item["substantive"]})
    qualities = next(i for i in items if i["is_list"])["qualities"]
    if RELIGIOUS_FAITH in qualities:
        raise RuntimeError("Religious faith already present in the saved 10-row source; list no longer approximate")
    battery.append({"id": "ChildQualities", "question":
                    "Here is a list of qualities that children can be encouraged to learn at home. "
                    "Which, if any, do you consider to be especially important? Please choose up to five.",
                    "options": qualities + [RELIGIOUS_FAITH]})
    return battery, child_rows


def render_packet(battery: list[dict]) -> str:
    blocks = []
    for number, q in enumerate(battery, 1):
        if q["id"] == "ChildQualities":
            opts = "\n".join(f"   {j}. {o}" for j, o in enumerate(q["options"], 1))
            blocks.append(f"{number}. {q['question']}\n{opts}\n"
                          "Choose up to five; give an empty list if none.")
        else:
            opts = "\n".join(f"   {chr(64 + j)}. {o}" for j, o in enumerate(q["options"], 1))
            blocks.append(f"{number}. {q['question']}\n{opts}\nChoose exactly one option.")
    return ("You are one person answering a social values survey. Answer every question as yourself, "
            "in order, choosing the option that best matches your own views. "
            "If you cannot or will not answer a question, set its \"selected\" value to \"refused\"; "
            "the refusal is recorded separately and is not one of the listed options.\n\n"
            + "\n\n".join(blocks))


def packet_schema(battery: list[dict]) -> dict:
    child = next(q for q in battery if q["id"] == "ChildQualities")
    ordinary = {q["id"]: {"type": "object",
                          "properties": {"selected": {"type": "string",
                                                      "enum": q["options"] + [REFUSED]}},
                          "required": ["selected"], "additionalProperties": False}
                for q in battery if q["id"] != "ChildQualities"}
    return {"type": "json_schema", "json_schema": {"name": "wvs_respondent_packet", "strict": True,
            "schema": {"type": "object", "properties": {
                "answers": {"type": "object", "properties": ordinary,
                            "required": list(ordinary), "additionalProperties": False},
                "child_qualities": {"type": "array",
                                    "items": {"type": "string", "enum": child["options"]},
                                    "minItems": 0, "maxItems": 5, "uniqueItems": True}},
                "required": ["answers", "child_qualities"], "additionalProperties": False}}}


def parse_packet(battery: list[dict], text: str) -> dict | None:
    """Validated respondent row, or None when invalid (rescued once, then a failed packet)."""
    objs = re.findall(r"\{.*\}", text, re.S)
    if not objs:
        return None
    try:
        raw = json.loads(objs[-1])
    except json.JSONDecodeError:
        return None
    answers, qualities = raw.get("answers"), raw.get("child_qualities")
    if not isinstance(answers, dict) or not isinstance(qualities, list):
        return None
    row = {}
    for q in battery:
        if q["id"] == "ChildQualities":
            if (len(qualities) > 5 or len(set(qualities)) != len(qualities)
                    or not set(qualities) <= set(q["options"])):
                return None
            row["ChildQualities"] = {"outcome": "refused" if len(qualities) == 0 else "substantive",
                                     "selected": qualities}
            continue
        answer = answers.get(q["id"])
        if not isinstance(answer, dict):
            return None
        selected = answer.get("selected")
        if selected not in q["options"] + [REFUSED]:
            return None
        row[q["id"]] = {"outcome": "refused" if selected == REFUSED else "substantive",
                        "selected": selected}
    return row


def force_msg(battery: list[dict]) -> str:
    ids = ", ".join(f'"{q["id"]}"' for q in battery)
    return ("Output ONLY the compact JSON respondent object now: "
            '{"answers": {"<question id>": {"selected": "<option or \"refused\">"}}, '
            '"child_qualities": [up to five quality names]}. '
            f"Every required key must appear exactly once: {ids}. "
            "No markdown, no reasoning, nothing else.")


def paired_seeds(count: int) -> list[int]:
    seeds = []
    for sequence in range(count):
        digest = hashlib.sha256(f"{EVAL_VERSION}|packet|{sequence}".encode()).digest()
        seeds.append(int.from_bytes(digest[:4], "big") & 0x7FFF_FFFF)
    if len(set(seeds)) != len(seeds):
        raise RuntimeError("seed collision")
    return seeds


def update_state(update) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    with LOCK.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = json.loads(STATE.read_text()) if STATE.exists() else {
            "schema": 1, "eval_version": EVAL_VERSION, "hard_cap_usd": str(STAGE_CAP_USD),
            "provider_reported_spent_usd": "0", "conservative_spent_usd": "0",
            "reserved_usd": "0", "completed_phases": 0,
            "completed_phases_without_provider_cost": 0, "failed_phases_charged_at_bound": 0}
        state["hard_cap_usd"] = str(STAGE_CAP_USD)
        update(state)
        atomic_json(STATE, state)
        fcntl.flock(lock, fcntl.LOCK_UN)
    return state


def request_bound(model: str) -> Decimal:
    endpoint = standard_endpoint(model)
    price = (Decimal(endpoint["pricing"]["prompt"])
             + Decimal(endpoint["pricing"]["completion"]) * 2)
    return Decimal(MAX_TOKENS) * price


def reserve_request(model: str) -> Decimal:
    bound = request_bound(model)
    def update(state: dict) -> None:
        spent, held = Decimal(state["conservative_spent_usd"]), Decimal(state["reserved_usd"])
        if spent + held + bound > STAGE_CAP_USD:
            raise RuntimeError(f"stage hard stop: spent={spent} held={held} next={bound} cap={STAGE_CAP_USD}")
        state["reserved_usd"] = str(held + bound)
    update_state(update)
    return bound


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


def append_attempt(record: dict) -> None:
    record["recorded_at_utc"] = datetime.now(UTC).isoformat()
    REQUEST_ATTEMPTS.parent.mkdir(parents=True, exist_ok=True)
    with REQUEST_ATTEMPTS.open("a") as file:
        file.write(json.dumps(record, sort_keys=True) + "\n")
        file.flush()
        os.fsync(file.fileno())


async def budgeted_request(model: str, payload: dict) -> dict:
    if not paid_calls_authorized():
        raise PaidCallsNotAuthorized(
            f"paid calls require --i-authorize-paid-calls (which sets {PAID_OPTIN_ENV}=1); "
            "offline tests must never reach the API")
    payload["eval_version"] = EVAL_VERSION
    payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    for attempt in range(1, MAX_ATTEMPTS + 1):
        bound = reserve_request(model)
        try:
            response = await openrouter_request_with_metadata_once(payload, timeout=TRANSPORT_TIMEOUT)
        except Exception as error:
            settle_request(bound, None)
            response_text = error.response.text if isinstance(error, httpx.HTTPStatusError) else None
            append_attempt({"event": "request_attempt_failed", "eval_version": EVAL_VERSION,
                            "model": model, "payload_sha256": payload_hash, "attempt": attempt,
                            "reserved_bound_usd": str(bound), "error_type": type(error).__name__,
                            "error": str(error),
                            "status_code": error.response.status_code if response_text else None})
            if attempt == MAX_ATTEMPTS or not is_retryable_error(error, response_text or ""):
                raise
            await asyncio.sleep(2 ** (attempt - 1))
            continue
        try:
            route = validate_route(response, model)
        except Exception as error:
            settle_request(bound, response)
            append_attempt({"event": "request_attempt_route_invalid", "eval_version": EVAL_VERSION,
                            "model": model, "payload_sha256": payload_hash, "attempt": attempt,
                            "reserved_bound_usd": str(bound), "response": response,
                            "error_type": type(error).__name__, "error": str(error)})
            raise
        settle_request(bound, response)
        append_attempt({"event": "request_attempt_completed", "eval_version": EVAL_VERSION,
                        "model": model, "payload_sha256": payload_hash, "attempt": attempt,
                        "provider_reported_cost_usd": (response.get("usage") or {}).get("cost"),
                        "response_id": response.get("id"), "route": route})
        return response
    raise AssertionError("unreachable")


def append_record(rpath: Path, record: dict) -> None:
    record["eval_version"] = EVAL_VERSION
    record["recorded_at_utc"] = datetime.now(UTC).isoformat()
    with rpath.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def load_events(rpath: Path) -> list[dict]:
    return [json.loads(line) for line in rpath.read_text().splitlines()] if rpath.exists() else []


async def run_packet(model: str, battery: list[dict], rpath: Path, run: str, pid: str,
                     seq: int, req: dict, prior: dict | None) -> dict:
    request_meta = {"request_id": f"{run}_{seq:03d}", "run_id": run, "protocol_id": pid,
                    "model": model, "packet": req["packet"], "seed": req["seed"]}
    if prior is not None:
        append_record(rpath, {"event": "packet_reused", **request_meta, "source_run_id": prior["run_id"]})
        return prior["row"]
    payload = {"model": model, "messages": [{"role": "user", "content": req["prompt"]}],
               "temperature": 1.0, "max_tokens": MAX_TOKENS, "seed": req["seed"],
               "reasoning": {"enabled": False}, "provider": PROVIDER,
               "response_format": packet_schema(battery)}
    phase = "initial"
    try:
        append_record(rpath, {"event": "request_started", "phase": phase, **request_meta,
                              "payload": payload})
        response = await asyncio.wait_for(budgeted_request(model, payload), timeout=REQUEST_TIMEOUT)
        append_record(rpath, {"event": "request_completed", "phase": phase, **request_meta,
                              "response": response, "usage": response.get("usage")})
        message = response["choices"][0]["message"]
        text = message.get("content") or ""
        row = parse_packet(battery, text)
        if row is None:
            phase = "rescue"
            tail = (message.get("reasoning") or text or "")[-1500:] or "(thinking truncated)"
            rescue_payload = payload | {"max_tokens": max(MAX_TOKENS, 2048), "messages": [
                {"role": "user", "content": req["prompt"]},
                {"role": "assistant", "content": tail},
                {"role": "user", "content": force_msg(battery)}]}
            append_record(rpath, {"event": "request_started", "phase": phase, **request_meta,
                                  "payload": rescue_payload, "initial_response_message": message})
            response = await asyncio.wait_for(budgeted_request(model, rescue_payload),
                                              timeout=REQUEST_TIMEOUT)
            append_record(rpath, {"event": "request_completed", "phase": phase, **request_meta,
                                  "response": response, "usage": response.get("usage")})
            text = response["choices"][0]["message"].get("content") or ""
            row = parse_packet(battery, text)
    except Exception as exc:
        append_record(rpath, {"event": "request_failed", "phase": phase, **request_meta,
                              "error_type": type(exc).__name__, "error": str(exc)})
        raise
    append_record(rpath, {"event": "respondent_parsed", **request_meta, "phase": phase, "row": row,
                          "parsed": row is not None, "text": text})
    return row


def prior_rows(rpath: Path, pid: str) -> dict[int, dict]:
    return {record["packet"]: record for record in load_events(rpath)
            if record.get("event") == "respondent_parsed" and record.get("parsed") is True
            and record.get("protocol_id") == pid}


def protocol_id(model: str, battery: list[dict]) -> str:
    protocol = {
        "schema": 1, "eval_version": EVAL_VERSION, "model": model,
        "temperature": 1.0, "max_tokens": MAX_TOKENS, "reasoning": {"enabled": False},
        "provider": PROVIDER, "n_packets": N_PACKETS, "seeds": paired_seeds(N_PACKETS),
        "battery": [{"id": q["id"], "question": q["question"], "options": q["options"]}
                    for q in battery],
        "packet_prompt": render_packet(battery),
    }
    encoded = json.dumps(protocol, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(encoded).hexdigest()


async def run_model(model: str, battery: list[dict], pid: str) -> dict:
    rpath = OUT / "records" / model.replace("/", "__") / "packets.jsonl"
    prior = prior_rows(rpath, pid)
    plan = [{"packet": k, "seed": paired_seeds(N_PACKETS)[k],
             "prompt": render_packet(battery)} for k in range(N_PACKETS)]
    if len(prior) == N_PACKETS:
        return summarize_model(model, battery, rpath, pid)
    run = f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{pid[:12]}"
    append_record(rpath, {"event": "run_started", "run_id": run, "protocol_id": pid, "model": model,
                          "planned_requests": len(plan),
                          "settings": {"temperature": 1.0, "max_tokens": MAX_TOKENS,
                                       "reasoning": {"enabled": False}, "provider": PROVIDER,
                                       "n_packets": N_PACKETS, "eval_version": EVAL_VERSION}})
    sem = asyncio.Semaphore(1)

    async def guarded(pair):
        seq, req = pair
        async with sem:
            return await run_packet(model, battery, rpath, run, pid, seq, req, prior.get(req["packet"]))

    rows = await asyncio.gather(*(guarded(pair) for pair in enumerate(plan)))
    summary = summarize_model(model, battery, rpath, pid)
    write_run_finished(model, rpath, pid, plan)
    return summary


def write_run_finished(model: str, rpath: Path, pid: str, plan: list[dict]) -> None:
    parsed = [e for e in load_events(rpath) if e["event"] == "respondent_parsed"
              and e.get("protocol_id") == pid and e.get("parsed") is True]
    rescued = len({e["packet"] for e in parsed if e.get("phase") == "rescue"})
    append_record(rpath, {"event": "run_finished", "run_id": parsed[-1]["run_id"] if parsed else None,
                          "protocol_id": pid, "model": model, "planned_requests": len(plan),
                          "valid_packets": len({e["packet"] for e in parsed}),
                          "failed_packets": len(plan) - len({e["packet"] for e in parsed}),
                          "rescued_packets": rescued,
                          "refused_question_instances": sum(
                              1 for e in parsed for q in (e["row"] or {}).values()
                              if q["outcome"] == "refused")})


def summarize_model(model: str, battery: list[dict], rpath: Path, pid: str) -> dict:
    events = load_events(rpath)
    rows = {}
    for event in events:
        if (event["event"] == "respondent_parsed" and event.get("parsed") is True
                and event.get("protocol_id") == pid):
            rows[event["packet"]] = event["row"]
    if len(rows) != N_PACKETS:
        raise RuntimeError(f"incomplete packet set for {model}: {len(rows)}/{N_PACKETS}")
    per_question = {}
    for q in battery:
        outcomes = [rows[k][q["id"]] for k in sorted(rows)]
        refused = [o for o in outcomes if o["outcome"] == "refused"]
        substantive = [o for o in outcomes if o["outcome"] == "substantive"]
        if q["id"] == "ChildQualities":
            counts = {opt: 0 for opt in q["options"]}
            for o in substantive:
                for sel in o["selected"]:
                    counts[sel] += 1
            per_question[q["id"]] = {"n": len(outcomes), "substantive": len(substantive),
                                     "refused": len(refused),
                                     "coverage": len(substantive) / len(outcomes),
                                     "selection_rates": {opt: counts[opt] / len(outcomes)
                                                         for opt in counts}}
        else:
            counts = {opt: 0 for opt in q["options"]}
            for o in substantive:
                counts[o["selected"]] += 1
            per_question[q["id"]] = {"n": len(outcomes), "substantive": len(substantive),
                                     "refused": len(refused),
                                     "coverage": len(substantive) / len(outcomes),
                                     "option_frequencies": {opt: counts[opt] / len(outcomes)
                                                            for opt in counts}}
    return {"model": model, "eval_version": EVAL_VERSION, "protocol_id": pid, "records": str(rpath),
            "valid_packets": len(rows),
            "refusal_rate_overall": sum(q["refused"] for q in per_question.values())
            / sum(q["n"] for q in per_question.values()),
            "per_question": per_question}


def write_manifest(battery: list[dict]) -> dict:
    catalog = {r["id"]: r for r in json.loads(MODEL_CATALOG.read_text())["data"]}
    rows, total = [], Decimal(0)
    for model in MODELS:
        endpoint = standard_endpoint(model)
        created = catalog[model]["created"]
        bound = Decimal(N_PACKETS) * request_bound(model)
        total += bound
        rows.append({"id": model, "created": created,
                     "created_utc": datetime.fromtimestamp(created, tz=timezone.utc).date().isoformat(),
                     "release_slug": endpoint["name"].removeprefix(f"{endpoint['provider_name']} | "),
                     "reasoning": {"enabled": False},
                     "advertised_quantization": endpoint.get("quantization"),
                     "requests": N_PACKETS, "reserve_bound_usd": str(bound)})
    smoke = Decimal(request_bound(MODELS[0]))
    payload = {"schema": 1, "eval_version": EVAL_VERSION,
               "created_utc": datetime.now(UTC).isoformat(), "models": rows,
               "battery": [{"id": q["id"], "question": q["question"], "options": q["options"]}
                           for q in battery],
               "instrument_status": ("GlobalOpinionQA-compatible approximation; 11th quality "
                                     "Religious faith appended; card order not recorded in source"),
               "n_packets": N_PACKETS, "max_tokens": MAX_TOKENS, "temperature": 1.0,
               "panel_requests": N_PACKETS * len(MODELS), "smoke_requests": 1,
               "panel_reserve_bound_usd": str(total), "smoke_reserve_bound_usd": str(smoke),
               "panel_plus_smoke_bound_usd": str(total + smoke),
               "stage_hard_stop_usd": str(STAGE_CAP_USD),
               "refusal_rule": ("per-question \"refused\" status inside the schema; never displayed "
                                "as an option; reported separately; never neutral"),
               "not_published": True, "merge_into_primary": False}
    atomic_json(MANIFEST, payload)
    return payload


def offline_smoke(battery: list[dict]) -> None:
    valid = {"answers": {q["id"]: {"selected": q["options"][0]} for q in battery
                         if q["id"] != "ChildQualities"},
             "child_qualities": ["Independence", RELIGIOUS_FAITH]}
    row = parse_packet(battery, json.dumps(valid))
    assert row is not None and row["ChildQualities"]["selected"] == ["Independence", RELIGIOUS_FAITH]
    assert all(row[q["id"]]["outcome"] == "substantive" for q in battery if q["id"] != "ChildQualities")
    refused = {"answers": {q["id"]: {"selected": REFUSED} for q in battery
                           if q["id"] != "ChildQualities"}, "child_qualities": []}
    row = parse_packet(battery, json.dumps(refused))
    assert row is not None and all(v["outcome"] == "refused" for v in row.values())
    bad = {"answers": {"nonexistent": {"selected": "x"}}, "child_qualities": []}
    assert parse_packet(battery, json.dumps(bad)) is None
    assert parse_packet(battery, "garbage") is None
    over = {"answers": valid["answers"],
            "child_qualities": next(q for q in battery if q["id"] == "ChildQualities")["options"][:6]}
    assert parse_packet(battery, json.dumps(over)) is None
    dup = {"answers": valid["answers"],
           "child_qualities": [RELIGIOUS_FAITH, RELIGIOUS_FAITH]}
    assert parse_packet(battery, json.dumps(dup)) is None
    # refusal sentinel must not collide with a listed option
    for q in battery:
        assert REFUSED not in q["options"], q["id"]
    assert len(next(q for q in battery if q["id"] == "ChildQualities")["options"]) == 11
    assert paid_calls_authorized() is False
    print("offline smoke passed")


def offline_regression(battery: list[dict]) -> None:
    """No paid call may execute without the opt-in, even with the read_api level patched."""
    os.environ.pop(PAID_OPTIN_ENV, None)
    assert not paid_calls_authorized()
    calls = {"n": 0}

    def would_reach_api(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json={})

    payload = {"model": MODELS[0], "messages": [{"role": "user", "content": "test"}]}
    original = openrouter_request_with_metadata_once
    old_api_key = os.environ.pop("OPENROUTER_API_KEY", None)
    os.environ["OPENROUTER_API_KEY"] = "test-key"
    try:
        ran = False
        try:
            asyncio.run(budgeted_request(MODELS[0], payload))
        except PaidCallsNotAuthorized:
            ran = True
        assert ran and calls["n"] == 0, "paid call executed without the opt-in"

        async def patched(payload, timeout=60.0, **kwargs):
            return await original(payload, timeout=timeout,
                                  transport=httpx.MockTransport(would_reach_api))
        globals()["openrouter_request_with_metadata_once"] = patched
        ran = False
        try:
            asyncio.run(budgeted_request(MODELS[0], payload))
        except PaidCallsNotAuthorized:
            ran = True
        assert ran and calls["n"] == 0, "opt-in guard bypassed"
    finally:
        globals()["openrouter_request_with_metadata_once"] = original
        if old_api_key is not None:
            os.environ["OPENROUTER_API_KEY"] = old_api_key
        else:
            os.environ.pop("OPENROUTER_API_KEY", None)
    import subprocess
    proc = subprocess.run(["uv", "run", "--offline", "--with", "datasets>=4.0,<5", "python",
                           "scripts/wvs_respondent_packet_v1.py", "--run"],
                          capture_output=True, text=True, timeout=600,
                          cwd=str(Path(__file__).parent.parent))
    assert proc.returncode != 0 and "--i-authorize-paid-calls" in (proc.stderr + proc.stdout), (
        f"CLI refusal check failed: rc={proc.returncode} stdout={proc.stdout[-500:]} stderr={proc.stderr[-500:]}")
    print("offline regression passed: opt-in guard, mis-patch defense, and CLI refusal check all hold")


def paid_smoke(battery: list[dict]) -> None:
    """One paid packet on qwen/qwen3.7-plus (default reasoning enabled: riskiest parse path)."""
    model = "qwen/qwen3.7-plus"
    pid = protocol_id(model, battery)
    req = {"packet": 0, "seed": paired_seeds(N_PACKETS)[0], "prompt": render_packet(battery)}
    if not paid_calls_authorized():
        raise SystemExit("paid smoke requires --i-authorize-paid-calls")
    from wvs_score_all_options_refresh import reserve, settle_external_reservation
    smoke_rid = f"pilot/resp-packet-smoke/{datetime.now(UTC).strftime('%Y%m%dT%H%M%S.%fZ')}"
    if not reserve({"id": smoke_rid, "lane": "google", "reserve_usd": "0.05"}):
        raise RuntimeError("global repository cap rejected respondent-packet smoke reservation")
    before = Decimal(update_state(lambda s: s)["conservative_spent_usd"])
    smoke_records = OUT / "paid_smoke.jsonl"
    try:
        row = asyncio.run(run_packet(model, battery, smoke_records, "smoke_run", pid, 0, req, None))
        if row is None:
            raise RuntimeError(f"paid smoke did not parse: {row}")
    finally:
        after = Decimal(update_state(lambda s: s)["conservative_spent_usd"])
        settle_external_reservation(smoke_rid, after - before)
    completed = [e for e in load_events(smoke_records) if e["event"] == "request_completed"]
    routes = []
    for e in completed:
        route = validate_route(e["response"], model)
        if route["selected_provider"] != "Alibaba":
            raise RuntimeError(f"unexpected smoke provider: {route}")
        if (e["response"].get("usage") or {}).get("cost") is None:
            raise RuntimeError("smoke response missing usage.cost")
        routes.append(route)
    message = completed[-1]["response"]["choices"][0]["message"]
    atomic_json(OUT / "paid_smoke_summary.json", {
        "status": "passed", "eval_version": EVAL_VERSION, "model": model,
        "row": row, "routes": routes,
        "usage": [(e.get("usage") or {}) | {"response_id": e["response"].get("id")} for e in completed],
        "reasoning_tokens": [(e["response"]["choices"][0]["message"] or {}).get("reasoning")
                             for e in completed][:1],
        "records": str(smoke_records), "budget": update_state(lambda s: s)})
    print(f"paid smoke passed: refusal statuses = "
          f"{[q['outcome'] for q in row.values()].count('refused')} of {len(row)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--offline-smoke", action="store_true")
    actions.add_argument("--offline-regression", action="store_true")
    actions.add_argument("--write-manifest", action="store_true")
    actions.add_argument("--paid-smoke", action="store_true")
    actions.add_argument("--run", action="store_true")
    actions.add_argument("--analyze", action="store_true")
    parser.add_argument("--i-authorize-paid-calls", action="store_true",
                        help="required for --paid-smoke/--run; sets the paid-call opt-in")
    args = parser.parse_args()
    battery, child_rows = build_battery()
    if args.offline_smoke:
        offline_smoke(battery)
    if args.offline_regression:
        offline_regression(battery)
    if args.write_manifest:
        write_manifest(battery)
    if args.paid_smoke or args.run:
        if not args.i_authorize_paid_calls:
            raise SystemExit("--paid-smoke/--run cost money and require --i-authorize-paid-calls")
        os.environ[PAID_OPTIN_ENV] = "1"
    if args.paid_smoke:
        paid_smoke(battery)
    if args.run:
        run(battery)
    if args.analyze:
        analyze()


def run(battery: list[dict]) -> None:
    pids = {m: protocol_id(m, battery) for m in MODELS}
    results = {"schema": 1, "eval_version": EVAL_VERSION, "models": [], "not_published": True,
               "merge_into_primary": False}
    for model in MODELS:
        summary = asyncio.run(run_model(model, battery, pids[model]))
        results["models"].append(summary)
        atomic_json(RESULTS, results)
    state = update_state(lambda value: value.update({"finished_utc": datetime.now(UTC).isoformat()}))
    saved = json.loads(RESULTS.read_text())
    atomic_json(RESULTS, saved | {"budget": {
        "provider_reported_spent_usd": state["provider_reported_spent_usd"],
        "conservative_spent_usd": state["conservative_spent_usd"],
        "failed_phases_charged_at_bound": state["failed_phases_charged_at_bound"]}})
    print("panel complete")


def analyze() -> None:
    raise SystemExit("analysis is implemented after the full run; see the preregistration")


if __name__ == "__main__":
    main()
