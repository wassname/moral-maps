# Plan: steer a large open model on the WVS culture map (honesty + credulity)

worktree `/workspace/2026/lite/moralmaps-wvs-steer-big`, branch `wvs-steer-big`
written by Claude (claude-opus-4.8 in pi), 2026-09-18. NOT yet approved by wassname.

> "moral maps, but for a larger model, run on modal (see vjp-steering for code), and show on a
> moral map how the cultural preference change when steered for honesty + credulity. I want to
> try a few steering methods." -- wassname

Decisions after the first pass (wassname, 2026-09-18):
- honesty only, one axis, credulity dropped
- WVS only, no MFQ-2. "that's the plot"
- "$100 is fine if it works"

Branch note: this worktree branched from 789829e, which the Gemini-pilot session later amended to
4955468. Rebase or cherry-pick the steering commits onto 4955468 before any merge, do not carry the
stale preregistration commit. (told to me over intercom by moralmap_add_astra)

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
| Qwen3.5-27B (dense) | 27B | 54 | 1xH200 | 4.54 | cheap, run first to measure seconds per readout |
| **Qwen3.5-122B-A10B** | 122B/10B | 244 | 2xB200 (360) | **12.50** | **primary** |
| GLM-5.3-Flash | 320B/18B | 640 | 4xB200 (720) | 25.00 | stretch, tight for activations |
| GLM-5.3 | 753B/40B | 1506 | nothing at bf16; fp8 ~753 on 8xH200 | 36-50 | backward through fp8 MoE is unproven, skip |
| Kimi K3 | 2.8T | 1561 GB at native 4-bit | > 8xB200 (1440) | n/a | does not fit one node, dead |

Rough budget for the primary: extraction 3 methods x 2 axes x 3 seeds, plus a dose sweep of
~5 doses x 2 directions x 3 methods x 2 axes read on a 12-item battery. Order of magnitude
**$50-150** including debugging. This is a guess with wide error bars. Run the 27B first and
replace the guess with measured seconds per readout before the big spend.

Cost leaks to avoid: an idle container holding 2xB200 while we poke at a bug ($12.50/hr), and
re-downloading 244 GB per cold start (keep weights on a Volume).

Why not the biggest: Kimi K3 does not fit one Modal container at any precision, and GLM-5.3 only
fits as fp8 where the `vjp_delta` backward is a research project of its own. Qwen3.5-122B-A10B also
gives a clean scaling story next to the published Qwen3-4B showcase, same family.

## Preregistered confound

The battery is 12 items, so one item can carry a whole apparent move. `scripts/wvs_steer_sweep.py`
saves each item's position at every dose, and `scripts/plot_wvs_steer.py` reports the move length
again with the single most influential item removed. A move that mostly disappears under that
leave-one-out is one item reacting to the persona wording, not a cultural shift.

This mattered most for credulity, which nearly paraphrases the X-axis trust item
(`"Most people can be trusted"`). Credulity is now out of scope, but the check is cheap and stays.

## Corrected-run decision rule (recorded before the next full sweep)

The first 27B sweep found two evaluation bugs: sampled think traces were not seeded before a
"paired" bootstrap, and VJP's behavioral sign was opposite its configured sign. Its baseline
pmass was also 0.75, below the preregistered 0.95 readability gate. Those outputs are diagnostic,
not the final result.

1. Use the largest probed model with base mean pmass >= 0.95. A plotted dose must keep mean pmass
   >= 0.90; do not replace this with a post-hoc relative threshold.
2. Orient every vector, including random, on four held-out true-vs-welcome questions. A method is
   honesty-specific only if its log-odds effect exceeds the 95th percentile over random directions.
3. A culture-map effect must beat the matched-dose random displacement and retain its direction
   after the single most influential WVS item is removed. Opposite doses should point to opposite
   half-planes locally; a non-monotonic or same-direction trajectory is evidence against an axis.
4. If no implementation passes these checks, conclude only that these implementations are
   inconclusive. Do not conclude that honesty has no cultural effect.

## Goals

