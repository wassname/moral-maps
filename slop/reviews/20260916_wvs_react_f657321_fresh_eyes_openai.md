# Independent image-only Goal 4 review

**Verdict: PASS for the pictured React stretch UAT.** No blocking visual regression found. Reviewed all four requested images and `AGENTS.md`, without relying on earlier reviews.

## Observed evidence

- **Crosshair orientation and origin match the static reference.** In `slop/research/wvs/20260916_openrouter/wvs_react_local.png`, "Self-expression" is left, "Survival" right, "Secular-Rational" above, and "Traditional" below, matching `docs/img/wvs/wvs_map_iw.png`. The crosshair intersects approximately at screenshot pixel `(780, 737)`, right and below the plot center. Relative to the country/model points, this agrees with the static reference's origin, rather than incorrectly centering the axes. The hidden-Qwen image preserves this crosshair.

- **Model positions and plotted family labels visually agree.** After accounting for plot scaling and page placement, the React image matches `slop/research/wvs/20260916_openrouter/wvs_page_local.png` and the static reference: the high blue star, neighboring "grok-4.3"/"muse-spark-1.3" stars, rightward "gemma-4-31b-it" and "qwen3.8-flash", and the remaining labeled family stars retain their relative positions. The plotted Claude label remains "fable-5.1". Minor chip wording difference: React says "claude: claude-fable-5.1", whereas the non-React page says "claude: fable-5.1"; this does not change the plotted label or placement.

- **Qwen-hidden state is correct visually.** In `slop/research/wvs/20260916_openrouter/wvs_react_qwen_hidden.png`, "qwen: qwen3.8-flash" becomes outlined and struck through. Qwen's purple star population and latest plotted label disappear. Other families, including the purple Muse and lavender Llama markers, remain. Country points, hulls, remaining labels, plot bounds, and crosshair do not visibly move.

## Limits and disproof checks

These screenshots establish visual parity and the supplied hidden state, not live click handling, exact numerical coordinates, artifact provenance, or other viewport behavior. A browser toggle test showing residual Qwen marks, removed non-Qwen marks, or layout movement would disprove the hidden-state conclusion. Coordinate comparison against the shared artifact could disprove the visually inferred origin/position agreement.