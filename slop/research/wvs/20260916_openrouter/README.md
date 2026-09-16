# WVS OpenRouter evidence

This directory is the persistent source evidence for the 2026-09-16 WVS OpenRouter panel.

- `openrouter_models_20260916T1303Z.json` is the public catalog response used for exact IDs, dates, and prices.
- `wvs_iw_requests.jsonl` is append-only. Each request phase is fsynced before the next await. It holds prompts, presented option order, raw provider responses, usage objects, generation IDs when exposed, parse outcomes, errors, and item summaries.
- `wvs_iw_rated.json` is only a cache of complete coordinate panels. It links each entry to a ledger run and exact protocol hash.

The ledger contains public WVS questions and model responses, not API keys. It is tracked so paid answers remain reusable after this session. -- PI[gpt-5.6-terra]
