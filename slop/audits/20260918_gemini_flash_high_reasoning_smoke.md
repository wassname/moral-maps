# Gemini Flash high-reasoning paid-smoke audit

Target: the one-item `normal_high` smoke for `google/gemini-3-flash-preview`, run on branch `research/gemini-flash-rubric-v1` from preregistration commit `4955468`. The executed source had uncommitted smoke-selection and route-validation changes that are included in the amended commit reported with this audit.

| stage | expected | observed | expected? | clues | missing metric | consequence |
|---|---|---|---|---|---|---|
| input and condition | First WVS item, normal rubric, high reasoning | Homosexuality item, `reasoning={"effort":"high"}` | yes | `paid_smoke.jsonl:1-2` | other items | No estimate of item-to-item rescue rate |
| provider routing | Google AI Studio only, exact release visible | `Google AI Studio`, `google/gemini-3-flash-preview-20251217` in both phases | yes | `paid_smoke.jsonl:3,5` | historical quantization | Route is established; quantization remains endpoint-advertised only |
| initial response | Parse-valid rating JSON within 1,024-token budget | `finish_reason="length"`; JSON stopped after key 4 | no | `paid_smoke.jsonl:3-4` | replicate rescue frequency | High reasoning can exhaust this budget |
| rescue | Same conversation returns compact valid JSON | Complete ten-key JSON, `finish_reason="stop"` | yes | `paid_smoke.jsonl:5-6` | none for mechanics | Reader recovered the sample |
| result | One valid sample, failures explicit | valid 1, failed 0, rescued 1 | yes | `paid_smoke.jsonl:7-8` | no coordinate is expected from one item | Mechanics only, not a scientific result |
| usage and reasoning | Full per-phase usage/reasoning retained | 2,362 total tokens, 1,581 reasoning tokens, USD 0.0053585 | yes | `paid_smoke.json:usage_totals,phases` | hidden provider reasoning beyond returned fields | Returned evidence is auditable; hidden fields remain unknowable |
| accounting | Local and global conservative accounting agree; no reservation remains | local actual/conservative USD 0.0053585, global external settlement USD 0.0053585, reserved zero | yes | `paid_smoke.json:budget`; `slop/research/wvs/20260917_score_all_options/budget.json` | none | Spend is reconciled |
| persistence | Raw requests, responses, route, reasoning, usage, parse, and summary saved | JSONL, summary, attempt ledger, and run log exist | yes | experiment directory | exact uncommitted execution diff before amend | Amend commit supplies it |

## Chronology and primary evidence

The request used the intended question and rubric. The complete rendered prompt is in `paid_smoke_run.log:4-20`.

The first response reached the completion limit. `paid_smoke.jsonl:3` records, verbatim inside the response:

> `"finish_reason": "length"` ... `"content": "{\"0\": 1, \"1\": 1, \"2\": 2, \"3\": 2, \"4\": 3,"` ... `"completion_tokens": 1009` ... `"reasoning_tokens": 979` ... `"cost": 0.00311`

Epistemic context: this is the full provider response saved before parsing, not a later summary.

The same record reports the selected route:

> `"requested": "google/gemini-3-flash-preview"` ... `"model": "google/gemini-3-flash-preview-20251217", "provider": "Google AI Studio", "selected": true`

The rescue completed the object. `paid_smoke.jsonl:5` records:

> `"finish_reason": "stop"` ... `"content": "{\"0\": 1, \"1\": 1, \"2\": 2, \"3\": 2, \"4\": 3, \"5\": 3, \"6\": 4, \"7\": 4, \"8\": 5, \"9\": 5}"` ... `"completion_tokens": 662` ... `"reasoning_tokens": 602` ... `"cost": 0.0022485`

`paid_smoke.jsonl:6-8` then records `parsed: true`, one valid sample, zero failures, and one rescue. The saved endpoint snapshot contains a present `quantization` field with value `unknown`; this is current endpoint metadata, not historical proof of the serving quantization.

The run log's only `SHOULD` line says replies should be bare rating JSON with a valid rate near one. `paid_smoke_run.log:21-25` shows the rescued complete JSON and `valid=1/1`; the initial truncation remains visible in the JSONL rather than being summarized away.

