"""M4 alternative sensor: import a phone IMU run recorded with the phyphox app (instead of the MPU6050).
In phyphox use "Accelerometer" (raw, includes g - matches the MPU6050) and optionally "Gyroscope";
export as "CSV (Comma, decimal point)". You get a zip/folder with Accelerometer.csv (and Gyroscope.csv).
Usage:
  python M4/phyphox_import.py --acc path/Accelerometer.csv [--gyro path/Gyroscope.csv] --label normal --run 1
  python M4/phyphox_import.py --zip path/export.zip --label fault --run 1
Writes M4/data/<label>_<run>.csv with t,ax,ay,az (g) and gx,gy,gz (deg/s), same as M4/mpu_logger.py.
Gyro is interpolated onto the accelerometer timestamps; without --gyro the gyro columns are 0
(then train AND test on phone data only - never mix sensors in one model).
Record the sensor name in M1/docs/data_card.md (phone model, sample rate shown in the summary below).
"""
import argparse, io, os, zipfile
import numpy as np
import pandas as pd

G = 9.80665
p = argparse.ArgumentParser()
p.add_argument("--acc")
p.add_argument("--gyro")
p.add_argument("--zip")
p.add_argument("--label", choices=["normal", "fault"], required=True)
p.add_argument("--run", type=int, required=True)
p.add_argument("--trim-s", type=float, default=2.0, help="drop this many seconds at start and end (phone handling)")
a = p.parse_args()


def read(src):
    df = pd.read_csv(src)
    if df.shape[1] < 4:
        raise SystemExit(f"expected time + 3 axes, got columns {list(df.columns)}")
    return df.iloc[:, 0].to_numpy(float), df.iloc[:, 1:4].to_numpy(float), list(df.columns)


if a.zip:
    z = zipfile.ZipFile(a.zip)
    names = {os.path.basename(n).lower(): n for n in z.namelist()}
    if "accelerometer.csv" not in names:
        raise SystemExit(f"no Accelerometer.csv in zip; found {list(names)}")
    acc_src = io.BytesIO(z.read(names["accelerometer.csv"]))
    gyro_src = io.BytesIO(z.read(names["gyroscope.csv"])) if "gyroscope.csv" in names else None
else:
    if not a.acc:
        raise SystemExit("give --acc (and optionally --gyro) or --zip")
    acc_src, gyro_src = a.acc, a.gyro

t, acc, acols = read(acc_src)
if any("without g" in c.lower() or "linear" in c.lower() for c in acols):
    print("WARNING: this looks like 'Acceleration without g'. Use the raw 'Accelerometer' experiment to match the MPU6050.")
acc = acc / G
if gyro_src is not None:
    tg, gy, _ = read(gyro_src)
    gyro = np.column_stack([np.interp(t, tg, gy[:, i]) for i in range(3)]) * (180.0 / np.pi)
else:
    gyro = np.zeros_like(acc)
keep = (t >= t[0] + a.trim_s) & (t <= t[-1] - a.trim_s)
t, acc, gyro = t[keep] - t[keep][0], acc[keep], gyro[keep]
os.makedirs("M4/data", exist_ok=True)
out = f"M4/data/{a.label}_{a.run}.csv"
if os.path.exists(out):
    raise SystemExit(f"{out} exists - pick another --run")
df = pd.DataFrame({"t": np.round(t, 4), "ax": acc[:, 0], "ay": acc[:, 1], "az": acc[:, 2],
                   "gx": gyro[:, 0], "gy": gyro[:, 1], "gz": gyro[:, 2], "label": a.label})
df.to_csv(out, index=False)
fs = 1.0 / np.median(np.diff(t)) if len(t) > 1 else 0
print(f"saved {len(df)} samples, {t[-1]:.1f}s, {fs:.1f} Hz measured, gyro={'yes' if gyro_src is not None else 'no'} -> {out}")
print(f"mean |a| = {np.linalg.norm(acc, axis=1).mean():.3f} g (about 1.0 expected with raw accelerometer)")
