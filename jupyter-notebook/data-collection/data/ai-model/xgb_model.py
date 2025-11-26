# xgb_model.py
from pathlib import Path
import sys

# Make sure the folder containing the model utilities is on sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from model_utils import extract_features_signal, load_model_artifacts  # noqa: E402

# Load persisted artifacts
model, scaler = load_model_artifacts(base_dir=BASE_DIR)


def predict_fall(signal) -> int:
    """Return 1 for fall, 0 for walk."""
    if model is None or scaler is None:
        raise RuntimeError("Model or scaler not loaded.")
    features = extract_features_signal(signal)
    features_scaled = scaler.transform(features)
    pred = model.predict(features_scaled)[0]
    return int(pred)
