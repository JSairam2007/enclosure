"""M5: summarise a live session from the MQTT subscriber log (m4_mqtt_log.csv).
Usage: python m5/live_session_report.py --since "2026-11-13 12:46:00" [--source-frames-reset]
Prints a timeline of verdict changes and which classes were detected, in 5-second buckets.
"""
import argparse, csv, datetime as dt, json
from collections import Counter

p = argparse.ArgumentParser()
p.add_argument("--log", default="m4_mqtt_log.csv")
p.add_argument("--since", required=True)
a = p.parse_args()
t0 = dt.datetime.strptime(a.since, "%Y-%m-%d %H:%M:%S").timestamp()
rows = []
for r in csv.DictReader(open(a.log)):
    if r["topic"] != "edgeai/vision/status" or float(r["recv_ts"]) < t0:
        continue
    try:
        rows.append((float(r["recv_ts"]), json.loads(r["payload"])))
    except ValueError:
        continue
if not rows:
    raise SystemExit("no vision messages since that time (is the subscriber running?)")
print(f"messages: {len(rows)}  from {dt.datetime.fromtimestamp(rows[0][0]):%H:%M:%S} to {dt.datetime.fromtimestamp(rows[-1][0]):%H:%M:%S}")
print("\nverdict changes:")
last = None
for ts, m in rows:
    if m["verdict"] != last:
        print(f"  {dt.datetime.fromtimestamp(ts):%H:%M:%S}  {m['verdict']}")
        last = m["verdict"]
print("\n5-s buckets: verdicts | classes seen (count of messages containing them) | max conf")
bucket = None
for ts, m in rows + [(None, None)]:
    b = int(ts // 5) if ts else None
    if b != bucket and bucket is not None:
        cls = ", ".join(f"{k} x{v}" for k, v in seen.most_common()) or "nothing"
        conf = ", ".join(f"{k} {v:.2f}" for k, v in mx.items())
        print(f"  {dt.datetime.fromtimestamp(bucket * 5):%H:%M:%S}  {dict(ver)} | {cls} | {conf}")
    if ts is None:
        break
    if b != bucket:
        bucket, ver, seen, mx = b, Counter(), Counter(), {}
    ver[m["verdict"]] += 1
    for k in {d["cls"] for d in m["detections"]}:
        seen[k] += 1
    for d in m["detections"]:
        mx[d["cls"]] = max(mx.get(d["cls"], 0), d["conf"])
k = rows[-1][1].get("kpi", {})
print(f"\nlast KPIs: fps={k.get('fps')} latency_median_ms={k.get('latency_median_ms')} fail_share_pct={k.get('fail_share_pct')}")
