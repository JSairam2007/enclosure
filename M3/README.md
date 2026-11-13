# M3 - Decide and act

## Task folders (one per assessment column)
The numbered folders are the group's M3 package (`group_package_README.md`; its own status table is in
`group_evidence_status.md` - it runs as a dry-run simulation). Real measured evidence for this project is
listed next to each task.

| # | Task | Group folder | Real evidence in this repo |
|---|---|---|---|
| 1 | Decision rule sheet | [01_decision_rule_sheet](01_decision_rule_sheet) | [rules.yaml](rules.yaml), [docs/decision_rules_filled.md](docs/decision_rules_filled.md) |
| 2 | Two-stream pipeline | [02_two_stream_pipeline](02_two_stream_pipeline) | [decide_act.py](decide_act.py) (2 video streams), [results/m3_fps.csv](results/m3_fps.csv) |
| 3 | Debounce | [03_debounce](03_debounce) | `Debounce` / `Verdict` in [../common/rules_engine.py](../common/rules_engine.py) |
| 4 | Actuator fires | [04_actuator_fires](04_actuator_fires) | [arduino_relay.ino](arduino_relay.ino), [results/m3_events.csv](results/m3_events.csv) (24 FIRE/RELEASE, on-screen LED) |
| 5 | Docker | [05_docker](05_docker) | [../Dockerfile](../Dockerfile) |
| 6 | End-to-end latency | [06_end_to_end_latency](06_end_to_end_latency) | [results/m3_summary.json](results/m3_summary.json) (median 177 ms, p95 218 ms, 24 events) |

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
