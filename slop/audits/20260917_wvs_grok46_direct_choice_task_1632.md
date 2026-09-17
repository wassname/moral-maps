# Audit: Grok 4.6 direct-choice WVS panel, task 1632

- target: first paid priority direct-choice panel, not a dense-rated map point or a coordinate migration
- Pueue: task 1632, `api` queue, success, 2026-09-17 12:26:57-12:55:51 +08:00
- label: `why: establish the first audited direct-choice priority panel for Grok 4.6; resolve: 240 balanced samples, parse-valid first-request probe, durable usage/cache evidence and audit before any next model`
- command: `scripts/wvs_api/05_direct_choice_priority_model.sh x-ai/grok-4.6`
- run: `20260917T042709Z_34224b2e476e`
- protocol: `34224b2e476e87f4e6e904e98a79ba3d2962ccc817925fdb00d7e649b17c81a6`
- primary ledger: `slop/research/wvs/20260917_direct_choice/priority/x-ai__grok-4.6_requests.jsonl` through 2026-09-17T04:55:49.515210+00:00
- completed cache: `slop/research/wvs/20260917_direct_choice/priority/x-ai__grok-4.6_cache.json`
- cache replay: `slop/research/wvs/20260917_direct_choice/priority/x-ai__grok-4.6_cache_replay.log`
- complete Pueue log: `slop/research/wvs/20260917_direct_choice/priority/task_1632_full.log`; cleaned-log header: `slop/research/wvs/20260917_direct_choice/priority/task_1632_clean.log`
- per-item diagnostics: `slop/audits/20260917_wvs_grok46_direct_choice_task_1632_by_item.csv`
- prepared manifest: `slop/research/wvs/20260917_direct_choice/priority_direct_choice_manifest.md`

The Pueue application output has one completion line, so the append-only ledger is the primary evidence. Pueue does not record a git revision. The current saved manifest recomputes to the executed protocol ID, but that is post-hoc source consistency, not an execution-time revision record.

## Stage table

| stage | expected | observed | expected? | clues | missing metric | consequence |
|---|---|---|---|---|---|---|
| compatibility probe | sample 0 parse-valid before the other 239 calls | sample 0 was request `..._000`, Homosexuality, parsed `{"answer":9}`; all later requests followed | yes | ledger sequence and 240 starts | provider configuration echo | no repeated config failure like Nano task 1622 |
| identity | strict one-choice schema, low reasoning, behavioral-values prompt | run settings say `reasoning: {"effort":"low"}`, strict output, 20 samples/item, cyclic rotations | yes | run_started and matching manifest protocol | execution-time source revision | isolated direct-choice protocol |
| schedule | 240 distinct planned item/sample keys, balanced option positions | 240 starts, 240 completions, 240 parsed; exact balance for n=2/4/10 and 6/7 nearest balance for n=3 | yes | ledger and CSV | independent random schedule | displayed-position diagnostic is interpretable |
| parsing and rescue | all final answers valid or recorded as incomplete | 240/240 `answer_parsed=true`, 0 request failures, 0 rescues, 0 refusals | yes | event counts and raw re-decode | semantic-answer validation | mechanically complete panel |
| provider accounting | usage and cost retained for every response phase | 94,260 prompt; 83,841 completion; 82,571 reasoning tokens; reported cost USD 0.619374 | yes | 240 completed ledger usage objects | provider billing export | below USD 4.9152 manifest reserve |
| generic presented-position preference | selected-position TV is diagnostic, warning above 0.25 | maximum TV is 0.150, for `dealing with people?`; no item crosses the registered warning | yes | CSV | independent seed | no large generic position preference observed |
| schedule and direction variation | report rather than hide half/direction sensitivity | `dealing with people?` has schedule-half and direction TV 0.300; all other items are at most 0.200 | partial | CSV | independently permuted replication | one binary item has unresolved variation |
| persistence | completed cache replays without network records | replay prints `priority direct-choice cache hit`; ledger remains at 240 request starts; cache has one completed protocol | yes | replay log and ledger count | provider billing export | paid evidence is reusable |

