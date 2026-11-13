"""Generate synthetic MPU6050-shaped example CSVs; NOT physical sensor readings."""
import csv, math, random
from pathlib import Path

OUT = Path("01_sensor_data/data")
OUT.mkdir(parents=True, exist_ok=True)
random.seed(7)

def generate(label, run, fault=False):
    path = OUT / f"{label}_run{run}_SYNTHETIC.csv"
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["timestamp_s","ax_g","ay_g","az_g","gx_dps","gy_dps","gz_dps","label","source"])
        for i in range(500):
            t=i*0.01
            noise=lambda: random.gauss(0,0.015)
            ax=0.02*math.sin(t)+noise()
            ay=0.02*math.cos(t)+noise()
            az=1.0+noise()
            gx,gy,gz=noise(),noise(),noise()
            if fault and 200 <= i < 300:
                ax += 0.8
                gy += 35
            w.writerow([f"{t:.3f}",f"{ax:.5f}",f"{ay:.5f}",f"{az:.5f}",
                        f"{gx:.5f}",f"{gy:.5f}",f"{gz:.5f}",label,"SYNTHETIC_NOT_MPU6050"])
    print(path)

for n in range(1,4):
    generate("normal", n, False)
    generate("fault", n, True)
