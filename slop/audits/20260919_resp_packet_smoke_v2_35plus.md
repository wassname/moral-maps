# Audit: wvs-respondent-packet-v2 compatibility smoke, oldest endpoint

Date: 2026-09-19. Auditor: PI[muse-spark-1.3-contributor]. Code: ef3fb66 (parameterized
smoke target) with run-scoping fix committed separately below. One paid request only;
no retry, no panel.

## Request

- Target `qwen/qwen3.5-plus-02-15`, packet index 0, request seed `392427931` (the first
  paired schedule seed; "seed 0" in the dispatch instruction means packet index 0, not a
  literal seed of zero — no rerun over this wording).
- Current v2 protocol: substantive-only prompt plus the transport sentence
  `Return one JSON object matching the required schema.`, strict schema, reasons required,
  reasoning disabled, Alibaba pinned, no fallbacks.

## Transport result

- HTTP 200. The JSON-word gate that rejected this endpoint's build in task 1799 is gone:
  route validates clean — requested `qwen/qwen3.5-plus-02-15`, response model
  `qwen/qwen3.5-plus-02-15`, provider Alibaba, release slug `qwen/qwen3.5-plus-20260216`,
  advertised quantization `unknown` (as preregistered).
- Usage: 306 completion tokens, reasoning_tokens 0, provider-reported cost USD 0.00075218.

## Parse result (corrected: parser compatibility difference, not refusal)

- The reply used positional keys `"1"`–`"9"` with field `"answer"` instead of question ids
  and `"selected"` (child: `{"answer": ["1","2","6","8","10"], "reason": "..."}`). The
  visible prompt itself numbers the blocks 1..9, letters ordinary options A.., and numbers
  child qualities 1..11, so this encoding is unambiguous: a narrow deterministic normalizer
  maps it to canonical selections with reasons recovered exactly. 9/9 substantive, every
  reason valid, every entry tagged `positional_labels`.
- The original `respondent_parsed` event (kind `nonconforming`, canonical-only parser) is
  preserved untouched; a clearly labeled offline `respondent_reinterpreted` event is
  appended with the new protocol_id (accepted encodings are part of protocol identity),
  and the per-release summary carries the reinterpretation. Shapes never affect scoring:
  one-hot canonical selections are identical either way.
- The run-scoping crash that followed (stale 3.7-plus completion in the shared file failed
  the new target's route check) is fixed separately with a fixture; the first summary was
  reconstructed offline from the single executed request via the committed
  `smoke_summary_dict`.

## Ledger reconciliation

- Smoke cost USD 0.00075218 settled against the reported figure (completed phase, no
  bound-charging). Global reservation for this smoke settled; global reservations empty.
- Local stage ledger after: conservative USD 0.02210706 (includes the earlier 3.7-plus
  repeat and the 3x bound charges from the deterministic 1799 failure), provider-reported
  USD 0.00287634, reserved 0. Rejected 400s are not provider spend; only bound charges.

## Conclusion

Compatibility established at transport, accounting, and parser layers: the oldest
endpoint serves the v2 instrument, and its positional reply is 9/9 substantive with
reasons exact (n=1). No refusal rate, no coordinate, no protocol selection follows.
Stopping before panel dispatch as instructed.
