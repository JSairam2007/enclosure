"""Shared: write a JSON state file atomically, robust to Windows file locks.
On Windows os.replace() fails with PermissionError while another process (the MQTT publisher reading the
file, OneDrive syncing it, an antivirus scan) holds the target open. Retry briefly; if it still fails,
return False instead of raising, so a busy reader can never kill the producer loop.
"""
import json, os, time


def write_json_atomic(path, obj, retries=10, delay_s=0.02):
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f)
    for _ in range(retries):
        try:
            os.replace(tmp, path)
            return True
        except PermissionError:
            time.sleep(delay_s)
    try:
        os.remove(tmp)
    except OSError:
        pass
    return False
