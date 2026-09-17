# smoke test: 5-item forced-choice eval on existing classic data
smoke:
    uv run python scripts/09_forced_choice.py --model Qwen/Qwen3-0.6B --limit 5 2>&1 | tee logs_smoke.log

# forced-choice eval on a config: just eval Qwen/Qwen3-0.6B classic
eval model name="classic":
    uv run python scripts/09_forced_choice.py --model {{model}} --name {{name}}

# Canonical WVS refresh: queue only score-all-options panels, not scripts/09_forced_choice.py.
wvs-refresh:
    uv run --offline --with 'datasets>=4.0,<5' python scripts/wvs_score_all_options_refresh.py --write-manifest --smoke --queue
