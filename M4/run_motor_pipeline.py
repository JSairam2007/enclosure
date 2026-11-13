"""M4: one command for the whole motor-anomaly pipeline from phone (phyphox) recordings.
1. Drop phyphox CSV exports (zips) into M4/phone_raw/ named normal_1.zip ... normal_3.zip (training),
   normal_11.zip ... normal_15.zip (false-alarm test), fault_1.zip ... (fault check).
2. Run:  python M4/run_motor_pipeline.py
Steps: import -> sanity check -> train (normal 1-3 only) -> false alarms (normal 11-15) -> drift check
(normal 11-15 vs training) -> live-alert replay of each fault run. Every number printed comes from the files.
Stops with a clear message if a required run is missing. Existing M4/data files are kept (not overwritten).
"""
import glob, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.dirname(HERE))  # project root
PY = sys.executable
RAW = "M4/phone_raw"
os.makedirs(RAW, exist_ok=True)
os.makedirs("M4/data", exist_ok=True)


def run(args, check=True):
    print("\n$ python", " ".join(args))
    r = subprocess.run([PY, "-B", *args])
    if check and r.returncode != 0:
        sys.exit(f"step failed (exit {r.returncode}): {' '.join(args)}")
    return r.returncode


# 1. import every zip whose name is <label>_<run>.zip
found = {}
for z in sorted(glob.glob(os.path.join(RAW, "*.zip"))):
    m = re.fullmatch(r"(normal|fault)_(\d+)\.zip", os.path.basename(z).lower())
    if not m:
        print(f"skipping {z}: name must be normal_<n>.zip or fault_<n>.zip")
        continue
    label, n = m.group(1), int(m.group(2))
    found[(label, n)] = f"M4/data/{label}_{n}.csv"
    if os.path.exists(found[(label, n)]):
        print(f"already imported: {found[(label, n)]}")
    else:
        run(["M4/phyphox_import.py", "--zip", z, "--label", label, "--run", str(n)])

train = [found[("normal", n)] for n in (1, 2, 3) if ("normal", n) in found]
test = [found[("normal", n)] for n in range(11, 16) if ("normal", n) in found]
faults = [v for (lab, _), v in sorted(found.items()) if lab == "fault"]
missing = [f"normal_{n}.zip" for n in (1, 2, 3) if ("normal", n) not in found] + \
          [f"normal_{n}.zip" for n in range(11, 16) if ("normal", n) not in found]
if missing:
    sys.exit(f"\nmissing in {RAW}: {', '.join(missing)}\nRecord those runs (60 s each), export as CSV zip, and re-run.")

# 2-5
run(["M4/train_anomaly.py", "--files", *train, "--fault-files", *faults])
run(["M4/false_alarm_counter.py", "--files", *test])
run(["M4/drift_check.py", "--files", *test], check=False)  # exit 1 just means drift flagged
for f in faults:
    run(["M4/live_alert.py", "--replay", f])
print("\nDone. Results: M4/train_report.json, M4/results/m4_false_alarms.csv, M4/results/m4_drift.csv, M4/results/m4_alert_log.csv (last fault replay)")
print("Record the sensor (phone model, sample rate above) in M1/docs/data_card.md.")
