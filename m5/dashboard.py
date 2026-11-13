"""M5: Flask live dashboard - camera view with boxes, PASS/FAIL, detections, 3 KPIs, motor alert, headline metrics.
Usage:
  python m5/dashboard.py --model models/best_int8.onnx --source 0                 # webcam
  python m5/dashboard.py --model models/best_int8.onnx --source clips/c.mp4 --loop
Open http://127.0.0.1:5000  (binds to localhost only; use --host 0.0.0.0 to expose on the LAN, and read
the threat model first). KPIs are rolling over the last --window frames and computed live:
  FPS (end-to-end), median inference latency (ms), FAIL share (% of frames judged bad).
Motor alert comes from m4/motor_state.json (written by m4/live_alert.py); shown as 'no data' if missing/stale.
Writes m5/status.json twice a second (for m4/mqtt_publisher.py and the watchdog heartbeat).
"""
import argparse, collections, json, os, statistics, sys, threading, time
import cv2
from flask import Flask, Response, jsonify

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common.rules_engine import load_rules, frame_is_bad, Debounce, Actuator
import headline

p = argparse.ArgumentParser()
p.add_argument("--model", required=True)
p.add_argument("--source", default="0")
p.add_argument("--rules", default="m3/rules.yaml")
p.add_argument("--loop", action="store_true")
p.add_argument("--serial")
p.add_argument("--host", default="127.0.0.1")
p.add_argument("--port", type=int, default=5000)
p.add_argument("--window", type=int, default=100)
p.add_argument("--motor-state", default="m4/motor_state.json")
p.add_argument("--status-file", default="m5/status.json")
a = p.parse_args()

from common.onnx_detector import Detector
R = load_rules(a.rules)
det = Detector(a.model, conf=R["confidence"])
act = Actuator(a.serial)
lock = threading.Lock()
S = {"jpeg": None, "verdict": "STARTING", "detections": [], "frames": 0, "source_state": "starting"}
lat = collections.deque(maxlen=a.window)
tstamps = collections.deque(maxlen=a.window)
bads = collections.deque(maxlen=a.window)


def write_status():
    with lock:
        st = {k: v for k, v in S.items() if k != "jpeg"}
        st["kpi"] = kpis()
        st["ts"] = time.time()
    tmp = a.status_file + ".tmp"
    with open(tmp, "w") as f:
        json.dump(st, f)
    os.replace(tmp, a.status_file)


def kpis():
    fps = (len(tstamps) - 1) / (tstamps[-1] - tstamps[0]) if len(tstamps) > 1 and tstamps[-1] > tstamps[0] else None
    return {"fps": round(fps, 1) if fps else None,
            "latency_median_ms": round(statistics.median(lat), 1) if lat else None,
            "fail_share_pct": round(100 * sum(bads) / len(bads), 1) if bads else None,
            "window_frames": len(lat)}


