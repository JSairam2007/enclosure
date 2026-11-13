# M5 - Integrate and prove

## Task folders (one per assessment column)
The numbered folders are the group's M5 package (`group_package_README.md`: templates and a dashboard
prototype). Real evidence for this project is listed next to each task.

| # | Task | Group folder | Real evidence in this repo |
|---|---|---|---|
| 1 | Inspection rig | [01_inspection_rig](01_inspection_rig) | [../M1/docs/data_card_filled.md](../M1/docs/data_card_filled.md) (camera, clips, setup) |
| 2 | Pass/fail station | [02_pass_fail_station](02_pass_fail_station) | [eval_parts.py](eval_parts.py) + [parts_manifest.csv](parts_manifest.csv) - **20-part test pending** |
| 3 | Full chain on the device | [03_full_chain_on_device](03_full_chain_on_device) | [dashboard.py](dashboard.py) (camera -> ONNX INT8 -> rule -> MQTT), [results/m5_soak_summary.json](results/m5_soak_summary.json) (10 min, 0 errors) |
| 4 | Live dashboard | [04_live_dashboard](04_live_dashboard) | [dashboard.py](dashboard.py) (Flask, live camera, FAIL / NO PART / PASS, KPIs) |
| 5 | Product readiness | [05_product_readiness](05_product_readiness) | [docs/m5_autostart_test.md](docs/m5_autostart_test.md) (power-cycle PASS), [autostart/](autostart) |
| 6 | Headline metric | [06_headline_metric](06_headline_metric) | [headline.py](headline.py) - false-pass rate after the 20-part test |
| 7 | Documents | [07_documents](07_documents) | [../README.md](../README.md), per-milestone `docs/` folders |
| 8 | Live demo and questions | [08_live_demo_questions](08_live_demo_questions) | [verdict_check.py](verdict_check.py), [live_session_report.py](live_session_report.py) |

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
