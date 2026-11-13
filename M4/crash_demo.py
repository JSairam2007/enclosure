"""M4: crash demo for the watchdog - crashes on its first two starts, then runs cleanly for 5 s.
Usage: python M4/watchdog.py --max-restarts 5 -- python M4/crash_demo.py
State is kept in M4/.crash_demo_count (delete it to repeat the demo).
"""
import os, sys, time

f = "M4/.crash_demo_count"
n = int(open(f).read()) if os.path.exists(f) else 0
open(f, "w").write(str(n + 1))
print(f"crash_demo start #{n + 1}")
time.sleep(2)
if n < 2:
    print("crash_demo: simulated crash (exit 3)")
    sys.exit(3)
time.sleep(3)
print("crash_demo: finished cleanly")
