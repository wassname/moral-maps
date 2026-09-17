# Final canonical WVS integration

-- PI[k3]

## Observations

- `wvs_iw_rated.json` has 97 complete cache records. `gpt-5-nano` remains excluded from the map because its prior content-quality audit documented systematic neutral/example-like outputs. The public artifact has 108 distinct names: 96 canonical `wvs-score-all-options-v1` entries and 12 distinct historical rounded coordinates. Four historical names overlap canonical names, so the canonical coordinate is shown for each overlap.
- The public artifact contains 13 families. The Grok entries are `grok-4.20`, `grok-4.3`, `grok-4.5`, and `grok-4.6`; the catalog-date latest label is `grok-4.6` (2026-08-12).
- The saved Artificial Analysis HLE mapping supplies 46 matches and 62 omissions among the 108 displayed names. The artifact retains the source URL and fetch time, `2026-09-17T10:13:20Z`.
- No displayed provenance protocol ID belongs to the DeepSeek reliability pilot. Reliability aggregate and incomplete replicate records were not used to generate the map.

## Verification

`uv run --no-project --offline --with 'playwright==1.62.0' python scripts/wvs_react/uat.py` passed. It checks the root and both redirects, 13 family controls, map/country geometry, all four Groks, `grok-4.6` as latest, canonical versus historical provenance, absent pilot IDs, release-date frontier labels without leader lines, capability fits under all-family and family-subset visibility, and accessible SVG titles/descriptions.

I inspected `slop/research/wvs/20260916_openrouter/wvs_react_root_playwright_default.png`. A fresh-eyes review also found the lower-left title/source readable and the revised OLS/frontier labels separated. Its evidence is a read-only reviewer response in this worker session, not a committed file.

## Exclusions

- `gpt-5-nano` is a completed cache diagnostic but is not plotted because its existing content-quality audit excluded it.
- Incomplete/partial score-all-options panels and all DeepSeek reliability-pilot data are excluded.
- The 16 historical rounded inputs remain distinct provenance; four duplicate canonical names resolve to the canonical panel.
