# README Comprehension Panel Triage

## Inputs
- Initial panel: `docs/reviews/readme_comprehension_20260630_123105/`
- Confirmation panel: `docs/reviews/readme_comprehension_rerun_20260630_123527/`
- README under review: `README.md`

## Expected Reader Answers
- tinymfv is a fast answer-token reader for local LLM value steering work.
- It includes MFV classic, MFV scifi, MFV ai-actor, MFQ-2, Big Five, 16PF, and Humor Styles.
- The map/range measurement is the profile: MFV foundation probability profile, survey expected 1-5 factor profile.
- For MFV showcase maps, profiles are z-scored across foundations before comparing to human country profiles.
- Gray = human societies/respondents, black = base model, red = positive steering, blue = negative steering.
- `c` is the signed multiplier on the calibrated steering vector.
- Answer mass is total probability on valid answer tokens. The path is a per-side prefix from `c=0`; drop the side once answer mass is at or below 99% of base.

## Panel Result
- Initial panel correctly recovered the main tool, dataset list, profile measurement, and researcher use case.
- Initial repeated gaps: `c` was not defined, answer mass was not exact enough, and the per-side prefix rule was easy to infer but not explicit.
- README fixes applied:
  - Defined `c` as the signed multiplier on the calibrated steering vector.
  - Defined answer mass as probability on valid answer tokens.
  - Stated that dropping is per side, at the first incoherent coefficient.
  - Added the compact answer-mass formula:
    `m(c) = E_i sum_{a in A_i} P_c(a | i)`.
- Confirmation panel: all four usable reviewers correctly reconstructed `c`, answer mass, the 99% threshold, and the per-side drop rule.

## Not Changed
- Did not add a steering-lite training recipe. This README links to steering-lite and shows the plot command; the full axis/template/scenario-selection workflow belongs in steering-lite or the persona-template skill.
- Did not define the calibrated steering vector mathematically here. It would make the README longer and is not needed to understand tinymfv's measurement.
- Did not add full human CSV schema docs. The dataset table links directly to the committed data files.
