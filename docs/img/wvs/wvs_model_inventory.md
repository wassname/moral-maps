# OpenRouter WVS model inventory

Checked 2026-09-16 against `slop/research/wvs/20260916_openrouter/openrouter_models_20260916T1303Z.json`. Prices are catalog USD per million tokens. Batch and free aliases are excluded because they duplicate an underlying model. Qwen entries with an expiration date before the check date are excluded. The remaining direct `qwen/` text-capable releases are candidates, not evidence that they completed the panel.

## Requested additions

| exact OpenRouter ID | name | created UTC | input USD/M | output USD/M | status |
|---|---|---:|---:|---:|---|
| `anthropic/claude-fable-5.1` | Anthropic: Claude Fable 5.1 | 2026-09-01 | 10 | 50 | candidate |
| `openai/gpt-6-astra` | OpenAI: GPT-6 Astra | 2026-09-04 | 10 | 50 | candidate |
| `meta/muse-spark-1.3` | Meta: Muse Spark 1.3 | 2026-09-02 | 1.25 | 4.25 | candidate |
| `moonshotai/kimi-k3` | MoonshotAI: Kimi K3 | 2026-07-16 | 2.64814 | 13.2827 | candidate |
| `thinkingmachines/inkling` | Thinking Machines: Inkling | 2026-07-17 | 1 | 4.05 | candidate |
| `deepseek/deepseek-v4.1-flash` | DeepSeek: DeepSeek V4.1 Flash | 2026-09-10 | 0.15 | 0.6 | candidate |
| `z-ai/glm-5.3` | Z.ai: GLM 5.3 | 2026-08-18 | 1.4 | 4.4 | candidate |
| `z-ai/glm-5.3-flash` | Z.ai: GLM 5.3 Flash | 2026-08-26 | 0.09 | 0.3 | candidate |
| `google/gemini-3.7-flash` | Google: Gemini 3.7 Flash | 2026-08-13 | 0.75 | 3.75 | candidate |
| `x-ai/grok-4.5` | SpaceXAI: Grok 4.5 | 2026-07-08 | 2 | 6 | candidate |
| `openai/gpt-5.6-sol` | OpenAI: GPT-5.6 Sol | 2026-07-09 | 2 | 10 | candidate |

## Direct Qwen candidates

