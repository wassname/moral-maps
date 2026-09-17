# React release panels, public deployment check

Checked 2026-09-17 after `f93a609` (`Add dated release scatter panels to React WVS map`) was pushed.

- URL: `https://wassname.github.io/moral-maps/wvs/react/`
- Public HTML is 170 bytes and names `assets/index-C5aVwI6z.js` and `assets/index-Ctfw88gw.css`.
- Public files exactly match local production artifacts, checked with `cmp`.
- Public `https://wassname.github.io/moral-maps/wvs/wvs_map_data.json` exactly matches the local shared JSON.

| artifact | SHA-256 |
|---|---|
| `index.html` | `bbb653dff6c1bf4ddeab10dd5c4fb5a2a14291c16b59a9845cdd7aa1537d5a5f` |
| `assets/index-C5aVwI6z.js` | `8fee180c2d13fbf0a57910d1a7a03a39b6abe0067c34b7418c3c9bfad11c468a` |
| `assets/index-Ctfw88gw.css` | `679b239f9dc9a310f0dee25afa30851590ab9b460fe289cfd57f4625c0b3b269` |

Observation: the public React page and shared coordinate artifact serve the reviewed `f93a609` bytes. This is a file-identity check, not a rerun of interaction UAT.

-- PI[gpt-5.6-terra]
