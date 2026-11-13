"""Generate software-only decision-to-dry-run-event timing samples."""
import argparse, csv, statistics, time
from pathlib import Path
from actuator_simulator import emit

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--events", type=int, default=25)
    p.add_argument("--output", default="06_end_to_end_latency/demo_latency.csv")
    args = p.parse_args()
    samples = []
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["event", "software_path_latency_ms", "measurement_scope"])
        for i in range(1, args.events + 1):
            start = time.perf_counter_ns()
            # Simulated decision + dry-run event. No physical actuator is connected.
            status = "OPEN" if i % 2 else "SEALED"
            _ = {"OPEN": "REJECT_REQUEST", "SEALED": "PASS_INDICATOR_ON"}[status]
            elapsed = (time.perf_counter_ns() - start) / 1e6
            samples.append(elapsed)
            writer.writerow([i, f"{elapsed:.6f}", "software simulation only"])
    ordered = sorted(samples)
    p95 = ordered[min(len(ordered)-1, int(0.95 * len(ordered)))]
    print(f"Events: {len(samples)}")
    print(f"Median software path: {statistics.median(samples):.6f} ms")
    print(f"P95 software path: {p95:.6f} ms")
    print(f"Saved: {out}")
    print("NOT camera-to-physical-actuator latency.")

if __name__ == "__main__":
    main()
