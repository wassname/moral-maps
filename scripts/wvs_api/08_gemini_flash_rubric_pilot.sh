#!/bin/sh
set -eu
exec uv run --offline --with 'datasets>=4.0,<5' python scripts/wvs_gemini_flash_rubric_pilot.py --run
