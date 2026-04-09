# 🧠 KhetBuddy: `train.py` Line-by-Line Explanation

This document breaks down the `train.py` script section by section. For each section, we ask: **"Why did we write it this way, and why not another way?"**

---

## 1. Top-level Setup and Imports (Lines 1–36)

```python
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
from app.utils.feature_engineering import (...)
```

### 🤔 Why this and not that?
*   **Why `joblib` and not `pickle` or `json`?** We use `joblib` because it is specifically optimized for saving large NumPy arrays (which is what scikit-learn Machine Learning models are made out of). Standard `pickle` is slower for arrays, and `json` cannot save Python objects like models natively.
*   **Why `sys.path.insert(0...)`?** Python's import system can be tricky. By inserting the project root (where `train.py` lives) into the system path, we guarantee that `train.py` can import code from `app/services/...` no matter where inside the terminal the user runs the script from. If we didn't do this, you'd get `ModuleNotFoundError`.
*   **Why `pathlib.Path` instead of `os.path.join`?** `Path` handles cross-platform slash directions automatically (Windows `\` vs Mac/Linux `/`). It makes paths object-oriented (`Path("models") / "yield_model.pkl"`) which is much cleaner than messy string concatenations.

---

## 2. Configuration & Constants (Lines 38–70)

```python
DEFAULT_CSV = r"D:\Downloads\apy.csv"
APY_CSV_PATH = os.getenv("APY_CSV_PATH", DEFAULT_CSV)

TARGET_CROPS = ["Wheat", "Rice", "Maize", "Cotton"]
MODEL_DIR     = Path("models")
# ... (Crop Temps, Weather Defaults, Irrigation Mappings) ...
```

### 🤔 Why this and not that?
*   **Why `os.getenv` for the CSV path?** This makes the script portable. If Developer A has the file in `D:\Downloads` but Developer B has it in `C:\Data`, Developer B doesn't have to edit the code. They just set the environment variable `APY_CSV_PATH=C:\Data\apy.csv`, and it works automatically via fallback.
*   **Why hardcode weather and irrigation defaults here instead of calling an API?** We are processing *hundreds of thousands* of rows of historical data from a CSV. If we made a live API call to OpenWeatherMap or SoilGrids for every row, it would take days to process and cost thousands of dollars in API fees. So, for training historical data, we use static, historical averages (like `PUNJAB_WEATHER`) mapped by season and district.

---

## 3. Loading Data: `load_yield_data` (Lines 76–134)

```python
def load_yield_data(csv_path: str) -> pd.DataFrame:
    # Check if exists -> sys.exit(1) if not
    df = pd.read_csv(csv_path)
    # Strip whitespace, rename columns to clean formats...
    df = df[df["state"].str.strip().str.lower() == "punjab"].copy()
    # Filter seasons, crops... Drop NaN...
    df["yield_qtl_ha"] = (df["production_tonnes"] * 10) / df["area_ha"]
    df = df[(df["yield_qtl_ha"] >= 5) & (df["yield_qtl_ha"] <= 150)]
    return df
```

### 🤔 Why this and not that?
*   **Why `sys.exit(1)` if CSV is missing?** If the script can't find the historical data, there is absolutely no point continuing. `exit(1)` is a clean OS-level abort that signals to tools (like Docker or CI pipelines) that a critical failure occurred, rather than crashing with a messy Python stack-trace later on.
*   **Why rename columns and strip whitespace?** Real-world government datasets (like `apy.csv`) are infamously dirty. A column might be named `"  Crop"` instead of `"Crop"`. By forcefully renaming and trimming `.str.strip()`, we inoculate our pipeline against "invisible space" bugs later on.
*   **Why calculate `yield_qtl_ha` manually? Why not just predict tonnes?** Predicting "Tonnes" makes no sense because a 1000-hectare farm will always produce more tonnes than a 2-hectare farm. Tonnes is a measure of farm size, not crop efficiency. By dividing tonnes by area (and multiplying by 10 to convert to quintals), we get **Yield Density (Quintals per Hectare)**. This gives the ML model an absolute truth about soil/weather efficiency regardless of farm size.
*   **Why clip between 5 and 150?** Typo defense. If the government CSV accidentally listed 10 tonnes from 0.001 hectares, the math would spit out an impossible yield of 100,000 qtl/ha. Clipping throws away physically impossible numbers that would confuse the ML model.

---

## 4. Appending Extra Data: Soil & Weather (Lines 140–181)

```python
def get_soil_for_district(district: str) -> dict:
    # Try exact match -> try partial match -> return default
def attach_soil(df: pd.DataFrame) -> pd.DataFrame:
    # use apply(get_soil_for_district)
def attach_weather(df: pd.DataFrame) -> pd.DataFrame:
    # Map season to PUNJAB_WEATHER
```

### 🤔 Why this and not that?
*   **Why fuzzy matching for Districts?** The CSV might say `"Hoshiarpur"`, but our dictionary might say `"HOSHIARPUR "` or `"Hoshiarpur city"`. Exact `==` matching breaks easily. The fuzzy string check makes the pipeline resilient.
*   **Why inject soil and weather data at all? The CSV doesn't have it.** The original CSV only has "District, Year, Crop, Tonnes". If we trained an ML model on that, all it could tell us is "Ludhiana produces good wheat." It wouldn't know *why*. By injecting the NPK and Temperature variables *into the dataset manually*, we are teaching the Random Forest the biological reasons (e.g., Nitrogen levels = higher wheat yield). This is how we give the model actual intelligence!

---

## 5. Feature Engineering (Lines 187–214)

```python
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    # df["nutrient_index"] = calculate_nutrient_index(...)
    # df["temperature_deviation"] = calculate_temperature_deviation(...)
    # infer_irrigation() based on BOREWELL_DISTRICTS
```

### 🤔 Why this and not that?
*   **Why create new features? Don't we already have N/P/K and Temp?** This is called "Feature Engineering". A Random Forest is smart, but doing math for it makes it smarter faster. Instead of hoping the model figures out that Wheat dies when it gets above 30°C, we explicitly hand it a `temperature_deviation` feature showing exactly how far off the temperature is from the ideal 20°C. We are giving the model shortcuts to the right answers!
*   **Why hardcode irrigation by district?** The historical CSV didn't record if a farm used a canal or borewell. But we know logically that Fazilka relies heavily on borewells due to geography, while central Punjab uses canals. We infer it here so the model has *something* to learn about water dependencies.

---

## 6. Encoding Categoricals: `encode_and_build` (Lines 220–244)

```python
def encode_and_build(df: pd.DataFrame):
    encoders = {}
    for col, enc_col in [("crop", "crop_enc"), ("season", "season_enc")...]:
        le = LabelEncoder()
        df[enc_col] = le.fit_transform(df[col].astype(str))
        encoders[col] = le
    # Build X matrix, y vector
    return X, y, encoders
```

### 🤔 Why this and not that?
*   **Why use `LabelEncoder` at all?** Machine Learning models are purely mathematical formulas `(y = mx + b)`. They cannot multiply the word `"Wheat"` by `0.5`. They throw an error. `LabelEncoder` changes `"Wheat"` to `0`, `"Rice"` to `1`, etc.
*   **Why not use "One-Hot Encoding" (`pd.get_dummies`)?** One-Hot Encoding creates a new column for every category (e.g., `is_wheat`, `is_rice`), giving us huge data frames with mostly zeros. Decision Trees (Random Forests) actually handle numerical label encoding (`0, 1, 2, 3`) quite well natively, and it keeps our input array size small (15 features instead of 40).
*   **Why save the `encoders` to a dictionary and `return` them?** This is critical. If `"Wheat"` is encoded as `0` during training, then when the API gets a live request a month later, we *must* encode `"Wheat"` as `0` again or the model will crash. We save these exact instances of `LabelEncoder` so the FastAPI app can load them later!

---

## 7. Model Training & Evaluation: `train_model` (Lines 250–282)

```python
def train_model(X, y):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=300, n_jobs=-1, random_state=42...)
    model.fit(X_train, y_train)
    # Calculate RMSE, R2, MAPE, and print Feature Importances
    return model
