# Audit: Pueue job 1698, Gemini Flash reasoning and rubric pilot

## Target and provenance

Pueue task 1698 ran `scripts/wvs_api/08_gemini_flash_rubric_pilot.sh` in `/workspace/2026/lite/moralmaps` from 2026-09-18 19:50:09 to 21:38:45 +0800 and exited `Success`. The queued label was:

> why: estimate Gemini Flash WVS sensitivity to reasoning and reversed rubric under one fixed protocol; resolve: audit all 20 cells for completion, route, rescue, cost, and paired shifts before interpretation

The complete cleaned Pueue log was read as `[pq] task 1698: last 444 of 444 clean lines`. The raw Pueue log was also saved and read, 524 lines. The executing branch began at `d64b788e56400ac52755d03fe81ef4ae06250101`; the durable result does not record a Git revision, so the exact runtime revision is likely but not provable from the artifact alone.

The primary raw data are the 20 JSONL files under `slop/research/wvs/20260918_gemini_flash_rubric_pilot/records/`; each preserves requests, full provider responses, parsed answers, per-item distributions, and a `run_finished` event. I programmatically checked all raw event records, then recomputed coordinates from every stored `item_result.p_samples` using `wvs_map.model_coord_ci` and the saved 12 WVS items. The runner is `scripts/wvs_gemini_flash_rubric_pilot.py`; the request and transform implementation is `src/moralmaps/read_api.py:302-499`.

## Stage table

| stage | expected | observed | expected? | clues | missing metric | consequence |
| --- | --- | --- | --- | --- | --- | --- |
| manifest and protocol | 5 models, 4 cells, 12 items, N=6, fixed 2048 completion limit | 1,440 planned initial requests; provider lock and separate reverse cells persisted | yes | `manifest.json` | endpoint behavior over time | design is recoverable |
| Google routing | one selected Google AI Studio endpoint per paid response | all panel responses passed route validation; exact dated release slugs saved | yes | `request_attempts.jsonl`, runner lines 115-149 | historical endpoint state beyond snapshot | no detected fallback |
| response and parse | 72 valid ratings per cell | all 20 cells completed 72/72, 1,440/1,440 parsed; 4 rescues | yes | every cell `run_finished`; `results.json` | independent re-run | valid JSON is not enough to establish construct validity |
| cost and reservations | stop below USD 20 and settle ledger | USD 3.20884450 conservative, zero held reservations | yes | both budget JSON files | whether timeout requests were provider-billed | accounting reconciles under the conservative rule |
| reasoning manipulation | minimum versus high request payloads produce different exposed token use | high cells had 44,239 to 111,138 reasoning tokens per cell; some low cells also reasoned | partial | raw `usage` and settings | hidden reasoning text for most responses | treatment was sent, but minimum is not uniform across releases |
| reverse-rubric manipulation | raw reversed ratings transformed by `6 - rating`, kept separate | source applies transform, all raw and transformed vectors retained; `not_published=true` | yes | `src/moralmaps/read_api.py:463-469`, manifest | alternative wording reversals | no accidental merge into primary map |
| resolve condition | audit completion, routing, rescue, cost, and paired shifts before interpretation | this audit supplies all requested fields | met | sections below | temporal control | results remain pilot-only |

## Primary evidence

### Completion, parsing, rescue, and accounting

`budget.json` is the durable local accounting state after the job:

> {
>   "completed_phases": 1447,
>   "completed_phases_without_provider_cost": 0,
>   "conservative_spent_usd": "3.20884450",
>   "failed_phases_charged_at_bound": 2,
>   "finished_utc": "2026-09-18T13:38:36.534826+00:00",
>   "hard_cap_usd": "20",
>   "provider_reported_spent_usd": "3.19041250",
>   "reserved_usd": "0E-8"
> }

Epistemic context: this is the runner's local file-lock-protected ledger. It establishes the runner's accounting behavior, not independent provider billing.

For every cell, the raw `run_finished` event reports 72 valid and zero failed samples. For example, the last cell says:

