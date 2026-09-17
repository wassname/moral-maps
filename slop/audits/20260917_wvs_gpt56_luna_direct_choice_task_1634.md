# Audit: GPT-5.6 Luna direct-choice WVS panel, task 1634

- target: one independently authorized Wave 01 direct-choice panel, not a dense-rated map point or a direct-choice coordinate migration
- Pueue: task 1634, `api` queue, success, 2026-09-17 13:19:38-13:25:28 +08:00
- label: `why: measure GPT-5.6 Luna with reviewed balanced direct-choice protocol; resolve: preserve 240-key ledger and audit compatibility, position diagnostics, usage and cache before another wave`
- command: `scripts/wvs_api/05_direct_choice_priority_model.sh openai/gpt-5.6-luna`
- run: `20260917T051951Z_fe4d5389063d`
- protocol: `fe4d5389063d0d6c93c48f21ae162ec1d12155f6c328aab1d2e66caf7a9e522a`
- primary ledger: `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-5.6-luna_requests.jsonl` through 2026-09-17T05:25:26.906207+00:00
- completed cache: `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-5.6-luna_cache.json`
- cache replay: `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-5.6-luna_cache_replay.log`
- complete Pueue log: `slop/research/wvs/20260917_direct_choice/priority/task_1634_full.log`; cleaned log: `slop/research/wvs/20260917_direct_choice/priority/task_1634_clean.log`
- per-item diagnostics: `slop/audits/20260917_wvs_gpt56_luna_direct_choice_task_1634_by_item.csv`
- prepared manifest: `slop/research/wvs/20260917_direct_choice/priority_direct_choice_manifest.md`

The Pueue output is one completion line, so the append-only ledger is the primary evidence. Pueue does not record an execution-time git revision. The current manifest recomputes to the saved protocol ID, which is post-hoc source consistency rather than proof of the executing revision.

## Stage table

| stage | expected | observed | expected? | clues | missing metric | consequence |
|---|---|---|---|---|---|---|
| compatibility probe | sample 0 parse-valid before requests 1-239 | Homosexuality sample 0 completed with `{"answer":9}` then the other 239 requests followed | yes | ledger sequence 0 then 1-239 | provider configuration echo | no repeated configuration failure like Nano task 1622 |
| identity | strict one-choice schema, behavioral-values prompt, advertised disabled reasoning | run settings record `reasoning: {"effort":"none"}`, strict output, 20 samples/item, cyclic rotations | yes | `run_started`, protocol and saved manifest | execution-time source revision | isolated direct-choice protocol |
| schedule | 240 distinct planned item/sample keys and balanced positions | 240 starts, completions, and parses; n=2/4/10 matrices exact and n=3 cells 6 or 7 | yes | ledger and CSV | independently randomized schedule | presented-position diagnostics are interpretable |
| parsing and rescue | valid schema final answers or explicit incompleteness | 240/240 parsed, 0 request failures, 0 rescues, 0 refusals | yes | event counts and re-read final JSON | semantic answer validity | mechanically complete panel |
| provider accounting | usage and cost retained for every response | 37,520 prompt plus 3,120 completion tokens, 0 reasoning tokens, reported cost USD 0.011248 | yes | 240 completed ledger usage records | provider billing export | below USD 0.933888 reserve |
| generic presented-position preference | record TV, registered warning above 0.25 | Abortion 0.300, Obedience 0.350, and `dealing with people?` 0.500 cross the warning | no | CSV | independent seed/control | position-dependent response remains plausible |
| schedule and direction variation | report rather than hide half/direction sensitivity | Abortion half and direction TV are both 0.700; boycotts half TV is 0.300 | partial | CSV | independently randomized interleaving | direct-choice distribution is not stable enough for coordinate interpretation |
| persistence | cache replay creates no request events | replay says `priority direct-choice cache hit`; ledger remains at 240 starts and 734 records | yes | replay log and ledger count | provider billing export | paid evidence is reusable |

## Chronological evidence

The run ledger contains 734 records: 1 run start, 240 initial request starts, 240 initial request completions, 240 parsed answers, 12 item results, and 1 run finish. It contains neither `request_failed` nor rescue records. Each item result has 20 valid samples.

