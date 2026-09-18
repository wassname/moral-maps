#!/usr/bin/env python3
"""wvs-original-choice-pilot-v1: original WVS response format (single choice; one
choose-up-to-five child-quality list) for the same five Gemini Flash releases. -- PI[gpt-5.6-terra]

Reconstructs the instrument from the saved Anthropic/llm_global_opinions WVS rows (see the
preregistration in docs/RESEARCH_JOURNAL.md). Non-substantive outcomes ("Don't know", "No answer",
empty list) are recorded as explicit cannot_answer and reported separately; they are never treated
as neutral or dropped.
"""
from __future__ import annotations

import argparse
import ast
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
from datasets import load_dataset

from moralmaps.iw_axes import X_AXIS, Y_AXIS, SKIP, positiveness, resolve_items
from moralmaps.read_api import openrouter_request_with_metadata_once
from openrouter_wrapper.retry import is_retryable_error
from wvs_gemini_flash_rubric_pilot import (
    ENDPOINT_CATALOG,
    MAX_ATTEMPTS,
    MODEL_CATALOG,
    MINIMUM_REASONING,
    MODELS,
    PROVIDER,
    TRANSPORT_TIMEOUT,
    atomic_json,
    reservation_id,
    standard_endpoint,
    validate_route,
)
from wvs_score_all_options_refresh import reserve, settle_external_reservation

EVAL_VERSION = "wvs-original-choice-pilot-v1"
N_SAMPLES = 24
MAX_TOKENS = 1024
REQUEST_TIMEOUT = 400
STAGE_CAP_USD = Decimal("5")
OUT = Path("slop/research/wvs/20260918_original_choice_pilot")
MANIFEST = OUT / "manifest.json"
RESULTS = OUT / "results.json"
STATE = OUT / "budget.json"
LOCK = OUT / "budget.lock"
REQUEST_ATTEMPTS = OUT / "request_attempts.jsonl"
GLOBAL_RESERVATION = "pilot/original-choice"
SMOKE_RESERVATION = "pilot/original-choice-smoke"
NONSUBSTANTIVE = ("Don't know", "No answer")
POSTHOC_MISSING = "Other missing; Multiple answers Mail (EVS)"
PANEL_QUALITIES = ("Obedience", "Independence", "Determination, perseverance", "Imagination")
CHILD_STEM = ("Here is a list of qualities that children can be encouraged to learn at home. "
              "Which, if any, do you consider to be especially important? Please choose up to five.")
ORDINARY_SUFFIXES = ("Religion", "God", "Abortion", "Homosexuality", "dealing with people?",
                     "Signing a petition", "Attending peaceful demonstrations", "Joining in boycotts")


def ordinary_choice_schema(offered: list[str]) -> dict:
    return {"type": "json_schema", "json_schema": {"name": "wvs_original_choice", "strict": True,
            "schema": {"type": "object", "properties": {"selected": {
                "type": "string", "enum": offered}},
                "required": ["selected"], "additionalProperties": False}}}


def child_choice_schema(qualities: list[str]) -> dict:
    return {"type": "json_schema", "json_schema": {"name": "wvs_child_qualities", "strict": True,
            "schema": {"type": "object", "properties": {"selected": {
                "type": "array", "items": {"type": "string", "enum": qualities},
                "minItems": 0, "maxItems": 5, "uniqueItems": True}},
                "required": ["selected"], "additionalProperties": False}}}


