#!/usr/bin/env python3
"""Replicate seven complete DeepSeek WVS v1 panels without touching canonical cache or Pages data."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import numpy as np

from moralmaps.iw_axes import X_AXIS, Y_AXIS, resolve_items
from moralmaps.read_api import rated_protocol_identity, read_items_rated
from wvs_map import _sample_only_coord_se, load_wvs_all, model_coord_ci
from wvs_score_all_options_refresh import OSS_PROVIDER, release, reserve

EVAL_VERSION = "wvs-score-all-options-v1"
MODELS = (
    "deepseek/deepseek-chat-v3-0324",
    "deepseek/deepseek-chat-v3.1",
    "deepseek/deepseek-v3.2",
    "deepseek/deepseek-v3.2-exp",
    "deepseek/deepseek-v4-flash",
    "deepseek/deepseek-v4-flash-0731",
    "deepseek/deepseek-v4.1-flash",
)
REPLICATES = 3
N_SAMPLES = 24
OUT = Path("slop/research/wvs/20260917_deepseek_reliability")
MANIFEST = OUT / "manifest.json"
RESULTS = OUT / "results.json"
STATE = OUT / "budget.json"
LOCK = OUT / "budget.lock"
CACHE = Path("slop/research/wvs/20260916_openrouter/wvs_iw_rated.json")
LEDGER = Path("slop/research/wvs/20260916_openrouter/wvs_iw_requests.jsonl")
PILOT_RESERVATION_ID = "pilot/deepseek-wvs-v1-reliability"
PILOT_CAP_USD = Decimal("1")


def atomic_json(path: Path, value: object) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temp.replace(path)


def pilot_state(update) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    with LOCK.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = json.loads(STATE.read_text()) if STATE.exists() else {
            "schema": 1, "pilot_cap_usd": str(PILOT_CAP_USD), "spent_usd": "0", "reserved_usd": "0",
        }
        update(state)
        atomic_json(STATE, state)
        fcntl.flock(lock, fcntl.LOCK_UN)
    return state


def deterministic_seeds(model: str, replicate: int, count: int) -> list[int]:
    seeds = []
    for sequence in range(count):
        digest = hashlib.sha256(f"{EVAL_VERSION}|{model}|{replicate}|{sequence}".encode()).digest()
        seeds.append(int.from_bytes(digest[:4], "big") & 0x7FFF_FFFF)
    if len(set(seeds)) != len(seeds):
        raise RuntimeError(f"seed collision for {model} replicate {replicate}")
    return seeds


def completed_v1_settings() -> dict[str, dict]:
    starts = {}
    finished = set()
    for line in LEDGER.read_text().splitlines():
        record = json.loads(line)
        if record.get("model") not in MODELS:
            continue
        if record.get("event") in {"run_started", "request_started"}:
            starts[record["run_id"]] = record
        if record.get("event") == "run_finished" and record["valid_samples"] == 144 and record["failed_samples"] == 0:
            finished.add(record["run_id"])
    settings = {}
    for run_id in sorted(finished):
        start = starts[run_id]
        settings[start["model"]] = start["settings"]
    if set(settings) != set(MODELS):
        raise RuntimeError(f"missing complete v1 DeepSeek settings: {sorted(set(MODELS) - set(settings))}")
    return settings


def rated_items() -> tuple[list[dict], dict]:
    resolved = resolve_items(load_wvs_all())
    items, seen = [], set()
    for axis in (X_AXIS, Y_AXIS):
        for item in resolved[axis]:
            if item["suffix"] in seen:
                continue
            seen.add(item["suffix"])
            items.append({"id": item["suffix"], "question": item["rec"]["q"], "options": item["rec"]["opts"], "n": item["n"]})
    return items, resolved


def catalog_seed_support() -> dict[str, bool]:
    catalog = json.loads(Path("slop/research/wvs/20260917_openrouter_models.json").read_text())["data"]
    by_id = {row["id"]: row for row in catalog}
    return {model: "seed" in by_id[model].get("supported_parameters", []) for model in MODELS}


def protocol_settings(model: str, v1: dict, seeds: list[int]) -> dict:
    return {
        "model": model, "n_samples": N_SAMPLES, "temperature": v1["temperature"],
        "max_tokens": v1["max_tokens"], "concurrency": 1, "req_timeout": v1["req_timeout"],
        "reasoning": v1["reasoning"], "structured_output": v1["structured_output"],
        "provider": v1.get("provider", OSS_PROVIDER), "eval_version": EVAL_VERSION, "seed_schedule": seeds,
    }


def manifest() -> dict:
    items, _ = rated_items()
    settings = completed_v1_settings()
    seed_support = catalog_seed_support()
    rows = []
    for model in MODELS:
        replicates = []
        for replicate in range(REPLICATES):
            seeds = deterministic_seeds(model, replicate, len(items) * N_SAMPLES)
            cfg = protocol_settings(model, settings[model], seeds)
            protocol_id = rated_protocol_identity(model, items, **{key: cfg[key] for key in (
                "n_samples", "temperature", "max_tokens", "concurrency", "req_timeout", "reasoning",
                "structured_output", "provider", "eval_version", "seed_schedule")})
            replicates.append({"replicate": replicate, "protocol_id": protocol_id, "seed_schedule": seeds,
                               "records": str(OUT / "records" / model.replace("/", "__") / f"replicate_{replicate}.jsonl")})
        rows.append({"id": model, "v1_settings": settings[model], "provider_policy": OSS_PROVIDER,
                     "endpoint_advertises_seed": seed_support[model], "replicates": replicates})
    return {
        "schema": 1, "eval_version": EVAL_VERSION, "purpose": "reliability replication, not a new evaluator",
        "models": rows, "items": len(items), "replicates": REPLICATES, "samples_per_item": N_SAMPLES,
        "expected_calls": len(MODELS) * REPLICATES * len(items) * N_SAMPLES,
        "pilot_cap_usd": str(PILOT_CAP_USD), "expected_cost_usd": "0.318363267912",
        "global_cap_reservation_id": PILOT_RESERVATION_ID,
        "hidden_reasoning": "unavailable when a provider does not return it; returned response fields are preserved verbatim",
        "created_utc": datetime.now(UTC).isoformat(),
    }


def replicate_result(records: Path, replicate: dict, items: list[dict], resolved: dict) -> dict | None:
    events = [json.loads(line) for line in records.read_text().splitlines()] if records.exists() else []
    finished = [record for record in events if record["event"] == "run_finished"
                and record["protocol_id"] == replicate["protocol_id"]]
    if not finished:
        return None
    final = finished[-1]
    run_id = final["run_id"]
    item_rows = {record["id"]: record for record in events
                 if record["event"] == "item_result" and record["run_id"] == run_id}
    cost, providers = Decimal(), Counter()
    for record in events:
        if record.get("run_id") == run_id and record["event"] == "request_completed":
            cost += Decimal(str(record.get("usage", {}).get("cost", 0)))
            providers[record.get("provider")] += 1
    result = {
        "replicate": replicate["replicate"], "protocol_id": replicate["protocol_id"],
        "records": str(records), "run_id": run_id, "provider_requests": dict(providers),
        "rescues": final["rescued_samples"], "failures": final["failed_samples"],
        "usage_cost_usd": str(cost), "valid_samples": final["valid_samples"],
    }
    complete = (final["valid_samples"] == len(items) * N_SAMPLES
                and final["failed_samples"] == 0
                and len(item_rows) == len(items)
                and all(row["valid_samples"] == N_SAMPLES for row in item_rows.values()))
    if not complete:
        return result | {"status": "incomplete"}
    psamples = {item["id"]: np.asarray(item_rows[item["id"]]["p_samples"]) for item in items}
    coords = model_coord_ci(psamples, resolved, np.random.default_rng(0))
    response_se = _sample_only_coord_se(psamples, resolved, np.random.default_rng(1), n_draws=N_SAMPLES)
    return result | {"status": "complete", "coords": list(coords), "response_mean_se": list(response_se)}


def pilot_spend() -> Decimal:
    cost = Decimal()
    for records in (OUT / "records").glob("**/*.jsonl"):
        for line in records.read_text().splitlines():
            record = json.loads(line)
            if record["event"] == "request_completed":
                cost += Decimal(str(record.get("usage", {}).get("cost", 0)))
    return cost


def v1_coords(model: str) -> list[float]:
    cache = json.loads(CACHE.read_text())["completed"]
    entries = [entry for entry in cache.values() if entry["model"] == model and entry.get("n_samples") == 12]
    if not entries:
        raise RuntimeError(f"missing canonical v1 cache entry for {model}")
    return entries[-1]["coords"]


def run_replicate(model: str, replicate: dict, v1: dict, items: list[dict], resolved: dict) -> dict:
    records = Path(replicate["records"])
    prior = replicate_result(records, replicate, items, resolved)
    if prior is not None:
        return prior
    records.parent.mkdir(parents=True, exist_ok=True)
    read_items_rated(model, items, n_samples=N_SAMPLES, temperature=v1["temperature"],
                     max_tokens=v1["max_tokens"], concurrency=1, req_timeout=v1["req_timeout"],
                     reasoning=v1["reasoning"], structured_output=v1["structured_output"], provider=v1.get("provider", OSS_PROVIDER),
                     records_path=records, verbose_first=True, probe_first=True, eval_version=EVAL_VERSION,
                     identity_eval_version=EVAL_VERSION, seed_schedule=replicate["seed_schedule"])
    result = replicate_result(records, replicate, items, resolved)
    if result is None:
        raise RuntimeError(f"replicate {model} {replicate['replicate']} did not write run_finished")
    return result


def run() -> None:
    data = json.loads(MANIFEST.read_text())
    items, resolved = rated_items()
    if not reserve({"id": PILOT_RESERVATION_ID, "lane": "deepseek", "reserve_usd": str(PILOT_CAP_USD)}):
        raise RuntimeError("global USD 80 cap would be exceeded by the USD 1 pilot reservation")
    pilot_state(lambda state: state.update({"reserved_usd": str(PILOT_CAP_USD), "started_utc": datetime.now(UTC).isoformat(),
                                             "spent_usd": str(pilot_spend())}))
    results = {"eval_version": EVAL_VERSION, "models": [], "not_published": True}
    try:
        for row in data["models"]:
            reps = []
            for replicate in row["replicates"]:
                if Decimal(pilot_state(lambda state: state)["spent_usd"]) >= PILOT_CAP_USD:
                    raise RuntimeError(f"pilot cap reached before {row['id']}: {pilot_spend()}")
                result = run_replicate(row["id"], replicate, row["v1_settings"], items, resolved)
                pilot_state(lambda state: state.update({"spent_usd": str(pilot_spend())}))
                reps.append(result)
                atomic_json(RESULTS, results | {"models": results["models"] + [{"id": row["id"], "replicates": reps}]})
            model_result = {"id": row["id"], "v1_coords": v1_coords(row["id"]), "replicates": reps}
            if all(rep["status"] == "complete" for rep in reps):
                values = np.asarray([rep["coords"][:2] for rep in reps])
                aggregate_samples = {}
                for rep in reps:
                    records = [json.loads(line) for line in Path(rep["records"]).read_text().splitlines()]
                    for record in records:
                        if record["event"] == "item_result" and record["run_id"] == rep["run_id"]:
                            aggregate_samples.setdefault(record["id"], []).extend(record["p_samples"])
                aggregate = model_coord_ci({key: np.asarray(value) for key, value in aggregate_samples.items()}, resolved, np.random.default_rng(2))
                model_result |= {"status": "complete", "between_replicate_coordinate_sd": np.std(values, axis=0, ddof=1).tolist(),
                                 "aggregate_n72_coords": list(aggregate),
                                 "delta_aggregate_minus_v1": (np.asarray(aggregate[:2]) - np.asarray(model_result["v1_coords"][:2])).tolist()}
            else:
                model_result |= {"status": "incomplete", "aggregate_excluded_reason": "at least one replicate has fewer than 288 valid samples"}
            results["models"].append(model_result)
            atomic_json(RESULTS, results)
    finally:
        release(PILOT_RESERVATION_ID)
        pilot_state(lambda state: state.update({"reserved_usd": "0", "finished_utc": datetime.now(UTC).isoformat()}))


def smoke() -> None:
    data = json.loads(MANIFEST.read_text())
    row, replicate = data["models"][0], data["models"][0]["replicates"][0]
    items, _ = rated_items()
    full_identity = replicate["protocol_id"]
    record = OUT / "smoke.jsonl"
    if record.exists():
        item_results = [json.loads(line) for line in record.read_text().splitlines()
                        if json.loads(line).get("event") == "item_result"]
        smoke_result = item_results[-1]
    else:
        rows = read_items_rated(row["id"], [items[0]], n_samples=1, temperature=row["v1_settings"]["temperature"],
                                max_tokens=row["v1_settings"]["max_tokens"], concurrency=1, req_timeout=row["v1_settings"]["req_timeout"],
                                reasoning=row["v1_settings"]["reasoning"], structured_output=row["v1_settings"]["structured_output"],
                                provider=row["v1_settings"].get("provider", OSS_PROVIDER), records_path=record, probe_first=True,
                                eval_version=EVAL_VERSION, identity_eval_version=EVAL_VERSION,
                                seed_schedule=[replicate["seed_schedule"][0]])
        smoke_result = rows[0]
    if smoke_result["valid_samples"] != 1:
        raise RuntimeError("one-request smoke was not parse-valid")
    atomic_json(OUT / "smoke.json", {"full_panel_protocol_id": full_identity, "smoke_model": row["id"],
                                      "smoke_item": items[0]["id"], "seed": replicate["seed_schedule"][0],
                                      "v1_settings": row["v1_settings"],
                                      "full_replicate_config": protocol_settings(row["id"], row["v1_settings"], replicate["seed_schedule"]),
                                      "endpoint_advertises_seed": row["endpoint_advertises_seed"], "result": smoke_result})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-manifest", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.write_manifest:
        OUT.mkdir(parents=True, exist_ok=True)
        atomic_json(MANIFEST, manifest())
    if args.smoke:
        smoke()
    if args.run:
        run()


if __name__ == "__main__":
    main()
