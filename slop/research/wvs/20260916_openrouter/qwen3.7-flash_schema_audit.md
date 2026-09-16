# WVS request-ledger audit

Source: `slop/research/wvs/20260916_openrouter/wvs_iw_requests.jsonl`.

## `qwen/qwen3.7-flash` run `20260916T133001Z_82875b6ee164`

| metric | value |
|---|---:|
| dispatched phases | 144 |
| completed phases | 144 |
| initial completed | 144 |
| rescue completed | 0 |
| failed request phases | 0 |
| parsed valid samples | 144 |
| distinct initial item/sample keys | 144 |
| item results | 12 |
| publication eligible 12 x 12 panel | True |
| provider generation IDs retained | 144 |

| provider usage field | total |
|---|---:|
| prompt_tokens | 22752 |
| completion_tokens | 3240 |
| reasoning_tokens | unknown |
| cache_read_input_tokens | unknown |
| cache_write_input_tokens | unknown |
| total_tokens | 25992 |
| cost | 0.00110376 |

Generation IDs are retained verbatim in the source ledger.

- count: 144
- SHA-256 of sorted IDs: `81e6b4bd61af3a862439f5ae7e88533a5841bcce08bc3354df6167189a69fb7c`
- first: `gen-1789565401-ePJlW2zJ71smju2BHp28`
- last: `gen-1789565562-TLgEuGlGDT65plHRQuWl`

| item | valid | requested | failed | rescues | parse rate |
|---|---:|---:|---:|---:|---:|
| Homosexuality | 12 | 12 | 0 | 0 | 1.000 |
| dealing with people? | 12 | 12 | 0 | 0 | 1.000 |
| Signing a petition | 12 | 12 | 0 | 0 | 1.000 |
| Attending peaceful demonstrations | 12 | 12 | 0 | 0 | 1.000 |
| Joining in boycotts | 12 | 12 | 0 | 0 | 1.000 |
| Religion | 12 | 12 | 0 | 0 | 1.000 |
| God | 12 | 12 | 0 | 0 | 1.000 |
| Abortion | 12 | 12 | 0 | 0 | 1.000 |
| Obedience | 12 | 12 | 0 | 0 | 1.000 |
| Independence | 12 | 12 | 0 | 0 | 1.000 |
| Determination, perseverance | 12 | 12 | 0 | 0 | 1.000 |
| Imagination | 12 | 12 | 0 | 0 | 1.000 |

Provider `cost` is reported only when the raw OpenRouter usage object exposed it. Missing usage fields are unknown, not zero. -- PI[gpt-5.6-terra]
