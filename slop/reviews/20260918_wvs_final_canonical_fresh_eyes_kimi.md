# Fresh-eyes review: WVS Pages integration @ 3aa2a09

Read-only review of `docs/img/wvs/wvs_map_iw.png`, the two Playwright screenshots
(`wvs_react_root_playwright_default.png`, `wvs_react_playwright_capability_all_families.png`),
`docs/wvs/wvs_map_data.json`, and `slop/audits/20260918_wvs_final_canonical_integration.md`.

## 1. What the visuals say without being told the conclusion

- A scatter of ~90 country dots with four labeled cultural-zone hulls (West, East Asia,
  Latin America, African-Islamic) forms the familiar Inglehart-Welzel butterfly. ~100+
  star/glyph model marks cluster tightly in the upper-left (secular-rational,
  self-expression) corner, all near or inside the "West" hull, beyond Sweden/Iceland.
  The unstated-but-obvious takeaway: frontier models sit at the extreme
  secular-rational/self-expression edge, past nearly all countries.
- Two release panels show weak descriptive OLS trends: newer models drift slightly more
  secular-rational (R² 0.28) and slightly less self-expressive (R² 0.19); higher HLE
  score associates with more secular-rational (R² 0.27) and less self-expression
  (R² 0.11). The page text correctly calls these "weak descriptive correlations".

## 2. Overlaps / axis / fit-label / duplication issues

- **Axis orientation is mirrored vs the canonical Inglehart-Welzel map.** The horizontal
  axis runs Self-expression (left) → Survival (right); the standard published WVS map
  runs Survival (left) → Self-expression (right). The JSON (`axis.x:
  ["Self-expression","Survival"]`) and the body text ("axes run from Traditional to
  Secular-Rational and from Self-expression to Survival") are internally consistent and
  the data match the labels (Sweden x=-0.670 far left; Egypt x=-0.062 far right), so
  this is a deliberate orientation choice, not a mislabel. It will still read as
  "flipped" to anyone comparing against the canonical WVS figure. Worth a one-line
  caveat; not a blocker.
- **Zone label anchors collide.** In `zone_hulls`, `African-Islamic.label_anchor =
  [-0.26226, 0.31093]` and `Latin America.label_anchor = [-0.25871, 0.30857]` are
  essentially the same point (Δx≈0.004, Δy≈0.002). In the static PNG this places the
  "African-Islamic" label mid-chart, adjacent to the "United States" label and inside
  the West hull's boundary, far from its own members' visual mass (Egypt bottom-right,
  Pakistan bottom-center). In the React screenshot the two labels are separated but both
  sit in the central overlap of all four hulls. Confusing; minor-to-moderate.
- **Hull overlaps make zone membership ambiguous at a glance.** Pakistan's dot and label
  sit inside the orange "Latin America" hull, and Turkey (listed in the African-Islamic
  zone in the JSON) sits inside the blue West hull. Only 4 of the ~9 classic IW zones
  are drawn (71 of 90 countries zoned), so unzoned countries (Pakistan, India, etc.)
  inevitably fall inside foreign hulls. This is a convex-hull artifact, but nothing on
  the page says so. Minor.
- **Static PNG label collisions.** In `wvs_map_iw.png` the "West" hull label is stacked
  directly on top of the "llama-4-maverick" model label, and "kimi-k3" overlaps a star
  glyph. Both remain readable; the React version avoids this. Minor, static-export only.
- **Duplicated title.** The map panel embeds "Moral Maps: Where Do Frontier Models'
  Cultural Values Lie?" + source line inside the chart, duplicating the page H1 directly
  above it. Minor.
- **Inconsistent model label.** The map labels `claude-fable-5.1` as "fable-5.1"
  (JSON `label` field) while the release panels label the same model "claude-fable-5.1".
  Minor inconsistency.
- **Frontier labels look odd in context (but are explained).** Release-date panels mark
  "running HLE score highs among shown mapped models", so labels like
  `qwen3-max-thinking` and `qwen3.5-397b-a17b` appear at the *bottom* of a values chart
  (low self-expression), which reads as "worst values" until you read the caption. The
  caption does explain it. Minor.
- Fit annotations ("OLS, n=97, R² 0.28" / "OLS, n=46, R² 0.27") are legible,
  separated from frontier labels, and n matches the data (see §3). No mislabeled axes
  found; HLE x-axis spans 0.0–0.6 ("fraction correct" per JSON `capability_x.protocol`).

## 3. HLE selector and counts

Understandable and internally consistent:
- Selector line: "Release-panel x axis [Release date ▾ | HLE score ▾] Artificial
  Analysis HLE score, saved 2026-09-17. 46 matched, 62 omitted." 46+62 = 108 = number
  of plotted models (verified: `hle_score` non-null on exactly 46 of 108 entries).
- JSON `capability_x` block carries source URL, fetch time `2026-09-17T10:13:20Z`,
  raw-source SHA-256, and an explicit caveat that the score is "a capability ceiling,
  not the score of the WVS request configuration" — a good disclosure.
- Release-date fit n=97 is explained by data, not a bug: exactly 11 of 108 models
  (10 historical + gemma-4-31b-it etc.) lack `release_created`, and 108−11 = 97.
- `median` in the JSON is the *country* median (verified: -0.2875, 0.3632 matches
  countries, not models) but is undocumented — ambiguous field, trivial.

## 4. Pilot / incomplete-data leak check

No evidence of leakage; audit claims verified against artifacts:
- All 96 `protocol_id`s in the public JSON match keys in
  `wvs_iw_rated.json.completed` (97 records); the single unused cache record is
  `7fe76f95… = "gpt-5-nano (rated)"` (12/12 complete), confirming the documented
  content-quality exclusion and "97 complete cache records" claim.
- Zero overlap between the 96 public `protocol_id`s/`run_id`s and the 22 pilot
  protocol/run IDs found under `slop/research/wvs/20260917_deepseek_reliability/`.
- Provenance counts match the audit exactly: 96 `canonical score-all-options`
  (`items=12, samples=12`) + 12 `historical rounded coordinate` = 108 distinct names;
  zero historical names duplicate a canonical name (the 4 overlapping of the 16
  historical inputs were resolved to canonical as stated).
- 13 families; Grok entries are exactly `grok-4.20, grok-4.3, grok-4.5, grok-4.6` with
  `grok-4.6` the catalog-date latest — all as the audit states.
- No partial panels: every canonical entry has `items=12, samples=12`.

## 5. Blockers vs minor issues

**Blockers: none found.** Data integrity claims in the audit reproduce exactly from the
artifacts; no pilot/incomplete data in the public payload; fits and counts are honest.

**Minor issues (none blocking deployment):**
1. Mirrored horizontal axis vs the canonical IW map — internally consistent, but add a
   note for readers cross-referencing the standard figure.
2. African-Islamic and Latin America `label_anchor`s are near-identical coordinates,
   producing confusing/misplaced zone labels, worst in the static PNG.
3. Unzoned countries (e.g. Pakistan) visually inside foreign hulls with no on-page
   explanation of hull semantics.
4. Static-PNG-only label collisions ("West" over "llama-4-maverick"; "kimi-k3" over a
   glyph).
5. Duplicated in-chart title; map label "fable-5.1" vs panel label "claude-fable-5.1";
   undocumented `median` field.
