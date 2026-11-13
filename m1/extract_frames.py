"""M1 step 1: turn each of your own videos into frames to label.
Usage: python m1/extract_frames.py clips/a.mp4 clips/b.mp4 clips/c.mp4 clips/d.mp4 --every 10
Frames go to dataset/raw/<video_name>/ so the later split is done BY VIDEO (no leakage).
Record 4+ videos: different angle / light / background / distance.
"""
import argparse, os, cv2

p = argparse.ArgumentParser()
p.add_argument("videos", nargs="+")
p.add_argument("--out", default="dataset/raw")
p.add_argument("--every", type=int, default=10, help="keep every Nth frame")
a = p.parse_args()

for v in a.videos:
    stem = os.path.splitext(os.path.basename(v))[0]
    d = os.path.join(a.out, stem)
    os.makedirs(d, exist_ok=True)
    cap = cv2.VideoCapture(v)
    if not cap.isOpened():
        print(f"cannot open {v}")
        continue
    i = saved = 0
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        if i % a.every == 0:
            cv2.imwrite(os.path.join(d, f"{stem}_{i:06d}.jpg"), fr)
            saved += 1
        i += 1
    print(f"{v}: read {i} frames, saved {saved} -> {d}")
