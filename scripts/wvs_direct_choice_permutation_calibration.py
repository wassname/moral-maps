#!/usr/bin/env python3
"""Calibrate direct-choice half and direction total variation under exchangeability."""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import numpy as np

RUN_ID = "20260917T033051Z_3e9c3d54727e"
PROTOCOL_ID = "3e9c3d54727e46c92af49321604778d9bae85bd83a22e23e1793cbefd06f29e3"
LEDGER = Path("slop/research/wvs/20260917_direct_choice/gemini37_direct_choice_production_requests.jsonl")
SEED = 20260917
N_PERMUTATIONS = 100_000
OUT_CSV = Path("slop/audits/20260917_wvs_direct_choice_exchangeability_calibration.csv")
OUT_MD = Path("slop/audits/20260917_wvs_direct_choice_exchangeability_calibration.md")


def events(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines()]


def tv_from_slots(values: np.ndarray, slots_a: np.ndarray, slots_b: np.ndarray, n: int) -> np.ndarray:
    choices = np.arange(n)
    p_a = (values[:, slots_a, None] == choices).mean(axis=1)
    p_b = (values[:, slots_b, None] == choices).mean(axis=1)
    return 0.5 * np.abs(p_a - p_b).sum(axis=1)


def holm_adjust(p_values: list[float]) -> list[float]:
    adjusted = [0.0] * len(p_values)
    running = 0.0
    for rank, index in enumerate(sorted(range(len(p_values)), key=p_values.__getitem__)):
        running = max(running, min(1.0, p_values[index] * (len(p_values) - rank)))
        adjusted[index] = running
    return adjusted


def main() -> None:
    run_events = [event for event in events(LEDGER) if event.get("run_id") == RUN_ID]
    assert {event.get("protocol_id") for event in run_events} == {PROTOCOL_ID}
    parsed = [event for event in run_events if event["event"] == "answer_parsed"]
    assert len(parsed) == 240 and all(event["parsed"] for event in parsed)
    by_item: dict[str, list[dict]] = {}
    for event in parsed:
        by_item.setdefault(event["item_id"], []).append(event)

    rng = np.random.default_rng(SEED)
    max_tv = np.zeros(N_PERMUTATIONS)
    records = []
    for item_id, item_events in by_item.items():
        item_events = sorted(item_events, key=lambda event: event["sample"])
        assert [event["sample"] for event in item_events] == list(range(20))
        n = len(item_events[0]["presented_order"])
        values = np.array([event["canonical_choice"] for event in item_events], dtype=int)
        schedule_a = np.array([event["sample"] < 10 for event in item_events])
        direction_a = np.array([event["order_name"] == "canonical" for event in item_events])
        schedule_observed = float(tv_from_slots(values[None, :], schedule_a, ~schedule_a, n)[0])
        direction_observed = float(tv_from_slots(values[None, :], direction_a, ~direction_a, n)[0])
        permutations = rng.permuted(np.broadcast_to(values, (N_PERMUTATIONS, len(values))), axis=1)
        schedule_null = tv_from_slots(permutations, schedule_a, ~schedule_a, n)
        direction_null = tv_from_slots(permutations, direction_a, ~direction_a, n)
        max_tv = np.maximum(max_tv, np.maximum(schedule_null, direction_null))
        same_partition = bool(np.array_equal(schedule_a, direction_a))
        for label, observed, null in (
            ("schedule_half", schedule_observed, schedule_null),
            ("canonical_vs_reversed", direction_observed, direction_null),
        ):
            records.append({
                "item_id": item_id,
                "n_options": n,
                "comparison": label,
                "group_sizes": f"{int((schedule_a if label == 'schedule_half' else direction_a).sum())}/{int((~(schedule_a if label == 'schedule_half' else direction_a)).sum())}",
                "same_partition_as_other_comparison": same_partition,
                "observed_tv": observed,
                "null_mean_tv": float(null.mean()),
                "null_p95_tv": float(np.quantile(null, 0.95)),
                "null_p99_tv": float(np.quantile(null, 0.99)),
                "randomization_p": float((np.count_nonzero(null >= observed) + 1) / (N_PERMUTATIONS + 1)),
            })

    max_adjusted = [float((np.count_nonzero(max_tv >= row["observed_tv"]) + 1) / (N_PERMUTATIONS + 1)) for row in records]
    holm_adjusted = holm_adjust([row["randomization_p"] for row in records])
    for row, holm, max_t in zip(records, holm_adjusted, max_adjusted):
        row["holm_adjusted_p_24"] = holm
        row["maxT_adjusted_p_24"] = max_t
    records.sort(key=lambda row: (row["item_id"], row["comparison"]))

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)

    through = max(event["recorded_at_utc"] for event in run_events)
    lines = [
        "# Fixed-seed direct-choice exchangeability calibration",
        "",
        f"- target run: `{RUN_ID}`, protocol `{PROTOCOL_ID}`",
        f"- source ledger: `{LEDGER}` through {through}",
        f"- fixed NumPy PCG64 seed: {SEED}; {N_PERMUTATIONS:,} permutations per item",
        f"- machine table: `{OUT_CSV}`",
        "",
        "## Null and scope",
        "",
        "For each item, the observed 20 canonical choices are held fixed and randomly reassigned to its actual 20 schedule slots. This conditional exchangeability null tests whether the observed split TV is unusual given that item's own choice multiset. It does not test whether a choice distribution is human-like, whether samples are independent, or whether the prompt measures a WVS coordinate.",
        "",
        "The two reports are first-ten versus last-ten schedule halves and canonical versus reversed direction slots. For the two 10-option items the present schedule makes these partitions identical, so they are reported twice for transparency but do not distinguish direction from request time. For n=3/n=4, unequal direction counts are registered design constraints.",
        "",
        "## Results",
        "",
        "Randomization p is one-sided for TV at least the observed value. Holm and maxT values adjust across all 24 listed reports. They are calibration summaries, not validity thresholds or a claim of statistical significance.",
        "",
        "| item | n | comparison | groups | observed TV | null mean | null p95 | randomization p | Holm p (24) | maxT p (24) | note |",
        "|---|---:|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in records:
        note = "same partition as the other report" if row["same_partition_as_other_comparison"] else "distinct partition"
        lines.append(
            f"| {row['item_id']} | {row['n_options']} | {row['comparison']} | {row['group_sizes']} | "
            f"{row['observed_tv']:.3f} | {row['null_mean_tv']:.3f} | {row['null_p95_tv']:.3f} | "
            f"{row['randomization_p']:.4f} | {row['holm_adjusted_p_24']:.4f} | {row['maxT_adjusted_p_24']:.4f} | {note} |"
        )
    lines.extend([
        "",
        "## Interpretation limits",
        "",
        "With only 20 choices/item, discrete distributions and concentrated responses make this calibration low power for moderate instability. A high adjusted p can arise because the observed split is ordinary under the conditional null, because the item has little response variation, or because 20 samples cannot resolve the effect. A low p would only identify a split unusual under this narrow exchangeability null. Neither outcome is a hard construct-validity cutoff.",
        "",
        "The calibrated values therefore refine the prior descriptive half TVs. They do not authorize a direct-choice map, a protocol merge, or additional paid models. The next decision remains parent review of whether a differently interleaved replication is worth its cost.",
        "",
        "-- PI[gpt-5.6-terra]",
        "",
    ])
    OUT_MD.write_text("\n".join(lines))
    print(f"wrote {OUT_CSV}: {len(records)} exchangeability reports")
    print(f"wrote {OUT_MD}: seed={SEED}, permutations={N_PERMUTATIONS}")


if __name__ == "__main__":
    main()
