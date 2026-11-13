"""Synthetic-data-only anomaly detection demonstration."""
from pathlib import Path
import csv
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report
import joblib

def load(path):
    rows=[]
    with path.open() as f:
        for r in csv.DictReader(f):
            rows.append([float(r[k]) for k in ("ax_g","ay_g","az_g","gx_dps","gy_dps","gz_dps")])
    return np.asarray(rows)

data=Path("01_sensor_data/data")
normal=np.vstack([load(data/f"normal_run{i}_SYNTHETIC.csv") for i in range(1,4)])
fault=np.vstack([load(data/f"fault_run{i}_SYNTHETIC.csv") for i in range(1,4)])
model=IsolationForest(contamination=0.05, random_state=42)
model.fit(normal)
X=np.vstack([normal, fault])
y_true=np.array([0]*len(normal)+[1]*len(fault))
y_pred=(model.predict(X)==-1).astype(int)
print(classification_report(y_true,y_pred,target_names=["normal","fault"]))
Path("02_anomaly_model").mkdir(exist_ok=True)
joblib.dump(model,"02_anomaly_model/isolation_forest_SYNTHETIC.joblib")
print("Saved synthetic demo model; not a validated production anomaly model.")
