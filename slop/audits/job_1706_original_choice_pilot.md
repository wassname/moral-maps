# Audit: Pueue job 1706, original-choice pilot (wvs-original-choice-pilot-v1)

## Status labels (correction 1)

The gemini-3.8-flash panel started 2026-09-19 07:20 +0800, while preregistration commit `5ad68ad40c4cf2d223e6d7554dd4e2b520dfb9ad` landed 07:31 +0800. The 3.8 panel is therefore **exploratory / unpreregistered**; it is retained as valid protocol output but the all-items five-release fit is NOT a preregistered prediction test. The preregistered claims are the per-release P1/P2 directions on the four later releases (3.7's smoke ran at 23:30 UTC on 09-18, after the prereg; its full panel and the other three panels ran after `5ad68ad`).


## Target and provenance

Pueue task 1706 ran `scripts/wvs_api/09_original_choice_pilot.sh` from 2026-09-19 07:31:23 to 07:56:26 +0800 and exited `Success` in 1503 s. The runner is `scripts/wvs_original_choice_pilot.py` (EVAL_VERSION `wvs-original-choice-pilot-v1`), preregistered in `docs/RESEARCH_JOURNAL.md` ("Preregistration: wvs-original-choice-pilot-v1") and committed at `5ad68ad40c4cf2d223e6d7554dd4e2b520dfb9ad` before the queued paid calls. Branch `research/gemini-flash-rubric-v1`; published map untouched.

Deviation disclosure: during pre-paid mocking, the request patch targeted the wrong module attribute, so the gemini-3.8-flash panel (216 requests, USD 0.07433250) executed before the preregistered smoke. The run used the exact preregistered protocol and payloads; the spend was settled into the global ledger as `pilot/original-choice-unplanned-3.8-panel`, and the data was retained as a valid partial panel. The preregistered smoke then ran separately and passed.

## Deviations from the preregistration

1. The point-estimate rule had to be amended during analysis: gemini-3.8-flash (and 3.7-flash) answered `cannot_answer` on ALL 24 samples of some items, so "conditional coordinates" were undefined there. Amended rule: each item's p is the mean over substantive samples; items with zero coverage are excluded from their axis mean (the map's half-coverage rule), exclusions are reported, and a bootstrap draw is skipped only if an axis loses more than half its items. No draw was skipped (1000/1000 used).
2. The smoke reservation was held under one id and settled under another, leaving a stale USD 0.05 reservation; the script is fixed and the stale reservation was released. Ledger now reconciles exactly with zero held reservations.

## Completion, routes, accounting

All five releases completed 9 original questions x 24 paired samples = 216 requests each, 1,080 panel phases plus 1 smoke, all 1,081 request attempts completed on the first attempt (zero retries, zero rescues, zero failures). All selected routes are exact Google AI Studio dated releases: `google/gemini-3-flash-preview-20251217`, `...3.5-flash-20260519`, `...3.6-flash-20260721`, `...3.7-flash-20260813`, `...3.8-flash-20260902`; advertised quantization is `unknown` for all.

| accounting quantity | USD | how known |
| --- | ---: | --- |
| unplanned 3.8 panel (216 phases) | 0.07433250 | sum of record `usage.cost`; global entry `pilot/original-choice-unplanned-3.8-panel` |
| paid smoke (1 phase) | 0.00072075 | `pilot/original-choice-smoke` global entry |
| queued panel (1,080 phases) | 0.23466450 | `pilot/original-choice` global entry; equals records sum 0.30899700 minus the unplanned 0.07433250 |
| total stage spend | 0.30971775 | stage `budget.json.conservative_spent_usd`; three global entries sum to the same value |

Hard stage stop was USD 5; headroom USD 4.69. Global reservations are empty.

## Results

`cannot_answer` is explicit and heterogeneous (overall rate per release): Preview 76/216 (35.2%), 3.5 16/216 (7.4%), 3.6 60/216 (27.8%), 3.7 118/216 (54.6%), 3.8 87/216 (40.3%). Zero-coverage items: Abortion for Preview and 3.6; God and Abortion for 3.7 and 3.8. Abortion is `cannot_answer` for 100% of samples in four of five releases.

Conditional coordinates (x = Survival<->Self-expression, y = Traditional<->Secular-Rational), with paired-bootstrap SE over the 24 shared sample indices (B=1000, all draws used). The 3.8 row is exploratory:

