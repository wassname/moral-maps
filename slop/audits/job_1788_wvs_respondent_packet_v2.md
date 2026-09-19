# Audit: Pueue task 1788, WVS respondent packet v2

Scope: offline audit and reanalysis of the completed 4 x 128 Qwen Plus packet panel. No replacement API calls were made. This audit covers the raw response bytes, encoding-aware reprocessing, fixed comparison to `wvs-score-all-options-v1`, costs, route metadata, and published-map integrity.

## Stage table

| stage | expected | observed | expected? | clues | missing metric | consequence |
|---|---|---|---|---|---|---|
| dispatch | API task runs once and finishes | task 1788 is `Success` after 51m36s | yes | `pueue_task_1788_status.json` | worker stdout progress | stdout cannot establish data validity |
| raw persistence | 512 complete packet records | 128 `respondent_parsed` events for each of 4 releases | yes | four `records/*/packets.jsonl` files | none | raw text supports independent reprocessing |
| parser | valid visible labels stay substantive | 266 of 273 prior nonconforming packets map deterministically; 7 retain two unmapped question fields | no, before fix | `reprocessing_inventory.json` | human adjudication of two paraphrase labels | the original refusal rates were parser artifacts |
| reason policy | reasons never change choices | 20 packets have `reason_format_failure`; their choices remain substantive | yes after fix | reprocessed events, `analysis.json` | none | reasons are qualitative only |
| packet analysis | whole-row bootstrap, fixed items, all 4 releases | 1,000 complete bootstrap draws per protocol | yes | `analysis.json` | repeated independent panel | uncertainty is sampling conditional on this serving route |
| dense comparison | same releases and fixed items | all 4 dense-v1 coordinates and packet-minus-dense CIs written | yes | `analysis.json` | paired responses, which do not exist | shift CIs use independent bootstraps |
| budget and route | pinned Alibaba route, costs reconciled | all completed panel routes are Alibaba, advertised quantization `unknown`; global observed ledger records panel cost | partial | `request_attempts.jsonl`, both budget ledgers | provider statement of failed-attempt charges | local conservative cost exceeds observed cost by failed-attempt reserve bounds |
| publication safety | no map changes | byte-empty diff and the three tracked map hashes match pre-audit values | yes | command below | none | this task did not publish or replace map coordinates |

## Provenance and raw-response audit

The task status artifact records the exact command, branch path, and terminal state:

> `"command": "scripts/wvs_api/10_respondent_packet_v2_panel.sh"`
> `"path": "/workspace/2026/lite/moralmaps"`
> `"result": "Success"`

Source: `slop/research/wvs/20260919_respondent_packet/pueue_task_1788_status.json`, copied from `pueue status --json` for task 1788. The complete Pueue log after ANSI and carriage-return stripping is one line, not a progress log:

> `panel complete`

Source: `slop/research/wvs/20260919_respondent_packet/pueue_task_1788_clean.log`, SHA-256 `92473da432bf48210d2a3cdb0d0386b5299493fd07f8b38afde9eb1dc66ad684` for the raw Pueue log. This establishes only successful shell completion; the packet JSONLs are the primary outcome evidence.

I inspected all 512 `respondent_parsed` raw `text` values. All were one well-formed JSON object. There were no empty texts, no no-JSON replies, no unparseable JSON, and no rescues. The original parser accepted the canonical schema and one strict positional spelling only. It had marked 273 responses nonconforming because endpoint serialization varied.

The new encoding-aware protocol accepts only mappings from visible labels:

- ordinary block `n`, `A` through the displayed maximum letter -> option `n`'s displayed option;
- child item integer or decimal string `1..11` -> the displayed 1-indexed child quality;
- numbered blocks `1..9`, `q1..q9`, or `N_...` blocks map by their visible numeric label;
- answer lists map only by explicit numeric question index or exact prompt ID, never by list order.

It accepts exactly one selection key per block. The supported keys are `answer`, `choice`, `option`, and `selected_option`, plus plural forms for child lists. A missing or >8-word reason sets `reason_status` but retains a valid selection. Duplicate indices, duplicate child values, out-of-range labels, lowercase letters, multiple choice fields, and unknown question aliases are refused. Fixtures in `offline_smoke` cover the observed forms and these ambiguity rejections.

