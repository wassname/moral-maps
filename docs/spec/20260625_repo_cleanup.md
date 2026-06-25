# Repo Cleanup

## Goal
Make tinymfv read like one simple research eval: one answer-token reader, datasets represented as instruments, nominal datasets reduced categorically and ordinal datasets reduced as Likert scales.

## Scope
In: stale tests, duplicate eval data paths, duplicated script JSON helpers, public docs/comments that point at legacy metrics or removed code, and root data artifacts produced by the deleted creation pipeline.
Out: rewriting the model rollout core, changing steering-lite metrics.

## Requirements
- R1: Pure tests import live code only. Done means: `uv run python -m unittest discover -s tests -v` reaches real assertions instead of import failure. UAT: `/tmp/tinymfv_unittest_cleanup.log`.
- R2: MFV vignette JSONL has one canonical repo path. Done means: scripts that write/read eval vignettes use `src/tinymfv/data`, while root `data/` is runtime output only. UAT: `rg -n 'ROOT / "data" / f"vignettes|ROOT / "data" / "vignettes' scripts src` shows no script JSONL consumers for eval vignettes.
- R3: Legacy OpenRouter dataset-construction scripts are preserved off-main and removed from the clean eval surface. Done means: branch `creating-tinymfv` exists and OpenRouter scripts are absent from `scripts/`. UAT: `git branch --list creating-tinymfv && rg -n 'openrouter|OPENROUTER|openrouter_request' scripts src README.md`.
- R4: Public docs describe nominal vs ordinal instruments as current behavior. Done means: README and `tinymfv.__init__` point at `mean_nll_T`/profile/coherence, not legacy JS as a headline. UAT: `rg -n 'legacy|mean_js' README.md src/tinymfv/__init__.py scripts/09_forced_choice.py`.
- R5: Python files compile. Done means: `python -m py_compile src/tinymfv/*.py scripts/*.py`. UAT: `/tmp/tinymfv_pycompile_cleanup.log`.
- R6: The main functional path still runs. Done means: `just smoke` loads a real tiny HF model, evaluates 5 vignettes, and writes a result JSONL. UAT: `/tmp/tinymfv_smoke_cleanup.log` and `data/results/forced_choice_classic.jsonl`.
- R7: Public prose avoids obvious AI-generated phrasing. Done means: humanizer lint has no OVER checks on README/spec. UAT: `/tmp/tinymfv_humanizer_lint_final.log`.
- R8: README explains what tinymfv measures, how to run it, why logprob readouts are the main research handle, and how the map/range figures relate to the easier summaries. Done means: README contains `evaluate`, `administer`, `pmass_allowed`, `nll_prefill`, `score`, `lp`, `profile_E`, `profile_C`, `dlogit_per_foundation`, `si_per_foundation`, and tracked image links. UAT: `/tmp/tinymfv_readme_docs_check.log`.

## Tasks
- [x] T1 (R1): Remove the dead `shuffle_dimensions` test and add nominal categorical reducer coverage.
- [x] T2 (R2): Point remaining scripts at packaged vignette JSONL and delete duplicate root vignette JSONL.
- [x] T3 (R3): Create branch `creating-tinymfv` to preserve dataset-construction history.
- [x] T4 (R3): Delete legacy OpenRouter creation/judge scripts from main.
- [x] T5 (R4): Update public docs and comments away from legacy JS headline and stale "wiring in progress" text.
- [x] T6 (R5/R6): Run UAT commands and record paths.
- [x] T7 (R7): Run humanizer on README/spec prose and fix mechanical tells.
- [x] T8 (R8): Rewrite README around the measured quantities: raw logprobs first, easier value summaries second, then showcase figures.

## Log
- 2026-06-25: `shuffle_dimensions` was removed in commit `abfe0e1`, but tests still import it.
- 2026-06-25: Root and packaged vignette JSONL currently hash-identical, so deleting root duplicates should not change eval data.
- 2026-06-25: Branch `creating-tinymfv` exists before deleting the OpenRouter creation scripts from main.
- 2026-06-25: README had the MFQ-2 culture-map image and MFV steering metrics, but it did not show the range plot or the ordinal `administer` path.

## UAT
- Human-readable evidence file: `docs/spec/20260625_repo_cleanup_uat.md`.
- `uv run python -m unittest discover -s tests -v`: PASS, 3 tests, see `/tmp/tinymfv_unittest_cleanup.log`.
- `uv run python -m py_compile src/tinymfv/*.py scripts/*.py`: PASS, see `/tmp/tinymfv_pycompile_cleanup.log`.
- `just smoke`: PASS, 5 Qwen/Qwen3-0.6B vignette rows, `mean_pmass_allowed=0.985396534204483`, result at `data/results/forced_choice_classic.jsonl`, see `/tmp/tinymfv_smoke_cleanup.log`.
- `python - <<'PY' ... data/results/forced_choice_classic.jsonl`: PASS, first result row includes `p`, `score`, `label`, `pmass_allowed`, `nll_prefill`, `top1`, and `margin`.
- `python3 /home/wassname/.agents/skills/humanizer/lint.py README.md docs/spec/20260625_repo_cleanup.md`: PASS, no OVER checks, see `/tmp/tinymfv_humanizer_lint_final.log`.
- `python - <<'PY' ... README.md`: PASS, required terms and all README image links present, see `/tmp/tinymfv_readme_docs_check.log`.
- `python3 /home/wassname/.agents/skills/humanizer/lint.py README.md docs/spec/20260625_repo_cleanup.md docs/spec/20260625_repo_cleanup_uat.md`: PASS, no OVER checks, see `/tmp/tinymfv_humanizer_lint_readme_followup.log`.
- `rg -n 'mean_js|median_js|max_js|nll_json|mean_nll_json|agree_logodds|logodds\b|keyed_logodds\b|openrouter|OpenRouter|OPENROUTER|openrouter_request|shuffle_dimensions|\bJS\b|Jensen|jensen' src scripts tests README.md pyproject.toml justfile`: PASS, output empty.
- `rg -n 'ROOT / "data" / f"vignettes|ROOT / "data" / "vignettes' scripts src`: PASS, output empty.
- `git branch --list creating-tinymfv`: PASS, branch exists.
