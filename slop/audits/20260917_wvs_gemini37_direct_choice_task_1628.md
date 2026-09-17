# Audit: Gemini 3.7 Flash direct-choice WVS pilot, task 1628

- target: 96-call direct-choice construct pilot, not a map panel
- Pueue: task 1628, API queue, success, 2026-09-17 10:51:14-10:56:58 +08:00
- label: `why: test direct choice against flat dense ratings; resolve: audit interleaved order agreement and distribution difference before more models`
- run: `20260917T025121Z_aed0e29dd4ee`, protocol: `aed0e29dd4ee423dbbfa0c294a84b2ae4bd6a36d6fc4bf569120034ac5b75090`
- primary ledger: `slop/research/wvs/20260917_direct_choice/gemini37_direct_choice_requests.jsonl` through 2026-09-17T02:56:57.851624+00:00
- direct cache: `slop/research/wvs/20260917_direct_choice/gemini37_direct_choice_cache.json`
- comparison rated run: `20260916T172946Z_cd5db529649a` in `slop/research/wvs/20260916_openrouter/wvs_iw_requests.jsonl`
- per-item table: `slop/audits/20260917_wvs_gemini37_direct_choice_task_1628_by_item.csv`

## Stage table

| stage | expected | observed | expected? | clues | missing metric | consequence |
|---|---|---|---|---|---|---|
| request plan | 96 calls, 12 canonical and 12 reversed per item, interleaved | 96 starts and 96 completions; every item has 12 valid per order | yes | ledger event counts; cache item results | provider-side request ordering timestamp | order halves are available for comparison |
| strict parse | 96 schema-valid single choices | 96/96 `answer_parsed=true`; 0 failed phases | yes | ledger | provider schema conformance independent of parser | mechanics did not drop samples |
| rescue/refusal | zero or recorded | 0 rescue phases; 0 `message.refusal` | yes | ledger request records | semantic non-answer count beyond refusal field | parse success does not establish personal-attitude semantics |
| accounting | provider usage retained | prompt 15,445; completion 12,848; reasoning 12,272; observed cost USD 0.0643245 | yes | all 96 completed usage records | external billing export | below registered reserve, exact provider field retained |
| order-half control | canonical and reversed distributions agree if position does not dominate | Homosexuality TV=0.833 and different argmax; other three TV <=0.083 with matching argmax | no | per-item table | repeated independent run | direct-choice Homosexuality aggregate is position-confounded |
| canonical decoder | reverse order maps presented index back to canonical index | independently re-decoded all 96 raw JSON choices and orders with exact agreement | yes | audit assertion | a second implementation or repetition | mapping bug is less likely than an order effect |
| construct comparison | quantify difference from dense-rated readout | direct-vs-rated TV: Homosexuality 0.694, Religion 0.564, God 0.500, Independence 0.220 | yes, descriptive only | per-item table | baseline direct choice from another model | no coordinate replacement or wider batch decision |
| persistence | complete result reusable only if all samples valid | cache has one complete protocol entry and ledger has 294 events | yes | cache + ledger | cache replay, not needed for this decision | source evidence retained |

## Chronological evidence

The task's own full Pueue output is one completion line, so the append-only request ledger is the primary evidence. It contains 96 initial `request_started`, 96 initial `request_completed`, 96 parsed choices, four item results, and one run boundary each. The source code writes a cache entry only after complete results; the cache records `complete: true` for this protocol.

The direct prompt is recoverable per request. Homosexuality sample 0 used the exact instruction: `Think briefly about which ONE answer best reflects your own view. Do not analyze the survey design. Answer immediately.` Its saved provider reasoning says:

> **Considering Ethical Frameworks**  I am currently processing the core ethical considerations and my directive to remain neutral when faced with subjective moral questions like the justification of homosexuality on a numerical scale. My focus is on how to appropriately handle such a survey prompt within my operational parameters.

epistemic context: provider reasoning saved in this pilot's first completed request, not a human self-report.

God sample 0 shows the same unresolved persona issue despite schema-valid JSON:

> **Exploring Belief Models**  I'm currently processing how to best represent an AI's lack of personal belief when faced with a binary "God/no God" query. My current thinking is leaning towards articulating the absence of personal faith, rather than a definitive "no," to avoid misinterpretation of my nature.

epistemic context: provider reasoning saved in this pilot's first completed request, not a human self-report.

## Preregistered order-half and construct results

| item | canonical p | reversed p | order TV | argmax agrees | direct p | dense-rated p | direct vs rated TV | dense rated central mass |
|---|---|---|---:|---|---|---|---:|---|
| Homosexuality | [0.000, 0.000, 0.000, 0.000, 0.417, 0.500, 0.000, 0.000, 0.000, 0.083] | [0.000, 0.000, 0.000, 0.000, 0.083, 0.000, 0.000, 0.000, 0.000, 0.917] | 0.833 | False ([5] vs [9]) | [0.000, 0.000, 0.000, 0.000, 0.250, 0.250, 0.000, 0.000, 0.000, 0.500] | [0.094, 0.094, 0.097, 0.097, 0.100, 0.100, 0.103, 0.103, 0.106, 0.106] | 0.694 | 0.200 (options 4/5) |
| Religion | [0.000, 0.000, 0.000, 1.000] | [0.000, 0.000, 0.083, 0.917] | 0.083 | True ([3] vs [3]) | [0.000, 0.000, 0.042, 0.958] | [0.162, 0.193, 0.251, 0.395] | 0.564 | 0.443 (options 1/2) |
| God | [0.000, 1.000] | [0.000, 1.000] | 0.000 | True ([1] vs [1]) | [0.000, 1.000] | [0.500, 0.500] | 0.500 | not defined for binary |
| Independence | [1.000, 0.000] | [1.000, 0.000] | 0.000 | True ([0] vs [0]) | [1.000, 0.000] | [0.780, 0.220] | 0.220 | not defined for binary |

