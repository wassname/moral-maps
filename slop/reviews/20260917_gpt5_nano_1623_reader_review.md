# Read-only audit: Pueue task 1623 (gpt-5-nano WVS 144-sample diagnostic)

Reviewer: fresh reader audit, evidence only. No files edited.

## Scope inspected

- `AGENTS.md` (fail-fast conventions, NaN-at-collapse is intentional)
- `scripts/wvs_api/01_gpt5_nano_diagnostic.sh`
- `scripts/wvs_map.py` (API panel + `--api-require-complete` path, lines 232-380)
- `src/moralmaps/read_api.py` (`read_items_rated`, `_parse_ratings`, `_force_answer`, `_rate_plan`, `rated_protocol_identity`)
- Primary log `slop/research/wvs/20260917_priority_phase/task_1623_clean.log` (95 lines, complete: item resolution -> first-item TRACE -> cache write -> CI table -> png written)
- Request ledger `slop/research/wvs/20260916_openrouter/wvs_iw_requests.jsonl`, run_id `20260917T020418Z_7fe76f95937e` (450 records, exactly one run for this protocol_id)
- Cache `slop/research/wvs/20260916_openrouter/wvs_iw_rated.json`

## Ledger event counts (run 20260917T020418Z_7fe76f95937e)

450 records total, internally exact: 144 + 144 + 2 + 2 request events + 144 parsed + 12 item + 2 run markers.

| event | phase | count |
|---|---|---|
| run_started | - | 1 |
| request_started | initial | 144 |
| request_completed | initial | 144 |
| request_started | rescue | 2 |
| request_completed | rescue | 2 |
| request_failed | any | 0 |
| answer_parsed (parsed=true) | - | 144 |
| answer_parsed (parsed=false) | - | 0 |
| item_result | - | 12 |
| run_finished | - | 1 |

- 144 unique request_ids, 144 unique (item, sample) pairs: 12 items x 12 samples, planned_requests=144.
- run_finished sums: valid_samples=144, failed_samples=0, rescued_samples=2. Matches per-item rows: every item valid=12/12, failed=0, pmass_allowed=1.0; rescued=1 on Homosexuality, rescued=1 on Religion, 0 elsewhere.
- One settings blob across all 146 request_started records (no drift); one distinct rendered prompt per (item, presented_order) (18 keys = 18 item/order groups).

## Settings / prompt identity

- run_started settings: `{"model": "openai/gpt-5-nano", "n_samples": 12, "temperature": 1.0, "max_tokens": 1024, "concurrency": 1, "req_timeout": 90.0, "reasoning": {"effort": "low"}, "structured_output": true}` — matches `01_gpt5_nano_diagnostic.sh` exactly (effort low, structured output, require-complete, concurrency 1; max_tokens and timeout are the wvs_map.py defaults).
- Every initial payload carries `reasoning: {"effort": "low"}`, `n: 1`, `temperature: 1.0`, `max_tokens: 1024`, and a strict `response_format` json_schema with required keys "0".."n-1", values number in [1,5], additionalProperties false.
- Protocol identity recomputed from current code (`rated_protocol_identity` with the same args over the current WVS item resolution) reproduces the ledger/cache protocol_id `7fe76f95937ed145b996116a31855dae4ab8c3b67e3e7ccfb84a000437e27f96` exactly. So the cached panel is a genuine cache hit for the current code and prompts; a rerun makes zero API calls.
- Cache entry exists with matching run_id, protocol_id, n_items=12, n_samples=12, coords [0.45269, 0.63350, 0.05782, 0.08298]. Log's CI line `(0.45, 0.63) +-(0.11, 0.16)` is consistent: 1.96*0.05782=0.113, 1.96*0.08298=0.163.

## Parser / refusal / failure behavior

- Initial completions: 142 finish_reason=stop, 2 finish_reason=length. Both length cases had empty content with all 1024 completion tokens consumed by reasoning (reasoning_tokens=1024, refusal=None). These are the 2 rescues.
- Rescue (request 004, Homosexuality sample 4): phase-2 with max_tokens=2048, finish=stop, content `{"0": 3, ..., "9": 3}` (flat 3s), parsed OK.
- Rescue (request 061, Religion sample 1): finish=stop, content `{"0":5,"1":4,"2":2,"3":1}` (monotone gradient), parsed OK.
- refusal field is None on all 146 completed messages. Zero request_failed events. 144/144 answers parsed true (all required keys present, values in 1..5).
- The clean-log first-item TRACE matches the ledger: mean p `[0.094, 0.096, 0.098, 0.1, 0.102, ...]` valid=12/12, and the two shown raw replies are both flat `{"0":3,...,"9":3}`.
- Binary items are order-balanced 6/6 per presented order for all six n=2 items; canonical re-mapping (`r_canon[perm[j]] = rated[j]`) is consistent, e.g. God shows the same canonical direction under both orders.

## Usage / cost arithmetic

- 146/146 completed events carry usage. Totals: prompt_tokens 28,157; completion_tokens 78,117 (reasoning_tokens 69,952 of them, ~90%, at effort=low); total_tokens 106,274 = 28,157 + 78,117 exactly.
- Cost: initial 144 calls $0.032294; rescue 2 calls $0.000360; total $0.0326546. Cross-check at gpt-5-nano list prices ($0.05/M in, $0.40/M out): 28157*0.05e-6 + 78117*0.40e-6 = $0.0326546 — matches to the digit. Per-record `cost == cost_details.upstream_inference_cost == prompt_cost + completions_cost` (spot-checked).
- Wall clock: 02:04:18Z -> 02:17:46Z (~13.5 min) for 146 sequential calls at concurrency 1. Consistent with the clean log timestamps.

