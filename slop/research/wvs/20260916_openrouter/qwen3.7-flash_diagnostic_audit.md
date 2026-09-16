# WVS request-ledger audit

Source: `slop/research/wvs/20260916_openrouter/wvs_iw_requests.jsonl`.

## `qwen/qwen3.7-flash`

| metric | value |
|---|---:|
| dispatched phases | 286 |
| completed phases | 286 |
| initial completed | 144 |
| rescue completed | 142 |
| failed request phases | 0 |
| parsed valid samples | 129 |
| item results | 12 |
| provider generation IDs retained | 286 |

| provider usage field | total |
|---|---:|
| prompt_tokens | 111447 |
| completion_tokens | 305854 |
| reasoning_tokens | unknown |
| cache_read_input_tokens | unknown |
| cache_write_input_tokens | unknown |
| total_tokens | 417301 |
| cost | 0.0431044 |

Generation IDs are retained verbatim in the source ledger.

- count: 286
- SHA-256 of sorted IDs: `cc086d2bf2a98cfbeb60ed4115e28c97ae10e12fca2de5822a11e41c64b2f880`
- first: `gen-1789564110-0WjESzJzswz5Y7xtD8zR`
- last: `gen-1789564677-xagE7T7PleXCYY3fF0aM`

| item | valid | requested | failed | rescues | parse rate |
|---|---:|---:|---:|---:|---:|
| Homosexuality | 10 | 12 | 0 | 12 | 0.833 |
| dealing with people? | 12 | 12 | 0 | 12 | 1.000 |
| Signing a petition | 12 | 12 | 0 | 12 | 1.000 |
| Attending peaceful demonstrations | 12 | 12 | 0 | 12 | 1.000 |
| Joining in boycotts | 12 | 12 | 0 | 11 | 1.000 |
| Religion | 12 | 12 | 0 | 12 | 1.000 |
| God | 12 | 12 | 0 | 11 | 1.000 |
| Abortion | 12 | 12 | 0 | 12 | 1.000 |
| Obedience | 6 | 12 | 0 | 12 | 0.500 |
| Independence | 10 | 12 | 0 | 12 | 0.833 |
| Determination, perseverance | 8 | 12 | 0 | 12 | 0.667 |
| Imagination | 11 | 12 | 0 | 12 | 0.917 |

Provider `cost` is reported only when the raw OpenRouter usage object exposed it. Missing usage fields are unknown, not zero. -- PI[gpt-5.6-terra]
