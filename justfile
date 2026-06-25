# smoke test: 5-item forced-choice eval on existing classic data
smoke:
    uv run python scripts/09_forced_choice.py --model Qwen/Qwen3-0.6B --limit 5 2>&1 | tee logs_smoke.log

# forced-choice eval on a config: just eval Qwen/Qwen3-0.6B classic
eval model name="classic":
    uv run python scripts/09_forced_choice.py --model {{model}} --name {{name}}
