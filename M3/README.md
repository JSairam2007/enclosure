# M3 - Decide and act

Detections -> decision rule (`rules.yaml`) -> debounce -> actuator (Arduino relay + LED over USB serial, or an
on-screen LED without `--serial`). Two camera/video streams at once, frame-to-actuator latency logged per event.
The detector and rule logic live in `../common/` and are shared with M5.

| File | Does |
|---|---|
| `decide_act.py` | the loop: streams, rule, debounce, actuator, latency + FPS logs |
| `rules.yaml` | mode, defect classes (`case_open`, `lid`), confidence, debounce, NO PART, camera timeout, safe state |
| `arduino_relay.ino` | Arduino sketch: `'1'` -> relay (pin 7) + LED (pin 13) on, `'0'` -> off |

```bat
python M3\decide_act.py --model models\best_int8.onnx --sources clips\c.mp4 clips\d.mp4 --headless --loop --max-seconds 240
python M3\decide_act.py --model models\best_int8.onnx --sources 0 --serial COM5      :: with the Arduino
```
Verdict order: FAIL (5 bad frames in a row) > NO PART (5 frames with no detection) > PASS.
Docker: `docker build -t edgeai .` from the repository root (see `../Dockerfile`).

## Results (`results/`)
- `m3_summary.json` - events, frame-to-actuator median / p95, FPS per stream
- `m3_events.csv` - every FIRE / RELEASE with its latency; `m3_fps.csv` - FPS per stream
- `m3_summary_v1.json` - the first model's run

## Reports (`docs/`)
- `decision_rules.md` - **blank: your reasons for each rule value**
- `decision_rules_filled.md` - current values, action table, measured latency

Status: **done with the on-screen LED.** Pending: a run with the real Arduino relay (`--serial COM?`).
