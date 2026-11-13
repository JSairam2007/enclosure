"""M5: run the station verdict logic (FAIL / NO PART / PASS) over a recorded clip and print the timeline.
Usage: python m5/verdict_check.py clips/a.mp4 [--model models/best_int8.onnx] [--every 1]
Same detector + rules as the dashboard, no web server. Prints each verdict change with its frame number.
"""
import argparse, os, sys
from collections import Counter
import cv2

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from common.rules_engine import load_rules, Verdict
from common.onnx_detector import Detector

p = argparse.ArgumentParser()
p.add_argument("video")
p.add_argument("--model", default="models/best_int8.onnx")
p.add_argument("--rules", default="m3/rules.yaml")
a = p.parse_args()
R = load_rules(a.rules)
det, v = Detector(a.model, conf=R["confidence"]), Verdict(R)
cap = cv2.VideoCapture(a.video)
n, last, count = 0, None, Counter()
while True:
    ok, fr = cap.read()
    if not ok:
        break
    verdict, _ = v.update([c for c, _, _ in det(fr)], R)
    count[verdict] += 1
    if verdict != last:
        print(f"frame {n:5d}  -> {verdict}")
        last = verdict
    n += 1
print(f"{a.video}: {n} frames  " + "  ".join(f"{k}={c}" for k, c in count.most_common()))
