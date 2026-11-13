"""M2: export to ONNX, INT8 quantize, compare accuracy, fair CPU benchmark.
Write your accuracy/speed TARGET in M2/docs/m2_target.md BEFORE running this.
Usage:
  python M2/export_benchmark.py --weights runs/detect/train/weights/best.pt --data dataset/data.yaml
  python M2/export_benchmark.py --weights yolov8n.pt          # pipeline check only: no --data = no accuracy
Optional --calib dataset/images/val  -> static INT8 (calibrated on your own images); default is dynamic INT8.
Outputs: models/best.onnx, models/best_int8.onnx, M2/results/m2_results.csv, M2/results/m2_results.md
Method: batch 1, same random input for every model, --warmup runs discarded, then --runs timed runs.
A model that fails to load/run is reported as FAILED with the error (dynamic INT8 can be unsupported/slow on CPU).
"""
import argparse, csv, glob, os, shutil, statistics, time
import numpy as np

p = argparse.ArgumentParser()
p.add_argument("--weights", required=True)
p.add_argument("--data", help="data.yaml; enables accuracy on the test split")
p.add_argument("--calib", help="folder of images for static INT8 calibration")
p.add_argument("--imgsz", type=int, default=640)
p.add_argument("--warmup", type=int, default=20)
p.add_argument("--runs", type=int, default=100)
a = p.parse_args()

from ultralytics import YOLO
import onnxruntime as ort
os.makedirs("models", exist_ok=True)

pt = YOLO(a.weights)
exported = pt.export(format="onnx", imgsz=a.imgsz, opset=13, dynamic=False)  # >=13 needed for per-channel QDQ
fp32 = "models/best.onnx"
shutil.copy(exported, fp32)
int8 = "models/best_int8.onnx"

if a.calib:
    import cv2
    from onnxruntime.quantization import quantize_static, CalibrationDataReader, QuantType, QuantFormat
    in_name = ort.InferenceSession(fp32, providers=["CPUExecutionProvider"]).get_inputs()[0].name
    files = sorted(glob.glob(os.path.join(a.calib, "*.jpg")))[:100]
    if not files:
        raise SystemExit(f"no .jpg in {a.calib}")

    class Reader(CalibrationDataReader):
        def __init__(self): self.it = iter(files)
        def get_next(self):
            f = next(self.it, None)
            if f is None: return None
            im = cv2.resize(cv2.imread(f), (a.imgsz, a.imgsz))[:, :, ::-1].transpose(2, 0, 1)
            return {in_name: (im[None].astype(np.float32) / 255.0)}
    # Keep the YOLO Detect head (last /model.N/ block: box decode + concat) in FP32; quantizing it
    # destroys box coordinates (seen here as mAP 0). Everything before it is INT8.
    import re, onnx
    g = onnx.load(fp32).graph
    idx = [int(m.group(1)) for n in g.node for m in [re.match(r"/model\.(\d+)/", n.name)] if m]
    head = f"/model.{max(idx)}/" if idx else None
    excl = [n.name for n in g.node if head and n.name.startswith(head)]
    print(f"INT8: keeping {len(excl)} head nodes ({head}) in FP32")
    quantize_static(fp32, int8, Reader(), quant_format=QuantFormat.QDQ, per_channel=True,
                    activation_type=QuantType.QUInt8, weight_type=QuantType.QInt8, nodes_to_exclude=excl)
    qmethod = "static-QDQ, head FP32"
else:
    from onnxruntime.quantization import quantize_dynamic, QuantType
    quantize_dynamic(fp32, int8, weight_type=QuantType.QUInt8)
    qmethod = "dynamic"


def accuracy(path):
    if not a.data:
        return "", "", ""
    m = YOLO(path, task="detect").val(data=a.data, split="test", imgsz=a.imgsz, device="cpu", verbose=False)
    return round(float(m.box.map50), 4), round(float(m.box.mp), 4), round(float(m.box.mr), 4)


x = np.random.default_rng(0).random((1, 3, a.imgsz, a.imgsz), dtype=np.float32)


def bench(path, prov):
    s = ort.InferenceSession(path, providers=[prov])
    name = s.get_inputs()[0].name
    for _ in range(a.warmup):
        s.run(None, {name: x})
    t = []
    for _ in range(a.runs):
        t0 = time.perf_counter()
        s.run(None, {name: x})
        t.append((time.perf_counter() - t0) * 1000)
    t.sort()
    return round(statistics.median(t), 2), round(t[max(0, int(0.95 * len(t)) - 1)], 2)


avail = ort.get_available_providers()
rows = []
size = lambda f: round(os.path.getsize(f) / 1e6, 2)
rows.append(["PyTorch FP32", "torch", *accuracy(a.weights), "", "", "", size(a.weights), ""])
for label, path in [("ONNX FP32", fp32), (f"ONNX INT8 ({qmethod})", int8)]:
    try:
        acc = accuracy(path)
    except Exception as e:
        acc = ("FAILED", str(e)[:60], "")
    for prov in [pv for pv in ("CPUExecutionProvider", "DmlExecutionProvider", "CUDAExecutionProvider") if pv in avail]:
        try:
            med, p95 = bench(path, prov)
            rows.append([label, prov, *acc, med, p95, round(1000 / med, 1), size(path), ""])
        except Exception as e:
            rows.append([label, prov, *acc, "", "", "", size(path), "FAILED: " + str(e)[:80]])

hdr = ["model", "provider", "mAP50", "precision", "recall", "median_ms", "p95_ms", "fps", "size_MB", "note"]
with open("M2/results/m2_results.csv", "w", newline="") as f:
    csv.writer(f).writerows([hdr] + rows)
with open("M2/results/m2_results.md", "w") as f:
    f.write("| " + " | ".join(hdr) + " |\n|" + "---|" * len(hdr) + "\n")
    for r in rows:
        f.write("| " + " | ".join(map(str, r)) + " |\n")
print(open("M2/results/m2_results.md").read())
print("providers available:", avail)
