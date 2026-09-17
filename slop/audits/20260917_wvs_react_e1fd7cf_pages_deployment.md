# Pages deployment audit: e1fd7cf

Fetch UTC: 2026-09-17, scheduled verification after the `e1fd7cf` push.

Public root and local files match:

| artifact | SHA-256 |
|---|---|
| root JS `assets/index-xQcEVNVX.js` | `974418a3e920eee698ff00449de5b4df80f88697bbfa444fb5f37daccb685ddb` |
| root CSS `assets/index-B27UlIE_.css` | `522d567306de17b5c8fa40f59173a8173cc72dca669150db39eb8b214bdf6a94` |
| shared data `wvs/wvs_map_data.json` | `f67f80fb535655e27d1943ca0709cb56aa3f64bc43e6c6943be34badd2fddc4b` |

Observed public routing:

- <https://wassname.github.io/moral-maps/> references `./assets/index-xQcEVNVX.js`.
- <https://wassname.github.io/moral-maps/wvs/> serves `<meta http-equiv="refresh" content="0; url=../">`.
- <https://wassname.github.io/moral-maps/wvs/react/> serves `<meta http-equiv="refresh" content="0; url=../../">`.
- <https://wassname.github.io/moral-maps/wvs/wvs_map_data.json> hashes to the shared local data above.

Conclusion: GitHub Pages serves the reviewed root React bundle, current shared JSON, and both compatibility redirects for commit `e1fd7cf`.

-- PI[gpt-5.6-terra]
