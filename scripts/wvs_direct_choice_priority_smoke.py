#!/usr/bin/env python3
"""Zero-network smoke checks for prepared direct-choice priority panels."""
from __future__ import annotations

import asyncio
import json
import tempfile
from collections import Counter
from pathlib import Path

import moralmaps.read_direct_choice as reader
from wvs_direct_choice_priority import entries
from wvs_direct_choice_production_pilot import (
    ANSWER_INSTRUCTION,
    PROMPT_INSTRUCTION,
    RESCUE_INSTRUCTION,
    items,
    schedule,
)


def main() -> None:
    prepared = entries()
    assert len(prepared) == 38
    assert all(row["initial_calls"] == 240 and row["structured_output"] for row in prepared)
    assert {str(row["reasoning"]) for row in prepared} == {
        "None", "{'enabled': False}", "{'effort': 'none'}", "{'effort': 'low'}", "{'effort': 'minimal'}",
    }
    assert all(row["protocol_id"] for row in prepared)
    print("smoke: 38 unique 240-call protocols cover omitted, effort-none, unverified disabled, low, and minimal reasoning settings")

    pilot_items = items()
    request_plan = schedule(pilot_items)
    for reasoning, expected in ((None, None), ({"effort": "none"}, {"effort": "none"}), ({"enabled": False}, {"enabled": False})):
        calls = []

        async def fail(payload: dict) -> dict:
            calls.append(payload)
            raise RuntimeError("synthetic compatibility failure")

        original = reader.openrouter_request
        reader.openrouter_request = fail
        try:
            with tempfile.TemporaryDirectory() as directory:
                records = Path(directory) / "records.jsonl"
                cache = Path(directory) / "cache.json"
                try:
                    reader.read_items_direct_choice(
                        "test/model", pilot_items, samples_per_order=10, temperature=1.0,
                        max_tokens=1024, concurrency=1, request_timeout=1, reasoning=reasoning,
                        structured_output=True, records_path=records, cache_path=cache,
                        prompt_instruction=PROMPT_INSTRUCTION, answer_instruction=ANSWER_INSTRUCTION,
                        rescue_instruction=RESCUE_INSTRUCTION, plan_override=request_plan,
                        fail_fast_first_request=True,
                    )
                except RuntimeError as error:
                    assert "first scheduled request failed before remaining 239 requests" in str(error)
                else:
                    raise AssertionError("synthetic first-request failure did not abort")
                events = [json.loads(line) for line in records.read_text().splitlines()]
                assert Counter(event["event"] for event in events) == Counter({
                    "run_started": 1, "request_started": 1, "request_failed": 1, "run_finished": 1,
                })
                assert len(calls) == 1 and calls[0].get("reasoning") == expected
                assert not cache.exists()
        finally:
            reader.openrouter_request = original
    print("smoke: synthetic request failure exits before remaining 239 and writes no cache")

    calls = []

    async def invalid_json(payload: dict) -> dict:
        calls.append(payload)
        return {"choices": [{"message": {"content": "not a JSON answer"}}]}

    original = reader.openrouter_request
    reader.openrouter_request = invalid_json
    try:
        with tempfile.TemporaryDirectory() as directory:
            records = Path(directory) / "records.jsonl"
            cache = Path(directory) / "cache.json"
            try:
                reader.read_items_direct_choice(
                    "test/model", pilot_items, samples_per_order=10, temperature=1.0,
                    max_tokens=1024, concurrency=1, request_timeout=1, reasoning=None,
                    structured_output=True, records_path=records, cache_path=cache,
                    prompt_instruction=PROMPT_INSTRUCTION, answer_instruction=ANSWER_INSTRUCTION,
                    rescue_instruction=RESCUE_INSTRUCTION, plan_override=request_plan,
                    fail_fast_first_request=True,
                )
            except RuntimeError as error:
                assert "first scheduled request failed before remaining 239 requests" in str(error)
            else:
                raise AssertionError("synthetic parse-invalid first response did not abort")
            events = [json.loads(line) for line in records.read_text().splitlines()]
            assert Counter(event["event"] for event in events) == Counter({
                "run_started": 1, "request_started": 2, "request_completed": 2,
                "answer_parsed": 1, "run_finished": 1,
            })
            parsed = next(event for event in events if event["event"] == "answer_parsed")
            assert not parsed["parsed"] and len(calls) == 2 and all("reasoning" not in payload for payload in calls) and not cache.exists()
    finally:
        reader.openrouter_request = original
    print("smoke: synthetic parse-invalid initial plus rescue records false parse, omits None reasoning in both payloads, then exits before remaining 239 and writes no cache")
    print("smoke: None omits reasoning; effort-none follows catalog support; enabled=false stays explicitly unverified")


if __name__ == "__main__":
    main()
