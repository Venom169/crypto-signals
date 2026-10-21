# Gold liquidity-sweep study - raw results

Cost per trade $0.5, time stop 32 bars, failed-sweep watch 16 bars, random baseline = 40 random entries per signal, same New York hour, same direction, same stop and target. 'coin-flip win %' = stop/(stop+target), what a driftless market gives.

## 15m chart, 2026-08-02 to 2026-10-21 (5270 bars, targets in dollars, median ATR $7.44)

Sweep signals: 322

### When a level is taken

|     n |   wick back inside % |   candle back inside (1-2 bars) % |   held beyond % |
|------:|---------------------:|----------------------------------:|----------------:|
| 475.0 |                 48.4 |                              21.9 |            29.7 |

### Reversal before the sweep extreme breaks

| target   |   reached before sweep extreme broke % |   coin-flip expectation % |
|:---------|---------------------------------------:|--------------------------:|
| $10      |                                   38.2 |                      42.0 |
| $15      |                                   28.9 |                      33.3 |
| $20      |                                   23.9 |                      27.7 |

### Reversal with no stop at all, vs random entries (same hour, same direction)

| target   |   sweep reached it within 16 bars % |   random entry reached it % |
|:---------|------------------------------------:|----------------------------:|
| $10      |                                56.8 |                        62.7 |
| $15      |                                40.4 |                        47.7 |
| $20      |                                32.6 |                        34.9 |

### Fading the sweep

| setup                        |   trades |   win % |   coin-flip win % |   random-entry win % |   $/trade |   random $/trade |   edge $/trade |   t-stat |   PF |   total $ (1 position) |   max DD $ (1 position) |
|:-----------------------------|---------:|--------:|------------------:|---------------------:|----------:|-----------------:|---------------:|---------:|-----:|-----------------------:|------------------------:|
| stop behind wick, target $15 |      322 |   28.88 |             33.31 |                33.04 |     -1.55 |            -0.44 |          -1.11 |    -1.79 | 0.73 |                -342.28 |                  363.05 |
| stop behind wick, target $20 |      322 |   23.91 |             27.70 |                27.20 |     -1.43 |            -0.31 |          -1.12 |    -1.58 | 0.77 |                -234.44 |                  273.44 |
| stop fixed $10, target $15   |      322 |   35.71 |             40.00 |                39.50 |     -1.48 |            -0.55 |          -0.92 |    -1.38 | 0.78 |                -462.11 |                  484.61 |
| stop fixed $10, target $20   |      322 |   30.12 |             33.33 |                32.78 |     -1.29 |            -0.41 |          -0.88 |    -1.14 | 0.82 |                -378.49 |                  417.49 |

### Fading the sweep, by trend

| setup                    |   trades |   win % |   coin-flip win % |   random-entry win % |   $/trade |   random $/trade |   edge $/trade |   t-stat |   PF |   total $ (1 position) |   max DD $ (1 position) |
|:-------------------------|---------:|--------:|------------------:|---------------------:|----------:|-----------------:|---------------:|---------:|-----:|-----------------------:|------------------------:|
| with trend (ema50_1h)    |       93 |   30.11 |             32.91 |                32.82 |     -0.62 |            -0.47 |          -0.15 |    -0.13 | 0.88 |                 -31.99 |                   82.36 |
| against trend (ema50_1h) |      229 |   28.38 |             33.47 |                33.22 |     -1.93 |            -0.37 |          -1.55 |    -2.05 | 0.68 |                -349.71 |                  370.48 |

### The sweep fails (closes beyond its extreme within 16 bars: 65.5% of sweeps; a random bar's high/low: 72.6%) - trade the break

