# Compare human-format WVS respondent packets with dense ratings

Build a versioned WVS evaluator where one API call is one coherent pseudo-respondent, then test one release family against the existing dense evaluator. Keep the experiment on its research branch and do not change the published map.

## User-visible result

Inspect versioned raw respondent packets and an audit comparing old and new WVS coordinate uncertainty for one four-release family under both a shared family location and a linear release trend.

## User voice

- > "ok so lets use this or a branch and try this one one family. maybe gemini is not best by we can choose 4 sequential qwen models for example? and compare uncertainty as implied by the family having to be in one spot or a linear trend. hopefulyl we can compare old and new eval (eval should be versioned too and the output data should have eval version)"
- > "I'm just sauing what id we ask that same way as the humans, how would that look? are we doing it"
- > "btu we woudl of coruse ask seperatly and combine"
- > "how did it refuse, by giving empty answer? like with human we were going to ask to select values, and a no value would be refusals, but we wuld not suggest it"
- > "no don't tell it that's aviable!!! models are told to have no opinion if you make it an option they will always choose it. human didn ot even get that"

## Preferences and spending

- Work on `research/wvs-respondent-packet-v1`; do not merge to `main` or update the published map.
- Use the existing repository USD 80 total limit and at most USD 5 for this stage.
- Worker model: none requested.

## Goals

1. [/] goal: Run and audit `wvs-respondent-packet-v2` on one four-release family
   - One call represents one pseudo-respondent answering the complete selected WVS battery in canonical order. Ask only for the closest listed answer, as in the human administration. Neither the visible prompt nor the JSON schema may offer refusal, null or missing as an allowed answer. Record a provider refusal, empty response or nonconforming answer as refusal after the call; do not rescue it into a substantive answer. Child qualities use the full 11-quality human list and choose up to five; an empty list is substantive none.
   - Preserve the v1 smoke as a stopped design diagnostic: it explicitly returned `refused` for all nine questions because v1 advertised that token. Do not extend v1.
   - Store `eval_version` in every request/response record, respondent row, aggregate, analysis and protocol/cache identity. Save full responses, reasoning, usage, exact route, release and endpoint metadata.
   - Use N=128 whole respondent packets per release after one paid v2 smoke. Bootstrap complete respondent rows so cross-question covariance is retained.
   - Compare the same releases and fixed scoring items under `wvs-score-all-options-v1` and `wvs-respondent-packet-v2`: coordinate SE/CI, refusal and coverage, shifts, constant-family scatter, linear-trend scatter, response-noise floors and leave-one-release-out prediction.
   - subtle failure mode: isolated question calls masquerade as respondents; refusal remains advertised through a hidden response schema; the 10-quality derivative replaces the 11-quality human list; provider or precision changes mimic a release trend; per-item resampling destroys respondent covariance; or an in-sample line through four releases looks precise because it is overfit.
   - discriminator: durable versioned rows reconstruct each complete respondent; old/new analysis uses identical models and items; route metadata shows one serving condition across the family; whole-row bootstrap and leave-one-out results distinguish response noise from family heterogeneity.
   - verify: offline paid-call guard, deterministic reanalysis, ledger reconciliation, full Pueue log audit, and a byte-empty diff for published map artifacts.
   - evidence:

## Future work / out of scope

Publishing or replacing current map coordinates, running all model families, steering experiments and choosing a protocol only because it gives a smoother trend are out of scope.

## Log

### 2026-09-19 v1 smoke stopped

The one v1 smoke on Qwen 3.7 Plus explicitly returned `refused` for all eight ordinary questions and `refused: true` for child qualities. It did not return an empty answer. V1 had advertised refusal in both the visible prompt and schema, unlike the human survey administration. The full v1 panel was not authorized. V2 offers only substantive answers in both the prompt and schema. Refusal is an observed failure to return a usable answer, not an option.

## Interview

### 2026-09-19

> "ok so lets use this or a branch and try this one one family. maybe gemini is not best by we can choose 4 sequential qwen models for example? and compare uncertainty as implied by the family having to be in one spot or a linear trend. hopefulyl we can compare old and new eval (eval should be versioned too and the output data should have eval version)"

Open choice: the saved endpoint inventory has no four-release matched-size Qwen line with both one provider and one known precision. The cleanest Qwen option is the Plus service line on Alibaba: `qwen3.5-plus-02-15`, `qwen3.6-plus`, `qwen3.5-plus-20260420`, `qwen3.7-plus`. It has one provider and product tier, but advertised quantization is `unknown`, and the later 3.5 revision was released after 3.6.

## Learnings

- The prior original-choice pilot used isolated question calls, not coherent respondent packets.
- The saved GlobalOpinionQA derivative has 10 child-quality rows; the human WVS question has 11, including Religious faith.

## Papercuts - problems, gotchas, suggestions

- A mis-targeted request mock previously made paid calls. All paid paths require an independent explicit opt-in.

## Appendix (context, not approved)

Matched-size candidates `qwen3-32b`, `qwen3.5-27b`, `qwen3.6-27b`, `qwen3.8-27b` do not share one known provider/precision route in the saved endpoint snapshot. DeepInfra serves the first three as FP8 but Qwen3.8-27B as BF16, and there is no matched Qwen3.7-27B entry. The four Qwen Plus releases all use Alibaba with quantization reported as unknown and already have complete dense-v1 results.

---
Copied verbatim from the revised .pi/plan/9a9c0a-v2.md on 2026-09-19 by PI[gpt-5.6-terra]; supersedes the v1-named copy (removed). The source of truth for edits remains the .pi plan.
