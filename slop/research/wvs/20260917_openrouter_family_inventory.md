# OpenRouter family inventory, 2026-09-17

Observation, not an evaluation run: this inventory fetched the public OpenRouter catalog at `https://openrouter.ai/api/v1/models`. The returned 444-model JSON is saved beside this file as `20260917_openrouter_models.json`, SHA-256 `940edd61d8103a51322710d8a6baee7f698b64b2cf033a933f0321e15c536fd2`.

Prices below are the catalog `pricing.prompt` and `pricing.completion` fields times 1,000,000, in USD per million tokens. `structured` means the catalog listed `structured_outputs`, not that this project's reader has tested the model. `created` is the catalog timestamp converted to a UTC date. No API model calls were made.

## Comparison method

The map contains 64 display names across 13 families. I compared a display name to the direct catalog ID with the same provider prefix and slug. This finds 63 live direct IDs. The exception is the historical plotted coordinate `gpt-5.3-chat`: `openai/gpt-5.3-chat` is absent from this live catalog, so it is retained as a historical coordinate, not treated as currently hostable.

`Missing` below is deliberately a decision shortlist rather than every old live alias. It includes direct, non-batch, non-free, non-specialized general chat/instruct models that add a newer family release, a current size point, or a same-release sibling. Models predating the latest plotted family member are not a priority for paid expansion. This rule avoids quietly turning a 64-point map into an unbounded historical backfill.

| family | plotted direct IDs, live | latest plotted catalog anchor | missing comparable status |
|---|---:|---|---|
| claude | 4 | `anthropic/claude-fable-5.1`, 2026-09-01 | no newer direct candidate |
| deepseek | 3 | `deepseek/deepseek-v4.1-flash`, 2026-09-10 | no newer direct candidate |
| gemini | 2 | `google/gemini-3.7-flash`, 2026-08-13 | 1 schema-ready candidate |
| gemma | 2 | `google/gemma-4-31b-it`, 2026-04-02 | 1 schema-ready size candidate |
| glm | 1 | `z-ai/glm-5.3`, 2026-08-18 | 1 schema-ready candidate |
| gpt | 4 plus 1 historical-only | `openai/gpt-6-astra`, 2026-09-04 | 1 same-release schema-ready sibling |
| grok | 2 | `x-ai/grok-4.3`, 2026-04-30 | 2 schema-ready candidates, 4.4 absent |
| inkling | 1 | `thinkingmachines/inkling`, 2026-07-17 | 1 candidate, no structured output |
| kimi | 1 | `moonshotai/kimi-k3`, 2026-07-16 | no newer direct candidate |
| llama | 2 | `meta-llama/llama-4-maverick`, 2025-04-05 | no newer direct candidate |
| mistral | 1 | `mistralai/mistral-large-2512`, 2025-12-01 | 5 schema-ready candidates |
| muse | 1 | `meta/muse-spark-1.3`, 2026-09-02 | 1 same-date schema-ready sibling |
| qwen | 39 | `qwen/qwen3.8-flash`, 2026-08-26 | 2 schema-ready 3.8 size/release candidates; one earlier incomplete panel is separately flagged |

## Missing comparable shortlist

