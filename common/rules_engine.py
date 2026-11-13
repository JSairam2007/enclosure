"""Shared by M3 and M5: rule loading, debounce, bad-frame decision, actuator."""
import time
import yaml


def load_rules(path):
    r = yaml.safe_load(open(path))
    for k in ("mode", "confidence", "debounce_frames", "camera_timeout_s", "safe_state"):
        if k not in r:
            raise SystemExit(f"{path}: missing key '{k}'")
    return r


def frame_is_bad(class_names, rules):
    """mode: defect_class | any_detection | missing_expected"""
    m = rules["mode"]
    if m == "defect_class":
        return any(n in rules.get("defect_classes", []) for n in class_names)
    if m == "any_detection":
        return len(class_names) > 0
    if m == "missing_expected":
        return rules["expected_class"] not in class_names
    raise SystemExit(f"unknown mode {m}")


class Debounce:
    """FIRE after N consecutive bad frames; RELEASE after N consecutive good frames."""
    def __init__(self, n):
        self.n, self.bad, self.good, self.active = n, 0, 0, False

    def update(self, bad):
        if bad:
            self.bad += 1; self.good = 0
        else:
            self.good += 1; self.bad = 0
        if not self.active and self.bad >= self.n:
            self.active = True
            return "FIRE"
        if self.active and self.good >= self.n:
            self.active = False
            return "RELEASE"
        return None


class Verdict:
    """Station verdict: FAIL (debounced bad) > NO PART (N frames in a row with no detection) > PASS.
    An empty station is not a pass: nothing was inspected. Set no_part: false in rules.yaml to disable."""
    def __init__(self, rules):
        self.deb = Debounce(rules["debounce_frames"])
        self.n = rules["debounce_frames"]
        self.no_part = rules.get("no_part", True)
        self.empty_run = 0

    def update(self, class_names, rules):
        """returns (verdict, debounce_event) ; debounce_event is FIRE / RELEASE / None for the actuator"""
        ev = self.deb.update(frame_is_bad(class_names, rules))
        self.empty_run = self.empty_run + 1 if not class_names else 0
        if self.deb.active:
            return "FAIL", ev
        if self.no_part and self.empty_run >= self.n:
            return "NO PART", ev
        return "PASS", ev


class Actuator:
    """Arduino relay/LED over serial ('1'/'0'); with no port it is an on-screen LED only."""
    def __init__(self, port=None):
        self.ser, self.state = None, "OFF"
        if port:
            import serial
            self.ser = serial.Serial(port, 9600, timeout=0.1)
            time.sleep(2)

    def set(self, on):
        self.state = "ON" if on else "OFF"
        if self.ser:
            self.ser.write(b"1" if on else b"0")
            self.ser.flush()
        return time.perf_counter()
