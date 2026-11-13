"""Draw the model's detections on every test-set image, next to the reviewed labels, for a visual check.
Usage: python M1/annotate_test.py [--model models/best_int8.onnx] [--conf 0.5]
Outputs: test_annotated/<image>.jpg (thick = prediction with conf, thin white = label) and
test_annotated/_sheet_<n>.jpg contact sheets (20 per sheet). Uses the same detector as M3/M5.
"""
import argparse, glob, os, sys
import cv2
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from common.onnx_detector import Detector

p = argparse.ArgumentParser()
p.add_argument("--model", default="models/best_int8.onnx")
p.add_argument("--images", default="dataset/images/test")
p.add_argument("--conf", type=float, default=0.5)
p.add_argument("--out", default="test_annotated")
a = p.parse_args()
os.makedirs(a.out, exist_ok=True)
det = Detector(a.model, conf=a.conf)
COL = {"case_closed": (0, 200, 0), "case_open": (0, 0, 255), "lid": (255, 120, 0)}
names = {i: n for i, n in det.names.items()}
tiles, summary = [], {"images": 0, "pred": {}, "label": {}}
for img in sorted(glob.glob(os.path.join(a.images, "*.jpg"))):
    im = cv2.imread(img)
    h, w = im.shape[:2]
    lab = img.replace("\\", "/").replace("/images/", "/labels/")[:-4] + ".txt"
    gt = []
    if os.path.exists(lab):
        for ln in open(lab):
            c, cx, cy, bw, bh = map(float, ln.split()[:5])
            gt.append(names.get(int(c), str(int(c))))
            x1, y1 = int((cx - bw / 2) * w), int((cy - bh / 2) * h)
            cv2.rectangle(im, (x1, y1), (int((cx + bw / 2) * w), int((cy + bh / 2) * h)), (255, 255, 255), 1)
    preds = det(im)
    for c, s, (x1, y1, x2, y2) in preds:
        col = COL.get(c, (0, 255, 255))
        cv2.rectangle(im, (x1, y1), (x2, y2), col, 4)
        cv2.putText(im, f"{c} {s:.2f}", (x1, max(22, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, col, 2)
    ok = sorted(gt) == sorted(c for c, _, _ in preds)
    cv2.putText(im, ("OK " if ok else "DIFF ") + os.path.basename(img), (8, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.9,
                (0, 255, 0) if ok else (0, 0, 255), 2)
    cv2.imwrite(os.path.join(a.out, os.path.basename(img)), im)
    s = 260 / max(h, w)
    t = np.full((260, 260, 3), 30, np.uint8)
    sm = cv2.resize(im, None, fx=s, fy=s)
    t[:sm.shape[0], :sm.shape[1]] = sm
    tiles.append(t)
    summary["images"] += 1
    summary.setdefault("class_set_match", 0)
    summary["class_set_match"] += ok
    for c, _, _ in preds:
        summary["pred"][c] = summary["pred"].get(c, 0) + 1
    for c in gt:
        summary["label"][c] = summary["label"].get(c, 0) + 1
for k in range(0, len(tiles), 20):
    g = tiles[k:k + 20] + [np.full((260, 260, 3), 30, np.uint8)] * (20 - len(tiles[k:k + 20]))
    cv2.imwrite(os.path.join(a.out, f"_sheet_{k // 20}.jpg"), np.vstack([np.hstack(g[r:r + 5]) for r in range(0, 20, 5)]))
print(summary)
print(f"images where predicted classes == labelled classes: {summary['class_set_match']} of {summary['images']}")
print(f"annotated images + contact sheets in {a.out}/")
