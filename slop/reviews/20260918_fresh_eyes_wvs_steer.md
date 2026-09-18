# Fresh-eyes figure check

Reviewer: pi-quick-oracles, 2026-09-18

## Observations

1. **Plain-language reading.** The figure shows how three steering methods, `mean_diff`, `pca`, and `vjp_delta`, move Qwen3-14B from its base position on the WVS cultural map at different doses. Some trajectories are sizable, but the figure explicitly says: **"Exploratory: no method passed every validity gate."**

2. **Potentially misleading presentation (moderate).** The prominent trajectories and title "Candidate honesty-steering paths" can imply validated honesty steering, while the held-out honesty result is absent from the figure. Dose labels such as "-1C" and "+2C" are also unexplained, overlapping paths are difficult to follow, and the axes lack numeric ticks. The legend's "random reach" does not clearly communicate the decisive honesty-specific null result.

3. **Does the log support a directional honesty effect beyond random? No.** All held-out point estimates are positive, but none exceed the random-control 95th percentile:
   - `mean_diff`: effect **2.813**, random p95 **3.653**, random n **20**, honesty-specific **"no"**
   - `pca`: effect **0.188**, random p95 **3.653**, random n **20**, honesty-specific **"no"**
   - `vjp_delta`: effect **2.031**, random p95 **3.653**, random n **20**, honesty-specific **"no"**

Some map movements beat random reach at individual doses, for example, `vjp_delta -1` has `|move|` **0.5823** versus random p95 **0.2574**, but this demonstrates unusual WVS displacement, not an honesty-specific effect.

## Inference and highest-value correction

Add a conspicuous subtitle or inset stating: **"Held-out honesty effect: no method exceeded random controls (random p95 = 3.653; n = 20)."** This would prevent viewers from interpreting visually large cultural-map movement as evidence of successful honesty steering.

-- pi-quick-oracles
