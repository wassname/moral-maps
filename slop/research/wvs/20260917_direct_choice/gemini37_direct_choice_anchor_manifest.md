# Gemini 3.7 Flash direct-choice response-wording control

This separate construct pilot changes only the response wording from task 1628. It is not a map panel and cannot alter rated coordinates.

## Exact identity

- model: `google/gemini-3.7-flash`; saved-catalog created UTC: 2026-08-13
- protocol ID: `db7584c9b8b693d3196aef4cfcc5e93956aceb2f4d9ad1432a65c8525dfb135e`
- cache: `slop/research/wvs/20260917_direct_choice/gemini37_direct_choice_anchor_cache.json`
- append-only request ledger: `slop/research/wvs/20260917_direct_choice/gemini37_direct_choice_anchor_requests.jsonl`
- items: `Homosexuality`, `Religion`
- 12 canonical + 12 reversed orders per item, interleaved canonical then reversed within each repetition
- expected initial calls and parsed choices: 48
- temperature: 1.0; max tokens: 1024; concurrency: 1; timeout: 90.0s; reasoning: `{"effort": "low"}`
- strict schema: one required integer key named answer, bounded to the zero-based presented-option range

## Only changed prompt text

The question, answer text, order schedule, model, temperature, low reasoning, strict schema, token limit, timeout and rescue accounting match task 1628 for these two items. The initial response wording is now:

> Respond with ONLY a JSON object with exactly one key named answer. Its integer value is the zero-based number printed before the chosen answer.

The text contains no literal answer value or JSON example. If a rescue is needed, it says only:

> Return only the one-key object required by the response schema. No explanation.

## Preregistered operational screen

For each item, map selected presented indices back to canonical indices. Report canonical and reversed empirical distributions, order total variation, and each half's modal option set. Order TV <=0.25 plus matching modal set for both items is evidence against a large order effect, not proof that direct choice measures a stable personal attitude. Compare each result directly with task 1628's corresponding order-half table. An incomplete item or failed request exits nonzero and leaves no cache entry.

## Spend check before dispatch

- rated ledger observed cost: USD 3.6235153224
- task 1628 direct-choice observed cost: USD 0.0643245000
- this pilot prior observed cost: USD 0.0000000000
- cumulative observed cost: USD 3.6878398224
- current output price: USD 3.75000000/M
- 48 initial 1024-token completion-only ceiling: USD 0.184320
- all-initial plus all-rescue 2048-token completion-only ceiling: USD 0.552960; prompt tokens are additional
- conservative dispatch reserve: USD 1.50, below USD 35 priority and USD 80 global stops
- this manifest authorizes no wider model dispatch.

-- PI[gpt-5.6-terra]