Exact reprocessed packet shape counts:

| release | canonical | numbered | q-numbered | N-prefix | numeric answer list | true-refusal packets | refused question instances |
|---|---:|---:|---:|---:|---:|---:|---:|
| qwen3.5-plus-02-15 | 0 | 86 | 0 | 2 | 40 | 7 | 14 |
| qwen3.6-plus | 0 | 109 | 3 | 0 | 16 | 0 | 0 |
| qwen3.5-plus-20260420 | 0 | 127 | 1 | 0 | 0 | 0 | 0 |
| qwen3.7-plus | 128 | 0 | 0 | 0 | 0 | 0 | 0 |

Source: `reprocessing_inventory.json`. The complete structural inventory, including key and scalar-type signature, is in that file. The seven residual packets are `qwen3.5-plus-02-15` answer lists with two paraphrase identifiers, including `"Trust in people"` and `"Important qualities for children"`. Those identifiers are not displayed labels or exact prompt IDs, so mapping them would need semantic inference. The other seven answers in each such packet remain directly labeled; the two unmapped question instances stay refusals. This is a partial-item refusal, not an invented full-packet refusal.

Examples of deterministic mappings:

> `"1": {"option": "C", ...}, ... "9": {"options": [1, 2, 6, 8, 10], ...}`

Source: `records/qwen__qwen3.5-plus-02-15/packets.jsonl`, packet 3. The visible `C` and child numbers map directly through the rendered labels.

> `"answers": [{"question_id": 1, "selected_option": "C", ...}, ... {"question_id": 9, "selected_options": [1, 2, 6, 9, 10], ...}]`

Source: `records/qwen__qwen3.6-plus/packets.jsonl`, packet 7. Each numeric `question_id` is an explicit displayed block number.

A fresh read-only reviewer separately audited every raw structure and identified the same two categories: deterministic label variation and seven name-paraphrase packets that must not be semantically mapped. Its session artifact is `/home/code/.pi/agent/sessions/--workspace-2026-lite-moralmaps--/subagent-artifacts/outputs/34acf2a8-94e1-46a3-a39e-cee4179392ee/slop/reviews/20260919_respondent_packet_raw_schema_review.md`.

## Reanalysis

Coordinates are `[Survival <-> Self-expression, Traditional <-> Secular-Rational]`. Both comparisons score the same 12 recovered WVS axis rows: 8 ordinary items plus the four child-quality coefficient rows in `PANEL_QUALITIES`, Obedience, Independence, Determination/perseverance, and Imagination. The packet asks all 11 human child qualities. The other seven selections, including Religious faith, remain in every raw respondent packet but do not enter these recovered coordinates because no axis coefficients are used for them here. Packet CIs and SEs use B=1,000 whole-respondent-row bootstrap draws. Dense-v1 uses its existing per-item rating samples, so packet-minus-dense shifts use independent bootstrap draws.

| release | packet coordinate, SE | packet CI95 | dense-v1 coordinate, SE | packet minus dense, CI95 |
|---|---|---|---|---|
| qwen3.5-plus-02-15 | [0.7734, 0.7599], [0.0094, 0.0058] | [[0.7539, 0.7495], [0.7906, 0.7715]] | [0.5372, 0.6595], [0.0070, 0.0052] | [0.2362, 0.1004], [[0.2110, 0.0863], [0.2576, 0.1152]] |
| qwen3.6-plus | [0.7320, 0.8100], [0.0155, 0.0067] | [[0.7023, 0.7971], [0.7609, 0.8224]] | [0.5197, 0.6699], [0.0082, 0.0101] | [0.2124, 0.1401], [[0.1780, 0.1159], [0.2466, 0.1621]] |
| qwen3.5-plus-20260420 | [0.5789, 0.7783], [0.0105, 0.0084] | [[0.5586, 0.7615], [0.5992, 0.7945]] | [0.5856, 0.6494], [0.0159, 0.0071] | [-0.0067, 0.1289], [[-0.0431, 0.1062], [0.0312, 0.1503]] |
| qwen3.7-plus | [0.7281, 0.8341], [0.0204, 0.0075] | [[0.6867, 0.8193], [0.7648, 0.8486]] | [0.5078, 0.6664], [0.0093, 0.0083] | [0.2203, 0.1676], [[0.1731, 0.1459], [0.2603, 0.1889]] |

