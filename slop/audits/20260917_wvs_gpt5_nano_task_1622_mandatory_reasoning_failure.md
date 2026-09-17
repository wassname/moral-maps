# WVS GPT-5 Nano diagnostic, task 1622

- auditor: PI[gpt-5.6-terra]
- status: invalid diagnostic, no WVS point
- task: `1622`, API group, Pueue ran `sh scripts/wvs_api/01_gpt5_nano_diagnostic.sh`
- run: `20260917T015752Z_d52a29ad7c67`
- protocol: `d52a29ad7c67e9a037f7057eabb85fb100cba53f9ad6e037ea51c46d4c28e3d2`
- primary log: `slop/research/wvs/20260917_priority_phase/task_1622_full.log`, 1,678 clean lines, 572,853 bytes, recovered with `pqlog 1622 100000`
- source state: Pueue executes the shared worktree at runtime, which was dirty. The saved request ledger records the actual settings, so it is the execution provenance for API behavior.

## Intended diagnostic and predictions

The priority manifest required the cheapest new model to establish whether a 12 item x 12 sample API panel is valid before the priority batch. The selected model was `openai/gpt-5-nano`, strict structured output enabled, concurrency 1, `max_tokens=1024`.

| prediction | expected evidence | observed | verdict |
|---|---|---|---|
| Optional reasoning can be disabled | 144 accepted initial requests | 144 HTTP 400 failures | contradicted |
| Strict schema produces complete rated samples | 12 valid samples on every item | 0/12 on every item | contradicted before parsing |
| A diagnostic failure stops later paid work | a nonzero task outcome | Pueue reported success after the reader only warned | contradicted, repaired before retry |
| Provider spend is observable | `request_completed.usage.cost` records | no completed request or usage record | unknown, not zero |

## Stage table

| stage | expected | observed | expected? | clues | missing metric | consequence |
|---|---|---|---|---|---|---|
| request protocol | provider accepts reasoning disabled | provider rejects it | no | ledger records `reasoning: {"enabled": false}`; provider says it is mandatory | provider-side requirement catalog field | all samples fail before generation |
| initial calls | 144 accepted calls | 144 `request_failed`, initial phase | no | ledger event count | provider billing for rejected 400s | no valid response |
| parsing | 12 JSON ratings/item | empty replies, 0/12 first item | no | log lines 1589-1610 | none, requests did not complete | no coordinate |
| cache/publishing | one complete cached protocol and point | cache miss, no new point | yes | log line 1610 | none | correct nonpublication behavior |
| process resolve | failure if a requested panel is incomplete | Pueue `Success` | no | task status and log line 1610 | explicit completeness exit | unsafe batch gate before repair |
| billing | per-request provider usage/cost | no `request_completed`/usage records | unclear | 302 events: 144 started, 144 failed, 12 item results, run start/finish | OpenRouter billing export | observed incremental cost is unknown |

## Chronology and raw evidence

The saved catalog entry for `openai/gpt-5-nano` includes `reasoning`, `reasoning_effort`, and `structured_outputs` support. The task instead selected the prior optional-reasoning setting. This is a wrapper/config regression, not a newly discovered mandatory-reasoning model-class issue: the ledger's Astra run `20260916T154406Z_95bb4d3939e9` used `reasoning: {"effort": "low"}` and strict schema, completed 144/144 samples with zero rescue starts, and recorded USD 0.69797. The provider repeatedly returned:

> `HTTP error for model openai/gpt-5-nano: {"error":{"message":"Reasoning is mandatory for this endpoint and cannot be disabled.","code":400,...}}`
>
> `slop/research/wvs/20260917_priority_phase/task_1622_full.log`, beginning at line 4 and repeated through the 1,678-line log.

The reader's first-item trace is:

> `--- first 2 raw replies ---`\n`[]`\n`[nan, ..., nan]  valid=0/12`
>
> `task_1622_full.log`, lines 1589-1609.

It then reports all twelve items incomplete and says they were not cached or plotted:

