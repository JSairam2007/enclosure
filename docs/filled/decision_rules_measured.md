# Decision rules (M3) - current values and measurements (filled)

Blank template with the WHY columns: [../decision_rules.md](../decision_rules.md) - the reasons are your design
decisions, so only facts are filled here. Source: `m3/rules.yaml`, `m3_summary.json`, `m3_events.csv`.

| Parameter | Value | Observed effect in tests |
|---|---|---|
| mode | defect_class | |
| defect_classes | case_open, lid | clip f: FAIL while the case is open with the lid beside it (frames 89-205) |
| confidence | 0.5 | top-down closed cases on clip c often below 0.5 -> no detection |
| no_part | true | empty view -> NO PART instead of PASS (clip a room frames 4-48; live camera without the case) |
| debounce_frames | 5 | FAIL needs 5 bad frames in a row, release / NO PART need 5 in a row |
| camera_timeout_s | 2.0 | not yet tested by unplugging a camera |
| safe_state | ON | not yet tested (needs the relay / camera unplug test) |

## Action table (as implemented)

| Condition | Output | Operator sees |
|---|---|---|
| 5 bad frames in a row | relay/LED ON (on-screen LED without Arduino) | FAIL (red) |
| 5 frames in a row with no detection | no change to relay | NO PART (amber) |
| 5 good frames in a row after FAIL | relay OFF | PASS (green) |
| no camera frame for 2 s | relay set to safe_state (ON) | CAMERA LOST - SAFE STATE (red) |

## Measured (4-minute two-stream run, clips c + d looped, AC power, on-screen LED - no Arduino)

| Metric | Value |
|---|---|
| Events logged | 24 (12 FIRE, 12 RELEASE, all on clip d; 0 on clip c = no false fires on the good part) |
| Frame-to-actuator median / p95 | 177.3 ms / 218.4 ms |
| FPS per stream | 4.45 (clip c), 5.20 (clip d) |
| Earlier 2-minute run (same code) | 7.2-7.6 FPS per stream, 124 ms median - the difference was not explained |

Not measured yet: latency with the real Arduino relay (serial write included).