| family | exact OpenRouter ID | created UTC | input USD/M | output USD/M | structured | status |
|---|---|---:|---:|---:|---|---|
| gemini | `google/gemini-3.8-flash` | 2026-09-02 | 0.75 | 3.75 | yes | missing, newer Flash |
| gemma | `google/gemma-4-26b-a4b-it` | 2026-04-03 | 0.09 | 0.30 | yes | missing, direct 26B size |
| glm | `z-ai/glm-5.3-flash` | 2026-08-26 | 0.07 | 0.2333 | yes | missing, Flash sibling |
| gpt | `openai/gpt-6-astra-pro` | 2026-09-04 | 10 | 50 | yes | missing, same-day Astra Pro sibling |
| grok | `x-ai/grok-4.6` | 2026-08-12 | 2 | 6 | yes | missing, newer general release |
| grok | `x-ai/grok-4.5` | 2026-07-08 | 2 | 6 | yes | missing, general release, previously attempted incomplete |
| inkling | `thinkingmachines/inkling-small` | 2026-07-30 | 0.45 | 1.2 | no | missing, reader needs a non-schema protocol before use |
| mistral | `mistralai/mistral-medium-3-5` | 2026-04-30 | 1.5 | 7.5 | yes | missing, newer direct release |
| mistral | `mistralai/mistral-small-2603` | 2026-03-16 | 0.15 | 0.6 | yes | missing, newer direct release |
| mistral | `mistralai/ministral-14b-2512` | 2025-12-02 | 0.2 | 0.2 | yes | missing, 14B direct size |
| mistral | `mistralai/ministral-8b-2512` | 2025-12-02 | 0.15 | 0.15 | yes | missing, 8B direct size |
| mistral | `mistralai/ministral-3b-2512` | 2025-12-02 | 0.1 | 0.1 | yes | missing, 3B direct size |
| muse | `meta/muse-spark-1.3-contributor` | 2026-09-02 | 0.1 | 0.2 | yes | missing, same-date catalog sibling |
| qwen | `qwen/qwen3.8-max-0902` | 2026-09-03 | 2 | 6 | yes | missing, later Qwen3.8 Max release |
| qwen | `qwen/qwen3.8-2.4t-a95b` | 2026-08-12 | 2 | 6 | yes | missing, Qwen3.8 2.4T A95B size point |
| qwen | `qwen/qwen3.5-flash-02-23` | 2026-02-25 | 0.065 | 0.26 | yes | missing from published map: both saved full attempts ended 138/144, so exclude unless a completion policy is approved |

The primary evidence for the last Qwen status is the append-only request ledger and its audit, not the catalog. The provider remains hostable, but the saved incomplete attempts are not a publication-eligible 12 by 12 panel.

## Grok version check

Live catalog observation:

| exact ID | created UTC | input USD/M | output USD/M | structured | status |
|---|---:|---:|---:|---|---|
| `x-ai/grok-4.6` | 2026-08-12 | 2 | 6 | yes | exists, missing comparable candidate |
| `x-ai/grok-4.5` | 2026-07-08 | 2 | 6 | yes | exists, missing comparable candidate; saved WVS attempts incomplete |
| `x-ai/grok-4.3` | 2026-04-30 | 2 | 6 | yes | exists and plotted |
| `x-ai/grok-4.20` | 2026-03-30 | 2 | 6 | yes | exists and plotted |
| `x-ai/grok-4.4` | -- | -- | -- | -- | absent from this 2026-09-17 catalog snapshot |

This is a direct absence check in the saved catalog, not proof that no provider will ever host 4.4.

## Excluded variants, reported separately

The thirteen target-provider prefixes contain 306 catalog records. I excluded 73 `:batch` aliases and five `:free` aliases from the shortlist because they are pricing/routes rather than independently comparable models.

Notable specialized or non-general exclusions:

| exact ID | reason |
|---|---|
| `x-ai/grok-4.20-multi-agent` | multi-agent variant |
| `x-ai/grok-build-0.1` | build/experimental variant, not a named general release |
| `deepseek/deepseek-v4-flash-vision-exp` | vision experimental variant |
| `mistralai/devstral-2512` | coding-focused Devstral |
| `mistralai/voxtral-small-24b-2507` | audio/voice-oriented Voxtral |
| `meta-llama/llama-guard-4-12b` | safeguard model |
| `google/gemini-3.1-flash-image` and `google/gemini-3.1-flash-lite-image` | image generation variants |
| `z-ai/glm-5v-turbo`, `z-ai/glm-4.6v`, `z-ai/glm-4.5v` | vision variants |
| `qwen/qwen3-vl-8b-thinking`, `qwen/qwen3-vl-30b-a3b-thinking`, `qwen/qwen3-vl-235b-a22b-thinking` | vision-language variants |
| `qwen/qwen3-coder-*` | coding variants |

The map retains already measured coder and vision-language Qwen coordinates, but they remain outside the direct-instruct comparison and this expansion shortlist.

## Exhaustive live direct-general appendix

