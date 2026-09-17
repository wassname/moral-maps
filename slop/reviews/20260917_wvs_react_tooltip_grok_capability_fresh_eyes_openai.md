# Fresh-eyes review: React WVS tooltips, Grok dates, capability blocker

Reviewer: reviewer-openai, image-only, 2026-09-17.

Verdict: PASS.

The reviewer inspected the current default, Qwen-hidden, tooltip, focus, OLS-state, static, and side-by-side captures after reading `AGENTS.md`.

Observed:

- Short copy, family controls, the Release date selector, and the capability-permission blocker are readable.
- Both Grok symbols appear in each release panel, including Qwen-hidden.
- The map tooltip gives the model and two coordinates; each release-panel tooltip gives its panel coordinate and release date only.
- `Survival -> Self-expression` visibly increases upward in the second release panel.
- OLS lines are thin/dashed and described as weak descriptive correlations. The all-family, Qwen-only, Qwen-hidden, and insufficient-data visual states are distinct and readable.
- Qwen-hidden preserves country outlines, axes, and other marks.
- Static and React maps agree visually in orientation and relative placement.

Limits from the reviewer: images do not prove catalog-date correctness, regression arithmetic, disabled-selector behavior, keyboard operation, or other viewport layouts. These are covered separately by the local Playwright UAT and saved catalog records.

-- reviewer-openai, copied by PI[gpt-5.6-terra]
