# 🌾 Punjab Crop Yield Prediction System – Project Plan

## 1. Problem Statement
Build an **API-deployable crop yield prediction system** focused on **Punjab** that predicts crop yield and provides actionable recommendations (irrigation & fertilizer). The system should be scalable to other states in the future.

---

## 2. Project Scope (MVP)

### Geography
- Punjab (district-level)

### Crops (Initial)
- Wheat
- Rice
- Maize
- Cotton

### Core Features
- Yield prediction (quintal/hectare)
- Yield range (low / expected / high)
- Yield improvement after recommendations
- Irrigation scheduling
- Fertilizer (NPK) recommendation

---

## 3. Inputs & Outputs

### 3.1 Model Inputs

#### A. User / Static Inputs
- District (Punjab)
- Crop type
- Season (Rabi / Kharif)
- Sowing date
- Irrigation type (Canal / Borewell / Rainfed)
- Soil parameters:
  - Nitrogen (N)
  - Phosphorus (P)
  - Potassium (K)
  - pH
  - Soil type

#### B. Dynamic Inputs (API Fetched)
- Historical rainfall
- Rainfall forecast (30–90 days)
- Average temperature
- Humidity / soil moisture proxy

---

### 3.2 Model Outputs

#### Primary Output
- Predicted yield (q/ha)

#### Secondary Outputs
- Yield range (min, expected, max)
- Improved yield after recommendations

#### Recommendations
- Irrigation schedule (weekly)
- Fertilizer quantity & timing
- Stress / risk indicator

---

## 4. Data Gathering Strategy

### 4.1 Crop Yield Data
**Sources**
- Government of India – Agriculture Statistics
- Punjab Agriculture Department
- Kaggle datasets (Punjab-filtered)

**Fields**
- District
- Crop
- Year
- Area sown
- Yield (q/ha)

---

### 4.2 Weather Data
**APIs**
- OpenWeatherMap / Meteostat

**API Calls**
```http
GET /historical/weather?lat={}&lon={}&start={}&end={}
GET /forecast/weather?lat={}&lon={}
```

**Features Extracted**
- Average temperature
- Total rainfall
- Humidity

---

### 4.3 Soil Data
**Sources**
- Soil Health Card dataset (India)
- Manual entry (fallback for MVP)

**Fields**
- N, P, K
- pH
- Soil type

---

### 4.4 Data Storage
| Data Type | Storage |
|---------|--------|
User profiles | PostgreSQL |
Historical datasets | CSV / Parquet |
Weather cache | Redis (optional) |
ML features | Local feature store |

---

## 5. Machine Learning Pipeline

### 5.1 Feature Engineering
- Crop encoding
- District encoding
- Season encoding
- Rainfall aggregation (pre-sowing, mid-season)
- Temperature averages
- Interaction features (crop × irrigation)

---

### 5.2 Model Selection
| Model | Reason |
|-----|-------|
Random Forest | Handles non-linear agri data |
XGBoost | High accuracy on tabular data |
LightGBM | Faster & scalable |

**Evaluation Metrics**
- RMSE
- R² Score
- MAPE

---

### 5.3 Training Workflow
```
Raw Data
 → Data Cleaning
 → Feature Engineering
 → Train/Validation Split (year-wise)
 → Model Training
 → Model Evaluation
 → Save model (.pkl)
```

---

### 5.4 Inference Workflow
- Load trained model at API startup
- Fetch real-time weather
- Merge with user & soil data
- Predict yield
- Generate recommendations

---

## 6. Backend & API Architecture

### 6.1 Tech Stack
- FastAPI
- PostgreSQL
- SQLAlchemy
- JWT Authentication
- Docker
- Render Deployment

---

### 6.2 API Flow
```
User Input
 → Validation
 → Weather API Fetch
 → Soil Data Fetch
 → ML Prediction
 → Recommendation Engine
 → Response
```

---

### 6.3 API Endpoints

#### Authentication
```http
POST /auth/register
POST /auth/login
```

#### User Profile
```http
POST /profile
GET /profile
```

#### Yield Prediction
```http
POST /predict/yield
```

**Sample Request**
```json
{
  "district": "Ludhiana",
  "crop": "Wheat",
  "season": "Rabi",
  "sowing_date": "2025-11-15",
  "irrigation": "Canal",
  "soil": {
    "n": 80,
    "p": 40,
    "k": 35,
    "ph": 6.8
  }
}
```

---

## 7. Deployment Plan (Render)

### 7.1 Project Structure
```
app/
 ├── main.py
 ├── routes/
 ├── services/
 ├── ml/
 ├── models/
 ├── requirements.txt
 └── Dockerfile
```

### 7.2 Deployment Steps
1. Push code to GitHub
2. Create Render Web Service (Docker)
3. Attach PostgreSQL instance
4. Add environment variables
5. Deploy API

---

## 8. Phase-wise Execution Plan

### Phase 1 (Week 1–2)
- Punjab-only dataset
- Yield prediction model
- Single inference API

### Phase 2 (Week 3)
- Irrigation & fertilizer recommendations
- Yield improvement simulation

### Phase 3 (Week 4)
- Authentication
- User profiles
- Prediction history

### Phase 4 (Future Enhancements)
- Image-based disease detection
- Weather alerts
- Community features
- Mobile app integration

---

## 9. Scaling Strategy

| Layer | Scaling Approach |
|-----|----------------|
Geography | Add state as feature |
ML | Per-state models |
Backend | Separate ML microservice |
Data | Feature store & pipelines |
UI | Multilingual support |

---

## 10. Final Outcome
A **production-ready, API-based crop yield prediction system** for Punjab that is:
- Accurate
- Deployable
- Scalable
- Interview & demo ready

---

✅ **This document serves as the single source of truth for development, deployment, and future scaling.**

