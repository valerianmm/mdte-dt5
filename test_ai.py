# test_ai.py
import sys
from pathlib import Path
# ensure module folder is on path
sys.path.insert(0, str(Path(__file__).resolve().parent / "jupyter-notebook" / "data-collection" / "data" / "ai-model"))

from xgb_model import predict_fall
import numpy as np

dummy_signal = np.random.randn(200, 6)  # 200 timesteps, 6 features
print("Predicted class:", "Fall" if predict_fall(dummy_signal) == 1 else "Walk")
