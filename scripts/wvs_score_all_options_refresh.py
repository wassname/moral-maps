#!/usr/bin/env python3
"""Queue and run canonical WVS score-all-options model refresh lanes."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import subprocess
from contextlib import contextmanager
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

CATALOG = Path("slop/research/wvs/20260917_openrouter_models.json")
CACHE = Path("slop/research/wvs/20260916_openrouter/wvs_iw_rated.json")
RECORDS = Path("slop/research/wvs/20260916_openrouter/wvs_iw_requests.jsonl")
OUT = Path("slop/research/wvs/20260917_score_all_options")
MANIFEST = OUT / "manifest.json"
STATE = OUT / "budget.json"
LOCK = OUT / "budget.lock"
GLOBAL_STOP_USD = Decimal("80")
# Includes the discarded pick-one-option spend. It remains spending under the USD 80 cap.
PRIOR_OBSERVED_USD = Decimal("5.34309727235")
DENSE_BASELINE_USD = Decimal("3.5908606723")
OSS_PROVIDER = {
    "allow_fallbacks": True,
    "require_parameters": True,
    "quantizations": ["fp8", "int8", "bf16", "fp16"],
}
LANES = ("openai", "google", "xai", "muse", "kimi", "glm", "deepseek", "qwen")
SPECIALIZED = ("batch", "free", "-pro", "-fast", "vision", "-vl", "-5v", "-4.6v", "-4.5v", "-code", "-codex", "coder", "audio", "clip", "image", "guard", "safeguard", "multi-agent", "embedding", "rerank")


def lane_for(model_id: str) -> str | None:
    prefixes = {
        "openai/": "openai", "google/": "google", "x-ai/": "xai", "meta/muse-": "muse",
        "moonshotai/": "kimi", "z-ai/": "glm", "deepseek/": "deepseek", "qwen/": "qwen",
    }
    return next((lane for prefix, lane in prefixes.items() if model_id.startswith(prefix)), None)


def catalog() -> dict[str, dict]:
    return {row["id"]: row for row in json.loads(CATALOG.read_text())["data"]}


def completed_models() -> set[str]:
    return {entry["model"] for entry in json.loads(CACHE.read_text())["completed"].values()}


def price(model: dict, field: str) -> Decimal:
    return Decimal(model["pricing"][field]) * 1_000_000


def reasoning(model: dict) -> tuple[dict | None, str]:
    metadata = model.get("reasoning")
    if metadata is None:
        return None, "omitted, not advertised"
    if metadata.get("mandatory"):
        efforts = set(metadata.get("supported_efforts", []))
        if "minimal" in efforts:
            return {"effort": "minimal"}, "minimal"
        if "low" in efforts:
            return {"effort": "low"}, "low"
        raise ValueError("mandatory reasoning lacks minimal/low")
    return {"enabled": False}, "disabled, optional"


def entry(model: dict, completed: set[str]) -> dict:
    model_id = model["id"]
    lane = lane_for(model_id)
    if lane is None:
        return {"id": model_id, "status": "outside requested families"}
    lowered = model_id.lower()
    if any(token in lowered for token in SPECIALIZED):
        return {"id": model_id, "lane": lane, "status": "excluded", "reason": "batch/free/pro/fast or specialized variant"}
    if lane == "google" and "gemma" in lowered:
        return {"id": model_id, "lane": lane, "status": "excluded", "reason": "Gemma is outside the requested Gemini series"}
    if price(model, "completion") > Decimal("15"):
        return {"id": model_id, "lane": lane, "status": "excluded", "reason": "output price exceeds USD 15/M"}
    if model_id in completed:
        return {"id": model_id, "lane": lane, "status": "complete_cached"}
    try:
        setting, setting_label = reasoning(model)
    except ValueError as error:
        return {"id": model_id, "lane": lane, "status": "excluded", "reason": str(error)}
    provider = OSS_PROVIDER if lane in {"muse", "kimi", "glm", "deepseek", "qwen"} or model_id.startswith("openai/gpt-oss-") else None
    reserve = Decimal(144) * (Decimal(1024 + 2048) * price(model, "completion") + Decimal(1024) * price(model, "prompt")) / Decimal(1_000_000)
    return {
        "id": model_id, "lane": lane, "status": "runnable", "created": model["created"],
        "input_usd_per_million": str(price(model, "prompt")),
        "output_usd_per_million": str(price(model, "completion")),
        "reasoning": setting, "reasoning_label": setting_label, "structured_output": "structured_outputs" in model["supported_parameters"],
        "provider": provider, "calls": 144, "reserve_usd": str(reserve),
    }


def prepare() -> list[dict]:
    done = completed_models()
    return [entry(model, done) for model in catalog().values() if lane_for(model["id"]) is not None]


def write_manifest() -> list[dict]:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = prepare()
    payload = {
        "schema": 1,
        "method": "score-all-options",
        "method_definition": "For every WVS item, return a JSON score 1..5 for each answer option, repeat 12 times, then normalize.",
        "catalog_sha256": hashlib.sha256(CATALOG.read_bytes()).hexdigest(),
        "global_stop_usd": str(GLOBAL_STOP_USD),
        "observed_before_refresh_usd": str(PRIOR_OBSERVED_USD),
        "aggregate_concurrency_ceiling": 10,
        "oss_provider_policy": OSS_PROVIDER,
        "models": rows,
    }
    MANIFEST.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return rows


@contextmanager
def budget_state():
    OUT.mkdir(parents=True, exist_ok=True)
    with LOCK.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = json.loads(STATE.read_text()) if STATE.exists() else {"schema": 1, "prior_observed_usd": str(PRIOR_OBSERVED_USD), "reservations": {}}
        yield state
        STATE.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
        fcntl.flock(lock, fcntl.LOCK_UN)


def rated_cost() -> Decimal:
    total = Decimal()
    for line in RECORDS.read_text().splitlines():
        record = json.loads(line)
        if record.get("event") == "request_completed":
            total += Decimal(str(record.get("usage", {}).get("cost", 0)))
    return total


def reserve(row: dict) -> bool:
    with budget_state() as state:
        held = sum(Decimal(value["reserve_usd"]) for value in state["reservations"].values())
        observed = PRIOR_OBSERVED_USD + max(Decimal(), rated_cost() - DENSE_BASELINE_USD)
        required = Decimal(row["reserve_usd"])
        if observed + held + required >= GLOBAL_STOP_USD:
            print(f"stop: observed={observed} held={held} required={required} cap={GLOBAL_STOP_USD}")
            return False
        state["reservations"][row["id"]] = {"lane": row["lane"], "reserve_usd": str(required), "reserved_utc": datetime.now(UTC).isoformat()}
        return True


def release(model_id: str) -> None:
    with budget_state() as state:
        state["reservations"].pop(model_id, None)
        state["rated_ledger_cost_usd"] = str(rated_cost())
        state["reconciled_utc"] = datetime.now(UTC).isoformat()


def command(row: dict) -> list[str]:
    args = [
        "uv", "run", "--offline", "--with", "datasets>=4.0,<5", "python", "scripts/wvs_map.py",
        "--api-models", row["id"], "--api-samples", "12", "--api-concurrency", "1",
        "--api-max-tokens", "1024", "--api-request-timeout", "90", "--api-require-complete",
        "--api-probe-first", "--cache", str(CACHE), "--records", str(RECORDS), "--out", "/tmp/wvs_score_all_options.png",
    ]
    if row["reasoning"] is not None:
        if row["reasoning"] == {"enabled": False}:
            args.append("--api-disable-reasoning")
        else:
            args.extend(["--api-reasoning-effort", row["reasoning"]["effort"]])
    if row["structured_output"]:
        args.append("--api-structured-output")
    if row["provider"] is not None:
        args.extend(["--api-provider-json", json.dumps(row["provider"], sort_keys=True)])
    return args


def run_lane(lane: str) -> None:
    rows = json.loads(MANIFEST.read_text())["models"]
    for row in rows:
        if row.get("lane") != lane or row["status"] != "runnable":
            continue
        if not reserve(row):
            return
        try:
            result = subprocess.run(command(row), check=False)
            if result.returncode:
                print(f"{row['id']}: incomplete score-all-options panel, exit={result.returncode}; evidence retained")
            else:
                print(f"{row['id']}: score-all-options complete or cache replay")
        finally:
            release(row["id"])


def queue(rows: list[dict]) -> None:
    for lane in LANES:
        count = sum(row.get("lane") == lane and row["status"] == "runnable" for row in rows)
        if not count:
            continue
        command = ["pueue", "add", "-w", str(Path.cwd()), "--group", "api", "-l",
                   f"why: fill {count} canonical WVS score-all-options panels in serialized {lane} lane; resolve: retained complete cache or per-model failure evidence under USD 80", "--",
                   "scripts/wvs_api/06_score_all_options_lane.sh", lane]
        print(subprocess.run(command, check=True, capture_output=True, text=True).stdout.strip())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-manifest", action="store_true")
    parser.add_argument("--queue", action="store_true")
    parser.add_argument("--lane", choices=LANES)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    rows = write_manifest() if args.write_manifest else json.loads(MANIFEST.read_text())["models"]
    if args.smoke:
        runnable = [row for row in rows if row["status"] == "runnable"]
        assert all(row["calls"] == 144 for row in runnable)
        assert all(row["provider"] == OSS_PROVIDER for row in runnable if row["lane"] in {"muse", "kimi", "glm", "deepseek", "qwen"} or row["id"].startswith("openai/gpt-oss-"))
        assert all(row["provider"] is None for row in runnable if row["lane"] in {"google", "xai"} or (row["lane"] == "openai" and not row["id"].startswith("openai/gpt-oss-")))
        print(f"smoke: {len(runnable)} score-all-options panels, {len(LANES)} provider lanes, concurrency <= 8")
    if args.queue:
        queue(rows)
    if args.lane:
        run_lane(args.lane)


if __name__ == "__main__":
    main()
