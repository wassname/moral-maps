# WVS priority API phase manifest, 2026-09-17

This exact manifest is generated from the saved 444-record OpenRouter catalog snapshot, not a fresh paid request. It authorizes no calls by itself.

## Guards

- A complete panel is 144 initial calls, 12 items x 12 samples.
- Existing ledger spend is USD 3.5908606724; the global stop remains USD 80.
- This priority phase stops before USD 35 of new observed provider cost, even if the manifest has remaining models.
- Sum of 1024-token completion-only ceilings for all listed priority panels is USD 28.6138. This excludes prompt tokens and rescues, so it is not a spend authorization or a cost prediction.
- Before every model, read cumulative `usage.cost` from the append-only ledger. Do not start a request whose conservative remaining cost could pass the phase or global stop.
- A panel is publishable only as one exact protocol/run with 144 distinct item/sample keys. Never merge the two old incomplete Grok 4.5 attempts.

## Required first diagnostic

Run only this panel before any other manifest model. Audit repeats, parser outcomes, rescues, refusals, cache replay and provider cost before dispatching the priority batch.

| exact ID | created UTC | input USD/M | output USD/M | structured | completion-only 144x1024 ceiling | rationale |
|---|---:|---:|---:|---|---:|---|
| `openai/gpt-5-nano` | 2025-08-07 | 0.05000000 | 0.4000000 | yes | USD 0.0590 | required cheapest new 144-call diagnostic |

## Priority manifest after diagnostic pass

The order is Grok, OpenAI, Google, then the requested Muse points. `Flash` entries are retained because the user excluded `Fast`, not `Flash`.

| exact ID | created UTC | input USD/M | output USD/M | structured | completion-only 144x1024 ceiling | rationale |
|---|---:|---:|---:|---|---:|---|
| **Grok** | | | | | | |
| `x-ai/grok-4.6` | 2026-08-12 | 2.000000 | 6.000000 | yes | USD 0.8847 | new direct panel |
| `x-ai/grok-4.5` | 2026-07-08 | 2.000000 | 6.000000 | yes | USD 0.8847 | clean new full attempt |
| **OpenAI** | | | | | | |
| `openai/gpt-5.6-luna` | 2026-07-09 | 0.2000000 | 1.2000000 | yes | USD 0.1769 | new direct panel |
| `openai/gpt-5.6-terra` | 2026-07-09 | 2.000000 | 12.000000 | yes | USD 1.7695 | new direct panel |
| `openai/gpt-5.4-nano` | 2026-03-17 | 0.2000000 | 1.25000000 | yes | USD 0.1843 | new direct panel |
| `openai/gpt-5.4-mini` | 2026-03-17 | 0.75000000 | 4.5000000 | yes | USD 0.6636 | new direct panel |
| `openai/gpt-5.2-chat` | 2025-12-10 | 1.75000000 | 14.000000 | yes | USD 2.0644 | new direct panel |
| `openai/gpt-5.2` | 2025-12-10 | 1.75000000 | 14.000000 | yes | USD 2.0644 | new direct panel |
| `openai/gpt-5.1` | 2025-11-13 | 1.25000000 | 10.00000 | yes | USD 1.4746 | new direct panel |
| `openai/gpt-5` | 2025-08-07 | 1.25000000 | 10.00000 | yes | USD 1.4746 | new direct panel |
| `openai/gpt-5-mini` | 2025-08-07 | 0.25000000 | 2.000000 | yes | USD 0.2949 | new direct panel |
| `openai/gpt-oss-120b` | 2025-08-05 | 0.037000000 | 0.17000000 | yes | USD 0.0251 | new direct panel |
| `openai/gpt-oss-20b` | 2025-08-05 | 0.03000000 | 0.13000000 | yes | USD 0.0192 | new direct panel |
| `openai/o4-mini-high` | 2025-04-16 | 1.1000000 | 4.4000000 | yes | USD 0.6488 | new direct panel |
| `openai/o3` | 2025-04-16 | 2.000000 | 8.000000 | yes | USD 1.1796 | new direct panel |
| `openai/o4-mini` | 2025-04-16 | 1.1000000 | 4.4000000 | yes | USD 0.6488 | new direct panel |
| `openai/gpt-4.1` | 2025-04-14 | 2.000000 | 8.000000 | yes | USD 1.1796 | new direct panel |
| `openai/gpt-4.1-mini` | 2025-04-14 | 0.4000000 | 1.6000000 | yes | USD 0.2359 | new direct panel |
| `openai/gpt-4.1-nano` | 2025-04-14 | 0.1000000 | 0.4000000 | yes | USD 0.0590 | new direct panel |
| `openai/o3-mini-high` | 2025-02-12 | 1.1000000 | 4.4000000 | yes | USD 0.6488 | new direct panel |
| `openai/o3-mini` | 2025-01-31 | 1.1000000 | 4.4000000 | yes | USD 0.6488 | new direct panel |
| `openai/gpt-4o-2024-11-20` | 2024-11-20 | 2.5000000 | 10.00000 | yes | USD 1.4746 | new direct panel |
| `openai/gpt-4o-2024-08-06` | 2024-08-06 | 2.5000000 | 10.00000 | yes | USD 1.4746 | new direct panel |
| `openai/gpt-4o-mini` | 2024-07-18 | 0.15000000 | 0.6000000 | yes | USD 0.0885 | new direct panel |
| `openai/gpt-4o` | 2024-05-13 | 2.5000000 | 10.00000 | yes | USD 1.4746 | new direct panel |
| `openai/gpt-3.5-turbo-0613` | 2024-01-25 | 1.000000 | 2.000000 | yes | USD 0.2949 | new direct panel |
| `openai/gpt-3.5-turbo-instruct` | 2023-09-28 | 1.5000000 | 2.000000 | yes | USD 0.2949 | new direct panel |
| `openai/gpt-3.5-turbo-16k` | 2023-08-28 | 3.000000 | 4.000000 | yes | USD 0.5898 | new direct panel |
| `openai/gpt-3.5-turbo` | 2023-05-28 | 0.5000000 | 1.5000000 | yes | USD 0.2212 | new direct panel |
| **Google** | | | | | | |
| `google/gemini-3.8-flash` | 2026-09-02 | 0.75000000 | 3.75000000 | yes | USD 0.5530 | new direct panel |
| `google/gemini-3.6-flash` | 2026-07-21 | 0.75000000 | 3.75000000 | yes | USD 0.5530 | new direct panel |
| `google/gemini-3.5-flash-lite` | 2026-07-21 | 0.3000000 | 2.5000000 | yes | USD 0.3686 | new direct panel |
| `google/gemini-3.5-flash` | 2026-05-19 | 1.5000000 | 9.000000 | yes | USD 1.3271 | new direct panel |
| `google/gemini-3.1-flash-lite` | 2026-05-07 | 0.25000000 | 1.5000000 | yes | USD 0.2212 | new direct panel |
| `google/gemma-4-26b-a4b-it` | 2026-04-03 | 0.09000000 | 0.3000000 | yes | USD 0.0442 | new direct panel |
| `google/gemini-3.1-flash-lite-preview` | 2026-03-03 | 0.25000000 | 1.5000000 | yes | USD 0.2212 | new direct panel |
| `google/gemini-3-flash-preview` | 2025-12-17 | 0.5000000 | 3.000000 | yes | USD 0.4424 | new direct panel |
| `google/gemini-2.5-flash-lite` | 2025-07-22 | 0.1000000 | 0.4000000 | yes | USD 0.0590 | new direct panel |
| `google/gemini-2.5-flash` | 2025-06-17 | 0.3000000 | 2.5000000 | yes | USD 0.3686 | new direct panel |
| **Muse** | | | | | | |
| `meta/muse-spark-1.2` | 2026-08-05 | 1.25000000 | 4.25000000 | yes | USD 0.6267 | new direct panel |
| `meta/muse-spark-1.1` | 2026-07-16 | 1.25000000 | 4.25000000 | yes | USD 0.6267 | new direct panel |

