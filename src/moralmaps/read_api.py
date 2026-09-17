"""Sampling readout for API models that do NOT expose token logprobs (OpenRouter / OpenAI-compatible).

Chat-completions-only API models return no next-token distribution, so read.py's forced-slot logprob
reader cannot touch them. Fallback (the "average of N responses" approach): SAMPLE N chat completions
at temperature and take the empirical answer frequency as the per-(item, frame) categorical `p`.

Why this stays comparable to the logprob reader: temperature-1 sampling is an unbiased estimator of
the model's softmax categorical, so the empirical `p` -> the true next-token `p` as N grows, and
E = sum_k k*p_k (readouts.expected_score) converges to the logprob E for the SAME model. Every
downstream summary (per_item_categorical, reduce_ordinal/nominal, expected_score, entropy) is a pure
function of `p`, so a sampled model drops onto the SAME map as a logprob model. N sets the
resolution: SE on a p~=0.5 cell is ~0.5/sqrt(N) (N=10 -> 0.16, coarse; N=100 -> 0.05).

What this CANNOT produce, by design (do not add it back):
- logit_contrast C and logodds_agree LO: log of an empirical frequency has -inf on any unsampled
  token; smoothing those zeros would fabricate the very fine steer signal C/LO exist to measure.
- full-vocab pmass_allowed: we cannot see mass on unsampled tokens. The sampling ANALOGUE we do
  report is the fraction of draws that PARSED to an allowed token -- the empirical refusal /
  off-format rate. At total collapse (nothing parses) `p` is NaN, matching read.py's
  NaN-at-collapse ("do not compare"), not an eps fallback.

Requires OPENROUTER_API_KEY. temperature MUST be > 0: at temp 0 the N draws collapse to one argmax
and E degenerates to an integer.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
from datetime import UTC, datetime
from math import inf
from pathlib import Path

import numpy as np
from loguru import logger
from openrouter_wrapper.retry import openrouter_request   # stamina backoff on 429/provider/upstream errors

from .instrument import Instrument, InstrItem
from .read import build_user_content

_ANSWER_SUFFIX = ("\n\nAnswer with ONLY one option from [{space}] -- a single token, nothing else: "
                  "no words, no punctuation, no explanation.")


def parse_answer(text: str, answer_space: list[str]) -> str | None:
    """The EARLIEST-appearing answer_space token in `text` (token-boundaried so '3' is not caught
    inside 'x3y', and a longer token wins a tie at the same position). None if no allowed token
    appears -- a refusal or off-format draw, counted against the parse rate, never coerced."""
    best, best_key = None, (inf, 0)
    for a in answer_space:
        m = re.search(rf"(?<![0-9A-Za-z]){re.escape(a)}(?![0-9A-Za-z])", text)
        if m and (m.start(), -len(a)) < best_key:
            best_key = (m.start(), -len(a))
            best = a
    return best


def _sample_texts(model: str, prompt: str, n_samples: int, temperature: float,
                  max_tokens: int) -> list[str]:
    """N completions via the openrouter_wrapper (stamina retry handles transient 429/provider/upstream
    errors), requesting up to 8 per call via `n` and topping up until N."""
    texts: list[str] = []
    while len(texts) < n_samples:
        # cap n at 4/call: a big n * max_tokens response is slow enough to trip httpx read timeouts
        # (which then exhaust the wrapper's retry budget); smaller requests are more reliable.
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}],
                   "temperature": temperature, "n": min(n_samples - len(texts), 4),
                   "max_tokens": max_tokens}
        data = asyncio.run(openrouter_request(payload))
        texts.extend((c["message"].get("content") or "") for c in data["choices"])
    return texts


def read_items_sampled(model: str, instr: Instrument, items: list[InstrItem], *,
                       n_samples: int = 20, temperature: float = 1.0, max_tokens: int = 32,
                       verbose_first: bool = False) -> list[dict]:
    """Per-(item, frame) rows shaped for `instrument.per_item_categorical`: id, frame, lp, p,
    pmass_allowed, dimension, sign, human_label. `p` is the empirical answer frequency over
    `instr.answer_space`; `pmass_allowed` is the parse rate; `lp = log(p)` carries -inf on unsampled
    tokens ON PURPOSE so any C/LO consumer fails loudly instead of reading a fabricated number."""
    assert temperature > 0, "sampling readout needs temperature > 0; temp 0 collapses E to an integer"
    space = instr.answer_space
    A = len(space)
    idx = {a: k for k, a in enumerate(space)}
    out: list[dict] = []
    for it_n, it in enumerate(items):
        user = build_user_content(instr, it)
        prompt = user + _ANSWER_SUFFIX.format(space="/".join(space))
        texts = _sample_texts(model, prompt, n_samples, temperature, max_tokens)
        counts = np.zeros(A)
        for t in texts:
            a = parse_answer(t, space)
            if a is not None:
                counts[idx[a]] += 1
        n_parsed = int(counts.sum())
        pmass = n_parsed / len(texts)
        p = counts / n_parsed if n_parsed else np.full(A, np.nan)   # NaN at collapse, by design
        with np.errstate(divide="ignore"):
            lp = np.log(p)
        out.append({
            "id": it.id, "frame": it.frame, "lp": lp, "p": p, "pmass_allowed": pmass,
            "dimension": it.dimension, "sign": it.sign, "human_label": it.human_label,
            "n_samples": len(texts), "n_parsed": n_parsed,
            "prompt": prompt, "texts": texts,   # raw responses kept so a run's answers are auditable/saveable
        })
        if verbose_first and it_n == 0:
            logger.debug(
                f"\n=== TRACE read_api first item ({instr.name}, {model}, N={len(texts)}) ===\n"
                f"--- prompt ---\n{prompt}\n"
                f"--- first 3 raw replies ---\n{texts[:3]}\n"
                f"--- counts over {space} ---\n{counts.tolist()}  parsed={n_parsed}/{len(texts)}\n"
                f"SHOULD: replies are a bare token in {space}; parse rate near 1.0 -> coherent. "
                f"ELSE the model is refusing / adding prose / the option set is off.\n")
    return out


# --- rated readout (dense, positional-bias-controlled) ------------------------------------------
_RATE_PROMPT = (
    "{question}\n\n"
    "Rate how strongly you personally agree with or endorse EACH of the following answers, on a "
    "scale of 1 (strongly reject) to 5 (strongly endorse):\n{legend}\n\n"
    'Respond with ONLY a JSON object mapping each answer\'s number to its 1-5 rating, e.g. '
    '{{"0": 2, "1": 5}}. Rate every answer, and output nothing but the JSON.')


def _parse_ratings(text: str, n: int) -> dict[int, float] | None:
    """The LAST brace-object in `text` parsed as {presented_label -> 1-5 rating}, or None if it is
    malformed / missing a label / out of range. LAST so a reasoning model that echoes the schema
    earlier doesn't win over its final answer."""
    objs = re.findall(r"\{[^{}]*\}", text)
    if not objs:
        return None
    try:
        raw = json.loads(objs[-1])
    except json.JSONDecodeError:
        return None
    out = {}
    for k in range(n):
        v = raw.get(str(k), raw.get(k))
        if v is None or not (1 <= float(v) <= 5):
            return None
        out[k] = float(v)
    return out