def build_items() -> tuple[list[dict], list[dict]]:
    """9 original questions: 8 ordinary single-choice + 1 child-quality choose-up-to-five list.
    Ordinary: {id, question, offered, substantive, is_list: False}. List: one item with
    {id: 'ChildQualities', qualities, is_list: True}. child_rows are the 10 per-quality source
    rows, used to score child qualities against the human binary marginals."""
    ds = load_dataset("Anthropic/llm_global_opinions", split="train")
    wvs = [r for r in ds if r["source"] == "WVS" and r["question"]]

    items = []
    for suffix in ORDINARY_SUFFIXES:
        hits = [r for r in wvs if r["question"].strip().endswith(suffix)]
        if len(hits) != 1:
            raise RuntimeError(f"expected exactly 1 WVS row ending {suffix!r}, got {len(hits)}")
        rec = hits[0]
        opts = ast.literal_eval(rec["options"]) if isinstance(rec["options"], str) else rec["options"]
        if opts[-1] != POSTHOC_MISSING or tuple(opts[-3:-1]) != NONSUBSTANTIVE:
            raise RuntimeError(f"unexpected non-substantive tail for {suffix!r}: {opts[-3:]}")
        offered = opts[:-1]
        if not set(NONSUBSTANTIVE) <= set(offered):
            raise RuntimeError(f"non-substantive options missing for {suffix!r}: {offered}")
        items.append({"id": suffix, "question": rec["question"], "offered": offered,
                      "substantive": [o for o in offered if o not in NONSUBSTANTIVE],
                      "is_list": False})

    rows = [r for r in wvs if "qualities that children" in r["question"]]
    stems = {r["question"].rsplit("\n", 1)[0].strip() for r in rows}
    if len(rows) != 10 or len(stems) != 1 or stems.pop() != CHILD_STEM:
        raise RuntimeError(f"child-quality stem mismatch: rows={len(rows)} stems={stems}")
    qualities = [r["question"].rsplit("\n", 1)[1].strip() for r in rows]
    if len(set(qualities)) != 10:
        raise RuntimeError(f"child-quality names not distinct: {qualities}")
    if not set(PANEL_QUALITIES) <= set(qualities):
        raise RuntimeError(f"panel qualities missing from source list: {qualities}")
    items.append({"id": "ChildQualities", "question": CHILD_STEM, "qualities": qualities,
                  "is_list": True})
    return items, rows


def presented(items: list[dict], q: int, sample: int) -> list[str]:
    """Cyclic rotation of the offered list by sample index; identical across releases."""
    base = items[q]["qualities"] if items[q]["is_list"] else items[q]["offered"]
    k = len(base)
    return [base[(sample + j) % k] for j in range(k)]


def render_prompt(item: dict, order: list[str]) -> str:
    legend = "\n".join(f"{j + 1}. {o}" for j, o in enumerate(order))
    if item["is_list"]:
        return (f"{item['question']}\n\nQualities:\n{legend}\n\n"
                'Answer as yourself by returning ONLY a JSON object '
                '{"selected": [<up to five quality names copied exactly from the list>]}. '
                "If you do not consider any quality especially important, return an empty list.")
    return (f"{item['question']}\n\nOptions:\n{legend}\n\n"
            'Answer as yourself by returning ONLY a JSON object '
            '{"selected": "<one option copied exactly from the list>"}.')


def paired_seeds(count: int) -> list[int]:
    seeds = []
    for sequence in range(count):
        digest = hashlib.sha256(f"{EVAL_VERSION}|paired|{sequence}".encode()).digest()
        seeds.append(int.from_bytes(digest[:4], "big") & 0x7FFF_FFFF)
    if len(set(seeds)) != len(seeds):
        raise RuntimeError("seed collision")
    return seeds


def parse_answer(item: dict, text: str) -> dict | None:
    """{outcome: 'substantive'|'cannot_answer', ...} or None when invalid."""
    objs = re.findall(r"\{.*\}", text, re.S)
    if not objs:
        return None
    try:
        raw = json.loads(objs[-1])
    except json.JSONDecodeError:
        return None
    if item["is_list"]:
        selected = raw.get("selected")
        if (not isinstance(selected, list) or len(selected) > 5
                or len(set(selected)) != len(selected)
                or not set(selected) <= set(item["qualities"])):
            return None
        if len(selected) == 0:
            return {"outcome": "cannot_answer", "selected": []}
        return {"outcome": "substantive", "selected": selected}
    selected = raw.get("selected")
    if not isinstance(selected, str) or selected not in item["offered"]:
        return None
    if selected in NONSUBSTANTIVE:
        return {"outcome": "cannot_answer", "selected": selected}
    return {"outcome": "substantive", "selected": selected}


def force_msg(item: dict) -> str:
    if item["is_list"]:
        return ('Output ONLY a compact JSON object {"selected": [...]} with up to five quality '
                'names copied exactly from the list, for example {"selected": ["Obedience"]}. '
                "No markdown, no reasoning, nothing else.")
    return ('Output ONLY a compact JSON object {"selected": "<option>"} with one option copied '
            "exactly from the list, for example {\"selected\": \"Don't know\"}. "
            "No markdown, no reasoning, nothing else.")


def answer_schema(item: dict) -> dict:
    return (child_choice_schema(item["qualities"]) if item["is_list"]
            else ordinary_choice_schema(item["offered"]))