> {"event": "run_finished", "failed_samples": 0, "model": "google/gemini-3.8-flash", "planned_requests": 72, "protocol_id": "2bf10e1d6fd2a0dc7aef8538423b966f3293ad2b881234f8c71e87b696849208", "recorded_at_utc": "2026-09-18T13:38:35.515787+00:00", "rescued_samples": 3, "run_id": "20260918T132854Z_2bf10e1d6fd2", "valid_samples": 72}

Epistemic context: this is a durable raw event generated after parsing the 72 responses in that cell. The corresponding 19 `run_finished` events have the same 72/0 completion count; only Gemini 3.8 high cells report rescues.

The full panel contained 1,440 final parse-valid ratings. It produced 1,444 response phases: 1,440 initial plus four rescue phases. Two `ReadTimeout` attempts did not yield a response and were conservatively charged at their per-request bounds; their retry attempts subsequently completed. There were no `request_attempt_route_invalid` events and no response without `usage.cost`.

The global ledger settles exactly the conservative amount:

> "pilot/gemini-flash-rubric-smoke/20260918T111625.452461Z": "0.0053585",
> "pilot/gemini-flash-rubric-smoke-2048/20260918T114112.952954Z": "0.0046880",
> "pilot/gemini-flash-rubric/20260918T115056.470656Z": "3.19879800"

The three values sum to USD 3.20884450. The full panel's provider-reported response cost was USD 3.18036600, and two failed attempts added USD 0.01843200 in conservative bounds, giving the USD 3.19879800 full-run settlement. Including the two earlier smokes gives USD 3.19041250 provider-reported versus USD 3.20884450 conservative local spend. `reservations` is empty in `slop/research/wvs/20260917_score_all_options/budget.json`.

### Route and quantization provenance

All 1,444 panel response phases selected Google AI Studio, with `allow_fallbacks=false` and `require_parameters=true`. Exact releases from selected endpoint metadata were:

| requested alias | selected release | completed panel response phases | advertised quantization |
| --- | --- | ---: | --- |
| google/gemini-3-flash-preview | google/gemini-3-flash-preview-20251217 | 288 | unknown |
| google/gemini-3.5-flash | google/gemini-3.5-flash-20260519 | 288 | unknown |
| google/gemini-3.6-flash | google/gemini-3.6-flash-20260721 | 288 | unknown |
| google/gemini-3.7-flash | google/gemini-3.7-flash-20260813 | 288 | unknown |
| google/gemini-3.8-flash | google/gemini-3.8-flash-20260902 | 292, including four rescues | unknown |

`validate_route` compares requested alias, response alias, selected provider, and selected dated release, and throws on mismatch (`scripts/wvs_gemini_flash_rubric_pilot.py:115-149`). The dated snapshot has `quantization: "unknown"` for each standard endpoint. Therefore route is known, but exact numeric precision is not. The prior 97-model audit also says, verbatim:

> No quantization-stratified variance is identifiable. Exact requires an explicit saved response quantization; current endpoint joins are ambiguous rather than historical route evidence.

Epistemic context: this is the authored conclusion in `quantization_audit.json` after joining stored results to the dated endpoint catalog. It rules out a quantization explanation only in the sense that such an explanation cannot be measured here.

### Cell coordinates, response uncertainty, and all-equal rates

Coordinates are `(Self-expression, Secular-Rational)`. `response_mean_se` holds the item set fixed and resamples the six response draws. `all-equal` means a raw rating vector assigned the same value to every option, which becomes uniform after the ratings are normalized.