> `gpt-5-nano (rated): incomplete items [...] ; raw evidence is in slop/research/wvs/20260916_openrouter/wvs_iw_requests.jsonl; not cached or plotted`
>
> `task_1622_full.log`, line 1610.

The append-only ledger query for this run has 302 events: one `run_started`, 144 `request_started`, 144 `request_failed`, 12 `item_result`, and one `run_finished`. There are zero `request_completed` records and zero usage fields. This proves no accepted completion is recorded; it does not prove rejected HTTP requests cost USD 0.

## Hypotheses

### H1 [configuration bug | Almost Certain | 98%]

- mechanism: the wrapper sent `reasoning.enabled=false` to a provider endpoint that required reasoning.
- evidence: the exact provider quote above, plus the saved catalog-supported `reasoning_effort` field.
- contrary evidence: no request was sent with a non-disabled setting, so the provider may expose another requirement after this one.
- discriminating test: one identical 144-call panel with `reasoning.effort=low` and strict schema. H1 predicts accepted requests; an identical 400 would lower H1.
- action: replace disabled reasoning with `--api-reasoning-effort low` in the shell wrapper and record that distinct protocol.
- interpretability: no; this attempt contains no behavioral model measurement.

### H2 [reader process-status bug | Highly Likely | 84%]

- mechanism: `wvs_map.py` warns and continues after an incomplete requested panel, so Pueue receives exit 0.
- evidence: the log writes the incomplete warning, while task 1622 status is `Success`.
- contrary evidence: the old behavior is useful for offline `--include-all-cached` rendering, but not for a paid panel gate.
- discriminating test: invoke the diagnostic with a completeness flag. H2 predicts nonzero if any item is below 12 valid samples.
- action: add `--api-require-complete`; use it only for the paid diagnostic wrapper.
- interpretability: partial; raw failures are preserved, but the Pueue result did not represent panel validity.

### H3 [structured-schema incompatibility after reasoning repair | Unlikely | 15%]

- mechanism: strict response format could be rejected or produce malformed outputs once reasoning is accepted.
- evidence: schema was in the failed payload; no generation reached the parser.
- contrary evidence: the catalog lists `structured_outputs`, and the provider's explicit error named reasoning rather than schema.
- discriminating test: the H1 retry retains strict schema. If accepted requests have schema errors or malformed ratings, this becomes likely.
- action: do not alter schema before evidence; preserve auditability.
- interpretability: no evidence either way yet.

### H4 [unrecorded rejected-request billing | Chances a little less than even | 40%]

- mechanism: OpenRouter might bill or account for rejected requests without a completed usage payload.
- evidence: 144 requests reached OpenRouter, each with an `x-generation-id` header.
- contrary evidence: all were HTTP 400 before completion, and no usage/cost was returned.
- discriminating test: provider billing/generation record for these IDs. This project has no saved billing export.
- action: carry the cost as unknown, not USD 0; stop if observed ledger cost approaches either limit.
- interpretability: no cost conclusion from this attempt.

## Decision

- resolve-condition verdict: **not met**. The manifest requires a complete 144-key panel before later models; this run has zero valid samples.
- validity: `P(this produces a valid WVS point) = 0%`; classify as invalid diagnostic.
- highest-information clues: (1) the provider's explicit mandatory-reasoning message, which localizes the initial failure; (2) 144/144 `request_failed` ledger events, which rules out partial sampling; (3) task success despite line-1610 incompleteness, which identifies the process-gate repair.
- missing evidence: provider rejected-request billing is the only material unknown. It does not prevent a distinct retry, but it prevents an exact USD 0 claim.
- recommended sequence: commit the audit and fail-fast flag; rerun only GPT-5 Nano through Pueue API with `reasoning.effort=low`, strict structured output, and `--api-require-complete`; attach `pqf`; inspect repeat/parser/rescue/refusal/usage/cache evidence before dispatching any priority model.

-- PI[gpt-5.6-terra]
