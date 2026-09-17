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
- compatibility probe: run scheduled sample 0 first; a configuration/request failure or a final parse-invalid response after rescue records a failed run and exits before the other 239 requests

## Spend checks before any later dispatch

- observed provider cost across current rated and direct-choice ledgers: USD 3.89710257235
- priority phase hard stop: USD 35; global hard stop: USD 80
- per-model reserve assumes 240 initial 1024-token completions plus 240 possible 2048-token rescues and 512 prompt tokens per phase; it is a pre-dispatch limit, not an observed cost
- the runner refuses a new model if current observed ledger cost plus its reserve reaches either stop
- no model below is dispatched by this commit

## Ordered panels

The order is Grok, OpenAI, Google, then Muse. Optional entries advertising `none` send `reasoning.effort=none`, as documented by OpenRouter. Otherwise `minimal` is used when advertised, then `low`. Optional metadata with no effort list uses an explicitly labelled, unverified `enabled:false` compatibility probe only when the `reasoning` parameter itself is advertised; models with no reasoning metadata omit the field.
- source for `effort=none` and mandatory-model rejection: <https://openrouter.ai/docs/guides/best-practices/reasoning-tokens>, fetched 2026-09-17; the saved catalog's `supported_efforts` remains the exact per-model source.

| family | exact ID | created UTC | input USD/M | output USD/M | reasoning | structured | protocol ID | calls | completion-only ceiling | conservative reserve | isolated ledger |
|---|---|---:|---:|---:|---|---|---|---:|---:|---:|---|
| Grok | `x-ai/grok-4.6` | 2026-08-12 | 2.000000 | 6.000000 | `{"effort": "low"}` (low) | yes | `34224b2e476e87f4e6e904e98a79ba3d2962ccc817925fdb00d7e649b17c81a6` | 240 | USD 1.4746 | USD 4.9152 | `slop/research/wvs/20260917_direct_choice/priority/x-ai__grok-4.6_requests.jsonl` |
| Grok | `x-ai/grok-4.5` | 2026-07-08 | 2.000000 | 6.000000 | `{"effort": "low"}` (low) | yes | `d1362e8b42a4e2ff54cbd66be8c6a65225f94c9679931299f0e5e359e4065c63` | 240 | USD 1.4746 | USD 4.9152 | `slop/research/wvs/20260917_direct_choice/priority/x-ai__grok-4.5_requests.jsonl` |
| OpenAI | `openai/gpt-5.6-luna` | 2026-07-09 | 0.2000000 | 1.2000000 | `{"effort": "none"}` (disabled (optional, none advertised)) | yes | `fe4d5389063d0d6c93c48f21ae162ec1d12155f6c328aab1d2e66caf7a9e522a` | 240 | USD 0.2949 | USD 0.9339 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-5.6-luna_requests.jsonl` |
| OpenAI | `openai/gpt-5.6-terra` | 2026-07-09 | 2.000000 | 12.000000 | `{"effort": "none"}` (disabled (optional, none advertised)) | yes | `9860a6923ef9c54111e3764280588b4b43395e706329a3a286d2d7db94794ff3` | 240 | USD 2.9491 | USD 9.3389 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-5.6-terra_requests.jsonl` |
| OpenAI | `openai/gpt-5.4-nano` | 2026-03-17 | 0.2000000 | 1.25000000 | `{"effort": "none"}` (disabled (optional, none advertised)) | yes | `8aeb61dba0aba732cc7f3e8f75bb21c0cc692f9d79c5444e972de8f5a57ce83e` | 240 | USD 0.3072 | USD 0.9708 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-5.4-nano_requests.jsonl` |
| OpenAI | `openai/gpt-5.4-mini` | 2026-03-17 | 0.75000000 | 4.5000000 | `{"effort": "none"}` (disabled (optional, none advertised)) | yes | `a130ac7f62e407eff6fe0ac8a78c6e0cac603a74a6477d7d5ea1cc9e2b828d89` | 240 | USD 1.1059 | USD 3.5021 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-5.4-mini_requests.jsonl` |
| OpenAI | `openai/gpt-5.2-chat` | 2025-12-10 | 1.75000000 | 14.000000 | `null` (not advertised) | yes | `4f19ecc3869b4328dd5ed3162113fa3c7f285e441c343ac109df17fe5e5e31ca` | 240 | USD 3.4406 | USD 10.7520 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-5.2-chat_requests.jsonl` |
| OpenAI | `openai/gpt-5.2` | 2025-12-10 | 1.75000000 | 14.000000 | `{"effort": "none"}` (disabled (optional, none advertised)) | yes | `bb6322d4ac157f48cc0581c9b4a434f6b77e2f4b37e835799fbdaff845ebaa1f` | 240 | USD 3.4406 | USD 10.7520 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-5.2_requests.jsonl` |
| OpenAI | `openai/gpt-5.1` | 2025-11-13 | 1.25000000 | 10.00000 | `{"effort": "none"}` (disabled (optional, none advertised)) | yes | `80c8c1e4782ee2d85cddfaede339b5f981cfbb2e08525de0ff8fe0b60d9fbe37` | 240 | USD 2.4576 | USD 7.6800 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-5.1_requests.jsonl` |
| OpenAI | `openai/gpt-5` | 2025-08-07 | 1.25000000 | 10.00000 | `{"effort": "minimal"}` (minimal) | yes | `4f7fe97763a5822831b2244e72b0d4cc01ff46da55090fed2485c79f97e4bdf0` | 240 | USD 2.4576 | USD 7.6800 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-5_requests.jsonl` |
| OpenAI | `openai/gpt-5-mini` | 2025-08-07 | 0.25000000 | 2.000000 | `{"effort": "minimal"}` (minimal) | yes | `5b115c7341384a37117745f735367dae10932cc9f16b3fdac5819b5adfe007f4` | 240 | USD 0.4915 | USD 1.5360 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-5-mini_requests.jsonl` |
| OpenAI | `openai/gpt-oss-120b` | 2025-08-05 | 0.037000000 | 0.17000000 | `{"effort": "low"}` (low) | yes | `ae278f4f5e91f668448c4b921633e999ba90a6cd9cc3819c8ee4beac8484d38a` | 240 | USD 0.0418 | USD 0.1344 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-oss-120b_requests.jsonl` |
| OpenAI | `openai/gpt-oss-20b` | 2025-08-05 | 0.03000000 | 0.13000000 | `{"effort": "low"}` (low) | yes | `2b45bec6a0271fb1390ea36e196eef7e75a53112c1dcd1e40b1b60b7631a9d7d` | 240 | USD 0.0319 | USD 0.1032 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-oss-20b_requests.jsonl` |
| OpenAI | `openai/o3` | 2025-04-16 | 2.000000 | 8.000000 | `{"enabled": false}` (unverified compatibility probe (optional reasoning parameter; no efforts advertised)) | yes | `0f658f28a30fe91d97c90672b8028e188b8043d464ec1238dc4acded0cfc2298` | 240 | USD 1.9661 | USD 6.3898 | `slop/research/wvs/20260917_direct_choice/priority/openai__o3_requests.jsonl` |
| OpenAI | `openai/o4-mini` | 2025-04-16 | 1.1000000 | 4.4000000 | `{"enabled": false}` (unverified compatibility probe (optional reasoning parameter; no efforts advertised)) | yes | `eb7a482e589089283c40598692520993d2bb26fe363a8fc0c5e8fe31fcc7a367` | 240 | USD 1.0813 | USD 3.5144 | `slop/research/wvs/20260917_direct_choice/priority/openai__o4-mini_requests.jsonl` |
| OpenAI | `openai/gpt-4.1` | 2025-04-14 | 2.000000 | 8.000000 | `null` (not advertised) | yes | `1f6ad277fcb151d83dd6b0c9d2f9ed5d2cb7466a09b30c4368ec0c74a8d72854` | 240 | USD 1.9661 | USD 6.3898 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-4.1_requests.jsonl` |
| OpenAI | `openai/gpt-4.1-mini` | 2025-04-14 | 0.4000000 | 1.6000000 | `null` (not advertised) | yes | `ce0bb6d5ff9f57496b0f677bb5ac47fc196380e084b457b43f6203d2b7d1b6d1` | 240 | USD 0.3932 | USD 1.2780 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-4.1-mini_requests.jsonl` |
| OpenAI | `openai/gpt-4.1-nano` | 2025-04-14 | 0.1000000 | 0.4000000 | `null` (not advertised) | yes | `0efb6591fbdbe87758af494f18fc0a5a1a4897451dc2bc05f45681e9b5d73758` | 240 | USD 0.0983 | USD 0.3195 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-4.1-nano_requests.jsonl` |
| OpenAI | `openai/o3-mini` | 2025-01-31 | 1.1000000 | 4.4000000 | `{"enabled": false}` (unverified compatibility probe (optional reasoning parameter; no efforts advertised)) | yes | `3ab06ed7aef32190fb8062c01a7d9f1e3e50b2eae8a6dadcf2983ad28d6b0de6` | 240 | USD 1.0813 | USD 3.5144 | `slop/research/wvs/20260917_direct_choice/priority/openai__o3-mini_requests.jsonl` |
| OpenAI | `openai/gpt-4o-2024-11-20` | 2024-11-20 | 2.5000000 | 10.00000 | `null` (not advertised) | yes | `8c3bd515d1ac0e9ee598baa0ad42dc958817e6ad14cad7a73ecd710f71b003a6` | 240 | USD 2.4576 | USD 7.9872 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-4o-2024-11-20_requests.jsonl` |
| OpenAI | `openai/gpt-4o-2024-08-06` | 2024-08-06 | 2.5000000 | 10.00000 | `null` (not advertised) | yes | `64377e05e282d8d9d5dc425635c6acdbf87ae8115aadfb39503c876ad5bbb9ac` | 240 | USD 2.4576 | USD 7.9872 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-4o-2024-08-06_requests.jsonl` |
| OpenAI | `openai/gpt-4o-mini` | 2024-07-18 | 0.15000000 | 0.6000000 | `null` (not advertised) | yes | `388af881427c7032c7a863540b75d7255292a83ee553dcb99eb2d07c7a1766df` | 240 | USD 0.1475 | USD 0.4792 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-4o-mini_requests.jsonl` |
| OpenAI | `openai/gpt-4o` | 2024-05-13 | 2.5000000 | 10.00000 | `null` (not advertised) | yes | `eb4b8ad31eea6d046b4caff46dd0bfb56f113e65111be3871e02ac2e351086e6` | 240 | USD 2.4576 | USD 7.9872 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-4o_requests.jsonl` |
| OpenAI | `openai/gpt-3.5-turbo-0613` | 2024-01-25 | 1.000000 | 2.000000 | `null` (not advertised) | yes | `b0abbb72e5db3b335516292c218a5937a9bc4979fa19b616301b6b969f48c585` | 240 | USD 0.4915 | USD 1.7203 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-3.5-turbo-0613_requests.jsonl` |
| OpenAI | `openai/gpt-3.5-turbo-instruct` | 2023-09-28 | 1.5000000 | 2.000000 | `null` (not advertised) | yes | `3ccab07621e008211a4fed870619e72e1f6568a12aedf955dfd0d8cfc45016a2` | 240 | USD 0.4915 | USD 1.8432 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-3.5-turbo-instruct_requests.jsonl` |
| OpenAI | `openai/gpt-3.5-turbo-16k` | 2023-08-28 | 3.000000 | 4.000000 | `null` (not advertised) | yes | `dfb7fd3c21a1cd90320c754b37d1d78e71d72eec2a1d3a1dfa3af320f7f5b189` | 240 | USD 0.9830 | USD 3.6864 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-3.5-turbo-16k_requests.jsonl` |
| OpenAI | `openai/gpt-3.5-turbo` | 2023-05-28 | 0.5000000 | 1.5000000 | `null` (not advertised) | yes | `b2f3aaa32e5e21e9e89a146ffe48e158fcae7b9b65937fb5bbf64df747bea23c` | 240 | USD 0.3686 | USD 1.2288 | `slop/research/wvs/20260917_direct_choice/priority/openai__gpt-3.5-turbo_requests.jsonl` |
| Google | `google/gemini-3.8-flash` | 2026-09-02 | 0.75000000 | 3.75000000 | `{"effort": "low"}` (low) | yes | `c1a151216652af24dca0a97c85b5d24f45fea8a28caa7075cdf09afb3fb646e7` | 240 | USD 0.9216 | USD 2.9491 | `slop/research/wvs/20260917_direct_choice/priority/google__gemini-3.8-flash_requests.jsonl` |
| Google | `google/gemini-3.6-flash` | 2026-07-21 | 0.75000000 | 3.75000000 | `{"effort": "minimal"}` (minimal) | yes | `4e8a491693ca97ff0bf6ce704a893651a86b1756b0e56a5ebe5fac05c32c6e4f` | 240 | USD 0.9216 | USD 2.9491 | `slop/research/wvs/20260917_direct_choice/priority/google__gemini-3.6-flash_requests.jsonl` |
| Google | `google/gemini-3.5-flash-lite` | 2026-07-21 | 0.3000000 | 2.5000000 | `{"effort": "minimal"}` (minimal) | yes | `24e7aee4cbb982a7b66cd14cbcf6e08a8f2ed80cb6cb132566b5ab1deed17245` | 240 | USD 0.6144 | USD 1.9169 | `slop/research/wvs/20260917_direct_choice/priority/google__gemini-3.5-flash-lite_requests.jsonl` |
| Google | `google/gemini-3.5-flash` | 2026-05-19 | 1.5000000 | 9.000000 | `{"effort": "minimal"}` (minimal) | yes | `4c5c5789977f56c13209d2babb47b3c79cd747fb2cd7cea568bd22301779d16f` | 240 | USD 2.2118 | USD 7.0042 | `slop/research/wvs/20260917_direct_choice/priority/google__gemini-3.5-flash_requests.jsonl` |
| Google | `google/gemini-3.1-flash-lite` | 2026-05-07 | 0.25000000 | 1.5000000 | `{"effort": "minimal"}` (minimal) | yes | `c9517bdfa0b53ccbf0aecb228cee50dc0f9c7abe4e5bf600132afa368b6eac8e` | 240 | USD 0.3686 | USD 1.1674 | `slop/research/wvs/20260917_direct_choice/priority/google__gemini-3.1-flash-lite_requests.jsonl` |
| Google | `google/gemini-3.1-flash-lite-preview` | 2026-03-03 | 0.25000000 | 1.5000000 | `{"effort": "minimal"}` (minimal) | yes | `851a22259abbe2da4fea19fd61b4fb7ce6e0406866e7bf2b54908f91d84cd860` | 240 | USD 0.3686 | USD 1.1674 | `slop/research/wvs/20260917_direct_choice/priority/google__gemini-3.1-flash-lite-preview_requests.jsonl` |
| Google | `google/gemini-3-flash-preview` | 2025-12-17 | 0.5000000 | 3.000000 | `{"effort": "minimal"}` (minimal) | yes | `1529b1845000ea4830c5c7c88e898b6e1d75abaab1aa4a0d86951330cec17200` | 240 | USD 0.7373 | USD 2.3347 | `slop/research/wvs/20260917_direct_choice/priority/google__gemini-3-flash-preview_requests.jsonl` |
| Google | `google/gemini-2.5-flash-lite` | 2025-07-22 | 0.1000000 | 0.4000000 | `{"enabled": false}` (unverified compatibility probe (optional reasoning parameter; no efforts advertised)) | yes | `028b2d617ca65993cc70998b26475c2bb06fc4c0f2f2ec7f0604bb4dc2c7c6c7` | 240 | USD 0.0983 | USD 0.3195 | `slop/research/wvs/20260917_direct_choice/priority/google__gemini-2.5-flash-lite_requests.jsonl` |
| Google | `google/gemini-2.5-flash` | 2025-06-17 | 0.3000000 | 2.5000000 | `{"enabled": false}` (unverified compatibility probe (optional reasoning parameter; no efforts advertised)) | yes | `0162c6349d01c312300afb9cb720820aca663c10e2b9af7cd2fe369f5cb59428` | 240 | USD 0.6144 | USD 1.9169 | `slop/research/wvs/20260917_direct_choice/priority/google__gemini-2.5-flash_requests.jsonl` |
| Muse | `meta/muse-spark-1.2` | 2026-08-05 | 1.25000000 | 4.25000000 | `{"effort": "minimal"}` (minimal) | yes | `5ddf04c58154c758756fb32cd2652f928678170010cf8638dd9cdb1c064522a2` | 240 | USD 1.0445 | USD 3.4406 | `slop/research/wvs/20260917_direct_choice/priority/meta__muse-spark-1.2_requests.jsonl` |
| Muse | `meta/muse-spark-1.1` | 2026-07-16 | 1.25000000 | 4.25000000 | `{"effort": "minimal"}` (minimal) | yes | `fcb191133bbd11dce82ac53f4d6b253a15c316d5abd71c54896f9dfdf644b964` | 240 | USD 1.0445 | USD 3.4406 | `slop/research/wvs/20260917_direct_choice/priority/meta__muse-spark-1.1_requests.jsonl` |

## Exclusions

- Already plotted dense-rated IDs are not repeated in this prepared direct-choice list, including Grok 4.3/4.20, GPT-6 Astra, GPT-5.6 Sol, GPT-5.5, GPT-5.4, GPT-5.3 Chat, Gemini 3.7 Flash, Gemini 2.5 Pro, and Muse 1.3.
- GPT-5 Nano is retained as a completed dense-rated protocol diagnostic, not silently relabelled as a direct-choice panel.
- Pro/Fast, batch/free aliases, output price above USD 15/M, and code/image/audio/safeguard/multi-agent entries remain excluded. `Flash` is included where it is a general chat model.
- `google/gemma-4-26b-a4b-it` is excluded: it is Gemma, not an identified member of the requested Gemini release series.
- `openai/o4-mini-high` and `openai/o3-mini-high` are excluded because their catalog entries advertise only `high` reasoning, not the registered minimal/low policy.
- The deferred Qwen/GLM/Mistral shortlist remains outside this priority manifest until a direct-choice expansion decision is made.

## Later execution only after review

`scripts/wvs_direct_choice_priority.py --model <exact-id> --smoke` validates one saved entry without network requests. The corresponding `--run` is intentionally not invoked or queued here; it requires a reviewed manifest match and the spend checks above.

-- PI[gpt-5.6-terra]