0. [/] goal: the target model's answer slot is readable, before renting anything big
   - subtle failure mode: the coordinate looks plausible while most of the answer-token mass sits
     off the digits, so every steered move is measured through mush
   - discriminator: mean pmass_allowed >= 0.95 on the unsteered battery. Qwen3-0.6B reads 1.000,
     Qwen3.5-0.8B reads 0.61-0.84 and its coordinate swings 0.15 in X with the think budget
   - verify: `just wvs-steer-readable` (Modal, ~$0.75 per model)
   - evidence:
     - > logs_think_probe.log, Qwen3.5-0.8B top-5 at the answer slot:
       > `'0':0.454 '1':0.214 'No':0.130 'You':0.018 'Answer':0.016`
       > the leak is the option WORD, not gibberish: a format-prior weakness, not a broken prefill
     - > Qwen3.5 chat template closes an empty think block by default, so the reader's own `<think>`
       > made `</think> ... <think>`. Fixed with enable_thinking=True; worth only +0.02 to +0.09 pmass,
       > so the template was not the main cause. Qwen3-0.6B unchanged at 1.000 (no regression).
   - tasks:
     1. [x] probe think budget 1/16/64/256 on the new family
     2. [x] fix the double-think template artifact
     3. [/] probe Qwen3.5-27B and Qwen3-32B on Modal, pick on the measured number

1. [x] goal: one source of truth for the WVS battery readout, importable outside `scripts/`
   - subtle failure mode: the steer script gets its own copy of the item resolution, the two
     drift, and the steered points are not comparable to the published base points
   - discriminator: `scripts/wvs_map.py --local-model Qwen/Qwen3.5-4B` before and after the
     refactor produces identical (x, y) to 6 decimals
   - verify: `just smoke` plus the before/after coordinate diff
   - evidence:
     - > before (git HEAD script) and after (src/moralmaps/wvs.py), Qwen/Qwen3-0.6B:
       > `COORD Qwen/Qwen3-0.6B x=0.495998 y=0.416814` both times
   - tasks:
     1. [x] move `load_wvs_all`, `build_instruments`, `read_model`, `model_axis_scores` from
        `scripts/wvs_map.py` into `src/moralmaps/wvs.py`, leave the script importing them

2. [ ] goal: honesty and credulity persona pairs that steer the intended axis, not style
   - subtle failure mode: the pair learns verbosity or refusal instead of the concept, and every
     WVS answer moves because the model got terse, not because it got honest
   - discriminator: base-vs-steered pmass_allowed stays > 0.9 at the doses we plot, and a held-out
     factual-recall probe is unchanged while the on-axis probe moves
   - verify: the `persona-steering` skill checklist, then read 10 generations per pole
   - tasks:
     1. [x] one mirrored pair, in `scripts/wvs_steer_sweep.py::HONESTY_PAIR`
     2. [ ] read 10 generations per pole and check the axis is honesty, not bluntness
     3. [~] credulity dropped by wassname

3. [ ] goal: a Modal runner that reproduces the local smoke result exactly
   - subtle failure mode: the Modal path silently uses a different dtype, device map or think
     budget than local, so the big-model numbers are not comparable to the 4B showcase
   - discriminator: `modal run ...::smoke` on the tiny random model returns the same coordinates as
     the local CPU smoke to 6 decimals
   - verify: `just wvs-steer-modal-smoke`
   - tasks:
     1. [x] port `vjp-steering/scripts/run_modal.py`, one container per (method, seed)
     2. [x] `device_map="auto"` for the multi-GPU path, weights cached on a Volume
     3. [ ] compare the Modal tiny-model coordinate against the same run locally

4. [ ] goal: the map figure, base plus a steered trajectory per method, with the confound holdout
   - subtle failure mode: the trajectory looks impressive because the model is degrading, and the
     dot drifts toward the map centre as answers go uniform
   - discriminator: every plotted dose passes the pmass gate, and the degradation direction (toward
     the uniform-answer coordinate) is drawn on the figure so a drift toward it is visible
   - verify: fresh-eyes subagent reads the PNG and says which way each method moved and why
   - tasks:
     1. [ ] dose sweep at iso-KL calibrated coefficients, bootstrap CI over items and samples
     2. [x] paths on the existing IW map, one colour per method, off the zone palette
     3. [x] leave-one-out column: move length again without the most influential item

## Open questions for wassname

1. honesty + credulity as two separate axes, or one combined vector? (plan assumes both plus sum)
2. is the 12-item IW battery enough, or should the steered run also carry MFQ-2 so the movement has
   a second, denser instrument to agree with? MFQ-2 costs ~9x the readout time.
3. budget ceiling for the Modal spend before I stop and ask.
