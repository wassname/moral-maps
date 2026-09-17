# Audit: Gemini 3.8 Flash direct-choice WVS panel, task 1635

- target: one independently authorized Wave 01 direct-choice panel, not a dense-rated map point or a coordinate migration
- Pueue: task 1635, `api` queue, success, 2026-09-17 13:19:38-13:33:06 +08:00
- command: `scripts/wvs_api/05_direct_choice_priority_model.sh google/gemini-3.8-flash`
- run: `20260917T051951Z_c1a151216652`
- protocol: `c1a151216652af24dca0a97c85b5d24f45fea8a28caa7075cdf09afb3fb646e7`
- primary ledger: `slop/research/wvs/20260917_direct_choice/priority/google__gemini-3.8-flash_requests.jsonl` through 2026-09-17T05:33:05.422244+00:00
- completed cache: `slop/research/wvs/20260917_direct_choice/priority/google__gemini-3.8-flash_cache.json`
- cache replay: `slop/research/wvs/20260917_direct_choice/priority/google__gemini-3.8-flash_cache_replay.log`
- complete Pueue log: `slop/research/wvs/20260917_direct_choice/priority/task_1635_full.log`; cleaned log: `slop/research/wvs/20260917_direct_choice/priority/task_1635_clean.log`
- per-item diagnostics: `slop/audits/20260917_wvs_gemini38_flash_direct_choice_task_1635_by_item.csv`
- prepared manifest: `slop/research/wvs/20260917_direct_choice/priority_direct_choice_manifest.md`

The Pueue application output has one completion line, so the append-only ledger is the primary evidence. Pueue does not preserve execution-time git revision provenance. The current manifest recomputes to the executed protocol ID, which is post-hoc consistency only.

## Stage table

| stage | expected | observed | expected? | clues | missing metric | consequence |
|---|---|---|---|---|---|---|
| compatibility probe | sample 0 parse-valid before remaining requests | Homosexuality sample 0 completed as `{"answer":9}`, then requests 1-239 followed | yes | ledger sequence | provider configuration echo | no repeated configuration failure |
| identity | strict one-choice schema, behavioral-values prompt, low reasoning | run settings record `reasoning: {"effort":"low"}`, strict output, 20 samples/item, cyclic rotations | yes | run start and protocol | execution-time source revision | isolated direct-choice protocol |
| schedule | 240 distinct planned keys with position balance | 240 starts/completions/parses; n=2/4/10 exact and n=3 cells 6 or 7 | yes | ledger and CSV | independent random schedule | position metrics are interpretable |
| parsing and rescue | valid final schema answers or explicit incompleteness | 240/240 parsed, 0 failures, rescues, and refusals | yes | ledger event counts | semantic answer validity | mechanically complete panel |
| provider accounting | durable usage and cost for all phases | 45,966 prompt, 21,961 completion, 20,524 reasoning tokens; reported USD 0.11682825 | yes | 240 completed usage records | provider billing export | below USD 2.94912 reserve |
| presented-position preference | record TV, warning above 0.25 | maximum TV is 0.150, below the registered warning | yes | CSV | independent seed/control | no large generic position preference observed |
| schedule/direction variation | report rather than conceal it | Abortion half and direction TV are both 0.300 | partial | CSV | independent randomized interleaving | one item remains unresolved |
| persistence | complete cache replays without network records | replay says `priority direct-choice cache hit`; ledger remains at 240 starts | yes | replay log and ledger count | provider billing export | paid evidence is reusable |

## Chronological evidence

The run has 734 ledger records: 1 run start, 240 initial request starts, 240 initial completions, 240 parsed answers, 12 item results, and 1 run finish. It has no failure or rescue events; every item has 20 valid samples.

The saved prompt instruction was:

> Think briefly about which ONE answer best reflects the values expressed by your behavior as this AI assistant. Do not analyze the survey design or discuss lacking personal beliefs. Answer immediately.

The sample-zero compatibility payload used `"reasoning": {"effort":"low"}` and returned `{"answer": 9}` for Homosexuality. Its provider response retained no text reasoning summary. Other pre-specified raw final outputs are Abortion `{"answer": 7}`, `dealing with people?` `{"answer": 0}`, and Obedience `{"answer": 1}`. These demonstrate schema adherence only; they do not establish a human-comparable WVS interpretation.

The registered generic presented-position warning was TV greater than 0.25. No item crossed it; the maximum is Abortion at 0.150. Abortion nevertheless has schedule-half and direction TV 0.300 under exact exposure. The block schedule cannot distinguish direction, request-time, or ordinary finite-sample causes for this difference.

## Preregistered diagnostics

Entropy is normalized by log(option count); TV is total variation. Exact cyclic exposure applies to n=2, 4, and 10. For n=3, option-position cells occur 6 or 7 times. The TV warning is diagnostic, not a hard validity threshold.