| setup                |   trades |   win % |   coin-flip win % |   random-entry win % |   $/trade |   random $/trade |   edge $/trade |   t-stat |   PF |   total $ (1 position) |   max DD $ (1 position) |
|:---------------------|---------:|--------:|------------------:|---------------------:|----------:|-----------------:|---------------:|---------:|-----:|-----------------------:|------------------------:|
| stop $8, target $15  |      211 |   35.55 |             34.78 |                36.10 |     -0.24 |            -0.16 |          -0.08 |    -0.11 | 0.96 |                 -39.40 |                  108.00 |
| stop $8, target $20  |      211 |   31.28 |             28.57 |                30.12 |      0.48 |             0.10 |           0.39 |     0.43 | 1.08 |                  96.34 |                  121.00 |
| stop $10, target $15 |      211 |   43.60 |             40.00 |                40.66 |      0.55 |            -0.24 |           0.79 |     0.92 | 1.09 |                  38.38 |                   94.41 |
| stop $10, target $20 |      211 |   37.91 |             33.33 |                34.09 |      1.21 |             0.03 |           1.18 |     1.19 | 1.19 |                 141.08 |                  133.04 |
| stop $15, target $15 |      211 |   51.18 |             50.00 |                49.03 |      0.33 |            -0.42 |           0.75 |     0.73 | 1.05 |                -119.84 |                  183.60 |
| stop $15, target $20 |      211 |   44.55 |             42.86 |                41.14 |      0.96 |            -0.20 |           1.16 |     0.99 | 1.12 |                 -40.65 |                  230.47 |

| setup                               |   trades |   win % |   coin-flip win % |   random-entry win % |   $/trade |   random $/trade |   edge $/trade |   t-stat |   PF |   total $ (1 position) |   max DD $ (1 position) |
|:------------------------------------|---------:|--------:|------------------:|---------------------:|----------:|-----------------:|---------------:|---------:|-----:|-----------------------:|------------------------:|
| with trend, stop $10, target $20    |       64 |   40.62 |             33.33 |                31.64 |      1.87 |            -0.73 |           2.60 |     1.41 | 1.31 |                  65.80 |                   88.50 |
| against trend, stop $10, target $20 |      147 |   36.73 |             33.33 |                32.38 |      0.92 |            -0.47 |           1.39 |     1.17 | 1.14 |                   1.90 |                  136.30 |

## 15m chart, 2026-08-02 to 2026-10-21 (5270 bars, targets in ATR multiples, median ATR $7.44)

Sweep signals: 322

### When a level is taken

|     n |   wick back inside % |   candle back inside (1-2 bars) % |   held beyond % |
|------:|---------------------:|----------------------------------:|----------------:|
| 475.0 |                 48.4 |                              21.9 |            29.7 |

### Reversal before the sweep extreme breaks

| target   |   reached before sweep extreme broke % |   coin-flip expectation % |
|:---------|---------------------------------------:|--------------------------:|
| 1.35xATR |                                   37.6 |                      41.5 |
| 2xATR    |                                   28.0 |                      33.0 |
| 2.7xATR  |                                   20.8 |                      27.1 |

### Reversal with no stop at all, vs random entries (same hour, same direction)

| target   |   sweep reached it within 16 bars % |   random entry reached it % |
|:---------|------------------------------------:|----------------------------:|
| 1.35xATR |                                56.5 |                        60.7 |
| 2xATR    |                                40.4 |                        46.7 |
| 2.7xATR  |                                29.2 |                        33.4 |

### Fading the sweep

| setup                               |   trades |   win % |   coin-flip win % |   random-entry win % |   $/trade |   random $/trade |   edge $/trade |   t-stat |   PF |   total $ (1 position) |   max DD $ (1 position) |
|:------------------------------------|---------:|--------:|------------------:|---------------------:|----------:|-----------------:|---------------:|---------:|-----:|-----------------------:|------------------------:|
| stop behind wick, target 2xATR      |      322 |   28.57 |             33.03 |                32.05 |     -1.14 |            -0.49 |          -0.66 |    -0.98 | 0.80 |                -202.65 |                  249.50 |
| stop behind wick, target 2.7xATR    |      322 |   21.43 |             27.15 |                25.54 |     -1.62 |            -0.39 |          -1.23 |    -1.66 | 0.75 |                -363.66 |                  403.44 |
| stop fixed 1.35xATR, target 2xATR   |      322 |   36.02 |             40.30 |                39.15 |     -1.05 |            -0.44 |          -0.61 |    -0.83 | 0.85 |                -392.87 |                  462.90 |
| stop fixed 1.35xATR, target 2.7xATR |      322 |   28.88 |             33.33 |                31.02 |     -1.27 |            -0.43 |          -0.84 |    -1.01 | 0.83 |                -399.78 |                  459.84 |