| release | x (SE) | y (SE) | status |
| --- | ---: | ---: | --- |
| 3 Flash Preview | 0.9125 (0.0225) | 0.6806 (0.0583) | preregistered panel |
| 3.5 Flash | 0.9083 (0.0237) | 0.5602 (0.0444) | preregistered panel |
| 3.6 Flash | 0.6042 (0.0195) | 0.6273 (0.0206) | preregistered panel |
| 3.7 Flash | 0.5542 (0.0272) | 0.9000 (0.0340) | smoke preregistered; panel preregistered |
| 3.8 Flash | 0.4875 (0.0209) | 0.9083 (0.0209) | exploratory, pre-prereg |

All-items release OLS (exploratory, not a prediction test): x slope -0.6062/year (SE 0.0496), y slope +0.2834/year (SE 0.0486), 2D residual RMSE 0.1541 (SE 0.0122).

## Fixed-item-set sensitivity (correction 2, the decisive comparison)

The all-items comparison changed the estimand: original-choice 3.7/3.8 Y coordinates omit God and Abortion (zero coverage) while the dense comparators use the full item sets, and different releases omit different items. The corrected comparison fixes one item set per coverage rule, applied to ALL five original-choice releases simultaneously, and recomputes both dense `normal_minimum` and `normal_high` comparators on exactly the same items. Original-choice coverage thresholds are on the substantive-answer fraction; dense comparators have 6/6 valid samples on every item.

| rule | X items | Y items | original RMSE (SE) | dense min RMSE (SE) | dense high RMSE (SE) | orig-vs-min delta (95%) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| common nonzero coverage | 5 | 5 | 0.1232 (0.0112) | 0.0627 (0.0063) | 0.0521 (0.0055) | +0.0628 [0.0376, 0.0870], p(>0)=1.000 |
| >= 25% per-model coverage | 3 | 5 | 0.1691 (0.0139) | 0.1106 (0.0098) | 0.0937 (0.0102) | +0.0606 [0.0255, 0.0936], p(>0)=1.000 |
| >= 50% per-model coverage | 1 | 5 | 0.2643 (0.0231) | 0.1259 (0.0183) | 0.1745 (0.0122) | +0.1385 [0.0820, 0.1935], p(>0)=1.000 |
| >= 75% per-model coverage | 0 | 5 | unavailable | unavailable | unavailable | unavailable |

Uncertainty method: for each protocol and rule, 1,000 response-resampling draws of the release coordinates. Original choice has two variants: the paired within-protocol bootstrap (one shared sample-index draw per release pair) and independent per-release resampling. The dense comparators are bootstrapped by resampling their 6 rating vectors per item (their per-model seed schedules are not pairable with the original 24-sample schedule, so original-minus-dense deltas subtract INDEPENDENT draws; this is stated in `analysis.json`). The >= 75% rule is emitted as an explicit `unavailable` entry with no mean/polyfit call, so no empty-array RuntimeWarning.

Noise floor (does the scatter survive sampling uncertainty?): under H0 of no between-release differences, each release's coordinates were drawn from N(0, diag(per-release response-sampling SD)) and the release-date OLS RMSE recomputed (2,000 draws). Observed versus floor: original 0.1232 vs 0.0292 (95% [0.0137, 0.0498]); dense min 0.0627 vs 0.0116; dense high 0.0521 vs 0.0137 (common nonzero rule). P(noise floor >= observed) = 0.000 for every protocol and rule. Estimated between-release RMSE after subtracting the noise floor: original 0.1197, dense min 0.0612, dense high 0.0502. With n=5 releases (3 residual dof per axis) this variance decomposition is itself unstable and is reported as indicative only; the robust statement is that BOTH protocols show real between-release differences (observed scatter far above their own response-noise floors), and the original-choice estimator's excess over dense survives its own noisier one-hot N=24 estimator: the delta CI excludes zero under every comparable rule.

Item membership per rule (common nonzero): X = {Homosexuality, trust, petition, demonstrations, boycotts}; Y = {Religion, Obedience, Independence, Determination, Imagination}. cov25 drops Homosexuality and trust from X; cov50 keeps only Signing a petition in X. Full coordinates and slopes per rule are in `analysis.json` (`sensitivity_fixed_item_sets`).

