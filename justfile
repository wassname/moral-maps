# uv_sync images need a 2025+ builder; the workspace default is still 2024.10
export MODAL_IMAGE_BUILDER_VERSION := "2025.06"

# smoke test: 5-item forced-choice eval on existing classic data
smoke:
    uv run python scripts/09_forced_choice.py --model Qwen/Qwen3-0.6B --limit 5 2>&1 | tee logs_smoke.log

# forced-choice eval on a config: just eval Qwen/Qwen3-0.6B classic
eval model name="classic":
    uv run python scripts/09_forced_choice.py --model {{model}} --name {{name}}

# Canonical WVS refresh: queue only score-all-options panels, not scripts/09_forced_choice.py.
wvs-refresh:
    uv run --offline --with 'datasets>=4.0,<5' python scripts/wvs_score_all_options_refresh.py --write-manifest --smoke --queue

# WVS honesty steering sweep: the correctness gate, a real steer on a tiny model in ~2 min
wvs-steer-smoke:
    uv run --extra steer python scripts/wvs_steer_sweep.py --model Qwen/Qwen3-0.6B \
        --methods mean_diff,random --smoke --out outputs/smoke 2>&1 | tee logs_wvs_steer_smoke.log

# the same sweep inside the Modal image, before spending on a big GPU
wvs-steer-modal-smoke:
    uv run --extra steer --group dev modal run scripts/run_modal_wvs.py::smoke

# the real fan-out, one container per (method, seed). H200 for 27B dense, B200:2 for 122B-A10B
wvs-steer-modal model="Qwen/Qwen3.5-27B" gpu="H200" seeds="0":
    WVS_GPU={{gpu}} uv run --extra steer --group dev modal run --detach scripts/run_modal_wvs.py::main \
        --model {{model}} --seeds {{seeds}}

wvs-steer-pull:
    uv run --group dev modal volume get --force moralmaps-wvs-steer outputs .

# which candidate large model reads the answer slot cleanly enough to be worth a sweep
wvs-steer-readable models="Qwen/Qwen3.5-27B,Qwen/Qwen3-32B":
    uv run --extra steer --group dev modal run scripts/run_modal_wvs.py::readable --models {{models}}