### Fading the sweep, by trend

| setup                    |   trades |   win % |   coin-flip win % |   random-entry win % |   $/trade |   random $/trade |   edge $/trade |   t-stat |   PF |   total $ (1 position) |   max DD $ (1 position) |
|:-------------------------|---------:|--------:|------------------:|---------------------:|----------:|-----------------:|---------------:|---------:|-----:|-----------------------:|------------------------:|
| with trend (ema50_1h)    |       93 |   30.11 |             32.79 |                32.45 |      0.10 |            -0.36 |           0.46 |     0.39 | 1.02 |                  18.01 |                   76.80 |
| against trend (ema50_1h) |      229 |   27.95 |             33.13 |                32.00 |     -1.65 |            -0.36 |          -1.29 |    -1.60 | 0.73 |                -286.55 |                  328.57 |

### The sweep fails (closes beyond its extreme within 16 bars: 65.5% of sweeps; a random bar's high/low: 72.6%) - trade the break

| setup                         |   trades |   win % |   coin-flip win % |   random-entry win % |   $/trade |   random $/trade |   edge $/trade |   t-stat |   PF |   total $ (1 position) |   max DD $ (1 position) |
|:------------------------------|---------:|--------:|------------------:|---------------------:|----------:|-----------------:|---------------:|---------:|-----:|-----------------------:|------------------------:|
| stop 1.1xATR, target 2xATR    |      211 |   36.97 |             35.48 |                36.11 |     -0.15 |            -0.25 |           0.10 |     0.13 | 0.97 |                 -52.15 |                  149.49 |
| stop 1.1xATR, target 2.7xATR  |      211 |   29.86 |             28.95 |                29.05 |     -0.04 |            -0.16 |           0.11 |     0.13 | 0.99 |                 -59.71 |                  180.14 |
| stop 1.35xATR, target 2xATR   |      211 |   40.28 |             40.30 |                40.37 |     -0.50 |            -0.32 |          -0.18 |    -0.21 | 0.92 |                -143.20 |                  197.28 |
| stop 1.35xATR, target 2.7xATR |      211 |   32.23 |             33.33 |                32.54 |     -0.60 |            -0.26 |          -0.33 |    -0.34 | 0.91 |                -170.27 |                  241.29 |
| stop 2xATR, target 2xATR      |      211 |   51.66 |             50.00 |                47.97 |     -0.06 |            -0.56 |           0.49 |     0.47 | 0.99 |                -104.49 |                  147.17 |
| stop 2xATR, target 2.7xATR    |      211 |   43.13 |             42.55 |                39.11 |      0.04 |            -0.50 |           0.53 |     0.44 | 1.00 |                -160.87 |                  204.15 |

| setup                                        |   trades |   win % |   coin-flip win % |   random-entry win % |   $/trade |   random $/trade |   edge $/trade |   t-stat |   PF |   total $ (1 position) |   max DD $ (1 position) |
|:---------------------------------------------|---------:|--------:|------------------:|---------------------:|----------:|-----------------:|---------------:|---------:|-----:|-----------------------:|------------------------:|
| with trend, stop 1.35xATR, target 2.7xATR    |       64 |   32.81 |             33.33 |                30.16 |     -0.59 |            -0.78 |           0.19 |     0.11 | 0.91 |                 -68.11 |                  145.11 |
| against trend, stop 1.35xATR, target 2.7xATR |      147 |   31.97 |             33.33 |                31.51 |     -0.60 |            -0.40 |          -0.20 |    -0.17 | 0.91 |                -136.98 |                  206.83 |

## 30m chart, 2026-01-01 to 2026-07-31 (6869 bars, targets in ATR multiples, median ATR $13.58)

Sweep signals: 471

### When a level is taken

|     n |   wick back inside % |   candle back inside (1-2 bars) % |   held beyond % |
|------:|---------------------:|----------------------------------:|----------------:|
| 666.0 |                 52.3 |                              20.3 |            27.5 |

### Reversal before the sweep extreme breaks

