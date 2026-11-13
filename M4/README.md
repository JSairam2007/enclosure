# M4 - Motor anomaly, communications, security, operations

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
