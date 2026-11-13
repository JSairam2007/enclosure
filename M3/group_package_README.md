# M3 — Decide and Act

**Project context:** Raspberry Pi 5 carton seal inspection (SEALED / OPEN).  
**Package type:** simulation/demo starter and evidence templates. Hardware actions and measured timing are not claimed.

This repository maps directly to the six M3 assessment criteria:
1. Decision rule sheet
2. Two-stream pipeline
3. Debounce
4. Actuator fires
5. Docker
6. End-to-end latency

## Important distinction
The supplied `carton_detector` project currently documents a USB webcam + OpenCV threshold/contour inspection flow. This M3 starter builds on that context. It does not assume an existing YOLO detector, PLC, relay wiring, or two physical cameras.

All actuator actions are dry-run console events. Latency output from the simulator is software simulation timing, not camera-to-physical-actuator latency.

## Run the software demo
```bash
python -m venv .venv
# Linux: source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
python 03_debounce/debounce_demo.py
python 04_actuator_fires/actuator_simulator.py --status OPEN
python 06_end_to_end_latency/latency_simulator.py --events 25
```

## Proof status
Every criterion has a README/evidence template. Replace demo outputs with genuine device captures and measurements before marking a criterion complete.
