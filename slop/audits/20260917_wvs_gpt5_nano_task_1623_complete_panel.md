# WVS GPT-5 Nano diagnostic, task 1623

- auditor: PI[gpt-5.6-terra]
- status: complete protocol diagnostic, not a priority result
- task: `1623`, Pueue `api` group, `sh scripts/wvs_api/01_gpt5_nano_diagnostic.sh`
- run: `20260917T020418Z_7fe76f95937e`
- protocol: `7fe76f95937ed145b996116a31855dae4ab8c3b67e3e7ccfb84a000437e27f96`
- primary logs: `slop/research/wvs/20260917_priority_phase/task_1623_clean.log`, 95/95 cleaned lines, SHA256 `f00b5bc42daaa1332b5812ce94976bd4fe26de199e3292af106b20dae9c6da39`; `task_1623_raw.log`, 99 lines, SHA256 `31871a0bfb5139e9bf36cd5fd1be7695f720050d9e9ed918a3175a24b5830981`
- saved source of truth: `slop/research/wvs/20260916_openrouter/wvs_iw_requests.jsonl`

## Intended diagnostic and predictions

The manifest's first new panel tests the exact rated-reader protocol before later models: 12 items x 12 initial samples, strict JSON schema, `reasoning.effort=low`, concurrency 1, and `max_tokens=1024`. Task 1622 showed that this endpoint rejects disabled reasoning; this retry retains strict schema but uses the catalog-supported minimum effort.

| prediction | expected evidence | observed | verdict |
|---|---|---|---|
| Mandatory reasoning is accepted | completed initial calls, not HTTP 400 | 144/144 initial requests completed | supported |
| The reader preserves 12 usable samples/item | 144 distinct item/sample parsed keys and 12 item results | 144 parsed keys and 12 item results, each `valid_samples: 12` | supported |
| Rescue preserves a missing final answer without disguising it | separately recorded rescue phases | 2 initial empty responses, 2 separately recorded rescue completions | supported |
| Strict schema gives parsable, non-refusal answers | JSON parse for every retained sample, no refusal/error event | 144 `answer_parsed`, 0 `request_failed`, no refusal strings in retained JSON | supported |
| Cache replay is offline | same protocol cache hit and no new request ledger events | task 1625 logs a cache hit; ledger has no later run/event | supported |

## Stage table

| stage | expected | observed | expected? | clues | missing metric | consequence |
|---|---|---|---|---|---|---|
| Pueue provenance | `api` task runs exact wrapper after 1622 repair | task 1623 success, 10:04:09 to 10:17:54 +0800 | yes | raw log header; wrapper specifies low reasoning, schema and completeness flag | immutable worktree revision was not emitted by Pueue | ledger payload is the API provenance |
| request protocol | low reasoning plus strict schema is accepted | 144 initial `request_completed`, zero `request_failed` | yes | ledger run events | provider catalog capability is snapshot, not live rechecked | unlike 1622, endpoint generated responses |
| rescue | 144 planned samples can be retained after any empty completion | 146 completions: 144 initial plus two rescue | yes | `Homosexuality/4`, `Religion/1` phase records | upstream reason for empty initial message | rescue costs are included in total |
| parsing | 144 valid JSON ratings | 144 `answer_parsed`, each item `valid_samples: 12` | yes | ledger counts and item-result records | no independent semantic-rating ground truth | reader gets a complete panel |
| order control | binary choices are evenly presented in both directions | every binary item is 6 canonical / 6 reversed initial calls | yes | initial `presented_order` ledger records | nonbinary cards were not permuted | binary order cannot explain a one-sided result |
| output / coordinates | cached rated output and coordinate CI are saved | `cached gpt-5-nano (rated): (0.45, 0.63) +-(0.11, 0.16) 95% CI` | yes | task 1623 clean log line 26 | coordinate signal quality is not assessed by parse completeness | raw panel is saved but does not yet authorize a coordinate conclusion |
| rating discrimination | each axis pole distinguishes answer options often enough to support a coordinate | Homosexuality has 11/12 constant ratings and near-uniform p | no | fresh review, raw ledger answers | explicit content-quality statistic in the reader | priority coordinate comparison is not yet validated |
| billing | all accepted requests expose provider usage | 146 usage records, USD 0.03265465 | yes | ledger `request_completed.usage` sum | provider billing export is not saved | cost is observed provider response, including rescues |
| cache replay | exact protocol does not make a network request | task 1625: `cache hit gpt-5-nano (rated): protocol=7fe76f95937e`; no ledger event after 02:17:46 UTC | yes | task 1625 full 73/73 clean log and ledger timestamps | no packet-level network trace | no second paid panel was initiated |

