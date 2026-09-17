#!/bin/sh
set -eu
uv run --with 'datasets>=4.0,<5' python scripts/wvs_map.py \
  --api-models openai/gpt-5-nano \
  --api-disable-reasoning \
  --api-structured-output \
  --api-concurrency 1 \
  --out slop/research/wvs/20260917_gpt-5-nano_diagnostic.png