| target   |   reached before sweep extreme broke % |   coin-flip expectation % |
|:---------|---------------------------------------:|--------------------------:|
| 1.35xATR |                                   42.7 |                      42.7 |
| 2xATR    |                                   34.2 |                      34.1 |
| 2.7xATR  |                                   25.1 |                      28.1 |

### Reversal with no stop at all, vs random entries (same hour, same direction)

| target   |   sweep reached it within 16 bars % |   random entry reached it % |
|:---------|------------------------------------:|----------------------------:|
| 1.35xATR |                                59.9 |                        56.9 |
| 2xATR    |                                43.1 |                        43.3 |
| 2.7xATR  |                                27.6 |                        32.6 |

### Fading the sweep

| setup                               |   trades |   win % |   coin-flip win % |   random-entry win % |   $/trade |   random $/trade |   edge $/trade |   t-stat |   PF |   total $ (1 position) |   max DD $ (1 position) |
|:------------------------------------|---------:|--------:|------------------:|---------------------:|----------:|-----------------:|---------------:|---------:|-----:|-----------------------:|------------------------:|
| stop behind wick, target 2xATR      |      471 |   34.39 |             34.12 |                30.71 |     -1.16 |            -0.26 |          -0.90 |    -0.60 | 0.91 |                 284.52 |                  450.33 |
| stop behind wick, target 2.7xATR    |      471 |   25.27 |             28.13 |                24.52 |     -2.15 |             0.20 |          -2.36 |    -1.40 | 0.84 |                 -84.27 |                  648.12 |
| stop fixed 1.35xATR, target 2xATR   |      471 |   37.79 |             40.30 |                36.49 |     -2.78 |            -0.34 |          -2.44 |    -1.65 | 0.81 |                -512.62 |                  800.13 |
| stop fixed 1.35xATR, target 2.7xATR |      471 |   27.60 |             33.33 |                29.12 |     -3.85 |             0.09 |          -3.94 |    -2.40 | 0.76 |                -669.96 |                  979.64 |

### Fading the sweep, by trend

| setup                    |   trades |   win % |   coin-flip win % |   random-entry win % |   $/trade |   random $/trade |   edge $/trade |   t-stat |   PF |   total $ (1 position) |   max DD $ (1 position) |
|:-------------------------|---------:|--------:|------------------:|---------------------:|----------:|-----------------:|---------------:|---------:|-----:|-----------------------:|------------------------:|
| with trend (ema50_1h)    |      125 |   36.00 |             33.35 |                31.34 |     -0.87 |            -0.17 |          -0.70 |    -0.29 | 0.92 |                 -74.55 |                  365.85 |
| against trend (ema50_1h) |      346 |   33.82 |             34.40 |                31.21 |     -1.26 |            -0.44 |          -0.82 |    -0.44 | 0.90 |                 323.34 |                  429.58 |

### The sweep fails (closes beyond its extreme within 16 bars: 54.8% of sweeps; a random bar's high/low: 70.8%) - trade the break

| setup                         |   trades |   win % |   coin-flip win % |   random-entry win % |   $/trade |   random $/trade |   edge $/trade |   t-stat |   PF |   total $ (1 position) |   max DD $ (1 position) |
|:------------------------------|---------:|--------:|------------------:|---------------------:|----------:|-----------------:|---------------:|---------:|-----:|-----------------------:|------------------------:|
| stop 1.1xATR, target 2xATR    |      258 |   37.21 |             35.48 |                31.57 |      1.45 |            -1.18 |           2.63 |     1.28 | 1.12 |                 316.10 |                  489.55 |
| stop 1.1xATR, target 2.7xATR  |      258 |   33.72 |             28.95 |                24.71 |      3.84 |            -1.05 |           4.89 |     2.00 | 1.31 |                 705.79 |                  392.27 |
| stop 1.35xATR, target 2xATR   |      258 |   41.47 |             40.30 |                35.80 |      0.90 |            -1.06 |           1.95 |     0.88 | 1.07 |                 336.32 |                  520.54 |
| stop 1.35xATR, target 2.7xATR |      258 |   37.60 |             33.33 |                28.37 |      3.58 |            -0.85 |           4.44 |     1.69 | 1.25 |                 773.02 |                  417.17 |
| stop 2xATR, target 2xATR      |      258 |   57.36 |             50.00 |                43.81 |      5.11 |            -1.19 |           6.29 |     2.40 | 1.35 |                 844.96 |                  427.28 |
| stop 2xATR, target 2.7xATR    |      258 |   49.61 |             42.55 |                35.14 |      7.50 |            -1.02 |           8.53 |     2.82 | 1.47 |                1301.68 |                  354.73 |

