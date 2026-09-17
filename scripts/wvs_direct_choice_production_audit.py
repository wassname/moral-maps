#!/usr/bin/env python3
"""Audit the complete Gemini direct-choice production panel without API calls."""
from __future__ import annotations

import csv
import json
import math
from collections import Counter
from decimal import Decimal
from pathlib import Path

import numpy as np

from wvs_direct_choice_production_pilot import (
    ANSWER_INSTRUCTION,
    CACHE_PATH,
    PROMPT_INSTRUCTION,
    RECORDS_PATH,
    RESCUE_INSTRUCTION,
    TOTAL_SAMPLES_PER_ITEM,
    items,
    protocol_id,
    schedule,
)

RUN_ID = "20260917T033051Z_3e9c3d54727e"
PROTOCOL_ID = "3e9c3d54727e46c92af49321604778d9bae85bd83a22e23e1793cbefd06f29e3"
RATED_LEDGER = Path("slop/research/wvs/20260916_openrouter/wvs_iw_requests.jsonl")
RATED_RUN_ID = "20260916T172946Z_cd5db529649a"
CACHE_REPLAY = Path("slop/research/wvs/20260917_direct_choice/production_cache_replay.log")
OUT_CSV = Path("slop/audits/20260917_wvs_gemini37_direct_choice_production_task_1631_by_item.csv")
OUT_MD = Path("slop/audits/20260917_wvs_gemini37_direct_choice_production_task_1631.md")


def read_events(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines()]


def distribution(rows: list[dict], key: str, n: int) -> np.ndarray:
    counts = np.zeros(n, dtype=int)
    for row in rows:
        counts[row[key]] += 1
    return counts / len(rows)


def total_variation(left: np.ndarray, right: np.ndarray) -> float:
    return float(0.5 * np.abs(left - right).sum())


def normalized_entropy(p: np.ndarray) -> float:
    entropy = float(-sum(value * math.log(value) for value in p if value) / math.log(len(p)))
    return 0.0 if entropy <= 0 else entropy


def modal_set(p: np.ndarray) -> list[int]:
    return np.flatnonzero(p == p.max()).tolist()


def display(p: np.ndarray) -> str:
    return "[" + ", ".join(f"{value:.3f}" for value in p) + "]"


def dense_distribution(rows: list[dict], n: int) -> np.ndarray:
    samples = []
    for row in rows:
        ratings = json.loads(row["text"])
        presented = np.array([ratings[str(index)] for index in range(n)], dtype=float)
        canonical = np.empty(n)
        canonical[np.asarray(row["presented_order"])] = presented
        samples.append(canonical / canonical.sum())
    return np.mean(samples, axis=0)


def response_quote(event: dict) -> str:
    message = event["response"]["choices"][0]["message"]
    return (message.get("reasoning") or message.get("content") or "").replace("\n", " ").strip()


def balance_matrix(rows: list[dict], n: int) -> np.ndarray:
    matrix = np.zeros((n, n), dtype=int)
    for row in rows:
        for position, option in enumerate(row["presented_order"]):
            matrix[option, position] += 1
    return matrix


