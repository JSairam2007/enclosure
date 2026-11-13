# Threat model (M4) - template, fill in for YOUR setup

## 1. System and assets

| Asset | Where it lives | Why it matters |
|---|---|---|
| Camera stream | | |
| Model file (best_int8.onnx) | | |
| rules.yaml | | |
| MPU6050 data + anomaly.joblib | | |
| MQTT broker + credentials | | |
| PLC tags (REJECT, MOTOR_ALERT, MOTOR_SCORE) | | |
| OTA packages | | |

## 2. Trust boundaries / data flows
(Draw or list: camera -> PC -> MQTT -> subscriber/dashboard -> PLC. Mark each network hop.)

## 3. Threats (STRIDE)

| # | Component | Threat (S/T/R/I/D/E) | Example attack | Mitigation in this project | Tested? (how / result) | Residual risk |
|---|---|---|---|---|---|---|
| 1 | MQTT broker | Spoofing | client connects without password | allow_anonymous false + password_file | m4/test_mqtt_auth.py result: | |
| 2 | MQTT link | Info disclosure / Tampering | sniff or alter messages on the LAN | TLS on 8883, no 1883 listener | | |
| 3 | OTA package | Tampering | modified model in update zip | SHA-256 manifest (integrity only, not signed) | | |
| 4 | OTA update | DoS | broken update bricks the line | health check + automatic rollback | m4/ota/demo_ota.py result: | |
| 5 | Edge app | DoS | process crash | watchdog restart | m4_watchdog_log.csv: | |
| 6 | Modbus TCP | Tampering / Spoofing | anyone on the LAN writes coils (Modbus has no auth) | | | |
| 7 | Camera | DoS | camera unplugged / covered | camera_timeout_s -> safe_state | | |
| 8 | Model | Tampering (data) | drift / poisoned retraining data | drift_check.py | | |
| 9 | | | | | | |

## 4. Out of scope / assumptions

## 5. Open actions (owner, date)
