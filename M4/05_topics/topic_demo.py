"""Print example MQTT-style payloads locally; no broker connection."""
import json
from datetime import datetime, timezone

device="rpi5-carton-inspection-01"
events=[
    ("factory/carton_inspection/line1/detection",
     {"schema_version":1,"device_id":device,"timestamp":datetime.now(timezone.utc).isoformat(),
      "classification":"OPEN","confidence":0.93,"model_version":"demo-not-validated"}),
    ("factory/carton_inspection/line1/motor_score",
     {"schema_version":1,"device_id":device,"timestamp":datetime.now(timezone.utc).isoformat(),
      "anomaly_score":0.71,"source":"synthetic-demo"})
]
for topic,payload in events:
    print("TOPIC:",topic)
    print("PAYLOAD:",json.dumps(payload))