def _rating_schema(n: int) -> dict:
    keys = [str(k) for k in range(n)]
    return {"type": "json_schema", "json_schema": {"name": "ratings", "strict": True, "schema": {
        "type": "object", "properties": {key: {"type": "number", "minimum": 1, "maximum": 5}
                                        for key in keys}, "required": keys, "additionalProperties": False,
    }}}


def _force_msg(n: int) -> str:
    keys = ", ".join(f'"{k}"' for k in range(n))
    example = ", ".join(f'"{k}": 1' for k in range(n))
    return (f"Output ONLY a compact JSON object with every required key [{keys}] and values from 1 to 5, "
            f"for example {{{example}}}. No markdown, no reasoning, nothing else.")


async def _force_answer(model: str, prompt: str, phase1_msg: dict, temperature: float,
                        max_tokens: int, req_timeout: float, reasoning: dict | None,
                        response_format: dict | None, n: int, provider: dict | None) -> dict:
    """Phase-2 rescue (wassname's bounded-thinking pattern, gist 72eed3a1): a reasoning model that
    spent its whole budget thinking and truncated the JSON mid-object gets a follow-up in the SAME
    conversation -- feed its (truncated) reasoning back as the assistant turn, then demand a compact
    one-line answer NOW. The caller keeps its selected reasoning configuration unchanged across both
    phases. A bigger cap than phase 1 lets mandatory-reasoning models finish the compact object. Still
    parsed by the caller; may fail again -> dropped sample."""
    tail = (phase1_msg.get("reasoning") or phase1_msg.get("content") or "")[-1500:] or "(thinking truncated)"
    msgs = [{"role": "user", "content": prompt},
            {"role": "assistant", "content": tail},
            {"role": "user", "content": _force_msg(n)}]
    payload = {"model": model, "messages": msgs, "temperature": temperature, "max_tokens": max(max_tokens, 2048)}
    if reasoning is not None:
        payload["reasoning"] = reasoning
    if response_format is not None:
        payload["response_format"] = response_format
    if provider is not None:
        payload["provider"] = provider
    return await asyncio.wait_for(openrouter_request(payload), timeout=req_timeout)