Source: `analysis.json`. The coordinates are data descriptions, not released map replacements.

| evaluator | constant-family RMSE | linear-release RMSE | response-noise floor, constant / linear | LOO constant, CI95 | LOO linear, CI95 |
|---|---:|---:|---:|---:|---:|
| packet v2 | 0.0792 | 0.0696 | 0.0132 / 0.0104 | 0.0942, [0.0840, 0.1072] | 0.1318, [0.1018, 0.1599] |
| dense v1 | 0.0307 | 0.0304 | 0.0108 / 0.0092 | 0.0338, [0.0236, 0.0506] | 0.0514, [0.0309, 0.0769] |

Observations:

- Packet family scatter is about six times its simulated response-noise floor, 0.0792 / 0.0132. This is strong evidence that the release differences are not explained by this bootstrap sampling noise alone.
- Linear fit has lower in-sample packet RMSE, 0.0696 vs 0.0792, but worse packet leave-one-release-out error, 0.1318 vs 0.0942. With four releases, the observed linear improvement is likely overfit rather than evidence for a release trend.
- Dense v1 also has worse LOO for the line, 0.0514 vs 0.0338. This supports the same warning but does not prove either protocol is closer to a human coordinate.
- Packet-vs-dense shifts are positive on both axes for three releases. The later 3.5 revision has an X shift CI overlapping zero and positive Y shift. These shifts are expected to include administration and representation changes, not just model behavior.

Qualitative reasons were inspected but never scored or used to select a protocol. They frequently describe AI identity or lack of physical agency. Examples include:

> `"I am an AI without spiritual beliefs."`

and

> `"I cannot physically sign documents."`

Source: raw response text in `records/qwen__qwen3.5-plus-20260420/packets.jsonl`, packet 1. This is an observation about the model's stated framing. It does not establish a causal explanation for the coordinates.

## Costs, attempts, and route metadata

The 512 panel `request_completed` events report USD 0.416999506 total:

| release | completed panel calls | provider-reported panel cost | selected release slug |
|---|---:|---:|---|
| qwen3.5-plus-02-15 | 128 | 0.099283600 | qwen/qwen3.5-plus-20260216 |
| qwen3.6-plus | 128 | 0.121719650 | qwen/qwen3.6-plus-04-02 |
| qwen3.5-plus-20260420 | 128 | 0.110536800 | qwen/qwen3.5-plus-20260420 |
| qwen3.7-plus | 128 | 0.085459456 | qwen/qwen3.7-plus-20260602 |

Every completed request in `request_attempts.jsonl` has `selected_provider: Alibaba`, `endpoint_tag: alibaba`, `response_model` equal to the requested model, and `advertised_quantization: unknown`. The four-release comparison is one provider and product tier, but quantization remains unknown. This is a route limitation, not evidence of a matched underlying precision.

Across the local stage ledger there are 524 attempt events: 516 completed and 8 failed. The 8 failures are six HTTP 400 and two HTTP 429 events. The local ledger reports provider cost USD 0.419875846 and conservative cost USD 0.447093766, with `reserved_usd: "0E-9"`; the difference covers failed-phase reserve charges and pre-panel smoke phases. The global ledger now contains `panel/resp-packet-v2/pueue-1788: "0.416999506"`, has no outstanding reservations, and was reconciled at `2026-09-19T12:22:49.318979+00:00`. It records observed provider panel cost, not an assertion that failed requests were free.

## ML-debug form, hypotheses, and decision