This appendix completes the inventory scope. It lists every current direct general/chat/instruct catalog ID under each plotted family prefix that is not already plotted, excluding `:batch`, `:free`, and the specialized categories listed above. The table is a live-catalog fact list, not a recommendation. Prices and structured-output status use the same definitions as the shortlist.

Status meanings: `shortlisted` appears in the decision table; `incomplete` has saved WVS records but no eligible 144-sample panel; `live general but deprioritized/older` is hostable but not selected for the next paid decision. Plotted IDs are summarized in the following table so their status is explicit without duplicating every already-measured row.

| family | current direct IDs that match plotted display names | historical-only |
|---|---:|---|
| claude | 4 plotted | -- |
| deepseek | 3 plotted | -- |
| gemini | 2 plotted | -- |
| gemma | 2 plotted | -- |
| glm | 1 plotted | -- |
| gpt | 4 plotted | `openai/gpt-5.3-chat` absent from catalog |
| grok | 2 plotted | -- |
| inkling | 1 plotted | -- |
| kimi | 1 plotted | -- |
| llama | 2 plotted | -- |
| mistral | 1 plotted | -- |
| muse | 1 plotted | -- |
| qwen | 39 plotted | -- |

### claude

| exact ID | created UTC | input USD/M | output USD/M | structured | status |
|---|---:|---:|---:|---|---|
| `anthropic/claude-opus-5` | 2026-07-24 | 5 | 25 | yes | live general but deprioritized/older |
| `anthropic/claude-sonnet-5` | 2026-06-30 | 2 | 10 | yes | live general but deprioritized/older |
| `anthropic/claude-fable-5` | 2026-06-09 | 10 | 50 | yes | live general but deprioritized/older |
| `anthropic/claude-sonnet-4.6` | 2026-02-17 | 3 | 15 | yes | live general but deprioritized/older |
| `anthropic/claude-opus-4.5` | 2025-11-24 | 5 | 25 | yes | live general but deprioritized/older |
| `anthropic/claude-haiku-4.5` | 2025-10-15 | 1 | 5 | yes | live general but deprioritized/older |
| `anthropic/claude-sonnet-4.5` | 2025-09-29 | 3 | 15 | yes | live general but deprioritized/older |
| `anthropic/claude-opus-4.1` | 2025-08-05 | 15 | 75 | no | live general but deprioritized/older |
| `anthropic/claude-opus-4` | 2025-05-22 | 15 | 75 | no | live general but deprioritized/older |
| `anthropic/claude-sonnet-4` | 2025-05-22 | 3 | 15 | no | live general but deprioritized/older |
| `anthropic/claude-3-haiku` | 2024-03-13 | 0.25 | 1.25 | no | live general but deprioritized/older |

### deepseek

| exact ID | created UTC | input USD/M | output USD/M | structured | status |
|---|---:|---:|---:|---|---|
| `deepseek/deepseek-v4-pro-0813` | 2026-08-12 | 0.66 | 1.98 | yes | live general but deprioritized/older |
| `deepseek/deepseek-v4-flash-0731` | 2026-07-31 | 0.06 | 0.12 | yes | live general but deprioritized/older |
| `deepseek/deepseek-v3.2` | 2025-12-01 | 0.269 | 0.4 | yes | live general but deprioritized/older |
| `deepseek/deepseek-v3.2-exp` | 2025-09-29 | 0.27 | 0.41 | yes | live general but deprioritized/older |
| `deepseek/deepseek-v3.1-terminus` | 2025-09-22 | 0.27 | 1 | yes | live general but deprioritized/older |
| `deepseek/deepseek-chat-v3.1` | 2025-08-21 | 0.25 | 0.95 | yes | live general but deprioritized/older |
| `deepseek/deepseek-r1-0528` | 2025-05-28 | 0.5 | 2.15 | yes | live general but deprioritized/older |
| `deepseek/deepseek-chat-v3-0324` | 2025-03-24 | 0.25 | 1 | yes | live general but deprioritized/older |
| `deepseek/deepseek-r1-distill-llama-70b` | 2025-01-23 | 0.8 | 0.8 | no | live general but deprioritized/older |
| `deepseek/deepseek-r1` | 2025-01-20 | 0.7 | 2.5 | no | live general but deprioritized/older |
| `deepseek/deepseek-chat` | 2024-12-26 | 0.2574 | 1.0287 | yes | live general but deprioritized/older |