## Chronology and raw evidence

The retry wrapper is explicit:

> `--api-reasoning-effort low \\`
> `--api-structured-output \\`
> `--api-require-complete \\`
> `--api-concurrency 1 \\`
>
> `scripts/wvs_api/01_gpt5_nano_diagnostic.sh`

The first-item trace gives two exact raw responses and its retained distribution:

> `['{"0":3,"1":3,"2":3,"3":3,"4":3,"5":3,"6":3,"7":3,"8":3,"9":3}', '{"0":3,"1":3,"2":3,"3":3,"4":3,"5":3,"6":3,"7":3,"8":3,"9":3}']`
> `[0.094, 0.096, 0.098, 0.1, 0.102, 0.102, 0.102, 0.102, 0.102, 0.102]  valid=12/12`
>
> `task_1623_clean.log`, lines 16-24.

The complete ledger event totals are one `run_started`, 146 `request_started`, 146 `request_completed`, 144 `answer_parsed`, 12 `item_result`, and one `run_finished`. There are exactly 144 distinct `(item_id, sample)` parsed keys. The run finish records `planned_requests: 144`, `valid_samples: 144`, `failed_samples: 0`, and `rescued_samples: 2`.

The two extra completions reconcile to the two recorded rescue phases. Initial completions for `Homosexuality`, sample 4 and `Religion`, sample 1 contained no final message content. Their rescue completions respectively retained:

> `{"0": 3, "1": 3, "2": 3, "3": 3, "4": 3, "5": 3, "6": 3, "7": 3, "8": 3, "9": 3}`
>
> `{"0":5,"1":4,"2":2,"3":1}`
>
> request-ledger rescue records for run `20260917T020418Z_7fe76f95937e`.

Thus the final dataset has no parser failures or provider request failures. Across the 144 retained JSON replies there are 46 distinct exact JSON strings. No retained JSON contains `cannot`, `unable`, `refuse`, or `sorry`; this string check is not a general refusal detector, but there is no refusal event or malformed retained answer either.

The ledger usage sum is 28,157 prompt tokens plus 78,117 completion tokens, 106,274 total tokens, and USD 0.03265465 across all 146 accepted calls. This includes the two rescues, so it is not a 144-call-only amount. It is below the manifest's USD 0.0590 completion-only ceiling, though that ceiling excluded prompts and rescues and therefore is not a billing prediction.

Task 1625 reran the same wrapper after completion. Its log says:

> `cache hit gpt-5-nano (rated): protocol=7fe76f95937e`
>
> `task_1625_cache_replay_clean.log`, line 14.

The ledger still has only the 450 events for this run; its last recorded timestamp is `2026-09-17T02:17:46.346268+00:00`, before the replay task. This establishes zero new ledger `request_started` events under the exact same protocol. The raw and cleaned replay logs are byte-identical, each SHA256 `f73dd2221a67a4b38520a2b91bbb5683eccc9eb9b4706222e0bd28a79e6131b1`.

## Hypotheses

### H1 [harness | Almost Certain | 97%]

- mechanism: the repaired wrapper's `reasoning.effort=low` meets Nano's endpoint requirement while retaining the strict JSON schema.
- evidence: task 1622 previously returned `Reasoning is mandatory for this endpoint and cannot be disabled.`; task 1623 has 144 initial completions and zero failures under the changed reasoning payload.
- contrary evidence: task 1623 changes reasoning only relative to the retry wrapper, but the exact upstream implementation between attempts is not separately versioned.
- discriminating test: this completed matched retry already distinguishes it. A repeat with disabled reasoning would predict 400s again, but it is not worth paying for.
- fix/action: use the `reasoning.effort=low` setting for this mandatory endpoint; retain an exact protocol ID rather than mixing it with disabled-reasoning attempts.
- interpretability: yes, for this protocol only.

### H2 [measurement | Highly Likely | 82%]

- mechanism: the two rescues repair missing final-message content while keeping the original attempts and rescue billing durable.
- evidence: the ledger has `146 = 144 initial + 2 rescue` completed calls but exactly 144 parsed sample keys, and `run_finished` reports `rescued_samples: 2`.
- contrary evidence: it lacks the upstream explanation for why the initial messages were empty, so the root cause of the two omissions is unknown.
- discriminating test: inspect future mandatory-reasoning panels for the same empty-content pattern. If it recurs at material frequency, capture reasoning/content fields and change the request cap only with that evidence.
- fix/action: retain phase-specific ledger records and count billed rescue calls separately; do not merge this run with 1622.
- interpretability: yes, because every retained item/sample has a valid rescue or initial JSON reply.

