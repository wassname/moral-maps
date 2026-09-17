#!/bin/sh
set -eu
uv run --with 'datasets>=4.0,<5' python scripts/wvs_direct_choice_anchor_pilot.py --run
