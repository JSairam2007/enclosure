"""M4 (optional): write PLC tags over Modbus TCP with pymodbus.
Tag map (agree this with whoever owns the PLC; document it in the threat model):
  coil 0            REJECT       1 = vision verdict FAIL
  coil 1            MOTOR_ALERT  1 = motor anomaly alert active
  holding reg 0     MOTOR_SCORE  anomaly score x 1000 (int, clipped 0..65535)
Usage (test against the simulator first: python M4/plc_sim.py):
  python M4/plc_write.py --host 127.0.0.1 --port 5020 --reject 1 --motor-alert 0 --score 0.123 --readback
"""
import argparse
from pymodbus.client import ModbusTcpClient

COIL_REJECT, COIL_MOTOR, REG_SCORE = 0, 1, 0


def _call(fn, *args, unit=1, **kw):
    # pymodbus renamed the unit kwarg across 3.x versions (slave -> device_id); try both.
    for name in ("device_id", "slave"):
        try:
            return fn(*args, **kw, **{name: unit})
        except TypeError:
            continue
    return fn(*args, **kw)


class PlcTags:
    def __init__(self, host, port=502, unit=1):
        self.c, self.unit = ModbusTcpClient(host, port=port, timeout=2), unit
        if not self.c.connect():
            raise ConnectionError(f"cannot reach Modbus server {host}:{port}")

    def write(self, reject=None, motor_alert=None, score=None):
        errs = []
        if reject is not None:
            errs.append(_call(self.c.write_coil, COIL_REJECT, bool(reject), unit=self.unit))
        if motor_alert is not None:
            errs.append(_call(self.c.write_coil, COIL_MOTOR, bool(motor_alert), unit=self.unit))
        if score is not None:
            errs.append(_call(self.c.write_register, REG_SCORE, max(0, min(65535, int(round(score * 1000)))), unit=self.unit))
        bad = [r for r in errs if r.isError()]
        if bad:
            raise IOError(f"Modbus write error: {bad[0]}")

    def read(self):
        co = _call(self.c.read_coils, COIL_REJECT, unit=self.unit, count=2)
        hr = _call(self.c.read_holding_registers, REG_SCORE, unit=self.unit, count=1)
        return {"reject": bool(co.bits[0]), "motor_alert": bool(co.bits[1]), "score_x1000": hr.registers[0]}

    def close(self):
        self.c.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=5020)
    p.add_argument("--reject", type=int, choices=[0, 1])
    p.add_argument("--motor-alert", type=int, choices=[0, 1])
    p.add_argument("--score", type=float)
    p.add_argument("--readback", action="store_true")
    a = p.parse_args()
    t = PlcTags(a.host, a.port)
    t.write(a.reject, a.motor_alert, a.score)
    print("written")
    if a.readback:
        print("readback:", t.read())
    t.close()
