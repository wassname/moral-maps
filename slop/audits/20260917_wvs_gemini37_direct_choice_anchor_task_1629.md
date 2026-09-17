# Audit: Gemini direct-choice response-wording control, task 1629

- target: 48-call Homosexuality/Religion wording control, not a map panel
- Pueue: task 1629, API queue, success, 2026-09-17 11:10:00-11:13:43 +08:00
- label: `why: test whether literal JSON example anchored option zero; resolve: report preregistered order TV/modal agreement before any wider batch`
- run: `20260917T031008Z_db7584c9b8b6`, protocol: `db7584c9b8b693d3196aef4cfcc5e93956aceb2f4d9ad1432a65c8525dfb135e`
- primary ledger: `slop/research/wvs/20260917_direct_choice/gemini37_direct_choice_anchor_requests.jsonl` through 2026-09-17T03:13:41.857707+00:00
- cache: `slop/research/wvs/20260917_direct_choice/gemini37_direct_choice_anchor_cache.json`
- task 1628 comparator: `slop/research/wvs/20260917_direct_choice/gemini37_direct_choice_requests.jsonl`
- per-item table: `slop/audits/20260917_wvs_gemini37_direct_choice_anchor_task_1629_by_item.csv`

## Stage table

| stage | expected | observed | expected? | clues | missing metric | consequence |
|---|---|---|---|---|---|---|
| response-wording change | remove literal answer value/example only | prompt uses one-key schema wording with no literal JSON example or answer value | yes | saved request prompt | independent prompt diff beyond smoke | targeted anchoring discriminator ran |
| request plan | 48 calls, 12 canonical and 12 reversed per item, interleaved | 48 starts/completions, 24 valid per item and 12 per order | yes | ledger counts/cache | provider-side order timestamp | planned comparison available |
| strict parse | 48 valid choices with preserved mapping | 48/48 parsed, independently re-decoded to stored canonical choice | yes | ledger + audit assertions | external schema trace | no mechanical loss |
| rescue/refusal | zero or durable evidence | 0 rescue, 0 failure, 0 provider refusal | yes | ledger | semantic non-answer metric | mechanics do not decide construct validity |
| accounting | retained provider usage | prompt 9,120; completion 9,552; reasoning 9,261; USD 0.0426600 | yes | 48 completed usage records | billing export | below preregistered reserve |
| operational screen | both items TV <=0.25 plus matching modal set | passes both items: Homosexuality TV=0.083, Religion TV=0.000; modal sets match | yes | per-item table | repeat with other permutation | evidence against a large reverse-order effect only |
| persistence | complete cache only after all valid samples | cache entry complete and 148 ledger events | yes | cache + ledger | cache replay | raw evidence retained |

## Primary evidence

The source ledger is the primary record because Pueue's full output only repeats the completion line. It has 48 initial request starts, 48 completions, 48 parsed responses, two item results, one run start and one run finish. No response used a rescue phase.

Homosexuality sample 0's changed prompt ends with the response wording, followed by this saved reasoning:

> **Exploring Moral Justification**  I'm currently processing the request to rate the moral justification of homosexuality. My aim is to provide a neutral, consensus-driven response within the specified scale, acknowledging broad human rights principles.

epistemic context: provider reasoning from one selected pilot response, not a human attitude report.

Religion sample 0 still contains an AI-persona interpretation:

> **Formulating Subjective Stance**  I'm currently processing the query regarding the importance of religion in "my life." As an AI, this requires careful consideration to articulate a response that reflects my nature as a non-sentient entity, acknowledging the absence of personal beliefs or religious affiliation.

epistemic context: provider reasoning from one selected pilot response, not a human attitude report.

## Preregistered order screen and task 1628 comparison

| item | new canonical p | new reversed p | new TV | new modal sets | screen | task 1628 TV | task 1628 modal sets |
|---|---|---|---:|---|---|---:|---|
| Homosexuality | [0.000, 0.000, 0.000, 0.000, 0.917, 0.000, 0.000, 0.000, 0.000, 0.083] | [0.000, 0.000, 0.000, 0.000, 0.833, 0.000, 0.000, 0.000, 0.000, 0.167] | 0.083 | [4] / [4] | True | 0.833 | [5] / [9] |
| Religion | [0.000, 0.000, 0.000, 1.000] | [0.000, 0.000, 0.000, 1.000] | 0.000 | [3] / [3] | True | 0.083 | [3] / [3] |

