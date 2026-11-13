"""M1 step 2: split labelled frames BY VIDEO into train/val/test and write dataset/data.yaml.
Label each frame in YOLO format (one .txt next to each .jpg; LabelImg / CVAT / Roboflow export).
Usage: python M1/split_dataset.py --train a b --val c --test d --classes enclosure
(names = the folder names under dataset/raw). A video may appear in only one split.
"""
import argparse, os, shutil, glob, sys

p = argparse.ArgumentParser()
p.add_argument("--raw", default="dataset/raw")
p.add_argument("--train", nargs="+", required=True)
p.add_argument("--val", nargs="+", required=True)
p.add_argument("--test", nargs="+", required=True)
p.add_argument("--classes", nargs="+", default=["case_closed", "case_open", "lid"])  # ids 0,1,2
a = p.parse_args()
splits = {"train": a.train, "val": a.val, "test": a.test}
allv = [v for vs in splits.values() for v in vs]
if len(allv) != len(set(allv)):
    sys.exit("a video is in more than one split (leakage)")

for sp, vids in splits.items():
    os.makedirs(f"dataset/images/{sp}", exist_ok=True)
    os.makedirs(f"dataset/labels/{sp}", exist_ok=True)
    n = unlabeled = 0
    for v in vids:
        for img in glob.glob(os.path.join(a.raw, v, "*.jpg")):
            lab = img[:-4] + ".txt"
            if not os.path.exists(lab):
                unlabeled += 1
                continue
            shutil.copy(img, f"dataset/images/{sp}")
            shutil.copy(lab, f"dataset/labels/{sp}")
            n += 1
    print(f"{sp}: {n} labelled images copied, {unlabeled} skipped (no .txt label)")
with open("dataset/data.yaml", "w") as f:
    # absolute path: ultralytics resolves a relative 'path' against its own datasets_dir, not the cwd
    f.write(f"path: {os.path.abspath('dataset').replace(os.sep, '/')}\ntrain: images/train\nval: images/val\ntest: images/test\nnames:\n")
    for i, c in enumerate(a.classes):
        f.write(f"  {i}: {c}\n")
print("wrote dataset/data.yaml (compute your real train/val/test ratio from the counts above)")