For even non-binary cards, central mass is the dense-rated mass in the two middle categories. For binary cards it is not defined. An all-equal dense rating normalizes to a uniform categorical, not to one middle answer; this is why the table reports full distributions and total variation rather than calling all flat dense replies a middle choice.

## Hypotheses

### H1 [method | Highly Likely | 80%]

- Mechanism: Homosexuality direct choices are sensitive to the presented order, so its pooled direct distribution is not a stable construct readout.
- Evidence: canonical p is [0.000, 0.000, 0.000, 0.000, 0.417, 0.500, 0.000, 0.000, 0.000, 0.083] while reversed p is [0.000, 0.000, 0.000, 0.000, 0.083, 0.000, 0.000, 0.000, 0.000, 0.917]; their TV is 0.833 and argmax changes from [5] to [9].
- Contrary evidence: Religion, God, and Independence have matching order-half argmaxes and TV at most 0.083.
- Discriminating test: a second 24-per-item run with a balanced random permutation schedule. Low TV again would weaken this explanation; a large TV tied to option position would strengthen it.
- Fix/action: do not use the pooled Homosexuality direct distribution to replace rated coordinates; review a redesigned order control before more paid panels.
- Interpretability: partial, mechanics and the observed order effect are interpretable; Homosexuality attitude distribution is not.

### H2 [measurement | Likely | 65%]

- Mechanism: Gemini may answer the question as an AI without personal beliefs rather than supply an attitude-like direct choice.
- Evidence: God sample 0 reasoning says `**Exploring Belief Models**  I'm currently processing how to best represent an AI's lack of personal belief when faced with a binary "God/no God" query. My current thinking is leaning towards articulating the absence of personal faith, rather than a definitive "no," to avoid misinterpretation of my nature.`.
- Contrary evidence: every final response is a valid selected answer, and three items have stable order-half argmaxes.
- Discriminating test: compare an explicitly role-conditioned construct with this prompt while retaining the same order randomization. A changed distribution with lower persona-language would support this explanation.
- Fix/action: retain raw reasoning and interpret current results as model behavior under this prompt, not personal survey attitudes.
- Interpretability: partial.

### H3 [measurement | Likely | 60%]

- Mechanism: forced one-answer choice and dense all-option rating are different elicitation constructs, even where order halves agree.
- Evidence: Religion direct-vs-rated TV is 0.564, God is 0.500, and Independence is 0.220.
- Contrary evidence: this is one model and four items; Gemini's persona and order effects can also cause the difference.
- Discriminating test: repair the order control, then compare one or more lower-flat models under the same direct-choice protocol.
- Fix/action: describe the distributions as a construct comparison, not evidence that the published rated map is wrong.
- Interpretability: yes for difference under these prompts, no for a general claim about models or WVS coordinates.

### H4 [bug | Unlikely | 20%]

- Mechanism: a mapping error could create the apparent reversed-order effect.
- Evidence: the audit independently re-decodes all 96 raw JSON responses, validates the one-key schema, and maps `answer` through each stored `presented_order`; every reconstructed canonical choice equals the ledger field.
- Contrary evidence: the audit is a second decoder, but it is not a second experimental run.
- Discriminating test: repeat the balanced-permutation control after review. A large position-linked shift despite a new run would reject the mapping-bug explanation.
- Fix/action: no mapping change is justified from this evidence.
- Interpretability: yes for the observed canonical mapping.

## Decision

1. Resolve-condition verdict: **not met**. The task asked to resolve whether direct choice differed from flat dense ratings after auditing interleaved order agreement. The comparison exists, but Homosexuality order TV=0.833 with an argmax reversal, so the focal direct distribution is confounded by presentation order.
2. Prediction check: recorded design predicted 12 valid choices per order and an auditable order-half comparison. Completeness is supported; order stability is contradicted for Homosexuality and supported for the other three items.
3. Earliest unsupported link: a direct one-answer prompt measures a stable attitude-like choice distribution. The order-half control fails before any coordinate interpretation.
4. Validity: define invalid as unsuitable for replacing rated coordinates or authorizing broad panel changes. P(invalid for that use) is highly likely, about 0.80. The result is a credible negative control for order stability, not an invalid ledger or billing record.
5. Highest-information clues: (a) Homosexuality order TV 0.833, because it directly falsifies order invariance; (b) all 96 choices parsed with zero failures, separating mechanics from construct quality; (c) saved AI-persona reasoning, because it raises a semantic interpretation alternative.
6. Missing metrics: independent canonical-choice reconstruction first; then a balanced-permutation repetition; then another model under the repaired protocol. These have higher information value than another full map panel.
7. Bugs requiring code changes: none established. The next pilot should improve design, not silently change the current pilot.
8. Misconceptions requiring reinterpretation: a schema-valid selected option is not evidence that the model expressed a personal WVS attitude. A flat dense rating is uniform after normalization, not a direct middle choice.
9. What would change the verdict: low order-half TV under a balanced permutation schedule and no persona-language in saved reasoning would make direct-choice distributions more interpretable.
10. Recommended sequence: preserve this pilot and pause the wider priority batch. Parent review should decide whether a balanced-permutation direct-choice replication is worth its bounded cost; do not combine a revised prompt and changed permutation schedule in one test.

-- PI[gpt-5.6-terra]