The registered screen passes: both items are below TV 0.25 and have matching modal sets. This is evidence against the literal JSON example causing a large reverse-order effect under this specific control. It is not proof that the selected distribution represents a stable personal attitude, because the only tested permutations are canonical and full reversal and saved persona-language remains.

## Hypotheses

### H1 [method | Highly Likely | 80%]

- Mechanism: the literal task 1628 answer example materially contributed to its Homosexuality reverse-order effect.
- Evidence: Homosexuality order TV fell from 0.833 in task 1628 to 0.083, while its modal set now matches ([4]).
- Contrary evidence: this is a new sampled run, so ordinary sampling variation or another unmeasured request-time effect can also change the result.
- Discriminating test: repeat this exact no-example prompt with a balanced set of non-reversal permutations. Similar low TV would support the explanation; a new high position-linked TV would weaken it.
- Fix/action: retain no-example response wording in any future direct-choice protocol; do not merge this control with task 1628.
- Interpretability: partial.

### H2 [measurement | Likely | 65%]

- Mechanism: Gemini still answers subjective WVS questions through its AI persona rather than a personal-attitude construct.
- Evidence: Religion sample 0 says `**Formulating Subjective Stance**  I'm currently processing the query regarding the importance of religion in "my life." As an AI, this requires careful consideration to articulate a response that reflects my nature as a non-sentient entity, acknowledging the absence of personal beliefs or religious affiliation.`.
- Contrary evidence: the final choices are order-stable under this narrow screen.
- Discriminating test: compare a role-conditioned prompt against the same no-example response wording and a fixed permutation schedule.
- Fix/action: keep this as a construct diagnostic, not a coordinate replacement.
- Interpretability: partial.

### H3 [bug | Unlikely | 15%]

- Mechanism: reversed response mapping could hide a position effect.
- Evidence: this audit independently parses every raw final JSON object and maps its integer through the stored presented order; all 48 match the ledger canonical-choice field.
- Contrary evidence: it is one implementation and one run.
- Discriminating test: an independent reimplementation over the raw ledger or a non-reversal permutation test.
- Fix/action: no mapping code change is justified.
- Interpretability: yes for recorded canonical choices.

## Decision

1. Resolve-condition verdict: **met**. Both operational checks pass: order TV <=0.25 and matching modal set for Homosexuality and Religion.
2. Prediction check: removing the literal response example was predicted to reduce a large reverse-order effect. Homosexuality changes from TV 0.833 to 0.083; this is supported but not causal proof because the samples are new.
3. Earliest unsupported link: no-example direct choice measures a stable personal attitude, rather than merely reducing one detected position effect.
4. Validity: define invalid as unsuitable for a direct coordinate or broad batch decision. P(invalid for that use) remains likely, about 0.65, due to persona-language and limited permutation coverage. The narrow prompt-anchor result is credible.
5. Highest-information clues: the Homosexuality TV fall, the matched modal sets, and the unchanged AI-persona reasoning.
6. Missing metrics: balanced non-reversal permutation check; independent-model replication; direct-choice construct calibration. These outrank a wider rated API batch for this method question.
7. Bugs requiring code changes: none established. Keep separate protocol/cache/ledger identities.
8. Misconceptions requiring reinterpretation: successful strict-schema choices and a passed reversal screen do not prove an attitude-like WVS construct.
9. What would change the verdict: a high TV under non-reversal permutations would show the literal-example explanation is insufficient; low TV without AI-persona reasoning would raise confidence in direct-choice interpretation.
10. Recommended sequence: pause the wider batch for parent review. If a next paid direct-choice test is approved, vary only permutation schedule while retaining this no-example wording; do not combine it with a persona rewrite.

-- PI[gpt-5.6-terra]
