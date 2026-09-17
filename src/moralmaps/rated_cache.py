"""Atomic merge persistence for completed score-all-options panels."""
from __future__ import annotations

import fcntl
import json
import os
from pathlib import Path


def merge_completed(path: Path, additions: dict[str, dict]) -> dict:
    """Merge complete entries while holding the cache lock across reread and replacement."""
    lock_path = path.with_suffix(path.suffix + ".lock")
    with lock_path.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        cache = json.loads(path.read_text()) if path.exists() else {"schema": 2, "completed": {}}
        if cache["schema"] != 2:
            raise ValueError(f"unsupported WVS cache schema {cache['schema']}")
        cache["completed"].update(additions)
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(json.dumps(cache, indent=2, sort_keys=True) + "\n")
        with temp.open("r+") as fh:
            fh.flush()
            os.fsync(fh.fileno())
        temp.replace(path)
        fcntl.flock(lock, fcntl.LOCK_UN)
    return cache
