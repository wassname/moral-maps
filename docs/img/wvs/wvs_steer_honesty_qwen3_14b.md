# Qwen3-14B saved WVS steering replot

Filled path points satisfy pooled `pmass(dose) / pmass(vanilla) >= 0.96`. The first failure is hollow and reached by a faint dashed segment. Later observations can recover answer mass, but remain disconnected from that signed path.

`entropy` is normalized entropy over allowed answer tokens. `max p` is the mean maximum allowed-answer probability. Coordinate intervals pair vanilla and dose samples. Random p95 uses only random directions whose own answer mass passes the same relative rule; `-` means no matched random control passed.

## vjp_delta: intended honest-persona direction (+)

| method    | order   | dose   | path state   | pmass/base   | entropy   | max p   | dx (95%)         | dy (95%)         | move   | LOO move   | random p95   | random n   | beats matched random?   | worst item                        |
|:----------|:--------|:-------|:-------------|:-------------|:----------|:--------|:-----------------|:-----------------|:-------|:-----------|:-------------|:-----------|:------------------------|:----------------------------------|
| vjp_delta | 1       | +0.5C  | connected    | 1.009        | 0.203     | 0.926   | -0.129 +/- 0.090 | -0.058 +/- 0.081 | 0.142  | 0.117      | 0.128        | 16         | yes                     | Attending peaceful demonstrations |
| vjp_delta | 2       | +1C    | connected    | 1.009        | 0.278     | 0.880   | -0.253 +/- 0.191 | -0.037 +/- 0.086 | 0.256  | 0.161      | 0.215        | 9          | yes                     | dealing with people?              |
| vjp_delta | 3       | +2C    | connected    | 1.004        | 0.124     | 0.942   | +0.180 +/- 0.239 | -0.197 +/- 0.243 | 0.267  | 0.193      | -            | -          | -                       | God                               |

## vjp_delta: intended dishonest-persona direction (-)

| method    | order   | dose   | path state             | pmass/base   | entropy   | max p   | dx (95%)         | dy (95%)         | move   | LOO move   | random p95   | random n   | beats matched random?   | worst item                        |
|:----------|:--------|:-------|:-----------------------|:-------------|:----------|:--------|:-----------------|:-----------------|:-------|:-----------|:-------------|:-----------|:------------------------|:----------------------------------|
| vjp_delta | 2       | -0.5C  | first failure          | 0.636        | 0.337     | 0.853   | +0.188 +/- 0.185 | -0.118 +/- 0.130 | 0.222  | 0.174      | 0.134        | 15         | -                       | Attending peaceful demonstrations |
| vjp_delta | 1       | -1C    | recovered disconnected | 0.963        | 0.112     | 0.976   | -0.337 +/- 0.431 | -0.475 +/- 0.491 | 0.582  | 0.506      | 0.237        | 8          | -                       | dealing with people?              |
| vjp_delta | 0       | -2C    | recovered disconnected | 1.002        | 0.008     | 0.998   | -0.332 +/- 0.446 | -0.472 +/- 0.505 | 0.577  | 0.500      | -            | -          | -                       | dealing with people?              |

## mean_diff: intended honest-persona direction (+)

| method    | order   | dose   | path state   | pmass/base   | entropy   | max p   | dx (95%)         | dy (95%)         | move   | LOO move   | random p95   | random n   | beats matched random?   | worst item         |
|:----------|:--------|:-------|:-------------|:-------------|:----------|:--------|:-----------------|:-----------------|:-------|:-----------|:-------------|:-----------|:------------------------|:-------------------|
| mean_diff | 1       | +0.5C  | connected    | 0.997        | 0.193     | 0.908   | +0.070 +/- 0.069 | -0.028 +/- 0.060 | 0.075  | 0.048      | 0.128        | 16         | no                      | Signing a petition |
| mean_diff | 2       | +1C    | connected    | 0.996        | 0.319     | 0.846   | +0.084 +/- 0.196 | -0.106 +/- 0.143 | 0.135  | 0.091      | 0.215        | 9          | no                      | God                |
| mean_diff | 3       | +2C    | connected    | 0.977        | 0.360     | 0.848   | +0.104 +/- 0.325 | -0.217 +/- 0.233 | 0.241  | 0.149      | -            | -          | -                       | Religion           |

