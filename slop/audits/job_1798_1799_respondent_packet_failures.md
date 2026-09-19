# Audit: failed respondent-packet panel tasks 1798 and 1799

Date: 2026-09-19. Auditor: PI[muse-spark-1.3-contributor]. Task logs copied whole:
`slop/research/wvs/20260919_respondent_packet/pueue_task_1798_clean.log` (36/36 lines),
`pueue_task_1799_clean.log` (48/48 lines). Raw records:
`records/qwen__qwen3.5-plus-02-15/packets.jsonl` (4 events). Attempt ledger:
`request_attempts.jsonl`. Code at dispatch: b55fc9d (1798), 7cef685 (1799).

## Stage table

| stage | task | evidence | spend |
| --- | --- | --- | --- |
| enqueue panel, entrypoint `scripts/wvs_api/10_respondent_packet_v2_panel.sh` | 1798 | `pueue add --group api`, label resolve 512 parsed packets | 0 |
| 1798 crash before any request | 1798 | `FileNotFoundError: ... 'records/qwen__qwen3.5-plus-02-15/packets.jsonl'`, 8 s after start | USD 0 |
| one-line fix (`append_record` creates per-model subdirs) + regression fixture, protocol bytes unchanged | worker | commit 7cef685, offline suites green | 0 |
| requeue after fix | 1799 | same entrypoint, label notes 1798 made no API call | 0 |
| packet 0 rejected 400, auto-retried 3x (same payload hash `a5e0106692269c44`) | 1799 | attempt ledger `request_attempt_failed` x3, `HTTPStatusError`, status 400 | 3 x bound = USD 0.01038336 conservative |
| packet 1 reserved then cancelled in loop teardown, hold leaked | 1799 | record `request_started` packet 1 with no matching settle; ledger `reserved_usd` 0.00346112 | held, not spent |
| hold released after verifying both tasks dead | worker | `reserved_usd` back to 0, conservative untouched | 0 |

Ledger after: conservative USD 0.02056736, provider-reported USD 0.00133664 (unchanged:
rejected 400s are NOT provider spend; only bound charges), completed_phases 2,
failed_phases 6, reserved 0, global reservations empty.

## Exact quotes

1798:
> `FileNotFoundError: [Errno 2] No such file or directory: 'slop/research/wvs/20260919_respondent_packet/records/qwen__qwen3.5-plus-02-15/packets.jsonl'`

1799 provider text (attempt ledger, `qwen/qwen3.5-plus-02-15`, release slug
`qwen/qwen3.5-plus-20260216`):
> `'messages' must contain the word 'json' in some form, to use 'response_format' of type 'json_object'.`
> (`invalid_parameter_error`; the v2 smoke on `qwen/qwen3.7-plus-20260602` accepted the
> identical shape, so the JSON-word requirement is enforced per-endpoint, not per-payload.)

## Provenance

- 1798: pre-existing `append_record` never created parent dirs (the smoke wrote to the
  existing OUT root; the panel writes per-model subdirs). Nothing reached the network.
- 1799: deterministic endpoint rejection (the JSON-word requirement); the triple charge came from the vendored
  `is_retryable_error`, which retries ANY "Provider returned error" message regardless of
  status (`RETRYABLE_ERROR_PATTERNS` in `openrouter_wrapper/retry.py`, verified in the
  cached source). The leaked hold came from `asyncio` teardown cancelling packet 1 between
  reserve and settle with no cancellation handler.

## Ranked diagnoses

1. (blocks panel) Oldest-endpoint JSON-word gate: transport incompatibility, not a model
   refusal and not evidence about the instrument. Fix approved separately (format-only
   sentence; new protocol_id).
2. (accounting) Vendored retry substring retried a deterministic 400 three times. Fix
   approved separately (local HTTP-status gate; fixture: exact 400 shape -> one attempt,
   429/500 -> retry).
3. (accounting) Cancelled phases leaked holds. Fix approved separately (settle + durable
   cancelled record on `CancelledError`, re-raise; fixture: hold zero, spend exactly one
   bound). No double-settle: normal exceptions keep the single existing settle path.
4. (minor) 1798 preflight I/O bug from a record path only the panel exercises. Fixed and
   fixture-covered.

## Verdict

Resolve condition (512 parsed packets) not met. Scientifically uninterpretable (zero
packets), but the engineering failure is localized: one preflight I/O bug, one
deterministic endpoint contract, and two accounting bugs, each with a committed fix and
fixture. No map/main artifacts touched; failed tasks and logs preserved, never cleaned.
