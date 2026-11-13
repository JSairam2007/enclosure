"""M4 shared: load the trained bundle, score windows, debounce alerts."""
import joblib
import numpy as np
from features import window_features


class AnomalyScorer:
    """anomaly score = -IsolationForest.score_samples (higher = more abnormal). Alert if score > threshold."""
    def __init__(self, bundle_path):
        self.b = joblib.load(bundle_path)
        self.win, self.hop, self.fs, self.threshold = self.b["win"], self.b["hop"], self.b["fs"], self.b["threshold"]
        self.train_files = self.b.get("train_files", [])

    def score_matrix(self, F):
        return -self.b["model"].score_samples(self.b["scaler"].transform(F))

    def score_window(self, w):
        return float(self.score_matrix(np.array([window_features(w, self.fs)]))[0])


class AlertState:
    """ALERT after k consecutive windows over threshold; CLEAR after k consecutive windows under."""
    def __init__(self, threshold, k=2):
        self.thr, self.k, self.over, self.under, self.active = threshold, k, 0, 0, False

    def update(self, score):
        if score > self.thr:
            self.over += 1; self.under = 0
        else:
            self.under += 1; self.over = 0
        if not self.active and self.over >= self.k:
            self.active = True
            return "ALERT"
        if self.active and self.under >= self.k:
            self.active = False
            return "CLEAR"
        return None
