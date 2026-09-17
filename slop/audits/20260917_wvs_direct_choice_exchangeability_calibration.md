# Fixed-seed direct-choice exchangeability calibration

- target run: `20260917T033051Z_3e9c3d54727e`, protocol `3e9c3d54727e46c92af49321604778d9bae85bd83a22e23e1793cbefd06f29e3`
- source ledger: `slop/research/wvs/20260917_direct_choice/gemini37_direct_choice_production_requests.jsonl` through 2026-09-17T03:45:41.975498+00:00
- fixed NumPy PCG64 seed: 20260917; 100,000 permutations per item
- machine table: `slop/audits/20260917_wvs_direct_choice_exchangeability_calibration.csv`

## Null and scope

For each item, the observed 20 canonical choices are held fixed and randomly reassigned to its actual 20 schedule slots. This conditional exchangeability null tests whether the observed split TV is unusual given that item's own choice multiset. It does not test whether a choice distribution is human-like, whether samples are independent, or whether the prompt measures a WVS coordinate.

The two reports are first-ten versus last-ten schedule halves and canonical versus reversed direction slots. For the two 10-option items the present schedule makes these partitions identical, so they are reported twice for transparency but do not distinguish direction from request time. For n=3/n=4, unequal direction counts are registered design constraints.

## Results

Randomization p is one-sided for TV at least the observed value. Holm and maxT values adjust across all 24 listed reports. They are calibration summaries, not validity thresholds or a claim of statistical significance.

| item | n | comparison | groups | observed TV | null mean | null p95 | randomization p | Holm p (24) | maxT p (24) | note |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| Abortion | 10 | canonical_vs_reversed | 10/10 | 0.400 | 0.327 | 0.600 | 0.3382 | 1.0000 | 0.3598 | same partition as the other report |
| Abortion | 10 | schedule_half | 10/10 | 0.400 | 0.327 | 0.600 | 0.3382 | 1.0000 | 0.3598 | same partition as the other report |
| Attending peaceful demonstrations | 3 | canonical_vs_reversed | 11/9 | 0.091 | 0.100 | 0.111 | 1.0000 | 1.0000 | 1.0000 | distinct partition |
| Attending peaceful demonstrations | 3 | schedule_half | 10/10 | 0.100 | 0.100 | 0.100 | 1.0000 | 1.0000 | 1.0000 | distinct partition |
| Determination, perseverance | 2 | canonical_vs_reversed | 10/10 | 0.000 | 0.000 | 0.000 | 1.0000 | 1.0000 | 1.0000 | distinct partition |
| Determination, perseverance | 2 | schedule_half | 10/10 | 0.000 | 0.000 | 0.000 | 1.0000 | 1.0000 | 1.0000 | distinct partition |
| God | 2 | canonical_vs_reversed | 10/10 | 0.000 | 0.000 | 0.000 | 1.0000 | 1.0000 | 1.0000 | distinct partition |
| God | 2 | schedule_half | 10/10 | 0.000 | 0.000 | 0.000 | 1.0000 | 1.0000 | 1.0000 | distinct partition |
| Homosexuality | 10 | canonical_vs_reversed | 10/10 | 0.300 | 0.168 | 0.300 | 0.3060 | 1.0000 | 0.5415 | same partition as the other report |
| Homosexuality | 10 | schedule_half | 10/10 | 0.300 | 0.168 | 0.300 | 0.3060 | 1.0000 | 0.5415 | same partition as the other report |
| Imagination | 2 | canonical_vs_reversed | 10/10 | 0.000 | 0.000 | 0.000 | 1.0000 | 1.0000 | 1.0000 | distinct partition |
| Imagination | 2 | schedule_half | 10/10 | 0.000 | 0.000 | 0.000 | 1.0000 | 1.0000 | 1.0000 | distinct partition |
| Independence | 2 | canonical_vs_reversed | 10/10 | 0.000 | 0.000 | 0.000 | 1.0000 | 1.0000 | 1.0000 | distinct partition |
| Independence | 2 | schedule_half | 10/10 | 0.000 | 0.000 | 0.000 | 1.0000 | 1.0000 | 1.0000 | distinct partition |
| Joining in boycotts | 3 | canonical_vs_reversed | 11/9 | 0.000 | 0.000 | 0.000 | 1.0000 | 1.0000 | 1.0000 | distinct partition |
| Joining in boycotts | 3 | schedule_half | 10/10 | 0.000 | 0.000 | 0.000 | 1.0000 | 1.0000 | 1.0000 | distinct partition |
| Obedience | 2 | canonical_vs_reversed | 10/10 | 0.100 | 0.100 | 0.100 | 1.0000 | 1.0000 | 1.0000 | distinct partition |
| Obedience | 2 | schedule_half | 10/10 | 0.100 | 0.100 | 0.100 | 1.0000 | 1.0000 | 1.0000 | distinct partition |
| Religion | 4 | canonical_vs_reversed | 12/8 | 0.000 | 0.000 | 0.000 | 1.0000 | 1.0000 | 1.0000 | distinct partition |
| Religion | 4 | schedule_half | 10/10 | 0.000 | 0.000 | 0.000 | 1.0000 | 1.0000 | 1.0000 | distinct partition |
| Signing a petition | 3 | canonical_vs_reversed | 11/9 | 0.000 | 0.000 | 0.000 | 1.0000 | 1.0000 | 1.0000 | distinct partition |
| Signing a petition | 3 | schedule_half | 10/10 | 0.000 | 0.000 | 0.000 | 1.0000 | 1.0000 | 1.0000 | distinct partition |
| dealing with people? | 2 | canonical_vs_reversed | 10/10 | 0.000 | 0.000 | 0.000 | 1.0000 | 1.0000 | 1.0000 | distinct partition |
| dealing with people? | 2 | schedule_half | 10/10 | 0.000 | 0.000 | 0.000 | 1.0000 | 1.0000 | 1.0000 | distinct partition |

## Interpretation limits

With only 20 choices/item, discrete distributions and concentrated responses make this calibration low power for moderate instability. A high adjusted p can arise because the observed split is ordinary under the conditional null, because the item has little response variation, or because 20 samples cannot resolve the effect. A low p would only identify a split unusual under this narrow exchangeability null. Neither outcome is a hard construct-validity cutoff.

The calibrated values therefore refine the prior descriptive half TVs. They do not authorize a direct-choice map, a protocol merge, or additional paid models. The next decision remains parent review of whether a differently interleaved replication is worth its cost.

-- PI[gpt-5.6-terra]
