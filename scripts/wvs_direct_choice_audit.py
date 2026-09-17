#!/usr/bin/env python3
"""Audit the preregistered Gemini direct-choice construct pilot without API calls."""
from __future__ import annotations

import csv
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

import numpy as np

RUN_ID = "20260917T025121Z_aed0e29dd4ee"
PROTOCOL_ID = "aed0e29dd4ee423dbbfa0c294a84b2ae4bd6a36d6fc4bf569120034ac5b75090"
MODEL = "google/gemini-3.7-flash"
DIRECT_LEDGER = Path("slop/research/wvs/20260917_direct_choice/gemini37_direct_choice_requests.jsonl")
DIRECT_CACHE = Path("slop/research/wvs/20260917_direct_choice/gemini37_direct_choice_cache.json")
RATED_LEDGER = Path("slop/research/wvs/20260916_openrouter/wvs_iw_requests.jsonl")
RATED_RUN_ID = "20260916T172946Z_cd5db529649a"
OUT_CSV = Path("slop/audits/20260917_wvs_gemini37_direct_choice_task_1628_by_item.csv")
OUT_MD = Path("slop/audits/20260917_wvs_gemini37_direct_choice_task_1628.md")


def events(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines()]


def total_variation(left: np.ndarray, right: np.ndarray) -> float:
    return float(0.5 * np.abs(left - right).sum())


def choice_distribution(rows: list[dict], n: int) -> np.ndarray:
    counts = np.zeros(n)
    for row in rows:
        counts[row["canonical_choice"]] += 1
    return counts / len(rows)


def dense_rated_distribution(rows: list[dict], n: int) -> np.ndarray:
    samples = []
    for row in rows:
        ratings = json.loads(row["text"])
        order = row["presented_order"]
        presented = np.array([ratings[str(index)] for index in range(n)], dtype=float)
        canonical = np.empty(n)
        canonical[np.asarray(order)] = presented
        samples.append(canonical / canonical.sum())
    return np.mean(samples, axis=0)


def display(p: np.ndarray) -> str:
    return "[" + ", ".join(f"{value:.3f}" for value in p) + "]"


def midpoint_mass(p: np.ndarray) -> str:
    if len(p) == 2:
        return "not defined for binary"
    lower = len(p) // 2 - 1
    upper = len(p) // 2
    return f"{p[lower] + p[upper]:.3f} (options {lower}/{upper})"


def quote(message: dict) -> str:
    reasoning = message.get("reasoning")
    return (reasoning or message.get("content") or "").replace("\n", " ").strip()