### gemini

| exact ID | created UTC | input USD/M | output USD/M | structured | status |
|---|---:|---:|---:|---|---|
| `google/gemini-3.8-flash` | 2026-09-02 | 0.75 | 3.75 | yes | shortlisted |
| `google/gemini-3.6-flash` | 2026-07-21 | 0.75 | 3.75 | yes | live general but deprioritized/older |
| `google/gemini-3.5-flash-lite` | 2026-07-21 | 0.3 | 2.5 | yes | live general but deprioritized/older |
| `google/gemini-3.5-flash` | 2026-05-19 | 1.5 | 9 | yes | live general but deprioritized/older |
| `google/gemini-3.1-flash-lite` | 2026-05-07 | 0.25 | 1.5 | yes | live general but deprioritized/older |
| `google/gemini-3.1-flash-lite-preview` | 2026-03-03 | 0.25 | 1.5 | yes | live general but deprioritized/older |
| `google/gemini-3.1-pro-preview` | 2026-02-19 | 2 | 12 | yes | live general but deprioritized/older |
| `google/gemini-3-flash-preview` | 2025-12-17 | 0.5 | 3 | yes | live general but deprioritized/older |
| `google/gemini-2.5-flash-lite` | 2025-07-22 | 0.1 | 0.4 | yes | live general but deprioritized/older |
| `google/gemini-2.5-flash` | 2025-06-17 | 0.3 | 2.5 | yes | live general but deprioritized/older |
| `google/gemini-2.5-pro-preview` | 2025-06-05 | 1.25 | 10 | yes | live general but deprioritized/older |

### gemma

| exact ID | created UTC | input USD/M | output USD/M | structured | status |
|---|---:|---:|---:|---|---|
| `google/gemma-4-26b-a4b-it` | 2026-04-03 | 0.09 | 0.3 | yes | shortlisted |
| `google/gemma-3-4b-it` | 2025-03-13 | 0.05 | 0.1 | yes | live general but deprioritized/older |
| `google/gemma-3-12b-it` | 2025-03-13 | 0.05 | 0.15 | yes | live general but deprioritized/older |
| `google/gemma-2-27b-it` | 2024-07-13 | 0.65 | 0.65 | yes | live general but deprioritized/older |

### glm

| exact ID | created UTC | input USD/M | output USD/M | structured | status |
|---|---:|---:|---:|---|---|
| `z-ai/glm-5.3-flash` | 2026-08-26 | 0.07 | 0.2333 | yes | shortlisted |
| `z-ai/glm-5.2` | 2026-06-16 | 1.4 | 4.4 | yes | live general but deprioritized/older |
| `z-ai/glm-5.1` | 2026-04-07 | 0.966 | 3.036 | yes | live general but deprioritized/older |
| `z-ai/glm-5-turbo` | 2026-03-15 | 1.2 | 4 | no | live general but deprioritized/older |
| `z-ai/glm-5` | 2026-02-11 | 0.6 | 1.92 | yes | live general but deprioritized/older |
| `z-ai/glm-4.7-flash` | 2026-01-19 | 0.0605 | 0.4 | yes | live general but deprioritized/older |
| `z-ai/glm-4.7` | 2025-12-22 | 0.4 | 1.75 | yes | live general but deprioritized/older |
| `z-ai/glm-4.6` | 2025-09-30 | 0.43 | 1.75 | yes | live general but deprioritized/older |
| `z-ai/glm-4.5` | 2025-07-25 | 0.6 | 2.2 | no | live general but deprioritized/older |
| `z-ai/glm-4.5-air` | 2025-07-25 | 0.13 | 0.85 | no | live general but deprioritized/older |

### gpt

