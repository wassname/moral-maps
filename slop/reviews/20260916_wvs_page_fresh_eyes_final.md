# Fresh-eyes image-only review: WVS page (2026-09-16)

Scope: `slop/research/wvs/20260916_openrouter/wvs_page_local.png`, `slop/research/wvs/20260916_openrouter/wvs_page_qwen_hidden.png`, and `docs/img/wvs/wvs_map_iw.png` (gross-mismatch check only). No files edited. No shell available; everything below is visual inspection of the supplied PNGs.

## 1. Do controls visibly show on/off?

**Observed: YES.**
- `wvs_page_local.png`: the `qwen: qwen3.8-flash` chip (top-left of chip row) is a filled purple pill with white text — same style as all 12 other chips.
- `wvs_page_qwen_hidden.png`: the same chip is rendered as an outlined pill (thin purple border, pale background) with greyed, struck-through text. All other chips are unchanged.
- This matches the page's own description: "Filled chips are visible; an outlined, struck-through chip hides that family's stars and latest-release name."
- The on/off distinction is unambiguous at a glance; the struck-through text is a good redundancy for colour-blind readers.

## 2. Do Qwen stars disappear when the chip is toggled off?

**Observed: NO visible change in the plot that I can detect.**

Comparing the two screenshots star-by-star, the plotted content of the chart looks identical. Specific spot checks (approximate pixel positions in the 1280×1000 screenshot, present in BOTH images):
- Purple star at ~(585, 507), just above/left of the East Asia hull's top-left vertex. In the static map, the star labelled `qwen3.8-flash` sits in exactly this relative position (just above Japan, right of the gemini cluster). If qwen were hidden, this star should be absent in `wvs_page_qwen_hidden.png`; it is still there.
- Purple stars at ~(214, 437), (344, 441), (403, 593), (410, 612), (249, 634), (585, 507), (455, 490), (483, 525) — all present in both images.
- Grey dots, dashed hulls, and region labels ("West", "East Asia", "Latin America", "African-Islamic") are pixel-identical as far as I can see.

Inference (not observed): the chip state toggles but either (a) the star-hiding is not wired to the chip, (b) the screenshot was captured before the re-render, (c) qwen stars are drawn but with a class/opacity that this render does not honour, or (d) qwen's family colour in `wvs_map_data.json` is not the purple I assume and its stars are somewhere I am not distinguishing. Given the static map labels the purple star near Japan as `qwen3.8-flash` and the qwen chip is purple, (d) seems least likely, but I cannot rule it out from images alone.

Also note: the description says hiding a chip removes the "latest-release name", but **no star labels are visible in either screenshot** (no `qwen3.8-flash`, `gpt-6-astra`, etc. text anywhere on the chart), so the label-hiding half of the feature is also unverifiable from these images. Either labels are not rendered in the web version, are hover-only, or are below the visible fold.

**Checks that would disprove/confirm this finding (for the parent, I have no shell):**
- Count `<path>`/star elements (or Plotly trace visibility / d3 selection with the qwen class) in the DOM before and after clicking the chip; expect a drop equal to the qwen family's star count.
- Take the "hidden" screenshot after an explicit wait for re-render (e.g. `await page.waitForFunction(...)` on a data attribute), not immediately after the click.
- Pixel-diff the two PNGs restricted to the plot area (y > 300). If the diff is empty, the stars did not change.
- Grep `wvs_map_data.json` for the qwen family colour and confirm it matches the chip colour (`#7B1FA2`-ish purple) rather than muse's violet — the two are very close visually in both the static map and the chips.

## 3. Other observations on the web screenshots

- **Viewport truncation.** Both screenshots are cut off at y=1000 with a scrollbar visible; the bottom of the chart (the "Traditional" axis label, the x-axis labels "Self-expression"/"Survival", any legend/footer) is not captured. I cannot assess the lower half of the plot or anything below it.
- **Axis labels.** Only "Secular-Rational" is visible as a chart title-like label. No "Self-expression"/"Survival" horizontal axis labels are visible in the captured area (they may be below the fold or at the plot edges). Cannot confirm from these images.
- **Hull rendering.** Web hulls are straight-edged dashed convex polygons; static map hulls are smoothed/rounded solid outlines. That's a stylistic difference, not a data mismatch. However, the web hulls overlap in a busier way (the "West" hull's long lower edge runs through the Latin America/African-Islamic region) and region labels are placed at hull centroids, which puts "African-Islamic" overlapping "Latin America" at ~(800–950, 860–880). Minor legibility issue.
- **No model labels on stars** (see §2). If the intended design is label-on-hover, that's fine, but the intro text implies static "latest-release name" labels.
- **Colour near-collisions.** qwen (purple) vs muse (violet) vs claude (magenta) vs deepseek (pink) are hard to tell apart at star size. Same issue exists on the static map.
- Chip text `inkling: inkling` reads oddly (family == model name) — cosmetic.

## 4. Static map `docs/img/wvs/wvs_map_iw.png` — gross-mismatch check

**No gross mismatch with the web screenshot.** Same overall geometry: LLM star cloud in the upper-left (secular-rational / self-expression quadrant), West hull enveloping it and stretching down-right, East Asia hull to the right of the star cloud, Latin America and African-Islamic hulls lower-right. Same 12-ish family colours. Same labelled latest models (muse-spark-1.3, kimi-k3, inkling, glm-5.3, gpt-6-astra, gemini-3.7-flash, qwen3.8-flash, fable-5.1, deepseek-v4.1-flash) plausibly correspond to the star positions in the web plot.

Static map has things the web capture lacks or that I couldn't see: axis arrows and all four pole labels, country labels (Sweden, Iceland, United States, Japan, South Korea, China, Turkey, Mexico, Pakistan, Egypt), model labels, "64 models, rated sampling" caption. Minor static-map nits (not in scope to fix): the kimi-k3 label has a leader line but sits away from its star; muse-spark-1.3 and qwen3.8-flash labels use near-identical purples.

## 5. Publishability assessment

**Not confirmed publishable on the supplied evidence.**

- ✅ Control on/off state is visible and clear.
- ❌ The core interactive claim ("hides that family's stars") is **not demonstrated** by `wvs_page_qwen_hidden.png` — the plot appears identical to the local screenshot. This is either a real bug or a screenshot-timing artefact; the parent needs the DOM/pixel-diff checks in §2 to tell which.
- ❌ The "latest-release name" labels the intro text promises are not visible in either screenshot.
- ⚠️ Screenshots are truncated at the fold; the lower chart, axis labels and any footer are unreviewed.

Recommended before publishing: (1) re-capture a full-page screenshot in both states after a deterministic post-click wait, (2) pixel-diff the plot region and confirm non-empty diff, (3) either render the latest-release labels or amend the intro sentence so it doesn't promise them.

Uncertainty: medium-high on the "stars don't disappear" finding — I'm comparing two rasters by eye at 1280px; a single missing star among ~60 could be missed, but the specific qwen3.8-flash star (identified via the static map) is clearly present in both.