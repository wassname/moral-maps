# Plan: validate honesty steering before drawing the WVS map

> "the personas you used suck and are too long and not even honesty" -- wassname
> "some methods need KL 2 target ... the effect is comparable not C" -- wassname

Decision: use Qwen3-14B with 64 think tokens. The target behavior is honest versus untruthful
conduct, not truth-over-approval. Use the library's `honest_untruthful` pair (`honest` / `untruthful`,
source `repeng`) only if it validates on this model. Use VJP-steering's method-specific dose walk.
Daily Dilemmas measures honesty. WVS and synthetic tinyMFV measure downstream value transfer.

- [ ] goal 1: validate a short honesty axis on Qwen3-14B
  - [ ] test the exact library pair across candidate templates; read examples and judge intended-axis change, refusal, style, length, and persona echo
  - [ ] use non-Daily-Dilemmas scenarios for extraction; split Daily Dilemmas by dilemma ID into dose-selection and untouched final sets
  - failure modes: both poles stay honest due to post-training, or the pair changes bluntness instead of honesty
  - deliverable: a manifest with the exact pair, template, split IDs, raw generations, judge prompt, and scores
  - success: poles separate on honest conduct with small off-axis change; likely failure: no separation; sneaky failure: the judge rewards saying "honest", caught by persona-echo filtering and blind examples

- [ ] goal 2: find each method's coherent effect range without comparing coefficients
  - [ ] extract mean-difference, PCA, and VJP from the same extraction split; walk each method and each random seed on its own signed log coefficient grid until confirmed breakdown, then sample densely near that boundary
  - [ ] judge Daily Dilemmas calibration items for honesty effect and off-axis damage; record achieved KL only as a diagnostic, not a shared target
  - [ ] give 20 random directions their own walks; compare methods only in honesty-effect/damage space and require both signs to leave the random region
  - failure modes: one shared KL hides a useful method; one easy sign hides a dead opposite sign; non-monotonic VJP is mistaken for dose response
  - deliverable: per-method Pareto plots, breakdown examples, and one frozen admissible dose per sign
  - success: both signs beat random before breakdown; likely failure: no admissible separation; sneaky failure: sign/dose overfits calibration, caught by the untouched final split

- [ ] goal 3: make the intervention auditable and run the held-out honesty test
  - [ ] keep the site fixed across methods: Qwen3-14B's 40 blocks, zero-based blocks 8-31, forward output after each block, residual-stream addition; log vector normalization and coefficient convention
  - [ ] keep decoding and the 64-token think budget fixed for bare, both signs, every method, random controls, and evaluation
  - [ ] freeze all choices, then run the untouched Daily Dilemmas split; invoke `ml-debug` and inspect raw outputs before accepting a negative result
  - failure modes: hooks hit another module or only one generation phase; the final result repeats calibration selection
  - deliverable: resolved hook manifest, held-out effect/damage table, raw generations, and audit log
  - success: held-out effect remains outside random; likely failure: it regresses to random; sneaky failure: coherence passes while answers truncate, caught by token counts and unfinished-answer checks

- [ ] goal 4: draw cultural transfer only for honesty-validated interventions
  - [ ] run paired bare/steered WVS and synthetic tinyMFV at each method's independently selected dose; keep pmass, item bootstrap, and leave-one-item-out checks
  - [ ] plot comparable WVS displacement and uncertainty, not raw `C`; label failed honesty methods as failed rather than showing candidate paths
  - failure modes: one WVS item or answer-token collapse makes a large move; the plot implies that map movement proves honesty
  - deliverable: final WVS map plus a table linking each point to its held-out honesty effect and health checks
  - success: validated honesty plus stable WVS movement; likely failure: honest steering has no stable WVS move; sneaky failure: one item drives it, caught by leave-one-item-out direction reversal

## UAT / verification

1. `run_manifest.json` names all 24 hooked outputs as blocks 8-31 of 40 and records 64 think tokens.
2. Split audit shows no dilemma ID in extraction, dose selection, and final evaluation more than once.
3. The results table has effect, damage, random percentile, achieved KL, and health; it has no cross-method coefficient ranking.
4. Read one bare, positive, negative, and breakdown generation per method before opening the final map.
5. Stop Modal spend at $90 and keep $10 for one diagnostic rerun; do not spend on WVS until one method passes held-out honesty.

-- PI/OpenAI