| setup                                        |   trades |   win % |   coin-flip win % |   random-entry win % |   $/trade |   random $/trade |   edge $/trade |   t-stat |   PF |   total $ (1 position) |   max DD $ (1 position) |
|:---------------------------------------------|---------:|--------:|------------------:|---------------------:|----------:|-----------------:|---------------:|---------:|-----:|-----------------------:|------------------------:|
| with trend, stop 1.35xATR, target 2.7xATR    |       65 |   29.23 |             33.33 |                28.88 |     -5.41 |            -0.95 |          -4.46 |    -1.15 | 0.67 |                -348.32 |                  511.46 |
| against trend, stop 1.35xATR, target 2.7xATR |      193 |   40.41 |             33.33 |                30.52 |      6.61 |             0.85 |           5.76 |     1.79 | 1.48 |                1118.87 |                  236.67 |

## 1h chart, 2025-01-01 to 2025-12-31 (5915 bars, targets in ATR multiples, median ATR $9.61)

Sweep signals: 498

### When a level is taken

|     n |   wick back inside % |   candle back inside (1-2 bars) % |   held beyond % |
|------:|---------------------:|----------------------------------:|----------------:|
| 738.0 |                 47.4 |                              22.5 |            30.1 |

### Reversal before the sweep extreme breaks

| target   |   reached before sweep extreme broke % |   coin-flip expectation % |
|:---------|---------------------------------------:|--------------------------:|
| 1.35xATR |                                   35.9 |                      41.3 |
| 2xATR    |                                   28.9 |                      32.8 |
| 2.7xATR  |                                   25.1 |                      26.9 |

### Reversal with no stop at all, vs random entries (same hour, same direction)

| target   |   sweep reached it within 16 bars % |   random entry reached it % |
|:---------|------------------------------------:|----------------------------:|
| 1.35xATR |                                60.0 |                        58.3 |
| 2xATR    |                                44.0 |                        45.2 |
| 2.7xATR  |                                32.5 |                        34.7 |

### Fading the sweep

| setup                               |   trades |   win % |   coin-flip win % |   random-entry win % |   $/trade |   random $/trade |   edge $/trade |   t-stat |   PF |   total $ (1 position) |   max DD $ (1 position) |
|:------------------------------------|---------:|--------:|------------------:|---------------------:|----------:|-----------------:|---------------:|---------:|-----:|-----------------------:|------------------------:|
| stop behind wick, target 2xATR      |      498 |   28.51 |             32.66 |                30.92 |     -1.30 |            -0.09 |          -1.21 |    -1.54 | 0.83 |                -493.39 |                  600.16 |
| stop behind wick, target 2.7xATR    |      498 |   24.70 |             26.80 |                24.17 |     -0.65 |             0.12 |          -0.76 |    -0.85 | 0.92 |                -107.65 |                  322.39 |
| stop fixed 1.35xATR, target 2xATR   |      498 |   37.15 |             40.30 |                37.38 |     -1.05 |            -0.32 |          -0.74 |    -0.82 | 0.89 |                -436.98 |                  766.25 |
| stop fixed 1.35xATR, target 2.7xATR |      498 |   31.12 |             33.33 |                29.35 |     -0.75 |            -0.15 |          -0.60 |    -0.59 | 0.93 |                -541.49 |                  735.16 |

### Fading the sweep, by trend

| setup                    |   trades |   win % |   coin-flip win % |   random-entry win % |   $/trade |   random $/trade |   edge $/trade |   t-stat |   PF |   total $ (1 position) |   max DD $ (1 position) |
|:-------------------------|---------:|--------:|------------------:|---------------------:|----------:|-----------------:|---------------:|---------:|-----:|-----------------------:|------------------------:|
| with trend (ema50_4h)    |      174 |   33.33 |             33.22 |                31.65 |     -0.29 |             0.11 |          -0.40 |    -0.28 | 0.96 |                 -35.64 |                  235.32 |
| against trend (ema50_4h) |      324 |   25.93 |             32.36 |                28.61 |     -1.83 |            -1.00 |          -0.84 |    -0.91 | 0.76 |                -532.20 |                  638.77 |