| exact ID | created UTC | input USD/M | output USD/M | structured | status |
|---|---:|---:|---:|---|---|
| `openai/gpt-6-astra-pro` | 2026-09-04 | 10 | 50 | yes | shortlisted |
| `openai/gpt-5.6-luna-pro` | 2026-07-09 | 0.2 | 1.2 | yes | live general but deprioritized/older |
| `openai/gpt-5.6-luna` | 2026-07-09 | 0.2 | 1.2 | yes | live general but deprioritized/older |
| `openai/gpt-5.6-terra-pro` | 2026-07-09 | 2 | 12 | yes | live general but deprioritized/older |
| `openai/gpt-5.6-terra` | 2026-07-09 | 2 | 12 | yes | live general but deprioritized/older |
| `openai/gpt-5.6-sol-pro` | 2026-07-09 | 2 | 10 | yes | live general but deprioritized/older |
| `openai/gpt-chat-latest` | 2026-05-05 | 5 | 30 | yes | live general but deprioritized/older |
| `openai/gpt-5.5-pro` | 2026-04-24 | 30 | 180 | yes | live general but deprioritized/older |
| `openai/gpt-5.4-nano` | 2026-03-17 | 0.2 | 1.25 | yes | live general but deprioritized/older |
| `openai/gpt-5.4-mini` | 2026-03-17 | 0.75 | 4.5 | yes | live general but deprioritized/older |
| `openai/gpt-5.4-pro` | 2026-03-05 | 30 | 180 | yes | live general but deprioritized/older |
| `openai/gpt-5.2-chat` | 2025-12-10 | 1.75 | 14 | yes | live general but deprioritized/older |
| `openai/gpt-5.2-pro` | 2025-12-10 | 21 | 168 | yes | live general but deprioritized/older |
| `openai/gpt-5.2` | 2025-12-10 | 1.75 | 14 | yes | live general but deprioritized/older |
| `openai/gpt-5.1` | 2025-11-13 | 1.25 | 10 | yes | live general but deprioritized/older |
| `openai/gpt-5-pro` | 2025-10-06 | 15 | 120 | yes | live general but deprioritized/older |
| `openai/gpt-5` | 2025-08-07 | 1.25 | 10 | yes | live general but deprioritized/older |
| `openai/gpt-5-mini` | 2025-08-07 | 0.25 | 2 | yes | live general but deprioritized/older |
| `openai/gpt-5-nano` | 2025-08-07 | 0.05 | 0.4 | yes | live general but deprioritized/older |
| `openai/gpt-oss-120b` | 2025-08-05 | 0.037 | 0.17 | yes | live general but deprioritized/older |
| `openai/gpt-oss-20b` | 2025-08-05 | 0.03 | 0.13 | yes | live general but deprioritized/older |
| `openai/o3-pro` | 2025-06-10 | 20 | 80 | yes | live general but deprioritized/older |
| `openai/o4-mini-high` | 2025-04-16 | 1.1 | 4.4 | yes | live general but deprioritized/older |
| `openai/o3` | 2025-04-16 | 2 | 8 | yes | live general but deprioritized/older |
| `openai/o4-mini` | 2025-04-16 | 1.1 | 4.4 | yes | live general but deprioritized/older |
| `openai/gpt-4.1` | 2025-04-14 | 2 | 8 | yes | live general but deprioritized/older |
| `openai/gpt-4.1-mini` | 2025-04-14 | 0.4 | 1.6 | yes | live general but deprioritized/older |
| `openai/gpt-4.1-nano` | 2025-04-14 | 0.1 | 0.4 | yes | live general but deprioritized/older |
| `openai/o1-pro` | 2025-03-19 | 150 | 600 | yes | live general but deprioritized/older |
| `openai/o3-mini-high` | 2025-02-12 | 1.1 | 4.4 | yes | live general but deprioritized/older |
| `openai/o3-mini` | 2025-01-31 | 1.1 | 4.4 | yes | live general but deprioritized/older |
| `openai/o1` | 2024-12-17 | 15 | 60 | yes | live general but deprioritized/older |
| `openai/gpt-4o-2024-11-20` | 2024-11-20 | 2.5 | 10 | yes | live general but deprioritized/older |
| `openai/gpt-4o-2024-08-06` | 2024-08-06 | 2.5 | 10 | yes | live general but deprioritized/older |
| `openai/gpt-4o-mini` | 2024-07-18 | 0.15 | 0.6 | yes | live general but deprioritized/older |
| `openai/gpt-4o-mini-2024-07-18` | 2024-07-18 | 0.15 | 0.6 | yes | live general but deprioritized/older |
| `openai/gpt-4o` | 2024-05-13 | 2.5 | 10 | yes | live general but deprioritized/older |
| `openai/gpt-4o-2024-05-13` | 2024-05-13 | 5 | 15 | yes | live general but deprioritized/older |
| `openai/gpt-4-turbo` | 2024-04-09 | 10 | 30 | yes | live general but deprioritized/older |
| `openai/gpt-3.5-turbo-0613` | 2024-01-25 | 1 | 2 | yes | live general but deprioritized/older |
| `openai/gpt-3.5-turbo-instruct` | 2023-09-28 | 1.5 | 2 | yes | live general but deprioritized/older |
| `openai/gpt-3.5-turbo-16k` | 2023-08-28 | 3 | 4 | yes | live general but deprioritized/older |
| `openai/gpt-3.5-turbo` | 2023-05-28 | 0.5 | 1.5 | yes | live general but deprioritized/older |
| `openai/gpt-4` | 2023-05-28 | 30 | 60 | yes | live general but deprioritized/older |

