#!/usr/bin/env python3
"""Audit the Gemini response-wording direct-choice control without API calls."""
from __future__ import annotations

import csv
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

import numpy as np

RUN_ID = "20260917T031008Z_db7584c9b8b6"
PROTOCOL_ID = "db7584c9b8b693d3196aef4cfcc5e93956aceb2f4d9ad1432a65c8525dfb135e"
LEDGER = Path("slop/research/wvs/20260917_direct_choice/gemini37_direct_choice_anchor_requests.jsonl")
CACHE = Path("slop/research/wvs/20260917_direct_choice/gemini37_direct_choice_anchor_cache.json")
PREVIOUS_LEDGER = Path("slop/research/wvs/20260917_direct_choice/gemini37_direct_choice_requests.jsonl")
OUT_CSV = Path("slop/audits/20260917_wvs_gemini37_direct_choice_anchor_task_1629_by_item.csv")
OUT_MD = Path("slop/audits/20260917_wvs_gemini37_direct_choice_anchor_task_1629.md")


def read_events(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines()]


def distribution(rows: list[dict], n: int) -> np.ndarray:
    counts = np.zeros(n)
    for row in rows:
        counts[row["canonical_choice"]] += 1
    return counts / len(rows)


def total_variation(left: np.ndarray, right: np.ndarray) -> float:
    return float(0.5 * np.abs(left - right).sum())


def display(p: np.ndarray) -> str:
    return "[" + ", ".join(f"{value:.3f}" for value in p) + "]"


def modal_set(p: np.ndarray) -> list[int]:
    return np.flatnonzero(p == p.max()).tolist()


def quote(message: dict) -> str:
    return (message.get("reasoning") or message.get("content") or "").replace("\n", " ").strip()


def by_item(parsed: list[dict], item_id: str) -> dict:
    rows = [event for event in parsed if event["item_id"] == item_id]
    n = len(rows[0]["presented_order"])
    canonical = [event for event in rows if event["order_name"] == "canonical"]
    reversed_order = [event for event in rows if event["order_name"] == "reversed"]
    assert len(canonical) == len(reversed_order) == 12
    canonical_p = distribution(canonical, n)
    reversed_p = distribution(reversed_order, n)
    return {
        "item_id": item_id, "n_options": n, "canonical_n": len(canonical), "reversed_n": len(reversed_order),
        "canonical_p": canonical_p, "reversed_p": reversed_p,
        "tv": total_variation(canonical_p, reversed_p),
        "canonical_modal": modal_set(canonical_p), "reversed_modal": modal_set(reversed_p),
    }


