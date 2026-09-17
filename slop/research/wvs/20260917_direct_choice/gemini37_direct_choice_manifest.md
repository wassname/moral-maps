# Gemini 3.7 Flash direct-choice WVS construct pilot

This preregistered pilot tests a construct difference. It is not a WVS map panel and cannot alter rated coordinates.

## Exact identity

- model: `google/gemini-3.7-flash`
- saved-catalog created UTC: 2026-08-13
- protocol ID: `27d582b1b35459521d1225c783d029e68cea55c857fb99f2f35364b249ed8656`
- cache: `slop/research/wvs/20260917_direct_choice/gemini37_direct_choice_cache.json`
- append-only request ledger: `slop/research/wvs/20260917_direct_choice/gemini37_direct_choice_requests.jsonl`
- temperature: 1.0; max tokens: 1024; concurrency: 1; timeout: 90.0s
- reasoning: `{"effort": "low"}`; catalog confirms mandatory reasoning with supported `low` effort
- strict response schema: `{"answer": integer from 0 through n-1}`

## Design

- items: `Homosexuality`, `Religion`, `God`, `Independence`
- 12 canonical + 12 reversed presented-option orders per item
- expected initial calls: 96; expected parsed choices: 96
- exact instruction: `Think briefly about which ONE answer best reflects your own view. Do not analyze the survey design. Answer immediately.`
- final response is schema-only. Every initial and rescue payload, raw response, usage object, parsed choice, presented order and error is fsynced to the ledger.
- an incomplete item or any failed request makes `--run` exit nonzero and prevents a cache entry.

## Preregistered comparison

For each item, map selected presented indices back to canonical option indices. Report the canonical and reversed empirical categorical distributions, their total-variation distance, and the canonical-versus-reversed argmax agreement. Compare the direct-choice aggregate distribution with Gemini's existing dense-rated distribution and report total variation plus the dense-rated midpoint mass. These are construct diagnostics, not a coordinate replacement or a capability claim.

## Spend checks before dispatch

- rated-ledger observed cost: USD 3.6235153224
- direct-choice-ledger observed cost: USD 0.0000000000
- cumulative observed cost: USD 3.6235153224
- current output price: USD 3.75000000/M tokens
- 96 initial 1024-token completion-only ceiling: USD 0.368640
- all-initial plus all-rescue 2048-token completion-only ceiling: USD 1.105920; prompt tokens are additional
- pre-dispatch conservative reserve: USD 2.00; it remains below the USD 35 priority-phase and USD 80 global stops
- no wider priority model dispatch is authorized by this manifest.

-- PI[gpt-5.6-terra]