## Deferred approved shortlist

These remain eligible only after the priority phase has a passing diagnostic and remaining observed budget. They are not queued by this manifest.

| exact ID | created UTC | input USD/M | output USD/M | structured | completion-only 144x1024 ceiling | rationale |
|---|---:|---:|---:|---|---:|---|
| `qwen/qwen3.8-max-0902` | 2026-09-03 | 2.000000 | 6.000000 | yes | USD 0.8847 | deferred Qwen/GLM/Mistral shortlist |
| `qwen/qwen3.8-2.4t-a95b` | 2026-08-12 | 2.000000 | 6.000000 | yes | USD 0.8847 | deferred Qwen/GLM/Mistral shortlist |
| `z-ai/glm-5.3-flash` | 2026-08-26 | 0.07000000 | 0.2333000000 | yes | USD 0.0344 | deferred Qwen/GLM/Mistral shortlist |
| `mistralai/mistral-medium-3-5` | 2026-04-30 | 1.5000000 | 7.5000000 | yes | USD 1.1059 | deferred Qwen/GLM/Mistral shortlist |
| `mistralai/mistral-small-2603` | 2026-03-16 | 0.15000000 | 0.6000000 | yes | USD 0.0885 | deferred Qwen/GLM/Mistral shortlist |
| `mistralai/ministral-14b-2512` | 2025-12-02 | 0.2000000 | 0.2000000 | yes | USD 0.0295 | deferred Qwen/GLM/Mistral shortlist |
| `mistralai/ministral-8b-2512` | 2025-12-02 | 0.15000000 | 0.15000000 | yes | USD 0.0221 | deferred Qwen/GLM/Mistral shortlist |
| `mistralai/ministral-3b-2512` | 2025-12-02 | 0.1000000 | 0.1000000 | yes | USD 0.0147 | deferred Qwen/GLM/Mistral shortlist |

## Exclusions checked

- Already complete/plotted direct IDs, including Grok 4.3 and 4.20, are excluded.
- `:batch` and `:free` routes, `Pro` and `Fast` IDs, output prices above USD 15/M, and code/image/audio/safeguard/multi-agent variants are excluded.
- `x-ai/grok-4.4` remains absent from the saved catalog.
- `qwen/qwen3.5-flash-02-23` and the prior Grok 4.5 records are retained as incomplete evidence, not plotted or merged.

-- PI[gpt-5.6-terra]
