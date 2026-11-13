@echo off
rem M5 Windows launcher used by the Task Scheduler task (edgeai_task.xml).
rem Edit the two SET lines, then test it by double-clicking before importing the task.
set PROJECT=C:\Users\J Sairam\OneDrive\Desktop\New folder\edgeai
set PY=%LOCALAPPDATA%\edgeai-venv\Scripts\python.exe
cd /d "%PROJECT%"
"%PY%" M4\watchdog.py --heartbeat M5\status.json --stale-s 20 --restart-on-clean-exit -- python M5\dashboard.py --model models\best_int8.onnx --source 0 >> M5/results/m5_autostart.log 2>&1