### The sweep fails (closes beyond its extreme within 16 bars: 63.3% of sweeps; a random bar's high/low: 71.0%) - trade the break

| setup                         |   trades |   win % |   coin-flip win % |   random-entry win % |   $/trade |   random $/trade |   edge $/trade |   t-stat |   PF |   total $ (1 position) |   max DD $ (1 position) |
|:------------------------------|---------:|--------:|------------------:|---------------------:|----------:|-----------------:|---------------:|---------:|-----:|-----------------------:|------------------------:|
| stop 1.1xATR, target 2xATR    |      315 |   33.97 |             35.48 |                34.12 |     -0.61 |            -0.15 |          -0.46 |    -0.47 | 0.92 |                -132.85 |                  360.72 |
| stop 1.1xATR, target 2.7xATR  |      315 |   27.94 |             28.95 |                27.21 |     -0.26 |             0.25 |          -0.52 |    -0.45 | 0.97 |                  30.93 |                  452.78 |
| stop 1.35xATR, target 2xATR   |      315 |   38.41 |             40.30 |                38.34 |     -1.00 |            -0.08 |          -0.92 |    -0.85 | 0.89 |                -183.05 |                  371.57 |
| stop 1.35xATR, target 2.7xATR |      315 |   32.38 |             33.33 |                30.76 |     -0.44 |             0.35 |          -0.79 |    -0.63 | 0.96 |                  31.05 |                  409.50 |
| stop 2xATR, target 2xATR      |      315 |   46.98 |             50.00 |                45.83 |     -1.39 |            -0.18 |          -1.21 |    -0.93 | 0.88 |                 -79.72 |                  351.86 |
| stop 2xATR, target 2.7xATR    |      315 |   40.00 |             42.55 |                36.99 |     -0.54 |             0.21 |          -0.75 |    -0.51 | 0.95 |                  81.62 |                  318.11 |

| setup                                        |   trades |   win % |   coin-flip win % |   random-entry win % |   $/trade |   random $/trade |   edge $/trade |   t-stat |   PF |   total $ (1 position) |   max DD $ (1 position) |
|:---------------------------------------------|---------:|--------:|------------------:|---------------------:|----------:|-----------------:|---------------:|---------:|-----:|-----------------------:|------------------------:|
| with trend, stop 1.35xATR, target 2.7xATR    |      102 |   31.37 |             33.33 |                27.38 |     -0.43 |            -0.84 |           0.41 |     0.16 | 0.96 |                -130.88 |                  240.75 |
| against trend, stop 1.35xATR, target 2.7xATR |      213 |   32.86 |             33.33 |                32.72 |     -0.44 |             0.95 |          -1.39 |    -0.97 | 0.95 |                  90.59 |                  269.51 |

## Filters, all three samples (edge vs random entries in ATR units; stop behind wick, target 2 ATR)

Fixed in advance. With 25 filters, one or two positive-in-all-3 rows are expected by luck alone.

