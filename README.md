# Edge AI & Embedded Vision - "ir case" inspection cell

Reference project on a Windows PC (Ryzen 5, CPU only). A camera watches my own 3D-printed IR-sensor
enclosure ("ir case"); a YOLOv8n model (ONNX INT8) detects `case_closed`, `case_open` and a loose `lid`;
a debounced rule drives an Arduino relay/LED; an MPU6050 on the motor feeds an IsolationForest anomaly
model; results go over MQTT (TLS + password), optionally to a PLC (Modbus TCP), and to a Flask dashboard.

**Every number in this repo must come from running these scripts on this machine.** The docs/ templates
have blank result fields on purpose. The scripts write their results to files (`m1_metrics.json`,
`m2_results.csv`, `m3_summary.json`, `m4_false_alarms.csv`, `m5_eval_summary.json`, `m5_soak_summary.json`)
and `python m5/headline.py` shows only what those files contain.

## Architecture

```mermaid
flowchart LR
  subgraph Edge PC [Windows PC - Ryzen 5, CPU]
    CAM[USB camera / video file] --> DET[YOLOv8n ONNX INT8<br/>m3 decide_act / m5 dashboard]
    DET --> RULE[rules.yaml<br/>debounce N frames]
    RULE -->|serial '1'/'0'| ARD[Arduino relay + LED]
    RULE --> STATUS[(m5/status.json)]
    IMU[MPU6050 + Arduino] -->|serial 100 Hz| LIVE[m4 live_alert<br/>IsolationForest]
    LIVE --> MOTOR[(m4/motor_state.json)]
    STATUS --> DASH[Flask dashboard :5000]
    MOTOR --> DASH
    STATUS --> PUB[mqtt_publisher]
    MOTOR --> PUB
    WD[watchdog] -.restarts.-> DASH
    OTA[OTA v1→v2<br/>health check + rollback] -.deploys.-> DET
  end
  PUB -->|TLS 8883 + password| BROKER[Mosquitto]
  BROKER --> SUB[mqtt_subscriber / SCADA]
  PUB -->|Modbus TCP, optional| PLC[PLC or plc_sim.py]
```

## Folder map

| Path | What |
|---|---|
| `m1/` | frames from video, auto-label helper, split by video, overlay + baseline log, train/eval |
| `m2/` | ONNX export, INT8 quantisation, warm-up + 100-run benchmark |
| `m3/` + `common/` | rules.yaml, debounce, actuator (Arduino), two streams, latency log, Dockerfile |
| `m4/` | MPU6050 logger + anomaly model, live alert, false alarms, MQTT (TLS), PLC, drift, OTA, watchdog |
| `m5/` | Flask dashboard, 20-part evaluation, 10-min soak test, autostart, headline metrics |
| `docs/` | blank templates: data card, decision rules, M2 target, threat model, M1 error analysis |

## Setup (Windows)

