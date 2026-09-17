# Audit: DeepSeek score-all-options reliability pilot continuation, task 1679

- target: Pueue task 1679, `sh scripts/wvs_api/07_deepseek_reliability_pilot.sh`, 2026-09-17 22:39:02 to 2026-09-18 01:21:01 +0800, exit success.
- method: separate `wvs-score-all-options-v1` replicate records, three panels of 12 items x 24 samples per model. The canonical N=12 cache and Pages data were not written.
- primary evidence: full normalized Pueue log 398/398 lines and raw log 470 lines in `/tmp/wvs-audit-1679/`; raw request records and summary are under `slop/research/wvs/20260917_deepseek_reliability/`.

| stage | expected | observed | expected? | clues | consequence |
|---|---|---|---|---|---|
| durable resume | retain 1674 records, make no duplicate calls | chat-v3-0324 retains 288, 288, 287 valid samples | yes | protocol IDs and run IDs from 1674 remain in `results.json` | incomplete model excluded from aggregate |
| per-model continuation | one incomplete replicate does not stop later models | six later models were run; five have 3 x 288/288 | yes | 1679 log spans v3.1 through v4.1; final summary | five N=72 aggregates available |
| parse/rescue | 24 valid samples/item per complete replicate | 19 complete replicates have 288 valid, 0 failed, 0 rescues | yes | every complete `run_finished` record | parser compatibility is high for those panels |
| incomplete panels | retain, do not estimate aggregate | chat-v3-0324 replicate 2 and chat-v3.1 replicate 1 each have 287/288 after one `ReadTimeout` | yes | raw records, results statuses | two models have no N=72 coordinate |
| cost/cap | total below USD 1 pilot cap and repository cap remains reconciled | USD 0.364683724004 raw-record cost, reserve released; global observed USD 9.504989444306 | yes | pilot/global budgets after settlement | no active reservation |
| publication isolation | no pilot coordinates used in canonical cache/Page | `not_published: true`; no cache write in pilot code | yes | `results.json`, pilot code | no reliability point is public |

## Observations

The continuation preserved the earlier failed replicate rather than rerunning it. Its ledger record is:

> `"event": "request_failed", "item_id": "Attending peaceful demonstrations", "sample": 10, "phase": "initial", "error_type": "ReadTimeout", "error": ""`
>
> `"event": "run_finished", "failed_samples": 1, "planned_requests": 288, "rescued_samples": 0, "valid_samples": 287`

The later analogous failure is also transport-labelled:

> `"event": "request_failed", "item_id": "Abortion", "sample": 18, "phase": "initial", "error_type": "ReadTimeout", "error": ""`
>
> `"event": "run_finished", "failed_samples": 1, "planned_requests": 288, "rescued_samples": 0, "valid_samples": 287`

A complete replicate records the requested scale:

> `"event": "run_finished", "failed_samples": 0, "model": "deepseek/deepseek-v3.2", "planned_requests": 288, "rescued_samples": 0, "valid_samples": 288`

The log's operational expectation was met for complete panels:

> `SHOULD: replies are a bare JSON dict of 1-5 ratings; valid rate near 1.0 -> coherent. ELSE the record shows malformed output, rescue, or request failure.`
>
> `... valid=24/24`

This establishes parse-valid score-all-options replies, not that the returned scores measure a stable model property.

## Replication summary

| model | usable replicates | aggregate delta from v1, X/Y | between-replicate SD, X/Y | mean response-only SE, X/Y | cost |
|---|---:|---:|---:|---:|---:|
| deepseek-v3.2 | 3/3 | +0.0180, +0.0381 | 0.0097, 0.0118 | 0.0087, 0.0109 | USD 0.04568444 |
| deepseek-v3.2-exp | 3/3 | -0.0039, -0.0351 | 0.0089, 0.0147 | 0.0079, 0.0091 | USD 0.09620404 |
| deepseek-v4-flash | 3/3 | +0.0030, -0.0004 | 0.0044, 0.0158 | 0.0067, 0.0107 | USD 0.02237091 |
| deepseek-v4-flash-0731 | 3/3 | +0.0096, +0.0146 | 0.0169, 0.0030 | 0.0070, 0.0097 | USD 0.01315660 |
| deepseek-v4.1-flash | 3/3 | +0.0048, +0.0225 | 0.0082, 0.0062 | 0.0060, 0.0100 | USD 0.05818026 |
| deepseek-chat-v3-0324 | 2/3, one 287/288 | not computed | -- | -- | USD 0.04716160 |
| deepseek-chat-v3.1 | 2/3, one 287/288 | not computed | -- | -- | USD 0.08192587 |

Coordinates use the existing X and Y WVS axes. The reported aggregate delta is descriptive: it is not a test that the v1 and replicate distributions agree, and it is not used in the public map.