Under every rule where a comparison exists, the original-choice release-date 2D RMSE remains about 2.0-2.4x the dense minimum's and larger than the dense high's. The corrected estimand does not reverse the earlier direction; it weakens it (0.1541 all-items was inflated by the item-set mismatch) but the conclusion survives: the original single-choice format shows MORE release-date scatter, not less. The cov50 X axis is a single item, so its RMSE is that item's release variance and the comparison there is weakest.

## Option-position and refusal contrast (correction 3, balance evidence)

Rotation balance: every offered list is cyclically rotated by sample index, so each option occupies each rank exactly 24/k times by construction; bucket occupancy of the DK position across the 8 ordinary items per model is 110 first-third / 66 middle / 16 last-third (bucket edges, not the rotation, produce unequal bucket sizes).

Refusal contrast (cannot_answer rate by the rank of the nearest non-substantive option, thirds): Preview 0.409/0.379/0.375, 3.5 0.073/0.106/0.063, 3.6 0.300/0.288/0.500, 3.7 0.591/0.621/0.750, 3.8 0.473/0.394/0.563 (first/middle/last). Selection share by position third is near-uniform for four of five models (0.30-0.36 per third); 3.7 mildly favors first-third (0.446). No contrast indicates the release-level patterns are a cyclic-order artifact: refusal rates differ strongly BETWEEN releases while staying nearly flat WITHIN release across DK positions.

## Comparison against the dense cells (descriptive only)

- Hidden versus explicit abstention: dense flat vectors are evidence of POSSIBLE hidden abstention, not observed refusals; only the original format's `cannot_answer` selections are observed abstentions. The two are related but not equivalent, and the dense flat rate (35.3-47.5% per cell, 40.7% overall) should not be read as a refusal rate. Under that caveat: explicit refusal in the original format (7.4-54.6%, mean about 33%) sits in the same range as the dense flat rates, so the original format does not clearly reduce total abstention; what it does is make part of it explicit and measurable (P1 supported).
- Scatter: on the fixed common item sets the original-choice release-date 2D RMSE is about 2.0-2.4x the dense cells' (see the sensitivity table). The corrected estimand confirms worse scatter for the original format.
- Coordinates differ from dense normal-minimum on most releases (P2 supported): for example Preview x 0.9125 vs 0.6170, and 3.7/3.8 y about 0.90 vs about 0.63 (all-items values; the fixed-set values are in `analysis.json`).
- Slope directions differ from the dense cells on the same fixed item sets (dense min x-slope -0.2369 on the common set vs original -0.6062).

## Paid-call guard (correction 3)

Root cause of the accidental run, precisely: `wvs_original_choice_pilot` imports `openrouter_request_with_metadata_once` via `from moralmaps.read_api import ...`, binding the function into the pilot module's namespace at import time. The pre-paid test monkeypatched `moralmaps.read_api.openrouter_request_with_metadata_once`, which rebinds only the read_api module attribute and never touches the pilot module's already-bound name, so the pilot kept calling the real API. Defenses added: (1) `budgeted_request` raises `PaidCallsNotAuthorized` unless env `WVS_PAID_CALLS_AUTHORIZED=1`, which only `--i-authorize-paid-calls` sets; (2) `--paid-smoke`/`--run` fail fast without that flag (the pueue wrapper passes it; offline tests do not); (3) CLI actions are mutually exclusive; (4) an offline regression (`--offline-regression`) proves no HTTP call executes without the opt-in even when the read_api level is patched, and that the CLI guard holds.

## Limits (unchanged from the dense pilot)

Release order, model identity, and fixed wall-clock execution order are exactly confounded; n=5; y coordinates for 3.7/3.8 rest on 5 of 7 Y items because God and Abortion had zero coverage. Coordinates are conditional on substantive answers and are not comparable to any published map. No protocol is selected or promoted on these numbers; per the preregistration, trend quality must not drive protocol choice.

## Verdict

The preregistered resolve condition is met: all five releases completed with paired samples, explicit refusal handling, exact-route provenance, exact accounting, and the preregistered analysis executed as written (with the two disclosed deviations). The single-choice original format is a valid instrument that surfaces abstention explicitly, but on this evidence it does not reduce abstention or measurement scatter relative to dense score-all-options scoring.
