"""M1 helper: PROPOSE YOLO boxes for the white printed case, then review them by eye.
The case is white (low saturation, high brightness) on darker floors, so a colour mask finds it.
Every proposal must be checked on the review sheets; fix or delete bad ones (labels are only as
good as that review - say so in docs/data_card.md).
Usage:
  python m1/autolabel.py propose --clip a --cls case_closed          # one object class per frame
  python m1/autolabel.py propose --clip d --two                      # case + lid: bigger blob = case_open
  python m1/autolabel.py sheet --clip a                              # review sheets -> review/a_*.jpg
  python m1/autolabel.py set --clip d --frame 000310 --boxes "1:x1,y1,x2,y2;2:x1,y1,x2,y2"   # manual fix (pixels)
  python m1/autolabel.py set --clip a --frame 000000 --boxes ""     # mark as negative (no object)
"""
import argparse, glob, os
import cv2, numpy as np

CLASSES = ["case_closed", "case_open", "lid"]
p = argparse.ArgumentParser()
p.add_argument("cmd", choices=["propose", "sheet", "set", "exclude"])
p.add_argument("--frames", nargs="*", default=[], help="exclude: frame numbers like 000370")
p.add_argument("--clip", required=True)
p.add_argument("--raw", default="dataset/raw")
p.add_argument("--cls", default="case_closed")
p.add_argument("--two", action="store_true")
p.add_argument("--s-max", type=int, default=45)
p.add_argument("--v-min", type=int, default=165)
p.add_argument("--v-margin", type=float, default=40, help="blob must be this much brighter than frame median V")
p.add_argument("--min-frac", type=float, default=0.0004, help="min blob area as fraction of image")
p.add_argument("--max-frac", type=float, default=0.35)
p.add_argument("--min-solidity", type=float, default=0.55)
p.add_argument("--frame"); p.add_argument("--boxes")
a = p.parse_args()
d = os.path.join(a.raw, a.clip)


