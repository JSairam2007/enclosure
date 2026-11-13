"""M4: tiny Modbus TCP PLC simulator for testing plc_write.py without a real PLC.
Supports function codes 1 (read coils), 3 (read holding regs), 5 (write coil), 6 (write register).
Prints every tag change. Usage: python m4/plc_sim.py [--port 5020]   (Ctrl-C to stop)
Pure standard library, so it does not depend on the pymodbus server API.
"""
import argparse, socketserver, struct, threading, time

p = argparse.ArgumentParser()
p.add_argument("--host", default="127.0.0.1")
p.add_argument("--port", type=int, default=5020)
a = p.parse_args()
coils, regs, lock = [False] * 64, [0] * 64, threading.Lock()
NAMES = {("coil", 0): "REJECT", ("coil", 1): "MOTOR_ALERT", ("reg", 0): "MOTOR_SCORE_x1000"}


def recv_exact(sock, n):
    b = b""
    while len(b) < n:
        chunk = sock.recv(n - len(b))
        if not chunk:
            raise ConnectionError
        b += chunk
    return b


class H(socketserver.BaseRequestHandler):
    def handle(self):
        s = self.request
        try:
            while True:
                tid, pid, ln, unit = struct.unpack(">HHHB", recv_exact(s, 7))
                pdu = recv_exact(s, ln - 1)
                fc = pdu[0]
                with lock:
                    resp = self.process(fc, pdu)
                s.sendall(struct.pack(">HHHB", tid, pid, len(resp) + 1, unit) + resp)
        except (ConnectionError, OSError):
            return

    def process(self, fc, pdu):
        if fc in (1, 3):
            addr, cnt = struct.unpack(">HH", pdu[1:5])
            if addr + cnt > 64:
                return bytes([fc | 0x80, 2])
            if fc == 1:
                out = bytearray((cnt + 7) // 8)
                for i in range(cnt):
                    if coils[addr + i]:
                        out[i // 8] |= 1 << (i % 8)
                return bytes([fc, len(out)]) + bytes(out)
            return bytes([fc, cnt * 2]) + b"".join(struct.pack(">H", regs[addr + i]) for i in range(cnt))
        if fc in (5, 6):
            addr, val = struct.unpack(">HH", pdu[1:5])
            if addr >= 64:
                return bytes([fc | 0x80, 2])
            kind = "coil" if fc == 5 else "reg"
            new = (val == 0xFF00) if fc == 5 else val
            store = coils if fc == 5 else regs
            if store[addr] != new:
                print(f"{time.strftime('%H:%M:%S')} {kind} {addr} {NAMES.get((kind, addr), '')} -> {int(new)}")
            store[addr] = new
            return pdu[:5]  # echo
        return bytes([fc | 0x80, 1])  # illegal function


socketserver.ThreadingTCPServer.allow_reuse_address = True
srv = socketserver.ThreadingTCPServer((a.host, a.port), H)
print(f"PLC simulator on {a.host}:{a.port} (coil0 REJECT, coil1 MOTOR_ALERT, reg0 MOTOR_SCORE_x1000)")
try:
    srv.serve_forever()
except KeyboardInterrupt:
    srv.shutdown()
