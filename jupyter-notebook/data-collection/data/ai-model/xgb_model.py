# xgb_model.py
from pathlib import Path
import joblib
import numpy as np

# Find folder where this module lives and expect model files there
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "best_xgb_model.joblib"
SCALER_PATH = BASE_DIR / "scaler.joblib"

if not MODEL_PATH.exists() or not SCALER_PATH.exists():
    raise FileNotFoundError(
        f"Model or scaler not found.\nExpected:\n  {MODEL_PATH}\n  {SCALER_PATH}\n"
        "Save the joblib files into the same folder as this module or update the paths."
    )

model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)

# --- feature extraction (your existing functions) ---
from scipy.stats import skew, kurtosis, entropy
from scipy.signal import welch
import numpy as np
import math

def extract_features_signal(signal: np.ndarray, fs: int = 50) -> np.ndarray:
    sig = np.array(signal, dtype=float)
    sig = np.nan_to_num(sig, nan=0.0, posinf=0.0, neginf=0.0)
    if sig.ndim == 2 and sig.shape[0] > sig.shape[1]:
        sig = sig.T
    if sig.ndim == 1:
        sig = sig.reshape(1, -1)
    n_features = sig.shape[0]
    N = sig.shape[1] if sig.shape[1] > 0 else 1
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
    return np.array(feats).reshape(1, -1)

def predict_fall(signal: np.ndarray) -> int:
    if model is None or scaler is None:
        raise RuntimeError("Model or scaler not loaded.")
    features = extract_features_signal(signal)
    features_scaled = scaler.transform(features)
    pred = model.predict(features_scaled)[0]
    return int(pred)
