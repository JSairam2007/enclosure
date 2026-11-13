"""M4 step 0: record labelled MPU6050 runs (Arduino serial) to CSV.
Usage: python m4/mpu_logger.py --port COM5 --label normal --run 1 --seconds 60
Plan: normal runs 1-3 = training; normal runs 11-15 = false-alarm test (never trained on);
fault runs 1-3 (tap the motor, add an unbalance weight, loosen a mount) = only for checking.
Output: m4/data/<label>_<run>.csv with columns t,ax,ay,az,gx,gy,gz,label
"""
import argparse, csv, os, time
import serial

p = argparse.ArgumentParser()
p.add_argument("--port", required=True)
p.add_argument("--label", choices=["normal", "fault"], required=True)
p.add_argument("--run", type=int, required=True)
p.add_argument("--seconds", type=float, default=60)
a = p.parse_args()
os.makedirs("m4/data", exist_ok=True)
path = f"m4/data/{a.label}_{a.run}.csv"
if os.path.exists(path):
    raise SystemExit(f"{path} exists - pick another --run number")
s = serial.Serial(a.port, 115200, timeout=1)
time.sleep(2)
s.reset_input_buffer()
t0, n, bad = time.time(), 0, 0
with open(path, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["t", "ax", "ay", "az", "gx", "gy", "gz", "label"])
    while time.time() - t0 < a.seconds:
        parts = s.readline().decode(errors="ignore").strip().split(",")
        if len(parts) != 6:
            bad += 1
            continue
        try:
            w.writerow([round(time.time() - t0, 4)] + [float(v) for v in parts] + [a.label])
            n += 1
        except ValueError:
            bad += 1
dur = time.time() - t0
print(f"saved {n} samples in {dur:.1f}s ({n / dur:.1f} Hz measured), {bad} bad lines -> {path}")