def worker():
    isfile = not a.source.isdigit()
    cap = cv2.VideoCapture(a.source if isfile else int(a.source))
    deb, last_ok, last_status = Debounce(R["debounce_frames"]), time.time(), 0
    while True:
        ok, fr = cap.read()
        if not ok:
            if isfile and a.loop:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            if isfile:
                with lock:
                    S["verdict"], S["source_state"] = "END OF VIDEO", "ended"
                write_status()
                return
            if time.time() - last_ok > R["camera_timeout_s"]:
                act.set(R["safe_state"] == "ON")
                with lock:
                    S["verdict"], S["source_state"] = "CAMERA LOST - SAFE STATE", "lost"
                    S["jpeg"] = None
            time.sleep(0.05)
            if time.time() - last_status > 0.5:
                write_status(); last_status = time.time()
            continue
        last_ok = time.time()
        t0 = time.perf_counter()
        raw = det(fr)
        ms = (time.perf_counter() - t0) * 1000
        dets = [{"cls": c, "conf": round(s, 3), "box": b} for c, s, b in raw]
        bad = frame_is_bad([d["cls"] for d in dets], R)
        ev = deb.update(bad)
        if ev:
            act.set(ev == "FIRE")
        for d in dets:
            x1, y1, x2, y2 = d["box"]
            col = (0, 0, 255) if d["cls"] in R.get("defect_classes", []) else (0, 200, 0)
            cv2.rectangle(fr, (x1, y1), (x2, y2), col, 2)
            cv2.putText(fr, f"{d['cls']} {d['conf']:.2f}", (x1, max(15, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, col, 1)
        ok2, jpg = cv2.imencode(".jpg", fr, [cv2.IMWRITE_JPEG_QUALITY, 75])
        with lock:
            lat.append(ms); tstamps.append(time.time()); bads.append(1 if bad else 0)
            S.update(jpeg=jpg.tobytes() if ok2 else None, detections=dets, frames=S["frames"] + 1,
                     verdict="FAIL" if deb.active else "PASS", source_state="ok")
        if time.time() - last_status > 0.5:
            write_status(); last_status = time.time()


def motor():
    try:
        m = json.load(open(a.motor_state))
    except (OSError, ValueError):
        return {"state": "no data"}
    age = time.time() - m.get("ts", 0)
    if age > 5:
        return {"state": "stale", "age_s": round(age, 1)}
    return {"state": "ALERT" if m.get("alert") else "normal", "score": round(m["score"], 4),
            "threshold": round(m["threshold"], 4)}


app = Flask(__name__)


@app.route("/video")
def video():
    def gen():
        while True:
            with lock:
                j = S["jpeg"]
            if j:
                yield b"--f\r\nContent-Type: image/jpeg\r\n\r\n" + j + b"\r\n"
            time.sleep(0.04)
    return Response(gen(), mimetype="multipart/x-mixed-replace; boundary=f")


@app.route("/api/status")
def status():
    with lock:
        d = {"verdict": S["verdict"], "detections": S["detections"], "frames": S["frames"],
             "source_state": S["source_state"], "kpi": kpis()}
    d["motor"] = motor()
    return jsonify(d)


@app.route("/api/headline")
def api_headline():
    return jsonify(headline.collect())


@app.route("/")
def index():
    return PAGE


PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>Edge AI line monitor</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{--bg:#0f1115;--card:#181b22;--fg:#e8eaed;--mut:#9aa0a6;--ok:#1e8e3e;--bad:#d93025;--warn:#f29900}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.4 system-ui,Segoe UI,sans-serif}
main{display:grid;grid-template-columns:minmax(0,2fr) minmax(260px,1fr);gap:16px;padding:16px;max-width:1300px;margin:auto}
@media(max-width:800px){main{grid-template-columns:1fr}}
.card{background:var(--card);border-radius:10px;padding:14px}
img{width:100%;border-radius:8px;background:#000;min-height:200px}
#verdict{font-size:44px;font-weight:700;text-align:center;padding:18px;border-radius:10px;background:#333}
.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:12px}
.kpi b{display:block;font-size:26px}.kpi span{color:var(--mut);font-size:12px}
table{width:100%;border-collapse:collapse;font-size:13px}td{padding:4px 2px;border-bottom:1px solid #2a2e37}
h3{margin:4px 0 8px;font-size:13px;color:var(--mut);text-transform:uppercase;letter-spacing:.05em}
#motor{font-size:20px;font-weight:600}
</style></head><body><main>
<section><div class="card"><img src="/video" alt="live camera"></div>
<div class="kpis"><div class="card kpi"><b id="fps">-</b><span>FPS (rolling)</span></div>
<div class="card kpi"><b id="lat">-</b><span>median inference ms</span></div>
<div class="card kpi"><b id="fail">-</b><span>FAIL share % of frames</span></div></div></section>
<section><div id="verdict">-</div>
<div class="card" style="margin-top:12px"><h3>Motor (MPU6050)</h3><div id="motor">-</div></div>
<div class="card" style="margin-top:12px"><h3>Detections</h3><table id="dets"></table></div>
<div class="card" style="margin-top:12px"><h3>Headline metrics (from result files)</h3><table id="head"></table></div>
</section></main>
<script>
const $=id=>document.getElementById(id);
function row(t,a,b){const tr=document.createElement('tr');[a,b].forEach(x=>{const td=document.createElement('td');td.textContent=x;tr.appendChild(td)});t.appendChild(tr)}
async function tick(){try{const d=await (await fetch('/api/status')).json();
 const v=$('verdict');v.textContent=d.verdict;v.style.background=d.verdict==='PASS'?'var(--ok)':d.verdict==='FAIL'||d.verdict.startsWith('CAMERA')?'var(--bad)':'#333';
 $('fps').textContent=d.kpi.fps??'-';$('lat').textContent=d.kpi.latency_median_ms??'-';$('fail').textContent=d.kpi.fail_share_pct??'-';
 const m=d.motor;$('motor').textContent=m.state+(m.score!==undefined?`  score ${m.score} / thr ${m.threshold}`:'');
 $('motor').style.color=m.state==='ALERT'?'var(--bad)':m.state==='normal'?'#81c995':'var(--warn)';
 const t=$('dets');t.innerHTML='';if(!d.detections.length)row(t,'none','');d.detections.forEach(x=>row(t,x.cls,x.conf));
}catch(e){$('verdict').textContent='DASHBOARD OFFLINE'}}
async function head(){try{const h=await (await fetch('/api/headline')).json();const t=$('head');t.innerHTML='';
 const ks=Object.keys(h);if(!ks.length)row(t,'no result files yet','');ks.forEach(k=>row(t,k,h[k]===null?'not run yet':h[k]))}catch(e){}}
setInterval(tick,500);tick();setInterval(head,10000);head();
</script></body></html>"""

if __name__ == "__main__":
    threading.Thread(target=worker, daemon=True).start()
    print(f"dashboard on http://{a.host}:{a.port}")
    app.run(host=a.host, port=a.port, threaded=True, debug=False)
