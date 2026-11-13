# M4 evidence status

| Criterion | Included asset | Actual proof still required |
|---|---|---|
| Sensor data | Synthetic MPU6050-shaped CSV generator | 3 normal + 3 fault real sensor CSV runs |
| Anomaly model | IsolationForest demo on synthetic data | Train on real normal-only data and inject live fault |
| False alarms | Synthetic evaluator | 5 real normal runs and threshold rationale |
| Secure MQTT | Mosquitto TLS config + test plan | Broker rejects anonymous and accepts authenticated TLS |
| Topics | Local topic/payload printer | Real broker publish + subscriber output |
| PLC link | Local PLC tag simulator | Actual PLC tag changes on detection |
| Threat model | Threat register | Apply and evidence 2 mitigations per level |
| Reliability | Restart demo + evidence template | Drift report, OTA rollback, forced-crash auto-restart |
