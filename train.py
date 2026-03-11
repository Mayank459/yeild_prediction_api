"""
KhetBuddy — ML Training Script
================================
Data sources:
  1. apy.csv  → District-wise season-wise crop production statistics
                (India Agriculture Production dataset, data.gov.in)
                Place the file at: D:/Downloads/apy.csv
                OR set env var: APY_CSV_PATH=path/to/apy.csv

  2. soil_service → Punjab district soil averages (N, P, K, pH, moisture)

Output:
  models/yield_model.pkl
  models/encoders.pkl
"""

import os
import sys
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder

# ─── Add project root so app modules are importable ────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from app.services.soil_service import PUNJAB_SOIL_AVERAGES, PUNJAB_DEFAULT_SOIL
from app.utils.feature_engineering import (
    calculate_nutrient_index,
    categorize_rainfall,
    calculate_temperature_deviation,
    calculate_stress_indicator,
)

# ─── Config ────────────────────────────────────────────────────────────────
# Default CSV path — override via env var APY_CSV_PATH
DEFAULT_CSV = r"D:\Downloads\apy.csv"
APY_CSV_PATH = os.getenv("APY_CSV_PATH", DEFAULT_CSV)

TARGET_CROPS = ["Wheat", "Rice", "Maize", "Cotton"]

MODEL_DIR     = Path("models")
MODEL_PATH    = MODEL_DIR / "yield_model.pkl"
ENCODERS_PATH = MODEL_DIR / "encoders.pkl"

# Crop mean temperatures for temperature deviation feature
CROP_MEAN_TEMPS = {"Wheat": 20, "Rice": 28, "Maize": 26, "Cotton": 30}

# Punjab typical weather (used since we don't need live API with local CSV)
# District-level medians based on historical Punjab climate data
PUNJAB_WEATHER = {
    "Rabi":   {"avg_temperature": 16.0, "total_rainfall": 120.0, "humidity": 72.0},
    "Kharif": {"avg_temperature": 30.5, "total_rainfall": 530.0, "humidity": 78.0},
}

# Seasons to keep (map raw CSV season strings → our labels)
SEASON_MAP = {
    "Rabi":        "Rabi",
    "Kharif":      "Kharif",
    "Rabi       ": "Rabi",   # trailing spaces in CSV
    "Kharif     ": "Kharif",
}

# Irrigation type inferred from district (no weather API needed)
BOREWELL_DISTRICTS = {"BATHINDA", "FAZILKA", "MANSA", "MUKTSAR", "FARIDKOT"}
RAINFED_DISTRICTS  = {"HOSHIARPUR", "PATHANKOT", "GURDASPUR"}


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Load and clean CSV
# ══════════════════════════════════════════════════════════════════════════════

