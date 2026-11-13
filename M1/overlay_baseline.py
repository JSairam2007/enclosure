"""M1 step 3: live overlay (boxes + count) and baseline speed log.
Usage:
  python M1/overlay_baseline.py --source clips/a.mp4                          # classical contour baseline
  python M1/overlay_baseline.py --source clips/a.mp4 --weights runs/detect/train/weights/best.pt
  python M1/overlay_baseline.py --source 0                                    # webcam
Keys: q quit, s save screenshot (M1/results/m1_screenshot.png). Writes M1/results/m1_baseline_log.csv and
M1/results/m1_baseline_summary.json. Every number comes from this run on this machine.
"""
import argparse, csv, json, statistics, time
import cv2, psutil

p = argparse.ArgumentParser()
p.add_argument("--source", default="0")
p.add_argument("--weights")
p.add_argument("--conf", type=float, default=0.5)
p.add_argument("--min-area", type=int, default=2000, help="contour baseline only")
p.add_argument("--max-frames", type=int, default=600)
p.add_argument("--headless", action="store_true")
a = p.parse_args()
src = int(a.source) if a.source.isdigit() else a.source
model = None
if a.weights:
    from ultralytics import YOLO
    model = YOLO(a.weights)


def detect(fr):
    if model is not None:
        r = model.predict(fr, conf=a.conf, verbose=False)[0]
        return [tuple(map(int, b)) for b in r.boxes.xyxy.tolist()]
    g = cv2.GaussianBlur(cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY), (5, 5), 0)
    _, th = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    cs, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = []
    for c in cs:
        if cv2.contourArea(c) > a.min_area:
            x, y, w, h = cv2.boundingRect(c)
            out.append((x, y, x + w, y + h))
    return out


def temp_c():
    try:
        for ents in psutil.sensors_temperatures().values():
            if ents:
                return ents[0].current
    except Exception:
        pass
    return None  # Windows usually exposes none: read it from HWiNFO/Core Temp and note it by hand


cap = cv2.VideoCapture(src)
if not cap.isOpened():
    raise SystemExit(f"cannot open source {a.source}")
psutil.cpu_percent(None)
rows, t_start, n = [], time.perf_counter(), 0
while n < a.max_frames:
    ok, fr = cap.read()
    if not ok:
        break
    t0 = time.perf_counter()
    boxes = detect(fr)
    ms = (time.perf_counter() - t0) * 1000
    cpu = psutil.cpu_percent(None)
    for x1, y1, x2, y2 in boxes:
        cv2.rectangle(fr, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.putText(fr, f"count={len(boxes)}  {1000 / ms if ms else 0:.1f} FPS  {ms:.1f} ms", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    rows.append([n, round(ms, 2), len(boxes), cpu, temp_c()])
    n += 1
    if not a.headless:
        cv2.imshow("M1 overlay", fr)
        k = cv2.waitKey(1) & 0xFF
        if k == ord("s"):
            cv2.imwrite("M1/results/m1_screenshot.png", fr)
            print("saved M1/results/m1_screenshot.png")
        if k == ord("q"):
            break
total = time.perf_counter() - t_start
with open("M1/results/m1_baseline_log.csv", "w", newline="") as f:
    csv.writer(f).writerows([["frame", "latency_ms", "count", "cpu_pct", "temp_c"]] + rows)
if rows:
    lat = sorted(r[1] for r in rows)
    s = {"method": "yolo" if model else "contour", "frames": n, "end_to_end_fps": round(n / total, 2),
         "latency_median_ms": statistics.median(lat), "latency_p95_ms": lat[max(0, int(.95 * len(lat)) - 1)],
         "cpu_mean_pct": round(statistics.mean(r[3] for r in rows), 1), "temp_last_c": rows[-1][4]}
    json.dump(s, open("M1/results/m1_baseline_summary.json", "w"), indent=1)
    print(json.dumps(s, indent=1))