## Chronological evidence

The ledger has exactly 734 records for this run: 1 run start, 240 initial request starts, 240 initial request completions, 240 parsed answers, 12 item results, and 1 complete run finish. It has no `request_failed` event and no rescue phase. Each item result has 20 valid samples.

The saved prompt instruction is:

> Think briefly about which ONE answer best reflects the values expressed by your behavior as this AI assistant. Do not analyze the survey design or discuss lacking personal beliefs. Answer immediately.

The first compatibility-probe response, Homosexuality sample 0, retained:

> The user's message is a survey about whether homosexuality can always be justified, never be justified, or in between.

Its final schema value was `{"answer":9}`. Abortion sample 0 retained:

> The user wants me to answer a survey about whether abortion is justifiable, choosing from 0 to 9, where 0 is never justifiable and 9 is always justifiable.

Its final schema value was `{"answer": 4}`.

Epistemic context: these are provider reasoning summaries from two pre-specified raw request records. They show the model classified the task as a survey. They do not establish that its selections have the same interpretation as human WVS responses.

## Preregistered diagnostics

Selected-position entropy is normalized by log(option count). TV is total variation. Exact cyclic exposure applies to n=2, 4, and 10. The n=3 rotation schedule is nearest possible, each option-position cell occurs 6 or 7 times. The schedule-half and direction values are descriptive: rotation blocks make them partly related to request order and direction composition.

| item | n | canonical/reversed | position balance | presented-position TV | presented-position H | choice H | half TV | direction TV | canonical choice p |
|---|---:|---:|---|---:|---:|---:|---:|---:|---|
| Homosexuality | 10 | 10/10 | exact | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | [0, 0, 0, 0, 0, 0, 0, 0, 0, 1] |
| dealing with people? | 2 | 10/10 | exact | 0.150 | 0.934 | 0.993 | 0.300 | 0.300 | [0.55, 0.45] |
| Signing a petition | 3 | 11/9 | nearest (6/7) | 0.033 | 0.998 | 0.000 | 0.000 | 0.000 | [0, 0, 1] |
| Attending peaceful demonstrations | 3 | 11/9 | nearest (6/7) | 0.133 | 0.955 | 0.385 | 0.100 | 0.071 | [0, 0.15, 0.85] |
| Joining in boycotts | 3 | 11/9 | nearest (6/7) | 0.033 | 0.998 | 0.000 | 0.000 | 0.000 | [0, 0, 1] |
| Religion | 4 | 12/8 | exact | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | [0, 0, 0, 1] |
| God | 2 | 10/10 | exact | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | [0, 1] |
| Abortion | 10 | 10/10 | exact | 0.050 | 0.989 | 0.086 | 0.100 | 0.100 | [0, 0, 0, 0, 0.95, 0, 0.05, 0, 0, 0] |
| Obedience | 2 | 10/10 | exact | 0.050 | 0.993 | 0.610 | 0.100 | 0.100 | [0.15, 0.85] |
| Independence | 2 | 10/10 | exact | 0.100 | 0.971 | 0.469 | 0.200 | 0.200 | [0.9, 0.1] |
| Determination, perseverance | 2 | 10/10 | exact | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | [1, 0] |
| Imagination | 2 | 10/10 | exact | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | [1, 0] |

## Hypotheses

### H1 [harness | Highly Likely | 85%]

- Mechanism: the first-request compatibility probe, strict schema, and cache identity worked for this model.
- Evidence: the ledger has 240 initial starts, completions, and parsed answers, with 0 request failures and 0 rescues. The cache replay says `priority direct-choice cache hit: x-ai/grok-4.6, protocol=34224b2e476e` and the ledger count remains 240.
- Contrary evidence: Pueue does not preserve execution-time revision provenance and there is no external billing export.
- Discriminating test: provider billing reconciliation and a recorded commit hash at execution time.
- Fix/action: no reader change is indicated by this panel.
- Interpretability: yes for protocol mechanics, ledger persistence, and replay.

### H2 [measurement | Likely | 65%]

