# Audit: DeepSeek score-all-options reliability pilot continuation, task 1679

- target: Pueue task 1679, `sh scripts/wvs_api/07_deepseek_reliability_pilot.sh`, 2026-09-17 22:39:02 to 2026-09-18 01:21:01 +0800, exit success.
- method: separate `wvs-score-all-options-v1` replicate records, three panels of 12 items x 24 samples per model. The canonical N=12 cache and Pages data were not written.
- primary evidence: full normalized Pueue log 398/398 lines and raw log 470 lines in `/tmp/wvs-audit-1679/`; raw request records and summary are under `slop/research/wvs/20260917_deepseek_reliability/`.

| stage | expected | observed | expected? | clues | consequence |
|---|---|---|---|---|---|
| durable resume | retain 1674 records, make no duplicate calls | chat-v3-0324 retains 288, 288, 287 valid samples | yes | protocol IDs and run IDs from 1674 remain in `results.json` | incomplete model excluded from aggregate |
| per-model continuation | one incomplete replicate does not stop later models | six later models were run; five have 3 x 288/288 | yes | 1679 log spans v3.1 through v4.1; final summary | five N=72 aggregates available |
| parse/rescue | 24 valid samples/item per complete replicate | 19 complete replicates have 288 valid, 0 failed, 0 rescues | yes | every complete `run_finished` record | structural validity only, not semantic quality |
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

Initial replies also contain all-equal rating vectors, which parse successfully but discard the requested option-level distinction:

| model | all-equal initial vectors / initial responses |
|---|---:|
| chat-v3-0324 | 27 / 863 (3.1%) |
| chat-v3.1 | 50 / 863 (5.8%) |
| v3.2 | 28 / 864 (3.2%) |
| v3.2-exp | 37 / 864 (4.3%) |
| v4-flash | 90 / 864 (10.4%) |
| v4-flash-0731 | 66 / 864 (7.6%) |
| v4.1-flash | 132 / 864 (15.3%) |

These are concentrated rather than uniform noise. For v4.1-flash, 28/72 `God`, 24/72 `dealing with people?`, and 23/72 `Joining in boycotts` initial responses are all-equal. More samples reduce response-mean uncertainty but cannot remove a recurring response style from the score-all-options measurement.

## Replication summary

| model | usable replicates | within-pilot SD, X/Y | mean response-only SE, X/Y | v1 delta, X/Y (confounded) | cost |
|---|---:|---:|---:|---:|---:|
| deepseek-v3.2 | 3/3 | 0.0097, 0.0118 | 0.0087, 0.0109 | +0.0180, +0.0381 | USD 0.04568444 |
| deepseek-v3.2-exp | 3/3 | 0.0089, 0.0147 | 0.0079, 0.0091 | -0.0039, -0.0351 | USD 0.09620404 |
| deepseek-v4-flash | 3/3 | 0.0044, 0.0158 | 0.0067, 0.0107 | +0.0030, -0.0004 | USD 0.02237091 |
| deepseek-v4-flash-0731 | 3/3 | 0.0169, 0.0030 | 0.0070, 0.0097 | +0.0096, +0.0146 | USD 0.01315660 |
| deepseek-v4.1-flash | 3/3 | 0.0082, 0.0062 | 0.0060, 0.0100 | +0.0048, +0.0225 | USD 0.05818026 |
| deepseek-chat-v3-0324 | 2/3, one 287/288 | -- | -- | not computed | USD 0.04716160 |
| deepseek-chat-v3.1 | 2/3, one 287/288 | -- | -- | not computed | USD 0.08192587 |

The clean quantity is the within-pilot repeatability under this fallback policy: median SD X=0.00888, Y=0.01176. The median N=24 response-only SE is approximately X=0.00719, Y=0.00968; the corresponding N=12 approximation is X=0.01017, Y=0.01369. Item-set uncertainty is larger and remains separate.

Canonical v1 and pilot routing differ materially, so aggregate-minus-v1 is not interpretable as an N/seed effect:

| model | canonical v1 actual provider counts | pilot actual provider counts |
|---|---|---|
| chat-v3-0324 | SiliconFlow 140, GMICloud 4 | GMICloud 863 |
| chat-v3.1 | Novita 61, CoreWeave 83 | Novita 759, CoreWeave 104 |
| v3.2 | StreamLake 143, SiliconFlow 1 | AtlasCloud 864 |
| v3.2-exp | SiliconFlow 134, AtlasCloud 10 | AtlasCloud 861, Novita 3 |
| v4-flash | StreamLake 139, DeepInfra 5 | Alibaba 851, DeepInfra 11, Parasail 2 |
| v4-flash-0731 | DeepInfra 144 | DeepInfra 822, Morph 15, NextBit 8, Parasail 19 |
| v4.1-flash | provider not recorded in v1 response records (144) | Parasail 695, DeepInfra 155, AtlasCloud 13, Morph 1 |

Coordinates use the existing X and Y WVS axes. The v1 deltas remain recorded for provenance but make no N/seed or model-drift claim, and no pilot coordinate is used in the public map.

## ML-debug form, adapted to this API measurement run

