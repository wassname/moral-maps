#!/usr/bin/env python3
"""Audit dense-rated WVS response discrimination without making API requests."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from wvs_map import X_AXIS, Y_AXIS, load_wvs_all, positiveness, resolve_items

CACHE_PATH = Path("slop/research/wvs/20260916_openrouter/wvs_iw_rated.json")
LEDGER_PATH = Path("slop/research/wvs/20260916_openrouter/wvs_iw_requests.jsonl")
ITEM_CSV_PATH = Path("slop/audits/20260917_wvs_content_quality_by_item.csv")
COORD_CSV_PATH = Path("slop/audits/20260917_wvs_content_quality_coordinate_sensitivity.csv")
REPORT_PATH = Path("slop/audits/20260917_wvs_content_quality_cross_panel.md")

CONSTRUCT_MISMATCH = (
    "mutually exclusive", "all the options", "each option", "every answer", "as an ai",
    "my nature as an ai", "i lack personal", "lack personal experience", "do not have personal",
    "don't have personal", "cannot personally", "can't personally", "do not hold beliefs",
    "don't hold beliefs", "non-human perspective",
)
EXPLICIT_INDIFFERENCE = ("no preference",)
NEUTRAL_POLICY = ("neutral", "neutrality", "balanced perspective")


def response_message(event: dict) -> dict:
    return event["response"]["choices"][0]["message"]


def rationale_class(reasoning: str | None) -> str:
    if reasoning is None:
        return "no_saved_rationale"
    normalized = reasoning.lower()
    if any(term in normalized for term in CONSTRUCT_MISMATCH):
        return "explicit_prompt_or_persona_mismatch"
    if any(term in normalized for term in EXPLICIT_INDIFFERENCE):
        return "explicit_indifference"
    if any(term in normalized for term in NEUTRAL_POLICY):
        return "explicit_neutral_policy"
    return "other_saved_rationale"


def compact_quote(reasoning: str | None) -> str:
    return "" if reasoning is None else " ".join(reasoning.split())[:280].rstrip()


def canonical_ratings(answer: dict) -> np.ndarray:
    parsed = json.loads(answer["text"])
    presented = np.array([parsed[str(index)] for index in range(len(parsed))], dtype=float)
    canonical = np.empty_like(presented)
    canonical[np.array(answer["presented_order"], dtype=int)] = presented
    return canonical


def normalized_spread(rating: np.ndarray) -> float:
    return float((rating.max() - rating.min()) / 4)


def total_variation(p: np.ndarray) -> float:
    return float(0.5 * np.abs(p - 1 / len(p)).sum())


def rating_sum(rating: np.ndarray) -> np.ndarray:
    return rating / rating.sum()


def argmax_split(rating: np.ndarray) -> np.ndarray:
    winners = rating == rating.max()
    return winners / winners.sum()


def min_shift(rating: np.ndarray) -> np.ndarray:
    shifted = rating - rating.min()
    assert shifted.sum() > 0, "min-shift requires a nonflat rating"
    return shifted / shifted.sum()


def coordinate(samples: dict[str, list[np.ndarray]], resolved: dict[str, list[dict]]) -> tuple[float, float] | None:
    output = []
    for axis in (X_AXIS, Y_AXIS):
        scores = []
        for item in resolved[axis]:
            ps = samples[item["suffix"]]
            if not ps:
                return None
            scores.append(positiveness(np.mean(ps, axis=0), item["pole_idx"], item["n"]))
        output.append(float(np.mean(scores)))
    return tuple(output)


def coordinate_fields(prefix: str, xy: tuple[float, float] | None) -> dict[str, float | str]:
    if xy is None:
        return {f"{prefix}_x": "", f"{prefix}_y": ""}
    return {f"{prefix}_x": xy[0], f"{prefix}_y": xy[1]}


def distance(current: tuple[float, float], alternative: tuple[float, float] | None) -> float | str:
    if alternative is None:
        return ""
    return float(np.linalg.norm(np.subtract(alternative, current)))


def write_csv(path: Path, rows: list[dict]) -> None:
    assert rows, f"{path} requires rows"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    cache = json.loads(CACHE_PATH.read_text())
    completed = cache["completed"]
    assert completed, "cached completed panels are required"
    runs = {entry["run_id"] for entry in completed.values()}
    entries = {entry["run_id"]: entry for entry in completed.values()}

    parsed: dict[str, list[dict]] = defaultdict(list)
    completed_responses: dict[tuple[str, str, int, str], dict] = {}
    ledger_through = ""
    with LEDGER_PATH.open() as fh:
        for line in fh:
            event = json.loads(line)
            if event.get("run_id") not in runs:
                continue
            ledger_through = max(ledger_through, event["recorded_at_utc"])
            if event["event"] == "answer_parsed":
                assert event["parsed"], f"complete cache run has unparsable answer: {event}"
                parsed[event["run_id"]].append(event)
            if event["event"] == "request_completed":
                completed_responses[(event["run_id"], event["item_id"], event["sample"], event["phase"])] = event

    resolved = resolve_items(load_wvs_all())
    expected_ids = {item["suffix"] for axis in (X_AXIS, Y_AXIS) for item in resolved[axis]}
    item_rows: list[dict] = []
    coord_rows: list[dict] = []
    examples: list[tuple[dict, str]] = []

    for run_id, entry in sorted(entries.items(), key=lambda pair: pair[1]["model"]):
        answers = parsed[run_id]
        assert len(answers) == entry["n_items"] * entry["n_samples"] == 144, f"incomplete cache entry {entry['model']}"
        by_item: dict[str, list[dict]] = defaultdict(list)
        for answer in answers:
            by_item[answer["item_id"]].append(answer)
        assert set(by_item) == expected_ids, f"item identity drift for {entry['model']}"

        current: dict[str, list[np.ndarray]] = {}
        argmax: dict[str, list[np.ndarray]] = {}
        minshift_nonflat: dict[str, list[np.ndarray]] = {}
        flat_missing: dict[str, list[np.ndarray]] = {}
        for item_id, item_answers in sorted(by_item.items()):
            assert len(item_answers) == 12, f"sample count drift for {entry['model']} {item_id}"
            ratings = [canonical_ratings(answer) for answer in item_answers]
            flats = [normalized_spread(rating) == 0 for rating in ratings]
            current[item_id] = [rating_sum(rating) for rating in ratings]
            argmax[item_id] = [argmax_split(rating) for rating in ratings]
            minshift_nonflat[item_id] = [min_shift(rating) for rating, flat in zip(ratings, flats) if not flat]
            flat_missing[item_id] = [rating_sum(rating) for rating, flat in zip(ratings, flats) if not flat]
            ties = [int((rating == rating.max()).sum()) for rating in ratings]
            aggregate = np.mean(current[item_id], axis=0)
            rationale_counts = Counter()
            item_examples: list[str] = []
            for answer, flat in zip(item_answers, flats):
                if not flat:
                    continue
                phase = "rescue" if (run_id, item_id, answer["sample"], "rescue") in completed_responses else "initial"
                reasoning = response_message(completed_responses[(run_id, item_id, answer["sample"], phase)]).get("reasoning")
                category = rationale_class(reasoning)
                rationale_counts[category] += 1
                if reasoning and not item_examples:
                    item_examples.append(f"sample {answer['sample']} ({phase}, {category}): {compact_quote(reasoning)}")
            row = {
                "model": entry["model"], "run_id": run_id, "protocol_id": entry["protocol_id"],
                "item_id": item_id, "n_samples": len(ratings), "flat_ratings": sum(flats),
                "flat_fraction": sum(flats) / len(ratings),
                "mean_normalized_spread": float(np.mean([normalized_spread(rating) for rating in ratings])),
                "unique_argmax_fraction": float(np.mean([tie == 1 for tie in ties])),
                "mean_argmax_tie_size": float(np.mean(ties)),
                "mean_sample_tv_from_uniform": float(np.mean([total_variation(p) for p in current[item_id]])),
                "aggregate_tv_from_uniform": total_variation(aggregate),
                "explicit_prompt_or_persona_mismatch": rationale_counts["explicit_prompt_or_persona_mismatch"],
                "explicit_indifference": rationale_counts["explicit_indifference"],
                "explicit_neutral_policy": rationale_counts["explicit_neutral_policy"],
                "other_saved_rationale": rationale_counts["other_saved_rationale"],
                "no_saved_rationale": rationale_counts["no_saved_rationale"],
                "rationale_example": " || ".join(item_examples),
            }
            item_rows.append(row)
            if item_examples:
                examples.append((row, item_examples[0]))

        current_xy = coordinate(current, resolved)
        assert current_xy is not None
        cached_xy = tuple(entry["coords"][:2])
        assert np.allclose(current_xy, cached_xy, atol=1e-12), f"cached coordinate drift for {entry['model']}"
        argmax_xy = coordinate(argmax, resolved)
        assert argmax_xy is not None
        minshift_xy = coordinate(minshift_nonflat, resolved)
        flat_missing_xy = coordinate(flat_missing, resolved)
        coord_rows.append({
            "model": entry["model"], "run_id": run_id, "protocol_id": entry["protocol_id"],
            **coordinate_fields("current_rating_sum", current_xy),
            **coordinate_fields("argmax_ties_split", argmax_xy),
            **coordinate_fields("minshift_nonflat", minshift_xy),
            **coordinate_fields("flat_missing", flat_missing_xy),
            "argmax_delta_l2": distance(current_xy, argmax_xy),
            "minshift_delta_l2": distance(current_xy, minshift_xy),
            "flat_missing_delta_l2": distance(current_xy, flat_missing_xy),
        })

    write_csv(ITEM_CSV_PATH, item_rows)
    write_csv(COORD_CSV_PATH, coord_rows)
    by_model: dict[str, list[dict]] = defaultdict(list)
    for row in item_rows:
        by_model[row["model"]].append(row)

    lines = [
        "# Cross-panel dense-rating content-quality audit",
        "",
        f"- ledger-through UTC: {ledger_through}",
        f"- cache source: `{CACHE_PATH}`",
        f"- ledger source: `{LEDGER_PATH}`",
        f"- complete panels: {len(by_model)}",
        f"- per-item/model table: `{ITEM_CSV_PATH}`",
        f"- coordinate-sensitivity table: `{COORD_CSV_PATH}`",
        "",
        "## Definitions",
        "",
        "Each dense-rated reply assigns a 1-5 rating to every answer in a card. A flat reply gives every "
        "answer the same rating. Normalized spread is `(max rating - min rating) / 4`. "
        "A unique argmax has one highest-rated option; tie size counts all highest-rated options. "
        "Distance from uniform is total variation, `0.5 * sum(abs(p - uniform))`, after normalizing a reply's ratings to p.",
        "",
        "Coordinate sensitivity is diagnostic only. `current_rating_sum` is the published readout. "
        "`argmax_ties_split` puts equal mass on all highest-rated answers. `minshift_nonflat` subtracts the "
        "minimum rating then normalizes, omitting flat replies. `flat_missing` omits flat replies but otherwise "
        "uses the current rating/sum transform. Blank alternative coordinates mean every reply for at least one "
        "required item was flat, so that diagnostic coordinate is undefined. No alternative is published or used to "
        "exclude a panel here.",
        "",
        "Rationale categories are evidence labels, not inferred mental states. `explicit_prompt_or_persona_mismatch` "
        "requires saved reasoning mentioning multi-option confusion, mutually exclusive answers, or a non-personal AI stance. "
        "`explicit_indifference` requires a direct no-preference phrase. `no_saved_rationale` leaves the distinction unresolved.",
        "",
        "## Model summary",
        "",
        "| model | flat / 144 | max flat item | Homosexuality flat | mean spread | mismatch evidence | explicit indifference | max coordinate shift |",
        "|---|---:|---|---:|---:|---:|---:|---:|",
    ]
    coords = {row["model"]: row for row in coord_rows}
    for model, rows in sorted(by_model.items(), key=lambda pair: (-sum(r["flat_ratings"] for r in pair[1]), pair[0])):
        total = sum(row["flat_ratings"] for row in rows)
        worst = max(rows, key=lambda row: (row["flat_ratings"], row["item_id"]))
        homosexuality = next(row for row in rows if row["item_id"] == "Homosexuality")
        mismatch = sum(row["explicit_prompt_or_persona_mismatch"] for row in rows)
        indifference = sum(row["explicit_indifference"] for row in rows)
        mean_spread = float(np.mean([row["mean_normalized_spread"] for row in rows]))
        c = coords[model]
        available_shifts = [float(c[key]) for key in ("argmax_delta_l2", "minshift_delta_l2", "flat_missing_delta_l2") if c[key] != ""]
        shift = "undefined" if not available_shifts else f"{max(available_shifts):.3f}"
        lines.append(
            f"| `{model}` | {total}/144 | {worst['item_id']} ({worst['flat_ratings']}/12) | "
            f"{homosexuality['flat_ratings']}/12 | {mean_spread:.3f} | {mismatch} | {indifference} | {shift} |"
        )

    lines.extend([
        "",
        "## High-flat cells",
        "",
        "Rows below have at least six flat replies. They are retained as observations, not excluded.",
        "",
        "| model | item | flat / 12 | mean spread | aggregate TV | rationale evidence |",
        "|---|---|---:|---:|---:|---|",
    ])
    for row in sorted((row for row in item_rows if row["flat_ratings"] >= 6), key=lambda row: (-row["flat_ratings"], row["model"], row["item_id"])):
        evidence = ", ".join(
            f"{name}={row[name]}" for name in (
                "explicit_prompt_or_persona_mismatch", "explicit_indifference", "explicit_neutral_policy",
                "other_saved_rationale", "no_saved_rationale",
            ) if row[name]
        ) or "none"
        lines.append(
            f"| `{row['model']}` | {row['item_id']} | {row['flat_ratings']}/12 | "
            f"{row['mean_normalized_spread']:.3f} | {row['aggregate_tv_from_uniform']:.3f} | {evidence} |"
        )

    lines.extend(["", "## Saved-reasoning examples", ""])
    for row, example in sorted(examples, key=lambda pair: (-pair[0]["flat_ratings"], pair[0]["model"], pair[0]["item_id"])):
        lines.extend([f"### `{row['model']}` / {row['item_id']}", "", f"> {example}", ""])

    lines.extend([
        "## Interpretation",
        "",
        "The table shows that flat replies and coordinate sensitivity vary across model and item, so Nano alone cannot "
        "supply a general rejection threshold. Saved mismatch rationale is evidence against interpreting those replies as attitudes. "
        "For other cells, no saved rationale does not establish genuine indifference. The direct-choice pilot should therefore compare "
        "the construct rather than silently replace or filter the published rated readout.",
        "",
        "-- PI[gpt-5.6-terra]",
        "",
    ])
    REPORT_PATH.write_text("\n".join(lines))
    print(f"wrote {ITEM_CSV_PATH}: {len(item_rows)} model/item rows")
    print(f"wrote {COORD_CSV_PATH}: {len(coord_rows)} model rows")
    print(f"wrote {REPORT_PATH}: stable through {ledger_through}")


if __name__ == "__main__":
    main()