### H3 [measurement | Almost Certain | 96%]

- mechanism: parse-valid constant ratings treat mutually exclusive answer options as simultaneously neutral and collapse an axis-pole item toward its midpoint.
- evidence: the independent review `slop/reviews/20260917_gpt5_nano_1623_reader_review.md` counts 11/12 constant ratings for Homosexuality, including 9 all-3 answers. Its recovered reasoning tail says, `the statements are mutually exclusive. So, maybe it's best to simply assign all of them a neutral rating of 3 to keep it straightforward!` The resulting expected score is 5.57 versus scale midpoint 5.5.
- contrary evidence: the same panel's binary items are order-balanced and directionally discriminative, and 46 distinct JSON strings occur overall. The failure is concentrated, not universal.
- discriminating test: calculate constant-rating share or a discrimination statistic per item before caching/publishing. H3 predicts Homosexuality exceeds a >50% flag; a uniformly low flag across pole items would contradict the concern.
- fix/action: do not publish or use this diagnostic as coordinate validation. Add a visible content-quality gate or diagnostic to the reader before comparing later panels, then rerun only the cheapest discriminating check if the gate changes behavior.
- interpretability: partial for mechanics and accounting; no for self-expression coordinate quality.

### H4 [measurement | Unlikely | 15%]

- mechanism: provider-reported `usage.cost` could differ from a later account billing export.
- evidence: the ledger returns usage on every accepted completion but no provider billing export was saved.
- contrary evidence: all 146 accepted calls include cost and token fields, and the sum is durable rather than inferred from a price table.
- discriminating test: compare the same generation IDs against an OpenRouter billing export if one becomes available.
- fix/action: record USD 0.03265465 as observed provider-reported cost, not independently reconciled account billing.
- interpretability: yes for ledger-reported cost; partial for invoice-level cost.

## Decision

- resolve-condition verdict: **not met as an authorization for the priority coordinate batch**. The literal mechanics condition, "all 12 items have 12 valid samples, recorded usage, and cache replay", is met. The independent fresh review identifies an earlier missing condition: the self-expression pole item has 11/12 constant ratings and gives no material directional signal. The parse-based completeness gate cannot distinguish that from a valid attitude readout.
- prediction check: low mandatory reasoning accepted, supported; strict schema parsability, supported; offline replay, supported; the implicit prediction that parsed ratings validate coordinate quality, contradicted.
- earliest unsupported link: discrimination of the self-expression pole response. A content-level per-item constant-rating or discrimination measurement would support it.
- validity: invalid means either incomplete mechanics or a coordinate whose pole item is non-discriminative under the rated protocol. `P(the mechanics result is invalid) ~= 0.03`; `P(this run validates self-expression coordinate quality) < 0.10` because 11/12 pole answers are constant. Classify as credible pipeline evidence but an inconclusive coordinate diagnostic.
- highest-information clues: (1) 144 distinct parsed keys establishes mechanical completeness; (2) phase counts reconcile every extra billed completion to a rescue; (3) 11/12 constant Homosexuality ratings and the quoted neutral-hedging explanation show the unmeasured content failure.
- missing metrics: (1) constant-rating or discrimination statistic per item, (2) provider explanation for two empty initial final messages, (3) invoice-level reconciliation of `usage.cost`.
- bugs requiring code changes: the completion gate needs a content-quality discriminator if it is used to authorize comparative coordinate panels.
- misconceptions requiring reinterpretation: task 1622 is not evidence that Nano or mandatory reasoning is unusable; it is a disabled-reasoning wrapper/config attempt. Task 1623 does not license later coordinate interpretation merely because its JSON parses.
- what would change the verdict: a content-quality measurement showing all pole items discriminate, or a reader repair plus a fresh cheapest panel showing the Homosexuality rate below a predeclared threshold, would support batch authorization. Another cache replay would not.
- recommended sequence: stop before the priority batch. Report the material content-quality failure to the parent, decide an explicit pre-registered discrimination metric and threshold, then make its smallest reader diagnostic. Do not merge this distinct run with task 1622 or incomplete Grok 4.5 attempts.

-- PI[gpt-5.6-terra]
