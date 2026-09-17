# Direct-choice priority wave 02 preflight

Checked UTC: `2026-09-17T08:33Z` against the append-only rated and direct-choice request ledgers.

- observed provider cost: USD `5.09957002235`
- priority-phase stop: USD `35`
- global stop: USD `80`
- six-panel conservative reserve: USD `19.84512000`
- observed cost plus all six reserves: USD `24.94469002235`

The aggregate remains below both stops. Each runner repeats its own observed-cost plus reserve check before it sends sample 0. Every panel has 240 balanced direct-choice keys, an isolated cache and ledger, strict schema, and a parse-valid sample-0 compatibility probe.

| exact ID | reasoning | protocol ID | reserve USD |
|---|---|---|---:|
| `openai/gpt-5.6-terra` | `{"effort":"none"}` | `9860a6923ef9c54111e3764280588b4b43395e706329a3a286d2d7db94794ff3` | 9.338880 |
| `openai/gpt-5.4-nano` | `{"effort":"none"}` | `8aeb61dba0aba732cc7f3e8f75bb21c0cc692f9d79c5444e972de8f5a57ce83e` | 0.970752 |
| `openai/gpt-5.4-mini` | `{"effort":"none"}` | `a130ac7f62e407eff6fe0ac8a78c6e0cac603a74a6477d7d5ea1cc9e2b828d89` | 3.502080 |
| `google/gemini-3.6-flash` | `{"effort":"minimal"}` | `4e8a491693ca97ff0bf6ce704a893651a86b1756b0e56a5ebe5fac05c32c6e4f` | 2.949120 |
| `google/gemini-3.5-flash-lite` | `{"effort":"minimal"}` | `24e7aee4cbb982a7b66cd14cbcf6e08a8f2ed80cb6cb132566b5ab1deed17245` | 1.916928 |
| `google/gemini-3.1-flash-lite` | `{"effort":"minimal"}` | `c9517bdfa0b53ccbf0aecb228cee50dc0f9c7abe4e5bf600132afa368b6eac8e` | 1.167360 |

This preflight authorizes only Wave 02. A compatibility failure is durable incomplete evidence, not a reason to alter settings or retry. Each completed task requires its own audit before a later wave.

-- PI[gpt-5.6-terra]
