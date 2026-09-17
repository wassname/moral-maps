# Audit: score-all-options Muse lane, Pueue 1657

-- PI[openai-codex]

## Target and provenance

Task 1657 ran `scripts/wvs_api/06_score_all_options_lane.sh muse` in this worktree and exited 0 after its lane loop. The complete cleaned log is `/home/code/.local/share/pueue/task_logs/1657.log`: `pqlog 1657 100000` reports all 6,574 lines. The durable request ledger is `slop/research/wvs/20260916_openrouter/wvs_iw_requests.jsonl`.

The lane intended to run five `score-all-options` panels, each 12 items x 12 samples. The OpenRouter provider policy required fallback-capable endpoints restricted to `fp8`, `int8`, `bf16`, or `fp16`.

| stage | expected | observed | expected? | clues | consequence |
|---|---|---|---|---|---|
| routing | an endpoint satisfies the whitelist | one Muse endpoint did; four did not | partial | task 1657 log: `failed_routing_step":"Filter by Quantization"` | four panels have no responses |
| responses | 144 parse-valid samples/model | Glimmer: 144/144; four Spark IDs: 0/144 | partial | durable ledger event counts | only Glimmer is reusable |
| accounting | recorded provider cost | Glimmer cost USD 0.05165016; failed IDs have USD 0 usage | yes | `request_completed.usage.cost` | no inferred cost for failures |
| persistence | cache only complete panels | Glimmer cached; failed panels exit nonzero and are not cached/plotted | yes | task summary plus cache | avoids fabricated coordinates |

## Chronological evidence

The lane completed `meta/muse-glimmer-30b`: its ledger has 144 `request_started`, 144 `request_completed`, 144 `answer_parsed`, 12 `item_result`, and one `run_finished`; the run records `valid_samples: 144`, `failed_samples: 0`, `rescued_samples: 0`. Its first stored completion names provider `DeepInfra`. Sum of the 144 recorded completion costs is USD 0.05165016.

Each of `meta/muse-spark-1.3-contributor`, `meta/muse-spark-1.2-contributor`, `meta/muse-spark-1.2`, and `meta/muse-spark-1.1` records 144 starts, 144 failures, zero completions and zero parsed answers. The complete Pueue log states:

> `No endpoints found for the request with quantization: fp8,int8,bf16,fp16 ... "failed_routing_step":"Filter by Quantization"`

This is a routing-policy incompatibility, not a rating result. The lane summary records each as `incomplete score-all-options panel, exit=1; evidence retained`.

## Hypotheses

### H1 [harness | Highly Likely | 90%]

- Mechanism: the approved OSS quantization whitelist has no eligible endpoint for the four Spark entries.
- Evidence: the OpenRouter response quotes `failed_routing_step":"Filter by Quantization"` and all 144 phases of each affected model fail before a completion.
- Contrary evidence: `meta/muse-glimmer-30b` succeeds through the same policy, so the policy itself is not globally malformed.
- Test: inspect a future saved catalog endpoint list for one of the Spark IDs. A listed whitelist quantization would falsify the current availability conclusion.
- Action: retain the raw failures as unavailable-under-policy. Do not relax the whitelist or substitute a lower-precision endpoint.
- Interpretability: no model-coordinate claim for the four Spark IDs; Glimmer is mechanically complete.

### H2 [bug | Highly Likely | 85%]

- Mechanism: the pre-commit lane reader dispatched every planned request after an incompatible first request, rather than stopping the model panel.
- Evidence: each unavailable ID has 144 identical pre-completion failures. This audit's completed task used the version before commit `99c3a28`.
- Contrary evidence: the failures carry no usage cost, so the practical spending impact here was zero.
- Test: the committed synthetic smoke for `--api-probe-first` should show one attempted request and `run_aborted` when its first response is invalid.
- Action: commit `99c3a28` adds the first-request parse-valid probe to future lanes; it records `run_aborted` and skips the remaining 143 requests.
- Interpretability: the availability result remains clear, but this task was not an efficient compatibility probe.

## Decision

**Resolve-condition verdict: partial.** The lane retained complete cache evidence for Glimmer and failure evidence for four unavailable-under-policy IDs. It did not complete all five requested panels.

**Validity:** Glimmer's mechanical completion is credible. The four failed panels are invalid as coordinate measurements, but credible as routing failures. No inference about their WVS values is supported.

**Recommended sequence:** allow independent queued lanes to use commit `99c3a28`; it stops a model after an incompatible sample 0. Keep the four Spark panels excluded unless a saved catalog revision supplies a whitelisted endpoint.