def load_yield_data(csv_path: str) -> pd.DataFrame:
    """
    Load apy.csv, filter to Punjab + target crops,
    compute yield_qtl_ha = Production (tonnes) × 10 / Area (ha).
    """
    print(f"\n📂 Loading CSV: {csv_path}")
    if not Path(csv_path).exists():
        print(f"❌ File not found: {csv_path}")
        print("   Set env var APY_CSV_PATH to your file location.")
        sys.exit(1)

    df = pd.read_csv(csv_path)
    print(f"   Total rows in CSV: {len(df):,}")

    # ── Standardise column names ─────────────────────────────────────────────
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={
        "State_Name":    "state",
        "District_Name": "district",
        "Crop_Year":     "year",
        "Season":        "season_raw",
        "Crop":          "crop_raw",
        "Area":          "area_ha",
        "Production":    "production_tonnes",
    })

    # ── Filter to Punjab ─────────────────────────────────────────────────────
    df = df[df["state"].str.strip().str.lower() == "punjab"].copy()
    print(f"   Punjab rows: {len(df):,}")

    # ── Filter seasons ───────────────────────────────────────────────────────
    df["season"] = df["season_raw"].str.strip().map(SEASON_MAP)
    df = df[df["season"].notna()].copy()

    # ── Filter crops ─────────────────────────────────────────────────────────
    df["crop"] = df["crop_raw"].str.strip().str.title()
    df = df[df["crop"].isin(TARGET_CROPS)].copy()

    # ── Numeric cleanup ──────────────────────────────────────────────────────
    df["area_ha"]           = pd.to_numeric(df["area_ha"],           errors="coerce")
    df["production_tonnes"] = pd.to_numeric(df["production_tonnes"], errors="coerce")
    df["year"]              = pd.to_numeric(df["year"],              errors="coerce").astype("Int64")

    df = df.dropna(subset=["area_ha", "production_tonnes", "year"])
    df = df[(df["area_ha"] > 0) & (df["production_tonnes"] > 0)]

    # ── Yield (quintal/ha) ───────────────────────────────────────────────────
    # Production in tonnes, Area in hectares; 1 tonne = 10 quintals
    df["yield_qtl_ha"] = (df["production_tonnes"] * 10) / df["area_ha"]

    # ── Sanity clip ──────────────────────────────────────────────────────────
    df = df[(df["yield_qtl_ha"] >= 5) & (df["yield_qtl_ha"] <= 150)]

    print(f"   After filtering: {len(df):,} rows")
    print(f"   Crops : {df['crop'].value_counts().to_dict()}")
    print(f"   Years : {int(df['year'].min())} – {int(df['year'].max())}")

    return df[["state", "district", "year", "season", "crop", "yield_qtl_ha"]].reset_index(drop=True)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Attach soil data from existing soil_service
# ══════════════════════════════════════════════════════════════════════════════

def get_soil_for_district(district: str) -> dict:
    """Fuzzy-match district name to Punjab soil averages."""
    d_title = district.strip().title()
    if d_title in PUNJAB_SOIL_AVERAGES:
        return PUNJAB_SOIL_AVERAGES[d_title]
    d_lower = d_title.lower()
    for key, vals in PUNJAB_SOIL_AVERAGES.items():
        if key.lower() in d_lower or d_lower.startswith(key.lower().split()[0]):
            return vals
    return PUNJAB_DEFAULT_SOIL


def attach_soil(df: pd.DataFrame) -> pd.DataFrame:
    """Add N, P, K, pH, soil_moisture from district lookup."""
    soil_rows = df["district"].apply(
        lambda d: pd.Series(get_soil_for_district(d))
    )
    return pd.concat([df, soil_rows], axis=1)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Attach weather (Punjab seasonal averages)
# ══════════════════════════════════════════════════════════════════════════════

