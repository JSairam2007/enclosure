# Data card (M1) - filled from the project files (v2 model, 2026-11-13)

Blank template: [../data_card.md](../data_card.md). Every count below was computed from `dataset/` and `clips/`.

| Field | Value |
|---|---|
| Object / task | 3D-printed enclosure ("ir case") for an IR obstacle-sensor module; detect whether the case is closed, open, or the lid is loose |
| Classes | 0 `case_closed`, 1 `case_open` (case body without its lid, open side up or flipped), 2 `lid` (loose lid, square window) |
| Camera + resolution + fps | Phone camera, recorded via WhatsApp: a,d 576x768; b,c 768x576; e,f 576x1024; all ~30 fps |
| Videos recorded | a 18.9 s, b 15.9 s, c 17.7 s, d 20.9 s (2026-11-11); e 25.2 s (closed case, top-down), f 20.8 s (closed, then opened + lid) (2026-11-12) |
| Lighting / background / distances | Indoor room light; grey floor, dark desk, laptop surface; handheld, distances ~10-80 cm; some motion blur |
| Frames extracted per video | every 10th frame (`m1/extract_frames.py --every 10`) |
| Labelling tool + who labelled | Boxes proposed automatically (`m1/autolabel.py`: white-object colour mask + GrabCut; lid = dark square window), then every frame reviewed by eye on contact sheets; wrong/ambiguous frames moved to `dataset/excluded/` (not deleted) |
| Frames excluded in review | a 10, b 40, c 28, d 29, e 25, f 53 (hands covering the part, part cut off, boxes on monitor/floor, tiny far shots) |
| Split by video | train: a, b, d1 (clip d frames 0-300), e  -  val: d2 (370-480), d3 (530-610)  -  test: c, f |
| Images per split | train 119 (case_closed 104, case_open 14, lid 14, 1 empty)  -  val 18 (case_open 11, lid 16)  -  test 35 (case_closed 28, case_open 7, lid 7) |
| Known gaps / biases | Only one physical case; open-case/lid views come from clips d and f only (d split by time, not by video); val has no `case_closed`; handheld footage, no fixed station mount; top-down closed case on brown floor is still often missed at conf 0.5 (9 of 28 test boxes); no other objects/distractors labelled |
| Licence / privacy notes | Own recordings; videos show the author's hands and room - kept out of the public repository |
