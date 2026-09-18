"""Fan the WVS honesty steering sweep out over Modal GPUs, one container per (method, seed).

Run from the repo root (uv_sync reads ./pyproject.toml + ./uv.lock):
    modal run scripts/run_modal_wvs.py::smoke       # tiny random model, one dose, ~minutes
    modal run --detach scripts/run_modal_wvs.py     # the real sweep
    modal volume get --force moralmaps-wvs-steer outputs .

Weights and the GlobalOpinionQA cache live on the Volume, so a rerun does not re-download 244 GB.
WVS_GPU picks the hardware: "H200" for a 27B dense model, "B200:2" for Qwen3.5-122B-A10B.
Ported from wassname/vjp-steering scripts/run_modal.py. -- Claude
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import modal

REPO = Path(__file__).resolve().parents[1]
MODEL = os.environ.get("WVS_MODEL", "Qwen/Qwen3.5-27B")
METHODS = ("mean_diff", "pca", "vjp_delta", "random")
SEEDS = (0, 1, 2)

image = (
    modal.Image.debian_slim(python_version="3.13")
    .apt_install("git")
    .uv_sync(extras=["steer"])
    .env({"PYTHONUNBUFFERED": "1", "HF_HOME": "/cache/hf", "PYTHONPATH": "/repo/src"})
    .add_local_dir(REPO / "src", "/repo/src")
    .add_local_dir(REPO / "scripts", "/repo/scripts")
)
app = modal.App("moralmaps-wvs-steer", image=image)
cache = modal.Volume.from_name("moralmaps-wvs-steer", create_if_missing=True)


@app.function(
    gpu=os.environ.get("WVS_GPU", "H200"),
    volumes={"/cache": cache},
    timeout=24 * 60 * 60,
)
def run(argv: list[str]) -> str:
    """One (method, seed) sweep of scripts/wvs_steer_sweep.py, outputs on the Volume."""
    from huggingface_hub import snapshot_download

    Path("/cache/outputs").mkdir(parents=True, exist_ok=True)
    if not Path("/repo/outputs").exists():
        os.symlink("/cache/outputs", "/repo/outputs")
    snapshot_download(argv[argv.index("--model") + 1])
    try:
        subprocess.run([sys.executable, "scripts/wvs_steer_sweep.py", *argv], cwd="/repo", check=True)
    finally:
        cache.commit()
    method = argv[argv.index("--methods") + 1]
    seed = argv[argv.index("--seed") + 1] if "--seed" in argv else "0"
    result = Path(f"/cache/outputs/wvs_steer_{method}_s{seed}.json")
    return result.read_text() if result.exists() else ""


@app.local_entrypoint()
def main(model: str = MODEL, methods: str = ",".join(METHODS), seeds: str = ",".join(map(str, SEEDS)),
         device_map: str = "auto", c_grid: str = "-2,-1,-0.5,0.5,1,2", extract_batch_size: int = 8):
    # one container per (method, seed): a dead lane must not hide the others
    jobs = [(m, s) for s in seeds.split(",") for m in methods.split(",")]
    handles = {
        job: run.spawn([
            "--model", model, "--methods", job[0], "--seed", job[1],
            "--device-map", device_map, "--c-grid", c_grid,
            "--extract-batch-size", str(extract_batch_size),
        ])
        for job in jobs
    }
    for (method, seed), handle in handles.items():
        try:
            res = json.loads(handle.get())
            base = res["doses"][0]
            far = max(res["doses"], key=lambda d: abs(d["mult"]))
            print(f"{method}\ts{seed}\tC={res['calibrated_C']:+.3f}\t"
                  f"dx={far['x'] - base['x']:+.4f}\tdy={far['y'] - base['y']:+.4f}\t"
                  f"pmass={far['mean_pmass']:.3f}")
        except Exception as error:
            print(f"{method}\ts{seed}\tFAILED\t{error}")


@app.function(gpu=os.environ.get("WVS_GPU", "H200"), volumes={"/cache": cache}, timeout=60 * 60)
def probe(model: str, device_map: str) -> str:
    """Read the battery unsteered at several think budgets: is this model's answer slot readable?"""
    from huggingface_hub import snapshot_download

    snapshot_download(model)
    argv = ["--model", model] + (["--device-map", device_map] if device_map else [])
    out = subprocess.run([sys.executable, "scripts/probe_wvs_think_budget.py", *argv],
                         cwd="/repo", check=True, capture_output=True, text=True)
    return out.stdout


@app.local_entrypoint()
def readable(models: str = "Qwen/Qwen3.5-27B,Qwen/Qwen3-32B", device_map: str = ""):
    """Which candidate large model reads cleanly enough to be worth a sweep? ~10 min per model."""
    handles = {m: probe.spawn(m, device_map) for m in models.split(",")}
    for m, handle in handles.items():
        print(f"\n===== {m} =====")
        try:
            print(handle.get())
        except Exception as error:
            print(f"FAILED\t{error}")


@app.local_entrypoint()
def smoke():
    """Same image, mounts and Volume as the real fan-out, on the tiny random model."""
    print(run.remote(
        "--model wassname/qwen3-5lyr-tiny-random --methods mean_diff --dtype float32"
        " --layers 1,2 --smoke --read-batch-size 4".split()
    ))
