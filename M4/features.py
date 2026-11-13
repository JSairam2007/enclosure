"""M4 shared: windowing + features for MPU6050 CSV runs (train, live, false-alarm, drift all use this)."""
import numpy as np
import pandas as pd

COLS = ["ax", "ay", "az", "gx", "gy", "gz"]
FEATURE_NAMES = [f"{c}_{s}" for c in COLS for s in ("mean", "std", "rms", "ptp")] + \
                ["mag_std", "mag_ptp", "mag_domfreq_hz", "mag_specsum"]


def load_run(path):
    df = pd.read_csv(path)
    return df["t"].to_numpy(dtype=float), df[COLS].to_numpy(dtype=float)


def estimate_fs(t):
    dt = np.diff(t)
    dt = dt[dt > 0]
    return float(1.0 / np.median(dt)) if dt.size else 100.0


def window_features(w, fs):
    """w: (n, 6) array -> feature list in FEATURE_NAMES order."""
    f = []
    for i in range(6):
        x = w[:, i]
        f += [x.mean(), x.std(), float(np.sqrt(np.mean(x ** 2))), float(np.ptp(x))]
    mag = np.linalg.norm(w[:, :3], axis=1)
    sp = np.abs(np.fft.rfft(mag - mag.mean()))
    freqs = np.fft.rfftfreq(len(mag), 1.0 / fs)
    f += [mag.std(), float(np.ptp(mag)), float(freqs[sp.argmax()]), float(sp.sum())]
    return f


def feature_matrix(x, win, hop, fs):
    rows = [window_features(x[i:i + win], fs) for i in range(0, len(x) - win + 1, hop)]
    return np.array(rows) if rows else np.empty((0, len(FEATURE_NAMES)))
