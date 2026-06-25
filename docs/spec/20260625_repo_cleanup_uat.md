# repo cleanup UAT evidence

## unittest

Command:

```sh
uv run python -m unittest discover -s tests -v
```

Result excerpt from `/tmp/tinymfv_unittest_cleanup.log`:

```text
test_nominal_flow_reduces_answer_categories_to_profile ... ok
test_ordinal_flow_canonicalizes_frames_then_keys_profile ... ok
test_packaged_vignettes_have_aligned_conditions_and_labels ... ok

Ran 3 tests in 0.007s

OK
```

## py_compile

Command:

```sh
uv run python -m py_compile src/tinymfv/*.py scripts/*.py
```

Result excerpt from `/tmp/tinymfv_pycompile_cleanup.log`:

```text
py_compile OK: src/tinymfv/*.py scripts/*.py
```

## smoke

Command:

```sh
just smoke
```

Result excerpt from `/tmp/tinymfv_smoke_cleanup.log`:

```text
loaded 5 classic vignettes
loading Qwen/Qwen3-0.6B on cuda dtype=bfloat16
forced-choice classic: 100%
classic: 5 rows in 7.2s
mean_pmass_allowed = 0.985396534204483
mean_nll_prefill = 2.6999061584472654
wrote 5 rows to data/results/forced_choice_classic.jsonl
```

First result row keys:

```text
['condition', 'foundation_coarse', 'id', 'label', 'margin', 'nll_prefill', 'p', 'pmass_allowed', 'score', 'top1']
```

## humanizer

Command:

```sh
python3 /home/wassname/.agents/skills/humanizer/lint.py README.md docs/spec/20260625_repo_cleanup.md docs/spec/20260625_repo_cleanup_uat.md
```

Result excerpt from `/tmp/tinymfv_humanizer_lint_final.log`:

```text
README.md: 73 prose lines
check                  count  budget  status
em_dash                    1       1  ok

docs/spec/20260625_repo_cleanup.md: 36 prose lines
check                  count  budget  status

docs/spec/20260625_repo_cleanup_uat.md: 19 prose lines
check                  count  budget  status
```

## README follow-up

Command:

```sh
python - <<'PY' 2>&1 | tee /tmp/tinymfv_readme_docs_check.log
...
PY
```

Result excerpt:

```text
required_terms_missing: []
image_links: ['docs/img/showcase/mfq2/map_pca_ipsative.png', 'docs/img/showcase/mfq2/range.png', 'docs/img/showcase/mfv/foundation_dlogit.png']
missing_image_links: []
tracked_image_links: ['docs/img/showcase/mfq2/map_pca_ipsative.png', 'docs/img/showcase/mfq2/range.png', 'docs/img/showcase/mfv/foundation_dlogit.png']
README docs check: PASS
```

Humanizer follow-up command:

```sh
python3 /home/wassname/.agents/skills/humanizer/lint.py README.md docs/spec/20260625_repo_cleanup.md docs/spec/20260625_repo_cleanup_uat.md
```

Result excerpt from `/tmp/tinymfv_humanizer_lint_readme_followup.log`:

```text
README.md: 108 prose lines
check                  count  budget  status
tricolon                   1       -  info

docs/spec/20260625_repo_cleanup.md: 41 prose lines
check                  count  budget  status

docs/spec/20260625_repo_cleanup_uat.md: 25 prose lines
check                  count  budget  status
```

Fresh-eyes review:

```text
no blockers.
README diff answers the latest ask well: raw answer-token logprobs are the primitive;
pmass_allowed/nll_prefill are defined; sensitive relative readouts are score, lp,
dlogit_per_foundation, and delta C; easier value summaries are profile, profile_E,
and logodds_agree. Artifact sweeps found no tracked/staged __pycache__, .pyc,
data/results, logs, root duplicate data, OpenRouter, multilabel, separation, or
calibration junk.
```

## stale-name sweeps

Command:

```sh
rg -n 'mean_js|median_js|max_js|nll_json|mean_nll_json|agree_logodds|logodds\b|keyed_logodds\b|openrouter|OpenRouter|OPENROUTER|openrouter_request|shuffle_dimensions|\bJS\b|Jensen|jensen' src scripts tests README.md pyproject.toml justfile
```

Result: output empty.

Command:

```sh
rg -n 'ROOT / "data" / f"vignettes|ROOT / "data" / "vignettes' scripts src
```

Result: output empty.
