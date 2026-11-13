"""M5: headline-metric display. Reads ONLY result files produced by running the other scripts and
shows them in one place; anything not run yet shows 'not run yet' (never a made-up value).
Usage: python M5/headline.py          (the dashboard also shows this at /api/headline)
"""
import csv, json, os

NOT_RUN = None


def _json(path):
    try:
        return json.load(open(path))
    except (OSError, ValueError):
        return None


def _csv(path):
    try:
        return list(csv.DictReader(open(path)))
    except OSError:
        return None


def collect():
    h = {}
    m1 = _json("M1/results/m1_metrics.json")
    h["M1 test mAP@0.5 (PyTorch)"] = (m1 or {}).get("mAP50")
    m2 = _csv("M2/results/m2_results.csv")
    if m2:
        i8 = [r for r in m2 if r["model"].startswith("ONNX INT8") and r["provider"] == "CPUExecutionProvider"]
        if i8:
            h["M2 INT8 CPU median latency (ms)"] = i8[0]["median_ms"] or i8[0]["note"]
            h["M2 INT8 test mAP@0.5"] = i8[0]["mAP50"] or None
    m3 = _json("M3/results/m3_summary.json")
    if m3:
        h["M3 frame->actuator median (ms)"] = m3.get("latency_median_ms")
        h["M3 frame->actuator p95 (ms)"] = m3.get("latency_p95_ms")
        h["M3 events measured"] = m3.get("events")
    fa = _csv("M4/results/m4_false_alarms.csv")
    if fa:
        h["M4 false alarms (normal runs)"] = f"{sum(int(r['false_alarm_events']) for r in fa)} in {len(fa)} runs"
    ev = _json("M5/results/m5_eval_summary.json")
    if ev:
        h["M5 false-pass rate"] = ev.get("false_pass_rate")
        h["M5 parts evaluated"] = ev.get("parts")
    so = _json("M5/results/m5_soak_summary.json")
    if so:
        h["M5 soak duration (min)"] = so.get("duration_min")
        h["M5 soak mean FPS"] = so.get("fps_mean")
        h["M5 soak errors"] = so.get("errors")
    return h


if __name__ == "__main__":
    keys = ["M1 test mAP@0.5 (PyTorch)", "M2 INT8 test mAP@0.5", "M2 INT8 CPU median latency (ms)",
            "M3 frame->actuator median (ms)", "M3 frame->actuator p95 (ms)", "M3 events measured",
            "M4 false alarms (normal runs)", "M5 false-pass rate", "M5 parts evaluated",
            "M5 soak duration (min)", "M5 soak mean FPS", "M5 soak errors"]
    h = collect()
    w = max(map(len, keys))
    print("=" * (w + 22))
    for k in keys:
        v = h.get(k)
        print(f"{k:<{w}}  {'not run yet' if v in (None, '') else v}")
    print("=" * (w + 22))
    print("source files: M1/results/m1_metrics.json M2/results/m2_results.csv M3/results/m3_summary.json M4/results/m4_false_alarms.csv "
          "M5/results/m5_eval_summary.json M5/results/m5_soak_summary.json (in the folder you run from)")
