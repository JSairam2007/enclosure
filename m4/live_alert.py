"""M4 step 2: live motor alert. Reads the MPU6050 stream (or replays a recorded CSV) and scores each window.
Usage:
  python m4/live_alert.py --port COM5                                # live from the Arduino
  python m4/live_alert.py --replay m4/data/fault_1.csv --realtime    # no hardware needed
Prints one line per window and ALERT/CLEAR on debounced changes. Writes m4/motor_state.json
(read by the M5 dashboard and m4/mqtt_publisher.py) and m4_alert_log.csv.
"""
import argparse, collections, csv, json, os, sys, time
import numpy as np
from anomaly_core import AnomalyScorer, AlertState
from features import load_run

p = argparse.ArgumentParser()
p.add_argument("--bundle", default="m4/anomaly.joblib")
p.add_argument("--port")
p.add_argument("--replay")
p.add_argument("--realtime", action="store_true", help="pace a replay at its recorded rate")
p.add_argument("--k", type=int, default=2, help="consecutive windows needed to alert / clear")
p.add_argument("--seconds", type=float, default=0, help="0 = until Ctrl-C / end of replay")
p.add_argument("--state", default="m4/motor_state.json")
a = p.parse_args()
if bool(a.port) == bool(a.replay):
    raise SystemExit("give exactly one of --port or --replay")

sc = AnomalyScorer(a.bundle)
st = AlertState(sc.threshold, a.k)


def rows():
    if a.replay:
        t, x = load_run(a.replay)
        for i, r in enumerate(x):
            if a.realtime and i:
                time.sleep(max(0.0, t[i] - t[i - 1]))
            yield r
    else:
        import serial
        s = serial.Serial(a.port, 115200, timeout=1)
        time.sleep(2)
        s.reset_input_buffer()
        while True:
            parts = s.readline().decode(errors="ignore").strip().split(",")
            if len(parts) == 6:
                try:
                    yield np.array([float(v) for v in parts])
                except ValueError:
                    pass


sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from common.atomic_json import write_json_atomic


def write_state(score, alert):
    # robust to the file being open in the publisher / dashboard / OneDrive (Windows locks on replace)
    write_json_atomic(a.state, {"ts": time.time(), "score": score, "threshold": sc.threshold, "alert": alert})


buf, since, n, t0, log = collections.deque(maxlen=sc.win), 0, 0, time.time(), []
try:
    for r in rows():
        buf.append(r)
        since += 1
        if len(buf) == sc.win and since >= sc.hop:
            since = 0
            n += 1
            score = sc.score_window(np.array(buf))
            ev = st.update(score)
            write_state(score, st.active)
            log.append([round(time.time() - t0, 3), n, round(score, 5), int(st.active), ev or ""])
            print(f"win {n:4d} score={score:.4f} thr={sc.threshold:.4f} {'ALERT' if st.active else 'ok'}"
                  + (f"  <-- {ev}" if ev else ""))
        if a.seconds and time.time() - t0 > a.seconds:
            break
except KeyboardInterrupt:
    pass
with open("m4_alert_log.csv", "w", newline="") as f:
    csv.writer(f).writerows([["t_s", "window", "score", "alert_active", "event"]] + log)
print(f"windows scored: {n}, alert events: {sum(1 for r in log if r[4] == 'ALERT')}")
