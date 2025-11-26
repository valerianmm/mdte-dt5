from collections import deque
from pathlib import Path
from typing import Iterable, Optional, Sequence, Tuple
import math

import joblib
import numpy as np
from scipy.signal import welch
from scipy.stats import entropy, kurtosis, skew

# Default sampling rate used during training
DEFAULT_FS = 50


def extract_features_signal(signal: np.ndarray, fs: int = DEFAULT_FS) -> np.ndarray:
    """
    Extract the same 6 handcrafted features used for training:
      C11, C12, C13 (magnitude sums) and C31, C32, C33 (axis correlations).
    Input may be (n_samples, n_features) or (n_features, n_samples).
    """
    sig = np.array(signal, dtype=float)
    sig = np.nan_to_num(sig, nan=0.0, posinf=0.0, neginf=0.0)

    # If shape is (n_samples, n_features), transpose to (n_features, n_samples)
    if sig.ndim == 2 and sig.shape[0] > sig.shape[1]:
        sig = sig.T
    if sig.ndim == 1:
        sig = sig.reshape(1, -1)

    n_features = sig.shape[0]
    N = sig.shape[1] if sig.shape[1] > 0 else 1

    # Ensure we always have three axes (acc_x, acc_y, acc_z)
    if n_features >= 3:
        ax, ay, az = sig[0, :], sig[1, :], sig[2, :]
    else:
        tmp = np.zeros((3, N))
        tmp[:n_features, :] = sig
        ax, ay, az = tmp[0, :], tmp[1, :], tmp[2, :]

    mag = np.sqrt(ax**2 + ay**2 + az**2) + 1e-12

    C11 = np.sum(np.abs(ax) + np.abs(az)) / N
    C12 = np.sum(mag)
    C13 = np.sum(np.sqrt(ax**2 + az**2))

    def safe_corr(a, b):
        if np.std(a) < 1e-12 or np.std(b) < 1e-12:
            return 0.0
        return float(np.corrcoef(a, b)[0, 1])

    C31 = safe_corr(ax, ay)
    C32 = safe_corr(ay, az)
    C33 = safe_corr(ax, az)

    feats = [C11, C12, C13, C31, C32, C33]
    return np.array(feats, dtype=float).reshape(1, -1)


def features_from_recordings(recordings: Sequence[np.ndarray], fs: int = DEFAULT_FS, verbose: bool = False) -> np.ndarray:
    """Batch version of extract_features_signal for a list of recordings."""
    feat_list = []
    for i, rec in enumerate(recordings):
        try:
            feat_list.append(extract_features_signal(rec, fs=fs).ravel())
        except Exception as exc:
            if verbose:
                print(f"Error extracting features for record {i}: {exc}")
            feat_list.append([0.0] * 6)
    return np.array(feat_list, dtype=float)


def load_model_artifacts(
    model_path: Optional[Path] = None,
    scaler_path: Optional[Path] = None,
    base_dir: Optional[Path] = None,
):
    """Load trained model and scaler; defaults to the joblib files in this folder."""
    base_dir = base_dir or Path(__file__).resolve().parent
    model_path = Path(model_path) if model_path else base_dir / "best_xgb_model.joblib"
    scaler_path = Path(scaler_path) if scaler_path else base_dir / "scaler.joblib"

    if not model_path.exists() or not scaler_path.exists():
        raise FileNotFoundError(
            f"Model or scaler not found.\nExpected:\n  {model_path}\n  {scaler_path}\n"
            "Save or mount the joblib files into this directory or pass explicit paths."
        )

    model = joblib.load(model_path)
    # Compatibility: ensure attributes missing in current runtime exist
    if isinstance(model, object):
        for attr, default in [
            ("use_label_encoder", False),
            ("gpu_id", None),
            ("predictor", None),
        ]:
            if not hasattr(model, attr):
                setattr(model, attr, default)
    scaler = joblib.load(scaler_path)
    return model, scaler


class SlidingWindowPredictor:
    """Maintain a fixed-size buffer and emit predictions once the window is full."""

    def __init__(self, model, scaler, fs: int = DEFAULT_FS, window_seconds: float = 2.0):
        self.model = model
        self.scaler = scaler
        self.fs = fs
        self.window_seconds = window_seconds
        self.window_samples = max(1, int(fs * window_seconds))
        self.buffer = deque(maxlen=self.window_samples)

    def add_sample(self, sample: Sequence[float]):
        if len(sample) < 3:
            raise ValueError("Sample must contain at least 3 axes (ax, ay, az).")
        self.buffer.append(np.array(sample, dtype=float))

    def add_samples(self, samples: Iterable[Sequence[float]]):
        for sample in samples:
            self.add_sample(sample)

    def ready(self) -> bool:
        return len(self.buffer) == self.window_samples

    def predict(self) -> Tuple[int, Optional[float]]:
        if not self.ready():
            raise RuntimeError("Not enough samples to predict yet.")

        window_arr = np.vstack(self.buffer)
        feats = extract_features_signal(window_arr, fs=self.fs)
        feats_scaled = self.scaler.transform(feats)
        pred = int(self.model.predict(feats_scaled)[0])
        proba = None
        if hasattr(self.model, "predict_proba"):
            proba = float(self.model.predict_proba(feats_scaled)[0, 1])
        return pred, proba
