"""M5: soak test - run the full vision + rule loop for N minutes (default 10) and log health every second.
Usage: python m5/soak_test.py --model models/best_int8.onnx --source clips/c.mp4 --minutes 10
(a file source is looped; --source 0 uses the webcam). Exceptions are counted and logged, not hidden.
Outputs: m5_soak_log.csv (per second: frames, fps, latency, cpu, memory, errors), m5_soak_summary.json
"""
import argparse, csv, json, os, statistics, sys, time, traceback
import cv2, psutil

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from common.rules_engine import load_rules, frame_is_bad, Debounce
from common.onnx_detector import Detector

p = argparse.ArgumentParser()
p.add_argument("--model", required=True)
p.add_argument("--source", required=True)
p.add_argument("--rules", default="m3/rules.yaml")
p.add_argument("--minutes", type=float, default=10)
a = p.parse_args()
R = load_rules(a.rules)
det = Detector(a.model, conf=R["confidence"])
isfile = not a.source.isdigit()
cap = cv2.VideoCapture(a.source if isfile else int(a.source))
if not cap.isOpened():
    sys.exit(f"cannot open {a.source}")
proc = psutil.Process()
psutil.cpu_percent(None)
deb = Debounce(R["debounce_frames"])
rows, errors, fires, total = [], 0, 0, 0
sec_frames, sec_lat, sec_err = 0, [], 0
t_start = t_sec = time.time()
rss0 = proc.memory_info().rss / 1e6
err_log = open("m5_soak_errors.txt", "w")
end = t_start + a.minutes * 60
while time.time() < end:
    try:
        ok, fr = cap.read()
        if not ok:
            if isfile:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            raise RuntimeError("camera read failed")
        t0 = time.perf_counter()
        dets = det(fr)
        sec_lat.append((time.perf_counter() - t0) * 1000)
        fires += deb.update(frame_is_bad([c for c, _, _ in dets], R)) == "FIRE"
        sec_frames += 1
        total += 1
    except Exception:
        errors += 1
        sec_err += 1
        err_log.write(f"{time.strftime('%H:%M:%S')}\n{traceback.format_exc()}\n")
        err_log.flush()
        time.sleep(0.1)
    now = time.time()
    if now - t_sec >= 1.0:
        rows.append([round(now - t_start, 1), sec_frames, round(sec_frames / (now - t_sec), 2),
                     round(statistics.median(sec_lat), 1) if sec_lat else "", psutil.cpu_percent(None),
                     round(proc.memory_info().rss / 1e6, 1), sec_err])
        sec_frames, sec_lat, sec_err, t_sec = 0, [], 0, now
        if len(rows) % 60 == 0:
            print(f"{rows[-1][0]:.0f}s frames={total} fps={rows[-1][2]} rss={rows[-1][5]}MB errors={errors}")
err_log.close()
with open("m5_soak_log.csv", "w", newline="") as f:
    csv.writer(f).writerows([["t_s", "frames", "fps", "latency_median_ms", "cpu_pct", "rss_mb", "errors"]] + rows)
fps = [r[2] for r in rows]
summ = {"duration_min": round((time.time() - t_start) / 60, 2), "frames": total, "errors": errors,
        "rule_fires": fires, "fps_mean": round(statistics.mean(fps), 2) if fps else None,
        "fps_min_1s": min(fps) if fps else None, "rss_start_mb": round(rss0, 1),
        "rss_end_mb": rows[-1][5] if rows else None, "rss_max_mb": max(r[5] for r in rows) if rows else None,
        "cpu_mean_pct": round(statistics.mean(r[4] for r in rows), 1) if rows else None,
        "source": a.source, "model": a.model}
json.dump(summ, open("m5_soak_summary.json", "w"), indent=1)
print(json.dumps(summ, indent=1))
