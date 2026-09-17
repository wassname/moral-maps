# Editorial + factual review: moralmaps & steering-lite README rewrites
Reviewer: PI/Kimi (cold read, diff vs. originals, spot-checked source, opened all 8 PNGs)
Verdict: **Approve with minor nits.** Both rewrites are shorter, gentler, human-voiced, and maps-first. No numeric values changed; no factual errors found in claims that were checked against source.

## One-sentence reads (as a cold reader)
- **moralmaps**: Puts LLMs through real human surveys and moral vignettes and plots the answers as points on the same maps as human societies, so you can see where a model (or a steered model) sits relative to cultures.
- **steering-lite**: A small, hackable library that steers a model by adding activation vectors at inference, with KL-based calibration to equalize dose and a benchmark table comparing ~16 methods on targeted moral change vs. side effects.

Both one-sentence impressions match the repos' actual contents.

## Maps-first intent (user correction: "about the maps... measurement is secondary")
**Met.** moralmaps opens with a question about the maps ("What do an LLM's values look like next to ours?"), WVS map first, then the three value maps and four range plots, and only then a two-paragraph "Measurement" section — the original's ~half-page of LaTeX (coherence/profile/Δ/sel_gated/si_flips) is compressed to plain prose and explicitly framed as secondary ("This is why we need to measure side effects as well as the target"). steering-lite is inherently a steering repo; it links out to the value maps early ("[Value maps](#)" in the top nav) and keeps its own measurement to one formula plus a clearly-marked proposal.

## Verified correct (checked against source, not just diffed)
1. **Main tables unchanged.** `git show 0be556b:README.md` and `ff9b5c6:README.md` table rows match the rewrites value-for-value (only bolding/header renames in steering-lite). WVS 13-row model table, 17-row z/Mahalanobis table, and the 14-row sel_gated table are all identical.
2. **All 8 real plots present and referenced** (`docs/img/wvs/wvs_map_iw.png`, 3× `map_value.png`, 4× `range.png` — all exist on disk). The steering original had only a broken `![moral map](TODO regenerate with full run)`; the rewrite's explicit TODO sentence is intentional and honest.
3. **sel_gated gating is real**: `moralmaps/src/moralmaps/metrics.py` has `OFF_WEIGHT = 0.1`, `coh = min(1, min(pmass_pos, pmass_neg)/pmass_base)`, `coh**2`, 2000-row bootstrap — matches both READMEs' formula. Both READMEs correctly label it gated selectivity, NOT F-beta.
4. **F-beta is proposal-only**: steering rewrite states β, target/control weighting, and logprob→count are all unchosen, and "None of the table above has been rescored." Accurate.
5. **Calibration doc corrected against current code**: `Vector.calibrate` default is `target_kl=1.0` (vector.py:60), `calibrate_iso_kl` defaults `target_stat="kl_rms"`, `T=50` (calibrate.py:336,340) — rewrite's "default `Vector.calibrate` target is 1 nat using the root-mean-square token KL over short, 50-token rollouts" is exact. (Note `calibrate_iso_kl`'s own bare default is 0.8, but `Vector.calibrate` overrides with 1.0, so the documented claim is correct.) Old table's "0.50 nats via kl_p95" matches the original results header.
6. **Sign-selection caveat is real and retained**: `results.py:92-96` — "Persona-aligned direction = the one that moves ΔAuth most downward" (i.e., selected on eval data). **prompt_only caveat retained**: `results.py:131` confirms it's a single-direction contrast vs. bare, unlike bidirectional steering rows. Both READMEs state this limits direct comparability.
7. **Plot captions are plot-faithful** (fresh-eyes read of all 6 showcase PNGs + WVS map + MFV range): MFQ2 c=+1 lands inside the African-Islamic outline near UAE ✓; Big Five base is far right of all regions with large vertical (volatile→neutral) movement ✓; Humor regions genuinely overlap heavily ✓; range-plot captions match observed bar positions (Authority largest MFV shift ~−0.1→+1.0; Care ~2.0→1.4; MFQ2 equality flat ~3.0; Big Five neuroticism flat, agreeableness/conscientiousness rise; Humor affiliative rises most) ✓.
8. **All linked files resolve** (wvs_model_ci.md, wvs_model_outlier_sd.md, execution_matrix.md, request ledger, metrics.py, iw_axes.py, MFV norms NOTE, all 4 survey JSONs, mean_diff/pca/vjp_delta/calibrate/word_readout, docs/RESEARCH_JOURNAL.md). The pinned "earlier README" link points at the exact original commit `ff9b5c6`, which does contain the dropped per-foundation tables and traces. README API snippets match real signatures (`administer`/`evaluate`/`get_instrument`/`load_vignettes`, `report["profile"]`/`["mean_pmass_allowed"]`, `Vector.train(...).calibrate(...)`, `v * 0.5`, `v + v2`); the steering quickstart even fixes the original's CPU/model-device mismatch by adding `.cuda()` + `.to(model.device)`.