def main() -> None:
    all_events = read_events(RECORDS_PATH)
    events = [event for event in all_events if event.get("run_id") == RUN_ID]
    assert events
    assert {event.get("protocol_id") for event in events} == {PROTOCOL_ID}
    counts = Counter(event["event"] for event in events)
    assert counts == Counter({
        "run_started": 1, "request_started": 240, "request_completed": 240,
        "answer_parsed": 240, "item_result": 12, "run_finished": 1,
    }), counts
    assert not [event for event in events if event["event"] == "request_failed"]
    assert not [event for event in events if event.get("phase") == "rescue"]

    pilot_items = items()
    request_plan = schedule(pilot_items)
    assert protocol_id(pilot_items, request_plan) == PROTOCOL_ID
    run_started = next(event for event in events if event["event"] == "run_started")
    assert run_started["planned_requests"] == 240
    assert run_started["settings"]["prompt_instruction"] == PROMPT_INSTRUCTION
    assert run_started["settings"]["reasoning"] == {"effort": "low"}
    assert run_started["settings"]["structured_output"]

    parsed = [event for event in events if event["event"] == "answer_parsed"]
    assert all(event["parsed"] for event in parsed)
    for event in parsed:
        answer = json.loads(event["text"])
        assert set(answer) == {"answer"}
        assert type(answer["answer"]) is int
        assert event["canonical_choice"] == event["presented_order"][answer["answer"]]

    cache = json.loads(CACHE_PATH.read_text())
    assert cache["completed"][PROTOCOL_ID]["run_id"] == RUN_ID
    assert cache["completed"][PROTOCOL_ID]["complete"]
    assert "network_request_events_added=0" in CACHE_REPLAY.read_text()

    completed = [event for event in events if event["event"] == "request_completed"]
    prompt_tokens = sum(event["usage"]["prompt_tokens"] for event in completed)
    completion_tokens = sum(event["usage"]["completion_tokens"] for event in completed)
    reasoning_tokens = sum(event["usage"]["completion_tokens_details"]["reasoning_tokens"] for event in completed)
    cost = sum(Decimal(str(event["usage"]["cost"])) for event in completed)
    refusals = sum(bool(event["response"]["choices"][0]["message"].get("refusal")) for event in completed)
    assert refusals == 0

    rated = read_events(RATED_LEDGER)
    rows = []
    item_summaries = {}
    for item in pilot_items:
        item_rows = [event for event in parsed if event["item_id"] == item["id"]]
        assert len(item_rows) == TOTAL_SAMPLES_PER_ITEM
        n = item["n"]
        matrix = balance_matrix(item_rows, n)
        if n in (2, 4, 10):
            assert np.all(matrix == TOTAL_SAMPLES_PER_ITEM // n), matrix
            balance_status = "exact"
        else:
            assert matrix.max() - matrix.min() <= 1, matrix
            balance_status = "nearest (6/7)"
        selected_position = distribution(item_rows, "presented_choice", n)
        canonical_choice = distribution(item_rows, "canonical_choice", n)
        first_half = distribution([event for event in item_rows if event["sample"] < 10], "canonical_choice", n)
        second_half = distribution([event for event in item_rows if event["sample"] >= 10], "canonical_choice", n)
        canonical_rows = [event for event in item_rows if event["order_name"] == "canonical"]
        reversed_rows = [event for event in item_rows if event["order_name"] == "reversed"]
        canonical_p = distribution(canonical_rows, "canonical_choice", n)
        reversed_p = distribution(reversed_rows, "canonical_choice", n)
        rated_rows = [
            event for event in rated
            if event.get("run_id") == RATED_RUN_ID and event["event"] == "answer_parsed" and event["item_id"] == item["id"]
        ]
        assert len(rated_rows) == 12
        rated_p = dense_distribution(rated_rows, n)
        row = {
            "item_id": item["id"], "axis": item["axis"], "n_options": n,
            "position_balance": balance_status, "position_matrix": json.dumps(matrix.tolist()),
            "canonical_requests": len(canonical_rows), "reversed_requests": len(reversed_rows),
            "selected_presented_position_p": display(selected_position),
            "selected_position_normalized_entropy": normalized_entropy(selected_position),
            "selected_position_tv_from_uniform": total_variation(selected_position, np.full(n, 1 / n)),
            "selected_position_warning_tv_gt_0_25": total_variation(selected_position, np.full(n, 1 / n)) > 0.25,
            "canonical_choice_p": display(canonical_choice),
            "canonical_choice_normalized_entropy": normalized_entropy(canonical_choice),
            "schedule_first_ten_p": display(first_half), "schedule_last_ten_p": display(second_half),
            "schedule_half_tv": total_variation(first_half, second_half),
            "schedule_half_modal_sets": f"{modal_set(first_half)} / {modal_set(second_half)}",
            "canonical_direction_p": display(canonical_p), "reversed_direction_p": display(reversed_p),
            "direction_tv": total_variation(canonical_p, reversed_p),
            "direction_modal_sets": f"{modal_set(canonical_p)} / {modal_set(reversed_p)}",
            "legacy_dense_rated_p": display(rated_p),
            "direct_vs_legacy_rated_tv": total_variation(canonical_choice, rated_p),
        }
        rows.append(row)
        item_summaries[item["id"]] = row

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    through = max(event["recorded_at_utc"] for event in events)
    warning_items = [row["item_id"] for row in rows if row["selected_position_warning_tv_gt_0_25"]]
    high_half = [row["item_id"] for row in rows if row["schedule_half_tv"] > 0.25]
    homo = next(event for event in completed if event["item_id"] == "Homosexuality" and event["sample"] == 0)
    abortion = next(event for event in completed if event["item_id"] == "Abortion" and event["sample"] == 0)
    lines = [
        "# Audit: Gemini 3.7 Flash full direct-choice production pilot, task 1631",
        "",
        "- target: preregistered 12-item direct-choice construct panel, not a map point or coordinate replacement",
        "- Pueue: task 1631, API queue, success, 2026-09-17 11:30:43-11:45:43 +08:00",
        "- label: `why: test full behavior-values direct-choice readout with exact prompt identity; resolve: audit position preference, entropy and schedule halves before any other model`",
        f"- run: `{RUN_ID}`, protocol: `{PROTOCOL_ID}`",
        f"- primary ledger: `{RECORDS_PATH}` through {through}",
        f"- complete cache: `{CACHE_PATH}`; replay: `{CACHE_REPLAY}`",
        "- complete Pueue logs: `slop/research/wvs/20260917_direct_choice/task_1631_clean.log` and `slop/research/wvs/20260917_direct_choice/task_1631_full.log` (each has the one application completion line; the clean-log header records 1 of 1 lines)",
        f"- legacy/proxy comparator only: rated run `{RATED_RUN_ID}` in `{RATED_LEDGER}`",
        f"- per-item table: `{OUT_CSV}`",
        "- excluded predecessor: run `20260917T032722Z_075bd0ef0c96` was killed with 10 completed request phases and no parsed samples; it is neither merged nor compared here.",
        "",
        "## Stage table",
        "",
        "| stage | expected | observed | expected? | clues | missing metric | consequence |",
        "|---|---|---|---|---|---|---|",
        "| identity | behavioral-values prompt, low reasoning, strict one-choice schema | saved run settings and recomputed protocol hash match the preregistered identity | yes | run_started + code assertion | provider-side prompt rendering | correct protocol partition |",
        "| schedule | 12 x 20, exact option-position exposure for n=2/4/10 and nearest for n=3 | 240 planned/started/completed/parsed; all position matrices meet their registered balance condition | yes | ledger and per-item CSV | randomized repeat | position diagnostic is interpretable |",
        "| parse and rescue | every selected response maps to a canonical option, failure is loud | 240/240 valid one-key JSON; 0 failures, 0 rescues, 0 refusals | yes | ledger event count and re-decode assertions | semantic answer audit | mechanics are complete |",
        f"| provider accounting | usage retained for every phase | prompt {prompt_tokens:,}; completion {completion_tokens:,}; reasoning {reasoning_tokens:,}; provider cost USD {cost:.8f} | yes | 240 completed usage objects | billing export | under registered USD 4 reserve |",
        f"| generic position preference | selected-presented-position TV from uniform is diagnostic, warning >0.25 | no warnings; maximum is {max(row['selected_position_tv_from_uniform'] for row in rows):.3f} | yes | per-item CSV | independent seed | no large generic position preference observed |",
        f"| schedule stability | first 10 vs last 10 canonical distributions are descriptive | >0.25 TV for {', '.join(high_half) if high_half else 'none'} | partial | per-item CSV | independent balanced schedule | temporal/direction variability remains for named items |",
        "| persistence | cache only after complete panel; replay makes no requests | cache complete and replay recorded zero added request events | yes | cache and replay hash | external billing export | raw response evidence reusable |",
        "",
        "## Primary evidence",
        "",
        "The Pueue log has one application completion line, so the append-only ledger is the primary run evidence. It has exactly 240 initial request starts, 240 initial completions, 240 parsed responses, 12 item results, one run start and one run finish. The prior killed run has a different run/protocol ID and is excluded.",
        "",
        "The production prompt, recorded both in the manifest and every request setting, was:",
        "",
        f"> {PROMPT_INSTRUCTION}",
        "",
        "Homosexuality sample 0 saved this provider reasoning:",
        "",
        f"> {response_quote(homo)}",
        "",
        "Abortion sample 0 saved this provider reasoning:",
        "",
        f"> {response_quote(abortion)}",
        "",
        "epistemic context: these are two pre-specified first samples from different 10-option WVS items, retained provider reasoning under the production prompt. They show model self-description, not human attitudes.",
        "",
        "## Preregistered item diagnostics",
        "",
        "Selected-position entropy is normalized by log(option count). TV from uniform measures generic preference for a displayed position, not substantive choice. Position balance is exact for n=2,4,10 and nearest possible for n=3. Schedule and direction comparisons are descriptive because their direction compositions differ for n=3/n=4.",
        "",
        "| item | n | balance | selected-position TV | selected-position H | canonical-choice H | schedule-half TV | modal sets | direction TV | direct vs legacy-rated TV |",
        "|---|---:|---|---:|---:|---:|---:|---|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['item_id']} | {row['n_options']} | {row['position_balance']} | "
            f"{row['selected_position_tv_from_uniform']:.3f} | {row['selected_position_normalized_entropy']:.3f} | "
            f"{row['canonical_choice_normalized_entropy']:.3f} | {row['schedule_half_tv']:.3f} | "
            f"{row['schedule_half_modal_sets']} | {row['direction_tv']:.3f} | {row['direct_vs_legacy_rated_tv']:.3f} |"
        )
    lines.extend([
        "",
        f"No item crosses the preregistered position-bias warning TV >0.25. The largest selected-position TV is {max(row['selected_position_tv_from_uniform'] for row in rows):.3f}. This does not prove absence of a smaller position effect or stable attitude-like choices.",
        "",
        "## Hypotheses",
        "",
        "### H1 [measurement | Highly Likely | 80%]",
        "",
        "- Mechanism: the cyclic rotations removed the earlier literal-example position anchor but do not establish an attitude-like WVS construct.",
        f"- Evidence: all selected-position TVs are <= {max(row['selected_position_tv_from_uniform'] for row in rows):.3f}; meanwhile Homosexuality reasoning says `{response_quote(homo)}`.",
        "- Contrary evidence: the prompt explicitly asks about values expressed by assistant behavior, and several canonical-choice distributions are highly concentrated.",
        "- Discriminating test: repeat the same full balanced schedule with another sampled run, preserving prompt and schema. Reproduced substantive choices with low position TV support stability; changed choices despite low position TV show sample/prompt sensitivity.",
        "- Fix/action: keep this as a direct-choice construct panel, separate from dense-rated coordinates and all family/capability fits.",
        "- Interpretability: partial, for sampled model behavior under the exact prompt.",
        "",
        "### H2 [measurement | Likely | 65%]",
        "",
        "- Mechanism: schedule direction or request time remains associated with substantive output variation for the two 10-option items.",
        f"- Evidence: schedule-half TV is {item_summaries['Homosexuality']['schedule_half_tv']:.3f} for Homosexuality and {item_summaries['Abortion']['schedule_half_tv']:.3f} for Abortion; each exceeds the descriptive 0.25 reference.",
        "- Contrary evidence: both retain the same Homosexuality modal set across halves, and generic displayed-position TVs are low.",
        "- Discriminating test: interleave one request from each direction/rotation rather than completing rotation blocks, with the identical prompt and 20 samples.",
        "- Fix/action: do not interpret the two named item distributions as time-invariant without replication.",
        "- Interpretability: partial.",
        "",
        "### H3 [bug | Unlikely | 15%]",
        "",
        "- Mechanism: canonical decoding or cached identity could be incorrect despite successful schema parsing.",
        "- Evidence: this audit re-decodes all 240 raw JSON values and verifies each stored canonical choice against its presented order; it recomputes the protocol ID and verifies a zero-new-request cache replay.",
        "- Contrary evidence: the audit shares the same raw-record interpretation and has no independent provider billing export.",
        "- Discriminating test: independent raw-ledger decoder and provider billing reconciliation.",
        "- Fix/action: no code change is indicated from this evidence.",
        "- Interpretability: yes for recorded responses and cache behavior.",
        "",
        "### H4 [measurement | Likely | 70%]",
        "",
        "- Mechanism: direct choice and legacy dense rating are different elicitation layers, even after the literal dense-example concern is isolated.",
        f"- Evidence: direct-versus-legacy rated TV ranges from {min(row['direct_vs_legacy_rated_tv'] for row in rows):.3f} to {max(row['direct_vs_legacy_rated_tv'] for row in rows):.3f} across the same Gemini items.",
        "- Contrary evidence: the two protocols differ in more than rating versus choice, including prompt wording, schedule, and sample count.",
        "- Discriminating test: a controlled same-prompt comparison that changes only answer format, after parent review.",
        "- Fix/action: never combine this panel with dense-rated map points or capability fits.",
        "- Interpretability: yes for observed protocol difference, no for a claim that one is the correct coordinate construct.",
        "",
        "## Decision",
        "",
        "1. Resolve-condition verdict: **met for mechanics and preregistered diagnostics; not yet met for a broad construct migration.** The complete panel, parser, balance, usage, and cache gates pass. The panel also records schedule/direction variation rather than hiding it.",
        "2. Prediction check: the balanced schedule predicted exact position exposure for n=2/4/10, nearest balance for n=3, and no automatic hard exclusion from the position TV diagnostic. These are supported. No prediction claimed that all items would have low schedule-half TV.",
        "3. Earliest unsupported link: direct choices under this assistant-behavior prompt are a stable substitute for dense-rated WVS coordinates.",
        "4. Validity: define invalid as a result suitable for merging into published rated coordinates or for authorizing the wider paid expansion. P(invalid for that use) is highly likely, about 0.80. The ledger and direct-choice behavioral observations are credible under the exact protocol.",
        "5. Highest-information clues: complete 240/240 parsing and replay, exact option-position matrices, low generic position TV, and the two 10-option schedule-half shifts. Together these separate mechanics from remaining construct and stability uncertainty.",
        "6. Missing metrics: independent full-schedule replication; fully interleaved rotation control; external billing reconciliation; and a reviewed comparison design that changes only response format.",
        "7. Bugs requiring code changes: none established. The n=3 near-balance and n=4 direction imbalance are registered constraints, not silent behavior.",
        "8. Misconceptions requiring reinterpretation: low generic selected-position TV is evidence against a large generic position preference, not proof of human-like values or a valid coordinate migration.",
        "9. What would change the verdict: stable canonical distributions under an independent, fully interleaved repeat would increase confidence; large changes would support request-time or remaining presentation sensitivity.",
        "10. Recommended sequence: pause. Parent review should decide whether the next bounded action is a same-prompt fully interleaved replication or a controlled answer-format comparison. Do not dispatch Grok/OpenAI/Google/Muse panels or publish a direct-choice map from this one panel.",
        "",
        "-- PI[gpt-5.6-terra]",
        "",
    ])
    OUT_MD.write_text("\n".join(lines))
    print(f"wrote {OUT_CSV}: {len(rows)} item rows")
    print(f"wrote {OUT_MD}: 240/240 parsed, cost USD {cost:.8f}, position warnings={len(warning_items)}")


if __name__ == "__main__":
    main()
