"""M5: pass/fail evaluation on 20 physical parts -> confusion matrix + false-pass rate.
Record one short clip per part (same fixed camera as the live demo) and fill M5/parts_manifest.csv:
  part_id,video,truth          truth = good | defect   (write truth down BEFORE running)
Usage: python M5/eval_parts.py --model models/best_int8.onnx --manifest M5/parts_manifest.csv
A part is predicted FAIL if the debounced rule (M3/rules.yaml) fires at any point in its clip.
'Positive' = defect. False-pass = a defective part judged PASS (the costly error).
Outputs: M5/results/m5_eval_parts.csv (per part), M5/results/m5_confusion.md, M5/results/m5_eval_summary.json
"""
import argparse, csv, json, os, sys
import cv2

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from common.rules_engine import load_rules, frame_is_bad, Debounce
from common.onnx_detector import Detector

p = argparse.ArgumentParser()
p.add_argument("--model", required=True)
p.add_argument("--manifest", default="M5/parts_manifest.csv")
p.add_argument("--rules", default="M3/rules.yaml")
p.add_argument("--expect", type=int, default=20)
a = p.parse_args()
R = load_rules(a.rules)
det = Detector(a.model, conf=R["confidence"])
parts = [r for r in csv.DictReader(open(a.manifest)) if r.get("video") and r.get("truth")]
if not parts:
    sys.exit(f"{a.manifest} has no rows with video + truth filled in")
if len(parts) != a.expect:
    print(f"note: {len(parts)} parts filled in, brief asks for {a.expect}")
rows = []
for r in parts:
    truth = r["truth"].strip().lower()
    if truth not in ("good", "defect"):
        sys.exit(f"{r['part_id']}: truth must be good or defect, got {truth!r}")
    cap = cv2.VideoCapture(r["video"])
    if not cap.isOpened():
        sys.exit(f"cannot open {r['video']}")
    deb, n, nbad, fired = Debounce(R["debounce_frames"]), 0, 0, False
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        bad = frame_is_bad([c for c, _, _ in det(fr)], R)
        nbad += bad
        fired |= deb.update(bad) == "FIRE"
        n += 1
    pred = "defect" if fired else "good"
    rows.append([r["part_id"], r["video"], truth, "FAIL" if fired else "PASS", n, nbad, "ok" if pred == truth else "WRONG"])
    print(f"{r['part_id']}: truth={truth:6s} verdict={'FAIL' if fired else 'PASS'}  frames={n} bad_frames={nbad}")

TP = sum(1 for x in rows if x[2] == "defect" and x[3] == "FAIL")
FN = sum(1 for x in rows if x[2] == "defect" and x[3] == "PASS")
FP = sum(1 for x in rows if x[2] == "good" and x[3] == "FAIL")
TN = sum(1 for x in rows if x[2] == "good" and x[3] == "PASS")
div = lambda x, y: round(x / y, 4) if y else None
summ = {"parts": len(rows), "TP_defect_failed": TP, "FN_defect_passed": FN, "FP_good_failed": FP, "TN_good_passed": TN,
        "false_pass_rate": div(FN, TP + FN), "false_fail_rate": div(FP, FP + TN), "accuracy": div(TP + TN, len(rows)),
        "rules": a.rules, "model": a.model}
with open("M5/results/m5_eval_parts.csv", "w", newline="") as f:
    csv.writer(f).writerows([["part_id", "video", "truth", "verdict", "frames", "bad_frames", "result"]] + rows)
json.dump(summ, open("M5/results/m5_eval_summary.json", "w"), indent=1)
with open("M5/results/m5_confusion.md", "w") as f:
    f.write("| truth \\ verdict | FAIL | PASS |\n|---|---|---|\n")
    f.write(f"| defect | {TP} | {FN} (false pass) |\n| good | {FP} (false fail) | {TN} |\n\n")
    f.write(f"false-pass rate = {summ['false_pass_rate']}  false-fail rate = {summ['false_fail_rate']}  "
            f"accuracy = {summ['accuracy']}  (n = {len(rows)})\n")
print(open("M5/results/m5_confusion.md").read())
if TP + FN == 0:
    print("note: no defective parts in the manifest, so false-pass rate cannot be computed")
