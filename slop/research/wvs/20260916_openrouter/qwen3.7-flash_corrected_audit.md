# WVS request-ledger audit

Source: `slop/research/wvs/20260916_openrouter/wvs_iw_requests.jsonl`.

## `qwen/qwen3.7-flash` run `20260916T132258Z_c2918219d8c3`

| metric | value |
|---|---:|
| dispatched phases | 210 |
| completed phases | 210 |
| initial completed | 144 |
| rescue completed | 66 |
| failed request phases | 0 |
| parsed valid samples | 79 |
| distinct initial item/sample keys | 144 |
| item results | 12 |
| publication eligible 12 x 12 panel | False |
| provider generation IDs retained | 210 |

| provider usage field | total |
|---|---:|
| prompt_tokens | 37168 |
| completion_tokens | 3296 |
| reasoning_tokens | unknown |
| cache_read_input_tokens | unknown |
| cache_write_input_tokens | unknown |
| total_tokens | 40464 |
| cost | 0.00154352 |

Generation IDs are retained verbatim in the source ledger.

- count: 210
- SHA-256 of sorted IDs: `a74412a88aadb5680eb0e2ef024ade648d5a0582f95c100fcd41b207cdeff4a6`
- first: `gen-1789564978-OX84XgDxxwyp2BHhOb7y`
- last: `gen-1789565251-LwqX85RylwSHRU5XdYk9`

| item | valid | requested | failed | rescues | parse rate |
|---|---:|---:|---:|---:|---:|
| Homosexuality | 12 | 12 | 0 | 0 | 1.000 |
| dealing with people? | 12 | 12 | 0 | 0 | 1.000 |
| Signing a petition | 4 | 12 | 0 | 8 | 0.333 |
| Attending peaceful demonstrations | 4 | 12 | 0 | 8 | 0.333 |
| Joining in boycotts | 8 | 12 | 0 | 4 | 0.667 |
| Religion | 0 | 12 | 0 | 12 | 0.000 |
| God | 9 | 12 | 0 | 3 | 0.750 |
| Abortion | 11 | 12 | 0 | 1 | 0.917 |
| Obedience | 6 | 12 | 0 | 6 | 0.500 |
| Independence | 3 | 12 | 0 | 9 | 0.250 |
| Determination, perseverance | 4 | 12 | 0 | 8 | 0.333 |
| Imagination | 6 | 12 | 0 | 7 | 0.500 |

Provider `cost` is reported only when the raw OpenRouter usage object exposed it. Missing usage fields are unknown, not zero. -- PI[gpt-5.6-terra]