def main() -> None:
    direct = [event for event in events(DIRECT_LEDGER) if event.get("run_id") == RUN_ID]
    rated = [event for event in events(RATED_LEDGER) if event.get("run_id") == RATED_RUN_ID]
    assert direct and rated
    counts = Counter(event["event"] for event in direct)
    assert counts == Counter({"request_started": 96, "request_completed": 96, "answer_parsed": 96,
                              "item_result": 4, "run_started": 1, "run_finished": 1}), counts
    parsed = [event for event in direct if event["event"] == "answer_parsed"]
    assert len(parsed) == 96 and all(event["parsed"] for event in parsed)
    for event in parsed:
        decoded = json.loads(event["text"])
        assert set(decoded) == {"answer"}
        assert type(decoded["answer"]) is int
        assert event["canonical_choice"] == event["presented_order"][decoded["answer"]]
    assert not [event for event in direct if event["event"] == "request_failed"]
    assert not [event for event in direct if event.get("phase") == "rescue"]
    assert {event["protocol_id"] for event in direct} == {PROTOCOL_ID}
    assert json.loads(DIRECT_CACHE.read_text())["completed"][PROTOCOL_ID]["complete"]

    request_events = [event for event in direct if event["event"] == "request_completed"]
    prompt_tokens = sum(event["usage"]["prompt_tokens"] for event in request_events)
    completion_tokens = sum(event["usage"]["completion_tokens"] for event in request_events)
    reasoning_tokens = sum(event["usage"]["completion_tokens_details"]["reasoning_tokens"] for event in request_events)
    cost = sum(Decimal(str(event["usage"]["cost"])) for event in request_events)
    refusals = sum(event["response"]["choices"][0]["message"].get("refusal") is not None for event in request_events)

    rows = []
    for item_id in ("Homosexuality", "Religion", "God", "Independence"):
        direct_rows = [event for event in parsed if event["item_id"] == item_id]
        n = len(direct_rows[0]["presented_order"])
        canonical = [event for event in direct_rows if event["order_name"] == "canonical"]
        reversed_order = [event for event in direct_rows if event["order_name"] == "reversed"]
        assert len(canonical) == len(reversed_order) == 12
        direct_p = choice_distribution(direct_rows, n)
        canonical_p = choice_distribution(canonical, n)
        reversed_p = choice_distribution(reversed_order, n)
        rated_rows = [event for event in rated if event["event"] == "answer_parsed" and event["item_id"] == item_id]
        assert len(rated_rows) == 12
        rated_p = dense_rated_distribution(rated_rows, n)
        canonical_argmax = np.flatnonzero(canonical_p == canonical_p.max()).tolist()
        reversed_argmax = np.flatnonzero(reversed_p == reversed_p.max()).tolist()
        rows.append({
            "item_id": item_id, "n_options": n, "canonical_n": len(canonical), "reversed_n": len(reversed_order),
            "canonical_distribution": display(canonical_p), "reversed_distribution": display(reversed_p),
            "order_half_tv": total_variation(canonical_p, reversed_p),
            "canonical_argmax": canonical_argmax, "reversed_argmax": reversed_argmax,
            "argmax_agrees": canonical_argmax == reversed_argmax,
            "direct_distribution": display(direct_p), "rated_distribution": display(rated_p),
            "direct_vs_rated_tv": total_variation(direct_p, rated_p),
            "rated_middle_mass": midpoint_mass(rated_p),
        })

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    first_homosexuality = next(event for event in request_events if event["item_id"] == "Homosexuality" and event["sample"] == 0)
    first_god = next(event for event in request_events if event["item_id"] == "God" and event["sample"] == 0)
    ledger_through = max(event["recorded_at_utc"] for event in direct)
    by_item = {row["item_id"]: row for row in rows}
    lines = [
        "# Audit: Gemini 3.7 Flash direct-choice WVS pilot, task 1628",
        "",
        "- target: 96-call direct-choice construct pilot, not a map panel",
        f"- Pueue: task 1628, API queue, success, 2026-09-17 10:51:14-10:56:58 +08:00",
        "- label: `why: test direct choice against flat dense ratings; resolve: audit interleaved order agreement and distribution difference before more models`",
        f"- run: `{RUN_ID}`, protocol: `{PROTOCOL_ID}`",
        f"- primary ledger: `{DIRECT_LEDGER}` through {ledger_through}",
        f"- direct cache: `{DIRECT_CACHE}`",
        f"- comparison rated run: `{RATED_RUN_ID}` in `{RATED_LEDGER}`",
        f"- per-item table: `{OUT_CSV}`",
        "",
        "## Stage table",
        "",
        "| stage | expected | observed | expected? | clues | missing metric | consequence |",
        "|---|---|---|---|---|---|---|",
        "| request plan | 96 calls, 12 canonical and 12 reversed per item, interleaved | 96 starts and 96 completions; every item has 12 valid per order | yes | ledger event counts; cache item results | provider-side request ordering timestamp | order halves are available for comparison |",
        "| strict parse | 96 schema-valid single choices | 96/96 `answer_parsed=true`; 0 failed phases | yes | ledger | provider schema conformance independent of parser | mechanics did not drop samples |",
        "| rescue/refusal | zero or recorded | 0 rescue phases; 0 `message.refusal` | yes | ledger request records | semantic non-answer count beyond refusal field | parse success does not establish personal-attitude semantics |",
        "| accounting | provider usage retained | prompt 15,445; completion 12,848; reasoning 12,272; observed cost USD 0.0643245 | yes | all 96 completed usage records | external billing export | below registered reserve, exact provider field retained |",
        "| order-half control | canonical and reversed distributions agree if position does not dominate | Homosexuality TV=0.833 and different argmax; other three TV <=0.083 with matching argmax | no | per-item table | repeated independent run | direct-choice Homosexuality aggregate is position-confounded |",
        "| canonical decoder | reverse order maps presented index back to canonical index | independently re-decoded all 96 raw JSON choices and orders with exact agreement | yes | audit assertion | a second implementation or repetition | mapping bug is less likely than an order effect |",
        "| construct comparison | quantify difference from dense-rated readout | direct-vs-rated TV: Homosexuality 0.694, Religion 0.564, God 0.500, Independence 0.220 | yes, descriptive only | per-item table | baseline direct choice from another model | no coordinate replacement or wider batch decision |",
        "| persistence | complete result reusable only if all samples valid | cache has one complete protocol entry and ledger has 294 events | yes | cache + ledger | cache replay, not needed for this decision | source evidence retained |",
        "",
        "## Chronological evidence",
        "",
        "The task's own full Pueue output is one completion line, so the append-only request ledger is the primary evidence. It contains 96 initial `request_started`, 96 initial `request_completed`, 96 parsed choices, four item results, and one run boundary each. The source code writes a cache entry only after complete results; the cache records `complete: true` for this protocol.",
        "",
        "The direct prompt is recoverable per request. Homosexuality sample 0 used the exact instruction: `Think briefly about which ONE answer best reflects your own view. Do not analyze the survey design. Answer immediately.` Its saved provider reasoning says:",
        "",
        f"> {quote(first_homosexuality['response']['choices'][0]['message'])}",
        "",
        "epistemic context: provider reasoning saved in this pilot's first completed request, not a human self-report.",
        "",
        "God sample 0 shows the same unresolved persona issue despite schema-valid JSON:",
        "",
        f"> {quote(first_god['response']['choices'][0]['message'])}",
        "",
        "epistemic context: provider reasoning saved in this pilot's first completed request, not a human self-report.",
        "",
        "## Preregistered order-half and construct results",
        "",
        "| item | canonical p | reversed p | order TV | argmax agrees | direct p | dense-rated p | direct vs rated TV | dense rated central mass |",
        "|---|---|---|---:|---|---|---|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['item_id']} | {row['canonical_distribution']} | {row['reversed_distribution']} | "
            f"{row['order_half_tv']:.3f} | {row['argmax_agrees']} ({row['canonical_argmax']} vs {row['reversed_argmax']}) | "
            f"{row['direct_distribution']} | {row['rated_distribution']} | {row['direct_vs_rated_tv']:.3f} | {row['rated_middle_mass']} |"
        )
    lines.extend([
        "",
        "For even non-binary cards, central mass is the dense-rated mass in the two middle categories. For binary cards it is not defined. An all-equal dense rating normalizes to a uniform categorical, not to one middle answer; this is why the table reports full distributions and total variation rather than calling all flat dense replies a middle choice.",
        "",
        "## Hypotheses",
        "",
        "### H1 [method | Highly Likely | 80%]",
        "",
        "- Mechanism: Homosexuality direct choices are sensitive to the presented order, so its pooled direct distribution is not a stable construct readout.",
        f"- Evidence: canonical p is {by_item['Homosexuality']['canonical_distribution']} while reversed p is {by_item['Homosexuality']['reversed_distribution']}; their TV is {by_item['Homosexuality']['order_half_tv']:.3f} and argmax changes from {by_item['Homosexuality']['canonical_argmax']} to {by_item['Homosexuality']['reversed_argmax']}.",
        "- Contrary evidence: Religion, God, and Independence have matching order-half argmaxes and TV at most 0.083.",
        "- Discriminating test: a second 24-per-item run with a balanced random permutation schedule. Low TV again would weaken this explanation; a large TV tied to option position would strengthen it.",
        "- Fix/action: do not use the pooled Homosexuality direct distribution to replace rated coordinates; review a redesigned order control before more paid panels.",
        "- Interpretability: partial, mechanics and the observed order effect are interpretable; Homosexuality attitude distribution is not.",
        "",
        "### H2 [measurement | Likely | 65%]",
        "",
        "- Mechanism: Gemini may answer the question as an AI without personal beliefs rather than supply an attitude-like direct choice.",
        f"- Evidence: God sample 0 reasoning says `{quote(first_god['response']['choices'][0]['message'])}`.",
        "- Contrary evidence: every final response is a valid selected answer, and three items have stable order-half argmaxes.",
        "- Discriminating test: compare an explicitly role-conditioned construct with this prompt while retaining the same order randomization. A changed distribution with lower persona-language would support this explanation.",
        "- Fix/action: retain raw reasoning and interpret current results as model behavior under this prompt, not personal survey attitudes.",
        "- Interpretability: partial.",
        "",
        "### H3 [measurement | Likely | 60%]",
        "",
        "- Mechanism: forced one-answer choice and dense all-option rating are different elicitation constructs, even where order halves agree.",
        f"- Evidence: Religion direct-vs-rated TV is {by_item['Religion']['direct_vs_rated_tv']:.3f}, God is {by_item['God']['direct_vs_rated_tv']:.3f}, and Independence is {by_item['Independence']['direct_vs_rated_tv']:.3f}.",
        "- Contrary evidence: this is one model and four items; Gemini's persona and order effects can also cause the difference.",
        "- Discriminating test: repair the order control, then compare one or more lower-flat models under the same direct-choice protocol.",
        "- Fix/action: describe the distributions as a construct comparison, not evidence that the published rated map is wrong.",
        "- Interpretability: yes for difference under these prompts, no for a general claim about models or WVS coordinates.",
        "",
        "### H4 [bug | Unlikely | 20%]",
        "",
        "- Mechanism: a mapping error could create the apparent reversed-order effect.",
        "- Evidence: the audit independently re-decodes all 96 raw JSON responses, validates the one-key schema, and maps `answer` through each stored `presented_order`; every reconstructed canonical choice equals the ledger field.",
        "- Contrary evidence: the audit is a second decoder, but it is not a second experimental run.",
        "- Discriminating test: repeat the balanced-permutation control after review. A large position-linked shift despite a new run would reject the mapping-bug explanation.",
        "- Fix/action: no mapping change is justified from this evidence.",
        "- Interpretability: yes for the observed canonical mapping.",
        "",
        "## Decision",
        "",
        "1. Resolve-condition verdict: **not met**. The task asked to resolve whether direct choice differed from flat dense ratings after auditing interleaved order agreement. The comparison exists, but Homosexuality order TV=0.833 with an argmax reversal, so the focal direct distribution is confounded by presentation order.",
        "2. Prediction check: recorded design predicted 12 valid choices per order and an auditable order-half comparison. Completeness is supported; order stability is contradicted for Homosexuality and supported for the other three items.",
        "3. Earliest unsupported link: a direct one-answer prompt measures a stable attitude-like choice distribution. The order-half control fails before any coordinate interpretation.",
        "4. Validity: define invalid as unsuitable for replacing rated coordinates or authorizing broad panel changes. P(invalid for that use) is highly likely, about 0.80. The result is a credible negative control for order stability, not an invalid ledger or billing record.",
        "5. Highest-information clues: (a) Homosexuality order TV 0.833, because it directly falsifies order invariance; (b) all 96 choices parsed with zero failures, separating mechanics from construct quality; (c) saved AI-persona reasoning, because it raises a semantic interpretation alternative.",
        "6. Missing metrics: independent canonical-choice reconstruction first; then a balanced-permutation repetition; then another model under the repaired protocol. These have higher information value than another full map panel.",
        "7. Bugs requiring code changes: none established. The next pilot should improve design, not silently change the current pilot.",
        "8. Misconceptions requiring reinterpretation: a schema-valid selected option is not evidence that the model expressed a personal WVS attitude. A flat dense rating is uniform after normalization, not a direct middle choice.",
        "9. What would change the verdict: low order-half TV under a balanced permutation schedule and no persona-language in saved reasoning would make direct-choice distributions more interpretable.",
        "10. Recommended sequence: preserve this pilot and pause the wider priority batch. Parent review should decide whether a balanced-permutation direct-choice replication is worth its bounded cost; do not combine a revised prompt and changed permutation schedule in one test.",
        "",
        "-- PI[gpt-5.6-terra]",
        "",
    ])
    OUT_MD.write_text("\n".join(lines))
    print(f"wrote {OUT_CSV}: {len(rows)} item rows")
    print(f"wrote {OUT_MD}: cost USD {cost:.7f}, 96/96 parsed, Homosexuality order TV {by_item['Homosexuality']['order_half_tv']:.3f}")


if __name__ == "__main__":
    main()