def _rate_plan(items: list[dict], n_samples: int, per_call: int = 1) -> list[dict]:
    """Flatten (item, presented-order, count) into a list of <=per_call requests. A binary item splits
    its draws between the two orders (positional-bias control); an ordinal item keeps natural order
    (shuffling "Never..Always" is nonsense). per_call=1: OpenRouter providers do NOT reliably honour
    n>1 (they return a single completion), so one request per sample -- fine, they fire concurrently."""
    plan = []
    for i, it in enumerate(items):
        opts, n = it["options"], it["n"]
        groups = [([0, 1], (n_samples + 1) // 2), ([1, 0], n_samples // 2)] if n == 2 \
            else [(list(range(n)), n_samples)]
        sample = 0
        for perm, tot in groups:
            legend = "\n".join(f"{j}) {opts[perm[j]]}" for j in range(n))
            prompt = _RATE_PROMPT.format(question=it["question"], legend=legend)
            while tot > 0:
                k = min(tot, per_call); tot -= k
                plan.append({"i": i, "perm": perm, "prompt": prompt, "cnt": k,
                             "sample": sample, "presented_options": [opts[j] for j in perm]})
                sample += k
    return plan


def rated_protocol_identity(model: str, items: list[dict], *, n_samples: int, temperature: float,
                            max_tokens: int, concurrency: int, req_timeout: float,
                            reasoning: dict | None, structured_output: bool,
                            provider: dict | None = None, eval_version: str | None = None,
                            seed_schedule: list[int] | None = None) -> str:
    """Hash the exact model, rendered prompts, and request settings that define a cacheable panel."""
    plan = _rate_plan(items, n_samples)
    protocol = {
        "schema": 2,
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "concurrency": concurrency,
        "req_timeout": req_timeout,
        "reasoning": reasoning,
        "structured_output": structured_output,
        "provider": provider,
        "rate_prompt": _RATE_PROMPT,
        "rescue_prompt": _force_msg(10),
        "requests": [{key: req[key] for key in ("i", "perm", "prompt", "cnt", "sample", "presented_options")}
                     for req in plan],
    }
    if eval_version is not None:
        protocol["eval_version"] = eval_version
    if seed_schedule is not None:
        protocol["seed_schedule"] = seed_schedule
    encoded = json.dumps(protocol, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def _append_record(path: Path, record: dict) -> None:
    record["recorded_at_utc"] = datetime.now(UTC).isoformat()
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def read_items_rated(model: str, items: list[dict], *, n_samples: int = 12, temperature: float = 1.0,
                     max_tokens: int = 512, concurrency: int = 8, req_timeout: float = 90.0,
                     reasoning: dict | None = None, structured_output: bool = False, records_path: str | Path,
                     verbose_first: bool = False, provider: dict | None = None,
                     probe_first: bool = False, eval_version: str = "wvs-score-all-options-v1",
                     identity_eval_version: str | None = None, seed_schedule: list[int] | None = None) -> list[dict]:
    """Run one score-all-options panel and write an fsynced JSONL event for every paid request phase.

    The record is the source of truth. It preserves dispatches, responses, rescues, provider usage,
    errors, prompt identity, presented option order, and final per-item samples. Returned rows are a
    reduced view for coordinates only. An incomplete item stays incomplete and the caller must not plot it.
    """
    assert temperature > 0, "sampling readout needs temperature > 0"
    plan = _rate_plan(items, n_samples)
    if seed_schedule is not None and len(seed_schedule) != len(plan):
        raise ValueError(f"seed schedule has {len(seed_schedule)} entries, expected {len(plan)}")
    protocol_id = rated_protocol_identity(model, items, n_samples=n_samples, temperature=temperature,
                                          max_tokens=max_tokens, concurrency=concurrency,
                                          req_timeout=req_timeout, reasoning=reasoning,
                                          structured_output=structured_output, provider=provider,
                                          eval_version=identity_eval_version, seed_schedule=seed_schedule)
    run_id = f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{protocol_id[:12]}"
    rpath = Path(records_path)
    rpath.parent.mkdir(parents=True, exist_ok=True)
    settings = {"model": model, "n_samples": n_samples, "temperature": temperature,
                "max_tokens": max_tokens, "concurrency": concurrency, "req_timeout": req_timeout,
                "reasoning": reasoning, "structured_output": structured_output, "provider": provider,
                "probe_first": probe_first, "eval_version": eval_version,
                "identity_eval_version": identity_eval_version, "seed_schedule": seed_schedule}
    _append_record(rpath, {"event": "run_started", "run_id": run_id, "protocol_id": protocol_id,
                           "settings": settings, "items": items, "planned_requests": len(plan)})

    async def run_all() -> list[dict]:
        sem = asyncio.Semaphore(concurrency)

        async def call(seq: int, req: dict) -> dict:
            item = items[req["i"]]
            request_id = f"{run_id}_{seq:03d}"
            seed = seed_schedule[seq] if seed_schedule is not None else None
            request_meta = {"request_id": request_id, "run_id": run_id, "protocol_id": protocol_id,
                            "model": model, "item_id": item["id"], "canonical_options": item["options"],
                            "presented_options": req["presented_options"], "presented_order": req["perm"],
                            "sample": req["sample"], "prompt": req["prompt"], "settings": settings,
                            "eval_version": eval_version, "seed": seed}
            payload = {"model": model, "messages": [{"role": "user", "content": req["prompt"]}],
                       "temperature": temperature, "n": req["cnt"], "max_tokens": max_tokens}
            if seed is not None:
                payload["seed"] = seed
            if reasoning is not None:
                payload["reasoning"] = reasoning
            if provider is not None:
                payload["provider"] = provider
            response_format = _rating_schema(item["n"]) if structured_output else None
            if response_format is not None:
                payload["response_format"] = response_format
            phase = "initial"
            async with sem:
                try:
                    _append_record(rpath, {"event": "request_started", "phase": phase,
                                           **request_meta, "payload": payload})
                    data = await asyncio.wait_for(openrouter_request(payload), timeout=req_timeout)
                    _append_record(rpath, {"event": "request_completed", "phase": phase,
                                           **request_meta, "response": data, "provider": data.get("provider"),
                                           "usage": data.get("usage")})
                    if len(data["choices"]) != req["cnt"]:
                        raise ValueError(f"expected {req['cnt']} choices, got {len(data['choices'])}")
                    message = data["choices"][0]["message"]
                    text = message.get("content") or ""
                    rescued = False
                    if _parse_ratings(text, item["n"]) is None:
                        phase = "rescue"
                        rescue_payload = {"model": model, "temperature": temperature,
                                          "max_tokens": max(max_tokens, 2048), "messages": [
                                              {"role": "user", "content": req["prompt"]},
                                              {"role": "assistant", "content":
                                               (message.get("reasoning") or message.get("content") or "")[-1500:]
                                               or "(thinking truncated)"},
                                              {"role": "user", "content": _force_msg(item["n"])},
                                          ]}
                        if response_format is not None:
                            rescue_payload["response_format"] = response_format
                        if reasoning is not None:
                            rescue_payload["reasoning"] = reasoning
                        if provider is not None:
                            rescue_payload["provider"] = provider
                        _append_record(rpath, {"event": "request_started", "phase": phase,
                                               **request_meta, "payload": rescue_payload,
                                               "initial_response_message": message})
                        rescue = await _force_answer(model, req["prompt"], message, temperature,
                                                     max_tokens, req_timeout, reasoning, response_format, item["n"], provider)
                        _append_record(rpath, {"event": "request_completed", "phase": phase,
                                               **request_meta, "response": rescue, "provider": rescue.get("provider"),
                                               "usage": rescue.get("usage")})
                        if len(rescue["choices"]) != 1:
                            raise ValueError(f"expected one rescue choice, got {len(rescue['choices'])}")
                        text = rescue["choices"][0]["message"].get("content") or ""
                        rescued = True
                    return {"text": text, "rescued": rescued, "error": None}
                except Exception as exc:
                    _append_record(rpath, {"event": "request_failed", "phase": phase,
                                           **request_meta, "error_type": type(exc).__name__, "error": str(exc)})
                    return {"text": None, "rescued": phase == "rescue", "error": f"{type(exc).__name__}: {exc}"}

        if not probe_first:
            return await asyncio.gather(*(call(seq, req) for seq, req in enumerate(plan)))
        first = await call(0, plan[0])
        first_valid = first["error"] is None and _parse_ratings(first["text"], items[plan[0]["i"]]["n"]) is not None
        if not first_valid:
            _append_record(rpath, {"event": "run_aborted", "run_id": run_id,
                                   "protocol_id": protocol_id, "model": model,
                                   "reason": "first request did not produce parse-valid ratings"})
            return [first] + [{"text": None, "rescued": False, "error": None, "skipped": True}
                              for _ in plan[1:]]
        return [first] + await asyncio.gather(*(call(seq, req) for seq, req in enumerate(plan[1:], start=1)))

    results = asyncio.run(run_all())
    agg = {i: {"p_samples": [], "texts": [], "failed": 0, "rescued": 0, "prompt": ""}
           for i in range(len(items))}
    for req, result in zip(plan, results):
        i, n, perm = req["i"], items[req["i"]]["n"], req["perm"]
        agg[i]["prompt"] = req["prompt"]
        agg[i]["rescued"] += int(result["rescued"])
        if result.get("skipped"):
            continue
        if result["error"] is not None:
            agg[i]["failed"] += 1
            continue
        text = result["text"]
        agg[i]["texts"].append(text)
        rated = _parse_ratings(text, n)
        _append_record(rpath, {"event": "answer_parsed", "run_id": run_id, "protocol_id": protocol_id,
                               "model": model, "item_id": items[i]["id"], "sample": req["sample"],
                               "presented_order": perm, "text": text, "parsed": rated is not None})
        if rated is None:
            continue
        r_canon = np.zeros(n)
        for j in range(n):
            r_canon[perm[j]] = rated[j]
        agg[i]["p_samples"].append(r_canon / r_canon.sum())

    out = []
    for i, item in enumerate(items):
        ps = agg[i]["p_samples"]
        p = np.mean(ps, axis=0) if ps else np.full(item["n"], np.nan)
        row = {"id": item["id"], "p": p, "p_samples": [x.tolist() for x in ps],
               "pmass_allowed": len(ps) / n_samples, "n_samples": n_samples,
               "valid_samples": len(ps), "failed_samples": agg[i]["failed"],
               "rescued_samples": agg[i]["rescued"], "prompt": agg[i]["prompt"],
               "texts": agg[i]["texts"], "protocol_id": protocol_id, "run_id": run_id}
        _append_record(rpath, {"event": "item_result", "run_id": run_id, "protocol_id": protocol_id,
                               "model": model, **row, "p": np.asarray(p).tolist()})
        out.append(row)
        if verbose_first and i == 0:
            logger.debug(
                f"\n=== TRACE read_items_rated first item ({model}, N={n_samples}) ===\n"
                f"--- prompt ---\n{row['prompt']}\n"
                f"--- first 2 raw replies ---\n{row['texts'][:2]}\n"
                f"--- mean p over {item['options']} ---\n{np.round(p, 3).tolist()}  valid={len(ps)}/{n_samples}\n"
                f"SHOULD: replies are a bare JSON dict of 1-5 ratings; valid rate near 1.0 -> coherent. "
                f"ELSE the record shows malformed output, rescue, or request failure.\n")
    _append_record(rpath, {"event": "run_finished", "run_id": run_id, "protocol_id": protocol_id,
                           "model": model, "planned_requests": len(plan),
                           "valid_samples": sum(row["valid_samples"] for row in out),
                           "failed_samples": sum(row["failed_samples"] for row in out),
                           "rescued_samples": sum(row["rescued_samples"] for row in out)})
    return out