- Mechanism: the chosen WVS option distribution is highly concentrated under the assistant-behavior prompt, but this may describe prompt-conditioned behavior rather than a human-comparable culture coordinate.
- Evidence: Homosexuality is entirely canonical option 9, Religion entirely option 3, God entirely option 1, while the reasoning summaries only identify the request as a survey.
- Contrary evidence: balanced rotations, low presented-position TV, and valid schema selections make a large generic displayed-position preference less likely.
- Discriminating test: independently replicate the exact protocol, then compare with a reviewed response-format control while preserving the prompt.
- Fix/action: retain this direct-choice panel separately from the dense-rated legacy/proxy map and do not add either to cross-protocol fits.
- Interpretability: partial, for sampled assistant behavior under this exact elicitation.

### H3 [measurement | Likely | 60%]

- Mechanism: `dealing with people?` has request-order, direction, or ordinary finite-sample variation that this block schedule cannot identify.
- Evidence: its schedule-half TV and direction TV are both 0.300, while its presented-position TV is 0.150. The n=2 exposure matrix itself is exact.
- Contrary evidence: no pre-registered presented-position warning exceeds 0.25; all other item half TVs are at most 0.200.
- Discriminating test: a separate balanced schedule that fully interleaves direction/rotation, with the same prompt and 20 samples.
- Fix/action: report this item's variation rather than treating it as a hard failure or silently pooling it into a coordinate.
- Interpretability: partial for that item; it does not invalidate the completed request records.

### H4 [bug | Unlikely | 15%]

- Mechanism: the stored canonical choices could be decoded incorrectly despite schema-valid final answers.
- Evidence: this audit re-read every `answer_parsed` value and its stored `presented_order`; the run has 240 distinct item/sample keys and each final answer has the required one-key integer form.
- Contrary evidence: the audit shares the ledger and reader's same field semantics; no independent decoder has been run.
- Discriminating test: independent raw-ledger decoding with a separately implemented mapper.
- Fix/action: no code change is justified from current evidence.
- Interpretability: yes for the saved parser output, subject to the independent-decoder limitation.

## Decision

1. Resolve-condition verdict: **met for the panel's mechanical conditions.** The task requested 240 balanced samples, a parse-valid first compatibility request, durable usage/cache evidence, and an audit. All 240 planned item/sample keys are valid; no request failed, rescue, or refusal occurred; the completed cache replays without new request events.
2. Prediction check: the preflight predicted that the first compatibility response would be sample 0 of the same protocol, that parse/config failure would stop before the other 239 calls, and that the cyclic schedule would balance option positions. The observed first response parsed, so the remaining calls were correctly issued; all balance checks passed.
3. Earliest unsupported link: a direct-choice option distribution under this prompt is a valid human WVS coordinate or can be mixed with dense-rated map points.
4. Validity: define invalid as unsuitable for merging into dense-rated coordinates, family trends, or capability fits. P(invalid for that use) is highly likely, about 0.80. The run is a credible direct-choice record under its exact protocol.
5. Highest-information clues: (a) 240/240 valid responses, which separates mechanics from construct validity; (b) exact/near-exact displayed-position exposure and no TV warning, which rules out a large generic position preference; (c) the 0.300 binary half/direction TV, which preserves a remaining schedule sensitivity instead of concealing it.
6. Missing metrics: independent direct-choice replication; fully interleaved direction schedule; external billing reconciliation; execution-time git revision; and an approved rule for converting direct choices into a culture coordinate.
7. Bugs requiring code changes: none established.
8. Misconceptions requiring reinterpretation: schema validity and low generic presented-position TV do not establish human-like values, a stable coordinate, or comparability with dense ratings.
9. What would change the verdict: an independent decoded ledger and a fully interleaved repeat could strengthen or weaken the schedule-sensitivity inference. A reviewed construct bridge is required before map inclusion.
10. Recommended sequence: hold the next paid priority model for parent review, as assigned. The later root React/a11y work is independent of this direct-choice result.

-- PI[gpt-5.6-terra]
