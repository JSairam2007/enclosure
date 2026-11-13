# Threat model - test results (filled)

Blank template: [threat_model.md](threat_model.md). This file records what was actually tested on this PC;
risk ratings and owners are yours to decide.

| # | Threat | Mitigation | Test + result (2026-11-12/13) |
|---|---|---|---|
| 1 | Client connects to MQTT without credentials | `allow_anonymous false` + password file | `M4/test_mqtt_auth.py`: no password -> refused "Not authorized" (PASS) |
| 1b | Wrong password | same | wrong password -> refused (PASS); real credentials -> accepted (PASS) |
| 2 | Sniffing/altering MQTT on the network | TLS only on 8883 (self-signed CA, TLSv1.3 negotiated) | broker log shows TLSv1.3 / TLS_AES_256_GCM_SHA384; plain port 1883 closed (PASS) |
| 2b | Unprotected broker installed alongside | Mosquitto's default Windows service listened on localhost:1883 with no auth | found by the test (FAIL), service stopped + disabled, re-test PASS |
| 3 | Tampered OTA package | SHA-256 per file in manifest (integrity only, NOT signed) | not attack-tested; zip-slip path check in code |
| 4 | Broken update stops the line | health check + automatic rollback | `M4/ota/demo_ota.py`: bad v3 -> rolled back to v2, manual rollback to v1 (PASS) |
| 5 | App crash | watchdog restart with backoff | crash demo: 2 crashes restarted, clean exit logged (PASS) |
| 5b | Silent freeze of the camera loop | worker catches errors, shows ERROR - RESTARTING | found a real freeze (PermissionError on status.json under OneDrive); fixed; 2-min re-test kept running |
| 6 | Anyone on the LAN writes PLC coils | none - Modbus TCP has no authentication | only tested against `M4/plc_sim.py` on localhost; open risk for a real PLC |
| 7 | Camera unplugged / covered | camera_timeout_s -> safe_state, NO PART when empty | NO PART tested; unplug test not done |
| 8 | Drift / poisoned retraining data | `M4/drift_check.py` | not run - no motor data yet |
| 9 | Power loss | Task Scheduler autostart + watchdog | full restart 2026-11-13: dashboard up with no manual step (PASS, `M5/docs/m5_autostart_test.md`) |
| 10 | Secrets leaked in the public repo | `.gitignore` for passwd, mqtt.env, certs; pre-push scan | scan of staged files: no password, no private key (PASS) |

Residual risks to write up: OTA packages are not signed; Modbus is unauthenticated; the broker password is stored
in plain text in `M4/mosquitto/mqtt.env` on the PC (git-ignored, but the folder is synced by OneDrive).
