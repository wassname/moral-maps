# Audit: DeepSeek reliability pilot task 1674

- Pueue task 1674 ran `sh scripts/wvs_api/07_deepseek_reliability_pilot.sh` from 21:38:41 to 22:31:21 +0800 and exited 1.
- full normalized Pueue log: 80/80 lines; raw log: 92 lines, both at `/tmp/wvs-audit-1674/`.
- scope: separate `wvs-score-all-options-v1` reliability records only. No canonical cache or Pages data changed.

| stage | expected | observed | expected? | consequence |
|---|---|---|---|---|
| pilot reservation | USD 1 pilot and global reservation released on exit | pilot `reserved_usd: 0`; global `reservations: {}` | yes | no stale budget block |
| first model replicate 0 | 288 valid ratings | 288/288, GMICloud, USD 0.01570740 | yes | retained separately |
| replicate 1 | 288 valid ratings | 288/288, GMICloud, USD 0.01578264 | yes | retained separately |
| replicate 2 | 288 valid ratings | 287/288, one `ReadTimeout` at `Attending peaceful demonstrations`, sample 10 | no | no N=72 aggregate for this model |
| remaining six models | continue after a model/replicate failure | not attempted because the runner raised | no | the task's continuation condition was not met |

## Evidence

The final replicate record says:

> `"event": "request_failed", "item_id": "Attending peaceful demonstrations", "sample": 10, "phase": "initial", "error_type": "ReadTimeout", "error": ""`
>
> `"event": "run_finished", "failed_samples": 1, "planned_requests": 288, "rescued_samples": 0, "valid_samples": 287`

The complete first two replicates have matching `run_finished` records with `valid_samples: 288`, `failed_samples: 0`, and `rescued_samples: 0`. The terminal traceback is:

> `RuntimeError: incomplete replicate deepseek/deepseek-chat-v3-0324 2`
>
> `File ".../scripts/wvs_deepseek_reliability_pilot.py", line 179, in run_replicate`

The measured raw response cost is USD 0.04716160: USD 0.01570740 + USD 0.01578264 + USD 0.01567156. The old pilot state recorded only the two completed replicates, USD 0.03149004, because the exception occurred before state reconciliation. It did release reservations in `finally`.

## ML-debug form, adapted to this API pilot

| row | answer |
|---|---|
| config in log | DeepSeek chat v3-0324; three separate 12-item x 24-sample replicate records; deterministic seed schedules; GMICloud responses |
| SHOULD line | `valid rate near 1.0 -> coherent`; observed 288/288, 288/288, then 287/288 |
| null/baseline | canonical v1 coordinate exists but no completed pilot aggregate can yet compare to it |
| full samples | each replicate's first item emitted bare parse-valid JSON; raw records retain all request payloads and responses |
| surprising event | one empty-message `ReadTimeout`, following 287 successful responses in replicate 2 |
| missing metric | whether OpenRouter executed the timed-out request; no receipt or usage record exists |
| second cause | a network timeout and a provider/model response failure both produce one missing sample; the raw record identifies only `ReadTimeout` |

## Hypotheses

### H1 [harness | Almost Certain | 95%]

- **Mechanism:** the runner treated one incomplete replicate as a process-level exception instead of retaining it and proceeding to later models.
- **Evidence:** the quoted traceback occurs immediately after the 287/288 final record; no files exist for the remaining six model directories.
- **Contrary evidence:** the original code did preserve the first two completed replicate records before failing.
- **Discriminating test:** re-read the three existing records without API calls. Expected result: statuses complete, complete, incomplete; no new request event.
- **Fix/action:** resume from durable `run_finished` records, label incomplete replicates, reconcile recorded cost, and continue later model/replicate work.
- **Interpretability:** yes, for the operational diagnosis.

### H2 [harness | Likely | 65%]

- **Mechanism:** the pilot state's USD 0.03149004 understated actual recorded spend because it increments only after a complete replicate returns.
- **Evidence:** the three raw record costs sum to USD 0.04716160 while `budget.json` contains USD 0.03149004.
- **Contrary evidence:** both the pilot and global reservations were correctly released, so the stale value did not leave the repository cap reserved.
- **Discriminating test:** reconcile state from every `request_completed` record before dispatch. Expected result: USD 0.04716160 before any new request.
- **Fix/action:** recompute pilot spend from durable records on resume.
- **Interpretability:** partial until reconciliation; it affects pilot accounting, not the raw response data.

### H3 [data | Chances a little better than even | 50%]

- **Mechanism:** the missing response is transient transport failure rather than a DeepSeek scoring incompatibility.
- **Evidence:** 863 other requests in this model's three replicates completed, including the same item in replicates 0 and 1.
- **Contrary evidence:** the timeout has no provider response, so the endpoint behavior is unobserved for that request.
- **Discriminating test:** not a silent retry. Keep this replicate incomplete and compare later completed model replicates; an owner-approved replacement protocol would be needed to estimate this model's N=72 aggregate.
- **Fix/action:** exclude the incomplete model aggregate for now.
- **Interpretability:** no aggregate claim for chat-v3-0324; the two complete replicate panels remain reusable reliability evidence.

## Decision

- **Resolve-condition verdict:** not met. The process did not produce seven model x three replicate results, and one failure stopped the remaining models.
- **Validity:** P(incomplete-replicate diagnosis is wrong) is Remote, about 5%; the raw record, run summary, and traceback agree. No numerical reliability conclusion is valid yet.
- **Recommended sequence:** resume using only durable completed records, mark chat-v3-0324 incomplete rather than replacing its schedule, and continue the other six models under the same USD 1 cap. Do not add any pilot result to the canonical cache or Pages.

-- PI[k3]