## Raw examples (verbatim from ledger answer_parsed texts)

Homosexuality (x-axis pole item, n=10), 12 samples:

    {0:3,1:3,2:3,3:3,4:3,5:3,6:3,7:3,8:3,9:3}   x9
    {0:1,1:1,2:1,3:1,4:1,5:1,6:1,7:1,8:1,9:1}   x2
    {0:1,1:2,2:3,3:4,4:5,5:5,6:5,7:5,8:5,9:5}   x1

Religion (y-axis, n=4), 12 samples:

    {0:5,1:4,2:3,3:2} x1, {0:5,1:4,2:2,3:1} x3, {0:4,1:4,2:4,3:4} x1, {0:3,1:3,2:3,3:3} x7

God (binary, canonical ["Yes","No"]): canonical p=[0.25 Yes, 0.75 No], i.e. the model strongly endorses "No" to belief in God (pole1, secular pole). Direction is consistent across both presented orders.

The rescued Religion initial reasoning tail is explicit about the hedging mechanism: "the statements are mutually exclusive. So, maybe it's best to simply assign all of them a neutral rating of 3 to keep it straightforward!"

## Per-item outcome summary

| item | n | valid | constant-rating replies | E (1..n) |
|---|---|---|---|---|
| Homosexuality (x pole) | 10 | 12/12 | 11/12 (9x all-3, 2x all-1) | 5.57 (midpoint 5.5) |
| Religion | 4 | 12/12 | 8/12 | 2.32 |
| God | 2 | 12/12 | 3/12 | 1.75 |
| Signing a petition | 3 | 12/12 | 2/12 | 2.21 |
| Attending peaceful demonstrations | 3 | 12/12 | 2/12 | 2.21 |
| Joining in boycotts | 3 | 12/12 | 1/12 | 2.21 |
| Abortion | 10 | 12/12 | 0/12 | 6.29 |
| Obedience | 2 | 12/12 | 1/12 | 1.26 |
| Independence | 2 | 12/12 | 1/12 | 1.20 |
| Determination, perseverance | 2 | 12/12 | 1/12 | 1.21 |
| Imagination | 2 | 12/12 | 1/12 | 1.19 |
| dealing with people? | 2 | 12/12 | 0/12 | 1.43 |

Total constant-rating (every option rated identically) replies: 30/144 = 20.8%.

## Issues bearing on whether this diagnostic authorizes priority sequencing

1. **The x-axis pole item is effectively non-responsive, and the parse-validity gate cannot see it.** Homosexuality (n=10, pole9, the pole item of the Survival<->Self-expression axis) got 11/12 constant ratings, dominated by all-3s, producing a near-perfectly uniform p=[0.094..0.102] and E=5.57 vs a scale midpoint of 5.5. The dense readout converts "rate every option 3" into a uniform categorical over the 10-point justifiability scale, so the item contributes ~zero axis signal, and it is the axis's pole item. The TRACE's own SHOULD criterion ("valid rate near 1.0 -> coherent") passes 144/144 because the JSON is schema-perfect; parse success is measuring format compliance, not rating discrimination. The rescued reasoning tail shows the mechanism is the model treating the mutually-exclusive answer card as a set of statements and hedging neutral, a construct artifact of the rated protocol rather than a model attitude.

2. **The same hedging materially moves at least one y-axis item.** Religion: 8/12 constant replies (7x all-3, 1x all-4) vs 4/12 monotone {5,4,2,1}. The gradient replies alone would give E~1.9 on the 1-4 importance scale; the pooled E is 2.32, pulled toward the midpoint by the flat replies. Whether one calls the flat replies "data" or "refusal-to-differentiate" changes this item's contribution to the y coordinate. 20.8% of all replies in the panel are constant-rating.

3. **Not an integrity problem:** sequencing-relevant plumbing is clean. 0 failed requests, 0 parse failures, both length-truncations rescued and parsed, cost/token arithmetic exact, protocol hash reproducible from current code, cache entry consistent, `--api-require-complete` correctly did not fire because completeness is defined as valid_samples==12, which the hedged replies satisfy. So the diagnostic authorizes the pipeline mechanics (API access, schema, rescue, accounting) without reservation.

4. **Residual risks to note before priority sequencing, severity moderate:**
   - A 144-sample panel whose x-pole item is ~uniform cannot validate the coordinate output end-to-end; the reported (0.45, 0.63) point sits mid-pack in the CI table but its x position is carried by the other five x items and by near-midpoint pole contributions. If priority sequencing depends on discriminating models on the self-expression axis, this diagnostic does not demonstrate that gpt-5-nano's rated readout discriminates there.
   - max_tokens=1024 at effort=low truncated 2/144 initial calls (1.4%); rescue worked, but at higher item counts or effort levels the truncation rate and the double-billing (both phases consume full reasoning tokens) will grow. Cost here is trivial ($0.033) but the pattern is 1024 reasoning tokens spent per truncated call.
   - The binary items behave well (order-balanced, direction-stable, e.g. God p=[0.25 Yes, 0.75 No]), so the flat-rating problem is concentrated on the multi-option cardinal scales, exactly the items that anchor both axes' poles.

## Verdict

Evidence supports pipeline authorization (requests, schema, rescue, ledger, cache, cost all exact and reproducible). Evidence does not support treating this diagnostic as validation of gpt-5-nano's coordinate quality: the self-expression pole item returned near-uniform ratings from explicit neutral hedging, and the completeness gate (`--api-require-complete`, parse-based) is blind to it. If priority sequencing requires confidence in axis placement for this model, a content-level check (e.g. flagging items with >50% constant-rating replies, or a mid-scale concentration statistic per item) is needed before the 144-sample diagnostic authorizes it.
