# AGENTS.md

**This is fail-fast research code.** Novel work, not in your training data. Extrapolate carefully.

## What tinymfv is

One answer-token logprob reader that runs many questionnaires. The model is prefilled to an
answer slot after a short think budget; we read the next-token distribution over the vocab and
gather the instrument's answer tokens. Two instrument kinds share that reader:

- nominal (MFV vignettes): the answer IS the foundation; profile = choice frequency; steer effect
  is a multicategory logit change `delta score[f]` (full-vocab logprob, nats).
- ordinal (MFQ-2, Big5, 16PF, humor): the answer is a scale point 1..M; reported as a renormalized
  categorical. The human-comparable summary is the expected score E; the steering-legible summary
  is the agree-vs-disagree log-odds (E is a bounded mean and saturates, see docs/reviews/).

The load-bearing primitive is `lp_gather`: the full-vocab logprobs at the answer tokens, per
(item, frame, sample). Keep it. Every readout (E, log-odds, entropy, profile) is a pure function
of it. Do not throw it away by renormalizing early.

## Conventions

- Fail fast. No defensive programming, no silent fallbacks, no backward-compat shims. A
  `config['key']` KeyError beats a `config.get('key', 0)` that fabricates a valid-looking number.
- NaN-at-collapse is intentional. When `pmass` (mass on allowed tokens) collapses, the renormalized
  distribution reads NaN by design: "do not compare." Do not guard it with an eps/softmax fallback.
- No accretion. If you add something, remove something of equal weight. Delete unused code rather
  than marking it legacy.
- ASCII only in code and prose, with a carve-out for math symbols (greek vars, `>=`, arrows in
  tables, `delta`). No em-dashes for parentheticals; use commas.
- Edit files with edit tools (reviewable diffs), not cat/sed/echo.
- The correctness gate is a fast smoke run on a tiny random model (real LLM, real eval, tiny scale),
  not a `tests/` dir. If a bug slips past, strengthen the smoke path.

## Code style

- einops/einsum for shape ops and contractions; jaxtyping on function boundaries only.
- loguru for logging; polars v1 API for dataframes (eval.py still uses pandas, fine).
- Single-letter dims (b, s, h, d); capital suffix for projected spaces (hsS after `@ U`).
- Comments explain why, not what. Long method-history belongs in docs/, not inline.