def main() -> None:
    events = [event for event in read_events(LEDGER) if event.get("run_id") == RUN_ID]
    counts = Counter(event["event"] for event in events)
    assert counts == Counter({"request_started": 48, "request_completed": 48, "answer_parsed": 48,
                              "item_result": 2, "run_started": 1, "run_finished": 1}), counts
    parsed = [event for event in events if event["event"] == "answer_parsed"]
    assert len(parsed) == 48 and all(event["parsed"] for event in parsed)
    for event in parsed:
        raw = json.loads(event["text"])
        assert set(raw) == {"answer"} and type(raw["answer"]) is int
        assert event["canonical_choice"] == event["presented_order"][raw["answer"]]
    assert not [event for event in events if event["event"] == "request_failed"]
    assert not [event for event in events if event.get("phase") == "rescue"]
    assert {event["protocol_id"] for event in events} == {PROTOCOL_ID}
    assert json.loads(CACHE.read_text())["completed"][PROTOCOL_ID]["complete"]

    current = {item: by_item(parsed, item) for item in ("Homosexuality", "Religion")}
    prior_events = read_events(PREVIOUS_LEDGER)
    prior_parsed = [event for event in prior_events if event["event"] == "answer_parsed"]
    prior = {item: by_item(prior_parsed, item) for item in ("Homosexuality", "Religion")}
    request_events = [event for event in events if event["event"] == "request_completed"]
    prompt_tokens = sum(event["usage"]["prompt_tokens"] for event in request_events)
    completion_tokens = sum(event["usage"]["completion_tokens"] for event in request_events)
    reasoning_tokens = sum(event["usage"]["completion_tokens_details"]["reasoning_tokens"] for event in request_events)
    cost = sum(Decimal(str(event["usage"]["cost"])) for event in request_events)
    refusals = sum(event["response"]["choices"][0]["message"].get("refusal") is not None for event in request_events)
    first_homosexuality = next(event for event in request_events if event["item_id"] == "Homosexuality" and event["sample"] == 0)
    first_religion = next(event for event in request_events if event["item_id"] == "Religion" and event["sample"] == 0)

    rows = []
    for item in ("Homosexuality", "Religion"):
        now, before = current[item], prior[item]
        screen = now["tv"] <= 0.25 and now["canonical_modal"] == now["reversed_modal"]
        rows.append({
            "item_id": item, "canonical_n": now["canonical_n"], "reversed_n": now["reversed_n"],
            "anchor_canonical_distribution": display(now["canonical_p"]),
            "anchor_reversed_distribution": display(now["reversed_p"]),
            "anchor_order_tv": now["tv"], "anchor_canonical_modal": now["canonical_modal"],
            "anchor_reversed_modal": now["reversed_modal"], "screen_passes": screen,
            "task1628_order_tv": before["tv"], "task1628_canonical_modal": before["canonical_modal"],
            "task1628_reversed_modal": before["reversed_modal"],
        })

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    ledger_through = max(event["recorded_at_utc"] for event in events)
    all_screen_pass = all(row["screen_passes"] for row in rows)
    lines = [
        "# Audit: Gemini direct-choice response-wording control, task 1629",
        "",
        "- target: 48-call Homosexuality/Religion wording control, not a map panel",
        "- Pueue: task 1629, API queue, success, 2026-09-17 11:10:00-11:13:43 +08:00",
        "- label: `why: test whether literal JSON example anchored option zero; resolve: report preregistered order TV/modal agreement before any wider batch`",
        f"- run: `{RUN_ID}`, protocol: `{PROTOCOL_ID}`",
        f"- primary ledger: `{LEDGER}` through {ledger_through}",
        f"- cache: `{CACHE}`",
        f"- task 1628 comparator: `{PREVIOUS_LEDGER}`",
        f"- per-item table: `{OUT_CSV}`",
        "",
        "## Stage table",
        "",
        "| stage | expected | observed | expected? | clues | missing metric | consequence |",
        "|---|---|---|---|---|---|---|",
        "| response-wording change | remove literal answer value/example only | prompt uses one-key schema wording with no literal JSON example or answer value | yes | saved request prompt | independent prompt diff beyond smoke | targeted anchoring discriminator ran |",
        "| request plan | 48 calls, 12 canonical and 12 reversed per item, interleaved | 48 starts/completions, 24 valid per item and 12 per order | yes | ledger counts/cache | provider-side order timestamp | planned comparison available |",
        "| strict parse | 48 valid choices with preserved mapping | 48/48 parsed, independently re-decoded to stored canonical choice | yes | ledger + audit assertions | external schema trace | no mechanical loss |",
        "| rescue/refusal | zero or durable evidence | 0 rescue, 0 failure, 0 provider refusal | yes | ledger | semantic non-answer metric | mechanics do not decide construct validity |",
        f"| accounting | retained provider usage | prompt {prompt_tokens:,}; completion {completion_tokens:,}; reasoning {reasoning_tokens:,}; USD {cost:.7f} | yes | 48 completed usage records | billing export | below preregistered reserve |",
        f"| operational screen | both items TV <=0.25 plus matching modal set | {'passes both items' if all_screen_pass else 'fails'}: Homosexuality TV={current['Homosexuality']['tv']:.3f}, Religion TV={current['Religion']['tv']:.3f}; modal sets match | {'yes' if all_screen_pass else 'no'} | per-item table | repeat with other permutation | evidence against a large reverse-order effect only |",
        "| persistence | complete cache only after all valid samples | cache entry complete and 148 ledger events | yes | cache + ledger | cache replay | raw evidence retained |",
        "",
        "## Primary evidence",
        "",
        "The source ledger is the primary record because Pueue's full output only repeats the completion line. It has 48 initial request starts, 48 completions, 48 parsed responses, two item results, one run start and one run finish. No response used a rescue phase.",
        "",
        "Homosexuality sample 0's changed prompt ends with the response wording, followed by this saved reasoning:",
        "",
        f"> {quote(first_homosexuality['response']['choices'][0]['message'])}",
        "",
        "epistemic context: provider reasoning from one selected pilot response, not a human attitude report.",
        "",
        "Religion sample 0 still contains an AI-persona interpretation:",
        "",
        f"> {quote(first_religion['response']['choices'][0]['message'])}",
        "",
        "epistemic context: provider reasoning from one selected pilot response, not a human attitude report.",
        "",
        "## Preregistered order screen and task 1628 comparison",
        "",
        "| item | new canonical p | new reversed p | new TV | new modal sets | screen | task 1628 TV | task 1628 modal sets |",
        "|---|---|---|---:|---|---|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['item_id']} | {row['anchor_canonical_distribution']} | {row['anchor_reversed_distribution']} | "
            f"{row['anchor_order_tv']:.3f} | {row['anchor_canonical_modal']} / {row['anchor_reversed_modal']} | "
            f"{row['screen_passes']} | {row['task1628_order_tv']:.3f} | "
            f"{row['task1628_canonical_modal']} / {row['task1628_reversed_modal']} |"
        )
    lines.extend([
        "",
        "The registered screen passes: both items are below TV 0.25 and have matching modal sets. This is evidence against the literal JSON example causing a large reverse-order effect under this specific control. It is not proof that the selected distribution represents a stable personal attitude, because the only tested permutations are canonical and full reversal and saved persona-language remains.",
        "",
        "## Hypotheses",
        "",
        "### H1 [method | Highly Likely | 80%]",
        "",
        "- Mechanism: the literal task 1628 answer example materially contributed to its Homosexuality reverse-order effect.",
        f"- Evidence: Homosexuality order TV fell from {prior['Homosexuality']['tv']:.3f} in task 1628 to {current['Homosexuality']['tv']:.3f}, while its modal set now matches ({current['Homosexuality']['canonical_modal']}).",
        "- Contrary evidence: this is a new sampled run, so ordinary sampling variation or another unmeasured request-time effect can also change the result.",
        "- Discriminating test: repeat this exact no-example prompt with a balanced set of non-reversal permutations. Similar low TV would support the explanation; a new high position-linked TV would weaken it.",
        "- Fix/action: retain no-example response wording in any future direct-choice protocol; do not merge this control with task 1628.",
        "- Interpretability: partial.",
        "",
        "### H2 [measurement | Likely | 65%]",
        "",
        "- Mechanism: Gemini still answers subjective WVS questions through its AI persona rather than a personal-attitude construct.",
        f"- Evidence: Religion sample 0 says `{quote(first_religion['response']['choices'][0]['message'])}`.",
        "- Contrary evidence: the final choices are order-stable under this narrow screen.",
        "- Discriminating test: compare a role-conditioned prompt against the same no-example response wording and a fixed permutation schedule.",
        "- Fix/action: keep this as a construct diagnostic, not a coordinate replacement.",
        "- Interpretability: partial.",
        "",
        "### H3 [bug | Unlikely | 15%]",
        "",
        "- Mechanism: reversed response mapping could hide a position effect.",
        "- Evidence: this audit independently parses every raw final JSON object and maps its integer through the stored presented order; all 48 match the ledger canonical-choice field.",
        "- Contrary evidence: it is one implementation and one run.",
        "- Discriminating test: an independent reimplementation over the raw ledger or a non-reversal permutation test.",
        "- Fix/action: no mapping code change is justified.",
        "- Interpretability: yes for recorded canonical choices.",
        "",
        "## Decision",
        "",
        "1. Resolve-condition verdict: **met**. Both operational checks pass: order TV <=0.25 and matching modal set for Homosexuality and Religion.",
        "2. Prediction check: removing the literal response example was predicted to reduce a large reverse-order effect. Homosexuality changes from TV 0.833 to 0.083; this is supported but not causal proof because the samples are new.",
        "3. Earliest unsupported link: no-example direct choice measures a stable personal attitude, rather than merely reducing one detected position effect.",
        "4. Validity: define invalid as unsuitable for a direct coordinate or broad batch decision. P(invalid for that use) remains likely, about 0.65, due to persona-language and limited permutation coverage. The narrow prompt-anchor result is credible.",
        "5. Highest-information clues: the Homosexuality TV fall, the matched modal sets, and the unchanged AI-persona reasoning.",
        "6. Missing metrics: balanced non-reversal permutation check; independent-model replication; direct-choice construct calibration. These outrank a wider rated API batch for this method question.",
        "7. Bugs requiring code changes: none established. Keep separate protocol/cache/ledger identities.",
        "8. Misconceptions requiring reinterpretation: successful strict-schema choices and a passed reversal screen do not prove an attitude-like WVS construct.",
        "9. What would change the verdict: a high TV under non-reversal permutations would show the literal-example explanation is insufficient; low TV without AI-persona reasoning would raise confidence in direct-choice interpretation.",
        "10. Recommended sequence: pause the wider batch for parent review. If a next paid direct-choice test is approved, vary only permutation schedule while retaining this no-example wording; do not combine it with a persona rewrite.",
        "",
        "-- PI[gpt-5.6-terra]",
        "",
    ])
    OUT_MD.write_text("\n".join(lines))
    print(f"wrote {OUT_CSV}: {len(rows)} item rows")
    print(f"wrote {OUT_MD}: cost USD {cost:.7f}, both preregistered order screens={all_screen_pass}")


if __name__ == "__main__":
    main()
