"""M4: MQTT subscriber - prints every edgeai/# message and logs it with receive time to M4/results/m4_mqtt_log.csv.
Usage: python M4/mqtt_subscriber.py [--seconds 0]
The publish->receive delay column uses the 'ts' field inside the message (same PC = same clock).
"""
import argparse, csv, json, time
from mqtt_common import connect

p = argparse.ArgumentParser()
p.add_argument("--topic", default="edgeai/#")
p.add_argument("--seconds", type=float, default=0)
a = p.parse_args()
f = open("M4/results/m4_mqtt_log.csv", "w", newline="")
w = csv.writer(f)
w.writerow(["recv_ts", "topic", "delay_ms", "payload"])
n = 0


def on_message(cl, ud, msg):
    global n
    now = time.time()
    try:
        obj = json.loads(msg.payload)
        delay = round((now - obj["ts"]) * 1000, 1) if isinstance(obj, dict) and "ts" in obj else ""
    except ValueError:
        delay = ""
    w.writerow([round(now, 3), msg.topic, delay, msg.payload.decode(errors="replace")])
    f.flush()
    n += 1
    print(msg.topic, msg.payload.decode(errors="replace")[:160])


c = connect("edgeai-subscriber")
c.on_message = on_message
c.subscribe(a.topic, qos=1)
print("subscribed to", a.topic, "- Ctrl-C to stop")
t0 = time.time()
try:
    while not a.seconds or time.time() - t0 < a.seconds:
        time.sleep(0.2)
except KeyboardInterrupt:
    pass
c.loop_stop(); c.disconnect(); f.close()
print("messages received:", n)
