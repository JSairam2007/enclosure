"""M4 step 1: train the anomaly model on NORMAL runs only (IsolationForest on windowed features).
Usage: python M4/train_anomaly.py --files M4/data/normal_1.csv M4/data/normal_2.csv M4/data/normal_3.csv
Threshold = the (100 - --alert-pct) percentile of the training-window scores; you choose how strict
it is and justify it. Fault runs are NEVER used for training: --fault-files are only scored afterwards
so you can see how the model reacts (computed, not assumed).
Outputs: M4/anomaly.joblib, M4/train_report.json
"""
import argparse, json
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from features import load_run, estimate_fs, feature_matrix, FEATURE_NAMES

p = argparse.ArgumentParser()
p.add_argument("--files", nargs="+", required=True)
p.add_argument("--fault-files", nargs="*", default=[])
p.add_argument("--win", type=int, default=100, help="samples per window")
p.add_argument("--hop", type=int, default=50)
p.add_argument("--alert-pct", type=float, default=1.0, help="%% of training windows allowed above threshold")
p.add_argument("--trees", type=int, default=200)
p.add_argument("--out", default="M4/anomaly.joblib")
a = p.parse_args()
if any("fault" in f.lower() for f in a.files):
    raise SystemExit("refusing: fault data must not be used for training")

runs = {f: load_run(f) for f in a.files}
fs = float(np.median([estimate_fs(t) for t, _ in runs.values()]))
F = np.vstack([feature_matrix(x, a.win, a.hop, fs) for _, x in runs.values()])
if len(F) < 20:
    raise SystemExit(f"only {len(F)} windows - record longer normal runs")
sc = StandardScaler().fit(F)
model = IsolationForest(n_estimators=a.trees, random_state=0).fit(sc.transform(F))
scores = -model.score_samples(sc.transform(F))
thr = float(np.percentile(scores, 100 - a.alert_pct))
joblib.dump({"model": model, "scaler": sc, "threshold": thr, "win": a.win, "hop": a.hop, "fs": fs,
             "feature_names": FEATURE_NAMES, "train_files": [f.replace("\\", "/") for f in a.files],
             "F_train": F}, a.out)
rep = {"train_files": a.files, "windows": int(len(F)), "fs_hz_measured": fs, "threshold": thr,
       "alert_pct": a.alert_pct, "fault_check": {}}
for f in a.fault_files:
    _, x = load_run(f)
    s = -model.score_samples(sc.transform(feature_matrix(x, a.win, a.hop, fs)))
    rep["fault_check"][f] = {"windows": int(len(s)), "frac_over_threshold": float((s > thr).mean()) if len(s) else None}
json.dump(rep, open("M4/train_report.json", "w"), indent=1)
print(json.dumps(rep, indent=1))
print("saved", a.out)
