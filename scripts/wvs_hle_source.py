"""Validate the saved Artificial Analysis HLE mapping used by the WVS page."""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAPPING_PATH = ROOT / "slop/research/wvs/20260917_artificialanalysis/wvs_hle_mapping.json"
WEB_DATA_PATH = ROOT / "docs/wvs/wvs_map_data.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate() -> dict[str, object]:
    mapping = json.loads(MAPPING_PATH.read_text())
    source = mapping["source"]
    source_dir = MAPPING_PATH.parent
    for filename_key, hash_key in (
        ("manifest_html", "manifest_html_sha256"),
        ("encrypted_models", "encrypted_models_sha256"),
        ("decoded_models", "decoded_models_sha256"),
    ):
        path = source_dir / source[filename_key]
        actual = sha256(path)
        if actual != source[hash_key]:
            raise ValueError(f"source hash mismatch: {path}: {actual}")

    rows = json.loads((source_dir / source["decoded_models"]).read_text())
    if len(rows) != source["canonical_configuration_rows"]:
        raise ValueError(f"configuration row count mismatch: {len(rows)}")
    hle_rows = [row for row in rows if row["hle"] is not None]
    if len(hle_rows) != source["non_null_hle_rows"]:
        raise ValueError(f"non-null HLE row count mismatch: {len(hle_rows)}")

    by_release: dict[str, list[dict]] = defaultdict(list)
    by_config = {}
    for row in hle_rows:
        by_release[row["release"]["slug"]].append(row)
        by_config[row["slug"]] = row

    plotted_names = {model["name"] for model in json.loads(WEB_DATA_PATH.read_text())["models"]}
    mapped_names = set()
    for entry in mapping["mappings"]:
        name = entry["plotted_model"]
        if name not in plotted_names:
            raise ValueError(f"mapped model is not plotted: {name}")
        if name in mapped_names:
            raise ValueError(f"mapping repeats plotted model: {name}")
        mapped_names.add(name)
        row = by_config[entry["source_configuration_slug"]]
        if row["release"]["slug"] != entry["source_release_slug"]:
            raise ValueError(f"release mismatch for {name}")
        if row["release"]["name"] != entry["source_release_name"]:
            raise ValueError(f"release name mismatch for {name}")
        if row["name"] != entry["source_name"]:
            raise ValueError(f"source name mismatch for {name}")
        if row.get("effort", {}).get("slug") != entry["source_effort"]:
            raise ValueError(f"source effort mismatch for {name}")
        if row["releaseDate"] != entry["source_release_date"]:
            raise ValueError(f"release date mismatch for {name}")
        if row["hle"] != entry["hle_score"]:
            raise ValueError(f"HLE score mismatch for {name}")
        selected = max(candidate["hle"] for candidate in by_release[entry["source_release_slug"]])
        if entry["hle_score"] != selected:
            raise ValueError(f"HLE ceiling mismatch for {name}")

    omitted_names = {entry["plotted_model"] for entry in mapping["omitted"]}
    if mapped_names | omitted_names != plotted_names:
        raise ValueError("mapped and omitted models do not partition plotted models")
    return {
        "canonical_configuration_rows": len(rows),
        "non_null_hle_rows": len(hle_rows),
        "exact_and_reviewed_alias_mappings": len(mapped_names),
        "omitted_plotted_models": len(omitted_names),
    }


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2, sort_keys=True))
