# Audit: OpenAI score-all-options lane 1669

- target: serialized OpenAI refresh lane `1669`, started 2026-09-17 20:29:43 +0800, ended 22:07:37 +0800, Pueue success.
- command: `scripts/wvs_api/06_score_all_options_lane.sh openai` at worktree `/workspace/2026/lite/moralmaps`.
- executed source revision is not recorded by Pueue. The raw ledger records `eval_version: wvs-score-all-options-v1` for requests created during the run. This audit inspected the full ANSI- and carriage-return-normalized log, 2,864/2,864 lines, and raw log, 2,976 lines, at `/tmp/wvs-audit-1669/`.
- this is an operational completion audit, not a comparison of model coordinates or a claim that one model is better.

| stage | expected | observed | expected? | clues | missing metric | consequence |
|---|---|---|---|---|---|---|
| cache/probe | cache replay or one parse-valid sample before 143 further calls | each unavailable model stopped after its first failed sample | yes | `run_aborted` records, ledger lines 44001, 50155, 50172, 51527, 53774, 54237, 54700 | provider feature declaration at request time | failures did not become 144 repeated requests |
| full panels | 144 parse-valid ratings, 12 items x 12 | 20 models have 144/144 valid, no rescues | yes | `run_finished` ledger rows, summarized below | independent semantic validity control | cacheable panels only, not substantive coordinate claims |
| partial panel | incomplete panels excluded | `gpt-oss-20b` has 142/144 valid after 16 rescues, and is absent from `completed` cache | yes | ledger line 50138; clean log line 1031 | per-item error classifications | no coordinate is cached/plotted |
| incompatible panels | retain raw evidence, do not cache | 7 models ended 0/144 after sample-0 failure | yes | full log 484-524, 2332-2410, 2545-2623, 2758-2836 | a supported schema alternative, deliberately not tried | exclusions are protocol compatibility results |
| accounting | release reserves after a model | refresh ledger reports USD 7.388069120252 total; only pilot reserve USD 1 remains | unclear | `slop/research/wvs/20260917_score_all_options/budget.json` after lane | per-lane cost reconciliation artifact | cost is ledger-derived, not independently billed-account verified |

## Observations

The runner is fail-fast on an incomplete panel. `scripts/wvs_map.py` says:

> `incomplete = [row["id"] for row in rows if row["valid_samples"] != args.api_samples]`
>
> `message = f"{key}: incomplete items {incomplete}; raw evidence is in {args.records}; not cached or plotted"`
>
> `if args.api_require_complete:`
> `    raise RuntimeError(message)`

The reader's sample-0 screen is also explicit:

> `first_valid = first["error"] is None and _parse_ratings(first["text"], items[plan[0]["i"]]["n"]) is not None`
>
> `if not first_valid:`
> `    _append_record(rpath, {"event": "run_aborted", ... "reason": "first request did not produce parse-valid ratings"})`
>
> `    return [first] + [{"text": None, ... "skipped": True} for _ in plan[1:]]`

Both quotes are source code observations. The ledger confirms that behavior for `openai/gpt-3.5-turbo`:

> `"event": "run_aborted", "model": "openai/gpt-3.5-turbo", ... "reason": "first request did not produce parse-valid ratings"`
>
> `"event": "run_finished", "failed_samples": 1, ... "planned_requests": 144, ... "valid_samples": 0`

The clean log supplies the upstream reason:

> `Invalid parameter: 'response_format' of type 'json_schema' is not supported with this model.`
>
> `gpt-3.5-turbo (rated): incomplete items [...] raw evidence is in ... wvs_iw_requests.jsonl; not cached or plotted`

The full model accounting reconstructed from run-finished records from the Pueue interval is:

| result | models | valid / planned | observed request cost |
|---|---|---:|---:|
| complete | gpt-5.6-luna, gpt-5.6-terra, gpt-5.4-nano, gpt-5.4-mini, gpt-5.4, gpt-5.2, gpt-5.1, gpt-5, gpt-5-mini, gpt-oss-120b, gpt-4.1, gpt-4.1-mini, gpt-4.1-nano, gpt-4o-2024-11-20, gpt-4o-2024-08-06, gpt-4o-mini, gpt-4o-mini-2024-07-18, gpt-4o, gpt-3.5-turbo-0613, gpt-3.5-turbo-16k | 2,880 / 2,880 | USD 1.06388504 |
| incomplete, not cached | gpt-oss-20b | 142 / 144 | USD 0.00246639 |
| sample-0 incompatible, not cached | gpt-5.2-chat, o3, o4-mini, o3-mini, gpt-4o-2024-05-13, gpt-3.5-turbo-instruct, gpt-3.5-turbo | 0 / 1 request each | USD 0 |

The lane's total observed response cost is USD 1.066351426. The USD 0.002466388 difference from the complete-panel total is the partial `gpt-oss-20b` panel. It is an exact sum of `request_completed.usage.cost` from these 28 `run_id`s, not a catalog price estimate.

A complete raw output is present for `gpt-4.1` item `Homosexuality`:

> `"content": "{\"0\":1,\"1\":1,\"2\":2,\"3\":3,\"4\":4,\"5\":5,\"6\":5,\"7\":5,\"8\":5,\"9\":5}"`
>
> `"provider": "OpenAI"`
>
> `"usage": {"completion_tokens": 42, ... "prompt_tokens": 258, "total_tokens": 300}`

