# Fresh-eyes visual review

Read root `AGENTS.md`; no additional `AGENTS.md` found under `slop`. Review limited to the six supplied screenshots. No files edited, code inspected, or browser checks run.

## Verdict

No blocking visual defect observed at the supplied 1440px desktop width. Visibility states visibly change the fitted lines and statistics without disturbing the chart layout.

## Observations

All paths below are relative to `slop/research/wvs/20260916_openrouter/`.

- **Root/redirect appearance:** `wvs_react_root_playwright_default.png` and `wvs_static_redirect.png` show the same complete page appearance: introduction, family chips, culture map, and two release-date panels. Neither shows an error, blank state, or redirect interstitial. Screenshots cannot establish the actual URL or redirect mechanism.
- **Marker hierarchy:** In those default views, plotted logos have thin rings and small footprints relative to the labeled control chips. They do not resemble oversized buttons. The dense purple cluster remains visually prominent through repetition, and individual logos are harder to distinguish than chip logos.
- **Vertical labels:** Both scatter panels have readable, unclipped vertical labels with directional arrows: "Traditional -> Secular-Rational up" and "Self-expression -> Survival up". The second panel heading, "Release date vs Self-expression", names the opposite endpoint from its upward direction. This is not demonstrably incorrect, but readers must notice the axis label to interpret an upward trend.
- **Fit readability and visibility changes:** Dashed gray lines remain distinguishable from pale gridlines. The small, bold upper-left annotations are readable in these captures.

| Screenshot | Secular-Rational annotation | Second-panel annotation |
|---|---|---|
| `wvs_react_root_playwright_default.png` | `OLS, n=48, R2 0.28` | `OLS, n=48, R2 0.26` |
| `wvs_react_playwright_release_fit_all_families.png` | `OLS, n=48, R2 0.28` | `OLS, n=48, R2 0.26` |
| `wvs_react_root_playwright_qwen_hidden.png` | `OLS, n=9, R2 0.08` | `OLS, n=9, R2 0.22` |
| `wvs_react_playwright_release_fit_qwen_only.png` | `OLS, n=39, R2 0.21` | `OLS, n=39, R2 0.24` |

The Qwen-hidden first-panel line slopes downward, unlike the default upward line. Its second-panel line becomes steeper and occupies the recent-date portion. Qwen-only lines also visibly differ from the all-family fits.

- **Insufficient data:** `wvs_react_playwright_release_fit_insufficient.png` shows only Muse enabled, a single mark in each release panel, and "Fit unavailable: fewer than two release dates". No fitted line or stale numerical fit annotation is visible. The message is readable and contained within each panel.
- **Qwen-hide geometry:** Comparing the two root screenshots, the Qwen chip becomes muted and struck through, purple Qwen marks and the `qwen3.8-flash` label disappear, and surviving marks, country outlines, chart frames, and axis extents appear stationary. Large empty historical areas remain in the release panels, consistent with keeping the original date domain rather than rescaling.
- **Copy:** The introductory explanation explicitly limits fitting to "dated models currently shown" and says statistics "describe correlation, not cause." That scope is useful and consistent with the pictured state changes. "Hover or keyboard focus" describes interactions that these screenshots do not verify.

## Nonblocking concern and disproof check

**Directional naming may invite reversed interpretation.** In all six screenshots, "Release date vs Self-expression" accompanies an axis pointing upward toward "Survival". An upward line could be mistaken for increasing self-expression if the reader follows the heading alone.

This is a visual interpretation risk, not an established sign error. Check the coordinate definition and ask a reader to explain what an upward line means without prompting; correct interpretation would weaken this concern.

## Limits

These images demonstrate distinct rendered states, not live interaction or numerical correctness. They do not establish redirect behavior, fit calculations, keyboard access, tooltips, responsive layout, or zero-point/same-date edge cases. No earlier marker design was supplied, so reduced prominence over time cannot be verified; only the current marker-versus-chip hierarchy can be assessed.

-- reviewer-openai
