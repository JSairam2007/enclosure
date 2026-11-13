"""M5: summarise m5_soak_log.csv by period - shows whether FPS or memory drift during the soak.
Usage: python m5/soak_report.py [--log m5_soak_log.csv]
"""
import argparse
import pandas as pd

p = argparse.ArgumentParser()
p.add_argument("--log", default="m5_soak_log.csv")
a = p.parse_args()
d = pd.read_csv(a.log)
d["latency_median_ms"] = pd.to_numeric(d["latency_median_ms"], errors="coerce")
end = d.t_s.max()
for name, s in [("first minute", d[d.t_s <= 60]), ("middle minute", d[(d.t_s > end / 2 - 30) & (d.t_s <= end / 2 + 30)]),
                ("last minute", d[d.t_s > end - 60])]:
    print(f"{name:13s} fps={s.fps.mean():.2f}  rss={s.rss_mb.mean():.1f} MB  latency={s.latency_median_ms.mean():.1f} ms  cpu={s.cpu_pct.mean():.0f}%")
w = d.loc[d.fps.idxmin()]
print(f"slowest second: t={w.t_s:.0f}s fps={w.fps:.2f}")
print(f"seconds below 6 FPS: {(d.fps < 6).sum()} of {len(d)}; total errors: {int(d.errors.sum())}")
