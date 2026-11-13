"""M1 step 4-5: train YOLOv8n on CPU, evaluate on the held-out test videos, list error candidates.
Usage: python M1/train_eval.py --epochs 50
Writes M1/results/m1_metrics.json (mAP@0.5, precision, recall from the test split) and M1/results/m1_errors.csv
(every test image with a false positive or a miss at IoU 0.5). Pick 10 rows, open the image,
and write ONE reason each in M1/docs/m1_error_analysis.md. Confusion matrix PNG is in runs/detect/.
"""
import argparse, csv, glob, json, os
import yaml
from ultralytics import YOLO

p = argparse.ArgumentParser()
p.add_argument("--data", default="dataset/data.yaml")
p.add_argument("--epochs", type=int, default=50)
p.add_argument("--imgsz", type=int, default=640)
p.add_argument("--batch", type=int, default=8)
p.add_argument("--weights", help="skip training and evaluate these weights")
p.add_argument("--conf", type=float, default=0.25)
a = p.parse_args()

if a.weights:
    model = YOLO(a.weights)
else:
    YOLO("yolov8n.pt").train(data=a.data, epochs=a.epochs, imgsz=a.imgsz, batch=a.batch, device="cpu")
    model = YOLO(sorted(glob.glob("runs/detect/train*/weights/best.pt"), key=os.path.getmtime)[-1])

m = model.val(data=a.data, split="test", imgsz=a.imgsz, device="cpu", plots=True)
met = {"mAP50": float(m.box.map50), "precision": float(m.box.mp), "recall": float(m.box.mr)}
json.dump(met, open("M1/results/m1_metrics.json", "w"), indent=1)
print(met)


def iou(p_, q_):
    ix = max(0, min(p_[2], q_[2]) - max(p_[0], q_[0]))
    iy = max(0, min(p_[3], q_[3]) - max(p_[1], q_[1]))
    inter = ix * iy
    u = (p_[2] - p_[0]) * (p_[3] - p_[1]) + (q_[2] - q_[0]) * (q_[3] - q_[1]) - inter
    return inter / u if u else 0


cfg = yaml.safe_load(open(a.data))
root = cfg.get("path", ".")
imgs = sorted(glob.glob(os.path.join(root, cfg["test"], "*.jpg")))
rows = []
for img in imgs:
    img = img.replace("\\", "/")  # glob on Windows mixes / and \ ; normalise before swapping folders
    lab = img.replace("/images/", "/labels/")[:-4] + ".txt"
    if not os.path.exists(lab):
        raise SystemExit(f"label file missing for {img} (looked for {lab})")
    r = model.predict(img, conf=a.conf, verbose=False)[0]
    h, w = r.orig_shape
    gt = []
    if os.path.exists(lab):
        for ln in open(lab):
            c, cx, cy, bw, bh = ln.split()[:5]
            cx, cy, bw, bh = float(cx) * w, float(cy) * h, float(bw) * w, float(bh) * h
            gt.append((int(c), (cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2)))
    pr = list(zip(r.boxes.cls.tolist(), r.boxes.xyxy.tolist(), r.boxes.conf.tolist()))
    used, fp = set(), []
    for c, b, s in pr:
        hit = next((i for i, (gc, gb) in enumerate(gt) if i not in used and gc == int(c) and iou(b, gb) >= 0.5), None)
        if hit is None:
            fp.append(s)
        else:
            used.add(hit)
    miss = len(gt) - len(used)
    if fp or miss:
        rows.append([img, len(gt), len(pr), len(fp), miss, round(min(fp), 3) if fp else ""])
with open("M1/results/m1_errors.csv", "w", newline="") as f:
    csv.writer(f).writerows([["image", "gt_boxes", "pred_boxes", "false_positives", "misses", "lowest_fp_conf"]] + rows)
print(f"{len(rows)} of {len(imgs)} test images have errors -> M1/results/m1_errors.csv")
