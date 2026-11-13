# M1 - Data, baseline and first model

Turn my own videos of the "ir case" into a labelled dataset (split by video), measure a classical baseline,
train YOLOv8n on the CPU and evaluate it on held-out test videos. Run all commands from the repository root.

| Script | Does |
|---|---|
| `extract_frames.py` | every Nth frame of each clip -> `dataset/raw/<clip>/` |
| `autolabel.py` | propose boxes (colour mask + GrabCut), review sheets, manual fixes, exclude bad frames |
| `split_dataset.py` | copy labelled frames into train/val/test **by video**, write `dataset/data.yaml` |
| `overlay_baseline.py` | live boxes + count overlay, latency/FPS/CPU log (contour baseline or a YOLO model) |
| `train_eval.py` | train YOLOv8n (CPU), test-split metrics, list of wrong detections |
| `annotate_test.py` | draw predictions + labels on every test image for a visual check |

```bat
python M1\extract_frames.py clips\a.mp4 clips\b.mp4 clips\c.mp4 clips\d.mp4 clips\e.mp4 clips\f.mp4 --every 10
python M1\split_dataset.py --train a b d1 e --val d2 d3 --test c f
python M1\overlay_baseline.py --source clips\c.mp4
python M1\train_eval.py --epochs 50
python M1\annotate_test.py
```

## Results (`results/`)
| File | Content |
|---|---|
| `m1_metrics.json` | test mAP@0.5, precision, recall (v2 model) |
| `m1_metrics_v1.json` | the first model, before clips e/f were added |
| `m1_errors.csv` | test images with a false positive or a miss (IoU 0.5) |
| `m1_baseline_summary.json`, `m1_baseline_log.csv` | contour baseline speed log |

## Reports (`docs/`)
- `data_card.md` (blank template) / `data_card_filled.md` (clips, splits, counts, labelling method)
- `m1_error_analysis.md` (blank) / `m1_error_analysis_filled.md` (10 wrong detections with reasons)

Status: **done.** Optional: save a screenshot with the `s` key in `overlay_baseline.py` (`--weights runs\detect\train\weights\best.pt`).
