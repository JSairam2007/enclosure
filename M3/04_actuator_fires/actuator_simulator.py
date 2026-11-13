"""Safe console-only actuator event simulator."""
import argparse
from datetime import datetime, timezone

def emit(status):
    mapping = {
        "SEALED": "PASS_INDICATOR_ON",
        "OPEN": "REJECT_REQUEST",
        "CAMERA_ERROR": "FAIL_SAFE_LINE_STOP_REQUEST",
        "WAITING": "OUTPUTS_INACTIVE",
        "UNKNOWN": "OUTPUTS_INACTIVE_REVIEW_REQUIRED",
    }
    event = mapping[status]
    print(f"{datetime.now(timezone.utc).isoformat()} | DRY_RUN | {status} | {event}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--status", choices=["SEALED","OPEN","CAMERA_ERROR","WAITING","UNKNOWN"], required=True)
    emit(p.parse_args().status)
