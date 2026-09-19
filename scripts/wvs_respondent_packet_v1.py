#!/usr/bin/env python3
"""wvs-respondent-packet-v2: ONE API call = ONE coherent pseudo-respondent answering the complete
selected WVS battery (8 ordinary single-choice questions + the 11-quality choose-up-to-five child
list) in canonical order. -- PI[gpt-5.6-terra]

V2 (owner-corrected) administration: the questionnaire never suggests refusal, inability, or AI
identity; the response schema permits ONLY the listed substantive options (ordinary) and ONLY a
0..5 array of listed qualities (child). Refusal is therefore an OBSERVED outcome, recorded only
when the model/API produces no usable value despite that schema (empty/no content, no JSON, or
nonconforming output); it is never a schema value, never shown as an option, never scored as
neutral, and never rescued into an answer. Only clearly syntactic malformed output (unparseable
JSON) is rescued once; if syntactic vs substantive cannot be distinguished, record refusal.
Each ordinary selection and the child selection also carry a required short English reason of at most eight words; reasons are qualitative audit fields only and are never scored. A missing/too-long reason is a format failure that preserves and scores the selected answer, never a new refusal channel. Child [] is a substantive zero-selection ("Which, if any"). Zero-substantive-coverage collapse is
handled explicitly: unavailable point coordinates, invalid bootstrap draws, unavailable
family/trend/LOO metrics with valid-draw counts, never a crash or a fit of the remaining releases.

Why v1 stopped: the v1 smoke (kept as a failed design diagnostic, paid_smoke.jsonl) showed
qwen3.7-plus explicitly refusing all 9 questions when the prompt/schema offered a "refused" token;
the owner ruled the escape hatch a protocol problem and removed it in v2.

Instrument status: the child-quality list is a GlobalOpinionQA-compatible APPROXIMATION -- the
saved source has 10 of the standard 11 qualities; "Religious faith" (standard WVS, absent from the
saved source) is appended as the 11th item, and the saved source does not record the human card
order, so list order is the saved source order plus that documented append.
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

import dotenv  # import only; load_dotenv() runs solely in the authorized paid CLI path
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

EVAL_VERSION = "wvs-respondent-packet-v2"
MODELS = ("qwen/qwen3.5-plus-02-15", "qwen/qwen3.6-plus",
          "qwen/qwen3.5-plus-20260420", "qwen/qwen3.7-plus")
PROVIDER = {"only": ["Alibaba"], "allow_fallbacks": False, "require_parameters": True}
N_PACKETS = 128
MAX_TOKENS = 2048
REQUEST_TIMEOUT = 600
TRANSPORT_TIMEOUT = 240
MAX_ATTEMPTS = 3
STAGE_CAP_USD = Decimal("5")
REFUSED = "refused"  # legacy v1 token; retained only so v1 smoke artifacts stay readable
REASON_MAX_WORDS = 8
REASON_RULE_V2 = ("each ordinary selection and the child selection include a required short English "
                  "reason of one to eight whitespace-delimited words; reasons are qualitative audit "
                  "fields only and are never scored")
REFUSAL_RULE_V2 = ("v2: neither the visible prompt nor the JSON schema offers refusal, null or "
                   "missing as an answer; ordinary answers select one listed option and then give a "
                   "short reason, while the child field selects 0..5 of the 11 listed qualities ([] "
                   "is a substantive none) and then gives a short reason. Refusal is recorded only "
                   "when the model/API produces no usable selection despite the schema (empty/no "
                   "content, no JSON, or nonconforming selections); refusals are reported separately, "
                   "never scored as neutral, and never rescued. A missing/too-long reason is a "
                   "qualitative format failure: its selected answer is retained and scored, its raw "
                   "response is retained for audit, and it is never rescued; only clearly syntactic "
                   "malformed output (unparseable or truncated JSON) is rescued once")
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
    """V2 questionnaire: never mentions refusal, inability, AI identity, or any escape token.
    Every selection comes first, followed by its short qualitative reason."""
    blocks = []
    for number, q in enumerate(battery, 1):
        if q["id"] == "ChildQualities":
            opts = "\n".join(f"   {j}. {o}" for j, o in enumerate(q["options"], 1))
            blocks.append(f"{number}. {q['question']}\n{opts}\n"
                          "Choose up to five; give an empty list if none. Then give a short English "
                          "reason in at most eight words.")
        else:
            opts = "\n".join(f"   {chr(64 + j)}. {o}" for j, o in enumerate(q["options"], 1))
            blocks.append(f"{number}. {q['question']}\n{opts}\n"
                          "Choose exactly one option; if none fits exactly, choose the closest. Then "
                          "give a short English reason in at most eight words.")
    return ("You are one person answering a social values survey. Answer every question as yourself, "
            "in order: choose the listed answer first, then give its short reason. "
            "Return one JSON object matching the required schema.\n\n"
            + "\n\n".join(blocks))


def packet_schema(battery: list[dict]) -> dict:
    """V2 schema permits ONLY substantive listed values plus required audit reasons. Ordinary
    enums remain exactly the listed options; the child selection remains a 0..5 array of listed
    qualities. The schema never advertises an escape. No array-uniqueness keyword (Alibaba rejects
    it); duplicates are invalid in parse_packet. Word count is parser-enforced, not schema-enforced."""
    reason = {"type": "string", "minLength": 1, "description": "short English reason, at most eight words"}
    child = next(q for q in battery if q["id"] == "ChildQualities")
    ordinary = {q["id"]: {"type": "object",
                          "properties": {"selected": {"type": "string", "enum": q["options"]},
                                         "reason": reason},
                          "required": ["selected", "reason"], "additionalProperties": False}
                for q in battery if q["id"] != "ChildQualities"}
    return {"type": "json_schema", "json_schema": {"name": "wvs_respondent_packet", "strict": True,
            "schema": {"type": "object", "properties": {
                "answers": {"type": "object", "properties": ordinary,
                            "required": list(ordinary), "additionalProperties": False},
                "child_qualities": {"type": "object", "properties": {
                    "selected": {"type": "array", "items": {"type": "string", "enum": child["options"]},
                                 "minItems": 0, "maxItems": 5},
                    "reason": reason}, "required": ["selected", "reason"],
                    "additionalProperties": False}},
                "required": ["answers", "child_qualities"], "additionalProperties": False}}}


def refusal_row(battery: list[dict]) -> dict:
    """Packet-level refusal: no usable value anywhere; every question is refused (observed, not
    scored as neutral)."""
    return {q["id"]: {"outcome": "refused", "selected": None, "reason": None,
                     "reason_status": "not_available"} for q in battery}


def reason_status(value: object) -> str:
    """Reasons are audit-only. Whitespace-delimited count matches the preregistered rule."""
    if not isinstance(value, str) or not value.split():
        return "missing"
    return "valid" if len(value.split()) <= REASON_MAX_WORDS else "too_long"


def substantive_row(selected: object, reason: object) -> dict:
    status = reason_status(reason)
    return {"outcome": "substantive", "selected": selected, "reason": reason,
            "reason_status": status}


def parse_packet(battery: list[dict], text: str) -> tuple[dict | None, str | None, bool]:
    """Classify one response. Returns (row, refusal_kind, rescueable).

    - (refusal_row, kind, False): no usable value despite the schema -> OBSERVED refusal, never
      rescued. kind: 'empty_content' (empty/no content), 'no_json' (a plain-text reply with no
      JSON object), or 'nonconforming' (parsed but structure/values outside the substantive
      space; offending questions are refused, conforming questions keep their answers).
    - a valid selected answer with a missing/too-long reason remains substantive and scored, but
      gets kind 'reason_format_failure' and is retained with its raw response for qualitative audit;
      it is never rescued.
    - (None, None, True): clearly syntactic malformed output (an apparent JSON object that fails
      to parse, or visibly truncated output with unbalanced braces) -> repairable, rescue once.
    Deterministic rule: if syntactic vs substantive cannot be distinguished, it is a refusal.
    """
    if not (text or "").strip():
        return refusal_row(battery), "empty_content", False
    objs = re.findall(r"\{.*\}", text, re.S)
    truncated = text.count("{") > text.count("}")
    if not objs and not truncated:
        return refusal_row(battery), "no_json", False
    try:
        raw = json.loads(objs[-1])
    except (json.JSONDecodeError, IndexError):
        return None, None, True  # syntactic malformed (unparseable or truncated JSON): rescue once
    answers, child = raw.get("answers"), raw.get("child_qualities")
    if not isinstance(answers, dict) or not isinstance(child, dict):
        return refusal_row(battery), "nonconforming", False
    row = {}
    for q in battery:
        if q["id"] == "ChildQualities":
            selected, reason = child.get("selected"), child.get("reason")
            if (isinstance(selected, list) and len(selected) <= 5 and len(set(selected)) == len(selected)
                    and set(selected) <= set(q["options"])):
                row[q["id"]] = substantive_row(selected, reason)
            else:
                row[q["id"]] = {"outcome": "refused", "selected": None, "reason": reason,
                                 "reason_status": "not_available"}
            continue
        answer = answers.get(q["id"])
        selected = answer.get("selected") if isinstance(answer, dict) else None
        reason = answer.get("reason") if isinstance(answer, dict) else None
        if selected in q["options"]:
            row[q["id"]] = substantive_row(selected, reason)
        else:
            row[q["id"]] = {"outcome": "refused", "selected": None, "reason": reason,
                             "reason_status": "not_available"}
    outcomes = [v["outcome"] for v in row.values()]
    reasons = [v["reason_status"] for v in row.values()]
    kind = ("nonconforming" if "refused" in outcomes else
            "reason_format_failure" if any(status != "valid" for status in reasons) else None)
    return row, kind, False


def force_msg(battery: list[dict]) -> str:
    """Rescue demand for syntactic malformed output only; describes the exact v2 schema and never
    mentions refusal."""
    ids = ", ".join(f'"{q["id"]}"' for q in battery)
    return ("Output ONLY the compact JSON respondent object now: "
            '{"answers": {"<question id>": {"selected": "<one listed option>", '
            '"reason": "<short English reason>"}}, "child_qualities": '
            '{"selected": [up to five quality names], "reason": "<short English reason>"}}. '
            f"Every required question key must appear exactly once: {ids}. "
            "Choose each answer first; each reason must be at most eight words. "
            "No markdown, no reasoning, nothing else.")


def paired_seeds(count: int) -> list[int]:
    seeds = []
    for sequence in range(count):
        digest = hashlib.sha256(f"{EVAL_VERSION}|packet|{sequence}".encode()).digest()
        seeds.append(int.from_bytes(digest[:4], "big") & 0x7FFF_FFFF)
    if len(set(seeds)) != len(seeds):
        raise RuntimeError("seed collision")
    return seeds


def migrate_ledger(state: dict) -> dict:
    """Schema 1 -> 2: this stage ledger accumulates costs across eval versions (v1 smoke plus
    v2 smoke/panel), so a single eval_version label is false. Replace it with the
    eval_versions list. Every numeric/counter field passes through untouched."""
    if state.get("schema", 1) < 2:
        versions = sorted({state.pop("eval_version", EVAL_VERSION), EVAL_VERSION})
        state["schema"] = 2
        state["eval_versions"] = versions
    versions = state.setdefault("eval_versions", [EVAL_VERSION])
    if EVAL_VERSION not in versions:
        state["eval_versions"] = sorted(versions + [EVAL_VERSION])
    return state


def update_state(update) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    with LOCK.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = json.loads(STATE.read_text()) if STATE.exists() else {
            "schema": 2, "eval_versions": [EVAL_VERSION], "hard_cap_usd": str(STAGE_CAP_USD),
            "provider_reported_spent_usd": "0", "conservative_spent_usd": "0",
            "reserved_usd": "0", "completed_phases": 0,
            "completed_phases_without_provider_cost": 0, "failed_phases_charged_at_bound": 0}
        migrate_ledger(state)
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


def request_retryable(error: Exception, response_text: str | None) -> bool:
    """Local HTTP-status gate in front of the vendored substring matcher: deterministic 4xx
    (e.g. Alibaba's invalid_parameter_error 400) fail after exactly one attempt instead of
    burning three bound-charged retries on the same rejection. Retries stay for 408/429, 5xx,
    and transport failures."""
    if isinstance(error, httpx.HTTPStatusError) and error.response is not None:
        status = error.response.status_code
        if status == 408 or status == 429 or status >= 500:
            return True
        return False
    return is_retryable_error(error, response_text or "")


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
        except asyncio.CancelledError:
            # cancelled mid-flight (loop teardown after a sibling packet failed): the reserved
            # hold must not leak. Settle once, write a durable cancelled record, re-raise.
            settle_request(bound, None)
            append_attempt({"event": "request_attempt_cancelled", "eval_version": EVAL_VERSION,
                            "model": model, "payload_sha256": payload_hash, "attempt": attempt,
                            "reserved_bound_usd": str(bound)})
            raise
        except Exception as error:
            settle_request(bound, None)
            response_text = error.response.text if isinstance(error, httpx.HTTPStatusError) else None
            append_attempt({"event": "request_attempt_failed", "eval_version": EVAL_VERSION,
                            "model": model, "payload_sha256": payload_hash, "attempt": attempt,
                            "reserved_bound_usd": str(bound), "error_type": type(error).__name__,
                            "error": str(error),
                            "response_text": response_text,
                            "status_code": error.response.status_code if response_text else None})
            if attempt == MAX_ATTEMPTS or not request_retryable(error, response_text):
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
    rpath.parent.mkdir(parents=True, exist_ok=True)  # panel writes per-model subdirs
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
        row, refusal_kind, rescueable = parse_packet(battery, text)
        if row is None and rescueable:
            # rescue ONLY clearly syntactic malformed output (unparseable JSON), once. An observed
            # refusal (empty/no JSON/nonconforming) is never rescued into an answer.
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
            row, refusal_kind, rescueable = parse_packet(battery, text)
    except Exception as exc:
        append_record(rpath, {"event": "request_failed", "phase": phase, **request_meta,
                              "error_type": type(exc).__name__, "error": str(exc)})
        raise
    append_record(rpath, {"event": "respondent_parsed", **request_meta, "phase": phase,
                          "row": row, "parsed": row is not None,
                          "refusal_kind": refusal_kind, "rescued": phase == "rescue",
                          "text": text})
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
        "packet_prompt": render_packet(battery), "response_schema": packet_schema(battery),
        "reason_rule": REASON_RULE_V2,
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
        reason_statuses = [o["reason_status"] for o in outcomes]
        reason_counts = {s: reason_statuses.count(s) for s in
                         ("valid", "missing", "too_long", "not_available")}
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
                                     "reason_status_counts": reason_counts,
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
                                     "reason_status_counts": reason_counts,
                                     "coverage": len(substantive) / len(outcomes),
                                     "option_frequencies": {opt: counts[opt] / len(outcomes)
                                                            for opt in counts}}
    zero_or_refused = sum(q.get("zero_selection_or_refusal", q["refused"]) for q in per_question.values())
    kinds = {}
    for event in events:
        if (event["event"] == "respondent_parsed" and event.get("parsed") is True
                and event.get("protocol_id") == pid and event.get("refusal_kind")):
            kinds[event["refusal_kind"]] = kinds.get(event["refusal_kind"], 0) + 1
    return {"model": model, "eval_version": EVAL_VERSION, "protocol_id": pid, "records": str(rpath),
            "valid_packets": len(rows),
            "refusal_kinds": kinds,  # observed refusal classification per packet (v2: never schema-offered)
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
               "packet_prompt": render_packet(battery), "response_schema": packet_schema(battery),
               "reason_rule": REASON_RULE_V2,
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
               "refusal_rule": REFUSAL_RULE_V2,
               "not_published": True, "merge_into_primary": False}
    # canonical-rule assertions: neither manifest prompt nor schema may advertise an escape.
    advertised = json.dumps({"battery": payload["battery"], "prompt": payload["packet_prompt"],
                             "schema": payload["response_schema"]}).lower()
    for forbidden in ("refused", "null", "missing"):
        assert forbidden not in advertised, f"manifest advertises {forbidden!r}"
    assert payload["refusal_rule"] == REFUSAL_RULE_V2
    assert payload["reason_rule"] == REASON_RULE_V2
    atomic_json(MANIFEST, payload)
    return payload


def offline_smoke(battery: list[dict], child_rows: list[dict]) -> None:
    # identity: v2 everywhere
    assert EVAL_VERSION == "wvs-respondent-packet-v2"
    # fixture: visible prompt contains no refusal/null/AI-identity language
    prompt = render_packet(battery).lower()
    for banned in ("refus", "cannot", "unable", "prefer not", "no answer", "don't know",
                   "as an ai", "ai ", "null", "decline", "abstain", "skip"):
        assert banned not in prompt, f"v2 prompt mentions {banned!r}"
    # fixture: schema permits ONLY listed substantive values (no escape advertised to the model)
    schema_text = json.dumps(packet_schema(battery))
    assert "refused" not in schema_text and "null" not in schema_text
    schema = packet_schema(battery)["json_schema"]["schema"]
    child_schema = schema["properties"]["child_qualities"]
    assert child_schema["type"] == "object"
    assert child_schema["properties"]["selected"]["type"] == "array"
    assert child_schema["properties"]["selected"]["minItems"] == 0
    assert child_schema["properties"]["selected"]["maxItems"] == 5
    assert child_schema["required"] == ["selected", "reason"]
    for q in battery:
        if q["id"] == "ChildQualities":
            continue
        answer_schema = schema["properties"]["answers"]["properties"][q["id"]]
        enum = answer_schema["properties"]["selected"]["enum"]
        assert enum == q["options"], f"{q['id']} enum must be exactly the listed options"
        assert answer_schema["required"] == ["selected", "reason"]

    def answers_row(child_value, reason="Personal values shape my view"):
        return {"answers": {q["id"]: {"selected": q["options"][0], "reason": reason}
                            for q in battery if q["id"] != "ChildQualities"},
                "child_qualities": {"selected": child_value, "reason": reason}}

    # fixture: fully conforming packet -> all substantive
    row, kind, rescueable = parse_packet(battery, json.dumps(
        answers_row(["Independence", RELIGIOUS_FAITH])))
    assert row is not None and kind is None and not rescueable
    assert row["ChildQualities"] == {"outcome": "substantive",
                                     "selected": ["Independence", RELIGIOUS_FAITH],
                                     "reason": "Personal values shape my view", "reason_status": "valid"}
    # fixture: child [] parses as SUBSTANTIVE none (the stem says "Which, if any")
    row, kind, rescueable = parse_packet(battery, json.dumps(answers_row([])))
    assert row is not None and not rescueable
    assert row["ChildQualities"] == {"outcome": "substantive", "selected": [],
                                     "reason": "Personal values shape my view", "reason_status": "valid"}
    # fixture: empty content is an OBSERVED refusal (never rescued, never neutral)
    row, kind, rescueable = parse_packet(battery, "")
    assert row is not None and kind == "empty_content" and not rescueable
    assert all(v["outcome"] == "refused" and v["selected"] is None for v in row.values())
    # fixture: a plain-text reply with no JSON is an observed refusal (not rescued)
    row, kind, rescueable = parse_packet(battery, "I would rather not answer this survey.")
    assert row is not None and kind == "no_json" and not rescueable
    assert all(v["outcome"] == "refused" for v in row.values())
    # fixture: parsed but nonconforming values are refusals per question, never rescued, and
    # conforming questions in the same packet keep their answers
    mixed = answers_row(["Obedience"])
    mixed["answers"]["Homosexuality"] = {"selected": "Don't know", "reason": "Personal values shape my view"}  # not a listed option in v2
    row, kind, rescueable = parse_packet(battery, json.dumps(mixed))
    assert row is not None and kind == "nonconforming" and not rescueable
    assert row["Homosexuality"]["outcome"] == "refused" and row["Homosexuality"]["selected"] is None
    assert row["Religion"]["outcome"] == "substantive"
    assert row["ChildQualities"]["outcome"] == "substantive"
    # fixture: unparseable JSON is the ONLY rescueable class (clearly syntactic)
    row, kind, rescueable = parse_packet(battery, '{"answers": {"Religion": {"selected": "Very')
    assert row is None and kind is None and rescueable
    # fixture: rescue-format output (what force_msg asks for) parses
    rescue_text = ('{"answers": {' + ", ".join(
        f'"{q["id"]}": {{"selected": "{q["options"][0]}", "reason": "Personal values shape my view"}}'
        for q in battery if q["id"] != "ChildQualities")
        + '}, "child_qualities": {"selected": ["Independence"], "reason": "Personal values shape my view"}}')
    row, kind, rescueable = parse_packet(battery, rescue_text)
    assert row is not None and kind is None and not rescueable
    assert "refused" not in force_msg(battery)
    # fixture: reason text is audit-only. Valid, missing, and too-long reasons retain the selected
    # answer; they cannot change item scoring. A contradictory-looking reason remains visible for
    # human audit without a semantic classifier deciding whether it is inconsistent.
    ordinary = next(q for q in battery if q["id"] == "Religion")
    valid_row, _, _ = parse_packet(battery, json.dumps(answers_row([], "Family practice matters most")))
    too_long_row, too_long_kind, _ = parse_packet(battery, json.dumps(
        answers_row([], "These nine separate words exceed the permitted reason length now")))
    missing_reason = answers_row([])
    del missing_reason["answers"][ordinary["id"]]["reason"]
    missing_row, missing_kind, _ = parse_packet(battery, json.dumps(missing_reason))
    assert too_long_kind == "reason_format_failure" and missing_kind == "reason_format_failure"
    assert valid_row[ordinary["id"]]["selected"] == too_long_row[ordinary["id"]]["selected"]
    assert valid_row[ordinary["id"]]["selected"] == missing_row[ordinary["id"]]["selected"]
    assert too_long_row[ordinary["id"]]["reason_status"] == "too_long"
    assert missing_row[ordinary["id"]]["reason_status"] == "missing"
    inconsistent = answers_row([])
    inconsistent["answers"][ordinary["id"]]["reason"] = "Religion has no role in life"
    inconsistent_row, _, _ = parse_packet(battery, json.dumps(inconsistent))
    assert inconsistent_row[ordinary["id"]]["selected"] == ordinary["options"][0]
    assert inconsistent_row[ordinary["id"]]["reason"] == "Religion has no role in life"
    score_rows = {0: valid_row, 1: too_long_row, 2: missing_row}
    score_lists = packet_item_lists(score_rows, battery, child_rows)
    religion_vectors = score_lists[ordinary["id"]]
    assert np.array_equal(religion_vectors[0], religion_vectors[1])
    assert np.array_equal(religion_vectors[0], religion_vectors[2])
    child_valid, _, _ = parse_packet(battery, json.dumps(answers_row(["Independence"], "Family values matter")))
    child_long, child_long_kind, _ = parse_packet(battery, json.dumps(
        answers_row(["Independence"], "These nine separate words exceed the child reason length now")))
    assert child_long_kind == "reason_format_failure"
    assert child_valid["ChildQualities"]["selected"] == child_long["ChildQualities"]["selected"]
    child_lists = packet_item_lists({0: child_valid, 1: child_long}, battery, child_rows)
    for quality in PANEL_QUALITIES:
        assert np.array_equal(child_lists[quality][0], child_lists[quality][1])
    # fixture: duplicate / oversized child lists are nonconforming (uniqueness enforced in parsing,
    # since Alibaba rejects array schemas with the uniqueness keyword)
    dup_row, dup_kind, rescueable = parse_packet(battery, json.dumps(
        answers_row([RELIGIOUS_FAITH, RELIGIOUS_FAITH])))
    assert dup_row is not None and dup_row["ChildQualities"]["outcome"] == "refused"
    over_row, _, _ = parse_packet(battery, json.dumps(
        answers_row(next(q for q in battery if q["id"] == "ChildQualities")["options"][:6])))
    assert over_row is not None and over_row["ChildQualities"]["outcome"] == "refused"
    assert not rescueable
    # fixture: child refusal vs zero-selection produce DIFFERENT item vectors
    rows_fixture = {0: {"ChildQualities": {"outcome": "refused", "selected": None}},
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
    # fixture: deterministic detection of accidental cross-model index sharing in coords_draws
    shared_lists = {m: {"Homosexuality": [np.array([1.0, 0.0]), np.array([0.0, 1.0])],
                        "Obedience": [np.array([1.0, 0.0]), np.array([0.0, 1.0])]}
                    for m in MODELS}
    fake_resolved = {X_AXIS: [{"suffix": "Homosexuality", "pole_idx": 0, "n": 2}],
                     Y_AXIS: [{"suffix": "Obedience", "pole_idx": 0, "n": 2}]}
    shared_lists[MODELS[1]]["Homosexuality"] = [np.array([0.0, 1.0]), np.array([1.0, 0.0])]
    draws, valid = coords_draws(shared_lists, fake_resolved, B=200, seed=3)
    both_low = np.sum((draws[:, 0, 0] < 0.5) & (draws[:, 1, 0] < 0.5))
    assert both_low > 0, "cross-model index sharing detected (A and B always anti-correlated)"
    assert len(next(q for q in battery if q["id"] == "ChildQualities")["options"]) == 11
    # fixture: --smoke-model target plumbing (the off-target 3.7 repeat must not recur). The
    # requested model reaches the artifact paths, the payload, route validation, and the
    # protocol identity; every release gets a distinct protocol_id and summary path.
    from unittest import mock as mock_smoke
    for m in MODELS:
        rec_path, sum_path = smoke_paths(m)
        assert rec_path.name == "paid_smoke_v2.jsonl"
        assert m.replace("/", "__") in sum_path.name
    assert len({protocol_id(m, battery) for m in MODELS}) == len(MODELS)
    target = MODELS[0]
    captured = {}

    async def capturing(model, payload, timeout=60.0, **kwargs):
        captured.update(payload)
        raise RuntimeError("no HTTP in offline fixture")
    import tempfile as tempfile_smoke
    with tempfile_smoke.TemporaryDirectory() as tmp:
        with mock_smoke.patch.object(sys.modules[__name__], "budgeted_request", capturing):
            try:
                asyncio.run(run_packet(target, battery, Path(tmp) / "r.jsonl", "run",
                                       protocol_id(target, battery), 0,
                                       {"packet": 0, "seed": 1, "prompt": "p"}, None))
            except RuntimeError:
                pass
    assert captured["model"] == target, "payload must carry the requested smoke target"
    assert captured["response_format"]["json_schema"]["name"] == "wvs_respondent_packet"
    endpoint = standard_endpoint(target)
    slug = endpoint["name"].removeprefix(f"{endpoint['provider_name']} | ")
    route = validate_route({"id": "fixture", "model": target, "openrouter_metadata": {
        "requested": target, "endpoints": {"available": [
            {"selected": True, "provider": "Alibaba", "model": slug}]}}}, target)
    assert route["selected_provider"] == "Alibaba"
    assert route["selected_release_slug"] == slug
    # fixture: smoke validation scopes to its own run (the 3.5-plus smoke crash: a stale 3.7-plus
    # completion in the shared file failed the new target's route check). Unscoped validation
    # must fail with the stale event present; the run_id filter paid_smoke applies must yield
    # exactly the new completion's route.
    def fake_completed(run_id, model):
        ep = standard_endpoint(model)
        ep_slug = ep["name"].removeprefix(f"{ep['provider_name']} | ")
        return {"event": "request_completed", "run_id": run_id, "protocol_id": "p",
                "model": model, "phase": "initial",
                "response": {"id": run_id, "model": model, "usage": {"cost": "0.001"},
                             "choices": [{"message": {}}], "openrouter_metadata": {
                                 "requested": model, "endpoints": {"available": [
                                     {"selected": True, "provider": "Alibaba",
                                      "model": ep_slug}]}}},
                "usage": {}}
    stale = fake_completed("smoke_run", MODELS[3])
    new = fake_completed("smoke_newrun", target)
    with mock_smoke.patch.object(sys.modules[__name__], "update_state",
                                  lambda u: {"fixture": True}):
        unscoped_fails = False
        try:
            smoke_summary_dict(target, {"row": True}, [stale, new], Path("x"))
        except RuntimeError:
            unscoped_fails = True
        assert unscoped_fails, "stale other-model completion must fail unscoped validation"
        summary = smoke_summary_dict(target, {"row": True},
                                     [e for e in (stale, new) if e["run_id"] == "smoke_newrun"],
                                     Path("x"))
    assert summary["model"] == target and len(summary["routes"]) == 1
    assert summary["routes"][0]["selected_release_slug"] == slug
    assert paid_calls_authorized() is False
    print("offline smoke passed: v2 identity, clean prompt/schema, refusal-as-observed, "
          "rescue-only-syntactic, child semantics, collapse fixtures")

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
    # dotenv gating: no credential load and no paid runner without BOTH the CLI flag and the
    # opt-in. main() sets the opt-in only from the flag, so the flag-off case must load nothing.
    from unittest import mock
    module = sys.modules[__name__]
    with mock.patch.object(dotenv, "load_dotenv") as dotenv_mock, \
         mock.patch.object(module, "paid_smoke") as smoke_stub, \
         mock.patch.object(module, "run") as run_stub:
        os.environ.pop(PAID_OPTIN_ENV, None)
        with mock.patch.object(sys, "argv", ["wvs_respondent_packet_v1.py", "--paid-smoke"]):
            refused = False
            try:
                main()
            except SystemExit:
                refused = True
            assert refused, "paid smoke ran without --i-authorize-paid-calls"
        assert dotenv_mock.call_count == 0, "dotenv loaded without authorization"
        assert smoke_stub.call_count == 0 and run_stub.call_count == 0
        with mock.patch.object(sys, "argv", ["wvs_respondent_packet_v1.py", "--paid-smoke",
                                                "--i-authorize-paid-calls",
                                                "--smoke-model", MODELS[0]]):
            main()
        assert dotenv_mock.call_count == 1, "authorized paid path must load runtime credentials"
        assert smoke_stub.call_count == 1 and run_stub.call_count == 0
        assert smoke_stub.call_args[0][0] == MODELS[0], "smoke must run the requested target"
        assert os.environ.get(PAID_OPTIN_ENV) == "1"
        os.environ.pop(PAID_OPTIN_ENV, None)
        # omitted --smoke-model fails fast (the off-target 3.7 repeat): no dotenv, no runner.
        with mock.patch.object(sys, "argv", ["wvs_respondent_packet_v1.py", "--paid-smoke",
                                                "--i-authorize-paid-calls"]):
            missing = False
            try:
                main()
            except SystemExit:
                missing = True
            assert missing, "paid smoke without --smoke-model must fail fast"
        assert dotenv_mock.call_count == 1
        assert smoke_stub.call_count == 1 and run_stub.call_count == 0
    # fixture: ledger migration labels both eval versions and preserves every numeric field
    v1_ledger = {"schema": 1, "eval_version": "wvs-respondent-packet-v1",
                 "hard_cap_usd": "5", "provider_reported_spent_usd": "0.00054048",
                 "conservative_spent_usd": "0.00938784", "reserved_usd": "0E-8",
                 "completed_phases": 1, "completed_phases_without_provider_cost": 0,
                 "failed_phases_charged_at_bound": 3}
    migrated = migrate_ledger(dict(v1_ledger))
    assert migrated["schema"] == 2
    assert migrated["eval_versions"] == ["wvs-respondent-packet-v1",
                                          "wvs-respondent-packet-v2"]
    assert "eval_version" not in migrated, "single-version label must be gone after migration"
    for key, value in v1_ledger.items():
        if key in ("schema", "eval_version"):
            continue
        assert migrated[key] == value, f"migration changed numeric field {key}"
    assert migrate_ledger(migrated) == migrated, "migration must be idempotent"
    # fixture: local retry gate (the 1799 triple-charge). The exact Alibaba 400 shape retried
    # under the old matcher, so the fixture first proves sensitivity, then the fixed behavior:
    # 400 -> exactly one attempt; 429 and 500 keep retrying to MAX_ATTEMPTS; every attempt
    # settles exactly once; the real ledger is untouched (all accounting faked).
    alibaba_text = ('{"error": {"message": "Provider returned error", "code": 400, '
                    '"metadata": {"provider_name": "Alibaba"}}}')

    def http_error(status: int, text: str) -> httpx.HTTPStatusError:
        req = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
        return httpx.HTTPStatusError("Client error", request=req,
                                     response=httpx.Response(status, text=text, request=req))
    err400 = http_error(400, alibaba_text)
    assert is_retryable_error(err400, alibaba_text) is True, \
        "fixture insensitive: old matcher must retry this 400"
    assert request_retryable(err400, alibaba_text) is False
    assert request_retryable(http_error(429, "rate limited"), "") is True
    assert request_retryable(http_error(500, "bad gateway"), "") is True
    assert request_retryable(http_error(408, "timeout"), "") is True

    def run_failures(status: int, text: str) -> dict:
        calls = {"attempts": 0, "settles": 0, "records": []}

        async def failing(payload, timeout=60.0, **kwargs):
            calls["attempts"] += 1
            raise http_error(status, text)
        with mock.patch.object(module, "openrouter_request_with_metadata_once", failing), \
             mock.patch.object(module, "reserve_request", lambda model: Decimal("0.001")), \
             mock.patch.object(module, "settle_request",
                               lambda bound, response: calls.__setitem__(
                                   "settles", calls["settles"] + 1)), \
             mock.patch.object(module, "append_attempt",
                               lambda record: calls["records"].append(record)), \
             mock.patch("asyncio.sleep", new_callable=mock.AsyncMock):
            os.environ[PAID_OPTIN_ENV] = "1"
            try:
                asyncio.run(budgeted_request(MODELS[0], {"model": MODELS[0]}))
            except httpx.HTTPStatusError:
                pass
            finally:
                os.environ.pop(PAID_OPTIN_ENV, None)
        return calls
    got400 = run_failures(400, alibaba_text)
    assert got400["attempts"] == 1, f"deterministic 400 must cost one attempt, got {got400}"
    assert got400["settles"] == 1 and len(got400["records"]) == 1
    for status in (429, 500):
        got = run_failures(status, "error")
        assert got["attempts"] == MAX_ATTEMPTS, f"{status} must keep retrying, got {got}"
        assert got["settles"] == MAX_ATTEMPTS, f"{status} must settle every attempt, got {got}"
    # fixture: a cancelled mid-flight phase settles its bound (the 1799 packet-1 hold leak).
    # Uses the real update_state against temp files: hold returns to zero, conservative spend
    # rises by exactly one bound, and a durable cancelled record exists.
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        expected_bound = request_bound(MODELS[0])

        async def cancelled(payload, timeout=60.0, **kwargs):
            raise asyncio.CancelledError()
        with mock.patch.object(module, "STATE", tmpdir / "budget.json"), \
             mock.patch.object(module, "LOCK", tmpdir / "budget.lock"), \
             mock.patch.object(module, "REQUEST_ATTEMPTS", tmpdir / "attempts.jsonl"), \
             mock.patch.object(module, "openrouter_request_with_metadata_once", cancelled):
            os.environ[PAID_OPTIN_ENV] = "1"
            try:
                raised = False
                try:
                    asyncio.run(budgeted_request(MODELS[0], {"model": MODELS[0]}))
                except asyncio.CancelledError:
                    raised = True
                assert raised, "cancellation must propagate after settling"
            finally:
                os.environ.pop(PAID_OPTIN_ENV, None)
            cancelled_state = json.loads((tmpdir / "budget.json").read_text())
            assert Decimal(cancelled_state["reserved_usd"]) == 0, \
                "cancelled phase must release its hold"
            assert Decimal(cancelled_state["conservative_spent_usd"]) == expected_bound
            assert cancelled_state["failed_phases_charged_at_bound"] == 1
            cancelled_events = [json.loads(line) for line in
                                (tmpdir / "attempts.jsonl").read_text().splitlines()]
            assert any(event["event"] == "request_attempt_cancelled"
                       for event in cancelled_events)
    # fixture: append_record creates missing per-model record subdirs (the 1798 panel crash)
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        nested = Path(tmp) / "records" / "qwen__test" / "packets.jsonl"
        append_record(nested, {"event": "run_started", "protocol_id": "test"})
        stored = json.loads(nested.read_text().splitlines()[0])
        assert stored["eval_version"] == EVAL_VERSION and stored["protocol_id"] == "test"
    print("offline regression passed: opt-in guard, mis-patch defense, CLI refusal check, "
          "dotenv paid-path gating, and ledger migration all hold")


def smoke_paths(model: str) -> tuple[Path, Path]:
    """Smoke artifacts: one shared versioned records file (every event carries model and
    protocol_id) plus a per-release summary, so smoke repeats on different releases never
    overwrite each other."""
    slug = model.replace("/", "__")
    return OUT / "paid_smoke_v2.jsonl", OUT / f"paid_smoke_summary_{slug}.json"


def smoke_summary_dict(model: str, row: dict, completed: list[dict], smoke_records: Path) -> dict:
    """Validate one smoke run's completions against its own target and build its summary. Raises
    on any route mismatch instead of attributing another release's output to this model."""
    routes = []
    for e in completed:
        route = validate_route(e["response"], model)
        if route["selected_provider"] != "Alibaba":
            raise RuntimeError(f"unexpected smoke provider: {route}")
        if (e["response"].get("usage") or {}).get("cost") is None:
            raise RuntimeError("smoke response missing usage.cost")
        routes.append(route)
    return {
        "status": "passed", "eval_version": EVAL_VERSION, "model": model,
        "row": row, "routes": routes,
        "usage": [(e.get("usage") or {}) | {"response_id": e["response"].get("id")} for e in completed],
        "reasoning_tokens": [(e["response"]["choices"][0]["message"] or {}).get("reasoning")
                             for e in completed][:1],
        "records": str(smoke_records), "budget": update_state(lambda s: s)}


def paid_smoke(model: str, battery: list[dict]) -> None:
    """One paid packet on the given MODELS release with reasoning disabled, matching the
    panel payload. The model is an explicit argument (CLI --smoke-model, no default)."""
    if model not in MODELS:
        raise ValueError(f"smoke target must be one of {MODELS}, got {model}")
    pid = protocol_id(model, battery)
    req = {"packet": 0, "seed": paired_seeds(N_PACKETS)[0], "prompt": render_packet(battery)}
    if not paid_calls_authorized():
        raise SystemExit("paid smoke requires --i-authorize-paid-calls")
    from wvs_score_all_options_refresh import reserve, settle_external_reservation
    smoke_rid = (f"pilot/resp-packet-smoke/{model.replace('/', '__')}/"
                 f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%S.%fZ')}")
    if not reserve({"id": smoke_rid, "lane": "alibaba", "reserve_usd": "0.05"}):
        raise RuntimeError("global repository cap rejected respondent-packet smoke reservation")
    before = Decimal(update_state(lambda s: s)["conservative_spent_usd"])
    smoke_records, smoke_summary = smoke_paths(model)
    # unique run id: the shared records file holds every smoke, so validation and summary must
    # scope to this run only (a stale other-model completion once failed a new target's check).
    run = f"smoke_{pid[:12]}_{datetime.now(UTC).strftime('%Y%m%dT%H%M%S')}"
    try:
        row = asyncio.run(run_packet(model, battery, smoke_records, run, pid, 0, req, None))
        if row is None:
            raise RuntimeError(f"paid smoke did not parse: {row}")
    finally:
        after = Decimal(update_state(lambda s: s)["conservative_spent_usd"])
        settle_external_reservation(smoke_rid, after - before)
    completed = [e for e in load_events(smoke_records) if e["event"] == "request_completed"
                 and e.get("run_id") == run]
    if not completed:
        raise RuntimeError("paid smoke recorded no completed request for this run")
    atomic_json(smoke_summary, smoke_summary_dict(model, row, completed, smoke_records))
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
    parser.add_argument("--smoke-model", choices=MODELS, default=None,
                        help="required for --paid-smoke: which MODELS release to smoke (no default, "
                             "an omitted target fails fast so a repeat can never hit the wrong model)")
    args = parser.parse_args()
    battery, child_rows = build_battery()
    if args.offline_smoke:
        offline_smoke(battery, child_rows)
    if args.offline_regression:
        offline_regression(battery)
    if args.write_manifest:
        write_manifest(battery)
    if args.paid_smoke and args.smoke_model is None:
        raise SystemExit("--paid-smoke requires --smoke-model (one of MODELS); no default")
    if args.paid_smoke or args.run:
        if not args.i_authorize_paid_calls:
            raise SystemExit("--paid-smoke/--run cost money and require --i-authorize-paid-calls")
        # Paid CLI path only: load the repo runtime credentials (OPENROUTER_API_KEY) without
        # ever printing them. Import-time and all offline paths stay credential-free.
        dotenv.load_dotenv()
        os.environ[PAID_OPTIN_ENV] = "1"
    if args.paid_smoke:
        paid_smoke(args.smoke_model, battery)
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


def unavailable_items(item_lists: dict[str, list[np.ndarray]], resolved: dict) -> dict[str, list[str]]:
    """Scored items with zero substantive responses, per axis, for one model."""
    out = {}
    for axis in (X_AXIS, Y_AXIS):
        out[axis] = [it["suffix"] for it in resolved[axis]
                     if sum(np.asarray(v).sum() for v in item_lists[it["suffix"]]) == 0]
    return out


def point_coords(item_lists: dict[str, list[np.ndarray]], resolved: dict) -> tuple[np.ndarray | None,
                                                                                   dict[str, list[str]]]:
    """Empirical coordinates from ALL observed rows/samples: the point estimate. Bootstrap draws
    are used only for SE/CI, never as the point. Fixed-battery rule: if ANY required item on an
    axis has zero substantive responses, that AXIS is unavailable (the battery changed, so no
    plausible coordinate may be computed from the remaining items); the model's 2D point requires
    both axes and is None then."""
    missing = unavailable_items(item_lists, resolved)
    xy = []
    for axis in (X_AXIS, Y_AXIS):
        if missing[axis]:  # any zero-coverage required item -> whole axis unavailable
            return None, missing
        vals = []
        for it in resolved[axis]:
            lists = item_lists[it["suffix"]]
            mean_p = np.mean(lists, axis=0)
            vals.append(positiveness(mean_p[None, :], it["pole_idx"], it["n"]))
        xy.append(float(np.mean(vals)))
    return np.array(xy), missing


def coords_draws(item_lists: dict[str, dict[str, list[np.ndarray]]], resolved: dict,
                 B: int = 1000, seed: int = 17, row_linked: bool = True) -> tuple[np.ndarray, dict]:
    """(B, n_models, 2) coordinate draws plus validity counts.

    row_linked=True (packet protocol): resample whole respondent rows; the index draw is shared
    across questions only WITHIN a model (preserving that model's cross-question covariance);
    resampling is independent across models. row_linked=False (dense v1): resample each item's
    vectors independently; dense samples are not row-linked.

    A draw whose model/axis loses all substantive coverage is INVALID for that model: its
    coordinates are NaN and it is excluded from metrics that need all four finite coordinates.
    `valid_draws` reports the per-model count of finite draws."""
    n = len(next(iter(next(iter(item_lists.values())).values())))
    rng = np.random.default_rng(seed)
    draws = np.full((B, len(MODELS), 2), np.nan)
    valid = {m: 0 for m in MODELS}
    for b in range(B):
        for k, m in enumerate(MODELS):
            idx = rng.integers(0, n, n) if row_linked else None
            xy, ok = [], True
            for axis in (X_AXIS, Y_AXIS):
                vals = []
                for it in resolved[axis]:
                    lists = item_lists[m][it["suffix"]]
                    draw_idx = idx if row_linked else rng.integers(0, n, n)
                    mean_p = np.mean([lists[j] for j in draw_idx], axis=0)
                    if mean_p.sum() == 0:
                        ok = False
                        break
                    vals.append(positiveness(mean_p[None, :], it["pole_idx"], it["n"]))
                if not ok:
                    break
                xy.append(float(np.mean(vals)))
            if ok:
                draws[b, k] = xy
                valid[m] += 1
    return draws, valid


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


MIN_COMPLETE_DRAWS = 100


def family_metrics_from_draws(draws: np.ndarray, valid: dict[str, int],
                              bootstrap_B: int) -> dict:
    """Constant-family, linear-trend, and LOO metrics. They require all four finite 2D coordinates,
    so a draw counts only when every model's coordinates are finite; if too few draws qualify (or a
    point coordinate is unavailable), the metric is an explicit unavailable result with the reason
    and valid-draw count, never a fit of the remaining releases."""
    complete = ~np.isnan(draws).any(axis=(1, 2))
    n_complete = int(complete.sum())
    base = {"valid_draws_per_model": dict(valid), "complete_draws": n_complete,
            "complete_draw_fraction": round(n_complete / draws.shape[0], 4),
            "min_complete_draws_required": MIN_COMPLETE_DRAWS}
    if n_complete < MIN_COMPLETE_DRAWS:
        return base | {"status": "unavailable",
                       "reason": ("fewer than 100 bootstrap draws have all four models' coordinates "
                                  "finite (zero-coverage collapse); no family or trend metric is "
                                  "fitted from the remaining releases")}
    cdraws = np.empty(n_complete); ldraws = np.empty(n_complete)
    loo_draws = np.empty((n_complete, 2))
    for b, k in enumerate(np.flatnonzero(complete)):
        cdraws[b], ldraws[b] = constant_and_linear_rmse(draws[k])
        loo = loo_prediction_error(draws[k])
        loo_draws[b] = (loo["constant_loo_mean"], loo["linear_loo_mean"])
    return base | {"status": "ok",
        "constant_family_rmse_draws_mean": float(np.mean(cdraws)),
        "constant_family_rmse_draws_se": float(np.std(cdraws)),
        "linear_trend_rmse_draws_mean": float(np.mean(ldraws)),
        "linear_trend_rmse_draws_se": float(np.std(ldraws)),
        "loo_constant_mean_draws_mean": float(np.mean(loo_draws[:, 0])),
        "loo_constant_mean_draws_se": float(np.std(loo_draws[:, 0])),
        "loo_linear_mean_draws_mean": float(np.mean(loo_draws[:, 1])),
        "loo_linear_mean_draws_se": float(np.std(loo_draws[:, 1])),
        "loo_constant_mean_ci95": [float(v) for v in np.percentile(loo_draws[:, 0], [2.5, 97.5])],
        "loo_linear_mean_ci95": [float(v) for v in np.percentile(loo_draws[:, 1], [2.5, 97.5])],
        "bootstrap_B": bootstrap_B,
    }


def family_point_metrics(points: dict[str, np.ndarray | None]) -> dict:
    """Point constant/linear RMSE and LOO, only when all four models have finite 2D coordinates."""
    if any(p is None for p in points.values()):
        missing = [m for m, p in points.items() if p is None]
        return {"status": "unavailable",
                "reason": (f"point coordinates unavailable for {missing} (zero-coverage collapse); "
                           "family and trend metrics are not fitted from the remaining releases")}
    coords = np.array([points[m] for m in MODELS])
    constant, linear = constant_and_linear_rmse(coords)
    return {"status": "ok", "constant_family_rmse": constant, "linear_trend_rmse": linear,
            "loo": loo_prediction_error(coords)}


def protocol_summary(item_lists: dict[str, dict[str, dict[str, list[np.ndarray]]]], resolved: dict,
                     bootstrap_seed: int, row_linked: bool) -> dict:
    """Point estimate from observed rows; bootstrap draws give SE/CI for coordinates, the
    constant/linear RMSEs, the LOO errors, and the response-noise floors. Collapse handling:
    unavailable coordinates and invalid draws are recorded, never silently dropped."""
    summary: dict = {"unavailable_items": {}, "point_status": "ok"}
    points: dict[str, np.ndarray | None] = {}
    for m in MODELS:
        pt, missing = point_coords(item_lists[m], resolved)
        points[m] = pt
        summary["unavailable_items"][m] = missing
        if pt is None:
            summary["point_status"] = "partially_unavailable"
    point_metrics = family_point_metrics(points)
    summary["point_coords_xy_per_model"] = {m: (None if points[m] is None else
                                                [float(v) for v in points[m]])
                                            for m in MODELS}
    summary["family_point"] = point_metrics
    draws, valid = coords_draws(item_lists, resolved, seed=bootstrap_seed, row_linked=row_linked)
    finite = ~np.isnan(draws).any(axis=2)
    summary["coord_se"] = {m: ([float(v) for v in np.nanstd(draws[:, k], axis=0)]
                               if valid[m] else None) for k, m in enumerate(MODELS)}
    summary["coord_ci95"] = {m: (np.nanpercentile(draws[:, k], [2.5, 97.5], axis=0).tolist()
                                 if valid[m] else None) for k, m in enumerate(MODELS)}
    bootstrap_B = draws.shape[0]
    family = family_metrics_from_draws(draws, valid, bootstrap_B)
    summary["family_bootstrap"] = family
    if family.get("status") == "ok" and point_metrics.get("status") == "ok":
        summary["constant_family_rmse"] = point_metrics["constant_family_rmse"]
        summary["constant_family_rmse_se"] = family["constant_family_rmse_draws_se"]
        summary["constant_family_rmse_ci95"] = [float(v) for v in np.percentile(
            [constant_and_linear_rmse(draws[b])[0] for b in range(draws.shape[0])
             if not np.isnan(draws[b]).any()], [2.5, 97.5])]
        summary["linear_trend_rmse"] = point_metrics["linear_trend_rmse"]
        summary["linear_trend_rmse_se"] = family["linear_trend_rmse_draws_se"]
        summary["linear_trend_rmse_ci95"] = [float(v) for v in np.percentile(
            [constant_and_linear_rmse(draws[b])[1] for b in range(draws.shape[0])
             if not np.isnan(draws[b]).any()], [2.5, 97.5])]
        summary["loo"] = point_metrics["loo"]
        summary["loo_constant_mean_se"] = family["loo_constant_mean_draws_se"]
        summary["loo_linear_mean_se"] = family["loo_linear_mean_draws_se"]
        summary["loo_constant_mean_ci95"] = family["loo_constant_mean_ci95"]
        summary["loo_linear_mean_ci95"] = family["loo_linear_mean_ci95"]
    else:
        summary["constant_family_rmse"] = None
        summary["linear_trend_rmse"] = None
        summary["loo"] = None
    # response-noise floors need all four SEs; use finite model SEs only when all exist
    se_values = [summary["coord_se"][m] for m in MODELS]
    if all(sv is not None for sv in se_values):
        rng = np.random.default_rng(bootstrap_seed + 6)
        floor_const, floor_lin = np.empty(2000), np.empty(2000)
        for b in range(2000):
            ys = np.array([rng.normal(0.0, sv) for sv in se_values])
            floor_const[b], floor_lin[b] = constant_and_linear_rmse(ys)
        summary["constant_noise_floor_mean"] = float(np.mean(floor_const))
        summary["linear_noise_floor_mean"] = float(np.mean(floor_lin))
        if point_metrics.get("status") == "ok":
            summary["p_constant_noise_ge_observed"] = float(np.mean(floor_const >= point_metrics["constant_family_rmse"]))
            summary["p_linear_noise_ge_observed"] = float(np.mean(floor_lin >= point_metrics["linear_trend_rmse"]))
    else:
        summary["constant_noise_floor_mean"] = None
        summary["linear_noise_floor_mean"] = None
    return summary


def analyze_from_data(packet_rows: dict[str, dict[int, dict]], battery: list[dict],
                      child_rows: list[dict], resolved: dict) -> dict:
    """The fixed preregistered analysis, run on real or synthetic rows. Collapse-safe: explicit
    unavailable results instead of crashes or fits of the remaining releases."""
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
    packet_summary = protocol_summary(item_lists, resolved, bootstrap_seed=17, row_linked=True)
    dense = dense_qwen_psamples()
    dense_item_lists = {m: {k: list(v) for k, v in dense[m].items()} for m in MODELS}
    dense_summary = protocol_summary(dense_item_lists, resolved, bootstrap_seed=29,
                                     row_linked=False)
    # independent-bootstrap shift distribution: packet and dense protocols are not pairable, so the
    # packet-minus-dense shift CI subtracts independent coordinate draws. Shifts are per-model and
    # need only those two models' coordinates finite.
    packet_draws, packet_valid = coords_draws(item_lists, resolved, seed=17, row_linked=True)
    dense_draws, _ = coords_draws(dense_item_lists, resolved, seed=29, row_linked=False)
    shift_draws = packet_draws - dense_draws
    shifts = {}
    for k, m in enumerate(MODELS):
        pt_packet, pt_dense = packet_summary["point_coords_xy_per_model"][m],             dense_summary["point_coords_xy_per_model"][m]
        if pt_packet is None or pt_dense is None:
            shifts[m] = {"point": None,
                         "status": "unavailable",
                         "reason": "one protocol has no point coordinate for this model"}
        else:
            finite = ~np.isnan(shift_draws[:, k]).any(axis=1)
            shifts[m] = {"point": [float(a - b) for a, b in zip(pt_packet, pt_dense)],
                         "ci95": np.percentile(shift_draws[finite, k], [2.5, 97.5], axis=0).tolist(),
                         "valid_shift_draws": int(finite.sum())}
    return {
        "eval_version": EVAL_VERSION, "n_packets": N_PACKETS,
        "release_years": release_years().tolist(),
        "packet": packet_summary | {
            "refusal": {m: per_model[m]["refusal_rate"] for m in MODELS},
            "coverage": {m: per_model[m]["coverage_per_question"] for m in MODELS},
            "child_diagnostics": {m: {k: per_model[m][k] for k in (
                "child_refusal_rate", "child_zero_selection_substantive_rate",
                "child_zero_selection_or_refusal_rate")} for m in MODELS},
            "collapse_handling": ("zero-substantive items make the containing axis coordinate "
                                  "unavailable for that model; bootstrap draws with a zero-"
                                  "coverage model/axis are invalid; family/trend/LOO metrics "
                                  "require all four finite coordinates and are otherwise an "
                                  "explicit unavailable result"),
        },
        "dense_v1": dense_summary | {
            "bootstrap_note": ("item-wise independent resampling of the 12 rating vectors per "
                               "item; dense samples are not row-linked, so protocols are not "
                               "pairable and differences use independent bootstraps"),
        },
        "coord_shifts_packet_minus_dense": shifts,
        "shift_pairing": "independent draws (protocols not pairable)",
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
                        row[q["id"]] = {"outcome": "refused", "selected": None}
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
    # healthy case: all four models have finite points and family metrics
    assert result["packet"]["family_point"]["status"] == "ok"
    assert result["dense_v1"]["family_point"]["status"] == "ok"
    assert np.isfinite(result["packet"]["constant_family_rmse"])
    assert np.isfinite(result["packet"]["loo"]["constant_loo_mean"])
    assert result["packet"]["refusal"][MODELS[3]] > result["packet"]["refusal"][MODELS[0]]
    print(f"synthetic analysis passed: packet constant={result['packet']['constant_family_rmse']:.4f} "
          f"linear={result['packet']['linear_trend_rmse']:.4f}; "
          f"dense constant={result['dense_v1']['constant_family_rmse']:.4f}; "
          f"packet LOO const={result['packet']['loo']['constant_loo_mean']:.4f} "
          f"lin={result['packet']['loo']['linear_loo_mean']:.4f}")

    # all-refusal release fixture: one model refuses EVERYTHING -> its point and coordinates are
    # unavailable, family/trend/LOO are explicit unavailable results with valid-draw counts, the
    # refusal/coverage diagnostics are retained, and the analysis completes deterministically.
    collapsed = dict(packet_rows)
    collapsed[MODELS[2]] = {k: {q["id"]: ({"outcome": "refused", "selected": None}
                                          if q["id"] == "ChildQualities" else
                                          {"outcome": "refused", "selected": REFUSED})
                                for q in battery} for k in range(N_PACKETS)}
    result = analyze_from_data(collapsed, battery, child_rows, resolved)
    assert result["packet"]["point_coords_xy_per_model"][MODELS[2]] is None
    assert result["packet"]["family_point"]["status"] == "unavailable"
    assert MODELS[2] in result["packet"]["family_point"]["reason"]
    assert result["packet"]["family_bootstrap"]["status"] == "unavailable"
    assert result["packet"]["family_bootstrap"]["complete_draws"] == 0
    assert result["packet"]["constant_family_rmse"] is None
    assert result["packet"]["loo"] is None
    # diagnostics retained despite collapse
    assert result["packet"]["refusal"][MODELS[2]] == 1.0
    assert result["packet"]["child_diagnostics"][MODELS[2]]["child_refusal_rate"] == 1.0
    # healthy models keep their coordinates and per-model valid-draw counts
    assert result["packet"]["point_coords_xy_per_model"][MODELS[0]] is not None
    assert result["packet"]["family_bootstrap"]["valid_draws_per_model"][MODELS[0]] > 0
    print("synthetic all-refusal fixture passed: analysis completes, family/trend/LOO explicitly "
          "unavailable, diagnostics retained")

    # one-missing-item fixture: exactly one zero-coverage item on an otherwise-covered axis makes
    # that AXIS unavailable for the model; the 2D point is None; family metrics are unavailable and
    # must NOT be computed from the remaining releases.
    one_missing = dict(packet_rows)
    broken = {k: dict(v) for k, v in packet_rows[MODELS[1]].items()}
    for k in broken:
        broken[k]["God"] = {"outcome": "refused", "selected": None}
    one_missing[MODELS[1]] = broken
    result = analyze_from_data(one_missing, battery, child_rows, resolved)
    ps = result["packet"]["point_coords_xy_per_model"]
    assert ps[MODELS[1]] is None, "a model with one dead Y item must have no 2D point"
    assert ps[MODELS[0]] is not None
    assert "God" in result["packet"]["unavailable_items"][MODELS[1]][Y_AXIS]
    assert result["packet"]["family_point"]["status"] == "unavailable"
    assert result["packet"]["constant_family_rmse"] is None
    assert result["packet"]["loo"] is None
    assert result["packet"]["refusal"][MODELS[1]] > 0  # diagnostics retained
    print("one-missing-item fixture passed: axis unavailable, 2D point None, family metrics "
          "explicitly unavailable (not fitted from remaining releases)")


if __name__ == "__main__":
    main()
