"""M4: MQTT publisher - detections + motor score, over TLS with a password.
It tails two state files written by the live programs:
  m5/status.json        (written by m5/dashboard.py: PASS/FAIL, detections, KPIs)
  m4/motor_state.json   (written by m4/live_alert.py: anomaly score, threshold, alert)
and publishes each new version once. Missing files are skipped (that source is simply not running).
Usage: python m4/mqtt_publisher.py [--period 0.5] [--plc-host 127.0.0.1 --plc-port 5020]
With --plc-host it also writes the PLC tags (see m4/plc_write.py) - optional.
"""
import argparse, json, os, time
from mqtt_common import connect, publish_json, TOPIC_DET, TOPIC_MOTOR

p = argparse.ArgumentParser()
p.add_argument("--vision", default="m5/status.json")
p.add_argument("--motor", default="m4/motor_state.json")
p.add_argument("--period", type=float, default=0.5)
p.add_argument("--plc-host")
p.add_argument("--plc-port", type=int, default=5020)
a = p.parse_args()

c = connect("edgeai-publisher")
plc = None
if a.plc_host:
    from plc_write import PlcTags
    plc = PlcTags(a.plc_host, a.plc_port)
last = {a.vision: None, a.motor: None}
sent = {a.vision: 0, a.motor: 0}
print("publishing; Ctrl-C to stop")
try:
    while True:
        for path, topic in ((a.vision, TOPIC_DET), (a.motor, TOPIC_MOTOR)):
            if not os.path.exists(path):
                continue
            m = os.path.getmtime(path)
            if m == last[path]:
                continue
            last[path] = m
            try:
                obj = json.load(open(path))
            except (json.JSONDecodeError, OSError):
                continue  # file being replaced; next loop
            publish_json(c, topic, obj)
            sent[path] += 1
            if plc:
                if topic == TOPIC_DET:
                    plc.write(reject=obj.get("verdict") == "FAIL")
                else:
                    plc.write(motor_alert=bool(obj.get("alert")), score=obj.get("score"))
        time.sleep(a.period)
except KeyboardInterrupt:
    pass
c.loop_stop(); c.disconnect()
print("messages sent:", {os.path.basename(k): v for k, v in sent.items()})