## ML-debug form, adapted to this API measurement run

| row | answer |
|---|---|
| log/config | full 398-line task log; fixed v1 prompt, order balancing, temperature, structured output, lowest v1 reasoning setting, OSS provider policy; unique saved seeds per initial request |
| null/baseline | canonical v1 coordinate is the comparison; no random/shuffled WVS control was run |
| complete input/output | every first-item trace contains the prompt and two bare JSON replies; all raw responses are retained by replicate |
| worst row | two 287/288 runs each fail at a single empty-message `ReadTimeout`; all other requested scores in those panels parsed |
| metric limitation | response-mean SE estimates resampling of N=24 response means; item heterogeneity and provider routing can still move coordinates |
| missing evidence | endpoint seed adherence is advertised, not verified; OpenRouter does not expose quantization; no held-out prompt wording or independent provider-locked control |
| wall time | 9,716 seconds for continuation; one request at a time per replicate was intentional |

## Hypotheses

### H1 [measurement | Likely | 70%]

- **Mechanism:** response variation is material relative to some canonical-v1 deltas, especially on Y, so a single N=12 panel can move noticeably under the same evaluation protocol.
- **Evidence:** v3.2 has Y delta `+0.0381` and between-replicate Y SD `0.0118`; v3.2-exp has `-0.0351` and SD `0.0147`; v4.1-flash has `+0.0225` and SD `0.0062` in `results.json`.
- **Contrary evidence:** v4-flash has Y delta `-0.0004`, and the pilot has only three replicates per completed model.
- **Discriminating test:** a preregistered provider-locked replication would distinguish sampling/routing variation from seed-controlled model variation. It must not replace v1 coordinates.
- **Fix/action:** retain this as a reliability warning; do not use these aggregate coordinates to overwrite v1 or publish them.
- **Interpretability:** partial, for these five models' within-protocol repeatability only.

### H2 [harness | Likely | 65%]

- **Mechanism:** fallback routing is a plausible part of replicate variation because several completed panels used more than one provider.
- **Evidence:** v4.1-flash used AtlasCloud, DeepInfra, Morph, and Parasail; v4-flash-0731 used DeepInfra, Morph, NextBit, and Parasail. The policy intentionally permits this routing.
- **Contrary evidence:** v3.2 stayed on AtlasCloud across all 864 completed requests but still has nonzero replicate SD.
- **Discriminating test:** compare a future provider-locked control to the same multi-provider policy. A lower SD under one provider would support routing contribution.
- **Fix/action:** retain actual provider counts in every run; do not attribute all variation to provider routing.
- **Interpretability:** partial.

### H3 [harness | Highly Likely | 80%]

- **Mechanism:** the two incomplete panels are likely network/transport failures, not evidence of a score-all-options parsing incompatibility.
- **Evidence:** each failure is explicitly `ReadTimeout`, while their other 575 and 575 requests respectively have parse-valid results; both affected models have two full replicates.
- **Contrary evidence:** the timeout lacks a provider receipt, so a failed upstream generation cannot be excluded.
- **Discriminating test:** an owner-approved replacement replicate with a separately recorded schedule. It must remain separate from the original incomplete schedule.
- **Fix/action:** leave both model aggregates excluded now; do not silently fill the missing samples.
- **Interpretability:** no N=72 coordinate for these two models.

### H4 [harness | Almost Certain | 95%]

- **Mechanism:** earlier pilot accounting omitted a failed replicate's USD 0.01567156 because it only incremented state after a complete replicate returned.
- **Evidence:** task 1674 recorded three costs summing USD 0.04716160 while its state held USD 0.03149004. Task 1679 reconciled all `request_completed` records to USD 0.364683724004.
- **Contrary evidence:** reservations were released even before the correction, so the defect did not strand the USD 1 reservation.
- **Discriminating test:** no-network recomputation from all pilot JSONL records must reproduce the settled amount.
- **Fix/action:** pilot settlement now records external observed spend atomically with reservation release; future starts remove stale `finished_utc`.
- **Interpretability:** yes for recorded raw cost after reconciliation.

## Decision

- **Resolve-condition verdict:** partially met. Five of seven models produced three complete N=24 replicate panels and N=72 aggregates; two models remain correctly excluded after one timeout each. The continuation requirement was met: those two did not stop later models.
- **Validity:** define invalid as an aggregate containing fewer than 72 responses/item, pilot values overwriting v1, or cost exceeding USD 1. P(invalid published-impact result) is Remote because no pilot value is public. P(the five reliability summaries miss important routing/prompt effects) is Likely because fallback routing is deliberately allowed and there are only three replicates.
- **Recommended sequence:** preserve raw records and current exclusions; do not queue retries or map changes from this pilot without review. The next canonical Pages refresh may use only independently complete score-all-options v1 panels, never these replicate aggregates.

-- PI[k3]