| filter                              |   15m n |   15m edge |   15m t |   30m n |   30m edge |   30m t |   1h n |   1h edge |   1h t |   pooled edge |   pooled t | positive in all 3   | negative in all 3   |
|:------------------------------------|--------:|-----------:|--------:|--------:|-----------:|--------:|-------:|----------:|-------:|--------------:|-----------:|:--------------------|:--------------------|
| all sweeps                          |     322 |     -0.114 |  -1.392 |     471 |      0.032 |   0.433 |    498 |    -0.133 | -2.078 |        -0.068 |     -1.616 |                     |                     |
| wick sweeps only (W)                |     220 |     -0.126 |  -1.364 |     340 |     -0.019 |  -0.226 |    335 |    -0.112 | -1.587 |        -0.080 |     -1.711 |                     | yes                 |
| candle sweeps only (C)              |      99 |     -0.088 |  -0.525 |     125 |      0.149 |   0.903 |    154 |    -0.148 | -1.131 |        -0.034 |     -0.385 |                     |                     |
| with HTF trend                      |      93 |      0.046 |   0.304 |     125 |      0.080 |   0.614 |    174 |    -0.104 | -0.930 |        -0.010 |     -0.133 |                     |                     |
| against HTF trend                   |     229 |     -0.179 |  -1.832 |     346 |      0.015 |   0.165 |    324 |    -0.148 | -1.906 |        -0.093 |     -1.829 |                     |                     |
| pullback sweep (run-in < 0)         |      33 |      0.316 |   1.385 |      65 |      0.182 |   1.094 |     63 |    -0.066 | -0.368 |         0.112 |      1.044 |                     |                     |
| after a run-up (run-in > 1.5 ATR)   |     133 |     -0.180 |  -1.322 |     182 |      0.145 |   1.107 |    233 |    -0.156 | -1.581 |        -0.062 |     -0.897 |                     |                     |
| with trend + pullback               |      14 |      0.539 |   1.427 |      28 |      0.437 |   1.686 |     30 |    -0.101 | -0.386 |         0.233 |      1.399 |                     |                     |
| HTF level (1H/4H/day/week)          |     131 |     -0.180 |  -1.291 |     330 |      0.070 |   0.743 |    200 |    -0.189 | -1.784 |        -0.058 |     -0.914 |                     |                     |
| day/week level (PD/PW)              |      36 |     -0.055 |  -0.177 |      92 |      0.217 |   1.171 |    159 |    -0.184 | -1.510 |        -0.039 |     -0.399 |                     |                     |
| chart-TF swing only                 |     175 |     -0.022 |  -0.212 |      90 |     -0.039 |  -0.268 |     89 |    -0.180 | -1.255 |        -0.066 |     -0.908 |                     | yes                 |
| Asia range level                    |      45 |     -0.390 |  -1.853 |     116 |     -0.007 |  -0.044 |    233 |    -0.090 | -0.970 |        -0.100 |     -1.347 |                     | yes                 |
| Asia session                        |     131 |     -0.181 |  -1.488 |     164 |     -0.047 |  -0.391 |    146 |    -0.197 | -1.822 |        -0.136 |     -2.022 |                     | yes                 |
| London session                      |      86 |     -0.124 |  -0.762 |     122 |      0.017 |   0.129 |    184 |    -0.172 | -1.654 |        -0.103 |     -1.399 |                     |                     |
| NY morning                          |      67 |      0.000 |   0.000 |     132 |      0.198 |   1.258 |    122 |     0.033 |  0.231 |         0.094 |      1.000 | yes                 |                     |
| London + NY morning                 |     153 |     -0.069 |  -0.552 |     254 |      0.111 |   1.069 |    306 |    -0.090 | -1.068 |        -0.014 |     -0.241 |                     |                     |
| close mid-bar (0.33-0.66)           |     100 |      0.166 |   1.171 |     177 |     -0.106 |  -0.961 |    175 |    -0.065 | -0.684 |        -0.030 |     -0.460 |                     |                     |
| strong rejection (close_loc > 0.66) |     164 |     -0.307 |  -2.425 |     224 |      0.133 |   1.096 |    243 |    -0.167 | -1.557 |        -0.097 |     -1.417 |                     |                     |
| big bar (range > 1.5 ATR)           |     112 |     -0.158 |  -0.964 |     192 |     -0.012 |  -0.088 |    155 |    -0.041 | -0.293 |        -0.058 |     -0.686 |                     | yes                 |
| small bar (range < 1 ATR)           |      97 |     -0.081 |  -0.690 |     124 |      0.135 |   1.054 |    167 |    -0.094 | -1.014 |        -0.018 |     -0.275 |                     |                     |
| deep penetration (> 0.5 ATR)        |     116 |     -0.114 |  -0.679 |     167 |      0.127 |   0.842 |    169 |    -0.255 | -1.927 |        -0.077 |     -0.896 |                     |                     |
| shallow penetration (< 0.15 ATR)    |      88 |     -0.140 |  -1.130 |     116 |      0.058 |   0.489 |    125 |    -0.099 | -0.957 |        -0.055 |     -0.824 |                     |                     |
| equal highs/lows                    |      20 |     -0.320 |  -0.801 |      19 |      0.303 |   0.746 |     36 |    -0.309 | -1.282 |        -0.157 |     -0.837 |                     |                     |
| near a $50 round number             |      45 |     -0.246 |  -1.333 |      78 |     -0.113 |  -0.537 |     62 |    -0.460 | -2.502 |        -0.261 |     -2.238 |                     | yes                 |
| with trend + London/NY morning      |      46 |      0.193 |   0.828 |      70 |      0.260 |   1.504 |    122 |     0.020 |  0.145 |         0.124 |      1.264 | yes                 |                     |

