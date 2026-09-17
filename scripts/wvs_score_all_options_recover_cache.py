#!/usr/bin/env python3
"""Recover complete score-all-options panels from the durable request ledger."""
from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing
import tempfile
from collections import defaultdict
from pathlib import Path

import numpy as np

from moralmaps.iw_axes import X_AXIS, Y_AXIS, resolve_items
from moralmaps.rated_cache import merge_completed
from wvs_map import load_wvs_all, model_coord_ci

CACHE = Path("slop/research/wvs/20260916_openrouter/wvs_iw_rated.json")
RECORDS = Path("slop/research/wvs/20260916_openrouter/wvs_iw_requests.jsonl")
AUDIT = Path("slop/audits/20260917_wvs_score_all_options_cache_recovery.json")


def read_records() -> list[dict]:
    records = []
    for line_number, line in enumerate(RECORDS.read_text().splitlines(), start=1):
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid JSONL record at {RECORDS}:{line_number}") from error
    return records


def recovered_entries(records: list[dict]) -> dict[str, dict]:
    starts = {record["run_id"]: record for record in records if record.get("event") == "run_started"}
    finished = [record for record in records if record.get("event") == "run_finished"
                and record["planned_requests"] == 144 and record["valid_samples"] == 144
                and record["failed_samples"] == 0]
    item_results: dict[str, dict[str, dict]] = defaultdict(dict)
    for record in records:
        if record.get("event") == "item_result":
            item_results[record["run_id"]][record["id"]] = record
    resolved = resolve_items(load_wvs_all())
    expected_ids = [item["suffix"] for axis in (X_AXIS, Y_AXIS) for item in resolved[axis]]
    entries = {}
    for finish in finished:
        run_id = finish["run_id"]
        start = starts[run_id]
        rows = item_results[run_id]
        if set(rows) != set(expected_ids):
            raise ValueError(f"complete run {run_id} has item results {sorted(rows)}, expected {expected_ids}")
        if any(row["valid_samples"] != 12 for row in rows.values()):
            raise ValueError(f"complete run {run_id} has non-12 item samples")
        psamples = {item_id: np.asarray(rows[item_id]["p_samples"]) for item_id in expected_ids}
        coords = model_coord_ci(psamples, resolved, np.random.default_rng(0))
        model = finish["model"]
        entries[finish["protocol_id"]] = {
            "model": model,
            "display_key": model.split("/")[-1] + " (rated)",
            "coords": list(coords),
            "records_path": str(RECORDS),
            "run_id": run_id,
            "protocol_id": finish["protocol_id"],
            "n_items": len(rows),
            "n_samples": 12,
        }
    return entries


def _writer(path: str, key: str) -> None:
    merge_completed(Path(path), {key: {"model": key}})


def concurrency_smoke() -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "cache.json"
        processes = [multiprocessing.Process(target=_writer, args=(str(path), key)) for key in ("a", "b")]
        for process in processes:
            process.start()
        for process in processes:
            process.join()
            if process.exitcode != 0:
                raise RuntimeError(f"cache writer exited {process.exitcode}")
        assert set(json.loads(path.read_text())["completed"]) == {"a", "b"}


def recovery_nonoverwriting_smoke() -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "cache.json"
        original = {"schema": 2, "completed": {"existing": {"coords": [1, 2, 3, 4]}}}
        path.write_text(json.dumps(original, sort_keys=True))
        recovered = {"existing": {"coords": [9, 9, 9, 9]}, "missing": {"coords": [5, 6, 7, 8]}}
        additions = {key: value for key, value in recovered.items() if key not in original["completed"]}
        merged = merge_completed(path, additions)
        assert merged["completed"]["existing"] == original["completed"]["existing"]
        assert merged["completed"]["missing"] == recovered["missing"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    if args.smoke:
        concurrency_smoke()
        recovery_nonoverwriting_smoke()
        print("smoke: concurrent writers merge, and recovery never overwrites an existing entry")
    records = read_records()
    existing = json.loads(CACHE.read_text())["completed"] if CACHE.exists() else {}
    existing_hash = hashlib.sha256(json.dumps(existing, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    entries = recovered_entries(records)
    additions = {key: value for key, value in entries.items() if key not in existing}
    overlaps = {key: entry for key, entry in entries.items() if key in existing}
    point_coordinates_match = all(existing[key]["coords"][:2] == entry["coords"][:2] for key, entry in overlaps.items())
    merged = merge_completed(CACHE, additions)
    preserved = {key: merged["completed"][key] for key in existing}
    preserved_hash = hashlib.sha256(json.dumps(preserved, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    audit = {
        "ledger": str(RECORDS),
        "ledger_valid_lines": len(records),
        "existing_entries_preserved_count": len(existing),
        "existing_entries_sha256_before": existing_hash,
        "existing_entries_sha256_after": preserved_hash,
        "new_complete_runs_added": len(additions),
        "new_protocol_ids": sorted(additions),
        "new_models": sorted(entry["model"] for entry in additions.values()),
        "overlap_complete_runs": len(overlaps),
        "overlap_point_coordinates_equal": point_coordinates_match,
        "cache_completed_entries_after_merge": len(merged["completed"]),
    }
    AUDIT.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(json.dumps(audit, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
