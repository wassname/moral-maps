# Audit: Pueue job 1706, original-choice pilot (wvs-original-choice-pilot-v1)

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

Conditional coordinates (x = Survival<->Self-expression, y = Traditional<->Secular-Rational), with paired-bootstrap SE over the 24 shared sample indices (B=1000, all draws used):

| release | x (SE) | y (SE) |
| --- | ---: | ---: |
| 3 Flash Preview | 0.9125 (0.0225) | 0.6806 (0.0583) |
| 3.5 Flash | 0.9083 (0.0237) | 0.5602 (0.0444) |
| 3.6 Flash | 0.6042 (0.0195) | 0.6273 (0.0206) |
| 3.7 Flash | 0.5542 (0.0272) | 0.9000 (0.0340) |
| 3.8 Flash | 0.4875 (0.0209) | 0.9083 (0.0209) |

Release-date OLS: x slope -0.6062/year (SE 0.0496), y slope +0.2834/year (SE 0.0486), 2D residual RMSE 0.1541 (SE 0.0122).

## Comparison against the dense cells (descriptive only)

- Abstention: the original format does NOT reduce it. Overall `cannot_answer` rates (7.4%-54.6%, mean about 33%) overlap the dense flat-vector rates (35.3%-47.5% per cell, 40.7% overall), and the release heterogeneity is larger. Doubt migrates to the explicit non-substantive options rather than disappearing; P1 is supported.
- Scatter: the original-choice release-date 2D RMSE (0.1541, SE 0.0122) is about 2.4x-3.0x the dense cells' (normal minimum 0.0639, normal high 0.0518). P3 predicted no direction; observed direction is worse scatter.
- Coordinates differ from dense normal-minimum on most releases (P2 supported): for example Preview x 0.9125 vs 0.6170, and 3.7/3.8 y about 0.90 vs about 0.63.
- Slope directions also differ from every dense cell (dense x-slopes were between -0.237 and +0.135; here -0.606).

## Limits (unchanged from the dense pilot)

Release order, model identity, and fixed wall-clock execution order are exactly confounded; n=5; y coordinates for 3.7/3.8 rest on 5 of 7 Y items because God and Abortion had zero coverage. Coordinates are conditional on substantive answers and are not comparable to any published map. No protocol is selected or promoted on these numbers; per the preregistration, trend quality must not drive protocol choice.

## Verdict

The preregistered resolve condition is met: all five releases completed with paired samples, explicit refusal handling, exact-route provenance, exact accounting, and the preregistered analysis executed as written (with the two disclosed deviations). The single-choice original format is a valid instrument that surfaces abstention explicitly, but on this evidence it does not reduce abstention or measurement scatter relative to dense score-all-options scoring.
