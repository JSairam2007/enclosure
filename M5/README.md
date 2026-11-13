# M5 - Integrate and prove

Run all commands from the repository root.

| File | Does |
|---|---|
| `dashboard.py` | Flask live dashboard: camera view, FAIL / NO PART / PASS, detections, 3 KPIs, motor alert, headline metrics (http://127.0.0.1:5000) |
| `verdict_check.py` | run the verdict logic over a recorded clip, print the timeline |
| `eval_parts.py` + `parts_manifest.csv` | 20-part pass/fail evaluation -> confusion matrix + false-pass rate |
| `soak_test.py` + `soak_report.py` | 10-minute soak test with a per-second log, and its summary by period |
| `live_session_report.py` | timeline of a live session from the MQTT subscriber log |
| `headline.py` | all headline metrics, read only from the result files |
| `autostart/` | Windows Task Scheduler task + launcher (watchdog -> dashboard), Linux systemd unit |

```bat
python M5\dashboard.py --model models\best_int8.onnx --source 0
python M5\soak_test.py --model models\best_int8.onnx --source clips\c.mp4 --minutes 10
python M5\eval_parts.py --model models\best_int8.onnx --manifest M5\parts_manifest.csv
python M5\headline.py
schtasks /Create /TN "EdgeAI" /XML M5\autostart\edgeai_task.xml
```

## Results (`results/`)
- `m5_soak_summary.json`, `m5_soak_log.csv` - 10-minute soak (frames, errors, FPS, memory)
- after the 20-part run: `m5_eval_summary.json`, `m5_eval_parts.csv`, `m5_confusion.md`

## Reports (`docs/`)
- `m5_autostart_test.md` - power-cycle test record (boot time, task run, dashboard up)

Status: dashboard, soak test, autostart **done.** Pending: **record 20 part clips** and fill `parts_manifest.csv`.