## ML-debug form

| row | answer |
|---|---|
| log length and config | 26 log lines; full config is `paid_smoke.jsonl:1`, including high reasoning, structured output, provider lock, seed, and timeouts |
| each `SHOULD` and observation | `paid_smoke_run.log:25` expects bare JSON and near-one validity; lines 21-24 show complete rescued JSON and `valid=1/1` |
| null or chance for cited numbers | Not applicable to a transport/parser smoke; no model-quality metric is interpreted |
| initialization, training, gradients, schedule, baseline, held-out | Not applicable; this is one API evaluation request with no training |
| one full sample | Input: `paid_smoke_run.log:4-20`; initial and rescue outputs: `paid_smoke.jsonl:3,5` |
| surprising line | Initial `finish_reason="length"` after 979 reasoning tokens, explained by high reasoning consuming almost all of the initial completion budget |
| missing evidence needed for trust | Rescue frequency across items/releases; one item cannot estimate it |
| diagnoses | See hypotheses below |
| fresh review | Kimi K3's blind read: "Parse -- established only via rescue" and "No" to queueing now; it also found that the panel path does not fail inline on a route mismatch and rescue payloads omit the paired seed |
| cheapest discriminating test | The already-planned full run, stopped by the USD 10 accounting cap, directly measures rescue frequency by condition; queue only after parent smoke review |
| wall clock and GPU | About twelve seconds from reservation to finish in saved timestamps; no GPU |

The number behind the main diagnosis is 979 reasoning tokens in the initial response. A second cause could be unusually long reasoning for this particular values item, rather than a general property of high reasoning. Rescue counts by item and release separate these explanations.

## Ranked hypotheses

### H1 [measurement | Likely | 65%]

- **Mechanism:** High reasoning often consumes the initial completion budget, so high-reasoning cells invoke the two-phase rescue more often than minimum-reasoning cells.
- **Evidence:** `paid_smoke.jsonl:3` says `finish_reason="length"`, `completion_tokens: 1009`, and `reasoning_tokens: 979`.
- **Contrary evidence:** Only one item and one release were sampled; the rescue stopped normally.
- **Discriminating test:** Compare rescue fractions by cell in the bounded pilot. A high-versus-minimum gap supports the mechanism; similar low rates do not.
- **Fix/action:** Do not change the preregistered protocol before review. Preserve phase counts and let the hard cap stop early if rescues accumulate.
- **Interpretability:** partial; smoke mechanics are interpretable, population rescue frequency is not.

### H2 [harness | Highly Unlikely | 10%]

- **Mechanism:** The route checker accepts an alias or wrong provider while presenting it as the intended release.
- **Evidence:** Both phases contain one selected endpoint with provider `Google AI Studio` and exact dated slug `google/gemini-3-flash-preview-20251217`; validation compares all requested, response, provider, and selected-slug fields.
- **Contrary evidence:** The endpoint snapshot is current and supplied the expected dated slug; it does not prove historical quantization.
- **Discriminating test:** Require the same four-field equality on every pilot response, which the runner does.
- **Fix/action:** Keep fail-fast route validation for summary/audit; all raw metadata is already retained.
- **Interpretability:** yes for provider/release routing, no for exact quantization.

### H3 [bug | Highly Unlikely | 8%]

- **Mechanism:** A rescue or retry is billed but omitted from local or repository-wide accounting.
- **Evidence:** The raw phases cost USD 0.0031100 and USD 0.0022485; `paid_smoke.json:budget` totals USD 0.0053585 with zero held reservation, and the global external entry records the same amount.
- **Contrary evidence:** This tested successful initial and rescue phases, but not a charged failed attempt in a real request; the offline smoke covers that path.
- **Discriminating test:** Reconcile every future raw `usage.cost` against both ledgers after the run.
- **Fix/action:** Keep per-attempt append-only records and unique global reservation IDs.
- **Interpretability:** yes for this smoke.

### H4 [data | Likely | 60%]