## Actionable findings (minor)

1. **moralmaps — unreconciled arithmetic (clarity).** Quote: *"The map combines 17 recovered historical coordinates with 48 newly completed panels; one model name overlaps."* 17+48=65, but the caption says 64 coordinates, and the rewrite never states that the overlap explains the gap. The original had "One name overlaps, so it displays 64 coordinates." Suggest restoring the conclusion clause.

2. **moralmaps — deliberate claim reversal on Big Five, confirm intent.** Quote: *"Personality changes too."* The original's takeaway was the opposite ("The Authority push barely moves the base model here, which is the point: it shifts values, not personality."). The **rewrite is more plot-faithful** — the original was internally inconsistent (its own map alt-text described movement "from strongly volatile down to about neutral" while its prose said "barely moves"; the actual PNG shows large vertical movement and the range plot shows agreeableness/conscientiousness rising ~0.35–0.45). So this is a correction, not an error — but it changes the headline message from "clean steer" to "steer has side effects," which supports the measurement-as-secondary framing. Flagging so the author consciously owns the change.

3. **steering-lite — sign-selection wording slightly loose.** Quote: *"The `[+]` or `[-]` direction was selected using the evaluation's Authority score."* Per `results.py`, it is specifically the arm that moves ΔAuthority most **downward** that gets picked. The current phrasing preserves the selection-on-eval caveat (the important part) but could be misread as selection on a standalone score. Optional: "...selected on the evaluation: the arm that moves Authority down most." One word-level fix; not blocking.

4. **moralmaps — minimal install path dropped.** Only `uv pip install "moral-maps[maps] @ ..."` remains; the plain non-maps install line from the original is gone. The quickstart example (`administer`/`evaluate`) doesn't need the maps extra, so a one-line "without plots: `uv pip install git+...`" would restore the option at near-zero length cost.

5. **steering-lite — methods table with paper links removed.** The original's 17-row method→file→paper table (arXiv links per method) is now one sentence naming variants. The per-file references do live in the variants docstrings, so nothing is lost to the repo, but readers browsing the README lose the citation map. Acceptable under "shorter," worth one line if the author misses it.

## Non-issues checked and cleared
- "Thirteen of sixteen steering methods had results" ✓ (13 steering rows + prompt_only + 3 TODO = 17 rows).
- "coh = 1 throughout, so the format check does not distinguish methods" matches the original's "coh=1 everywhere (pmass saturates...)" ✓.
- Intervals "2,000 row-bootstrap samples" ✓; run ID `82d4c8319de5`, git `514b97e`, 2026-07-16 ✓; layers 7-27, 256 pairs, 132 vignettes, 256-token thinking budget ✓.
- Qwen3.5-4B hybrid-attention/KV-fork caveat preserved ✓; `just sweep`/`just results` recipes match the justfile ✓.
- Survey item counts (MFQ-2 36, Big Five 50, 16PF 162, Humor 32; MFV 132) match the originals ✓.
- moralmaps HTML comment still credits "PI/gpt-6-astra"; steering same. No attribution regressions.

— PI/Kimi
