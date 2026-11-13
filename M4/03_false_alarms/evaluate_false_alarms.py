"""Evaluate false alerts on synthetic normal runs using the demo IsolationForest."""
import csv
from pathlib import Path
import joblib

model=joblib.load("02_anomaly_model/isolation_forest_SYNTHETIC.joblib")
data=Path("01_sensor_data/data")
for run in range(1,4):
    rows=[]
    with (data/f"normal_run{run}_SYNTHETIC.csv").open() as f:
        for r in csv.DictReader(f):
            rows.append([float(r[k]) for k in ("ax_g","ay_g","az_g","gx_dps","gy_dps","gz_dps")])
    alerts=int((model.predict(rows)==-1).sum())
    print(f"SYNTHETIC normal run {run}: {alerts} flagged samples / {len(rows)}")
print("Assessment requires 5 real normal runs; this demo has 3 synthetic runs.")