def refine(im, box):
    """GrabCut around the bright face so the shaded sides of the case are included too."""
    H, W = im.shape[:2]
    x1, y1, x2, y2 = box
    mx, my = int((x2 - x1) * 0.35) + 4, int((y2 - y1) * 0.35) + 4
    r = (max(0, x1 - mx), max(0, y1 - my), min(W, x2 + mx) - max(0, x1 - mx), min(H, y2 + my) - max(0, y1 - my))
    mask = np.zeros((H, W), np.uint8)
    mask[r[1]:r[1] + r[3], r[0]:r[0] + r[2]] = cv2.GC_PR_BGD
    mask[y1:y2, x1:x2] = cv2.GC_PR_FGD
    try:
        cv2.grabCut(im, mask, None, np.zeros((1, 65)), np.zeros((1, 65)), 3, cv2.GC_INIT_WITH_MASK)
    except cv2.error:
        return box
    fg = ((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(fg)
    if n < 2:
        return box
    k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    x, y, w, h = st[k, :4]
    nb = (int(x), int(y), int(x + w), int(y + h))
    a0 = (x2 - x1) * (y2 - y1)
    return nb if a0 <= w * h <= 3.0 * a0 else box   # reject runaway grabcut


def blobs(im):
    hsv = cv2.cvtColor(cv2.GaussianBlur(im, (5, 5), 0), cv2.COLOR_BGR2HSV)
    v_thr = max(a.v_min, float(np.median(hsv[..., 2])) + a.v_margin)   # brighter than THIS frame's floor
    m = ((hsv[..., 1] <= a.s_max) & (hsv[..., 2] >= v_thr)).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    H, W = im.shape[:2]
    out = []
    for c in cs:
        ar = cv2.contourArea(c) / (H * W)
        x, y, w, h = cv2.boundingRect(c)
        solidity = cv2.contourArea(c) / max(1, w * h)
        if a.min_frac <= ar <= a.max_frac and solidity >= a.min_solidity and max(w, h) / max(1, min(w, h)) <= 4:
            out.append((ar, refine(im, (x, y, x + w, y + h))))
    return sorted(out, reverse=True)


def write(img, items):
    H, W = cv2.imread(img).shape[:2]
    with open(img[:-4] + ".txt", "w") as f:
        for c, (x1, y1, x2, y2) in items:
            f.write(f"{c} {(x1 + x2) / 2 / W:.6f} {(y1 + y2) / 2 / H:.6f} {(x2 - x1) / W:.6f} {(y2 - y1) / H:.6f}\n")


def read(img):
    H, W = cv2.imread(img).shape[:2]
    t = img[:-4] + ".txt"
    if not os.path.exists(t):
        return None
    out = []
    for ln in open(t):
        c, cx, cy, w, h = map(float, ln.split())
        out.append((int(c), (int((cx - w / 2) * W), int((cy - h / 2) * H), int((cx + w / 2) * W), int((cy + h / 2) * H))))
    return out


def has_window(im, box):
    """Lid = white part with a dark square window in its middle; the open case body has none."""
    x1, y1, x2, y2 = box
    w, h = x2 - x1, y2 - y1
    roi = cv2.cvtColor(im[y1 + h // 5:y2 - h // 5, x1 + w // 5:x2 - w // 5], cv2.COLOR_BGR2GRAY)
    if roi.size == 0:
        return False
    dark = roi < 0.5 * float(np.percentile(roi, 90))
    return 0.02 <= dark.mean() <= 0.45


imgs = sorted(glob.glob(os.path.join(d, "*.jpg")))
if a.cmd == "exclude":
    xd = os.path.join("dataset", "excluded", a.clip)
    os.makedirs(xd, exist_ok=True)
    for fr in a.frames:
        for ext in (".jpg", ".txt"):
            src = os.path.join(d, f"{a.clip}_{fr}{ext}")
            if os.path.exists(src):
                os.replace(src, os.path.join(xd, os.path.basename(src)))
    print(f"excluded {len(a.frames)} frames of {a.clip} -> {xd}")
elif a.cmd == "propose":
    for img in imgs:
        im = cv2.imread(img)
        b = blobs(im)
        if a.two:
            write(img, [(2 if has_window(im, bx) else 1, bx) for _, bx in b[:2]])
        else:
            write(img, [(CLASSES.index(a.cls), b[0][1])] if b else [])
    print(f"proposed labels for {len(imgs)} frames in {d}")
elif a.cmd == "set":
    img = os.path.join(d, f"{a.clip}_{a.frame}.jpg")
    items = []
    for part in filter(None, a.boxes.split(";")):
        c, xy = part.split(":")
        items.append((int(c), tuple(map(int, xy.split(",")))))
    write(img, items)
    print("set", img, items)
else:
    os.makedirs("review", exist_ok=True)
    tiles = []
    col = [(0, 200, 0), (0, 0, 255), (255, 0, 0)]
    for img in imgs:
        im = cv2.imread(img)
        for c, (x1, y1, x2, y2) in read(img) or []:
            cv2.rectangle(im, (x1, y1), (x2, y2), col[c], 4)
            cv2.putText(im, CLASSES[c], (x1, max(20, y1 - 8)), 0, 1.0, col[c], 3)
        s = 240 / max(im.shape[:2])
        im = cv2.resize(im, None, fx=s, fy=s)
        t = np.full((240, 240, 3), 255, np.uint8); t[:im.shape[0], :im.shape[1]] = im
        cv2.putText(t, img[-10:-4], (3, 234), 0, 0.5, (0, 0, 0), 1)
        tiles.append(t)
    for k in range(0, len(tiles), 20):
        g = tiles[k:k + 20] + [np.full((240, 240, 3), 255, np.uint8)] * (20 - len(tiles[k:k + 20]))
        cv2.imwrite(f"review/{a.clip}_{k // 20}.jpg", np.vstack([np.hstack(g[r:r + 5]) for r in range(0, 20, 5)]))
    print(f"review sheets for {a.clip} in review/")
