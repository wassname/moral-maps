"""Durable direct-choice sampling for construct checks, separate from dense ratings."""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path

from openrouter_wrapper.retry import openrouter_request


def _append_record(path: Path, record: dict) -> None:
    record["recorded_at_utc"] = datetime.now(UTC).isoformat()
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def _choice_schema(n: int) -> dict:
    return {"type": "json_schema", "json_schema": {"name": "one_choice", "strict": True, "schema": {
        "type": "object",
        "properties": {"answer": {"type": "integer", "minimum": 0, "maximum": n - 1}},
        "required": ["answer"], "additionalProperties": False,
    }}}


def _parse_choice(text: str, n: int) -> int | None:
    objects = re.findall(r"\{[^{}]*\}", text)
    if not objects:
        return None
    try:
        answer = json.loads(objects[-1])
    except json.JSONDecodeError:
        return None
    if set(answer) != {"answer"}:
        return None
    choice = answer["answer"]
    if type(choice) is not int or not 0 <= choice < n:
        return None
    return choice


def _force_choice(n: int) -> str:
    return f'Return ONLY {{"answer": <integer 0 through {n - 1}>}}. No explanation.'


def _plan(items: list[dict], samples_per_order: int) -> list[dict]:
    plan = []
    for item_index, item in enumerate(items):
        orders = (("canonical", list(range(item["n"]))), ("reversed", list(reversed(range(item["n"])))) )
        for repetition in range(samples_per_order):
            for order_index, (order_name, order) in enumerate(orders):
                plan.append({
                    "item_index": item_index,
                    "item_id": item["id"],
                    "sample": 2 * repetition + order_index,
                    "order_name": order_name,
                    "repetition": repetition,
                    "presented_order": order,
                    "presented_options": [item["options"][index] for index in order],
                    "prompt": _choice_prompt(item, order),
                })
    return plan


def _choice_prompt(item: dict, order: list[int]) -> str:
    options = "\n".join(f"{position}) {item['options'][canonical]}" for position, canonical in enumerate(order))
    return (
        f"{item['question']}\n\n"
        "Think briefly about which ONE answer best reflects your own view. Do not analyze the survey design. "
        "Answer immediately.\n\n"
        f"Choose exactly one answer:\n{options}\n\n"
        f"Respond with ONLY a JSON object such as {{\"answer\": 0}}. The answer must be an integer from 0 through {item['n'] - 1}."
    )


def direct_choice_protocol_identity(model: str, items: list[dict], *, samples_per_order: int,
                                    temperature: float, max_tokens: int, concurrency: int,
                                    request_timeout: float, reasoning: dict, structured_output: bool) -> str:
    plan = _plan(items, samples_per_order)
    protocol = {
        "schema": 1,
        "construct": "direct_choice",
        "model": model,
        "samples_per_order": samples_per_order,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "concurrency": concurrency,
        "request_timeout": request_timeout,
        "reasoning": reasoning,
        "structured_output": structured_output,
        "prompt_instruction": "Think briefly about which ONE answer best reflects your own view. Do not analyze the survey design. Answer immediately.",
        "response_schemas": {item["id"]: _choice_schema(item["n"]) for item in items},
        "rescue_instructions": {item["id"]: _force_choice(item["n"]) for item in items},
        "requests": plan,
    }
    encoded = json.dumps(protocol, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def _save_cache(path: Path, cache: dict) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(cache, indent=2, sort_keys=True) + "\n")
    temp.replace(path)


