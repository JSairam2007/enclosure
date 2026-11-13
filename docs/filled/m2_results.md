# M2 - measured results (filled)

Blank template with your TARGET: [../m2_target.md](../m2_target.md) - the target column is yours to fill (it should be
set before measuring), so it is not filled here.

Measured on 2026-11-13, laptop on AC power (on battery the same model measured ~40% slower), Ryzen 5 CPU only,
batch 1, 20 warm-up + 100 timed runs, same random input, accuracy on the same 35-image test split (clips c, f).
Source: `m2_results.md`.

| Model | mAP@0.5 | Precision | Recall | Median ms | p95 ms | FPS | Size MB |
|---|---|---|---|---|---|---|---|
| PyTorch FP32 | 0.995 | 0.990 | 1.000 | - | - | - | 6.5 |
| ONNX FP32 | 0.995 | 0.994 | 1.000 | 91.5 | 97.2 | 10.9 | 12.8 |
| ONNX INT8 (static QDQ, Detect head FP32) | 0.990 | 0.991 | 0.964 | 70.7 | 75.1 | 14.2 | 6.2 |

- INT8 vs ONNX FP32: 23% lower median latency, half the size, mAP@0.5 -0.005, recall -0.036.
- First INT8 attempt (whole graph quantised) gave mAP 0.0; keeping the Detect head in FP32 + per-channel weights
  (ONNX opset 13) fixed it.
- Providers available on this PC: CPU only (no GPU / DirectML provider installed).
- Note: the mAP numbers average over all confidence levels; at the dashboard threshold (0.5) the model still misses
  9 of 28 test closed cases (see `m1_error_analysis.md`).

| Item | Your target | Measured | Met? |
|---|---|---|---|
| Min mAP@0.5 | | 0.990 (INT8) | |
| Max accuracy drop FP32->INT8 | | 0.005 | |
| Max median latency (ms) | | 70.7 (INT8) | |
| Min FPS | | 14.2 (INT8, model only) | |
| Max model size (MB) | | 6.2 (INT8) | |