A contrasting complete request from `gpt-oss-20b` was parseable but carries provider-visible reasoning text and then did not reach 144 valid samples:

> `"provider": "Darkbloom"`
>
> `"content": "{\"0\":3,\"1\":3,...,\"9\":3}"`
>
> `"reasoning": "We need ratings for each key 0-9. Justify homosexuality can be justified? It's controversial. I'll give 3 for all? Perhaps 3 each."`
>
> `"valid_samples": 142`

The raw response records preserve returned `reasoning` fields when the provider supplies them. They do not establish access to hidden chain-of-thought.

## ML-debug form, adapted to this API measurement run

| row | answer |
|---|---|
| log length; config | clean 2,864/2,864 and raw 2,976 lines; 12 items x 12 samples, temperature 1, JSON-schema output, probe-first |
| SHOULD line | `SHOULD: replies are a bare JSON dict ... valid rate near 1.0`; 20 panels reached 144/144, partial/failed panels did not |
| null/baseline | no prediction or baseline coordinate was evaluated; output parse validity, not coordinates, is the lane's resolved condition |
| full sample | `gpt-4.1` quoted above, exact prompt and response retained in ledger |
| surprising rows | `gpt-oss-20b` had 16 rescues and 142 valid; it was not cached, as required |
| missing evidence | semantic response quality, item-level score stability, and billing-account reconciliation |
| second cause for headline | a 144/144 parser rate could still be mechanically valid but semantically degenerate; inspect answer distributions and the separate reliability pilot before interpreting coordinates |
| wall time | 5,874 seconds Pueue duration; serial OpenAI routing is intentional |

## Hypotheses

### H1 [harness | Almost Certain | 95%]

- **Mechanism:** sample-0 probing prevented deterministic JSON-schema incompatibilities from spending the remaining 143 calls.
- **Evidence:** the quoted `run_aborted` ledger record for `gpt-3.5-turbo` follows one `request_failed`, and its `run_finished` records `valid_samples: 0`.
- **Contrary evidence:** no negative control deliberately bypassed the probe, appropriately, so its avoided-call count is inferred from the schedule.
- **Discriminating test:** a local mocked request that returns invalid JSON should produce one request record and 143 skipped requests.
- **Fix/action:** retain this behavior; do not retry these models with a changed schema inside the canonical panel.
- **Interpretability:** yes, for the operational compatibility claim only.

### H2 [data | Highly Likely | 80%]

- **Mechanism:** `gpt-oss-20b` is incomplete due to response/parser instability or provider behavior, not a valid 12-sample coordinate.
- **Evidence:** `run_finished` says `"valid_samples": 142` with `"rescued_samples": 16`; `scripts/wvs_map.py` requires every item to have 12 valid samples and the clean log says it was "not cached or plotted".
- **Contrary evidence:** 142 parsed samples show it is not wholly incompatible.
- **Discriminating test:** an explicitly separate re-evaluation with the same v1 identity only if the owner authorizes it; 144/144 would support transient instability, another shortfall supports incompatibility.
- **Fix/action:** preserve the incomplete raw record and exclude it from the map now.
- **Interpretability:** partial, as provider compatibility evidence, not a WVS coordinate.

### H3 [measurement | Likely | 65%]

- **Mechanism:** the 20 full panels are structurally complete but parser success alone cannot establish meaningful or stable moral-value measurements.
- **Evidence:** the `gpt-oss-20b` raw response quoted above is structurally valid despite the visible reasoning "I'll give 3 for all"; analogous degeneration could occur in fully parsed panels.
- **Contrary evidence:** `gpt-4.1` shows a non-constant first response, and 20 panels have all requested samples.
- **Discriminating test:** the authorized DeepSeek three-replicate pilot distinguishes response-mean sampling noise from a stable v1 coordinate for its seven models.
- **Fix/action:** do not publish fresh coordinates on parser completeness alone; use item/sample distribution and replicate evidence during the later integration audit.
- **Interpretability:** partial.

## Decision

- **Resolve-condition verdict:** met operationally. The task specified "retained cache or one-request failure evidence"; 20 complete panels were cached, one partial panel and seven sample-0 failures have raw evidence and are not cached.
- **Prediction check:** no quantitative coordinate prediction was recorded before this lane; the recorded compatibility prediction was supported for successful panels and contradicted for the eight non-complete panels.
- **Earliest unsupported link:** parse-valid JSON -> stable WVS measurement. The DeepSeek pilot measures only seven DeepSeek models, so it will not establish this link for every OpenAI model.
- **Validity:** define invalid as a cached point having fewer than 144 parse-valid samples or an unrecorded config change. P(invalid operational-completion result) is Remote (about 10%): ledger counts, cache absence for incomplete panels, and full logs agree. P(a complete point is a valid substantive measurement) is not estimated here.
- **Three highest-information clues:** (1) 20 exact 144/144 `run_finished` records, (2) sample-0 abort records with zero extra calls, (3) `gpt-oss-20b` absent from cache despite 142 samples.
- **Recommended sequence:** leave raw failure evidence unchanged; let task 1674 finish; audit its replicate distributions before deciding whether any completed panels enter a public refresh. Do not silently alter settings or resubmit the seven incompatible models.

-- PI[k3]