def read_items_direct_choice(model: str, items: list[dict], *, samples_per_order: int,
                             temperature: float, max_tokens: int, concurrency: int,
                             request_timeout: float, reasoning: dict, structured_output: bool,
                             records_path: str | Path, cache_path: str | Path) -> dict:
    """Sample exactly one selected option per prompt, including canonical and reversed option orders.

    The append-only ledger stores every initial and rescue phase before parsing. A cache entry is written only
    after all planned samples parse, so an incomplete construct pilot cannot look reusable.
    """
    assert samples_per_order > 0
    assert temperature > 0
    assert reasoning == {"effort": "low"}, "the registered Gemini pilot uses catalog-supported low reasoning"
    assert structured_output
    plan = _plan(items, samples_per_order)
    protocol_id = direct_choice_protocol_identity(
        model, items, samples_per_order=samples_per_order, temperature=temperature,
        max_tokens=max_tokens, concurrency=concurrency, request_timeout=request_timeout,
        reasoning=reasoning, structured_output=structured_output,
    )
    cache_file = Path(cache_path)
    cache = json.loads(cache_file.read_text()) if cache_file.exists() else {"schema": 1, "completed": {}}
    assert cache["schema"] == 1
    if protocol_id in cache["completed"]:
        return {"cached": True, **cache["completed"][protocol_id]}

    run_id = f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{protocol_id[:12]}"
    records = Path(records_path)
    records.parent.mkdir(parents=True, exist_ok=True)
    settings = {
        "model": model, "samples_per_order": samples_per_order, "temperature": temperature,
        "max_tokens": max_tokens, "concurrency": concurrency, "request_timeout": request_timeout,
        "reasoning": reasoning, "structured_output": structured_output,
    }
    _append_record(records, {
        "event": "run_started", "run_id": run_id, "protocol_id": protocol_id,
        "construct": "direct_choice", "settings": settings, "items": items,
        "planned_requests": len(plan), "canonical_requests": len(plan) // 2,
        "reversed_requests": len(plan) // 2,
    })

    async def run_all() -> list[dict]:
        semaphore = asyncio.Semaphore(concurrency)

        async def call(sequence: int, request: dict) -> dict:
            item = items[request["item_index"]]
            request_id = f"{run_id}_{sequence:03d}"
            request_meta = {
                "request_id": request_id, "run_id": run_id, "protocol_id": protocol_id,
                "construct": "direct_choice", "model": model, "item_id": item["id"],
                "canonical_options": item["options"], "presented_options": request["presented_options"],
                "presented_order": request["presented_order"], "order_name": request["order_name"],
                "sample": request["sample"], "repetition": request["repetition"],
                "prompt": request["prompt"], "settings": settings,
            }
            response_format = _choice_schema(item["n"])
            payload = {
                "model": model, "messages": [{"role": "user", "content": request["prompt"]}],
                "temperature": temperature, "max_tokens": max_tokens, "reasoning": reasoning,
                "response_format": response_format,
            }
            phase = "initial"
            async with semaphore:
                try:
                    _append_record(records, {"event": "request_started", "phase": phase, **request_meta, "payload": payload})
                    response = await asyncio.wait_for(openrouter_request(payload), timeout=request_timeout)
                    _append_record(records, {"event": "request_completed", "phase": phase, **request_meta,
                                             "response": response, "usage": response.get("usage")})
                    if len(response["choices"]) != 1:
                        raise ValueError(f"expected one choice, got {len(response['choices'])}")
                    message = response["choices"][0]["message"]
                    text = message.get("content") or ""
                    rescued = False
                    if _parse_choice(text, item["n"]) is None:
                        phase = "rescue"
                        assistant_tail = (message.get("reasoning") or message.get("content") or "")[-1500:] or "(thinking truncated)"
                        rescue_payload = {
                            "model": model, "messages": [
                                {"role": "user", "content": request["prompt"]},
                                {"role": "assistant", "content": assistant_tail},
                                {"role": "user", "content": _force_choice(item["n"])},
                            ], "temperature": temperature, "max_tokens": max(max_tokens, 2048),
                            "reasoning": reasoning, "response_format": response_format,
                        }
                        _append_record(records, {"event": "request_started", "phase": phase, **request_meta,
                                                 "payload": rescue_payload, "initial_response_message": message})
                        response = await asyncio.wait_for(openrouter_request(rescue_payload), timeout=request_timeout)
                        _append_record(records, {"event": "request_completed", "phase": phase, **request_meta,
                                                 "response": response, "usage": response.get("usage")})
                        if len(response["choices"]) != 1:
                            raise ValueError(f"expected one rescue choice, got {len(response['choices'])}")
                        text = response["choices"][0]["message"].get("content") or ""
                        rescued = True
                    return {"text": text, "rescued": rescued, "error": None}
                except Exception as exc:
                    _append_record(records, {"event": "request_failed", "phase": phase, **request_meta,
                                             "error_type": type(exc).__name__, "error": str(exc)})
                    return {"text": None, "rescued": phase == "rescue", "error": f"{type(exc).__name__}: {exc}"}

        return await asyncio.gather(*(call(sequence, request) for sequence, request in enumerate(plan)))

    results = asyncio.run(run_all())
    by_item = {item["id"]: [] for item in items}
    failed = 0
    rescues = 0
    for request, result in zip(plan, results):
        rescues += int(result["rescued"])
        if result["error"] is not None:
            failed += 1
            continue
        presented_choice = _parse_choice(result["text"], items[request["item_index"]]["n"])
        _append_record(records, {
            "event": "answer_parsed", "run_id": run_id, "protocol_id": protocol_id,
            "construct": "direct_choice", "model": model, "item_id": request["item_id"],
            "sample": request["sample"], "order_name": request["order_name"],
            "repetition": request["repetition"], "presented_order": request["presented_order"],
            "text": result["text"], "parsed": presented_choice is not None,
            "presented_choice": presented_choice,
            "canonical_choice": request["presented_order"][presented_choice] if presented_choice is not None else None,
        })
        if presented_choice is not None:
            by_item[request["item_id"]].append({
                "sample": request["sample"], "order_name": request["order_name"],
                "repetition": request["repetition"], "presented_order": request["presented_order"],
                "presented_choice": presented_choice, "canonical_choice": request["presented_order"][presented_choice],
            })

    item_results = []
    expected_samples = 2 * samples_per_order
    for item in items:
        samples = by_item[item["id"]]
        canonical = sum(sample["order_name"] == "canonical" for sample in samples)
        reversed_order = sum(sample["order_name"] == "reversed" for sample in samples)
        result = {
            "item_id": item["id"], "n": item["n"], "expected_samples": expected_samples,
            "valid_samples": len(samples), "canonical_valid": canonical, "reversed_valid": reversed_order,
            "samples": samples,
        }
        _append_record(records, {"event": "item_result", "run_id": run_id, "protocol_id": protocol_id,
                                 "construct": "direct_choice", "model": model, **result})
        item_results.append(result)

    complete = failed == 0 and all(result["valid_samples"] == expected_samples for result in item_results)
    summary = {
        "run_id": run_id, "protocol_id": protocol_id, "model": model, "settings": settings,
        "planned_requests": len(plan), "failed_requests": failed, "rescued_requests": rescues,
        "complete": complete, "items": item_results,
    }
    _append_record(records, {"event": "run_finished", "construct": "direct_choice", **summary})
    if complete:
        cache["completed"][protocol_id] = summary
        _save_cache(cache_file, cache)
    return {"cached": False, **summary}
