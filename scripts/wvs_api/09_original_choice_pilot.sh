#!/bin/sh
set -eu
exec uv run --offline --with 'datasets>=4.0,<5' python scripts/wvs_original_choice_pilot.py --run --i-authorize-paid-calls
