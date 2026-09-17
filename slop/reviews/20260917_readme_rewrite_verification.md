# README rewrite verification

PI/gpt-6-astra, 2026-09-17. Documentation only; no evaluation results recomputed or published.

## User request

> shorter, simpler, include the main table and all plots

> moral maps is about the maps.... the measurement is a secondary measurement after the maps!

The moralmaps opening now describes mapping model survey responses against human societies. Measurement follows all eight plots. Steering-lite introduces activation steering before the API and method comparison.

## Committed originals

Before edits, each working README's git blob matched HEAD exactly:

- moralmaps: commit `0be556bcef977a9092af162369167dd996b3f29a`, README blob `2e6f05900a99bf38198fe5e68ed4bee6e1bd7260`.
- steering-lite: commit `ff9b5c6d386026fd65acec95bd5ea6ee3694c7ee`, README blob `5006c46ac079103bb90b209a67f6df5e34e5343e`.

No baseline edits needed committing. Other sessions' code, lockfiles, and untracked files were left alone.

## Checks

A temporary standard-library check compares the working READMEs with those immutable originals:

- Both WVS tables: every data cell unchanged.
- Steering-lite headline table: all 17 rows and numeric/TODO cells unchanged, including the prompting baseline.
- All eight actual embedded plots retained in their original order, with existing files. Steering-lite had only a broken image placeholder; its pending task is now plain text.
- All relative file and image links resolve locally.
- Code fences, display-math blocks, and HTML details blocks are balanced.
- `git diff --check -- README.md` passes in both repositories.

I opened all eight PNGs. The Big Five map has visible vertical movement; the rewritten caption no longer says personality is untouched. Plot assets were not changed.

`annoy-less/lint.py`: moralmaps passes; steering-lite has one `bold_section` warning for four best-cell marks in the results table. This is the table-formatting exception specified by the markdown-tables skill, not four bold labels in prose.

Calibration wording was checked against `Vector.calibrate` (target 1.0) and `calibrate_iso_kl` (default statistic `kl_rms`, 50 tokens). The historical result caption retains its different 0.50/p95 setup. The table's evaluation-based sign selection and prompting comparator were checked against the committed `scripts/results.py`.

F-beta is labelled a proposal. No beta, logprob threshold, soft-count rule, or target/control weighting has been selected or implemented. Existing numbers retain their original metric.

Final whitespace-delimited word counts: moralmaps 4,007 -> 1,432 (64.3% shorter); steering-lite 2,678 -> 1,193 (55.5% shorter).

## Independent review

[PI/Kimi's review](20260917_readme_editorial_review.md) approved with minor suggestions. Applied the explicit 17 + 48 - 1 = 64 explanation and clarified that the selected steering direction decreased Authority most. Kept the corrected Big Five description after both reviewers inspected the PNG. Did not restore the optional installation variant or long methods table: the user asked for shorter, maps-first documentation, and method references remain linked through source files. Replaced the phrase "gated selectivity" in steering-lite prose with the concrete valid-answer probability check; the formula retains its exact code identifier.

The review contains minor summary imprecision: moralmaps has three measurement paragraphs, not two, and only steering-lite states the sign-selection/prompting comparison caveat. The full steering table has 14 measured rows plus 3 TODO rows. The mechanical row-count check above includes all 17.

External URLs, installation commands, and GPU examples were not executed. These checks preserve reported results; they do not independently validate the underlying experiments.

## Follow-up: remove changelog framing

User: "we don't want 'new models', people don't need a changelog" and "if we have a table, have one table with all." Removed both partial README tables and linked the existing complete results table instead; its data file is unchanged. This resolves the author's README TODO and supersedes the earlier inline-table preservation requirement. Kept the author's deletion of the historical/new panel counts, removed model-count promotion from the image description, and moved the human-coordinate source note to Measurement. All eight plot paths remain unchanged; local links and annoy-less lint pass. Steering-lite was not edited in this follow-up. -- PI/gpt-6-astra

## Follow-up: one steering measurement

At the user's request, both READMEs now explain steering selectivity using intended versus unintended logprob movement. Removed the F-beta proposal and the flips column; removed the constant format-check column and moved its definition, sign-selection limitations, and run settings under details. The simplified equation equals the stored score here because every measured row has `coh=1`. A cell-by-cell check confirmed that all retained values in the 17 steering rows are unchanged. Plot paths and relative links pass; no metric code or experiment was changed. Annoy-less lint passes for moralmaps; steering-lite retains only the results-table best-cell bolding exception (three cells). Preserved the author's interactive-map link and corrected its spelling. -- PI/gpt-6-astra
