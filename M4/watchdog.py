"""M4: watchdog - runs a command and restarts it when it crashes (or when its heartbeat file goes stale).
Usage:
  python M4/watchdog.py -- python M5/dashboard.py --model models/best_int8.onnx --source 0
  python M4/watchdog.py --max-restarts 3 -- python M4/crash_demo.py        # see it restart
  python M4/watchdog.py --heartbeat M5/status.json --stale-s 10 -- python M5/dashboard.py ...
Backoff doubles after each quick crash (1,2,4..30 s) and resets after --stable-s of uptime.
Every start/exit/restart is logged to M4/results/m4_watchdog_log.csv with exit code and uptime.
"""
import argparse, csv, os, subprocess, sys, time

p = argparse.ArgumentParser()
p.add_argument("--max-restarts", type=int, default=0, help="0 = unlimited")
p.add_argument("--heartbeat", help="file the child must keep updating (mtime)")
p.add_argument("--stale-s", type=float, default=15)
p.add_argument("--stable-s", type=float, default=60)
p.add_argument("--restart-on-clean-exit", action="store_true")
p.add_argument("--log", default="M4/results/m4_watchdog_log.csv")
p.add_argument("cmd", nargs=argparse.REMAINDER)
a = p.parse_args()
cmd = a.cmd[1:] if a.cmd and a.cmd[0] == "--" else a.cmd
if not cmd:
    sys.exit("give the command after --")
if cmd[0] == "python":
    cmd[0] = sys.executable

new = not os.path.exists(a.log)
logf = open(a.log, "a", newline="")
log = csv.writer(logf)
if new:
    log.writerow(["time", "event", "pid", "exit_code", "uptime_s", "restarts"])


def L(ev, pid="", rc="", up=""):
    log.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), ev, pid, rc, up, restarts])
    logf.flush()
    print(f"[watchdog] {ev} pid={pid} rc={rc} uptime={up}s restarts={restarts}")


restarts, backoff = 0, 1.0
try:
    while True:
        t0 = time.time()
        child = subprocess.Popen(cmd)
        L("start", child.pid)
        reason = None
        while child.poll() is None:
            time.sleep(1)
            if a.heartbeat and time.time() - t0 > a.stale_s:
                hb = os.path.getmtime(a.heartbeat) if os.path.exists(a.heartbeat) else 0
                if time.time() - hb > a.stale_s:
                    reason = "heartbeat_stale"
                    child.kill()
                    child.wait()
                    break
        up = round(time.time() - t0, 1)
        rc = child.returncode
        L(reason or ("exit_clean" if rc == 0 else "crash"), child.pid, rc, up)
        if rc == 0 and not reason and not a.restart_on_clean_exit:
            break
        if a.max_restarts and restarts >= a.max_restarts:
            L("giving_up")
            break
        backoff = 1.0 if up >= a.stable_s else min(backoff * 2, 30.0)
        time.sleep(backoff)
        restarts += 1
        L("restart")
except KeyboardInterrupt:
    if child.poll() is None:
        child.terminate()
        try:
            child.wait(5)
        except subprocess.TimeoutExpired:
            child.kill()
    L("stopped_by_user", child.pid)
