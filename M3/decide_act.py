"""M3: decision rule + debounce + actuator + two streams + frame-to-actuator latency log.
Usage:
  python M3/decide_act.py --model models/best_int8.onnx --sources clips/a.mp4 clips/b.mp4
  python M3/decide_act.py --model models/best_int8.onnx --sources 0 --serial COM5     # Arduino relay + LED
Options: --loop replay files until --max-seconds; --headless no windows (Docker/soak).
Rules come from M3/rules.yaml. Without --serial the actuator is an on-screen red LED only.
Logs: M3/results/m3_events.csv (one row per FIRE/RELEASE with frame->actuator ms), M3/results/m3_fps.csv, M3/results/m3_summary.json.
Latency = time from frame read (t_capture) to the moment the serial write returned.
"""
import argparse, csv, json, os, sys, threading, time, queue
import cv2

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from common.rules_engine import load_rules, frame_is_bad, Debounce, Actuator
from common.onnx_detector import Detector, threads_per_stream

p = argparse.ArgumentParser()
p.add_argument("--model", required=True)
p.add_argument("--sources", nargs="+", default=["0"])
p.add_argument("--serial")
p.add_argument("--rules", default="M3/rules.yaml")
p.add_argument("--headless", action="store_true")
p.add_argument("--loop", action="store_true")
p.add_argument("--max-seconds", type=float, default=0, help="0 = until sources end / q pressed")
a = p.parse_args()
R = load_rules(a.rules)
act, lock, stop = Actuator(a.serial), threading.Lock(), threading.Event()
events, fps_log, frames_q = [], [], queue.Queue(maxsize=4)
t_begin = time.perf_counter()


def stream(idx, src):
    det = Detector(a.model, conf=R["confidence"], threads=threads_per_stream(len(a.sources)))
    isfile = not src.isdigit()
    cap = cv2.VideoCapture(src if isfile else int(src))
    deb = Debounce(R["debounce_frames"])
    n, t0, last_ok = 0, time.perf_counter(), time.perf_counter()
    while not stop.is_set():
        if a.max_seconds and time.perf_counter() - t_begin > a.max_seconds:
            break
        ok, fr = cap.read()
        if not ok:
            if isfile:
                if a.loop:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                break  # end of clip
            if time.perf_counter() - last_ok > R["camera_timeout_s"]:
                with lock:
                    act.set(R["safe_state"] == "ON")
                print(f"[stream {idx}] camera lost -> SAFE STATE {R['safe_state']}")
                break
            continue
        last_ok = t_cap = time.perf_counter()
        dets = det(fr)
        bad = frame_is_bad([c for c, _, _ in dets], R)
        d = deb.update(bad)
        if d:
            with lock:
                t_act = act.set(d == "FIRE")
                events.append([idx, n, d, round((t_act - t_cap) * 1000, 2)])
        n += 1
        if not a.headless:
            for c, s, (x1, y1, x2, y2) in dets:
                col = (0, 0, 255) if c in R.get("defect_classes", []) else (0, 255, 0)
                cv2.rectangle(fr, (x1, y1), (x2, y2), col, 2)
                cv2.putText(fr, f"{c} {s:.2f}", (x1, max(15, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, col, 1)
            cv2.circle(fr, (fr.shape[1] - 30, 30), 15, (0, 0, 255) if act.state == "ON" else (60, 60, 60), -1)
            cv2.putText(fr, f"S{idx} {n / (time.perf_counter() - t0):.1f}FPS bad={bad}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            try:
                frames_q.put_nowait((idx, fr))
            except queue.Full:
                pass
    with lock:
        fps_log.append([idx, n, round(n / max(1e-9, time.perf_counter() - t0), 2)])


threads = [threading.Thread(target=stream, args=(i, s), daemon=True) for i, s in enumerate(a.sources)]
for t in threads:
    t.start()
try:
    while any(t.is_alive() for t in threads):
        if a.headless:
            time.sleep(0.2)
            continue
        try:
            i, f = frames_q.get(timeout=0.1)
            cv2.imshow(f"stream {i}", f)
        except queue.Empty:
            pass
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
except KeyboardInterrupt:
    pass
stop.set()
for t in threads:
    t.join(timeout=3)

with open("M3/results/m3_events.csv", "w", newline="") as f:
    csv.writer(f).writerows([["stream", "frame", "decision", "frame_to_actuator_ms"]] + events)
with open("M3/results/m3_fps.csv", "w", newline="") as f:
    csv.writer(f).writerows([["stream", "frames", "fps"]] + fps_log)
lat = sorted(e[3] for e in events)
summ = {"events": len(lat), "fps_per_stream": fps_log, "serial": bool(a.serial)}
if lat:
    summ["latency_median_ms"] = lat[len(lat) // 2]
    summ["latency_p95_ms"] = lat[max(0, int(.95 * len(lat)) - 1)]
json.dump(summ, open("M3/results/m3_summary.json", "w"), indent=1)
print(json.dumps(summ, indent=1))
if len(lat) < 20:
    print(f"note: only {len(lat)} events; the brief asks for 20+ for a latency claim")