| row | answer |
|---|---|
| log length and config | Pueue log after ANSI and carriage-return stripping is 1/1 line; task executed `scripts/wvs_api/10_respondent_packet_v2_panel.sh`; each payload and response is retained in 512 raw record triplets. |
| `SHOULD` checks | no `SHOULD:` lines in task stdout; the real checks are route validation, raw persistence, reprocessing fixtures, and map diff. |
| null / scale | a null family has the simulated response-noise floor above; observed scatter exceeds it. Linear-vs-constant generalization is the LOO comparison, not in-sample RMSE. |
| full sample | raw packet examples above; every model's 128 raw responses were structurally inventoried. |
| surprising observation | qwen3.6 had 128/128 apparent refusals before reprocessing but has 128 direct label-mapped packets afterward. This was parser strictness, not an observed provider refusal. |
| missing evidence | independent repeat panels, known quantization, and a human-response calibration of the packet framing. |
| fresh review | the independent reviewer artifact above found the same strict-parser issue and kept name-paraphrase list fields unscored. |
| wall-clock | 51m36s for task 1788; sequential API requests were intentional. |

### H1 [bug | Almost Certain | 95%]

- Mechanism: the prior parser accepted only a strict schema and one strict positional form. It classified endpoint key spelling, integer child labels, and numeric answer lists as refusals.
- Evidence: `reprocessing_inventory.json` records 109 numbered plus 16 numeric-list packets for qwen3.6, while the original `results.json` had coverage 0.0 for that model. The raw response form uses visible labels, for example `"question_id": 9` with `"selected_options": [1, 2, 6, 9, 10]`.
- Contrary evidence: seven answer-list packets contain paraphrase question identifiers; those are not mapped.
- Discriminating test: rerun the offline fixtures against a response with two selection keys, a duplicate numeric question index, or `"Trust in people"`. Expected: no substantive mapping for the ambiguous field. The fixtures pass.
- Fix/action: append `respondent_reprocessed` rows under new encoding-aware protocol IDs; preserve raw and original parsed events.
- Interpretability: partial before reprocessing, yes after deterministic reprocessing.

### H2 [measurement | Highly Likely | 80%]

- Mechanism: packet choice frequencies and dense option ratings are different administrations and response geometries, so their coordinate differences are protocol effects as well as model effects.
- Evidence: packet-minus-dense shifts are [0.2362, 0.1004] for the oldest release and [0.2203, 0.1676] for qwen3.7, with both coordinate CIs positive.
- Contrary evidence: one later-3.5 X shift is -0.0067 with CI [-0.0431, 0.0312], so protocol shifts are not constant across releases.
- Discriminating test: repeat both evaluators with multiple independent respondent panels and a preregistered common scoring subset. A stable within-model shift across repeats would support an administration effect.
- Fix/action: report both evaluator versions separately. Do not overwrite dense coordinates or publish packet coordinates.
- Interpretability: yes for within-protocol descriptions; no for a claim that either is the human-ground-truth coordinate.

### H3 [method | Likely | 65%]

- Mechanism: the in-sample linear release fit overfits four heterogeneous releases.
- Evidence: packet linear RMSE is lower in sample, 0.0696 vs 0.0792, yet linear LOO error is higher, 0.1318 vs 0.0942. Dense v1 has the same sign, 0.0514 vs 0.0338 LOO.
- Contrary evidence: both point metrics are calculated on the only available four-release family; there is no held-out fifth Qwen Plus release.
- Discriminating test: add a preregistered fifth same-route release, then compare constant and linear predictions without refitting their form.
- Fix/action: treat family centroid as the better current predictive summary; do not select a release trend.
- Interpretability: yes for the observed four-release scatter, partial for extrapolation.

### H4 [harness | Likely | 60%]

- Mechanism: unknown advertised quantization and no independent panel leave route and response-sampling effects confounded with release differences.
- Evidence: every route record says `advertised_quantization: unknown`; response-noise floors are much lower than packet scatter, but bootstrap does not model route changes or a different generation run.
- Contrary evidence: provider is pinned to Alibaba and each completed response validates its dated release slug.
- Discriminating test: run an approved repeat with saved endpoint metadata that states quantization, or a provider route with known matched precision.
- Fix/action: retain route metadata and qualify release comparisons as service-release comparisons.
- Interpretability: partial.

### H5 [data | Chances a little better than even | 50%]

