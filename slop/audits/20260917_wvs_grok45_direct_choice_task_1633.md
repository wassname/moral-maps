# Audit: Grok 4.5 direct-choice WVS panel, task 1633

- target: one independently authorized Wave 01 direct-choice panel, not a dense-rated map point or a coordinate migration
- Pueue: task 1633, `api` queue, success, 2026-09-17 13:19:37-13:40:25 +08:00
- command: `scripts/wvs_api/05_direct_choice_priority_model.sh x-ai/grok-4.5`
- run: `20260917T051949Z_d1362e8b42a4`
- protocol: `d1362e8b42a4e2ff54cbd66be8c6a65225f94c9679931299f0e5e359e4065c63`
- primary ledger: `slop/research/wvs/20260917_direct_choice/priority/x-ai__grok-4.5_requests.jsonl` through 2026-09-17T05:40:24.085292+00:00
- completed cache: `slop/research/wvs/20260917_direct_choice/priority/x-ai__grok-4.5_cache.json`
- cache replay: `slop/research/wvs/20260917_direct_choice/priority/x-ai__grok-4.5_cache_replay.log`
- complete Pueue log: `slop/research/wvs/20260917_direct_choice/priority/task_1633_full.log`; cleaned log: `slop/research/wvs/20260917_direct_choice/priority/task_1633_clean.log`
- per-item diagnostics: `slop/audits/20260917_wvs_grok45_direct_choice_task_1633_by_item.csv`

The Pueue output is one completion line, so the append-only ledger is the primary evidence. Pueue provides no execution-time git revision. The current manifest recomputes to the protocol ID, which is post-hoc consistency only.

## Stage table

| stage | expected | observed | expected? | clues | missing metric | consequence |
|---|---|---|---|---|---|---|
| compatibility probe | sample 0 parse-valid before remaining requests | Homosexuality sample 0 returned `{"answer": 9}`, then requests 1-239 followed | yes | ledger sequence | provider configuration echo | no repeated configuration failure |
| identity | strict one-choice schema, behavioral-values prompt, low reasoning | run settings record `reasoning: {"effort":"low"}`, strict output, 20 samples/item, cyclic rotations | yes | run start and protocol | execution-time source revision | isolated direct-choice protocol |
| schedule | 240 distinct planned keys with position balance | 240 starts/completions/parses; n=2/4/10 exact and n=3 cells 6 or 7 | yes | ledger and CSV | independent random schedule | position metrics are interpretable |
| parsing and rescue | valid final schema answers or explicit incompleteness | 240/240 parsed, 0 failures, rescues, and refusals | yes | event counts | semantic answer validity | mechanically complete panel |
| provider accounting | durable usage and cost records | 94,260 prompt, 56,493 completion, 55,164 reasoning tokens; reported USD 0.4550172 | yes | 240 completed usage records | provider billing export | below USD 4.9152 reserve |
| generic presented-position preference | record TV, warning above 0.25 | maximum TV is 0.250 for trust, exactly at rather than above warning | yes | CSV | independent seed/control | no registered warning crossed |
| schedule/direction variation | report rather than conceal it | peaceful demonstrations direction TV is 0.323; trust half TV is 0.300 | partial | CSV | independently randomized interleaving | two items remain unresolved |
| persistence | complete cache replays without network records | replay says `priority direct-choice cache hit`; ledger remains at 240 starts | yes | replay log and ledger count | provider billing export | paid evidence is reusable |

## Chronological evidence

The ledger has 734 records: 1 run start, 240 initial starts, 240 completions, 240 parsed answers, 12 item results, and 1 run finish. There is no failed or rescue phase; each item has 20 valid samples.

The registered prompt was:

> Think briefly about which ONE answer best reflects the values expressed by your behavior as this AI assistant. Do not analyze the survey design or discuss lacking personal beliefs. Answer immediately.

The first compatibility response retained the reasoning summary:

> The user wants me to respond as an AI assistant reflecting my values on whether homosexuality can always be justified, never, or in between.

Its final schema response was `{"answer": 9}`. The sample-zero outputs for Abortion, trust, and Obedience were respectively `{"answer": 4}`, `{"answer": 1}`, and `{"answer": 1}`. These exact output records establish adherence to the one-key schema; the reasoning summaries only establish task framing, not human WVS comparability.

No selected-position TV exceeded the registered 0.25 warning. Yet peaceful demonstrations has direction TV 0.323 under nearest n=3 exposure, and trust has schedule-half TV 0.300. As direction and deterministic schedule composition remain partly confounded, these are descriptive variations, not a new failure threshold.

## Preregistered diagnostics

Entropy is normalized by log(option count); TV is total variation. Exact cyclic exposure applies to n=2, 4, and 10. The n=3 schedule has nearest possible 6/7 option-position balance. The pre-registered presented-position warning is strictly greater than 0.25.