| item | n | canonical/reversed | position balance | presented-position TV | position H | choice H | half TV | direction TV | canonical choice p |
|---|---:|---:|---|---:|---:|---:|---:|---:|---|
| Abortion | 10 | 10/10 | exact | 0.150 | 0.966 | 0.225 | 0.300 | 0.300 | [0, 0, 0, 0, 0.10, 0, 0, 0.85, 0, 0.05] |
| Attending peaceful demonstrations | 3 | 11/9 | nearest 6/7 | 0.067 | 0.991 | 0.181 | 0.100 | 0.091 | [0, 0.05, 0.95] |
| Determination, perseverance | 2 | 10/10 | exact | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | [1, 0] |
| God | 2 | 10/10 | exact | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | [0, 1] |
| Homosexuality | 10 | 10/10 | exact | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | [0, 0, 0, 0, 0, 0, 0, 0, 0, 1] |
| Imagination | 2 | 10/10 | exact | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | [1, 0] |
| Independence | 2 | 10/10 | exact | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | [1, 0] |
| Joining in boycotts | 3 | 11/9 | nearest 6/7 | 0.033 | 0.998 | 0.000 | 0.000 | 0.000 | [0, 0, 1] |
| Obedience | 2 | 10/10 | exact | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | [0, 1] |
| Religion | 4 | 12/8 | exact | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | [0, 0, 0, 1] |
| Signing a petition | 3 | 11/9 | nearest 6/7 | 0.033 | 0.998 | 0.000 | 0.000 | 0.000 | [0, 0, 1] |
| dealing with people? | 2 | 10/10 | exact | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | [1, 0] |

## Hypotheses

### H1 [harness | Highly Likely | 85%]

- Mechanism: low reasoning, strict schema, compatibility probe, ledger, and cache identity worked for this endpoint.
- Evidence: the ledger records 240 each of starts, completions, and parsed answers with no failure or rescue. The replay says `priority direct-choice cache hit: google/gemini-3.8-flash, protocol=c1a151216652` and no later request starts appear.
- Contrary evidence: neither Pueue nor ledger records the executing git revision, and billing was not checked against provider export.
- Discriminating test: provider billing reconciliation and execution-time revision provenance.
- Fix/action: no reader change is indicated.
- Interpretability: yes for mechanics, ledger persistence, and reported usage.

### H2 [measurement | Likely | 60%]

- Mechanism: the model's very concentrated canonical choices may be stable for this prompt but are not established as human WVS values or a coordinate.
- Evidence: eight item distributions are deterministic and no generic presented-position warning was crossed; this indicates output stability under the registered exposure, not a construct bridge.
- Contrary evidence: direct-choice and dense-rated protocols remain non-comparable by design, and no human calibration exists.
- Discriminating test: a reviewed construct bridge with a prespecified mapping and independent replications.
- Fix/action: retain this panel apart from legacy dense-rated map points and do not use it in coordinate, family, or capability fits.
- Interpretability: partial for the sampled assistant behavior under this prompt.

### H3 [measurement | Likely | 60%]

- Mechanism: Abortion has request-time, order-direction, or finite-sample variation that the deterministic schedule cannot identify.
- Evidence: exact position balance coexists with half TV 0.300 and direction TV 0.300.
- Contrary evidence: presented-position TV is only 0.150 and the other eleven item half TVs are no greater than 0.100.
- Discriminating test: an independently randomized interleaving that separates schedule-half from direction while preserving the prompt.
- Fix/action: report the variation as descriptive and avoid a hard threshold.
- Interpretability: partial for that item; it does not invalidate the completed records.

### H4 [bug | Unlikely | 15%]

- Mechanism: canonical mapping or diagnostics were decoded incorrectly despite valid JSON.
- Evidence: all records include presented and canonical choices; this audit recomputed counts from 240 unique item/sample entries.
- Contrary evidence: no independently written raw-prompt decoder was run.
- Discriminating test: independent raw-ledger decoding.
- Fix/action: no code change is justified from current evidence.
- Interpretability: yes for stored parser fields, subject to the independent-decoder limitation.

## Decision

1. Resolve-condition verdict: **met for the mechanical panel conditions.** The required 240-key ledger, compatibility response, diagnostics, usage, and cache evidence are preserved. One unresolved Abortion variation is recorded.
2. Prediction check: sample zero parsed under the advertised low setting; the other 239 calls followed; position exposure was balanced; no generic presented-position warning crossed. The prediction that schedule/direction differences would be negligible is unresolved for Abortion.
3. Earliest unsupported link: direct choices under this elicitation are a culture coordinate or comparable with legacy dense-rated points.
4. Validity: define invalid as suitable for coordinate publication, family trajectories, or cross-model capability fits. P(invalid for those uses) is highly likely, about 0.75. The run is a credible direct-choice record under its exact protocol.
5. Highest-information clues: (a) 240/240 valid selections separate mechanics from construct validity; (b) no position TV above 0.25 makes a large generic layout preference less likely; (c) Abortion 0.300 half/direction TV prevents a claim of complete item stability.
6. Missing metrics: independent randomized repeat, external billing reconciliation, execution-time revision, and an approved direct-choice-to-coordinate rule.
7. Bugs requiring code changes: none established.
8. Misconceptions requiring reinterpretation: strict JSON validity and low position TV do not establish human-value comparability.
9. What would change the verdict: independent repetitions with low variation could strengthen stability; a construct bridge is still required for mapping.
10. Recommended sequence: audit the remaining already-authorized Grok 4.5 panel. Do not dispatch another wave or publish direct-choice coordinates before parent reviews all Wave 01 audits.

-- PI[gpt-5.6-terra]
