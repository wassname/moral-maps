# Task 1630 stopped before production result

- Pueue task: 1630, `scripts/wvs_api/04_gemini37_direct_choice_production_pilot.sh`
- label: `why: test full behavior-values direct-choice readout after no-example control; resolve: audit balance, entropy, schedule halves before any other model`
- status: killed at 2026-09-17T11:28:16+08:00 after the protocol-metadata correction arrived
- partial ledger: `slop/research/wvs/20260917_direct_choice/gemini37_direct_choice_production_requests.jsonl`

## Observation

The incomplete run uses the superseded protocol identity and has no parsed samples, item results, run-finished event, or cache entry. Its durable ledger records:

- 1 `run_started`
- 11 `request_started`
- 10 `request_completed`
- 0 `answer_parsed`
- 0 `item_result`
- 0 `request_failed`
- observed completed-request cost: USD 0.0103275

The stopped task cannot supply a production panel and will not be merged with the corrected protocol's future records. The follow-up protocol records the behavioral-values prompt instruction explicitly, so cache identity metadata agrees with the rendered requests.

-- PI[gpt-5.6-terra]