| release | cell | coordinate | response mean SE | all-equal / 72 | rescues |
| --- | --- | --- | --- | ---: | ---: |
| 3 Flash Preview | normal minimum | (0.6170, 0.6283) | (0.0067, 0.0064) | 28 | 0 |
| 3 Flash Preview | normal high | (0.4496, 0.6769) | (0.0249, 0.0088) | 27 | 0 |
| 3 Flash Preview | reversed minimum | (0.5808, 0.6101) | (0.0081, 0.0118) | 27 | 0 |
| 3 Flash Preview | reversed high | (0.4155, 0.6693) | (0.0240, 0.0040) | 28 | 0 |
| 3.5 Flash | normal minimum | (0.6138, 0.5615) | (0.0117, 0.0121) | 20 | 0 |
| 3.5 Flash | normal high | (0.5505, 0.6388) | (0.0198, 0.0075) | 32 | 0 |
| 3.5 Flash | reversed minimum | (0.6142, 0.5531) | (0.0070, 0.0165) | 32 | 0 |
| 3.5 Flash | reversed high | (0.4958, 0.6523) | (0.0293, 0.0109) | 32 | 0 |
| 3.6 Flash | normal minimum | (0.5891, 0.6023) | (0.0072, 0.0055) | 24 | 0 |
| 3.6 Flash | normal high | (0.5522, 0.6389) | (0.0132, 0.0052) | 27 | 0 |
| 3.6 Flash | reversed minimum | (0.6244, 0.5470) | (0.0062, 0.0163) | 30 | 0 |
| 3.6 Flash | reversed high | (0.5807, 0.6649) | (0.0106, 0.0122) | 30 | 0 |
| 3.7 Flash | normal minimum | (0.4679, 0.6303) | (0.0199, 0.0076) | 29 | 0 |
| 3.7 Flash | normal high | (0.5077, 0.6193) | (0.0112, 0.0084) | 28 | 0 |
| 3.7 Flash | reversed minimum | (0.5035, 0.6309) | (0.0072, 0.0108) | 45 | 0 |
| 3.7 Flash | reversed high | (0.5295, 0.6360) | (0.0186, 0.0090) | 32 | 0 |
| 3.8 Flash | normal minimum | (0.4114, 0.6264) | (0.0183, 0.0057) | 26 | 0 |
| 3.8 Flash | normal high | (0.4240, 0.6154) | (0.0048, 0.0078) | 24 | 1 |
| 3.8 Flash | reversed minimum | (0.4215, 0.6002) | (0.0164, 0.0095) | 37 | 0 |
| 3.8 Flash | reversed high | (0.4553, 0.6446) | (0.0133, 0.0098) | 28 | 3 |

Across cells, 586/1,440 raw rating vectors were all-equal, 40.7%. This is a response style, not necessarily a parser bug: every all-equal vector was syntactically valid and retained by the published scoring rule. It is nevertheless a material reason the coordinate can move without a directional change among options.

### Was the requested manipulation applied?

The normal prompt anchors ratings as `1 (strongly reject) to 5 (strongly endorse)`. The reversed prompt anchors them as `1 (strongly endorse) to 5 (strongly reject)`. In the reader, the exact transform is:

> r_raw[perm[j]] = rated[j]
> r_transformed = 6 - r_raw if rating_rubric == "reversed" else r_raw.copy()
> agg[i]["rating_samples_transformed"].append(r_transformed)
> agg[i]["p_samples"].append(r_transformed / r_transformed.sum())

Source: `src/moralmaps/read_api.py:463-469`. The raw and transformed reversed ratings remain in each `item_result`, and both manifest and result contain `not_published: true`.

The high payloads specified `{"effort":"high"}`. Minimum is not the same setting for every release: 3, 3.5, and 3.6 use `minimal`; 3.7 and 3.8 use `low`. Observed reasoning-token totals support that the high payload changed generated behavior, but also show that `low` is not no reasoning:

| release | normal minimum reasoning tokens | normal high reasoning tokens | reversed minimum reasoning tokens | reversed high reasoning tokens |
| --- | ---: | ---: | ---: | ---: |
| 3 Flash Preview | 0 | 69,666 | 0 | 74,305 |
| 3.5 Flash | 0 | 44,239 | 0 | 44,620 |
| 3.6 Flash | 0 | 57,045 | 0 | 54,386 |
| 3.7 Flash | 6,909 | 38,849 | 8,729 | 44,798 |
| 3.8 Flash | 4,679 | 101,817 | 4,251 | 111,138 |

