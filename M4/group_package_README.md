# M4 — Monitor and Connect

**Project context:** Raspberry Pi 5 carton seal inspection (SEALED / OPEN), with monitoring and industrial connectivity concepts.  
**Package type:** Offline demo scripts, synthetic data, configuration examples and proof templates. Not evidence of connected physical sensors, broker, PLC, or production deployment.

## Eight M4 assessment criteria
1. Sensor data
2. Anomaly model
3. False alarms
4. Secure MQTT
5. Topics
6. PLC link
7. Threat model
8. Reliability

## Run the offline demos
```bash
python -m venv .venv
# Linux: source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt

python 01_sensor_data/generate_sensor_data.py
python 02_anomaly_model/train_anomaly_demo.py
python 03_false_alarms/evaluate_false_alarms.py
python 05_topics/topic_demo.py
python 06_plc_link/plc_tag_simulator.py
python 08_reliability/restart_simulator.py
```

## Important status
Sensor CSVs are synthetic. The anomaly model is a simple software demonstration. MQTT security, PLC tag changes, OTA rollback, drift monitoring and auto-restart still require tests against actual infrastructure before being marked complete.