- Mechanism: the model frames itself as an AI despite the respondent instruction, particularly on religion and physical political actions, which can change packet coordinates.
- Evidence: raw reasons include `"I am an AI without spiritual beliefs."` and `"I cannot physically sign documents."`.
- Contrary evidence: reasons are short, not exhaustive rationales, and were not scored. They cannot estimate how much this framing moved a coordinate.
- Discriminating test: compare a future preregistered framing manipulation while holding schema, model, route, and sample count fixed.
- Fix/action: retain reasons as qualitative audit material only.
- Interpretability: yes for observed answers, no causal attribution to the stated reasons.

## Resolve condition and recommendation

The task label says:

> `resolve: audit uncertainty, refusals, family scatter and release trend without publishing`

Verdict: met. The full raw panel was reprocessed without calls, uncertainty and coverage are in `analysis.json`, family scatter and LOO trend tests are reported, costs and routes are reconciled, and the map diff is empty.

Prediction check: the plan recorded no directional prediction that a line should generalize better than a family centroid. The observed LOO result contradicts choosing the line. The original parser's reported refusal pattern is contradicted by the raw responses.

Earliest unsupported link: a service-release difference is not yet a model-release difference, because advertised quantization is unknown and there is only one response panel per release.

Validity: define invalid as a result that still silently treats deterministic serialization variants as refusals, changes the published map, loses respondent covariance, or fits trend metrics after a coverage collapse. Under that definition, P(invalid) is about 0.10 to 0.20. The main result is a credible descriptive packet-vs-dense comparison, not a credible causal estimate of model evolution.

Highest-information clues, in order:

1. qwen3.6 raw responses used visible labels in all 128 packets despite original 100% refusal output. This directly localized a parser error.
2. Packet linear LOO is worse than constant LOO despite a better in-sample line. This rejects the tempting trend interpretation.
3. Packet scatter is materially above the response-noise floor. This rejects an explanation based only on within-panel resampling variation.

Missing evidence, ordered by expected information gain: (1) a fifth or repeated same-route panel, (2) verified route precision, (3) human calibration of the respondent prompt, (4) manual adjudication only if name-paraphrase items must be recovered.

Recommended sequence: keep this versioned packet result as an un-published evaluator artifact; do not choose a linear trend or replace the dense map. Before any broader family panel, require a known-precision route or state that precision is unknown, and run a fixed repeat or fifth-release prediction check. Do not combine a prompt change, route change, and evaluator change in one follow-up because that destroys attribution.

## Verification commands

```sh
uv run --offline --with 'datasets>=4.0,<5' python scripts/wvs_respondent_packet_v1.py --offline-smoke
uv run --offline --with 'datasets>=4.0,<5' python scripts/wvs_respondent_packet_v1.py --offline-regression
uv run --offline --with 'datasets>=4.0,<5' python scripts/wvs_respondent_packet_v1.py --synthetic-analysis-test
uv run --offline --with 'datasets>=4.0,<5' python scripts/wvs_respondent_packet_v1.py --reprocess-existing
uv run --offline --with 'datasets>=4.0,<5' python scripts/wvs_respondent_packet_v1.py --analyze
sha256sum slop/research/wvs/20260919_respondent_packet/analysis.json slop/research/wvs/20260919_respondent_packet/reprocessing_inventory.json
git diff --quiet -- docs/wvs/wvs_map_data.json docs/img/wvs/wvs_map_iw.png docs/img/wvs/wvs_map_iw.svg
```

Two full deterministic analysis executions produced the same SHA-256s:

> `887f66cd56e9abb38ec87df58f5060058c2726485607573744010a58783b3ce6  analysis.json`
> `f12badd1faa210b33a881bbbbfc0db5abe1cc0a53fbea449e77330ff1c65889b  reprocessing_inventory.json`

Map diff exit code was 0. Map SHA-256 values are `c03b5104a9a31482fa547a8a2996e33d3d3d59453d5189f94e95d9d451bf63d1` for JSON, `a7164901ff69e1e51696ade8fb9dd9c62d81af5cfa0c94a49ddf5598c68b4103` for PNG, and `d35cb80a70d34472e967ac1453aa54d43c24418b8b74fe71e726d2a927771aa2` for SVG.

-- PI[gpt-5.6-terra]
