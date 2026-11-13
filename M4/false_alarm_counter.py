"""M4 step 3: false-alarm counter over normal runs (record >=5 NEW normal runs, not the training ones).
Usage: python M4/false_alarm_counter.py --files M4/data/normal_11.csv M4/data/normal_12.csv ... normal_15.csv
Every alert here is a false alarm, because every run is normal. Writes M4/results/m4_false_alarms.csv.
Warns if a file was used for training (that result would not count).
"""
import argparse, csv
from anomaly_core import AnomalyScorer, AlertState
from features import load_run, feature_matrix

p = argparse.ArgumentParser()
p.add_argument("--files", nargs="+", required=True)
p.add_argument("--bundle", default="M4/anomaly.joblib")
p.add_argument("--k", type=int, default=2)
a = p.parse_args()
sc = AnomalyScorer(a.bundle)
if len(a.files) < 5:
    print(f"note: {len(a.files)} runs given; the brief asks for 5")
rows, tot_w, tot_e, tot_s = [], 0, 0, 0.0
for f in a.files:
    if f.replace("\\", "/") in sc.train_files:
        print(f"WARNING: {f} was used for training - not a valid false-alarm test")
    t, x = load_run(f)
    s = sc.score_matrix(feature_matrix(x, sc.win, sc.hop, sc.fs))
    st = AlertState(sc.threshold, a.k)
    events = sum(1 for v in s if st.update(v) == "ALERT")
    over = int((s > sc.threshold).sum())
    dur = float(t[-1] - t[0]) if len(t) > 1 else 0.0
    rows.append([f, round(dur, 1), len(s), over, events])
    tot_w += len(s); tot_e += events; tot_s += dur
    print(f"{f}: {dur:.1f}s windows={len(s)} over_threshold={over} false_alarm_events={events}")
with open("M4/results/m4_false_alarms.csv", "w", newline="") as fh:
    csv.writer(fh).writerows([["file", "duration_s", "windows", "windows_over_threshold", "false_alarm_events"]] + rows)
rate = f"{tot_e / (tot_s / 3600):.2f} per hour" if tot_s else "n/a"
print(f"TOTAL runs={len(rows)} duration={tot_s:.0f}s windows={tot_w} false_alarm_events={tot_e} ({rate})")
