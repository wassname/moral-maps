# Qwen3-14B WVS honesty-steering artifacts

Run: 2026-09-18, Modal H200 fan-out, source commit `6e9341a`.

- `run.log`: complete interleaved stdout from 29 containers
- `outputs/`: 3 read seeds for mean-diff, PCA, and VJP delta; 20 random directions
- `plot.log`: pooled confidence intervals, matched-dose random thresholds, and manipulation table
- figure: `docs/img/wvs/wvs_steer_honesty_qwen3_14b.{png,svg}`
- audit: `slop/audits/20260918_qwen3_14b_wvs_honesty.md`

Result: computational run complete, causal honesty interpretation inconclusive. No method exceeded
the 20-direction random p95 on the held-out honesty check.

-- PI/OpenAI
