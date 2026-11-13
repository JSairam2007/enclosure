"""M4: data-drift check. Compares features of NEW normal data with the training baseline stored in the
bundle (two-sample KS test per feature + standardised mean shift). Windows overlap, so p-values are
optimistic: treat the result as a flag, not proof.
Usage: python m4/drift_check.py --files m4/data/normal_20.csv
Exit code 0 = no drift flagged, 1 = drift flagged. Thresholds are arguments; justify yours.
Writes m4_drift.csv.
"""
import argparse, csv, sys
import numpy as np
from scipy.stats import ks_2samp
from anomaly_core import AnomalyScorer
from features import load_run, feature_matrix, FEATURE_NAMES

p = argparse.ArgumentParser()
p.add_argument("--files", nargs="+", required=True)
p.add_argument("--bundle", default="m4/anomaly.joblib")
p.add_argument("--alpha", type=float, default=0.01, help="per-feature KS p-value flag level")
p.add_argument("--max-flagged-frac", type=float, default=0.25, help="drift if more than this fraction is flagged")
a = p.parse_args()
sc = AnomalyScorer(a.bundle)
base = sc.b["F_train"]
new = np.vstack([feature_matrix(load_run(f)[1], sc.win, sc.hop, sc.fs) for f in a.files])
rows, flagged = [], 0
for i, name in enumerate(FEATURE_NAMES):
    ks = ks_2samp(base[:, i], new[:, i])
    sd = base[:, i].std() or 1.0
    shift = (new[:, i].mean() - base[:, i].mean()) / sd
    fl = bool(ks.pvalue < a.alpha)
    flagged += fl
    rows.append([name, round(float(ks.statistic), 4), f"{ks.pvalue:.3g}", round(float(shift), 3), int(fl)])
with open("m4_drift.csv", "w", newline="") as fh:
    csv.writer(fh).writerows([["feature", "ks_stat", "p_value", "mean_shift_in_train_std", "flagged"]] + rows)
frac = flagged / len(FEATURE_NAMES)
print(f"baseline windows={len(base)} new windows={len(new)} flagged={flagged}/{len(FEATURE_NAMES)} ({frac:.0%})")
drift = frac > a.max_flagged_frac
print("DRIFT FLAGGED - re-record normal data and retrain" if drift else "no drift flagged")
sys.exit(1 if drift else 0)