| exact OpenRouter ID | name | created UTC | input USD/M | output USD/M | status |
|---|---|---:|---:|---:|---|
| `qwen/qwen3.8-max-0902` | Qwen: Qwen3.8 Max (0902) | 2026-09-03 | 2 | 6 | candidate |
| `qwen/qwen3.8-flash` | Qwen: Qwen3.8 Flash | 2026-08-26 | 0.15 | 0.47 | candidate |
| `qwen/qwen3.8-27b` | Qwen: Qwen3.8 27B | 2026-08-14 | 0.214 | 2.55 | candidate |
| `qwen/qwen3.8-2.4t-a95b` | Qwen: Qwen3.8 2.4T A95B | 2026-08-12 | 2 | 6 | candidate |
| `qwen/qwen3.7-flash` | Qwen: Qwen3.7 Flash | 2026-07-27 | 0.03 | 0.13 | candidate |
| `qwen/qwen3.7-plus` | Qwen: Qwen3.7 Plus | 2026-06-03 | 0.32 | 1.28 | candidate |
| `qwen/qwen3.7-max` | Qwen: Qwen3.7 Max | 2026-05-21 | 1.475 | 4.425 | candidate |
| `qwen/qwen3.5-plus-20260420` | Qwen: Qwen3.5 Plus 2026-04-20 | 2026-04-27 | 0.3 | 1.8 | candidate |
| `qwen/qwen3.6-flash` | Qwen: Qwen3.6 Flash | 2026-04-27 | 0.1875 | 1.125 | candidate |
| `qwen/qwen3.6-35b-a3b` | Qwen: Qwen3.6 35B A3B | 2026-04-27 | 0.1 | 0.9 | candidate |
| `qwen/qwen3.6-max-preview` | Qwen: Qwen3.6 Max Preview | 2026-04-27 | 1.027 | 6.162 | candidate |
| `qwen/qwen3.6-27b` | Qwen: Qwen3.6 27B | 2026-04-27 | 0.3 | 2 | candidate |
| `qwen/qwen3.6-plus` | Qwen: Qwen3.6 Plus | 2026-04-02 | 0.325 | 1.95 | candidate |
| `qwen/qwen3.5-9b` | Qwen: Qwen3.5-9B | 2026-03-10 | 0.1 | 0.15 | candidate |
| `qwen/qwen3.5-35b-a3b` | Qwen: Qwen3.5-35B-A3B | 2026-02-25 | 0.1625 | 1.3 | candidate |
| `qwen/qwen3.5-27b` | Qwen: Qwen3.5-27B | 2026-02-25 | 0.195 | 1.56 | candidate |
| `qwen/qwen3.5-122b-a10b` | Qwen: Qwen3.5-122B-A10B | 2026-02-25 | 0.26 | 2.08 | candidate |
| `qwen/qwen3.5-flash-02-23` | Qwen: Qwen3.5-Flash | 2026-02-25 | 0.065 | 0.26 | candidate |
| `qwen/qwen3.5-plus-02-15` | Qwen: Qwen3.5 Plus 2026-02-15 | 2026-02-16 | 0.26 | 1.56 | candidate |
| `qwen/qwen3.5-397b-a17b` | Qwen: Qwen3.5 397B A17B | 2026-02-16 | 0.55 | 3.5 | candidate |
| `qwen/qwen3-max-thinking` | Qwen: Qwen3 Max Thinking | 2026-02-09 | 0.78 | 3.9 | candidate |
| `qwen/qwen3-coder-next` | Qwen: Qwen3 Coder Next | 2026-02-04 | 0.12 | 0.8 | candidate |
| `qwen/qwen3-vl-32b-instruct` | Qwen: Qwen3 VL 32B Instruct | 2025-10-23 | 0.104 | 0.416 | candidate |
| `qwen/qwen3-vl-8b-thinking` | Qwen: Qwen3 VL 8B Thinking | 2025-10-14 | 0.18 | 2.1 | candidate |
| `qwen/qwen3-vl-8b-instruct` | Qwen: Qwen3 VL 8B Instruct | 2025-10-14 | 0.117 | 0.455 | candidate |
| `qwen/qwen3-vl-30b-a3b-thinking` | Qwen: Qwen3 VL 30B A3B Thinking | 2025-10-06 | 0.2 | 2.4 | candidate |
| `qwen/qwen3-vl-30b-a3b-instruct` | Qwen: Qwen3 VL 30B A3B Instruct | 2025-10-06 | 0.15 | 0.6 | candidate |
| `qwen/qwen3-vl-235b-a22b-thinking` | Qwen: Qwen3 VL 235B A22B Thinking | 2025-09-23 | 0.4 | 4 | candidate |
| `qwen/qwen3-vl-235b-a22b-instruct` | Qwen: Qwen3 VL 235B A22B Instruct | 2025-09-23 | 0.21 | 1.9 | candidate |
| `qwen/qwen3-max` | Qwen: Qwen3 Max | 2025-09-23 | 0.78 | 3.9 | candidate |
| `qwen/qwen3-coder-plus` | Qwen: Qwen3 Coder Plus | 2025-09-23 | 0.65 | 3.25 | candidate |
| `qwen/qwen3-coder-flash` | Qwen: Qwen3 Coder Flash | 2025-09-17 | 0.195 | 0.975 | candidate |
| `qwen/qwen3-next-80b-a3b-thinking` | Qwen: Qwen3 Next 80B A3B Thinking | 2025-09-11 | 0.15 | 1.2 | candidate |
| `qwen/qwen3-next-80b-a3b-instruct` | Qwen: Qwen3 Next 80B A3B Instruct | 2025-09-11 | 0.09 | 1.1 | candidate |
| `qwen/qwen-plus-2025-07-28` | Qwen: Qwen Plus 0728 | 2025-09-08 | 0.26 | 0.78 | candidate |
| `qwen/qwen3-30b-a3b-thinking-2507` | Qwen: Qwen3 30B A3B Thinking 2507 | 2025-08-28 | 0.2 | 2.4 | candidate |
| `qwen/qwen3-coder-30b-a3b-instruct` | Qwen: Qwen3 Coder 30B A3B Instruct | 2025-07-31 | 0.07 | 0.28 | candidate |
| `qwen/qwen3-30b-a3b-instruct-2507` | Qwen: Qwen3 30B A3B Instruct 2507 | 2025-07-29 | 0.04815 | 0.19305 | candidate |
| `qwen/qwen3-235b-a22b-thinking-2507` | Qwen: Qwen3 235B A22B Thinking 2507 | 2025-07-25 | 0.23 | 2.3 | candidate |
| `qwen/qwen3-coder` | Qwen: Qwen3 Coder 480B A35B | 2025-07-23 | 0.3 | 1 | candidate |
| `qwen/qwen3-235b-a22b-2507` | Qwen: Qwen3 235B A22B Instruct 2507 | 2025-07-21 | 0.0875 | 0.35 | candidate |
| `qwen/qwen3-30b-a3b` | Qwen: Qwen3 30B A3B | 2025-04-28 | 0.12 | 0.5 | candidate |
| `qwen/qwen3-8b` | Qwen: Qwen3 8B | 2025-04-28 | 0.117 | 0.455 | candidate |
| `qwen/qwen3-14b` | Qwen: Qwen3 14B | 2025-04-28 | 0.12 | 0.24 | candidate |
| `qwen/qwen3-32b` | Qwen: Qwen3 32B | 2025-04-28 | 0.08 | 0.28 | candidate |
| `qwen/qwen3-235b-a22b` | Qwen: Qwen3 235B A22B | 2025-04-28 | 0.455 | 1.82 | candidate |
| `qwen/qwen2.5-vl-72b-instruct` | Qwen: Qwen2.5 VL 72B Instruct | 2025-02-01 | 0.8 | 1 | candidate |
| `qwen/qwen-plus` | Qwen: Qwen-Plus | 2025-02-01 | 0.26 | 0.78 | candidate |
| `qwen/qwen-2.5-coder-32b-instruct` | Qwen2.5 Coder 32B Instruct | 2024-11-11 | 0.66 | 1 | candidate |
| `qwen/qwen-2.5-7b-instruct` | Qwen: Qwen2.5 7B Instruct | 2024-10-16 | 0.1 | 0.2 | candidate |
| `qwen/qwen-2.5-72b-instruct` | Qwen2.5 72B Instruct | 2024-09-19 | 0.36 | 0.4 | candidate |

The catalog did not contain the requested ID when an addition is marked unavailable. No similar ID was substituted. -- PI[gpt-5.6-terra]
