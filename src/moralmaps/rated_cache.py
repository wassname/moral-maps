"""Atomic merge persistence for completed score-all-options panels."""
from __future__ import annotations

import fcntl
import json
import os
from pathlib import Path


def _write_locked(path: Path, update) -> dict:
    lock_path = path.with_suffix(path.suffix + ".lock")
    with lock_path.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        cache = json.loads(path.read_text()) if path.exists() else {"schema": 2, "completed": {}}
        if cache["schema"] != 2:
            raise ValueError(f"unsupported WVS cache schema {cache['schema']}")
        update(cache["completed"])
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(json.dumps(cache, indent=2, sort_keys=True) + "\n")
        with temp.open("r+") as fh:
            fh.flush()
            os.fsync(fh.fileno())
        temp.replace(path)
        fcntl.flock(lock, fcntl.LOCK_UN)
    return cache


def merge_completed(path: Path, additions: dict[str, dict]) -> dict:
    """Merge complete entries while holding the cache lock across reread and replacement."""
    return _write_locked(path, lambda completed: completed.update(additions))


def update_coords(path: Path, coords: dict[str, list[float]]) -> dict:
    """Replace only the derived coordinate summaries for complete protocol records."""
    def update(completed: dict[str, dict]) -> None:
        for protocol_id, values in coords.items():
            completed[protocol_id]["coords"] = values
            completed[protocol_id]["ci_method"] = "combined item and N-response-mean bootstrap"
    return _write_locked(path, update)


def update_eval_versions(path: Path, versions: dict[str, str]) -> dict:
    """Add evaluator provenance without changing cached coordinates or run records."""
    def update(completed: dict[str, dict]) -> None:
        for protocol_id, version in versions.items():
            completed[protocol_id]["eval_version"] = version
    return _write_locked(path, update)