onnxruntime has no wheel for Python 3.15, so use Python 3.12. Keep the venv at a short path
(deep project paths break pip on Windows' 260-character limit).

```bat
py install 3.12
py -3.12 -m venv %LOCALAPPDATA%\edgeai-venv
%LOCALAPPDATA%\edgeai-venv\Scripts\activate
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

Runtime inference uses `common/onnx_detector.py` (onnxruntime directly, explicit thread budget per stream);
on this CPU the ultralytics `predict()` wrapper was about 2x slower for the same model and outputs.

Hardware: Arduino Uno/Nano for the relay (`m3/arduino_relay.ino`, relay on pin 7, LED pin 13) and for the
MPU6050 (`m4/mpu6050_stream.ino`, SDA A4, SCL A5). Mosquitto for M4: install from mosquitto.org.
Find your COM port in Device Manager → Ports.

## Run order

### M1 - data, baseline, first model
```bat
python m1\extract_frames.py clips\a.mp4 clips\b.mp4 clips\c.mp4 clips\d.mp4 clips\e.mp4 clips\f.mp4 --every 10
:: label: either Roboflow/CVAT/LabelImg (YOLO .txt next to each .jpg), or propose + review:
python m1\autolabel.py propose --clip a --cls case_closed
python m1\autolabel.py propose --clip d --two
python m1\autolabel.py sheet --clip a          :: look at review\a_*.jpg
python m1\autolabel.py exclude --clip a --frames 000000 000010   :: move bad frames aside (recoverable)
:: clip d was cut into time segments d1/d2/d3 (with gaps) so every split has open-case/lid frames
python m1\split_dataset.py --train a b d1 e --val d2 d3 --test c f
python m1\overlay_baseline.py --source clips\c.mp4                      :: contour baseline
python m1\train_eval.py --epochs 50
python m1\annotate_test.py                     :: boxes on every test image -> test_annotated\
```
Clips: a-d first recording session; e = closed case filmed top-down, f = closed then opened + loose lid
(e and f were added after v1 missed top-down closed cases). Test clips c and f are never trained on.
Fill `docs/data_card.md` and `docs/m1_error_analysis.md` (10 rows from `m1_errors.csv`).

### M2 - optimise
Fill `docs/m2_target.md` **first**, then:
```bat
python m2\export_benchmark.py --weights runs\detect\train\weights\best.pt --data dataset\data.yaml --calib dataset\images\val
```

### M3 - decide and act
Edit `m3/rules.yaml`, justify it in `docs/decision_rules.md`, flash `m3/arduino_relay.ino`.
```bat
python m3\decide_act.py --model models\best_int8.onnx --sources clips\c.mp4 clips\a.mp4
python m3\decide_act.py --model models\best_int8.onnx --sources 0 --serial COM5
docker build -t edgeai . && docker run --rm edgeai
```

### M4 - motor, comms, security, operations
```bat
:: data option A - phone IMU (no Arduino): record 60 s runs in phyphox (raw Accelerometer [+ Gyroscope]),
::   export CSV zips named normal_1..3, normal_11..15, fault_1.. into m4\phone_raw\, then ONE command:
python m4\run_motor_pipeline.py
:: data option B - MPU6050 (flash m4\mpu6050_stream.ino first)
python m4\mpu_logger.py --port COM5 --label normal --run 1 --seconds 60     :: runs 1-3 = training
python m4\mpu_logger.py --port COM5 --label normal --run 11 --seconds 60    :: runs 11-15 = false-alarm test
python m4\mpu_logger.py --port COM5 --label fault  --run 1 --seconds 60
python m4\train_anomaly.py --files m4\data\normal_1.csv m4\data\normal_2.csv m4\data\normal_3.csv --fault-files m4\data\fault_1.csv
python m4\live_alert.py --port COM5
python m4\false_alarm_counter.py --files m4\data\normal_11.csv m4\data\normal_12.csv m4\data\normal_13.csv m4\data\normal_14.csv m4\data\normal_15.csv
python m4\drift_check.py --files m4\data\normal_20.csv

:: MQTT with TLS + password
python m4\mosquitto\gen_certs.py
mosquitto_passwd -c m4\mosquitto\passwd edgeai
mosquitto -c m4\mosquitto\mosquitto.conf -v
set MQTT_USER=edgeai
set MQTT_PASS=<your password>
python m4\test_mqtt_auth.py             :: no-password client must be refused
python m4\mqtt_subscriber.py
python m4\mqtt_publisher.py

:: optional PLC
python m4\plc_sim.py
python m4\plc_write.py --reject 1 --motor-alert 0 --score 0.123 --readback

:: operations
python m4\ota\demo_ota.py
python m4\watchdog.py --max-restarts 5 -- python m4\crash_demo.py
```
Fill `docs/threat_model.md` with the test results.

### M5 - integrate and prove
```bat
python m5\dashboard.py --model models\best_int8.onnx --source 0          :: http://127.0.0.1:5000
python m5\eval_parts.py --model models\best_int8.onnx --manifest m5\parts_manifest.csv
python m5\soak_test.py --model models\best_int8.onnx --source clips\c.mp4 --minutes 10
python m5\soak_report.py                      :: FPS / memory per period of the soak
python m5\live_session_report.py --since "2026-11-13 12:46:00"   :: timeline from the MQTT subscriber log
python m5\headline.py
:: auto-start: edit paths in m5\autostart\start_edgeai.bat and edgeai_task.xml, then
schtasks /Create /TN "EdgeAI" /XML m5\autostart\edgeai_task.xml
```
Linux: `m5/autostart/edgeai.service` (instructions in the file).

## Status

| Milestone | State |
|---|---|
| M1 data + model | done (v2 model with clips e/f); results in `m1_metrics.json`, error list in `m1_errors.csv` |
| M2 optimise | done; `m2_results.md` (measured on AC power - battery throttles the CPU) |
| M3 decide + act | done with the on-screen LED actuator; Arduino relay run pending (hardware) |
| M4 motor anomaly | code ready; **pending real vibration recordings** (phone/phyphox or MPU6050) |
| M4 MQTT / PLC / OTA / watchdog | done and tested (TLS + password, no-password refused, PLC simulator, rollback, restart) |
| M5 dashboard / soak / autostart | done; power-cycle evidence in `docs/m5_autostart_test.md` |
| M5 20-part evaluation | **pending: record 20 part clips** and fill `m5/parts_manifest.csv` |

Known gap: with no part in view the verdict is PASS (rules only fail on a defect class). A `NO PART`
state is a planned change to `m3/rules.yaml` / the dashboard.

Not in this repository (see `.gitignore`): videos, extracted frames, trained models, the broker password
file and TLS keys. Re-create them with the commands above.

## Templates (blank - fill from your own runs)

- [Data card](docs/data_card.md)
- [Decision-rule sheet](docs/decision_rules.md)
- [M2 target](docs/m2_target.md)
- [Threat model](docs/threat_model.md)
- [M1 error analysis](docs/m1_error_analysis.md)
- [M5 auto-start test record](docs/m5_autostart_test.md)

## Results

| Headline metric | Value | Source file |
|---|---|---|
| M1 test mAP@0.5 | | m1_metrics.json |
| M2 INT8 CPU median latency (ms) | | m2_results.csv |
| M3 frame→actuator median / p95 (ms) | | m3_summary.json |
| M4 false alarms over 5 normal runs | | m4_false_alarms.csv |
| M5 false-pass rate (20 parts) | | m5_eval_summary.json |
| M5 10-min soak: errors / mean FPS | | m5_soak_summary.json |
