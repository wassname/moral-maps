Fresh-eyes image-only review — `docs/img/wvs/wvs_map_iw.png` (second pass)

Observed (from the rendered PNG only; no code or prior renders inspected):

1. Upper-left readability — PARTIALLY improved, still not publication-clean.
   - The dense purple-star cluster around x≈200–420, y≈330–580 still has heavy star-on-star overlap (e.g., the stack at ~(350,370–430), ~(240,440), ~(310,540)). Individual models there are not distinguishable; several stars sit on top of the "West" hull edge and on top of country dots (a blue dot is fully hidden under stars near (350,520) and (300,470)).
   - Labeled names in that area (`kimi-k3`, `glm-5.3`, `fable-5.1`, `deepseek-v4.1-flash`) are legible, and their halos work. But "Sweden" and "Iceland" sit adjacent to stars; "Sweden" is fine, "Iceland" is fine.
   - Unlabeled stars vastly outnumber labeled ones; that is a design choice, but the pile-up in the upper-left means the reader cannot count or separate ~30 models. If the goal is "show the cloud", it passes; if the goal is "identify models", it does not.

2. Qwen vs Latin America color collision — IMPROVED, acceptable.
   - `qwen3.8-flash` label is now a saturated violet/purple (~#7B2FBE), Latin America hull/label is orange. No confusion.
   - Residual: the violet Qwen color is nearly identical to the generic purple used for the ~30 unlabeled stars, so Qwen's labeled star at (760,358) does not visually pop as "special" — but that is not a Latin-America collision.
   - Minor: `muse-spark-1.3` label uses a slightly lighter violet than the qwen label; both are close enough to the bulk-star purple that the labels read as the same family. Not a blocker.

3. Leader / label ambiguity — MOSTLY improved.
   - Short leader ticks are visible for `kimi-k3` (to the brown star at ~(305,293)), `glm-5.3` (to the red star at ~(455,343)), `fable-5.1` (to the pink star at ~(485,427)), `deepseek-v4.1-flash` (up to ~(485,430)).
   - Ambiguity remains for: `inkling` (teal label at (513,258) — teal star at (437,260) is 75 px left with no visible leader; a reader could pair the label with the purple star at (405,247) instead); `gemini-3.7-flash` (label at (700,327) — nearest matching cyan star ambiguous between (580,373) and (640,238); no leader visible); `gpt-6-astra` (blue label at (778,283) — two blue stars at (675,287) and (683,275) sit adjacent, unclear which is the labeled one, and the unlabeled blue star at (750,128) at the very top is unlabeled); `muse-spark-1.3` (label immediately right of a purple star at (735,183) — fine, but a black star at (705,183) is equally adjacent).
   - `fable-5.1` and `deepseek-v4.1-flash` labels both point at the pink star region around (485,427–430); the leader ticks converge close enough that a reader may assume they are the same model. Check: are there two distinct pink stars there or one?

4. Great Britain overlap — CANNOT CONFIRM from image.
   - No "Great Britain" / "United Kingdom" label is present in the current render; only Sweden, Iceland, United States, Japan, South Korea, China, Turkey, Mexico, Pakistan, Egypt are labeled. Either the GB label was dropped, or it was never in this version. If it was dropped to fix the overlap, the "fix" is by omission — flag whether that was intended.

Other observations:
   - The "West" and "African-Islamic" region labels are italic, outlined and readable. "East Asia" and "Latin America" labels are placed outside their hulls at the right edge; "Latin America" is clipped-adjacent to the frame but not cut.
   - Axis labels ("Self-expression"/"Survival"/"Secular-Rational"/"Traditional") are clear.
   - The West hull extends far into Survival/Traditional territory (to ~(1280,1020)) and overlaps East Asia and Latin America heavily — visually confusing but that's data, not rendering.
   - A single green star at (245,348) and a single teal-green star at (880,312) are unlabeled; if those are notable models the reader has no way to identify them.
   - One pink star at top (465,182) and a black star at (705,183) are unlabeled — same issue.

Verdict:
   - Qwen/Latin America collision: resolved.
   - Leader ambiguity: improved for the four upper-left labels; still ambiguous for `inkling`, `gemini-3.7-flash`, `gpt-6-astra`.
   - Upper-left star pile-up: not resolved; acceptable only if the figure's intent is to show a cloud, not individual models.
   - Great Britain: no evidence in this image; cannot judge.
   - Not yet publication-ready without either (a) leaders on the three ambiguous labels and (b) an explicit decision on whether the GB label was meant to be present.

Disproving checks the parent can run: overlay the label anchor coordinates from the plotting code onto the image for `inkling`, `gemini-3.7-flash`, `gpt-6-astra`; confirm whether "Great Britain" is in the label list; count pink stars near (485,428).