### grok

| exact ID | created UTC | input USD/M | output USD/M | structured | status |
|---|---:|---:|---:|---|---|
| `x-ai/grok-4.6` | 2026-08-12 | 2 | 6 | yes | shortlisted |
| `x-ai/grok-4.5` | 2026-07-08 | 2 | 6 | yes | incomplete, do not plot |

### inkling

| exact ID | created UTC | input USD/M | output USD/M | structured | status |
|---|---:|---:|---:|---|---|
| `thinkingmachines/inkling-small` | 2026-07-30 | 0.45 | 1.2 | no | shortlisted |

### kimi

| exact ID | created UTC | input USD/M | output USD/M | structured | status |
|---|---:|---:|---:|---|---|
| `moonshotai/kimi-k2.6` | 2026-04-20 | 0.95 | 4 | yes | live general but deprioritized/older |
| `moonshotai/kimi-k2.5` | 2026-01-27 | 0.45 | 2.25 | yes | live general but deprioritized/older |
| `moonshotai/kimi-k2-thinking` | 2025-11-06 | 0.6 | 2.5 | yes | live general but deprioritized/older |
| `moonshotai/kimi-k2-0905` | 2025-09-04 | 0.6 | 2.5 | yes | live general but deprioritized/older |
| `moonshotai/kimi-k2` | 2025-07-11 | 0.57 | 2.3 | no | live general but deprioritized/older |

### llama

| exact ID | created UTC | input USD/M | output USD/M | structured | status |
|---|---:|---:|---:|---|---|
| `meta-llama/llama-3.3-70b-instruct` | 2024-12-06 | 0.1 | 0.32 | yes | live general but deprioritized/older |
| `meta-llama/llama-3.2-1b-instruct` | 2024-09-25 | 0.027 | 0.201 | no | live general but deprioritized/older |
| `meta-llama/llama-3.2-3b-instruct` | 2024-09-25 | 0.05 | 0.33 | yes | live general but deprioritized/older |
| `meta-llama/llama-3.1-70b-instruct` | 2024-07-23 | 0.4 | 0.4 | yes | live general but deprioritized/older |
| `meta-llama/llama-3.1-8b-instruct` | 2024-07-23 | 0.05 | 0.08 | yes | live general but deprioritized/older |

### mistral

