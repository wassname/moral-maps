# WVS latest-label selection

The static map and `docs/wvs/wvs_map_data.json` label exactly one model for each plotted family. The code is `scripts/wvs_map.py:LEGACY_LATEST` plus the saved OpenRouter `created` metadata in `docs/img/wvs/wvs_model_metadata.json`.

- Catalog-backed families use the maximum saved `created` date. This is the release-order source, not numeric parsing.
- Four historical families have no saved catalog entries. Their explicit choices are: Gemma `gemma-4-31b-it`, Grok `grok-4.3`, Llama `llama-4-maverick`, Mistral `mistral-large-2512`.
- The Grok choice is constrained by the README's observed series, which says it ends at Grok 4.3. The single Mistral point is necessarily its own label. The Gemma and Llama choices are recorded explicit legacy decisions rather than fabricated release dates.

`latest_by_family` in the generated web JSON retains the selected name and source category. -- PI[gpt-5.6-terra]
