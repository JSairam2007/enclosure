# Live demonstration script

## Normal run
1. Show device and camera.
2. Present a known-good sealed carton.
3. Show detector output and PASS decision.
4. Show dashboard update and log entry.

## Injected fault
1. Present a known defective/open carton or approved test sample.
2. Show stable detection and debounce.
3. Show FAIL/reject request in safe demo mode.
4. Show dashboard alert and log entry.

## Questions to prepare for
- What are the model classes and confidence threshold?
- How did you prevent train/test leakage?
- What are median and p95 latency?
- What happens if the camera fails?
- What is the false-pass rate and how was it measured?
- Does the system work offline?
- How are updates rolled back?