The raw response record often exposes only a Gemini reasoning signature. Of 1,444 panel response phases, 889 report nonzero reasoning tokens, but only 758 include visible reasoning text. Hidden reasoning cannot be audited from this data.

### Paired effects and order contrast

For each release, I used the same six seed positions across the two compared cells, computed a coordinate at each position from the fixed 12 items, then report mean difference and ordinary paired SE over six positions. This is a descriptive paired uncertainty, not an independent replicate estimate.

| release | normal high minus minimum | reversed minimum minus normal minimum | difference-in-differences interaction |
| --- | --- | --- | --- |
| 3 Flash Preview | (-0.1674 +/- 0.0203, +0.0486 +/- 0.0096) | (-0.0362 +/- 0.0183, -0.0181 +/- 0.0114) | (+0.0021 +/- 0.0348, +0.0106 +/- 0.0121) |
| 3.5 Flash | (-0.0634 +/- 0.0348, +0.0773 +/- 0.0176) | (+0.0004 +/- 0.0122, -0.0084 +/- 0.0247) | (-0.0550 +/- 0.0467, +0.0219 +/- 0.0341) |
| 3.6 Flash | (-0.0369 +/- 0.0127, +0.0366 +/- 0.0062) | (+0.0353 +/- 0.0126, -0.0553 +/- 0.0207) | (-0.0068 +/- 0.0146, +0.0813 +/- 0.0155) |
| 3.7 Flash | (+0.0398 +/- 0.0293, -0.0111 +/- 0.0034) | (+0.0355 +/- 0.0135, +0.0005 +/- 0.0156) | (-0.0137 +/- 0.0362, +0.0162 +/- 0.0159) |
| 3.8 Flash | (+0.0125 +/- 0.0256, -0.0110 +/- 0.0056) | (+0.0100 +/- 0.0339, -0.0262 +/- 0.0155) | (+0.0213 +/- 0.0353, +0.0554 +/- 0.0103) |

These high-minus-minimum directions do not repeat across releases. The high shift is negative on Self-expression for 3, 3.5, and 3.6 but positive for 3.7 and 3.8; it is positive on Secular-Rational for the first three but negative for the latter two. This directly contradicts the preregistered expectation of a repeated effect direction.

Binary items use three identity-order and three reversed-order draws. Descriptively, using sample positions 3-5 minus 0-2, with all items retained in each coordinate, produced contrasts from -0.0902 to +0.0632 on Self-expression and -0.1028 to +0.0218 on Secular-Rational across cells. This is too variable, and is entangled with which seed positions fall in each half, to call a positional-bias correction. It is evidence that the binary order control is not negligible at N=6.

### Rescues and complete-response inspection

All four rescues were Gemini 3.8 high-effort responses. Their initial responses were a valid provider `stop` but lacked a parse-valid JSON rating object, so the runner sent an assistant-turn tail plus the forcing prompt. The rescue use is visible in `src/moralmaps/read_api.py:390-421`. For the three reversed-high Homosexuality rescues, recorded reasoning-token counts were 1,966, 1,912, and 512; all three rescue messages stopped and yielded parse-valid JSON. This is better than dropping samples, but these repaired second turns are not exchangeable with ordinary one-turn samples.

I inspected a complete item result and its six raw strings from each cell. As one representative raw artifact, `records/google__gemini-3.8-flash/reversed_high.jsonl` preserves both raw and transformed ratings for Homosexuality. Its raw vector begins `[5, 5, 4, 4, 3, 3, 2, 2, 1, 1]`, and the stored transformed vector is `[1, 1, 2, 2, 3, 3, 4, 4, 5, 5]`. This is consistent with the intended transform, not a silent coordinate inversion.

### Independent fresh review

A fresh read-only reviewer, Kimi K3, independently inspected the runner, manifest, all raw records, attempt ledger, and both budgets. It reported:

