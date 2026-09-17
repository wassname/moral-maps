#!/bin/sh
set -eu
uv run --with 'datasets>=4.0,<5' python scripts/wvs_map.py \
  --api-models openai/gpt-5-nano \
  --api-reasoning-effort low \
  --api-structured-output \
  --api-require-complete \
  --api-concurrency 1 \
  --out slop/research/wvs/20260917_gpt-5-nano_diagnostic.png
