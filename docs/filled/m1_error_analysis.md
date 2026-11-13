# M1 - wrong detections (filled, v2 model on the test split c + f)

Blank template: [../m1_error_analysis.md](../m1_error_analysis.md). Source: `m1_errors.csv` (IoU 0.5, conf 0.25)
and `python m1/annotate_test.py` (conf 0.5). The brief asks for 10; the v2 model has fewer errors than that at
conf 0.25, so the list is completed with the misses seen at the dashboard threshold (conf 0.5).

| # | Image | Type | One-line reason |
|---|---|---|---|
| 1 | c_000360 | FP (case_closed 0.26) | Bright grey laptop edge at the frame border looks like a white case side |
| 2 | f_000100 | Duplicate class (case_closed 0.52 on the open case, plus case_open 0.73) | Open case seen from above: the white rim resembles a closed case; model unsure between the two classes |
| 3 | c_000000 | Miss at conf 0.5 | Closed case top-down on brown floor: only the lid face with window is visible, rare in training |
| 4 | c_000020 | Miss at conf 0.5 | Same top-down view; soft shadow on one side |
| 5 | c_000030 | Miss at conf 0.5 | Same top-down view, case near bottom edge of frame |
| 6 | c_000100 | Miss at conf 0.5 | Top-down, case large in frame (close distance) |
| 7 | c_000110 | Miss at conf 0.5 | Top-down, slight motion blur |
| 8 | c_000190 | Miss at conf 0.5 | Case small, near dark desk edge, low contrast |
| 9 | c_000200 | Miss at conf 0.5 | Side view in strong blur |
| 10 | c_000370 / c_000380 | Miss at conf 0.5 | Top-down on brown floor again (same failure mode as 3-7) |

Pattern: 8 of 10 are one failure mode - closed case seen straight from above on the brown floor of clip c.
Fix: more top-down closed-case footage on varied floors, or a lower confidence for `case_closed` only.