> Cell order fully confounded with time. Cells always ran in fixed order normal_minimum -> normal_high -> reversed_minimum -> reversed_high, models sequential 3-preview -> 3.8, single-threaded (`concurrency: 1`), 11:50-13:38 UTC. Any endpoint drift / load / time-of-day effect is perfectly aliased with cell and model.

> All-equal response styles are common and uneven. Fraction of samples rating every option identically (-> uniform p, pulls coords to simplex center): ranges 20/72 (3.5 normal_minimum) to 45/72 (3.7 reversed_minimum).

Epistemic context: this is an independent artifact and code review, not a new measurement. Its audit transcript is recorded in the parent Pi session and its numerical claims match the raw-record recount above.

## Hypotheses

### H1 [measurement | Highly Likely | 80%]

- Mechanism: the crossed prompt settings change these measured coordinates, but the results do not identify a release-invariant effect of reasoning depth.
- Evidence: 3 Preview high-minus-minimum is `(-0.1674, +0.0486)`, while 3.7 is `(+0.0398, -0.0111)`, from the same recomputation over stored samples. This direction reversal is difficult to reconcile with one shared directional reasoning effect.
- Contrary evidence: high effort produced much more observed reasoning-token use in every release, so the requested payload manipulation was real.
- Discriminating test: rerun only two releases with cell order randomized or counterbalanced within model, holding 2048 tokens and the same provider lock. A time-order explanation predicts the apparent condition effect changes with order; a stable treatment predicts it survives counterbalancing.
- Fix/action: do not select a reasoning setting from this pilot. Treat the effects as sensitivity evidence and design the counterbalanced follow-up before another paid panel.
- Interpretability: partial, the pilot shows protocol sensitivity but not its causal mechanism.

### H2 [measurement | Highly Likely | 75%]

- Mechanism: anchor polarity and its `6 - rating` correction affect coordinates for some releases, rather than recovering one rubric-invariant readout.
- Evidence: 3.6 reversed-minus-normal at minimum is `(+0.0353, -0.0553)`, with paired SE `(0.0126, 0.0207)`; 3.5 is close to zero on Self-expression. The effect is neither uniformly zero nor directionally stable.
- Contrary evidence: the raw-to-transformed fixture and retained item vectors support implementation correctness.
- Discriminating test: add a semantically equivalent wording perturbation without changing numerical anchor polarity. If it moves coordinates similarly, prompt semantics rather than arithmetic correction is the leading explanation.
- Fix/action: keep normal human-facing rubric as primary and keep reversed data separate, as already implemented.
- Interpretability: yes for sensitivity, no for claiming corrected-rubric equivalence.

### H3 [data | Likely | 65%]

- Mechanism: all-equal vectors materially pull item distributions toward uniform and can account for some cell movement.
- Evidence: 586/1,440 vectors are all-equal, including 45/72 in 3.7 reversed minimum; `p = r_transformed / r_transformed.sum()` converts an all-equal rating to uniform (`src/moralmaps/read_api.py:463-469`).
- Contrary evidence: the flat vectors are valid responses under the explicitly chosen dense-rating protocol, so deleting them after observing results would change the estimator.
- Discriminating test: report a prespecified flat-vector rate and a sensitivity coordinate that excludes them only as a diagnostic, never as a replacement measurement. If condition deltas vanish only in that diagnostic, flat-response style is the likely driver.
- Fix/action: add flat-vector rate to any future pilot manifest and report it before interpreting coordinates.
- Interpretability: partial, current coordinates remain protocol outputs but not clean attitude-only measurements.

### H4 [harness | Likely | 60%]

- Mechanism: high-effort Gemini 3.8 responses can consume the shared completion budget and require conditioned rescue, making those four samples a distinct response procedure.
- Evidence: three 3.8 reversed-high rescues had 1,966, 1,912, and 512 reasoning tokens, while their rescue JSON parses successfully. The first high smoke had already shown a 1,024-token truncation, which motivated the common 2,048 cap.
- Contrary evidence: all four final samples are valid and all response phases ended `stop`; no sample was silently substituted with a different provider or seed.
- Discriminating test: a small 3.8 high-only panel at a larger fixed shared completion limit. If rescues vanish but coordinate stays within paired uncertainty, rescue conditioning was not the source of the current shift.
- Fix/action: record rescue status in all analyses and do not mix rescue and initial phases as iid observations.
- Interpretability: partial for 3.8 high cells, yes for parse completeness.

