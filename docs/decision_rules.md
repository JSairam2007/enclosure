# Decision-rule sheet (M3) - one row per value in m3/rules.yaml

| Parameter | Value chosen | Why (evidence from your data) | What happens if too low | What happens if too high |
|---|---|---|---|---|
| mode | | | | |
| defect_classes / expected_class | | | | |
| confidence | | | | |
| debounce_frames | | | | |
| camera_timeout_s | | | | |
| safe_state | | | | |

## Action table

| Condition | Output (relay / LED) | Operator sees | Reset how |
|---|---|---|---|
| Debounced bad | | | |
| Camera lost | | | |
| Back to good | | | |

## Measured (fill from m3_summary.json after a run with 20+ events)

| Metric | Value |
|---|---|
| Events logged | |
| Frame-to-actuator median / p95 (ms) | |
| FPS per stream | |
