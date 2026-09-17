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

## Decision

No paid expansion was started. The lowest-cost schema-ready additions are the Mistral size points, GLM 5.3 Flash, Gemma 4 26B, and Muse Spark 1.3 Contributor. The most directly requested current additions are Gemini 3.8 Flash, Grok 4.5/4.6, Qwen3.8 Max and 2.4T, and Astra Pro. Inkling Small needs an explicit non-schema reader protocol before it can be compared. The saved incomplete Qwen3.5 Flash and Grok 4.5 records should not be plotted or silently merged into a complete panel.

-- PI[gpt-5.6-terra]