| row | answer |
|---|---|
| log/config | full 398-line task log; fixed v1 prompt, order balancing, temperature, structured output, lowest v1 reasoning setting, OSS provider policy; unique saved seeds per initial request |
| null/baseline | canonical v1 coordinate is the comparison; no random/shuffled WVS control was run |
| complete input/output | every first-item trace contains the prompt and two bare JSON replies; all raw responses are retained by replicate |
| worst row | two 287/288 runs each fail at a single empty-message `ReadTimeout`; all other requested scores in those panels parsed |
| metric limitation | response-mean SE estimates resampling of N=24 response means; item heterogeneity, fallback routing, and recurring all-equal vectors can still move coordinates |
| missing evidence | endpoint seed adherence is advertised, not verified; OpenRouter does not expose quantization; no held-out prompt wording or independent provider-locked control |
| wall time | 9,716 seconds for continuation; one request at a time per replicate was intentional |

## Hypotheses

### H1 [measurement | Likely | 70%]

- **Mechanism:** five models have usable repeatability estimates under the current fallback policy, but only within that policy.
- **Evidence:** the median within-pilot SD is X=0.00888 and Y=0.01176 across five complete three-replicate panels; all 15 component panels have 288/288 valid responses.
- **Contrary evidence:** three replicates per model are too few to establish tails or separate all sources of variation.
- **Discriminating test:** a preregistered provider-locked replication would separate provider routing from the remaining response/seed variation. It must not replace v1 coordinates.
- **Fix/action:** retain the five within-pilot summaries as reliability evidence; do not use their aggregate coordinates to overwrite v1 or publish them.
- **Interpretability:** partial, for within-pilot repeatability only.

### H2 [harness | Almost Certain | 95%]

- **Mechanism:** v1-to-pilot coordinate deltas confound N/seeds with changed actual provider routing.
- **Evidence:** v3.2 changed from StreamLake 143/SiliconFlow 1 to AtlasCloud 864; v3.2-exp changed from SiliconFlow 134/AtlasCloud 10 to AtlasCloud 861/Novita 3; v4-flash changed from StreamLake 139/DeepInfra 5 to Alibaba 851 plus fallback providers.
- **Contrary evidence:** none of these comparisons isolates identical routing, so they do not identify which source drove each delta.
- **Discriminating test:** provider-locked matched v1/replicate panels. Equal routing with a persistent delta would support an N/seed contribution.
- **Fix/action:** label every v1 delta confounded and do not interpret it as a replication shift.
- **Interpretability:** no, for v1-minus-pilot causal attribution.

### H3 [measurement | Almost Certain | 90%]

- **Mechanism:** parse-valid all-equal score vectors are a recurring score-all-options response style, so more N cannot remove that systematic component.
- **Evidence:** all-equal initial vector rates range from 3.1% (chat-v3-0324) to 15.3% (v4.1-flash); v4.1-flash has 28/72 on God, 24/72 on dealing-with-people, and 23/72 on boycotts.
- **Contrary evidence:** the audit has not established whether this style is a model preference, an endpoint/provider behavior, or a prompt interaction.
- **Discriminating test:** a planned prompt-format control with fixed provider and the same score-all-options evaluator. A lower all-equal rate would locate a prompt contribution.
- **Fix/action:** treat parser success as structural validity only; do not spend remaining reliability authorization on more N before a design decision.
- **Interpretability:** partial, for the observed response-style rate.

### H4 [harness | Highly Likely | 80%]

- **Mechanism:** the two incomplete panels are likely network/transport failures, not evidence of a score-all-options parsing incompatibility.
- **Evidence:** each failure is explicitly `ReadTimeout`, while their other 575 and 575 requests respectively have parse-valid results; both affected models have two full replicates.
- **Contrary evidence:** the timeout lacks a provider receipt, so a failed upstream generation cannot be excluded.
- **Discriminating test:** an owner-approved replacement replicate with a separately recorded schedule. It must remain separate from the original incomplete schedule.
- **Fix/action:** leave both model aggregates excluded now; do not silently fill the missing samples.
- **Interpretability:** no N=72 coordinate for these two models.

### H5 [harness | Almost Certain | 95%]

- **Mechanism:** earlier pilot accounting omitted a failed replicate's USD 0.01567156 because it only incremented state after a complete replicate returned.
- **Evidence:** task 1674 recorded three costs summing USD 0.04716160 while its state held USD 0.03149004. Task 1679 reconciled all `request_completed` records to USD 0.364683724004.
- **Contrary evidence:** reservations were released even before the correction, so the defect did not strand the USD 1 reservation.
- **Discriminating test:** no-network recomputation from all pilot JSONL records must reproduce the settled amount.
- **Fix/action:** pilot settlement now records external observed spend atomically with reservation release; future starts remove stale `finished_utc`.
- **Interpretability:** yes for recorded raw cost after reconciliation.

## Decision

- **Resolve-condition verdict:** partially met. Five of seven models produced usable within-pilot N=72 reliability estimates; two models remain correctly excluded after one timeout each. The continuation requirement was met: those two did not stop later models.
- **Validity:** define invalid as an aggregate containing fewer than 72 responses/item, pilot values overwriting v1, or cost exceeding USD 1. P(invalid published-impact result) is Remote because no pilot value is public. P(the five within-pilot summaries miss important routing/prompt effects) is Likely because fallback routing is deliberately allowed, all-equal response styles recur, and there are only three replicates. No external review evidence exists: an attempted independent Anthropic fresh-eye launch failed with `credits_required`.
- **Recommended sequence:** do not spend the remaining reliability authorization on more N yet. Preserve raw records and current exclusions; do not queue retries or map changes from this pilot without review. Proceed with the canonical-only Pages refresh, using independently complete score-all-options v1 panels and never these replicate aggregates.

-- PI[k3]
