"""Shared lean YOLOv8 ONNX detector (no ultralytics at runtime): letterbox -> onnxruntime -> decode -> NMS.
Why: ultralytics' predict() wrapper added ~2x overhead on this CPU, and each session grabbed every core,
so two streams fought each other. Here each stream gets an explicit thread budget.
Accepts .onnx (fast path) or .pt (falls back to ultralytics, for checks only).
"""
import ast, os
import cv2
import numpy as np


class Detector:
    def __init__(self, path, conf=0.5, iou=0.5, threads=0):
        self.conf, self.iou = conf, iou
        self.yolo = None
        if not path.endswith(".onnx"):
            from ultralytics import YOLO
            self.yolo = YOLO(path)
            self.names = self.yolo.names
            return
        import onnxruntime as ort
        so = ort.SessionOptions()
        if threads:
            so.intra_op_num_threads = threads
            so.inter_op_num_threads = 1
        so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self.s = ort.InferenceSession(path, so, providers=["CPUExecutionProvider"])
        self.inp = self.s.get_inputs()[0]
        self.size = self.inp.shape[2] if isinstance(self.inp.shape[2], int) else 640
        meta = self.s.get_modelmeta().custom_metadata_map
        self.names = ast.literal_eval(meta["names"]) if "names" in meta else {}

    def __call__(self, frame):
        """returns list of (class_name, conf, [x1,y1,x2,y2]) in frame pixels"""
        if self.yolo is not None:
            r = self.yolo.predict(frame, conf=self.conf, iou=self.iou, verbose=False)[0]
            return [(self.names[int(c)], float(s), [int(v) for v in b])
                    for c, s, b in zip(r.boxes.cls.tolist(), r.boxes.conf.tolist(), r.boxes.xyxy.tolist())]
        h, w = frame.shape[:2]
        r = min(self.size / h, self.size / w)
        nh, nw = round(h * r), round(w * r)
        top, left = (self.size - nh) // 2, (self.size - nw) // 2
        img = np.full((self.size, self.size, 3), 114, np.uint8)
        img[top:top + nh, left:left + nw] = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_LINEAR)
        x = img[:, :, ::-1].transpose(2, 0, 1)[None].astype(np.float32) / 255.0
        out = self.s.run(None, {self.inp.name: np.ascontiguousarray(x)})[0][0]  # (4+nc, N)
        scores = out[4:]
        cls = scores.argmax(0)
        conf = scores[cls, np.arange(scores.shape[1])]
        keep = conf >= self.conf
        if not keep.any():
            return []
        b, cls, conf = out[:4, keep].T, cls[keep], conf[keep]
        x1 = (b[:, 0] - b[:, 2] / 2 - left) / r
        y1 = (b[:, 1] - b[:, 3] / 2 - top) / r
        bw, bh = b[:, 2] / r, b[:, 3] / r
        idx = cv2.dnn.NMSBoxesBatched(np.stack([x1, y1, bw, bh], 1).tolist(), conf.tolist(), cls.tolist(),
                                      self.conf, self.iou)
        res = []
        for i in np.array(idx).flatten():
            res.append((self.names.get(int(cls[i]), str(cls[i])), float(conf[i]),
                        [int(max(0, x1[i])), int(max(0, y1[i])), int(min(w, x1[i] + bw[i])), int(min(h, y1[i] + bh[i]))]))
        return res


def threads_per_stream(n_streams):
    return max(1, (os.cpu_count() or 4) // max(1, n_streams))