def plan_requests(items: list[dict]) -> list[dict]:
    """One request per (question, sample): 9 x N_SAMPLES per model, shared seed schedule."""
    seeds = paired_seeds(N_SAMPLES)
    plan = []
    for q, item in enumerate(items):
        for sample in range(N_SAMPLES):
            order = presented(items, q, sample)
            plan.append({"q": q, "sample": sample, "seed": seeds[sample], "order": order,
                         "prompt": render_prompt(item, order)})
    return plan


def protocol_id(model: str, plan: list[dict]) -> str:
    protocol = {
        "schema": 1, "eval_version": EVAL_VERSION, "model": model,
        "temperature": 1.0, "max_tokens": MAX_TOKENS,
        "reasoning_effort": {m: MINIMUM_REASONING[m] for m in MODELS},
        "provider": PROVIDER, "n_samples": N_SAMPLES, "seeds": paired_seeds(N_SAMPLES),
        "requests": [{"q": r["q"], "sample": r["sample"], "order": r["order"], "prompt": r["prompt"]}
                     for r in plan],
    }
    encoded = json.dumps(protocol, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def update_state(update) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    with LOCK.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = json.loads(STATE.read_text()) if STATE.exists() else {
            "schema": 1, "hard_cap_usd": str(STAGE_CAP_USD),
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
    price = Decimal(endpoint["pricing"]["prompt"]) + Decimal(endpoint["pricing"]["completion"])
    return Decimal(MAX_TOKENS) * price


def reserve_request(model: str) -> Decimal:
    bound = request_bound(model)
    def update(state: dict) -> None:
        spent = Decimal(state["conservative_spent_usd"])
        held = Decimal(state["reserved_usd"])
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
    payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    for attempt in range(1, MAX_ATTEMPTS + 1):
        bound = reserve_request(model)
        try:
            response = await openrouter_request_with_metadata_once(payload, timeout=TRANSPORT_TIMEOUT)
        except Exception as error:
            settle_request(bound, None)
            response_text = error.response.text if isinstance(error, httpx.HTTPStatusError) else None
            append_attempt({"event": "request_attempt_failed", "model": model,
                            "payload_sha256": payload_hash, "attempt": attempt,
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
            append_attempt({"event": "request_attempt_route_invalid", "model": model,
                            "payload_sha256": payload_hash, "attempt": attempt,
                            "reserved_bound_usd": str(bound), "response": response,
                            "error_type": type(error).__name__, "error": str(error)})
            raise
        settle_request(bound, response)
        append_attempt({"event": "request_attempt_completed", "model": model,
                        "payload_sha256": payload_hash, "attempt": attempt,
                        "provider_reported_cost_usd": (response.get("usage") or {}).get("cost"),
                        "response_id": response.get("id"), "route": route})
        return response
    raise AssertionError("unreachable")


def append_record(rpath: Path, record: dict) -> None:
    rpath.parent.mkdir(parents=True, exist_ok=True)
    record["recorded_at_utc"] = datetime.now(UTC).isoformat()
    with rpath.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def load_events(rpath: Path) -> list[dict]:
    return [json.loads(line) for line in rpath.read_text().splitlines()] if rpath.exists() else []


async def run_one(model: str, items: list[dict], rpath: Path, run: str, pid: str,
                  seq: int, req: dict, prior: dict | None) -> dict:
    item = items[req["q"]]
    request_meta = {"request_id": f"{run}_{seq:03d}", "run_id": run, "protocol_id": pid,
                    "model": model, "item_id": item["id"], "sample": req["sample"],
                    "seed": req["seed"], "presented_order": req["order"], "prompt": req["prompt"]}
    if prior is not None:
        append_record(rpath, {"event": "request_reused", **request_meta, "source_run_id": prior["run_id"]})
        return {"parsed": {"outcome": prior["outcome"], "selected": prior["selected"]},
                "rescued": prior.get("rescued", False)}
    payload = {"model": model, "messages": [{"role": "user", "content": req["prompt"]}],
               "temperature": 1.0, "max_tokens": MAX_TOKENS, "seed": req["seed"],
               "reasoning": {"effort": MINIMUM_REASONING[model]}, "provider": PROVIDER,
               "response_format": answer_schema(item)}
    phase = "initial"
    try:
        append_record(rpath, {"event": "request_started", "phase": phase, **request_meta,
                              "payload": payload})
        response = await asyncio.wait_for(budgeted_request(model, payload), timeout=REQUEST_TIMEOUT)
        append_record(rpath, {"event": "request_completed", "phase": phase, **request_meta,
                              "response": response, "usage": response.get("usage")})
        message = response["choices"][0]["message"]
        text = message.get("content") or ""
        parsed = parse_answer(item, text)
        if parsed is None:
            phase = "rescue"
            tail = (message.get("reasoning") or text or "")[-1500:] or "(thinking truncated)"
            rescue_payload = payload | {"max_tokens": max(MAX_TOKENS, 2048), "messages": [
                {"role": "user", "content": req["prompt"]},
                {"role": "assistant", "content": tail},
                {"role": "user", "content": force_msg(item)}]}
            append_record(rpath, {"event": "request_started", "phase": phase, **request_meta,
                                  "payload": rescue_payload, "initial_response_message": message})
            response = await asyncio.wait_for(budgeted_request(model, rescue_payload),
                                              timeout=REQUEST_TIMEOUT)
            append_record(rpath, {"event": "request_completed", "phase": phase, **request_meta,
                                  "response": response, "usage": response.get("usage")})
            text = response["choices"][0]["message"].get("content") or ""
            parsed = parse_answer(item, text)
    except Exception as exc:
        append_record(rpath, {"event": "request_failed", "phase": phase, **request_meta,
                              "error_type": type(exc).__name__, "error": str(exc)})
        raise
    append_record(rpath, {"event": "answer_parsed", **request_meta, "text": text, "phase": phase,
                          "parsed": parsed is not None,
                          "outcome": None if parsed is None else parsed["outcome"],
                          "selected": None if parsed is None else parsed["selected"]})
    return {"parsed": parsed, "rescued": phase == "rescue"}


def prior_answers(rpath: Path, pid: str) -> dict[tuple[str, int], dict]:
    return {(record["item_id"], record["sample"]): record for record in load_events(rpath)
            if record.get("event") == "answer_parsed" and record.get("parsed") is True
            and record.get("protocol_id") == pid}


async def run_model(model: str, items: list[dict], plan: list[dict], pid: str) -> dict:
    rpath = OUT / "records" / model.replace("/", "__") / "original_choice.jsonl"
    prior = prior_answers(rpath, pid)
    if len(prior) == len(plan):
        return summarize_model(model, items, rpath, pid, plan)
    run = f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{pid[:12]}"
    append_record(rpath, {"event": "run_started", "run_id": run, "protocol_id": pid, "model": model,
                          "planned_requests": len(plan),
                          "settings": {"temperature": 1.0, "max_tokens": MAX_TOKENS,
                                       "reasoning": {"effort": MINIMUM_REASONING[model]},
                                       "provider": PROVIDER, "n_samples": N_SAMPLES,
                                       "eval_version": EVAL_VERSION}})
    sem = asyncio.Semaphore(1)

    async def guarded(pair):
        seq, req = pair
        key = (items[req["q"]]["id"], req["sample"])
        async with sem:
            return await run_one(model, items, rpath, run, pid, seq, req, prior.get(key))

    await asyncio.gather(*(guarded(pair) for pair in enumerate(plan)))
    write_run_finished(model, rpath, pid, plan, run)
    return summarize_model(model, items, rpath, pid, plan)


def summarize_model(model: str, items: list[dict], rpath: Path, pid: str, plan: list[dict]) -> dict:
    events = load_events(rpath)
    answers = {(event["item_id"], event["sample"]): event for event in events
               if event["event"] == "answer_parsed" and event.get("parsed") is True
               and event.get("protocol_id") == pid}
    finished = [event for event in events if event["event"] == "run_finished"
                and event.get("protocol_id") == pid]
    if not finished:
        raise RuntimeError(f"no run_finished for {model}")
    per_question = {}
    for q, item in enumerate(items):
        rows = [answers[(item["id"], req["sample"])] for req in plan if req["q"] == q]
        if len(rows) != N_SAMPLES:
            raise RuntimeError(f"incomplete item {item['id']} for {model}")
        substantive = [row for row in rows if row["outcome"] == "substantive"]
        cannot = [row for row in rows if row["outcome"] == "cannot_answer"]
        if item["is_list"]:
            counts = {quality: 0 for quality in item["qualities"]}
            for row in substantive:
                for quality in row["selected"]:
                    counts[quality] += 1
            per_question[item["id"]] = {
                "is_list": True, "n": len(rows), "substantive": len(substantive),
                "cannot_answer": len(cannot), "coverage": len(substantive) / len(rows),
                "important_rates": {quality: counts[quality] / len(rows) for quality in counts}}
        else:
            counts = {option: 0 for option in item["offered"]}
            for row in substantive:
                counts[row["selected"]] += 1
            per_question[item["id"]] = {
                "is_list": False, "n": len(rows), "substantive": len(substantive),
                "cannot_answer": len(cannot), "coverage": len(substantive) / len(rows),
                "option_frequencies": {option: counts[option] / len(rows) for option in counts}}
    final = finished[-1]
    return {"model": model, "protocol_id": pid, "run_id": final["run_id"], "records": str(rpath),
            "valid_samples": final["valid_samples"], "failed_samples": final["failed_samples"],
            "rescued_samples": final["rescued_samples"],
            "cannot_answer_samples": final["cannot_answer_samples"],
            "per_question": per_question}


def write_run_finished(model: str, rpath: Path, pid: str, plan: list[dict], run: str) -> None:
    events = load_events(rpath)
    answers = [event for event in events if event["event"] == "answer_parsed"
               and event.get("protocol_id") == pid]
    substantive = sum(1 for event in answers
                      if event["outcome"] == "substantive")
    cannot = sum(1 for event in answers if event["outcome"] == "cannot_answer")
    rescued = 0
    seen_samples: set[tuple[str, int]] = set()
    for event in answers:
        key = (event["item_id"], event["sample"])
        if key in seen_samples:
            continue
        seen_samples.add(key)
        if event.get("phase") == "rescue":
            rescued += 1
    append_record(rpath, {"event": "run_finished", "run_id": run, "protocol_id": pid, "model": model,
                          "planned_requests": len(plan),
                          "valid_samples": len(seen_samples), "failed_samples": len(plan) - len(seen_samples),
                          "rescued_samples": rescued, "substantive_samples": substantive,
                          "cannot_answer_samples": cannot})


def child_binary_rows(child_rows: list[dict]) -> dict[str, list[str]]:
    """quality -> substantive option names in source order (['Important','Not mentioned'] or swap)."""
    out = {}
    for row in child_rows:
        quality = row["question"].rsplit("\n", 1)[1].strip()
        opts = ast.literal_eval(row["options"]) if isinstance(row["options"], str) else row["options"]
        out[quality] = [o for o in opts if not SKIP.search(o)]
    return out


def sample_psamples(model: str, items: list[dict], rpath: Path, pid: str,
                    plan: list[dict], child_rows: list[dict]) -> dict[str, list[np.ndarray]]:
    """Per item: one p vector over canonical substantive options per sample index. Child quality q
    gets its binary row vector [P(Important), 1-P(...)] consistent with the source rec."""
    events = load_events(rpath)
    answers = {(event["item_id"], event["sample"]): event for event in events
               if event["event"] == "answer_parsed" and event.get("parsed") is True
               and event.get("protocol_id") == pid}
    binaries = child_binary_rows(child_rows)
    out = {}
    for q, item in enumerate(items):
        if item["is_list"]:
            for quality in PANEL_QUALITIES:
                opts = binaries[quality]
                vecs = []
                for req in (r for r in plan if r["q"] == q):
                    row = answers[(item["id"], req["sample"])]
                    mentioned = row["outcome"] == "substantive" and quality in row["selected"]
                    vecs.append(np.array([1.0 if o == "Important" else 0.0 for o in opts])
                                if mentioned else
                                np.array([0.0 if o == "Important" else 1.0 for o in opts]))
                out[quality] = vecs
            continue
        vecs = []
        for req in (r for r in plan if r["q"] == q):
            row = answers[(item["id"], req["sample"])]
            vec = np.zeros(len(item["substantive"]))
            if row["outcome"] == "substantive":
                vec[item["substantive"].index(row["selected"])] = 1.0
            vecs.append(vec)
        out[item["id"]] = vecs
    return out


class NoSubstantive(Exception):
    """A bootstrap draw (or the full sample) left an item with zero substantive answers."""


def model_coords(psample_lists: dict[str, list[np.ndarray]], resolved: dict,
                 idx: np.ndarray) -> tuple[float, float, dict[str, int]]:
    """Conditional coordinates: each item's p is the mean over substantive samples; an item with
    zero coverage is excluded from its axis mean (half-coverage rule), and exclusions are returned
    so the caller can report them. Raises NoSubstantive only if an axis loses more than half its
    items."""
    xy, excluded_total = [], {}
    for axis in (X_AXIS, Y_AXIS):
        vals = []
        excluded = 0
        for it in resolved[axis]:
            ps = np.mean([psample_lists[it["suffix"]][j] for j in idx], axis=0)
            if ps.sum() == 0:
                excluded += 1
                continue
            vals.append(positiveness(ps[None, :], it["pole_idx"], it["n"]))
        if excluded * 2 > len(resolved[axis]):
            raise NoSubstantive(f"axis {axis} lost more than half its items in this draw")
        xy.append(float(np.mean(vals)))
        excluded_total[axis] = excluded
    return xy[0], xy[1], excluded_total


def paired_bootstrap(items: list[dict], child_rows: list[dict], resolved: dict,
                     summaries: dict[str, dict], created: dict[str, int], B: int = 1000) -> dict:
    """Resample the 24 paired sample indices; recompute every model's conditional coordinates,
    the release-date OLS slopes, and 2D residual RMSE. Draws where any item loses all substantive
    answers are skipped and counted."""
    def decimal_year(timestamp: int) -> float:
        d = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        jan = datetime(d.year, 1, 1, tzinfo=timezone.utc)
        nxt = datetime(d.year + 1, 1, 1, tzinfo=timezone.utc)
        return d.year + (d - jan).total_seconds() / (nxt - jan).total_seconds()

    x = np.array([decimal_year(created[m]) for m in MODELS])
    lists = {m: sample_psamples(m, items, Path(summaries[m]["records"]), summaries[m]["protocol_id"],
                                plan_requests(items), child_rows) for m in MODELS}
    full = np.arange(N_SAMPLES)

    def fit(idx: np.ndarray) -> tuple[np.ndarray, np.ndarray, float, dict[str, dict[str, int]]]:
        rows, exclusions = [], {}
        for m in MODELS:
            x0, y0, excluded = model_coords(lists[m], resolved, idx)
            rows.append((x0, y0))
            exclusions[m] = excluded
        ys = np.array(rows)
        slopes, preds = [], []
        for k in range(2):
            slope, intercept = np.polyfit(x, ys[:, k], 1)
            slopes.append(slope)
            preds.append(slope * x + intercept)
        rmse2 = float(np.sqrt(np.mean(np.sum((ys - np.column_stack(preds)) ** 2, axis=1))))
        return ys, np.array(slopes), rmse2, exclusions

    point_ys, point_slopes, point_rmse, point_excluded = fit(full)
    rng = np.random.default_rng(7)
    draws = []
    for _ in range(B):
        idx = rng.integers(0, N_SAMPLES, N_SAMPLES)
        try:
            ys, slopes, rmse, _ = fit(idx)
        except NoSubstantive:
            continue
        draws.append([*ys.ravel(), *slopes, rmse])
    arr = np.array(draws)
    return {
        "point": {"coords_xy_per_model": {m: [float(v) for v in point_ys[k]]
                                          for k, m in enumerate(MODELS)},
                  "slope_x_per_year": float(point_slopes[0]),
                  "slope_y_per_year": float(point_slopes[1]),
                  "rmse_2d": point_rmse,
                  "items_excluded_zero_coverage": point_excluded},
        "bootstrap": {"draws_used": len(draws), "draws_requested": B,
                      "coord_xy_se": np.std(arr[:, :10], axis=0).tolist(),
                      "slope_x_se": float(np.std(arr[:, 10])),
                      "slope_y_se": float(np.std(arr[:, 11])),
                      "rmse_2d_se": float(np.std(arr[:, 12]))},
    }


def write_manifest(items: list[dict]) -> dict:
    plan = plan_requests(items)
    catalog = {r["id"]: r for r in json.loads(ENDPOINT_CATALOG.read_text())["models"]}
    rows, total = [], Decimal(0)
    for model in MODELS:
        endpoint = standard_endpoint(model)
        created = catalog[model]["created"]
        bound = Decimal(len(plan)) * request_bound(model)
        total += bound
        rows.append({"id": model, "created": created,
                     "created_utc": datetime.fromtimestamp(created, tz=timezone.utc).isoformat(),
                     "release_slug": endpoint["name"].removeprefix(f"{endpoint['provider_name']} | "),
                     "minimum_reasoning": MINIMUM_REASONING[model],
                     "advertised_quantization": endpoint.get("quantization"),
                     "requests": len(plan), "reserve_bound_usd": str(bound)})
    payload = {"schema": 1, "eval_version": EVAL_VERSION,
               "created_utc": datetime.now(UTC).isoformat(), "models": rows,
               "questions": [{"id": i["id"], "is_list": i["is_list"], "offered": i.get("offered"),
                              "qualities": i.get("qualities")} for i in items],
               "n_samples": N_SAMPLES, "max_tokens": MAX_TOKENS, "temperature": 1.0,
               "panel_requests": sum(r["requests"] for r in rows),
               "panel_reserve_bound_usd": str(total), "stage_hard_stop_usd": str(STAGE_CAP_USD),
               "cannot_answer_rule": ("ordinary: Don't know / No answer; list: empty selection; "
                                      "reported separately, never neutral"),
               "not_published": True, "merge_into_primary": False}
    atomic_json(MANIFEST, payload)
    return payload


def offline_smoke(items: list[dict]) -> None:
    ordinary = next(i for i in items if not i["is_list"])
    order = presented(items, 0, 1)
    assert parse_answer(ordinary, '{"selected": "Don\'t know"}') == {
        "outcome": "cannot_answer", "selected": "Don't know"}
    assert parse_answer(ordinary, '{"selected": "%s"}' % ordinary["substantive"][0])["outcome"] == "substantive"
    assert parse_answer(ordinary, '{"selected": "Not an option"}') is None
    assert parse_answer(ordinary, "garbage") is None
    list_item = next(i for i in items if i["is_list"])
    assert parse_answer(list_item, '{"selected": []}') == {"outcome": "cannot_answer", "selected": []}
    five = parse_answer(list_item, '{"selected": %s}' % json.dumps(list_item["qualities"][:5]))
    assert five is not None and five["outcome"] == "substantive"
    assert parse_answer(list_item,
                        '{"selected": %s}' % json.dumps(list_item["qualities"][:6])) is None
    assert parse_answer(list_item, '{"selected": ["Obedience", "Obedience"]}') is None
    # rotation covers positions and pairs identically across releases
    plan = plan_requests(items)
    assert len(plan) == 9 * N_SAMPLES
    assert [r["seed"] for r in plan[:N_SAMPLES]] == paired_seeds(N_SAMPLES)
    for q, item in enumerate(items):
        base = item["qualities"] if item["is_list"] else item["offered"]
        k = len(base)
        orders = [tuple(presented(items, q, s)) for s in range(N_SAMPLES)]
        assert len(set(orders)) == min(k, N_SAMPLES)
        for s in range(N_SAMPLES):
            assert orders[s][0] == base[s % k]
    print("offline smoke passed")


def paid_smoke(items: list[dict]) -> None:
    """One paid request: gemini-3.7-flash, Homosexuality (flat-prone), N=1."""
    model = "google/gemini-3.7-flash"
    q = next(q for q, i in enumerate(items) if i["id"] == "Homosexuality")
    item = items[q]
    plan = plan_requests(items)
    pid = protocol_id(model, plan)
    req = plan[q * N_SAMPLES]
    if not reserve({"id": reservation_id(SMOKE_RESERVATION), "lane": "google", "reserve_usd": "0.05"}):
        raise RuntimeError("global repository cap rejected original-choice smoke reservation")
    before = Decimal(update_state(lambda state: state)["conservative_spent_usd"])
    smoke_records = OUT / "paid_smoke.jsonl"
    try:
        outcome = asyncio.run(run_one(model, items, smoke_records, "smoke_run", pid, 0, req, None))
        if outcome["parsed"] is None:
            raise RuntimeError(f"paid smoke did not parse: {outcome}")
        if outcome["parsed"]["outcome"] not in ("substantive", "cannot_answer"):
            raise RuntimeError(f"unexpected smoke outcome: {outcome}")
    finally:
        after = Decimal(update_state(lambda state: state)["conservative_spent_usd"])
        settle_external_reservation(reservation_id(SMOKE_RESERVATION), after - before)
    completed = [event for event in load_events(smoke_records) if event["event"] == "request_completed"]
    routes = []
    for event in completed:
        route = validate_route(event["response"], model)
        if route["selected_provider"] != "Google AI Studio":
            raise RuntimeError(f"unexpected smoke provider: {route}")
        if (event["response"].get("usage") or {}).get("cost") is None:
            raise RuntimeError("smoke response missing usage.cost")
        routes.append(route)
    parsed = outcome["parsed"]
    atomic_json(OUT / "paid_smoke_summary.json", {
        "status": "passed", "model": model, "item": "Homosexuality", "outcome": parsed,
        "routes": routes, "records": str(smoke_records),
        "budget": update_state(lambda state: state)})
    print(f"paid smoke passed: {parsed}")


def run() -> None:
    items, child_rows = build_items()
    resolved = resolve_items(load_wvs_recs())
    # the substantive option sets seen by the pilot must equal the map's canonical recs
    for item in items:
        if item["is_list"]:
            continue
        rec_opts = next(it["rec"]["opts"] for axis in (X_AXIS, Y_AXIS) for it in resolved[axis]
                        if it["suffix"] == item["id"])
        if item["substantive"] != rec_opts:
            raise RuntimeError(f"substantive option mismatch for {item['id']}: "
                               f"{item['substantive']} vs {rec_opts}")
    plan = plan_requests(items)
    pids = {m: protocol_id(m, plan) for m in MODELS}
    global_reservation = reservation_id(GLOBAL_RESERVATION)
    if not reserve({"id": global_reservation, "lane": "google", "reserve_usd": str(STAGE_CAP_USD)}):
        raise RuntimeError("global repository cap rejected original-choice reservation")
    before = Decimal(update_state(lambda state: state)["conservative_spent_usd"])
    results = {"schema": 1, "eval_version": EVAL_VERSION, "models": [], "not_published": True,
               "merge_into_primary": False}
    try:
        for model in MODELS:
            summary = asyncio.run(run_model(model, items, plan, pids[model]))
            results["models"].append(summary)
            atomic_json(RESULTS, results)
    finally:
        after = Decimal(update_state(lambda state: state)["conservative_spent_usd"])
        settle_external_reservation(global_reservation, after - before)
        state = update_state(lambda value: value.update(
            {"finished_utc": datetime.now(UTC).isoformat()}))
        if RESULTS.exists():
            saved = json.loads(RESULTS.read_text())
            atomic_json(RESULTS, saved | {"budget": {
                "provider_reported_spent_usd": state["provider_reported_spent_usd"],
                "conservative_spent_usd": state["conservative_spent_usd"],
                "failed_phases_charged_at_bound": state["failed_phases_charged_at_bound"]}})
    print("panel complete")


def load_wvs_recs() -> list[dict]:
    from wvs_map import load_wvs_all
    return load_wvs_all()


def analyze() -> None:
    """Post-run analysis: coordinates, coverage, refusal rates, paired bootstrap, release trend."""
    items, child_rows = build_items()
    resolved = resolve_items(load_wvs_recs())
    results = json.loads(RESULTS.read_text())
    summaries = {row["model"]: row for row in results["models"]}
    catalog = {r["id"]: r for r in json.loads(MODEL_CATALOG.read_text())["data"]}
    created = {m: catalog[m]["created"] for m in MODELS}
    fits = paired_bootstrap(items, child_rows, resolved, summaries, created)
    cannot = {m: {item_id: stats["cannot_answer"] / stats["n"]
                  for item_id, stats in summaries[m]["per_question"].items()} for m in MODELS}
    coverage = {m: {item_id: stats["coverage"]
                    for item_id, stats in summaries[m]["per_question"].items()} for m in MODELS}
    atomic_json(OUT / "analysis.json", {
        "fits": fits,
        "cannot_answer_rate_per_model": {m: sum(cannot[m].values()) / len(cannot[m]) for m in MODELS},
        "cannot_answer_rate_per_question_per_model": cannot,
        "coverage_per_question_per_model": coverage,
    })
    print(json.dumps(fits["point"], indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline-smoke", action="store_true")
    parser.add_argument("--write-manifest", action="store_true")
    parser.add_argument("--paid-smoke", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--analyze", action="store_true")
    args = parser.parse_args()
    items, child_rows = build_items()
    if args.offline_smoke:
        offline_smoke(items)
    if args.write_manifest:
        write_manifest(items)
    if args.paid_smoke:
        paid_smoke(items)
    if args.run:
        run()
    if args.analyze:
        analyze()


if __name__ == "__main__":
    main()
