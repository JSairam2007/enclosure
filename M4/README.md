# M4 - Motor anomaly, communications, security, operations

## Task folders (one per assessment column)
The numbered folders are the group's M4 package (`group_package_README.md`; status in
`group_evidence_status.md` - its sensor data is synthetic). Real evidence for this project is listed next to each task.

| # | Task | Group folder | Real evidence in this repo |
|---|---|---|---|
| 1 | Sensor data | [01_sensor_data](01_sensor_data) | [mpu6050_stream.ino](mpu6050_stream.ino), [mpu_logger.py](mpu_logger.py), [phyphox_import.py](phyphox_import.py) - **real recordings pending** |
| 2 | Anomaly model | [02_anomaly_model](02_anomaly_model) | [train_anomaly.py](train_anomaly.py), [live_alert.py](live_alert.py), [run_motor_pipeline.py](run_motor_pipeline.py) |
| 3 | False alarms | [03_false_alarms](03_false_alarms) | [false_alarm_counter.py](false_alarm_counter.py) - runs once the 5 normal recordings exist |
| 4 | Secure MQTT | [04_secure_mqtt](04_secure_mqtt) | [results/m4_mqtt_auth_test.json](results/m4_mqtt_auth_test.json) (4/4 PASS), [mosquitto/](mosquitto) |
| 5 | Topics | [05_topics](05_topics) | [mqtt_publisher.py](mqtt_publisher.py), [mqtt_subscriber.py](mqtt_subscriber.py) (`edgeai/vision/status`, `edgeai/motor/score`) |
| 6 | PLC link | [06_plc_link](06_plc_link) | [plc_write.py](plc_write.py) + [plc_sim.py](plc_sim.py) (Modbus TCP, read-back tested) |
| 7 | Threat model | [07_threat_model](07_threat_model) | [docs/threat_model_filled.md](docs/threat_model_filled.md) |
| 8 | Reliability | [08_reliability](08_reliability) | [ota/](ota) (rollback tested), [watchdog.py](watchdog.py) (restart tested), [drift_check.py](drift_check.py) |

Run all commands from the repository root.

## Motor anomaly (IsolationForest, trained on normal runs only)
| File | Does |
|---|---|
| `phyphox_import.py` + `run_motor_pipeline.py` | phone IMU path: import phyphox zips from `phone_raw/`, then train -> false alarms -> drift -> fault replays, in one command |
| `mpu6050_stream.ino` + `mpu_logger.py` | Arduino path: stream and record MPU6050 runs to `data/` |
| `features.py`, `anomaly_core.py` | windowing + features, scorer, debounced alert |
| `train_anomaly.py` | train on normal runs; threshold from training scores |
| `live_alert.py` | live (serial) or replayed alert; writes `motor_state.json` for the dashboard / MQTT |
| `false_alarm_counter.py` | alerts over 5 new normal runs = false alarms |
| `drift_check.py` | KS test of new normal data vs the training baseline |

```bat
python M4\run_motor_pipeline.py
```

## Communications and security
| File | Does |
|---|---|
| `mosquitto/gen_certs.py` + `mosquitto.conf.template` | self-signed CA + server cert, TLS-only broker config with password |
| `test_mqtt_auth.py` | no-password / wrong-password must be refused, real login accepted, port 1883 closed |
| `mqtt_publisher.py`, `mqtt_subscriber.py`, `mqtt_common.py` | publish vision status + motor score over TLS, log what arrives |
| `plc_write.py` + `plc_sim.py` | optional Modbus TCP tags (REJECT, MOTOR_ALERT, MOTOR_SCORE) and a simulator |

## Operations
| File | Does |
|---|---|
| `ota/ota.py` + `ota/demo_ota.py` | OTA v1 -> v2 with SHA-256 check, health check and automatic rollback |
| `watchdog.py` + `crash_demo.py` | restart on crash or stale heartbeat, with backoff and a log |

## Results (`results/`)
- `m4_mqtt_auth_test.json` - the 4 security checks (all PASS)
- motor results appear here after the pipeline runs: `m4_false_alarms.csv`, `m4_drift.csv`, `m4_alert_log.csv`

## Reports (`docs/`)
- `threat_model.md` - **blank template: risks, owners**
- `threat_model_filled.md` - what was tested and the results

Status: MQTT / PLC / OTA / watchdog **done and tested.** Pending: **motor vibration recordings** (phone or Arduino).
