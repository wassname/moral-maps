# Revised Gemini Flash high-reasoning smoke audit

Target: the distinct `normal_high`, `max_tokens=2048` smoke for `google/gemini-3-flash-preview` on `research/gemini-flash-rubric-v1`.

| stage | expected | observed | expected? | source | consequence |
|---|---|---|---|---|---|
| protocol | High reasoning with fixed 2,048 output-token cap | High reasoning, 2,048 in request and protocol identity | yes | `paid_smoke_2048.jsonl:1-2` | Tests the amended condition |
| route | Pinned standard Google AI Studio release | `Google AI Studio`, exact slug `google/gemini-3-flash-preview-20251217` | yes | `paid_smoke_2048.jsonl:3` | Route accepted inline |
| response | Complete ratings without rescue | `finish_reason=stop`, complete ten-key JSON | yes | `paid_smoke_2048.jsonl:3-4` | Requirement met in this sample |
| parser | One valid sample | valid 1, failed 0, rescued 0 | yes | `paid_smoke_2048.jsonl:4-6` | End-to-end reader passed |
| reasoning and usage | Returned reasoning and full usage retained | 166 prompt, 1,535 completion, 1,494 reasoning, 1,701 total tokens | yes | `paid_smoke_2048.json:phases,usage_totals` | Provider-visible evidence retained |
| accounting | Actual cost settled locally and globally; no held reservation | revised smoke USD 0.004688, no matching reservation | yes | `paid_smoke_2048.json:budget,global_accounting` | No observed accounting leak |
| full panel | Must remain unqueued | Only three smoke phases in shared attempt ledger | yes | `request_attempts.jsonl` | Parent must approve before dispatch |

## Primary evidence

`paid_smoke_2048.jsonl:3` contains the complete provider response:

> `"finish_reason": "stop"` ... `"content": "{\"0\":1,\"1\":1,\"2\":2,\"3\":2,\"4\":3,\"5\":3,\"6\":4,\"7\":4,\"8\":5,\"9\":5}"` ... `"completion_tokens": 1535` ... `"reasoning_tokens": 1494` ... `"cost": 0.004688`

Epistemic context: this is the full response saved before parsing, not a later reconstruction.

The same record contains the selected route:

> `"requested": "google/gemini-3-flash-preview"` ... `"model": "google/gemini-3-flash-preview-20251217", "provider": "Google AI Studio", "selected": true`

`paid_smoke_2048.jsonl:4-6` records `parsed: true`, one valid sample, zero failures, and zero rescues. `paid_smoke_2048_run.log:21-25` quotes the complete raw rating object and `valid=1/1`, satisfying its only `SHOULD` line.

## ML-debug form

| row | answer |
|---|---|
| log and config | Complete 25-line log; resolved request settings in `paid_smoke_2048.jsonl:1-2` |
| null or baseline | Not applicable to this transport/parser smoke; no model-quality claim is made |
| one full sample | Prompt in `paid_smoke_2048_run.log:4-20`; raw output in lines 21-22 and JSONL line 3 |
| surprise | Reasoning still used 1,494 tokens, but the response stopped normally and included complete JSON |
| missing evidence | Truncation/rescue frequency across all items and releases |
| wall clock and GPU | About ten seconds from saved reservation/request timestamps; no GPU |
| fresh review | Pi quick oracle found no blocker before parent review and confirmed all 20 cells use 2,048 tokens, route/seed tests pass, accounting reconciles, and the full panel is unqueued |

The main operational number is zero rescues in one revised sample. A second cause besides the larger budget is sample-to-sample reasoning-length variation. Rescue counts across the full cells separate these explanations.

## Ranked hypotheses

### H1 [measurement | Likely | 65%]

- **Mechanism:** The fixed 2,048-token cap materially reduces condition-specific rescue in high-reasoning cells.
- **Evidence:** `paid_smoke_2048.jsonl:3` stops normally after 1,535 completion tokens, whereas the earlier 1,024-token smoke stopped for length.
- **Contrary evidence:** This is one item and one release.
- **Discriminating test:** Record rescue fractions by cell during the bounded pilot.
- **Action:** Keep phase counts and do not infer a population rate from this smoke.
- **Interpretability:** partial.

### H2 [harness | Highly Unlikely | 8%]

- **Mechanism:** A wrong provider/release is accepted despite the requested lock.
- **Evidence:** The route validator matched requested model, response model, selected provider, and dated slug before the caller accepted the response.
- **Contrary evidence:** Only one release has paid confirmation; the other four rely on fail-fast runtime checks.
- **Discriminating test:** The first response for each release must pass the same validator.
- **Action:** Keep inline validation on every paid phase.
- **Interpretability:** yes for this smoke.

### H3 [bug | Highly Unlikely | 8%]

- **Mechanism:** A paid phase is omitted from the local or repository-wide ledger.
- **Evidence:** The attempt record reserves USD 0.007168 and settles USD 0.004688; summary and global external accounting record the same actual amount with no held reservation.
- **Contrary evidence:** A real route mismatch was not purchased; that settlement path is covered offline.
- **Discriminating test:** Reconcile all raw `usage.cost` values after any future run.
- **Action:** Retain append-only attempt and global reservation records.
- **Interpretability:** yes for this smoke.

## Decision

**Resolve-condition verdict: met.** The revised high-reasoning smoke returned parse-valid JSON without rescue, on the exact pinned route, with complete reasoning/usage and reconciled accounting.

**Prediction check:** The operational prediction that the larger fixed cap can avoid rescue is supported in this sample. Scientific coordinate, rubric, and release-trend predictions remain unresolved.

**Earliest unsupported link:** One smoke does not establish the all-item rescue rate; condition-level phase counts are required.

**Validity:** Invalid means the revised smoke did not exercise or faithfully record the reviewed protocol. I estimate `P(smoke mechanics are invalid) = 0.02-0.06`; this is a credible mechanics result, not a values result.

**Highest-information clues:** normal stop with complete JSON; exact dated Google route; exact local/global cost reconciliation.

**Missing metrics:** rescue rate by condition, reasoning-token distribution by item, and first-call confirmation for the other releases.

**Bugs requiring code changes:** None demonstrated. Both the actual rescue request and its `request_started.payload` contain the paired seed; the offline capture records both phases.

**Misconceptions requiring reinterpretation:** USD 16.220160 is the initial-request bound, not a rescue/retry worst case. The USD 20 runtime stop is the spending bound.

**Recommended sequence:** Amend and push the research branch, report this smoke, and keep the full run unqueued until the parent inspects it.

-- PI[gpt-5.6-terra]
