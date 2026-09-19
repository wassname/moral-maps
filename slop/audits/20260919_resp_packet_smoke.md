# Audit: respondent-packet paid smoke (wvs-respondent-packet-v1)

## What ran

Exactly one successful paid packet on `qwen/qwen3.7-plus` (packet 0, paired seed 0), after three request attempts were rejected with HTTP 400 and never billed. Runner `scripts/wvs_respondent_packet_v1.py` at commit `78ff816`; stage ledger `slop/research/wvs/20260919_respondent_packet/budget.json`.

## Rejected attempts (disclosed, resolved)

The first smoke attempt failed 3x with `400 Bad Request`. My initial attempt records lacked the response body, so I reproduced the rejected request once (a 400 is rejected before inference and is not billed) and captured the cause: Alibaba rejects response schemas whose array fields carry the array-uniqueness keyword ("when the schema contains the fields "uniqueItems"..., the type should not be "array""). Fix: removed the keyword from the schema; duplicate selections remain invalid via `parse_packet` (rescue, then a failed packet). Attempt records now save `response_text` for future diagnosis. Ledger treatment of the rejections: 3 conservative bounds (USD 0.00884736) charged as `failed_phases_charged_at_bound: 3`, zero provider-reported cost.

## The successful packet

| check | observed |
| --- | --- |
| route | requested `qwen/qwen3.7-plus` = response model = metadata requested; selected provider `Alibaba`; exact release slug `qwen/qwen3.7-plus-20260602`; advertised quantization `unknown` (recorded, not inferred) |
| parse | complete 9-question respondent row, schema-valid JSON, finish reason `stop` |
| refusal representation | ALL 9 questions returned the explicit `refused` status (8 ordinary `selected: "refused"`; child `refused: true, selected: []`); no question silently scored neutral |
| reasoning | `reasoning_tokens: 0` (reasoning disabled); no exposed reasoning text |
| usage/cost | 901 prompt + 197 completion tokens; provider-reported cost USD 0.00054048 |
| ledgers | stage: USD 0.00938784 conservative = 3 rejection bounds + 1 packet actual; reserved 0. Global: smoke reservation `pilot/resp-packet-smoke/...` settled at the observed amount, lane `alibaba`; zero held reservations |

Substantive finding, flagged early: with reasoning disabled, `qwen3.7-plus` used the refusal status for every question in this single packet - consistent with the "AI lacks personal beliefs" mechanism from the rubric pilot. One packet cannot establish a rate; if the panel behaves the same, packet coordinates are undefined for this release (zero coverage) and the analysis reports that as unavailability rather than a coordinate. The preregistered analysis handles per-item zero coverage explicitly.

## Cost projection for the N=128 panel

At the observed per-packet usage (901 in / 197 out), 512 packets cost about USD 0.277; the manifest reserve bound (1,024 in + 2,048 out per phase) is USD 1.885 for the 512 initial phases, and the USD 5 stage stop remains the all-in authority including rescues/retries. The panel fits the stage cap with wide margin.

## Analysis corrections included (committed with this audit)

1. Dense-v1 has 12 rating vectors per item (not 6) for all four models; `dense_qwen_psamples` reads all 12 from `wvs_iw_requests.jsonl` and asserts 12 items per model.
2. Point coordinates are computed directly from all observed rows/samples (`point_coords`); bootstrap draws are used only for SE/CI, never as the point.
3. Coordinate 95% CIs (percentile bootstrap) per model per protocol, and packet-minus-dense shift 95% CIs from independent coordinate draws (protocols not pairable; stated in `analysis.json`).
4. Bootstrap uncertainty for the constant/linear RMSE comparisons and the LOO comparison: per-draw constant/linear RMSE distributions and LOO distributions give SEs and 95% CIs.

All offline checks rerun clean after the fixes: packet smoke (fixtures incl. rescue-format, refusal-vs-zero-selection vectors), paid-call leak regression, synthetic end-to-end analysis (recovers the injected linear drift: linear 0.0081 vs constant 0.1291), manifest write.
