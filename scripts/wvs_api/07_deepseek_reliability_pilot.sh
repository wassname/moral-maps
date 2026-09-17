#!/bin/sh
set -eu
exec uv run --offline --with 'datasets>=4.0,<5' python scripts/wvs_deepseek_reliability_pilot.py --run