## The indicator's grades (AVOID = Asia session, near a $50 round number, or against the trend; A = with trend in London/NY morning; B = the rest)

Derived from the filter table above, so this is in-sample by construction - not proof of an edge.

| setup           |   trades |   win % |   coin-flip win % |   random-entry win % |   $/trade |   edge $/trade |   t-stat |
|:----------------|---------:|--------:|------------------:|---------------------:|----------:|---------------:|---------:|
| 15m grade A     |       38 |   31.58 |             35.25 |                33.68 |     -0.62 |           0.19 |     0.11 |
| 15m grade B     |       10 |   40.00 |             32.14 |                29.75 |      1.21 |           1.86 |     0.48 |
| 15m grade AVOID |      274 |   28.10 |             33.08 |                33.01 |     -1.78 |          -1.42 |    -2.09 |
| 30m grade A     |       57 |   42.11 |             34.72 |                30.70 |      2.05 |           3.42 |     0.96 |
| 30m grade B     |       12 |   41.67 |             35.16 |                30.42 |      8.56 |          10.48 |     1.04 |
| 30m grade AVOID |      402 |   33.08 |             34.00 |                31.06 |     -1.90 |          -1.84 |    -1.11 |
| 1h grade A      |      108 |   37.96 |             33.47 |                31.81 |      0.39 |           0.68 |     0.38 |
| 1h grade B      |       10 |   30.00 |             30.83 |                33.75 |     -1.09 |          -3.46 |    -0.63 |
| 1h grade AVOID  |      380 |   25.79 |             32.48 |                29.76 |     -1.78 |          -1.39 |    -1.57 |

## 15m robustness: other swing sizes and candle-sweep windows (stop behind wick + $1, target $15)

| setup                                   |   trades |   win % |   coin-flip win % |   random-entry win % |   $/trade |   edge $/trade |   t-stat |
|:----------------------------------------|---------:|--------:|------------------:|---------------------:|----------:|---------------:|---------:|
| swing k=3, candle sweep within 1 bar(s) |      434 |   26.50 |             31.13 |                31.30 |     -1.67 |          -1.33 |    -2.61 |
| swing k=3, candle sweep within 2 bar(s) |      479 |   29.23 |             32.42 |                32.28 |     -1.21 |          -0.84 |    -1.68 |
| swing k=3, candle sweep within 3 bar(s) |      507 |   30.97 |             33.37 |                32.73 |     -0.88 |          -0.40 |    -0.80 |
| swing k=5, candle sweep within 1 bar(s) |      288 |   26.39 |             31.71 |                31.60 |     -1.89 |          -1.53 |    -2.40 |
| swing k=5, candle sweep within 2 bar(s) |      322 |   28.88 |             33.31 |                33.04 |     -1.55 |          -1.11 |    -1.79 |
| swing k=5, candle sweep within 3 bar(s) |      341 |   31.38 |             34.42 |                33.99 |     -0.99 |          -0.54 |    -0.87 |
| swing k=8, candle sweep within 1 bar(s) |      203 |   27.09 |             33.15 |                32.93 |     -2.09 |          -1.71 |    -2.17 |
| swing k=8, candle sweep within 2 bar(s) |      224 |   29.91 |             34.49 |                33.83 |     -1.56 |          -1.06 |    -1.37 |
| swing k=8, candle sweep within 3 bar(s) |      239 |   33.47 |             36.06 |                35.40 |     -0.92 |          -0.50 |    -0.64 |
