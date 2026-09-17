#!/bin/sh
set -eu
exec uv run --offline --with 'datasets>=4.0,<5' python scripts/wvs_score_all_options_refresh.py --lane "$1"
