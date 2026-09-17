#!/bin/sh
set -eu
[ "$#" -eq 1 ] || { echo "usage: $0 exact-model-id" >&2; exit 2; }
uv run --with 'datasets>=4.0,<5' python scripts/wvs_direct_choice_priority.py --model "$1" --run
