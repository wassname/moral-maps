# Direct-choice priority wave 01 preflight

- checked UTC: 2026-09-17T05:20Z
- current observed ledger cost: USD 4.51647657235, including Grok 4.6 task 1632 at USD 0.619374
- priority-phase hard stop: USD 35
- global hard stop: USD 80

| model | protocol ID | reasoning payload | 240-call conservative reserve USD |
|---|---|---|---:|
| `x-ai/grok-4.5` | `d1362e8b42a4e2ff54cbd66be8c6a65225f94c9679931299f0e5e359e4065c63` | `{"effort":"low"}` | 4.915200 |
| `openai/gpt-5.6-luna` | `fe4d5389063d0d6c93c48f21ae162ec1d12155f6c328aab1d2e66caf7a9e522a` | `{"effort":"none"}` | 0.9338880 |
| `google/gemini-3.8-flash` | `c1a151216652af24dca0a97c85b5d24f45fea8a28caa7075cdf09afb3fb646e7` | `{"effort":"low"}` | 2.94912000 |

Wave reserve: USD 8.79820800.

Observed plus all three reserves: USD 13.31468457235, below both stops. The runner repeats its per-model observed-cost plus reserve check before each model. Each job has an isolated ledger, cache, and sample-0 compatibility probe. A failed probe remains an incomplete run and is not retried or reconfigured in this wave.

-- PI[gpt-5.6-terra]