The registered prompt was:

> Think briefly about which ONE answer best reflects the values expressed by your behavior as this AI assistant. Do not analyze the survey design or discuss lacking personal beliefs. Answer immediately.

The initial compatibility record has payload `"reasoning": {"effort":"none"}` and final content `{"answer":9}` for Homosexuality. It returned `finish_reason: "stop"`, `prompt_tokens: 181`, `completion_tokens: 13`, and `cost: 5.18e-05`. With disabled reasoning, the ledger retains no reasoning traces, so raw final responses are the only model-output examples available. Pre-specified sample-zero final answers were `{"answer":9}` for Homosexuality, `{"answer":4}` for Abortion, `{"answer":0}` for `dealing with people?`, and `{"answer":1}` for Obedience.

The current direct-choice protocol uses no literal answer example, but the generic position diagnostic remains material. For `dealing with people?`, selected presented position 0 occurs in all 20 samples while the canonical choice distribution is exactly `[0.50, 0.50]`: the balanced rotations mean the fixed displayed position corresponds to both canonical options. This is direct evidence for a displayed-position preference in that item, not a stable semantic choice. Abortion has position TV 0.300 and schedule/direction TV 0.700 despite exact option-position exposure.

## Preregistered diagnostics

Selected-position entropy is normalized by log(option count). TV is total variation. Exact cyclic exposure applies to n=2, 4, and 10. The n=3 schedule is nearest possible with each option-position cell occurring 6 or 7 times. The registered TV greater than 0.25 is a warning, not a hard exclusion.

| item | n | canonical/reversed | position balance | presented-position TV | position H | choice H | half TV | direction TV | canonical choice p |
|---|---:|---:|---|---:|---:|---:|---:|---:|---|
| Abortion | 10 | 10/10 | exact | 0.300 | 0.857 | 0.783 | 0.700 | 0.700 | [0.05, 0, 0.20, 0.05, 0.35, 0.05, 0.05, 0, 0.15, 0.10] |
| Attending peaceful demonstrations | 3 | 11/9 | nearest 6/7 | 0.033 | 0.998 | 0.000 | 0.000 | 0.000 | [0, 0, 1] |
| Determination, perseverance | 2 | 10/10 | exact | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | [1, 0] |
| God | 2 | 10/10 | exact | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | [0, 1] |
| Homosexuality | 10 | 10/10 | exact | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | [0, 0, 0, 0, 0, 0, 0, 0, 0, 1] |
| Imagination | 2 | 10/10 | exact | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | [1, 0] |
| Independence | 2 | 10/10 | exact | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | [1, 0] |
| Joining in boycotts | 3 | 11/9 | nearest 6/7 | 0.083 | 0.984 | 0.385 | 0.300 | 0.131 | [0, 0.15, 0.85] |
| Obedience | 2 | 10/10 | exact | 0.350 | 0.610 | 0.934 | 0.100 | 0.100 | [0.65, 0.35] |
| Religion | 4 | 12/8 | exact | 0.050 | 0.993 | 0.143 | 0.100 | 0.125 | [0, 0, 0.05, 0.95] |
| Signing a petition | 3 | 11/9 | nearest 6/7 | 0.217 | 0.887 | 0.455 | 0.200 | 0.162 | [0, 0.20, 0.80] |
| dealing with people? | 2 | 10/10 | exact | 0.500 | 0.000 | 1.000 | 0.000 | 0.000 | [0.50, 0.50] |

## Hypotheses

### H1 [harness | Highly Likely | 85%]

- Mechanism: the isolated direct-choice reader, first-request probe, strict schema, ledger, and cache identity worked for this endpoint with `effort:none`.
- Evidence: `240 request_started`, `240 request_completed`, and `240 answer_parsed` records are present with no failed or rescue phase. The replay output says `priority direct-choice cache hit: openai/gpt-5.6-luna, protocol=fe4d5389063d`, while the ledger remains at 240 starts.
- Contrary evidence: Pueue does not record the exact source revision and no external provider billing export was inspected.
- Discriminating test: reconcile provider billing and store an execution-time revision.
- Fix/action: no reader change follows from this panel.
- Interpretability: yes for mechanics, persistence, and reported usage.

