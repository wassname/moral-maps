# Audit: wvs-respondent-packet-v2 paid smoke (qwen/qwen3.7-plus, packet seed 0)

Date: 2026-09-19. Commit: d9307a8 (script) + this audit. Auditor: PI[muse-spark-1.3-contributor].
Raw records: `slop/research/wvs/20260919_respondent_packet/paid_smoke_v2.jsonl` (3 events:
request_started, request_completed, respondent_parsed, all phase `initial`, all
eval_version `wvs-respondent-packet-v2`). Summary: `paid_smoke_summary.json`.
Spend authority: single-smoke approval seq 150; the 512-call panel was not queued.

## What was sent

- Model `qwen/qwen3.7-plus`, temperature 1.0, max_tokens 2048, seed 392427931
  (paired seed index 0), reasoning disabled, provider pin Alibaba, no fallbacks.
- Prompt (4010 chars): "You are one person answering a social values survey. Answer every
  question as yourself, in order: choose the listed answer first, then give its short
  reason." Machine-checked on the sent text: no refusal/null/AI-identity language.
- Schema `wvs_respondent_packet` (strict): 8 ordinary questions, each requiring
  `[selected, reason]` with `selected` enum exactly the listed options; child requires
  `[selected, reason]` with `selected` a 0..5 array of the 11 listed qualities.
  Machine-checked on the sent schema: no `refused`, no null anywhere.

## What came back

- One response, no rescue (the reply parsed first try; rescue triggers only on
  unparseable/truncated JSON).
- 9/9 substantive, 0 refusals. Bounded comparison: the same model gave 9/9 refusal under v1
  versus 9/9 substantive under v2. This is consistent with the advertised refusal token
  causing the v1 result, but n=1 and the added reason fields do not isolate causality.
- Every reason has 6-7 words, status `valid`. Child selected 5 qualities
  (Feeling of responsibility; Tolerance and respect for other people; Independence;
  Imagination; Determination, perseverance). Observation, not inference: reason
  lengths cluster at 6-7 of the allowed 8, so length alone carries little signal; the
  audit value is in the text (e.g. "Love is a fundamental human right." next to
  "Always justifiable").
- Full per-question selections and reasons are in the raw record, not repeated here.

## Route and usage

- Route: requested `qwen/qwen3.7-plus`, response model `qwen/qwen3.7-plus`, provider
  Alibaba, release slug `qwen/qwen3.7-plus-20260602`, advertised quantization `unknown`
  (as preregistered; single serving condition, no fallback).
- Reasoning: message `reasoning` None, usage `reasoning_tokens` 0; disabled confirmed.
- Usage: 1048 prompt / 360 completion / 1408 total tokens; provider-reported cost
  USD 0.00079616, inside the USD 0.00294912 smoke bound.

## Ledger reconciliation

- Local stage ledger: conservative 0.00938784 -> 0.01018400 (+0.00079616, exactly the
  provider-reported cost, so no bound-charging occurred); provider-reported 0.00054048 ->
  0.00133664 (+0.00079616); completed_phases 1 -> 2; reserved back to 0;
  failed_phases_charged_at_bound unchanged at 3. Hard stop USD 5 untouched.
- Global ledger: reservation settled as
  `pilot/resp-packet-smoke/20260919T091356.312349Z: 0.00079616`; reservations empty.
- v1 diagnostic (`paid_smoke.jsonl`, eval v1, all-nine-refused) preserved untouched.

## Conclusion

The v2 instrument works end to end on the first live call: substantive-only schema,
audited reasons, pinned route, cost inside bound, ledgers reconciled. This smoke does
not establish a refusal rate (n=1) and does not select any protocol; the full panel
still needs explicit approval.
