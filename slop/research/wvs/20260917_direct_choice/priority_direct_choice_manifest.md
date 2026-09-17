# Direct-choice priority manifest, prepared but not dispatched

This manifest prepares the reviewed direct-choice protocol for future panels. It queues and authorizes no API request. Dense-rated panels remain a separate legacy/proxy layer and cannot be mixed with these outputs in coordinates, family summaries, or capability fits.

## Shared direct-choice identity

- saved catalog: `slop/research/wvs/20260917_openrouter_models.json`, SHA-256 `940edd61d8103a51322710d8a6baee7f698b64b2cf033a933f0321e15c536fd2`
- 12 WVS items x 20 samples/item = 240 initial requests/model
- deterministic balanced cyclic rotations: exact option-position balance for n=2,4,10 and registered nearest 6/7 balance for n=3
- prompt: `Think briefly about which ONE answer best reflects the values expressed by your behavior as this AI assistant. Do not analyze the survey design or discuss lacking personal beliefs. Answer immediately.`
- final response: `Respond with ONLY a JSON object with exactly one key named answer. Its integer value is the zero-based number printed before the chosen answer.`
- rescue response: `Return only the one-key object required by the response schema. No explanation.`
- strict structured output; each model has an isolated append-only ledger, cache, and model-specific protocol ID

## Spend checks before any later dispatch

- observed provider cost across current rated and direct-choice ledgers: USD 3.89710257235
- priority phase hard stop: USD 35; global hard stop: USD 80
- per-model reserve assumes 240 initial 1024-token completions plus 240 possible 2048-token rescues and 512 prompt tokens per phase; it is a pre-dispatch limit, not an observed cost
- the runner refuses a new model if current observed ledger cost plus its reserve reaches either stop
- no model below is dispatched by this commit

## Ordered panels

The order is Grok, OpenAI, Google, then Muse. `minimal` is used when catalog metadata advertises it; otherwise `low`; disabled is used only when the catalog says reasoning is optional and accepts `none`.

