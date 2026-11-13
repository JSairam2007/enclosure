"""M4 shared MQTT client setup: TLS + username/password from environment variables (never hard-coded).
Env: MQTT_HOST (localhost) MQTT_PORT (8883) MQTT_CA (M4/mosquitto/certs/ca.crt) MQTT_USER MQTT_PASS
PowerShell:  $env:MQTT_USER="edgeai"; $env:MQTT_PASS="<your password>"
"""
import json, os, time
import paho.mqtt.client as mqtt

TOPIC_DET = "edgeai/vision/status"
TOPIC_MOTOR = "edgeai/motor/score"


def _load_env_file(path="M4/mosquitto/mqtt.env"):
    """Fill MQTT_USER/MQTT_PASS from the git-ignored file if the environment does not set them."""
    if os.path.exists(path):
        for ln in open(path):
            if "=" in ln:
                k, v = ln.strip().split("=", 1)
                os.environ.setdefault(k, v)


def settings():
    _load_env_file()
    return {"host": os.environ.get("MQTT_HOST", "localhost"), "port": int(os.environ.get("MQTT_PORT", "8883")),
            "ca": os.environ.get("MQTT_CA", "M4/mosquitto/certs/ca.crt"),
            "user": os.environ.get("MQTT_USER"), "password": os.environ.get("MQTT_PASS")}


def connect(client_id, user="env", password="env", timeout=5.0):
    """Returns a connected, looping client or raises RuntimeError with the broker's reason."""
    s = settings()
    user = s["user"] if user == "env" else user
    password = s["password"] if password == "env" else password
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    c.tls_set(ca_certs=s["ca"])
    if user:
        c.username_pw_set(user, password)
    res = {}
    c.on_connect = lambda cl, ud, fl, rc, pr: res.setdefault("rc", rc)
    c.connect(s["host"], s["port"], keepalive=30)
    c.loop_start()
    t0 = time.time()
    while "rc" not in res and time.time() - t0 < timeout:
        time.sleep(0.05)
    if "rc" not in res:
        c.loop_stop()
        raise RuntimeError("no CONNACK from broker (timeout)")
    if res["rc"].is_failure:
        c.loop_stop()
        raise RuntimeError(f"broker refused: {res['rc']}")
    return c


def publish_json(client, topic, obj, qos=1):
    return client.publish(topic, json.dumps(obj), qos=qos)