def attach_weather(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add avg_temperature, total_rainfall, humidity.
    Uses Punjab seasonal climate averages (Rabi vs Kharif).
    These are typical multi-year averages — sufficient for model training
    without needing a live weather API.
    """
    df["avg_temperature"] = df["season"].map(
        lambda s: PUNJAB_WEATHER[s]["avg_temperature"]
    )
    df["total_rainfall"] = df["season"].map(
        lambda s: PUNJAB_WEATHER[s]["total_rainfall"]
    )
    df["humidity"] = df["season"].map(
        lambda s: PUNJAB_WEATHER[s]["humidity"]
    )
    return df


# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Feature engineering
# ══════════════════════════════════════════════════════════════════════════════

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute all derived features using existing feature_engineering utils."""
    df["nutrient_index"] = df.apply(
        lambda r: calculate_nutrient_index(r["nitrogen"], r["phosphorus"], r["potassium"]),
        axis=1
    )
    df["rainfall_category"] = df["total_rainfall"].apply(categorize_rainfall)
    df["temperature_deviation"] = df.apply(
        lambda r: calculate_temperature_deviation(
            r["avg_temperature"], CROP_MEAN_TEMPS.get(r["crop"], 25)
        ), axis=1
    )
    df["stress_indicator"] = df.apply(
        lambda r: int(calculate_stress_indicator(r["total_rainfall"], r["avg_temperature"])),
        axis=1
    )

    def infer_irrigation(district):
        d = district.upper()
        if any(b in d for b in BOREWELL_DISTRICTS):
            return "Borewell"
        if any(r in d for r in RAINFED_DISTRICTS):
            return "Rainfed"
        return "Canal"

    df["irrigation_type"] = df["district"].apply(infer_irrigation)
    return df


# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 — Encode categoricals and build feature matrix
# ══════════════════════════════════════════════════════════════════════════════

FEATURE_COLUMNS = [
    "nitrogen", "phosphorus", "potassium", "soil_ph", "soil_moisture",
    "avg_temperature", "total_rainfall", "humidity",
    "nutrient_index", "temperature_deviation", "stress_indicator",
    "crop_enc", "season_enc", "district_enc", "irrigation_enc",
]


def encode_and_build(df: pd.DataFrame):
    """Label encode categoricals, return (X, y, encoders dict)."""
    encoders = {}
    for col, enc_col in [
        ("crop",           "crop_enc"),
        ("season",         "season_enc"),
        ("district",       "district_enc"),
        ("irrigation_type","irrigation_enc"),
    ]:
        le = LabelEncoder()
        df[enc_col] = le.fit_transform(df[col].astype(str))
        encoders[col] = le

    X = df[FEATURE_COLUMNS].values
    y = df["yield_qtl_ha"].values
    return X, y, encoders


# ══════════════════════════════════════════════════════════════════════════════
# STEP 6 — Train and evaluate
# ══════════════════════════════════════════════════════════════════════════════

def train_model(X, y):
    """Train RandomForestRegressor, print evaluation metrics."""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"\n🤖 Training RandomForestRegressor on {len(X_train)} samples...")

    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=None,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2   = r2_score(y_test, y_pred)
    mape = np.mean(np.abs((y_test - y_pred) / np.maximum(y_test, 1))) * 100

    print(f"\n  📊 Test set ({len(X_test)} samples):")
    print(f"     RMSE : {rmse:.2f} quintal/ha")
    print(f"     R²   : {r2:.4f}")
    print(f"     MAPE : {mape:.2f}%")

    importance = pd.Series(model.feature_importances_, index=FEATURE_COLUMNS)
    print("\n  📈 Top-5 feature importances:")
    print(importance.sort_values(ascending=False).head(5).to_string())

    return model


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    MODEL_DIR.mkdir(exist_ok=True)

    # 1. Load CSV
    df = load_yield_data(APY_CSV_PATH)
    if df.empty:
        print("❌ No data after filtering. Exiting.")
        sys.exit(1)

    # 2. Soil
    print("\n🌱 Attaching soil data...")
    df = attach_soil(df)

    # 3. Weather
    print("☁️  Attaching Punjab seasonal weather averages...")
    df = attach_weather(df)

    # 4. Feature engineering
    print("⚙️  Engineering features...")
    df = engineer_features(df)

    # 5. Drop rows with NaN in raw (pre-encoding) columns
    RAW_COLS = [
        "nitrogen", "phosphorus", "potassium", "soil_ph", "soil_moisture",
        "avg_temperature", "total_rainfall", "humidity",
        "nutrient_index", "temperature_deviation", "stress_indicator",
        "crop", "season", "district", "irrigation_type", "yield_qtl_ha",
    ]
    df = df.dropna(subset=RAW_COLS)
    print(f"\n✅ Final training set: {len(df):,} rows")

    if len(df) < 50:
        print("❌ Not enough data. Exiting.")
        sys.exit(1)

    # 6. Encode + build matrix (adds crop_enc, season_enc etc. to df)
    X, y, encoders = encode_and_build(df)

    # 7. Train
    model = train_model(X, y)

    # 8. Save
    joblib.dump(model,    MODEL_PATH)
    joblib.dump(encoders, ENCODERS_PATH)
    print(f"\n✅ Model saved    → {MODEL_PATH}")
    print(f"✅ Encoders saved → {ENCODERS_PATH}")
    print("\n🎉 Training complete! Restart the API server to use the real ML model.")


if __name__ == "__main__":
    main()