### H5 [bug | Unlikely | 25%]

- Mechanism: an unobserved route or transform error could still create a spurious shift.
- Evidence: every panel request has a selected Google AI Studio route, no route-invalid event occurred, and source code applies the specified reversal exactly once before normalization.
- Contrary evidence: model aliases and hidden reasoning remain opaque, and endpoint behavior could drift during the fixed-order run.
- Discriminating test: replay the offline raw-record audit in a clean checkout, assert one transform per reversed sample, and compare all selected route tuples against the saved catalog.
- Fix/action: no implementation change is justified from this run; add the offline audit assertion to a maintained smoke only if this pilot is extended.
- Interpretability: yes for route and arithmetic provenance, partial for causal effects.

## Decision

1. Resolve-condition verdict: met. The job's stated resolve condition was to audit all 20 cells for completion, route, rescue, cost, and paired shifts before interpretation. All 20 are complete, routes are exact to selected dated Google AI Studio releases, rescue and retry paths are counted, the cost ledger is reconciled, and paired shifts are above.
2. Prediction check:
   - Repeated high-minus-minimum direction across releases: contradicted.
   - Reversed rubric differs from normal under the same effort: supported as sensitivity for several releases, but direction is not stable.
   - One release trend agrees across all four cells: unresolved. No preregistered trend statistic was computed, and fixed cell order makes a descriptive trend non-diagnostic.
   - Normal and transformed-reversed agree within paired sampling uncertainty: contradicted for several cells, for example 3.6 minimum on both axes.
3. Earliest unsupported link: that a high-versus-minimum coordinate difference is caused by reasoning depth rather than fixed execution order, endpoint time variation, all-equal response style, or rescue conditioning. Counterbalanced cell order is the cheapest decisive measurement.
4. Validity: define invalid as unable to establish that every reported coordinate came from the specified release/provider/rubric/effort protocol. On that definition, P(invalid) is about 0.10-0.20: route, raw data, transform and costs are well preserved. For a causal claim about reasoning, P(invalid) is above 0.60 because cell order is fully confounded with time. Classification: credible protocol-sensitivity result, inconclusive causal explanation.
5. Highest-information clues, ranked: (a) opposite high-minus-minimum directions across release generations, because it rejects a simple shared treatment story; (b) 586/1,440 all-equal vectors, because the estimator maps them directly to uniform probability; (c) exact global-local conservative reconciliation, because it validates the USD 20 control did not silently overspend.
6. Missing metrics, ranked: randomized/counterbalanced cell order; reasoning text or another observable reasoning-depth proxy; a prespecified flat-vector sensitivity diagnostic; independent day/provider replicate; a direct positional-bias estimator with randomized seed assignment.
7. Bugs requiring code changes: none demonstrated. The observed limitations are measurement design, not a demonstrated parser, route, transform, or ledger fault.
8. Misconceptions requiring reinterpretation: high means substantially more exposed reasoning tokens but not necessarily a causal moral-coordinate treatment; low is not equivalent to no reasoning; inverse rubric arithmetic does not guarantee rubric invariance; provider name does not identify quantization.
9. What would change the verdict: a counterbalanced run retaining direction and magnitude within paired uncertainty would raise confidence in a reasoning effect. A randomized flat-vector diagnostic explaining the differences would instead make response style the leading account.
10. Recommended sequence: preserve and commit this branch-contained evidence, append observed costs to the journal, and do not change the published map. Before another paid run, compare a small counterbalanced two-release follow-up with a flat-vector diagnostic. Do not combine a larger N, a token-limit change, a new wording, different provider, and counterbalancing in one experiment, because it would destroy attribution.

-- PI[gpt-5.6-terra]
