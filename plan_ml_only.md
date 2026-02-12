# 🌾 Crop Yield Prediction System – ML-Only Plan (Punjab)

> **Scope Clarification**  
This document defines **ONLY the Machine Learning (ML) system** for crop yield prediction.  
❌ No backend architecture  
❌ No authentication / database  
❌ No full application logic  

The goal is to build a **working ML model + inference-ready logic** for yield prediction, aligned with the project PDF.

---

## 1. Objective

Develop a **Punjab-specific crop yield prediction model** that predicts:
- Expected yield (quintal/hectare)
- Yield range (lower–expected–higher)

The model uses **soil + crop + season + weather features** and can later be plugged into any backend or API.

---

## 2. Geographic & Crop Scope

### Region
- Punjab (district-level)

### Crops (Initial)
- Wheat
- Rice
- Maize
- Cotton

### Seasons
- Rabi
- Kharif

---

## 3. ML Input Features

### 3.1 Soil & Farm Features (Manual Input)

| Feature | Type | Description |
|------|----|------------|
| Nitrogen (N) | Numeric | kg/ha |
| Phosphorus (P) | Numeric | kg/ha |
| Potassium (K) | Numeric | kg/ha |
| Soil pH | Numeric | Acidity/alkalinity |
| Soil Moisture | Numeric | % or proxy |
| Irrigation Type | Categorical | Canal / Borewell / Rainfed |

---

### 3.2 Crop & Season Features

| Feature | Type | Description |
|------|----|------------|
| Crop Type | Categorical | Wheat, Rice, etc. |
| Season | Categorical | Rabi / Kharif |
| District | Categorical | Punjab districts |

---

### 3.3 Weather & Climate Features

| Feature | Source | Description |
|------|------|------------|
| Average Temperature | Weather API | Crop season mean |
| Total Rainfall | Weather API | Sowing → current |
| Rainfall Forecast | Weather API | Short-term future |
| Humidity (optional) | Weather API | Moisture proxy |

---

## 4. Target Variable

| Variable | Unit |
|--------|------|
| Crop Yield | Quintal / Hectare |

---

## 5. Data Sources (Free & Public)

### Crop Yield Data
- Government of India – Agriculture Statistics
- Punjab Agriculture Department
- Kaggle (India Crop Production datasets)

### Weather Data
- NASA POWER (historical climate data)
- Meteostat (historical temperature & rainfall)
- OpenWeatherMap (current & forecast weather)

### Soil Data
- Soil Health Card Dataset (India)
- District-level soil averages

---

## 6. Feature Engineering Plan

### 6.1 Encoding
- Crop → Label Encoding
- District → Label Encoding
- Season → Binary encoding
- Irrigation Type → Label Encoding

---

### 6.2 Derived Features

| Feature | Description |
|------|------------|
| Nutrient Index | (N + P + K) / 3 |
| Rainfall Category | Low / Medium / High |
| Temperature Deviation | Avg temp − crop mean |
| Stress Indicator | Low rain + high temp |

---

## 7. Model Selection

### Primary Model (Mandatory)
- **Random Forest Regressor**

**Reason**
- Handles non-linear agricultural data
- Works well with mixed feature types
- Robust for small and noisy datasets

---

### Optional Models (Future Improvement)
- XGBoost Regressor
- LightGBM Regressor

---

## 8. Training Pipeline

```
Raw Datasets
 → Data Cleaning
 → Feature Engineering
 → Train-Test Split (year-wise)
 → Model Training
 → Model Evaluation
 → Save model & encoders
```

### Evaluation Metrics
- RMSE
- R² Score
- MAPE

---

## 9. Prediction Logic

### Base Prediction
```
yield_prediction = model.predict(X)
```

### Yield Range Calculation
```
Lower Bound  = prediction × 0.92
Expected     = prediction
Upper Bound  = prediction × 1.08
```

---

## 10. Final ML Output

```json
{
  "yield_per_hectare": {
    "lower": 48.2,
    "expected": 52.4,
    "higher": 56.7
  },
  "unit": "quintal/hectare"
}
```

---

## 11. Deliverables (ML-Only)

- Cleaned Punjab crop dataset
- Feature-engineered training data
- Trained ML model (`model.pkl`)
- Encoders (`encoders.pkl`)
- Model evaluation report
- Inference-ready prediction logic

---

## 12. Explicit Exclusions (Out of Scope)

❌ Backend services  
❌ Authentication / database  
❌ Recommendation systems  
❌ Irrigation & fertilizer models  
❌ Disease detection  

---

## 13. Future Integration Note

> This ML system is designed as a **standalone, inference-ready component** and can be integrated into APIs, mobile apps, or dashboards in later phases without retraining.

---

✅ **This document serves as the final ML-only plan for the Crop Yield Prediction System.**

