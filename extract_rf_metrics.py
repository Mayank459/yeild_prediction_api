"""
KhetBuddy — RF Metrics Extractor
==================================
Loads the trained Random Forest model + dataset and produces
models/rf_metrics.json in the same format as dl_metrics.json
so generate_comparison_report.py can compare them side by side.

Run AFTER training the RF model (python train.py) and
BEFORE generating the report.
"""

import os
import sys
import json
import time
import joblib
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent))

# ── Config ────────────────────────────────────────────────────────────────────
DATASET_PATH    = Path("datasets/05_complete_training_dataset.csv")
RF_MODEL_PATH   = Path("models/yield_model.pkl")
RF_METRICS_PATH = Path("models/rf_metrics.json")

FEATURE_COLUMNS = [
    "nitrogen", "phosphorus", "potassium", "soil_ph", "soil_moisture",
    "avg_temperature", "total_rainfall", "humidity",
    "nutrient_index", "temperature_deviation", "stress_indicator",
    "crop_enc", "season_enc", "district_enc", "irrigation_enc",
]
TARGET_COLUMN = "yield_qtl_ha"
RANDOM_SEED   = 42


def main():
    print("\n[RF] Extracting Random Forest metrics...")

    if not RF_MODEL_PATH.exists():
        print(f"[ERROR] RF model not found at {RF_MODEL_PATH}")
        print("  Run: python train.py first")
        sys.exit(1)

    if not DATASET_PATH.exists():
        print(f"[ERROR] Dataset not found at {DATASET_PATH}")
        sys.exit(1)

    # Load model + dataset
    model = joblib.load(RF_MODEL_PATH)
    df    = pd.read_csv(DATASET_PATH)

    missing = [c for c in FEATURE_COLUMNS + [TARGET_COLUMN] if c not in df.columns]
    if missing:
        print(f"[ERROR] Missing columns: {missing}")
        sys.exit(1)

    X = df[FEATURE_COLUMNS].values.astype(np.float32)
    y = df[TARGET_COLUMN].values.astype(np.float32)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_SEED
    )

    # Time a single predict call for fairness (RF doesn't need full retrain)
    t0 = time.time()
    y_train_pred = model.predict(X_train)
    y_test_pred  = model.predict(X_test)
    inference_time = time.time() - t0

    def metrics(y_true, y_pred):
        rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
        r2   = float(r2_score(y_true, y_pred))
        mae  = float(np.mean(np.abs(y_true - y_pred)))
        mape = float(np.mean(np.abs((y_true - y_pred) / np.maximum(y_true, 1))) * 100)
        return {"rmse": round(rmse,4), "r2": round(r2,4), "mae": round(mae,4), "mape": round(mape,4)}

    train_m = metrics(y_train, y_train_pred)
    test_m  = metrics(y_test,  y_test_pred)

    # Feature importances
    fi = dict(zip(FEATURE_COLUMNS, model.feature_importances_.tolist()))

    out = {
        "model": "RandomForest",
        "n_estimators": model.n_estimators,
        "inference_time_sec": round(inference_time, 4),
        "train": train_m,
        "test":  test_m,
        "test_y_pred":  y_test_pred.tolist(),
        "test_y_true":  y_test.tolist(),
        "train_y_pred": y_train_pred.tolist(),
        "train_y_true": y_train.tolist(),
        "feature_importances": fi,
    }

    with open(RF_METRICS_PATH, "w") as f:
        json.dump(out, f, indent=2)

    print(f"\n  Train -> RMSE={train_m['rmse']:.4f}  R2={train_m['r2']:.4f}  MAPE={train_m['mape']:.2f}%")
    print(f"  Test  -> RMSE={test_m['rmse']:.4f}  R2={test_m['r2']:.4f}  MAPE={test_m['mape']:.2f}%")
    print(f"\n[OK] RF metrics saved -> {RF_METRICS_PATH}")


if __name__ == "__main__":
    main()