| exact ID | created UTC | input USD/M | output USD/M | structured | status |
|---|---:|---:|---:|---|---|
| `mistralai/mistral-medium-3-5` | 2026-04-30 | 1.5 | 7.5 | yes | shortlisted |
| `mistralai/mistral-small-2603` | 2026-03-16 | 0.15 | 0.6 | yes | shortlisted |
| `mistralai/ministral-14b-2512` | 2025-12-02 | 0.2 | 0.2 | yes | shortlisted |
| `mistralai/ministral-8b-2512` | 2025-12-02 | 0.15 | 0.15 | yes | shortlisted |
| `mistralai/ministral-3b-2512` | 2025-12-02 | 0.1 | 0.1 | yes | shortlisted |
| `mistralai/mistral-medium-3.1` | 2025-08-13 | 0.4 | 2 | yes | live general but deprioritized/older |
| `mistralai/mistral-small-3.2-24b-instruct` | 2025-06-20 | 0.09375 | 0.25 | yes | live general but deprioritized/older |
| `mistralai/mistral-medium-3` | 2025-05-07 | 0.4 | 2 | yes | live general but deprioritized/older |
| `mistralai/mistral-small-3.1-24b-instruct` | 2025-03-17 | 0.351 | 0.555 | no | live general but deprioritized/older |
| `mistralai/mistral-saba` | 2025-02-17 | 0.2 | 0.6 | yes | live general but deprioritized/older |
| `mistralai/mistral-small-24b-instruct-2501` | 2025-01-30 | 0.05 | 0.08 | yes | live general but deprioritized/older |
| `mistralai/mistral-large-2407` | 2024-11-19 | 2 | 6 | yes | live general but deprioritized/older |
| `mistralai/mistral-nemo` | 2024-07-19 | 0.019 | 0.03 | yes | live general but deprioritized/older |
| `mistralai/mixtral-8x22b-instruct` | 2024-04-17 | 2 | 6 | yes | live general but deprioritized/older |
| `mistralai/mistral-large` | 2024-02-26 | 2 | 6 | yes | live general but deprioritized/older |

### muse

| exact ID | created UTC | input USD/M | output USD/M | structured | status |
|---|---:|---:|---:|---|---|
| `meta/muse-spark-1.3-contributor` | 2026-09-02 | 0.1 | 0.2 | yes | shortlisted |
| `meta/muse-spark-1.2-contributor` | 2026-08-21 | 0.1 | 0.2 | yes | live general but deprioritized/older |
| `meta/muse-glimmer-30b` | 2026-08-09 | 0.35 | 1.5 | yes | live general but deprioritized/older |
| `meta/muse-spark-1.2` | 2026-08-05 | 1.25 | 4.25 | yes | live general but deprioritized/older |
| `meta/muse-spark-1.1` | 2026-07-16 | 1.25 | 4.25 | yes | live general but deprioritized/older |

### qwen

| exact ID | created UTC | input USD/M | output USD/M | structured | status |
|---|---:|---:|---:|---|---|
| `qwen/qwen3.8-max-0902` | 2026-09-03 | 2 | 6 | yes | shortlisted |
| `qwen/qwen3.8-2.4t-a95b` | 2026-08-12 | 2 | 6 | yes | shortlisted |
| `qwen/qwen3.5-flash-02-23` | 2026-02-25 | 0.065 | 0.26 | yes | incomplete, do not plot |
| `qwen/qwen3-max` | 2025-09-23 | 0.78 | 3.9 | yes | live general but deprioritized/older |
| `qwen/qwen3-next-80b-a3b-thinking` | 2025-09-11 | 0.15 | 1.2 | yes | live general but deprioritized/older |
| `qwen/qwen3-30b-a3b-thinking-2507` | 2025-08-28 | 0.2 | 2.4 | no | live general but deprioritized/older |
| `qwen/qwen3-235b-a22b-thinking-2507` | 2025-07-25 | 0.23 | 2.3 | no | live general but deprioritized/older |

## Decision

No paid expansion was started. The lowest-cost schema-ready additions are the Mistral size points, GLM 5.3 Flash, Gemma 4 26B, and Muse Spark 1.3 Contributor. The most directly requested current additions are Gemini 3.8 Flash, Grok 4.5/4.6, Qwen3.8 Max and 2.4T, and Astra Pro. Inkling Small needs an explicit non-schema reader protocol before it can be compared. The saved incomplete Qwen3.5 Flash and Grok 4.5 records should not be plotted or silently merged into a complete panel.

-- PI[gpt-5.6-terra]
