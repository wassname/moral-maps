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
from moralmaps.iw_axes import X_AXIS, Y_AXIS, positiveness, resolve_items
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
    # child: refused flag is separate from the 0..5 selected list; zero selections with refused=false
    # is a valid substantive "none of these" answer (the human stem says "Which, if any").
    return {"type": "json_schema", "json_schema": {"name": "wvs_respondent_packet", "strict": True,
            "schema": {"type": "object", "properties": {
                "answers": {"type": "object", "properties": ordinary,
                            "required": list(ordinary), "additionalProperties": False},
                "child_qualities": {"type": "object", "properties": {
                    "refused": {"type": "boolean"},
                    "selected": {"type": "array",
                                 "items": {"type": "string", "enum": child["options"]},
                                 "minItems": 0, "maxItems": 5, "uniqueItems": True}},
                    "required": ["refused", "selected"], "additionalProperties": False}},
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
    answers, child = raw.get("answers"), raw.get("child_qualities")
    if not isinstance(answers, dict) or not isinstance(child, dict):
        return None
    qualities, child_refused = child.get("selected"), child.get("refused")
    if not isinstance(qualities, list) or not isinstance(child_refused, bool):
        return None
    row = {}
    for q in battery:
        if q["id"] == "ChildQualities":
            if (len(qualities) > 5 or len(set(qualities)) != len(qualities)
                    or not set(qualities) <= set(q["options"])):
                return None
            if child_refused and qualities:
                return None  # a refusal selects nothing
            row["ChildQualities"] = {"outcome": "refused" if child_refused else "substantive",
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
            '{"answers": {"<question id>": {"selected": "<option or \'refused\'>"}}, '
            '"child_qualities": {"refused": <true|false>, "selected": [up to five quality names]}}. '
            "If you refuse the child question, set refused=true and selected=[]. "
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


INPUT_RESERVE_TOKENS = 1024
OUTPUT_RESERVE_TOKENS = 2048


def request_bound(model: str) -> Decimal:
    """Reserve bound for ONE API phase (initial call, rescue, or retry attempt): 1,024 input +
    2,048 output tokens at the saved Alibaba prices. The manifest 'panel bound' multiplies this by
    the 512 initial calls only; rescue and retry phases each reserve ANOTHER such bound, and the
    USD 5 stage stop (checked on every reserve) remains the authoritative all-in limit."""
    endpoint = standard_endpoint(model)
    bound = (Decimal(INPUT_RESERVE_TOKENS) * Decimal(endpoint["pricing"]["prompt"])
             + Decimal(OUTPUT_RESERVE_TOKENS) * Decimal(endpoint["pricing"]["completion"]))
    return bound


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
            zero_selection = 0
            for o in substantive:
                for sel in o["selected"]:
                    counts[sel] += 1
                if not o["selected"]:
                    zero_selection += 1
            per_question[q["id"]] = {"n": len(outcomes), "substantive": len(substantive),
                                     "refused": len(refused),
                                     "zero_selection_substantive": zero_selection,
                                     "zero_selection_or_refusal": zero_selection + len(refused),
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
    zero_or_refused = sum(q.get("zero_selection_or_refusal", q["refused"]) for q in per_question.values())
    return {"model": model, "eval_version": EVAL_VERSION, "protocol_id": pid, "records": str(rpath),
            "valid_packets": len(rows),
            "refusal_rate_overall": sum(q["refused"] for q in per_question.values())
            / sum(q["n"] for q in per_question.values()),
            "zero_selection_or_refusal_rate_overall": zero_or_refused
            / sum(q["n"] for q in per_question.values()),
            "per_question": per_question}


def write_manifest(battery: list[dict]) -> dict:
    catalog = {r["id"]: r for r in json.loads(MODEL_CATALOG.read_text())["data"]}
    rows, total = [], Decimal(0)
    smoke_model = MODELS[3]
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
    smoke_bound = request_bound(smoke_model)
    payload = {"schema": 2, "eval_version": EVAL_VERSION,
               "created_utc": datetime.now(UTC).isoformat(), "models": rows,
               "battery": [{"id": q["id"], "question": q["question"], "options": q["options"]}
                           for q in battery],
               "instrument_status": ("GlobalOpinionQA-compatible approximation; 11th quality "
                                     "Religious faith appended; card order not recorded in source"),
               "n_packets": N_PACKETS, "max_tokens": MAX_TOKENS, "temperature": 1.0,
               "reserve_bound_formula": ("per API phase: 1,024 input + 2,048 output tokens at the "
                                         "saved Alibaba per-token prices; the panel bound covers "
                                         "the 512 initial calls only, rescue/retry phases each "
                                         "reserve another bound, and the USD 5 stage stop is the "
                                         "authoritative all-in limit"),
               "panel_requests": N_PACKETS * len(MODELS), "smoke_requests": 1,
               "smoke_model": smoke_model,
               "smoke_reserve_bound_usd": str(smoke_bound),
               "panel_reserve_bound_usd": str(total),
               "panel_plus_smoke_bound_usd": str(total + smoke_bound),
               "endpoint_provenance": ("endpoints and pricing from the authenticated 2026-09-18 "
                                       "snapshot; the unauthenticated live models GET returns "
                                       "endpoints=null, so the paid smoke is the current live "
                                       "route test"),
               "stage_hard_stop_usd": str(STAGE_CAP_USD),
               "refusal_rule": ("ordinary: per-question \"refused\" status inside the schema, "
                                "never displayed as an option; child: separate refused flag plus "
                                "a 0..5 selected list, zero selections with refused=false is a "
                                "valid substantive none; all refusals reported separately, never "
                                "neutral"),
               "not_published": True, "merge_into_primary": False}
    atomic_json(MANIFEST, payload)
    return payload


def offline_smoke(battery: list[dict], child_rows: list[dict]) -> None:
    valid = {"answers": {q["id"]: {"selected": q["options"][0]} for q in battery
                         if q["id"] != "ChildQualities"},
             "child_qualities": {"refused": False, "selected": ["Independence", RELIGIOUS_FAITH]}}
    row = parse_packet(battery, json.dumps(valid))
    assert row is not None and row["ChildQualities"]["selected"] == ["Independence", RELIGIOUS_FAITH]
    assert row["ChildQualities"]["outcome"] == "substantive"
    assert all(row[q["id"]]["outcome"] == "substantive" for q in battery if q["id"] != "ChildQualities")
    # zero selections with refused=false: valid substantive "none", NOT refusal
    none = {"answers": {q["id"]: {"selected": q["options"][0]} for q in battery
                        if q["id"] != "ChildQualities"},
            "child_qualities": {"refused": False, "selected": []}}
    row = parse_packet(battery, json.dumps(none))
    assert row is not None and row["ChildQualities"] == {"outcome": "substantive", "selected": []}
    # refused=true with empty selection: refusal
    refused = {"answers": {q["id"]: {"selected": REFUSED} for q in battery
                           if q["id"] != "ChildQualities"},
               "child_qualities": {"refused": True, "selected": []}}
    row = parse_packet(battery, json.dumps(refused))
    assert row is not None and all(v["outcome"] == "refused" for v in row.values())
    bad = {"answers": {"nonexistent": {"selected": "x"}},
           "child_qualities": {"refused": False, "selected": []}}
    assert parse_packet(battery, json.dumps(bad)) is None
    assert parse_packet(battery, "garbage") is None
    over = {"answers": valid["answers"],
            "child_qualities": {"refused": False,
                                "selected": next(q for q in battery
                                                 if q["id"] == "ChildQualities")["options"][:6]}}
    assert parse_packet(battery, json.dumps(over)) is None
    dup = {"answers": valid["answers"],
           "child_qualities": {"refused": False, "selected": [RELIGIOUS_FAITH, RELIGIOUS_FAITH]}}
    assert parse_packet(battery, json.dumps(dup)) is None
    inconsistent = {"answers": valid["answers"],
                    "child_qualities": {"refused": True, "selected": [RELIGIOUS_FAITH]}}
    assert parse_packet(battery, json.dumps(inconsistent)) is None
    # refusal sentinel must not collide with a listed option
    for q in battery:
        assert REFUSED not in q["options"], q["id"]
    # rescue-format fixture: the force message describes the exact object schema and its output parses
    rescue_text = ('{"answers": {' + ", ".join(
        f'"{q["id"]}": {{"selected": "{q["options"][0]}"}}' for q in battery
        if q["id"] != "ChildQualities") +
        '}, "child_qualities": {"refused": false, "selected": ["Independence"]}}')
    row = parse_packet(battery, rescue_text)
    assert row is not None and row["ChildQualities"]["selected"] == ["Independence"]
    assert force_msg(battery).find("refused") != -1
    # child refusal vs zero-selection produce DIFFERENT item vectors: refusal is a zero vector
    # (excluded from the mean), substantive none is all Not-mentioned
    rows_fixture = {0: {"ChildQualities": {"outcome": "refused", "selected": []}},
                    1: {"ChildQualities": {"outcome": "substantive", "selected": []}}}
    for q in battery:
        if q["id"] != "ChildQualities":
            for r in rows_fixture.values():
                r[q["id"]] = {"outcome": "substantive", "selected": q["options"][0]}
    lists = packet_item_lists(rows_fixture, battery, child_rows)
    for quality in PANEL_QUALITIES:
        refusal_vec, none_vec = lists[quality][0], lists[quality][1]
        assert refusal_vec.sum() == 0, "refusal must be a zero vector (excluded)"
        assert none_vec.sum() > 0 and none_vec.min() == 0.0, (
            "substantive none is all Not-mentioned, not a zero vector")
    # deterministic fixture detecting accidental cross-model index sharing in coords_draws
    shared_lists = {m: {"Homosexuality": [np.array([1.0, 0.0]), np.array([0.0, 1.0])],
                        "Obedience": [np.array([1.0, 0.0]), np.array([0.0, 1.0])]}
                    for m in MODELS}
    # model A's coordinate depends on row 0 vs 1 oppositely to model B's: build via distinct items
    fake_resolved = {X_AXIS: [{"suffix": "Homosexuality", "pole_idx": 0, "n": 2}],
                     Y_AXIS: [{"suffix": "Obedience", "pole_idx": 0, "n": 2}]}
    # invert model B's rows so shared indices force perfect anti-correlation
    shared_lists[MODELS[1]]["Homosexuality"] = [np.array([0.0, 1.0]), np.array([1.0, 0.0])]
    draws = coords_draws(shared_lists, fake_resolved, B=200, seed=3)
    both_low = np.sum((draws[:, 0, 0] < 0.5) & (draws[:, 1, 0] < 0.5))
    assert both_low > 0, "cross-model index sharing detected (A and B always anti-correlated)"
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
    if not reserve({"id": smoke_rid, "lane": "alibaba", "reserve_usd": "0.05"}):
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
    actions.add_argument("--synthetic-analysis-test", action="store_true")
    parser.add_argument("--i-authorize-paid-calls", action="store_true",
                        help="required for --paid-smoke/--run; sets the paid-call opt-in")
    args = parser.parse_args()
    battery, child_rows = build_battery()
    if args.offline_smoke:
        offline_smoke(battery, child_rows)
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
        analyze_real()
    if args.synthetic_analysis_test:
        synthetic_analysis_test(battery, child_rows)


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


def release_years() -> np.ndarray:
    catalog = {r["id"]: r for r in json.loads(MODEL_CATALOG.read_text())["data"]}
    def decimal_year(ts: int) -> float:
        d = datetime.fromtimestamp(ts, tz=timezone.utc)
        jan = datetime(d.year, 1, 1, tzinfo=timezone.utc)
        nxt = datetime(d.year + 1, 1, 1, tzinfo=timezone.utc)
        return d.year + (d - jan).total_seconds() / (nxt - jan).total_seconds()
    return np.array([decimal_year(catalog[m]["created"]) for m in MODELS])


class NoSubstantive(Exception):
    """A bootstrap draw left an item with zero substantive rows."""


def analyze() -> None:
    raise SystemExit("replaced; see analyze_real")


DENSE_LEDGER = Path("slop/research/wvs/20260916_openrouter/wvs_iw_requests.jsonl")


def dense_qwen_psamples() -> dict[str, dict[str, list[np.ndarray]]]:
    """model -> item suffix -> per-rating-sample p vectors, from the canonical dense-v1 ledger."""
    run_ids = {e["model"]: e["run_id"] for e in
               json.loads(DENSE_CACHE.read_text())["completed"].values()
               if e.get("model") in MODELS}
    if len(run_ids) != len(MODELS):
        raise RuntimeError(f"dense cache lacks runs for: {set(MODELS) - set(run_ids)}")
    out = {m: {} for m in MODELS}
    for line in DENSE_LEDGER.read_text().splitlines():
        r = json.loads(line)
        if (r.get("event") == "item_result" and r.get("run_id") in run_ids.values()
                and r.get("model") in MODELS):
            out[r["model"]][r["id"]] = [np.asarray(v) for v in r["p_samples"]]
    for m in MODELS:
        if len(out[m]) != 12:
            raise RuntimeError(f"dense item set incomplete for {m}: {len(out[m])}")
    return out


def packet_item_lists(rows: dict[int, dict], battery: list[dict],
                      child_rows: list[dict]) -> dict[str, list[np.ndarray]]:
    """One vector per packet per scored item; refused packets contribute a zero vector (excluded
    from the mean by the positivity of the mean, and coverage counts them)."""
    from wvs_original_choice_pilot import child_binary_rows
    binaries = child_binary_rows(child_rows)
    out = {}
    for q in battery:
        if q["id"] == "ChildQualities":
            for quality in PANEL_QUALITIES:
                opts = binaries[quality]
                vecs = []
                for k in sorted(rows):
                    entry = rows[k]["ChildQualities"]
                    if entry["outcome"] == "refused":
                        vecs.append(np.zeros(len(opts)))  # excluded, like an ordinary refusal
                    else:
                        mentioned = quality in entry["selected"]
                        vecs.append(np.array([1.0 if o == "Important" else 0.0 for o in opts])
                                    if mentioned else
                                    np.array([0.0 if o == "Important" else 1.0 for o in opts]))
                out[quality] = vecs
            continue
        vecs = []
        for k in sorted(rows):
            entry = rows[k][q["id"]]
            vec = np.zeros(len(q["options"]))
            if entry["outcome"] == "substantive":
                vec[q["options"].index(entry["selected"])] = 1.0
            vecs.append(vec)
        out[q["id"]] = vecs
    return out


def coords_draws(item_lists: dict[str, dict[str, list[np.ndarray]]], resolved: dict,
                 B: int = 1000, seed: int = 17, row_linked: bool = True) -> np.ndarray:
    """(B, n_models, 2) coordinate draws.

    row_linked=True (packet protocol): resample whole respondent rows, one index draw shared across
    all items, preserving cross-question covariance. row_linked=False (dense v1): resample each
    item's rating vectors independently; dense samples are not row-linked."""
    n = len(next(iter(next(iter(item_lists.values())).values())))
    rng = np.random.default_rng(seed)
    out = np.empty((B, len(MODELS), 2))
    for b in range(B):
        for k, m in enumerate(MODELS):
            # whole-row resampling is independent per model: a shared seed schedule does NOT make
            # different models' pseudo-respondents the same respondent. Indices are shared across
            # questions only WITHIN a model (preserving that model's cross-question covariance).
            idx = rng.integers(0, n, n) if row_linked else None
            xy = []
            for axis in (X_AXIS, Y_AXIS):
                vals = []
                for it in resolved[axis]:
                    lists = item_lists[m][it["suffix"]]
                    draw_idx = idx if row_linked else rng.integers(0, n, n)
                    mean_p = np.mean([lists[j] for j in draw_idx], axis=0)
                    if mean_p.sum() == 0:
                        raise NoSubstantive(f"{m} {it['suffix']} has no substantive rows in this draw")
                    vals.append(positiveness(mean_p[None, :], it["pole_idx"], it["n"]))
                xy.append(float(np.mean(vals)))
            out[b, k] = xy
    return out


def constant_and_linear_rmse(coords: np.ndarray) -> tuple[float, float]:
    """2D residual RMSE of the n_models coordinates around (a) the family centroid and (b) the
    release-date OLS line."""
    x = release_years()
    centroid = coords.mean(axis=0)
    constant = float(np.sqrt(np.mean(np.sum((coords - centroid) ** 2, axis=1))))
    residuals = []
    for k in range(2):
        slope, intercept = np.polyfit(x, coords[:, k], 1)
        residuals.append(coords[:, k] - (slope * x + intercept))
    linear = float(np.sqrt(np.mean(np.sum(np.stack(residuals, axis=1) ** 2, axis=1))))
    return constant, linear


def loo_prediction_error(coords: np.ndarray) -> dict:
    """Leave-one-release-out prediction error (mean 2D distance) for the constant (family centroid
    of the other releases) vs linear (OLS on the other releases) predictor. With n=4 the linear
    fit has 1 residual dof and is expected to overfit; this makes that visible."""
    x = release_years()
    const_errs, lin_errs = [], []
    for i in range(len(MODELS)):
        others = [j for j in range(len(MODELS)) if j != i]
        const_pred = coords[others].mean(axis=0)
        slopes = [np.polyfit(x[others], coords[others, k], 1) for k in range(2)]
        lin_pred = np.array([slopes[k][0] * x[i] + slopes[k][1] for k in range(2)])
        const_errs.append(float(np.linalg.norm(coords[i] - const_pred)))
        lin_errs.append(float(np.linalg.norm(coords[i] - lin_pred)))
    return {"constant_loo_mean": float(np.mean(const_errs)),
            "linear_loo_mean": float(np.mean(lin_errs)),
            "constant_loo_per_release": const_errs, "linear_loo_per_release": lin_errs}


def analyze_from_data(packet_rows: dict[str, dict[int, dict]], battery: list[dict],
                      child_rows: list[dict], resolved: dict) -> dict:
    """The fixed preregistered analysis, run on real or synthetic rows."""
    per_model, item_lists = {}, {}
    for m in MODELS:
        rows = packet_rows[m]
        if len(rows) != N_PACKETS:
            raise RuntimeError(f"{m}: expected {N_PACKETS} rows, got {len(rows)}")
        il = packet_item_lists(rows, battery, child_rows)
        item_lists[m] = il
        refused = {q["id"]: sum(1 for k in sorted(rows) if rows[k][q["id"]]["outcome"] == "refused")
                   for q in battery}
        child_refused = refused["ChildQualities"]
        child_zero_substantive = sum(
            1 for k in sorted(rows) if rows[k]["ChildQualities"]["outcome"] == "substantive"
            and not rows[k]["ChildQualities"]["selected"])
        per_model[m] = {"refused_per_question": refused,
                        "refusal_rate": sum(refused.values()) / (len(refused) * N_PACKETS),
                        "coverage_per_question": {q["id"]: 1 - refused[q["id"]] / N_PACKETS
                                                  for q in battery},
                        "child_refusal_rate": child_refused / N_PACKETS,
                        "child_zero_selection_substantive_rate": child_zero_substantive / N_PACKETS,
                        "child_zero_selection_or_refusal_rate":
                        (child_refused + child_zero_substantive) / N_PACKETS}
    draws = coords_draws(item_lists, resolved)
    point = draws.mean(axis=0)
    se = draws.std(axis=0)
    constant, linear = constant_and_linear_rmse(point)
    # bootstrap scatter distributions
    constant_draws = np.empty(draws.shape[0]); linear_draws = np.empty(draws.shape[0])
    for b in range(draws.shape[0]):
        constant_draws[b], linear_draws[b] = constant_and_linear_rmse(draws[b])
    # noise floors: H0 = no between-release differences; draw each release from N(0, SE)
    rng = np.random.default_rng(23)
    floor_const, floor_lin = np.empty(2000), np.empty(2000)
    for b in range(2000):
        ys = np.array([rng.normal(0.0, se[k]) for k in range(len(MODELS))])
        floor_const[b], floor_lin[b] = constant_and_linear_rmse(ys)
    dense = dense_qwen_psamples()
    dense_item_lists = {m: {k: list(v) for k, v in dense[m].items()} for m in MODELS}
    dense_draws = coords_draws(dense_item_lists, resolved, seed=29, row_linked=False)
    dense_point = dense_draws.mean(axis=0)
    dense_se = dense_draws.std(axis=0)
    dense_constant, dense_linear = constant_and_linear_rmse(dense_point)
    dense_constant_draws = np.empty(draws.shape[0]); dense_linear_draws = np.empty(draws.shape[0])
    for b in range(draws.shape[0]):
        dense_constant_draws[b], dense_linear_draws[b] = constant_and_linear_rmse(dense_draws[b])
    rng2 = np.random.default_rng(31)
    dense_floor_const, dense_floor_lin = np.empty(2000), np.empty(2000)
    for b in range(2000):
        ys = np.array([rng2.normal(0.0, dense_se[k]) for k in range(len(MODELS))])
        dense_floor_const[b], dense_floor_lin[b] = constant_and_linear_rmse(ys)
    release_years_list = release_years().tolist()
    return {
        "eval_version": EVAL_VERSION, "n_packets": N_PACKETS,
        "release_years": release_years_list,
        "packet": {
            "coords_xy_per_model": {m: [float(v) for v in point[k]] for k, m in enumerate(MODELS)},
            "coord_se": {m: [float(v) for v in se[k]] for k, m in enumerate(MODELS)},
            "constant_family_rmse": constant, "constant_family_rmse_se": float(np.std(constant_draws)),
            "linear_trend_rmse": linear, "linear_trend_rmse_se": float(np.std(linear_draws)),
            "constant_noise_floor_mean": float(np.mean(floor_const)),
            "linear_noise_floor_mean": float(np.mean(floor_lin)),
            "p_constant_noise_ge_observed": float(np.mean(floor_const >= constant)),
            "p_linear_noise_ge_observed": float(np.mean(floor_lin >= linear)),
            "loo": loo_prediction_error(point),
            "refusal": {m: per_model[m]["refusal_rate"] for m in MODELS},
            "coverage": {m: per_model[m]["coverage_per_question"] for m in MODELS},
            "child_diagnostics": {m: {k: per_model[m][k] for k in (
                "child_refusal_rate", "child_zero_selection_substantive_rate",
                "child_zero_selection_or_refusal_rate")} for m in MODELS},
        },
        "dense_v1": {
            "coords_xy_per_model": {m: [float(v) for v in dense_point[k]] for k, m in enumerate(MODELS)},
            "coord_se": {m: [float(v) for v in dense_se[k]] for k, m in enumerate(MODELS)},
            "constant_family_rmse": dense_constant,
            "constant_family_rmse_se": float(np.std(dense_constant_draws)),
            "linear_trend_rmse": dense_linear, "linear_trend_rmse_se": float(np.std(dense_linear_draws)),
            "constant_noise_floor_mean": float(np.mean(dense_floor_const)),
            "linear_noise_floor_mean": float(np.mean(dense_floor_lin)),
            "p_constant_noise_ge_observed": float(np.mean(dense_floor_const >= dense_constant)),
            "p_linear_noise_ge_observed": float(np.mean(dense_floor_lin >= dense_linear)),
            "loo": loo_prediction_error(dense_point),
            "bootstrap_note": ("item-wise independent resampling of the 6 rating vectors per item; "
                               "dense samples are not row-linked, so protocols are not pairable and "
                               "differences use independent bootstraps"),
        },
        "coord_shifts_packet_minus_dense": {m: [float(a - b) for a, b in zip(point[k], dense_point[k])]
                                            for k, m in enumerate(MODELS)},
    }


def load_wvs_recs() -> list[dict]:
    from wvs_map import load_wvs_all
    return load_wvs_all()


def analyze_real() -> None:
    battery, child_rows = build_battery()
    resolved = resolve_items(load_wvs_recs())
    packet_rows = {}
    for m in MODELS:
        rpath = OUT / "records" / m.replace("/", "__") / "packets.jsonl"
        packet_rows[m] = prior_rows(rpath, protocol_id(m, battery))
    analysis = analyze_from_data(packet_rows, battery, child_rows, resolved)
    atomic_json(OUT / "analysis.json", analysis)
    print(json.dumps({"packet": {k: analysis["packet"][k]
                                 for k in ("constant_family_rmse", "linear_trend_rmse", "loo")},
                      "dense": {k: analysis["dense_v1"][k]
                                for k in ("constant_family_rmse", "linear_trend_rmse", "loo")}},
                     indent=2))


def synthetic_analysis_test(battery: list[dict], child_rows: list[dict]) -> None:
    """End-to-end analysis on synthetic data: refusal semantics, covariance preservation, fits,
    floors, and LOO all exercise without any paid call."""
    resolved = resolve_items(load_wvs_recs())
    rng = np.random.default_rng(5)
    options = {q["id"]: q["options"] for q in battery}
    packet_rows = {}
    for k, m in enumerate(MODELS):
        rows = {}
        for p in range(N_PACKETS):
            row = {}
            for q in battery:
                if q["id"] == "ChildQualities":
                    pool = q["options"]
                    if rng.random() < 0.03:
                        row[q["id"]] = {"outcome": "refused", "selected": []}
                    else:
                        picked = list(rng.choice(pool, size=rng.integers(0, 6), replace=False))
                        row[q["id"]] = {"outcome": "substantive", "selected": picked}
                else:
                    if rng.random() < 0.05 * (k + 1):
                        row[q["id"]] = {"outcome": "refused", "selected": REFUSED}
                    else:
                        # drift with release index k so the linear fit has signal
                        j = min(len(q["options"]) - 1, max(0, int(rng.normal(k * 0.8, 1.5))))
                        row[q["id"]] = {"outcome": "substantive", "selected": q["options"][j]}
            rows[p] = row
        packet_rows[m] = rows
    result = analyze_from_data(packet_rows, battery, child_rows, resolved)
    for section in ("packet", "dense_v1"):
        for key in ("constant_family_rmse", "linear_trend_rmse", "loo"):
            value = result[section][key]
            assert np.isfinite(value if not isinstance(value, dict) else
                               value["constant_loo_mean"] + value["linear_loo_mean"]), (section, key)
    assert result["packet"]["refusal"][MODELS[3]] > result["packet"]["refusal"][MODELS[0]]
    print(f"synthetic analysis passed: packet constant={result['packet']['constant_family_rmse']:.4f} "
          f"linear={result['packet']['linear_trend_rmse']:.4f}; "
          f"dense constant={result['dense_v1']['constant_family_rmse']:.4f}; "
          f"packet LOO const={result['packet']['loo']['constant_loo_mean']:.4f} "
          f"lin={result['packet']['loo']['linear_loo_mean']:.4f}")


if __name__ == "__main__":
    main()