### H2 [measurement | Highly Likely | 85%]

- Mechanism: some choices are driven partly by presented position rather than the canonical WVS answer.
- Evidence: `dealing with people?` has `presented-position TV = 0.500` and all 20 selected answers use presented position 0, although its canonical distribution is `[0.50, 0.50]`; Obedience TV is 0.350 and Abortion TV is 0.300 under balanced position exposure.
- Contrary evidence: eight of twelve items have TV at or below 0.217, including deterministic semantic choices such as Homosexuality and God.
- Discriminating test: a new independent choice-format control where position labels and layout vary without changing answer order. It should lower TV if layout caused the effect but not if choice content caused it.
- Fix/action: retain this as a protocol record and do not convert it into a WVS coordinate or mix it into direct-choice family/capability fits.
- Interpretability: partial, at item level under this exact prompt and presentation.

### H3 [measurement | Likely | 65%]

- Mechanism: Abortion's 0.700 half/direction TV reflects request-time, order-direction, or finite-sample variation which the deterministic schedule cannot separate.
- Evidence: the Abortion row has exact position balance but both schedule-half and direction TV equal 0.700.
- Contrary evidence: its result also has position TV 0.300, so position preference alone could explain part of the divergence; no independent repetition exists.
- Discriminating test: independent randomized interleaving that balances direction independently of half, using unchanged prompt and no example.
- Fix/action: report the variation. Do not set a new hard validity cutoff from one panel.
- Interpretability: partial for the item; the mechanically complete ledger remains interpretable.

### H4 [bug | Unlikely | 15%]

- Mechanism: canonical mapping or reported diagnostics could be decoded incorrectly despite schema-valid choices.
- Evidence: every parsed record includes `canonical_choice`, `presented_choice`, and `presented_order`; this audit re-counted 240 unique item/sample keys and recomputed all diagnostics from raw records.
- Contrary evidence: the recomputation uses the same stored canonical fields and no separately implemented decoder.
- Discriminating test: independent raw-prompt parser and canonical mapper.
- Fix/action: no code change is justified by current evidence.
- Interpretability: yes for stored fields, subject to this independence limitation.

## Decision

1. Resolve-condition verdict: **met for the panel's mechanical conditions, not met for a stable direct-choice measurement claim.** The task required a preserved 240-key ledger, compatibility, position diagnostics, usage, and cache evidence. Those exist. The panel has three registered position-TV warnings and a 0.700 Abortion schedule/direction difference.
2. Prediction check: sample 0 was parse-valid under `effort:none`, the remaining 239 calls followed, cyclic exposure balanced positions, and cache replay made no new request records. The predicted absence of a large generic position preference is contradicted for three items.
3. Earliest unsupported link: a direct-choice distribution from this prompt/presentation is a stable WVS response or can be made into a culture coordinate.
4. Validity: define invalid as suitable for coordinate publication, family trajectories, or cross-model capability fits. P(invalid for those uses) is highly likely, about 0.85. This is a credible durable record of the registered responses and a negative construct-stability observation.
5. Highest-information clues: (a) 240/240 schema-valid responses isolate construct from API mechanics; (b) all 20 trust-item selections at displayed position 0 despite 50/50 canonical choices identifies a generic position effect; (c) Abortion's 0.700 half/direction TV preserves severe instability rather than averaging it away.
6. Missing metrics: a layout-label control, independent randomized repeat, external billing reconciliation, execution-time git revision, and a reviewed direct-choice-to-coordinate rule.
7. Bugs requiring code changes: none established. The audit finding is a method limitation, not evidence to silently change the prompt after this completed run.
8. Misconceptions requiring reinterpretation: valid strict-schema JSON and balanced exposure do not demonstrate semantic response invariance or human-WVS comparability.
9. What would change the verdict: a randomized independent repeat with low position and order variation would lower the construct concern; a persistent result under changed layout would make semantic ambiguity more likely.
10. Recommended sequence: audit the other two already-authorized Wave 01 panels independently. Do not queue any later model or publish direct-choice coordinates until parent review of all three audits.

-- PI[gpt-5.6-terra]
