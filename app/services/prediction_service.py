"""
Prediction Service - ML + DL Model Integration
Supports three backends: rf | dl | ensemble (via MODEL_TYPE env var)
"""

import os
import joblib
import numpy as np
from pathlib import Path
from typing import Dict, Optional
from app.config import settings
from app.constants import CROPS, SEASONS, IRRIGATION_TYPES
from app.models.prediction import YieldRange
from app.utils.feature_engineering import prepare_features, encode_categorical
from app.utils.logger import logger

# ── Optional PyTorch import (DL model) ───────────────────────────────────────
try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not installed. DL model unavailable; RF will be used.")


# ══════════════════════════════════════════════════════════════════════════════
# DL Model Definition (must match train_dl.py)
# ══════════════════════════════════════════════════════════════════════════════

class YieldMLP(nn.Module):
    def __init__(self, input_dim, hidden_sizes, dropout_rates):
        super().__init__()
        layers = []
        in_dim = input_dim
        for h, d in zip(hidden_sizes, dropout_rates):
            layers += [nn.Linear(in_dim, h), nn.BatchNorm1d(h), nn.GELU(), nn.Dropout(d)]
            in_dim = h
        layers.append(nn.Linear(in_dim, 1))
        self.network = nn.Sequential(*layers)

    def forward(self, x):
        return self.network(x).squeeze(-1)


FEATURE_COLUMNS = [
    "nitrogen", "phosphorus", "potassium", "soil_ph", "soil_moisture",
    "avg_temperature", "total_rainfall", "humidity",
    "nutrient_index", "temperature_deviation", "stress_indicator",
    "crop_enc", "season_enc", "district_enc", "irrigation_enc",
]


# ══════════════════════════════════════════════════════════════════════════════
# SHARED ENCODING HELPER
# ══════════════════════════════════════════════════════════════════════════════

def _build_feature_vector(features: Dict) -> np.ndarray:
    """Encode categoricals and return the 15-feature vector (float32)."""
    fe = features.copy()
    fe["crop_type"]      = encode_categorical(features["crop_type"], CROPS)
    fe["season"]         = encode_categorical(features["season"], SEASONS)
    fe["district"]       = abs(hash(features.get("district", ""))) % 1000
    fe["irrigation_type"]= encode_categorical(features["irrigation_type"], IRRIGATION_TYPES)

    return np.array([
        fe["nitrogen"], fe["phosphorus"], fe["potassium"],
        fe["soil_ph"], fe["soil_moisture"],
        fe["avg_temperature"], fe["total_rainfall"], fe["humidity"],
        fe["nutrient_index"], fe["temperature_deviation"], fe["stress_indicator"],
        fe["crop_type"], fe["season"], fe["district"], fe["irrigation_type"],
    ], dtype=np.float32).reshape(1, -1)


# ══════════════════════════════════════════════════════════════════════════════
# RANDOM FOREST BACKEND
# ══════════════════════════════════════════════════════════════════════════════

class RFBackend:
    def __init__(self):
        self.model = None
        self.loaded = False
        model_path   = Path(settings.ml_model_path)
        encoders_path = Path(settings.ml_encoders_path)
        if model_path.exists() and encoders_path.exists():
            try:
                self.model = joblib.load(model_path)
                self.loaded = True
                logger.info("RF model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load RF model: {e}")

    def predict(self, features: Dict) -> Optional[float]:
        if not self.loaded:
            return None
        try:
            x = _build_feature_vector(features)
            return float(self.model.predict(x)[0])
        except Exception as e:
            logger.error(f"RF prediction error: {e}")
            return None


# ══════════════════════════════════════════════════════════════════════════════
# DEEP LEARNING BACKEND
# ══════════════════════════════════════════════════════════════════════════════

class DLBackend:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.loaded = False

        if not TORCH_AVAILABLE:
            return

        model_path  = Path(settings.dl_model_path)
        scaler_path = Path(settings.dl_scaler_path)

        if model_path.exists() and scaler_path.exists():
            try:
                checkpoint = torch.load(model_path, map_location="cpu", weights_only=False)
                cfg = checkpoint["config"]
                self.model = YieldMLP(
                    cfg["input_dim"], cfg["hidden_sizes"], cfg["dropout_rates"]
                )
                self.model.load_state_dict(checkpoint["model_state_dict"])
                self.model.eval()
                self.scaler = joblib.load(scaler_path)
                self.loaded = True
                logger.info("DL model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load DL model: {e}")
        else:
            logger.info("DL model files not found. Run python train_dl.py to train.")

    def predict(self, features: Dict) -> Optional[float]:
        if not self.loaded:
            return None
        try:
            x_raw   = _build_feature_vector(features)
            x_scaled = self.scaler.transform(x_raw).astype(np.float32)
            x_tensor = torch.tensor(x_scaled)
            with torch.no_grad():
                pred = self.model(x_tensor).item()
            return float(pred)
        except Exception as e:
            logger.error(f"DL prediction error: {e}")
            return None


# ══════════════════════════════════════════════════════════════════════════════
# PREDICTION SERVICE (unified)
# ══════════════════════════════════════════════════════════════════════════════

class PredictionService:
    """Unified yield prediction service. Backend selected by settings.model_type."""

    def __init__(self):
        self.rf = RFBackend()
        self.dl = DLBackend()
        mode = settings.model_type.lower()
        logger.info(f"PredictionService init: mode={mode}, RF={'✓' if self.rf.loaded else '✗'}, DL={'✓' if self.dl.loaded else '✗'}")

    def predict_yield(self, features: Dict) -> YieldRange:
        mode = settings.model_type.lower()

        if mode == "dl":
            pred = self.dl.predict(features)
            if pred is None:
                logger.warning("DL unavailable, falling back to RF")
                pred = self.rf.predict(features)
        elif mode == "ensemble" and self.rf.loaded and self.dl.loaded:
            rf_p = self.rf.predict(features)
            dl_p = self.dl.predict(features)
            pred = (rf_p + dl_p) / 2.0
        else:  # default: rf
            pred = self.rf.predict(features)

        if pred is None:
            pred = self._placeholder(features)

        return self._range(pred)

    def _placeholder(self, features: Dict) -> float:
        base = {"Wheat": 50.0, "Rice": 55.0, "Maize": 45.0, "Cotton": 25.0}
        crop = features.get("crop_type", "Wheat")
        b = base.get(crop, 50.0)
        ni = features.get("nutrient_index", 50)
        b *= 1.0 + (ni - 50) / 100
        b *= {"Low": 0.85, "Medium": 1.0, "High": 1.1}.get(features.get("rainfall_category", "Medium"), 1.0)
        b *= 0.9 if features.get("stress_indicator", 0) else 1.0
        b *= {"Canal": 1.05, "Borewell": 1.1, "Rainfed": 0.9}.get(features.get("irrigation_type", "Canal"), 1.0)
        return max(10.0, min(b, 100.0))

    def _range(self, expected: float) -> YieldRange:
        return YieldRange(
            lower=round(expected * 0.92, 2),
            expected=round(expected, 2),
            higher=round(expected * 1.08, 2),
        )

    async def predict(self, request_data: Dict) -> YieldRange:
        features   = prepare_features(request_data)
        yield_range = self.predict_yield(features)
        logger.info(
            f"Prediction [{settings.model_type.upper()}] "
            f"{request_data.get('crop_type')} @ {request_data.get('district')}: "
            f"{yield_range.expected} qtl/ha"
        )
        return yield_range


# Global instance
prediction_service = PredictionService()
