"""Demonstrate a supervised child process restart after a simulated failure."""
import subprocess, sys, time

child = "import time; print('service started'); time.sleep(0.5); raise SystemExit(2)"
for attempt in range(1,3):
    print(f"Supervisor start attempt {attempt}")
    result=subprocess.run([sys.executable,"-c",child])
    print("Child exit code:",result.returncode)
    if result.returncode != 0 and attempt == 1:
        print("Simulated crash detected; restarting once...")
        time.sleep(0.2)
    else:
        print("Demo complete.")
