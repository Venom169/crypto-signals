# Additions from the liquidity literature - tested

Edge = result minus random entries (same NY hour, direction, stop, target), in ATR units per trade; stop behind the wick + 0.15 ATR, target 2 ATR unless stated; cost $0.5. Samples: 15m Aug-Oct 2026, 30m Jan-Jul 2026, 1h 2025.

| idea                                                   | type   |   15m n |   15m edge |   30m n |   30m edge |   1h n |   1h edge |   pooled edge |   pooled t | all 3 positive   |
|:-------------------------------------------------------|:-------|--------:|-----------:|--------:|-----------:|-------:|----------:|--------------:|-----------:|:-----------------|
| all sweeps (baseline)                                  | filter |     322 |     -0.114 |     471 |      0.032 |    498 |    -0.133 |        -0.068 |     -1.616 |                  |
| premium/discount of yesterday's range                  | filter |     218 |     -0.143 |     350 |      0.035 |    393 |    -0.213 |        -0.107 |     -2.176 |                  |
| against premium/discount                               | filter |     104 |     -0.052 |     121 |      0.024 |    105 |     0.168 |         0.046 |      0.567 |                  |
| beyond the NY midnight open                            | filter |     242 |     -0.207 |     401 |      0.008 |    426 |    -0.110 |        -0.088 |     -1.942 |                  |
| volume spike (>1.5x the 20-bar mean)                   | filter |     119 |     -0.146 |     197 |      0.021 |    151 |     0.015 |        -0.023 |     -0.293 |                  |
| low volume sweep (<1x)                                 | filter |     101 |      0.044 |     140 |      0.154 |    211 |    -0.110 |         0.006 |      0.099 |                  |
| ICT killzones (London 2-5, NY 7-10 NY time)            | filter |     103 |     -0.048 |     157 |     -0.088 |    212 |    -0.176 |        -0.119 |     -1.678 |                  |
| silver bullet hours (3, 10, 14 NY)                     | filter |      37 |     -0.015 |      76 |      0.308 |     85 |    -0.066 |         0.087 |      0.811 |                  |
| LBMA auction windows (10:30, 15:00 London)             | filter |      29 |     -0.099 |      55 |      0.324 |     48 |     0.285 |         0.217 |      1.515 |                  |
| SMT: silver did not confirm                            | filter |     106 |     -0.102 |     144 |     -0.075 |    148 |    -0.279 |        -0.158 |     -2.149 |                  |
| with trend + SMT                                       | filter |      30 |      0.429 |      33 |      0.115 |     16 |    -0.051 |         0.201 |      1.215 |                  |
| grade A                                                | filter |      38 |      0.127 |      57 |      0.288 |    108 |     0.061 |         0.137 |      1.313 | yes              |
| grade A + premium/discount                             | filter |       5 |     -0.118 |      16 |     -0.049 |     47 |    -0.119 |        -0.103 |     -0.620 |                  |
| confirm: FVG (displacement) within 4 bars              | entry  |      90 |     -0.218 |     121 |      0.095 |    106 |    -0.004 |        -0.027 |     -0.208 |                  |
| confirm: structure shift (MSS) within 6 bars           | entry  |      45 |     -0.400 |      76 |      0.183 |     67 |    -0.178 |        -0.086 |     -0.462 |                  |
| target: nearest opposite liquidity (1-5 ATR away)      | target |     238 |     -0.224 |     361 |     -0.081 |    395 |    -0.127 |        -0.134 |     -2.474 |                  |
| same signals, fixed 2 ATR target (control)             | target |     238 |     -0.076 |     361 |     -0.010 |    395 |    -0.113 |        -0.067 |     -1.392 |                  |
| minimum stop 2.7 ATR (~$20) with target 2.7 ATR (~$20) | stop   |     322 |     -0.257 |     471 |     -0.273 |    498 |    -0.098 |        -0.201 |     -2.804 |                  |