```

### 🤔 Why this and not that?
*   **Why an 80/20 train/test split? Why not train on 100% of the data?** If you give a student the answers to the test before the exam, they will score 100%—but they didn't actually learn anything. If we trained on 100% of data, the model would simply memorize the CSV ("Overfitting") and fail horribly when the user inputs new API data. We hide 20% of the data (`X_test`), train on 80%, and ask the model to predict the hidden 20% to see how truly smart it is.
*   **Why `n_jobs=-1`?** By default, Python models train on 1 CPU core. Random Forests are just 300 independent decision trees; they can all be grown at the same time. `n_jobs=-1` tells scikit-learn to use *all available CPU cores* on the computer, speeding up training by up to 10x!
*   **Why print Feature Importances?** It tells us if the model is learning nonsense. If `crop_enc` is the most important feature, great (obviously crop type affects yield the most). If `soil_ph` suddenly became the most important, we would investigate, as a decimal point of pH shouldn't cause a massive spike in yield isolated from other features.

---

## 8. Main Orchestrator: `main` (Lines 288–339)

```python
def main():
    MODEL_DIR.mkdir(exist_ok=True)
    df = load_yield_data(...)
    df = attach_soil(df)
    df = attach_weather(df)
    df = engineer_features(df)
    # df.dropna()
    X, y, encoders = encode_and_build(df)
    model = train_model(X, y)
    
    joblib.dump(model, MODEL_PATH)
    joblib.dump(encoders, ENCODERS_PATH)
```

### 🤔 Why this and not that?
*   **Why structure it with a single `main()` block at the bottom?** Why not just drop the code freely in the script? Wrapping it inside `main()` and running via `if __name__ == "__main__":` prevents the training process from spontaneously launching if another script merely imports a function (e.g., `from train import encode_and_build`).
*   **Why `dropna` right before encoding?** Over the course of the pipeline, some fuzzy matches might have failed or data logic might have returned `NaN` (Not a Number). If there is a single `NaN` in a matrix of 100,000 numbers, `RandomForest` will explode with an error. The `dropna` acts as a final safety net, cleaning the dataset of any rows that lost data during the joining process.
*   **Why use `.pkl` output files?** By writing to `/models/yield_model.pkl`, the training script successfully passes the baton. The Heavy Training script shuts down and exits, using zero RAM. The FastAPI app can instantly wake up, open those lightweight `.pkl` files, and begin making live predictions instantly!
