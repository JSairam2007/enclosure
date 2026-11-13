"""M4: security test - the broker must REFUSE clients without a password (and with a wrong one),
and accept the real credentials from MQTT_USER / MQTT_PASS.
Usage: python M4/test_mqtt_auth.py          (broker must be running: mosquitto -c M4/mosquitto/mosquitto.conf -v)
Exit 0 = all checks passed, 1 = a check failed, 2 = broker not reachable (cannot conclude anything).
Results go to M4/results/m4_mqtt_auth_test.json.
"""
import json, socket, ssl, sys
from mqtt_common import connect, settings

s = settings()
results = []


def case(name, user, password, expect_ok):
    try:
        c = connect(f"authtest-{name}", user=user, password=password)
        c.loop_stop(); c.disconnect()
        ok, detail = True, "connected"
    except RuntimeError as e:
        ok, detail = False, str(e)
    except (ConnectionRefusedError, socket.timeout, OSError, ssl.SSLError) as e:
        print(f"broker not reachable at {s['host']}:{s['port']}: {e!r}")
        sys.exit(2)
    passed = ok == expect_ok
    results.append({"case": name, "expected": "accept" if expect_ok else "refuse",
                    "got": "accept" if ok else "refuse", "detail": detail, "pass": passed})
    print(f"[{'PASS' if passed else 'FAIL'}] {name}: expected {'accept' if expect_ok else 'refuse'}, got {detail}")


case("no_password", None, None, expect_ok=False)
case("wrong_password", s["user"] or "edgeai", "definitely-wrong-password", expect_ok=False)
if s["user"] and s["password"]:
    case("valid_credentials", "env", "env", expect_ok=True)
else:
    print("[SKIP] valid_credentials: set MQTT_USER and MQTT_PASS to test the positive case")

# Plain-text port must not be open (config opens TLS 8883 only).
try:
    socket.create_connection((s["host"], 1883), timeout=2).close()
    results.append({"case": "plaintext_1883_closed", "pass": False, "detail": "port 1883 accepted a TCP connection"})
    print("[FAIL] plaintext_1883_closed: something is listening on 1883 (another broker/service?)")
except OSError:
    results.append({"case": "plaintext_1883_closed", "pass": True, "detail": "connection refused"})
    print("[PASS] plaintext_1883_closed")

json.dump(results, open("M4/results/m4_mqtt_auth_test.json", "w"), indent=1)
sys.exit(0 if all(r["pass"] for r in results) else 1)
