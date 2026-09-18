# Plan: steer a large open model on the WVS culture map (honesty + credulity)

worktree `/workspace/2026/lite/moralmaps-wvs-steer-big`, branch `wvs-steer-big`
written by Claude (claude-opus-4.8 in pi), 2026-09-18. NOT yet approved by wassname.

> "moral maps, but for a larger model, run on modal (see vjp-steering for code), and show on a
> moral map how the cultural preference change when steered for honesty + credulity. I want to
> try a few steering methods." -- wassname

## What exists already (observation, read from the code today)

- `scripts/wvs_map.py --local-model X` already reads the 12-item Inglehart-Welzel battery with the
  answer-token logprob reader and places the model on the map. It loads with a bare
  `.to(args.device)`, no steering, no `n_samples`, no CI for the local path (wvs_map.py:378-393).
- `moralmaps.iw_axes` holds the battery: 7 items on Y (Traditional <-> Secular-Rational),
  5 on X (Survival <-> Self-expression).
- steering-lite has the methods we want as variants: `mean_diff`, `pca`, `vjp_delta`, `random`,
  plus iso-KL `Vector.calibrate` so doses are comparable across methods.
- `steering-lite/scripts/run_allinstr_showcase.py` is the existing steer-then-`administer` glue for
  the ordinal instruments. The WVS instruments are built inside `scripts/wvs_map.py`, not in `src/`,
  so that glue cannot reach them yet.
- `vjp-steering/scripts/run_modal.py` is the Modal fan-out template: `uv_sync` image, one container
  per (method, seed), HF cache + outputs on a `modal.Volume`, `::smoke` entrypoint on a tiny random
  model.

## Model and cost (answers the "how much / which model" question)

Modal published rates (modal.com/pricing, per-second, hourly = x3600): A100-80 $2.50, H100 $3.95,
H200 $4.54, B200 $6.25, B300 $7.10. Max 8 GPUs per container.

bf16 weights = 2 bytes/param. Steering vector extraction for `vjp_delta` needs a backward pass, so
the model must fit with an autograd graph, not just a KV cache.

| model | total/active | bf16 GB | fits | $/hr | verdict |
| --- | --- | --- | --- | --- | --- |
| Qwen3.5-27B (dense) | 27B | 54 | 1xH200 | 4.54 | cheap rung, measure timings here |
| **Qwen3.5-122B-A10B** | 122B/10B | 244 | 2xB200 (360) | **12.50** | **primary** |
| GLM-5.3-Flash | 320B/18B | 640 | 4xB200 (720) | 25.00 | stretch, tight for activations |
| GLM-5.3 | 753B/40B | 1506 | nothing at bf16; fp8 ~753 on 8xH200 | 36-50 | backward through fp8 MoE is unproven, skip |
| Kimi K3 | 2.8T | 1561 GB at native 4-bit | > 8xB200 (1440) | n/a | does not fit one node, dead |

Rough budget for the primary: extraction 3 methods x 2 axes x 3 seeds, plus a dose sweep of
~5 doses x 2 directions x 3 methods x 2 axes read on a 12-item battery. Order of magnitude
**$50-150** including debugging. This is a guess with wide error bars, the 27B rung exists to
replace it with measured seconds-per-readout before the big spend.

Cost leaks to avoid: an idle container holding 2xB200 while we poke at a bug ($12.50/hr), and
re-downloading 244 GB per cold start (keep weights on a Volume).

Why not the biggest: Kimi K3 does not fit one Modal container at any precision, and GLM-5.3 only
fits as fp8 where the `vjp_delta` backward is a research project of its own. Qwen3.5-122B-A10B also
gives a clean scaling story next to the published Qwen3-4B showcase, same family.

## Preregistered confound (raise before running)

X-axis item 2 is interpersonal trust, `"Most people can be trusted"`. A **credulity** steer is
close to a paraphrase of that item, so an X shift may be lexical leakage, not a cultural move.
Discriminator: recompute X with that item held out. If the credulity effect on X survives the
holdout, it is a cultural move; if X collapses to base, it is item leakage and must be reported
as such. Honesty has no equivalent overlap in the battery.

## Goals

1. [ ] goal: one source of truth for the WVS battery readout, importable outside `scripts/`
   - subtle failure mode: the steer script gets its own copy of the item resolution, the two
     drift, and the steered points are not comparable to the published base points
   - discriminator: `scripts/wvs_map.py --local-model Qwen/Qwen3.5-4B` before and after the
     refactor produces identical (x, y) to 6 decimals
   - verify: `just smoke` plus the before/after coordinate diff
   - tasks:
     1. [ ] move `load_wvs_all`, `build_instruments`, `read_model`, `model_axis_scores` from
        `scripts/wvs_map.py` into `src/moralmaps/wvs.py`, leave the script importing them

2. [ ] goal: honesty and credulity persona pairs that steer the intended axis, not style
   - subtle failure mode: the pair learns verbosity or refusal instead of the concept, and every
     WVS answer moves because the model got terse, not because it got honest
   - discriminator: base-vs-steered pmass_allowed stays > 0.9 at the doses we plot, and a held-out
     factual-recall probe is unchanged while the on-axis probe moves
   - verify: the `persona-steering` skill checklist, then read 10 generations per pole
   - tasks:
     1. [ ] write pos/neg persona sets for honesty and for credulity
     2. [ ] decide: separate vectors, or the sum `v_honesty + v_credulity` (steering-lite supports
        `v1 + v2`). Proposal: run both separately plus the sum, 3 axes total.

3. [ ] goal: a Modal runner that reproduces the local smoke result exactly
   - subtle failure mode: the Modal path silently uses a different dtype, device map or think
     budget than local, so the big-model numbers are not comparable to the 4B showcase
   - discriminator: `modal run ...::smoke` on the tiny random model returns the same coordinates as
     the local CPU smoke to 6 decimals
   - verify: `just modal-smoke`
   - tasks:
     1. [ ] port `vjp-steering/scripts/run_modal.py`, one container per (axis, method, seed)
     2. [ ] `device_map="auto"` for the multi-GPU path, weights cached on a Volume

4. [ ] goal: the map figure, base plus a steered trajectory per method, with the confound holdout
   - subtle failure mode: the trajectory looks impressive because the model is degrading, and the
     dot drifts toward the map centre as answers go uniform
   - discriminator: every plotted dose passes the pmass gate, and the degradation direction (toward
     the uniform-answer coordinate) is drawn on the figure so a drift toward it is visible
   - verify: fresh-eyes subagent reads the PNG and says which way each method moved and why
   - tasks:
     1. [ ] dose sweep at iso-KL calibrated coefficients, bootstrap CI over items and samples
     2. [ ] arrows on the existing IW map, one colour per method

## Open questions for wassname

1. honesty + credulity as two separate axes, or one combined vector? (plan assumes both plus sum)
2. is the 12-item IW battery enough, or should the steered run also carry MFQ-2 so the movement has
   a second, denser instrument to agree with? MFQ-2 costs ~9x the readout time.
3. budget ceiling for the Modal spend before I stop and ask.