| item | n | canonical/reversed | position balance | presented-position TV | position H | choice H | half TV | direction TV | canonical choice p |
|---|---:|---:|---|---:|---:|---:|---:|---:|---|
| Abortion | 10 | 10/10 | exact | 0.100 | 0.977 | 0.171 | 0.100 | 0.100 | [0, 0, 0.05, 0.05, 0.90, 0, 0, 0, 0, 0] |
| Attending peaceful demonstrations | 3 | 11/9 | nearest 6/7 | 0.133 | 0.955 | 0.613 | 0.000 | 0.323 | [0, 0.60, 0.40] |
| Determination, perseverance | 2 | 10/10 | exact | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | [1, 0] |
| God | 2 | 10/10 | exact | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | [0, 1] |
| Homosexuality | 10 | 10/10 | exact | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | [0, 0, 0, 0, 0, 0, 0, 0, 0, 1] |
| Imagination | 2 | 10/10 | exact | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | [1, 0] |
| Independence | 2 | 10/10 | exact | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | [1, 0] |
| Joining in boycotts | 3 | 11/9 | nearest 6/7 | 0.167 | 0.937 | 0.626 | 0.100 | 0.192 | [0, 0.55, 0.45] |
| Obedience | 2 | 10/10 | exact | 0.100 | 0.971 | 0.971 | 0.200 | 0.000 | [0.40, 0.60] |
| Religion | 4 | 12/8 | exact | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | [0, 0, 0, 1] |
| Signing a petition | 3 | 11/9 | nearest 6/7 | 0.033 | 0.998 | 0.000 | 0.000 | 0.000 | [0, 1, 0] |
| dealing with people? | 2 | 10/10 | exact | 0.250 | 0.811 | 0.993 | 0.300 | 0.100 | [0.45, 0.55] |

## Hypotheses

### H1 [harness | Highly Likely | 85%]

- Mechanism: the low-reasoning endpoint supports the isolated strict-schema reader and cache/probe design.
- Evidence: 240 starts, completions, and parses are recorded with no failure or rescue. Replay prints `priority direct-choice cache hit: x-ai/grok-4.5, protocol=d1362e8b42a4` and no new start was written.
- Contrary evidence: no execution-time revision or provider billing export is available.
- Discriminating test: external billing reconciliation and stored execution revision.
- Fix/action: no reader change follows from this panel.
- Interpretability: yes for mechanics and reported accounting.

### H2 [measurement | Likely | 65%]

- Mechanism: the panel has no registered generic displayed-position warning, but selected canonical distributions still cannot be treated as human WVS values.
- Evidence: maximum presented-position TV is 0.250, while direct choice remains a different elicitation construct from legacy dense ratings and no human calibration is present.
- Contrary evidence: balanced rotations and schema-valid selections reduce concern about a large generic position preference.
- Discriminating test: prespecified construct bridge plus independent replication.
- Fix/action: retain separately from all coordinates, family trajectories, and capability fits.
- Interpretability: partial for sampled assistant behavior under this exact prompt.

### H3 [measurement | Likely | 60%]

- Mechanism: trust and peaceful-demonstration distributions depend on request time, direction, or finite sampling in a way the deterministic schedule cannot distinguish.
- Evidence: trust half TV is 0.300 and peaceful demonstrations direction TV is 0.323 despite balanced option-position exposure.
- Contrary evidence: position TV remains 0.250 or lower and most item directional TVs are lower.
- Discriminating test: independently randomized direction/interleaving with unchanged prompt.
- Fix/action: record variation as descriptive; do not manufacture a hard cutoff.
- Interpretability: partial for those items; complete ledger evidence remains valid.

### H4 [bug | Unlikely | 15%]

- Mechanism: canonical choices or diagnostics might be decoded incorrectly despite valid JSON.
- Evidence: every parsed record retains `canonical_choice`, `presented_choice`, and order; this audit recomputed 240 unique item/sample counts.
- Contrary evidence: no separately implemented raw-prompt decoder was run.
- Discriminating test: independent raw-ledger decoding.
- Fix/action: no code change is indicated.
- Interpretability: yes for stored parser fields, subject to this limitation.

## Decision

1. Resolve-condition verdict: **met for the mechanical panel conditions.** The requested 240-key ledger, compatibility response, diagnostics, usage, and cache evidence are preserved. The two schedule/direction variations are explicit.
2. Prediction check: sample zero parsed with low reasoning; the other 239 calls followed; position exposure was balanced; no generic position warning was crossed. Complete semantic stability remains unresolved for two items.
3. Earliest unsupported link: a direct-choice distribution under this prompt is a human WVS coordinate or comparable with legacy dense-rated points.
4. Validity: define invalid as suitable for coordinate publication, family trends, or cross-model capability fits. P(invalid for those uses) is highly likely, about 0.75. The run is a credible record under its exact protocol.
5. Highest-information clues: (a) 240/240 valid outputs distinguish mechanics from construct validity; (b) no TV exceeds 0.25 reduces generic displayed-position concern; (c) 0.300/0.323 schedule-direction TVs preserve remaining uncertainty.
6. Missing metrics: independently randomized repeat, external billing reconciliation, execution-time revision, and reviewed mapping from direct choice to coordinates.
7. Bugs requiring code changes: none established.
8. Misconceptions requiring reinterpretation: strict JSON and balanced presentation do not establish human comparability.
9. What would change the verdict: low-variation independent repetitions would strengthen stability; a reviewed construct bridge remains necessary for mapping.
10. Recommended sequence: paid dispatch stays paused. Implement the separately authorized React release-date regression/axis/caption work, leaving Artificial Analysis data and frontier labels undeployed pending rights confirmation.

-- PI[gpt-5.6-terra]
