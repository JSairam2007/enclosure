# M2 - Optimise (ONNX + INT8) and benchmark

Export the trained model to ONNX, quantise it to INT8, check accuracy on the same test split and benchmark
fairly on the CPU (batch 1, 20 warm-up + 100 timed runs). Run from the repository root, on mains power.

```bat
python M2\export_benchmark.py --weights runs\detect\train\weights\best.pt --data dataset\data.yaml --calib dataset\images\train
```
Writes `models/best.onnx`, `models/best_int8.onnx` (not in git) and the results below.
INT8 keeps the YOLO Detect head in FP32 (quantising it gave mAP 0.0) and uses per-channel weights (opset 13).

## Results (`results/`)
- `m2_results.md` / `m2_results.csv` - PyTorch FP32 vs ONNX FP32 vs ONNX INT8: mAP, precision, recall,
  median / p95 latency, FPS, size
- `m2_results_v1.md` - the same table for the first model

## Reports (`docs/`)
- `m2_target.md` - **your targets (blank - fill them in)**
- `m2_results_filled.md` - measured values and conditions, with a "met?" column for your targets

Status: **done** (targets still to be written by you).
