| model | provider | mAP50 | precision | recall | median_ms | p95_ms | fps | size_MB | note |
|---|---|---|---|---|---|---|---|---|---|
| PyTorch FP32 | torch | 0.7343 | 0.6415 | 0.8294 |  |  |  | 6.5 |  |
| ONNX FP32 | CPUExecutionProvider | 0.7137 | 0.6609 | 0.7977 | 97.96 | 103.63 | 10.2 | 12.77 |  |
| ONNX INT8 (static-QDQ, head FP32) | CPUExecutionProvider | 0.6422 | 0.6882 | 0.5945 | 76.31 | 81.11 | 13.1 | 6.22 |  |