- **Mechanism:** This item's reasoning length is not representative of the other items or releases.
- **Evidence:** The smoke contains only Homosexuality, as shown in `paid_smoke_run.log:4-20`.
- **Contrary evidence:** The initial response spent nearly the full fixed completion budget, so the failure mode itself is real even if its frequency is unknown.
- **Discriminating test:** Rescue fractions by item, release, and reasoning cell in the bounded run.
- **Fix/action:** Do not infer a global rescue rate from the smoke.
- **Interpretability:** yes for mechanics, no for frequency.

## Blind review

Kimi K3 independently read the runner and complete smoke artifacts without this diagnosis. Its central observation was:

> **Parse -- established only via rescue.** The initial phase truncated: `"finish_reason": "length"`, `"native_finish_reason": "MAX_TOKENS"` [...] The rescue phase returned `"finish_reason": "stop"` and the full object, yielding `"parse_valid": true`, `"rescued_samples": 1`.

It recommended not queueing the full run yet. Its additional code findings were that the full panel saves route metadata but does not call `validate_route()` inline, successful provider-reported cost is called conservative rather than tracked under a more exact label, and the rescue follow-up omits the paired seed. Source: reviewer session `/home/code/.pi/agent/sessions/--workspace-2026-lite-moralmaps--/2026-09-18T09-52-42-678Z_01a0b3ee-bcb6-74a9-9466-71816e47002e/cb91d1f9-d68f-4dbe-a960-ffe4aad449a5/run-0/session.jsonl`.

## Decision

**Resolve-condition verdict: met.** The required smoke condition was a parse-valid `normal_high` request with exact Google AI Studio routing, exact release metadata, saved reasoning/usage, endpoint quantization field, and reconciled accounting. The raw and summary artifacts contain each field. The smoke also exposed an initial truncation and successful rescue.

**Prediction check:** The design's scientific predictions about coordinate shifts, rubric sensitivity, family trend, and rubric invariance remain unresolved because the smoke has one item and one cell. The operational prediction that high reasoning might consume the initial budget is supported in this sample.

**Earliest unsupported link:** One high-reasoning truncation does not establish the rescue frequency or final pilot cost. Condition-level phase counts would support that link.

**Validity:** Invalid here means that the smoke did not exercise or faithfully record the reviewed route/parser/accounting path. I estimate `P(smoke mechanics are invalid) = 0.03-0.08`; this is a credible positive mechanics smoke, not a scientific result.

**Three highest-information clues:**

1. The selected dated release and provider are present in both raw phases, so alias/provider ambiguity did not occur.
2. The first response stopped for length after almost all completion tokens were reasoning, demonstrating the principal high-reasoning risk.
3. Raw phase costs reconcile exactly with local and global accounting, including rescue cost.

**Missing metrics:** Rescue frequency by condition is highest value, followed by per-item reasoning-token distributions, then whether other releases return the same exact-route metadata shape.

**Bugs requiring code changes:** Before the full run, the parent should decide whether to add fail-fast route validation to every panel response and copy the paired seed into rescue payloads. The smoke route validation and aggregate phase summaries are already included. `conservative_spent_usd` is exact provider-reported spend for successful phases and a bound only for failed phases, so the field name should not be interpreted as an upper bound on all future billing.

**Misconceptions requiring reinterpretation:** The USD 9.363456 panel figure is an initial-request bound, not a completion guarantee when rescues occur. The runtime USD 10 stop remains the true spending bound. A rescued high-reasoning cell also tests the repository's two-phase bounded-thinking protocol, not only a single seeded completion.

**What would change the verdict:** A mismatch between raw phase-cost sums and either ledger, a selected endpoint other than the pinned dated Google release, or a replay that makes another paid call would invalidate the mechanics claim.

**Recommended sequence:** Amend and push the research branch with the raw smoke and this audit. Wait for parent inspection. Before queueing, decide whether to keep the two-phase high-reasoning protocol and likely early USD 10 stop, or revise and re-preregister its token budget; also resolve panel route validation and rescue seeding. Do not combine these decisions silently.

-- PI[gpt-5.6-terra]
