#!/bin/sh
set -eu
# wvs-respondent-packet-v2 full panel: 4 Qwen Plus releases x N=128 whole respondent packets
# (512 initial calls), committed prompt/schema/seeds, Alibaba pinned, USD 5 stage stop.
# Dispatched 2026-09-19; resumable by protocol_id; one Alibaba request at a time (semaphore 1).
# OPENROUTER_API_KEY loads at runtime via dotenv in the authorized paid path only; never printed.
exec uv run --with 'datasets>=4.0,<5' python scripts/wvs_respondent_packet_v1.py --run --i-authorize-paid-calls
