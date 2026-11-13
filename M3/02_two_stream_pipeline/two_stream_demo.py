"""Two independent synthetic streams; replace generators with camera/video readers."""
import argparse
import threading
import time

def stream_worker(name, duration, results):
    count = 0
    end = time.perf_counter() + duration
    while time.perf_counter() < end:
        # Placeholder frame-processing workload.
        _ = sum(range(1000))
        count += 1
    results[name] = count / duration

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--duration", type=int, default=5)
    args = p.parse_args()
    results = {}
    threads = [
        threading.Thread(target=stream_worker, args=("stream_1", args.duration, results)),
        threading.Thread(target=stream_worker, args=("stream_2", args.duration, results)),
    ]
    for t in threads: t.start()
    for t in threads: t.join()
    for name, fps in results.items():
        print(f"{name}: {fps:.2f} processed iterations/sec (synthetic demo, not camera FPS)")

if __name__ == "__main__":
    main()
