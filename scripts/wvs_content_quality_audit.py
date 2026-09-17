#!/usr/bin/env python3
"""Summarize constant dense-rating answers from every cached complete WVS panel."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

CACHE_PATH = Path("slop/research/wvs/20260916_openrouter/wvs_iw_rated.json")
LEDGER_PATH = Path("slop/research/wvs/20260916_openrouter/wvs_iw_requests.jsonl")
CSV_PATH = Path("slop/audits/20260917_wvs_content_quality_by_item.csv")
REPORT_PATH = Path("slop/audits/20260917_wvs_content_quality_cross_panel.md")

CONSTRUCT_MISMATCH = (
    "mutually exclusive",
    "all the options",
    "each option",
    "every answer",
    "as an ai",
    "my nature as an ai",
    "i lack personal",
    "lack personal experience",
    "do not have personal",
    "don't have personal",
    "cannot personally",
    "can't personally",
    "do not hold beliefs",
    "don't hold beliefs",
    "non-human perspective",
)
EXPLICIT_INDIFFERENCE = ("no preference",)
NEUTRAL_POLICY = ("neutral", "neutrality", "balanced perspective")


def response_message(event: dict) -> dict:
    return event["response"]["choices"][0]["message"]


def constant_rating(text: str) -> bool:
    ratings = json.loads(text)
    values = list(ratings.values())
    assert values, "parsed rating object must have values"
    return len(set(values)) == 1


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
    if reasoning is None:
        return ""
    return " ".join(reasoning.split())[:280].rstrip()


def main() -> None:
    cache = json.loads(CACHE_PATH.read_text())
    completed = cache["completed"]
    assert completed, "cached completed panels are required"

    parsed: dict[str, list[dict]] = defaultdict(list)
    completed_responses: dict[tuple[str, str, int, str], dict] = {}
    with LEDGER_PATH.open() as fh:
        for line in fh:
            event = json.loads(line)
            run_id = event.get("run_id")
            if run_id not in {entry["run_id"] for entry in completed.values()}:
                continue
            if event["event"] == "answer_parsed":
                assert event["parsed"], f"complete cache run has unparsable answer: {event}"
                parsed[run_id].append(event)
            if event["event"] == "request_completed":
                key = (run_id, event["item_id"], event["sample"], event["phase"])
                completed_responses[key] = event

    rows: list[dict] = []
    for entry in sorted(completed.values(), key=lambda value: value["model"]):
        run_id = entry["run_id"]
        answers = parsed[run_id]
        assert len(answers) == entry["n_items"] * entry["n_samples"], (
            f"{entry['model']} {run_id}: {len(answers)} parsed answers, expected "
            f"{entry['n_items'] * entry['n_samples']}"
        )
        by_item: dict[str, list[dict]] = defaultdict(list)
        for answer in answers:
            by_item[answer["item_id"]].append(answer)
        assert len(by_item) == entry["n_items"], f"{entry['model']}: item count drift"
        for item_id, item_answers in sorted(by_item.items()):
            assert len(item_answers) == entry["n_samples"], f"{entry['model']} {item_id}: sample count drift"
            constant_answers = [answer for answer in item_answers if constant_rating(answer["text"])]
            rationale_counts = Counter()
            examples: list[str] = []
            for answer in constant_answers:
                phase = "rescue" if (run_id, item_id, answer["sample"], "rescue") in completed_responses else "initial"
                response = completed_responses[(run_id, item_id, answer["sample"], phase)]
                rationale = response_message(response).get("reasoning")
                classification = rationale_class(rationale)
                rationale_counts[classification] += 1
                if rationale and len(examples) < 2:
                    examples.append(
                        f"sample {answer['sample']} ({phase}, {classification}): {compact_quote(rationale)}"
                    )
            rows.append(
                {
                    "model": entry["model"],
                    "run_id": run_id,
                    "protocol_id": entry["protocol_id"],
                    "item_id": item_id,
                    "n_samples": entry["n_samples"],
                    "constant_ratings": len(constant_answers),
                    "constant_share": len(constant_answers) / entry["n_samples"],
                    "explicit_prompt_or_persona_mismatch": rationale_counts["explicit_prompt_or_persona_mismatch"],
                    "explicit_indifference": rationale_counts["explicit_indifference"],
                    "explicit_neutral_policy": rationale_counts["explicit_neutral_policy"],
                    "other_saved_rationale": rationale_counts["other_saved_rationale"],
                    "no_saved_rationale": rationale_counts["no_saved_rationale"],
                    "rationale_examples": " || ".join(examples),
                }
            )

    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with CSV_PATH.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    by_model: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_model[row["model"]].append(row)
    fetched_utc = datetime.now(UTC).isoformat()
    lines = [
        "# Cross-panel dense-rating content-quality audit",
        "",
        f"- generated UTC: {fetched_utc}",
        f"- cache source: `{CACHE_PATH}`",
        f"- ledger source: `{LEDGER_PATH}`",
        f"- complete panels: {len(by_model)}",
        f"- per-item/model source table: `{CSV_PATH}`",
        "",
        "## What this measures",
        "",
        "A constant rating gives every answer option in one presented card the same 1-5 rating. "
        "It is parse-valid but maps to a uniform categorical distribution after renormalization. "
        "This is a descriptive diagnostic, not a rejection threshold: a constant rating can mean "
        "indifference, a deliberate neutral policy, or a misunderstanding of the multi-option prompt.",
        "",
        "The rationale categories are evidence labels, not inferred mental states. "
        "`explicit_prompt_or_persona_mismatch` requires saved reasoning to mention multi-option "
        "format confusion, mutually exclusive answers, or a non-personal AI stance. "
        "`explicit_indifference` requires a direct no-preference phrase. "
        "`explicit_neutral_policy` records a neutral-policy phrase without a stronger mismatch signal. "
        "`no_saved_rationale` means the ledger cannot distinguish indifference from misunderstanding.",
        "",
        "## Model summary",
        "",
        "| model | constant / 144 | max item | Homosexuality | explicit mismatch | explicit indifference | no saved rationale |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for model, model_rows in sorted(by_model.items(), key=lambda pair: (-sum(r["constant_ratings"] for r in pair[1]), pair[0])):
        total = sum(row["constant_ratings"] for row in model_rows)
        worst = max(model_rows, key=lambda row: (row["constant_ratings"], row["item_id"]))
        homosexuality = next(row for row in model_rows if row["item_id"] == "Homosexuality")
        mismatch = sum(row["explicit_prompt_or_persona_mismatch"] for row in model_rows)
        indifference = sum(row["explicit_indifference"] for row in model_rows)
        no_rationale = sum(row["no_saved_rationale"] for row in model_rows)
        lines.append(
            f"| `{model}` | {total}/144 | {worst['item_id']} ({worst['constant_ratings']}/12) | "
            f"{homosexuality['constant_ratings']}/12 | {mismatch} | {indifference} | {no_rationale} |"
        )

    lines.extend([
        "",
        "## Flagged item/model cells",
        "",
        "Rows below have at least six constant replies. They are not excluded here. "
        "The full CSV retains every 49 x 12 cell for a later threshold or modeling decision.",
        "",
        "| model | item | constant / 12 | rationale evidence |",
        "|---|---|---:|---|",
    ])
    for row in sorted((row for row in rows if row["constant_ratings"] >= 6), key=lambda row: (-row["constant_ratings"], row["model"], row["item_id"])):
        evidence = ", ".join(
            f"{name}={row[name]}" for name in (
                "explicit_prompt_or_persona_mismatch",
                "explicit_indifference",
                "explicit_neutral_policy",
                "other_saved_rationale",
                "no_saved_rationale",
            ) if row[name]
        ) or "none"
        lines.append(f"| `{row['model']}` | {row['item_id']} | {row['constant_ratings']}/12 | {evidence} |")

    examples = [row for row in rows if row["rationale_examples"]]
    lines.extend(["", "## Saved-reasoning examples", ""])
    if examples:
        for row in sorted(examples, key=lambda row: (-row["constant_ratings"], row["model"], row["item_id"])):
            lines.extend([
                f"### `{row['model']}` / {row['item_id']}",
                "",
                f"> {row['rationale_examples']}",
                "",
            ])
    else:
        lines.extend(["No constant-rated answer had a saved reasoning field.", ""])

    lines.extend([
        "## Interpretation",
        "",
        "The table establishes rate and available explanation evidence, not whether a model is genuinely indifferent. "
        "An explicit prompt-or-persona mismatch is direct evidence against treating that answer as an attitude measurement. "
        "The saved runs contain no direct evidence that a constant rating expresses a stable human-like attitude of indifference; "
        "no saved rationale leaves the alternatives unresolved. Any future gate must be selected against the full distribution "
        "and documented before it excludes or reruns a panel.",
        "",
        "-- PI[gpt-5.6-terra]",
        "",
    ])
    REPORT_PATH.write_text("\n".join(lines))
    print(f"wrote {CSV_PATH}: {len(rows)} model/item rows")
    print(f"wrote {REPORT_PATH}: {len(by_model)} complete panels")


if __name__ == "__main__":
    main()
