# M5 auto-start after power cycle - test record

Method: full restart (Start-equivalent `shutdown /r`), normal user login, no manual action afterwards.
Mechanism: Windows Task Scheduler task "EdgeAI" (M5/autostart/edgeai_task.xml, logon trigger + 30 s delay)
-> start_edgeai.bat -> M4/watchdog.py -> M5/dashboard.py (webcam, models/best_int8.onnx).

| Evidence | Value (read from the system, 2026-11-13) |
|---|---|
| Windows last boot time | 2026-11-13 12:01:11 |
| Task "EdgeAI" last run time | 2026-11-13 12:02:12 |
| Watchdog log: child started | 2026-11-13 12:02:14 (pid 16796) |
| Dashboard /api/status at 12:04:19 | reachable, verdict=PASS, frames=414, source=ok |
| Manual steps needed after login | none |

Result: PASS - the dashboard came back by itself after a power cycle.
Not covered: the MQTT broker (not part of auto-start; started by hand), cold power-off with Fast Startup.