## mean_diff: intended dishonest-persona direction (-)

| method    | order   | dose   | path state    | pmass/base   | entropy   | max p   | dx (95%)         | dy (95%)         | move   | LOO move   | random p95   | random n   | beats matched random?   | worst item                        |
|:----------|:--------|:-------|:--------------|:-------------|:----------|:--------|:-----------------|:-----------------|:-------|:-----------|:-------------|:-----------|:------------------------|:----------------------------------|
| mean_diff | 2       | -0.5C  | connected     | 1.003        | 0.180     | 0.929   | -0.187 +/- 0.145 | -0.015 +/- 0.040 | 0.188  | 0.134      | 0.134        | 15         | yes                     | Attending peaceful demonstrations |
| mean_diff | 1       | -1C    | connected     | 0.987        | 0.293     | 0.883   | -0.131 +/- 0.123 | -0.026 +/- 0.090 | 0.134  | 0.084      | 0.237        | 8          | no                      | Attending peaceful demonstrations |
| mean_diff | 0       | -2C    | first failure | 0.844        | 0.484     | 0.780   | +0.083 +/- 0.234 | -0.217 +/- 0.188 | 0.233  | 0.171      | -            | -          | -                       | Abortion                          |

## pca: intended honest-persona direction (+)

| method   | order   | dose   | path state    | pmass/base   | entropy   | max p   | dx (95%)         | dy (95%)         | move   | LOO move   | random p95   | random n   | beats matched random?   | worst item                        |
|:---------|:--------|:-------|:--------------|:-------------|:----------|:--------|:-----------------|:-----------------|:-------|:-----------|:-------------|:-----------|:------------------------|:----------------------------------|
| pca      | 1       | +0.5C  | connected     | 1.009        | 0.230     | 0.915   | -0.129 +/- 0.103 | +0.006 +/- 0.041 | 0.129  | 0.094      | 0.128        | 16         | yes                     | Attending peaceful demonstrations |
| pca      | 2       | +1C    | connected     | 1.007        | 0.283     | 0.890   | -0.222 +/- 0.140 | -0.016 +/- 0.097 | 0.223  | 0.177      | 0.215        | 9          | yes                     | Attending peaceful demonstrations |
| pca      | 3       | +2C    | first failure | 0.941        | 0.507     | 0.781   | +0.004 +/- 0.330 | -0.239 +/- 0.202 | 0.239  | 0.156      | -            | -          | -                       | God                               |

## pca: intended dishonest-persona direction (-)

| method   | order   | dose   | path state    | pmass/base   | entropy   | max p   | dx (95%)         | dy (95%)         | move   | LOO move   | random p95   | random n   | beats matched random?   | worst item   |
|:---------|:--------|:-------|:--------------|:-------------|:----------|:--------|:-----------------|:-----------------|:-------|:-----------|:-------------|:-----------|:------------------------|:-------------|
| pca      | 2       | -0.5C  | connected     | 0.975        | 0.234     | 0.889   | +0.074 +/- 0.061 | -0.060 +/- 0.080 | 0.095  | 0.077      | 0.134        | 15         | no                      | God          |
| pca      | 1       | -1C    | connected     | 0.978        | 0.205     | 0.896   | +0.081 +/- 0.067 | -0.200 +/- 0.219 | 0.216  | 0.123      | 0.237        | 8          | no                      | God          |
| pca      | 0       | -2C    | first failure | 0.809        | 0.424     | 0.744   | -0.106 +/- 0.213 | -0.311 +/- 0.286 | 0.329  | 0.230      | -            | -          | -                       | God          |

## Dose-matched random controls

| dose   |   movement p95 |   coherent n |
|:-------|---------------:|-------------:|
| -1C    |          0.237 |            8 |
| -0.5C  |          0.134 |           15 |
| +0.5C  |          0.128 |           16 |
| +1C    |          0.215 |            9 |