| family | exact ID | created UTC | input USD/M | output USD/M | reasoning | structured | protocol ID | calls | completion-only ceiling | conservative reserve | isolated ledger |
|---|---|---:|---:|---:|---|---|---|---:|---:|---:|---|
| Grok | `x-ai/grok-4.6` | 2026-08-12 | 2.000000 | 6.000000 | `{"effort": "low"}` (low) | yes | `f1dcc6e5e4651add7df5473e80ba5b5a5ec733d788a6a791625776501f8605d6` | 240 | USD 1.4746 | USD 4.9152 | `slop/research/wvs/20260917_direct_choice/priority/x-ai__grok-4.6_requests.jsonl` |
| Grok | `x-ai/grok-4.5` | 2026-07-08 | 2.000000 | 6.000000 | `{"effort": "low"}` (low) | yes | `fdb4ff16d7879cd840722b7f84654da2e67bc388cdf0b52ea64a1d12b487de18` | 240 | USD 1.4746 | USD 4.9152 | `slop/research/wvs/20260917_direct_choice/priority/x-ai__grok-4.5_requests.jsonl` |
| OpenAI | `openai/gpt-5.6-luna` | 2026-07-09 | 0.2000000 | 1.2000000 | `{"effort": "low"}` (low) | yes | `b9bd5e38934aeae851dcd6227403c474e41c52ebb0bf599b112203b30403e718` | 240 | USD 0.2949 | USD 0.9339 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-5.6-luna_requests.jsonl` |
| OpenAI | `openai/gpt-5.6-terra` | 2026-07-09 | 2.000000 | 12.000000 | `{"effort": "low"}` (low) | yes | `76c8b34537d9ec301ec168c8566849a0a0d26fffa088b70b8da09acb760130b1` | 240 | USD 2.9491 | USD 9.3389 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-5.6-terra_requests.jsonl` |
| OpenAI | `openai/gpt-5.4-nano` | 2026-03-17 | 0.2000000 | 1.25000000 | `{"effort": "low"}` (low) | yes | `a25533b578ada960251c7fa244a98b86e68a054346d641b6215888a09c92b09e` | 240 | USD 0.3072 | USD 0.9708 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-5.4-nano_requests.jsonl` |
| OpenAI | `openai/gpt-5.4-mini` | 2026-03-17 | 0.75000000 | 4.5000000 | `{"effort": "low"}` (low) | yes | `42e8c091233072fd0925ab8f5554bc01e23c5cf3051e09ba7b45970af189fb10` | 240 | USD 1.1059 | USD 3.5021 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-5.4-mini_requests.jsonl` |
| OpenAI | `openai/gpt-5.2-chat` | 2025-12-10 | 1.75000000 | 14.000000 | `null` (not advertised) | yes | `6911c78f8c33d085e4d2e4a627c8e311059855cfb859b16a6a319185b6abb807` | 240 | USD 3.4406 | USD 10.7520 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-5.2-chat_requests.jsonl` |
| OpenAI | `openai/gpt-5.2` | 2025-12-10 | 1.75000000 | 14.000000 | `{"effort": "low"}` (low) | yes | `6d72c036f9f413fa500c0a2902750b0a2c29fc1145d77d3fa02ecf89b48054ff` | 240 | USD 3.4406 | USD 10.7520 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-5.2_requests.jsonl` |
| OpenAI | `openai/gpt-5.1` | 2025-11-13 | 1.25000000 | 10.00000 | `{"effort": "low"}` (low) | yes | `063cbfba0812ff35df231154d69a498e77cd240961d61f18913e6465c1ac1938` | 240 | USD 2.4576 | USD 7.6800 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-5.1_requests.jsonl` |
| OpenAI | `openai/gpt-5` | 2025-08-07 | 1.25000000 | 10.00000 | `{"effort": "minimal"}` (minimal) | yes | `48ffd6a149a5583355dd779b855e944ba26e4eab9b9cd4b5acd780cb3e3fb4e1` | 240 | USD 2.4576 | USD 7.6800 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-5_requests.jsonl` |
| OpenAI | `openai/gpt-5-mini` | 2025-08-07 | 0.25000000 | 2.000000 | `{"effort": "minimal"}` (minimal) | yes | `00e8beddc47977c22afa2128d78af2c00acf8ddb87077f427bcb1360ed87a980` | 240 | USD 0.4915 | USD 1.5360 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-5-mini_requests.jsonl` |
| OpenAI | `openai/gpt-oss-120b` | 2025-08-05 | 0.037000000 | 0.17000000 | `{"effort": "low"}` (low) | yes | `25ac3627e4795573424e184ab883ed80e3abb3bfadb0adba94a8e5b1ce659725` | 240 | USD 0.0418 | USD 0.1344 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-oss-120b_requests.jsonl` |
| OpenAI | `openai/gpt-oss-20b` | 2025-08-05 | 0.03000000 | 0.13000000 | `{"effort": "low"}` (low) | yes | `06243dd30d6fb69a30c4b24a9b891b95a25975d7d41b7071a474e4365e856169` | 240 | USD 0.0319 | USD 0.1032 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-oss-20b_requests.jsonl` |
| OpenAI | `openai/o3` | 2025-04-16 | 2.000000 | 8.000000 | `null` (not advertised (optional; omitted)) | yes | `f4054a623913b60fa79beee9aacec15967aa058434835937e4e8af276adf9557` | 240 | USD 1.9661 | USD 6.3898 | `slop/research/wvs/20260917_direct_choice/priority/openai__o3_requests.jsonl` |
| OpenAI | `openai/o4-mini` | 2025-04-16 | 1.1000000 | 4.4000000 | `null` (not advertised (optional; omitted)) | yes | `26873a2a9f3d6530a06368113b903fbc80f673849ed605f1f49963f1f7abb638` | 240 | USD 1.0813 | USD 3.5144 | `slop/research/wvs/20260917_direct_choice/priority/openai__o4-mini_requests.jsonl` |
| OpenAI | `openai/gpt-4.1` | 2025-04-14 | 2.000000 | 8.000000 | `null` (not advertised) | yes | `9a3bb10b7179275010d35313de4a9d8021ca42abb0901414450ef0c6a42f2aea` | 240 | USD 1.9661 | USD 6.3898 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-4.1_requests.jsonl` |
| OpenAI | `openai/gpt-4.1-mini` | 2025-04-14 | 0.4000000 | 1.6000000 | `null` (not advertised) | yes | `59833d4bac77233732006cfada3136d655274a1fba463a994c4bd3107348b642` | 240 | USD 0.3932 | USD 1.2780 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-4.1-mini_requests.jsonl` |
| OpenAI | `openai/gpt-4.1-nano` | 2025-04-14 | 0.1000000 | 0.4000000 | `null` (not advertised) | yes | `91b5e653465ea8562e62d0a5c76895e4dfa9cc774dc777f04268be6643f04cb9` | 240 | USD 0.0983 | USD 0.3195 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-4.1-nano_requests.jsonl` |
| OpenAI | `openai/o3-mini` | 2025-01-31 | 1.1000000 | 4.4000000 | `null` (not advertised (optional; omitted)) | yes | `2a0f497f04f98ce1a6ff53412018721609b993a091a0da4e7c339b5a72b1859c` | 240 | USD 1.0813 | USD 3.5144 | `slop/research/wvs/20260917_direct_choice/priority/openai__o3-mini_requests.jsonl` |
| OpenAI | `openai/gpt-4o-2024-11-20` | 2024-11-20 | 2.5000000 | 10.00000 | `null` (not advertised) | yes | `e558a7bb4fdfbf9c4ddc6cd2f7505850a0779b7f8c02cde480dff902e709674b` | 240 | USD 2.4576 | USD 7.9872 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-4o-2024-11-20_requests.jsonl` |
| OpenAI | `openai/gpt-4o-2024-08-06` | 2024-08-06 | 2.5000000 | 10.00000 | `null` (not advertised) | yes | `ac49e31fe7abf39eadc966e042c72652b063d56d698cf437b76c53411e0a6979` | 240 | USD 2.4576 | USD 7.9872 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-4o-2024-08-06_requests.jsonl` |
| OpenAI | `openai/gpt-4o-mini` | 2024-07-18 | 0.15000000 | 0.6000000 | `null` (not advertised) | yes | `1662dce1e899d6b1060b2dfaa19034935ff097e77114ae42936eb5b52ddc7296` | 240 | USD 0.1475 | USD 0.4792 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-4o-mini_requests.jsonl` |
| OpenAI | `openai/gpt-4o` | 2024-05-13 | 2.5000000 | 10.00000 | `null` (not advertised) | yes | `11a70a549953db006a77522bc587bcf9464f9c601afc7b3d09b0119ade903d99` | 240 | USD 2.4576 | USD 7.9872 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-4o_requests.jsonl` |
| OpenAI | `openai/gpt-3.5-turbo-0613` | 2024-01-25 | 1.000000 | 2.000000 | `null` (not advertised) | yes | `3b8af120356177e5159f76ee1736a89695006f54cd3055b2c2588ec9050374c6` | 240 | USD 0.4915 | USD 1.7203 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-3.5-turbo-0613_requests.jsonl` |
| OpenAI | `openai/gpt-3.5-turbo-instruct` | 2023-09-28 | 1.5000000 | 2.000000 | `null` (not advertised) | yes | `74b3ad3c9d06e892a0c08968419e330a7a8a91e5db7393e23c31f41c97139967` | 240 | USD 0.4915 | USD 1.8432 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-3.5-turbo-instruct_requests.jsonl` |
| OpenAI | `openai/gpt-3.5-turbo-16k` | 2023-08-28 | 3.000000 | 4.000000 | `null` (not advertised) | yes | `07953ad5d1b968e61ff14f3ef8337e407d128295918855be42d7a0993acb0e32` | 240 | USD 0.9830 | USD 3.6864 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-3.5-turbo-16k_requests.jsonl` |
| OpenAI | `openai/gpt-3.5-turbo` | 2023-05-28 | 0.5000000 | 1.5000000 | `null` (not advertised) | yes | `446953742af525795631082baf5f3df86027c1710d1003ca6054f6e2a48dc18f` | 240 | USD 0.3686 | USD 1.2288 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-3.5-turbo_requests.jsonl` |
| Google | `google/gemini-3.8-flash` | 2026-09-02 | 0.75000000 | 3.75000000 | `{"effort": "low"}` (low) | yes | `1e42dbfead6255ca8efab8f522b5c7684cd8eec6035059bfdf1fdac5d40dc3ae` | 240 | USD 0.9216 | USD 2.9491 | `slop/research/wvs/20260917_direct_choice/priority/google__gemini-3.8-flash_requests.jsonl` |
| Google | `google/gemini-3.6-flash` | 2026-07-21 | 0.75000000 | 3.75000000 | `{"effort": "minimal"}` (minimal) | yes | `4524a90e3320fb15103d7468b5e8088ab99c73051539240d0c1ae14d353d7eac` | 240 | USD 0.9216 | USD 2.9491 | `slop/research/wvs/20260917_direct_choice/priority/google__gemini-3.6-flash_requests.jsonl` |
| Google | `google/gemini-3.5-flash-lite` | 2026-07-21 | 0.3000000 | 2.5000000 | `{"effort": "minimal"}` (minimal) | yes | `0f44f6e4ebb50ece2ada37707d79b988d36fc55a207f23235bb38740e7726b01` | 240 | USD 0.6144 | USD 1.9169 | `slop/research/wvs/20260917_direct_choice/priority/google__gemini-3.5-flash-lite_requests.jsonl` |
| Google | `google/gemini-3.5-flash` | 2026-05-19 | 1.5000000 | 9.000000 | `{"effort": "minimal"}` (minimal) | yes | `fab233d2ad1205b7fa4c2346875105509219846ceeeb7fd292d209615473c231` | 240 | USD 2.2118 | USD 7.0042 | `slop/research/wvs/20260917_direct_choice/priority/google__gemini-3.5-flash_requests.jsonl` |
| Google | `google/gemini-3.1-flash-lite` | 2026-05-07 | 0.25000000 | 1.5000000 | `{"effort": "minimal"}` (minimal) | yes | `c325d9a280a083263f3705cf8d7fa8d4733877cb733526c2fe2290948d3ac4a4` | 240 | USD 0.3686 | USD 1.1674 | `slop/research/wvs/20260917_direct_choice/priority/google__gemini-3.1-flash-lite_requests.jsonl` |
| Google | `google/gemma-4-26b-a4b-it` | 2026-04-03 | 0.09000000 | 0.3000000 | `null` (not advertised (optional; omitted)) | yes | `08d96b55bfee15010d2b9053f40c21d8e1d23d912ef84c645eb810eaa8803f1a` | 240 | USD 0.0737 | USD 0.2433 | `slop/research/wvs/20260917_direct_choice/priority/google__gemma-4-26b-a4b-it_requests.jsonl` |
| Google | `google/gemini-3.1-flash-lite-preview` | 2026-03-03 | 0.25000000 | 1.5000000 | `{"effort": "minimal"}` (minimal) | yes | `4a85c0754b9bd2903c6cc978b2ded49ca381bc0e90199bff6eaf53e42d03e879` | 240 | USD 0.3686 | USD 1.1674 | `slop/research/wvs/20260917_direct_choice/priority/google__gemini-3.1-flash-lite-preview_requests.jsonl` |
| Google | `google/gemini-3-flash-preview` | 2025-12-17 | 0.5000000 | 3.000000 | `{"effort": "minimal"}` (minimal) | yes | `1c64e2725648b42570c0c0bd443655de81ee55c0477bdc835ff4c1087a76cded` | 240 | USD 0.7373 | USD 2.3347 | `slop/research/wvs/20260917_direct_choice/priority/google__gemini-3-flash-preview_requests.jsonl` |
| Google | `google/gemini-2.5-flash-lite` | 2025-07-22 | 0.1000000 | 0.4000000 | `null` (not advertised (optional; omitted)) | yes | `f5dbbdf216a4373df531ec7fef4a02fcec6e89609aa13553bb1f903dc8e0a43b` | 240 | USD 0.0983 | USD 0.3195 | `slop/research/wvs/20260917_direct_choice/priority/google__gemini-2.5-flash-lite_requests.jsonl` |
| Google | `google/gemini-2.5-flash` | 2025-06-17 | 0.3000000 | 2.5000000 | `null` (not advertised (optional; omitted)) | yes | `4d8587d1f7a72ee96a78e2693aec222cba6d313c5fcc978b82b27508d736a223` | 240 | USD 0.6144 | USD 1.9169 | `slop/research/wvs/20260917_direct_choice/priority/google__gemini-2.5-flash_requests.jsonl` |
| Muse | `meta/muse-spark-1.2` | 2026-08-05 | 1.25000000 | 4.25000000 | `{"effort": "minimal"}` (minimal) | yes | `a716da6000adc3d9792e112c55d516e21c49fbe46acac6517d8b740e81b30e69` | 240 | USD 1.0445 | USD 3.4406 | `slop/research/wvs/20260917_direct_choice/priority/meta__muse-spark-1.2_requests.jsonl` |
| Muse | `meta/muse-spark-1.1` | 2026-07-16 | 1.25000000 | 4.25000000 | `{"effort": "minimal"}` (minimal) | yes | `c4cd8eedebc35b380c52d7c559f87c293623a04858b8acfeb091145340dde72d` | 240 | USD 1.0445 | USD 3.4406 | `slop/research/wvs/20260917_direct_choice/priority/meta__muse-spark-1.1_requests.jsonl` |

## Exclusions

- Already plotted dense-rated IDs are not repeated in this prepared direct-choice list, including Grok 4.3/4.20, GPT-6 Astra, GPT-5.6 Sol, GPT-5.5, GPT-5.4, GPT-5.3 Chat, Gemini 3.7 Flash, Gemini 2.5 Pro, and Muse 1.3.
- GPT-5 Nano is retained as a completed dense-rated protocol diagnostic, not silently relabelled as a direct-choice panel.
- Pro/Fast, batch/free aliases, output price above USD 15/M, and code/image/audio/safeguard/multi-agent entries remain excluded. `Flash` is included where it is a general chat model.
- `openai/o4-mini-high` and `openai/o3-mini-high` are excluded because their catalog entries advertise only `high` reasoning, not the registered minimal/low policy.
- The deferred Qwen/GLM/Mistral shortlist remains outside this priority manifest until a direct-choice expansion decision is made.

## Later execution only after review

`scripts/wvs_direct_choice_priority.py --model <exact-id> --smoke` validates one saved entry without network requests. The corresponding `--run` is intentionally not invoked or queued here; it requires a reviewed manifest match and the spend checks above.

-- PI[gpt-5.6-terra]
