# 🌾 KhetBuddy Yield Prediction API

A FastAPI-based ML system for predicting crop yields in Punjab, India.  
Farmers only need to provide **GPS coordinates + crop type + irrigation type** — everything else is auto-fetched.

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-supported-blue)](https://docker.com)
[![License](https://img.shields.io/badge/Data-Public%20%26%20Free-brightgreen)](#-data-sources)

---

## 📋 Overview

KhetBuddy predicts crop yield (quintal/hectare) for Punjab farmers. The API is designed to be **mobile-friendly** — a farmer's phone sends GPS coordinates and the API does the rest automatically.

### Auto-Fetched from GPS
| Parameter | Source |
|-----------|--------|
| **District & State** | Nominatim reverse geocoding (OpenStreetMap) |
| **Season** | Auto-detected from current calendar month |
| **Soil N, pH** | SoilGrids API (ISRIC) — free, no key |
| **Soil P, K** | Punjab district averages (Soil Health Cards) |
| **Soil Moisture** | Estimated from weather humidity + rainfall |
| **Temperature, Humidity, Rainfall** | OpenWeatherMap (free tier) |

### Supported Crops & Seasons
| Crop | Typical Season |
|------|---------------|
| Wheat | Rabi (Oct–Mar) |
| Rice | Kharif (Apr–Sep) |
| Maize | Kharif (Apr–Sep) |
| Cotton | Kharif (Apr–Sep) |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- OpenWeatherMap API key ([free tier](https://openweathermap.org/api))

### Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-username/khetBuddy.git
cd khetBuddy

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env
# Open .env and set your OpenWeatherMap API key

# 5. Run the API
python main.py
```

API available at: **http://localhost:8000**  
Interactive docs: **http://localhost:8000/docs**

### Docker Setup

```bash
# Set your API key
echo OPENWEATHER_API_KEY=your_key_here > .env

# Build and run
docker-compose up --build
```

---

## 📚 API Reference

> Interactive Swagger UI: `http://localhost:8000/docs`  
> ReDoc: `http://localhost:8000/redoc`

### Endpoints Summary

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/predict` | Predict crop yield |
| `GET` | `/api/crops` | List supported crops |
| `GET` | `/api/seasons` | List seasons + auto-detected current season |
| `GET` | `/api/irrigation-types` | List irrigation types |
| `POST` | `/api/geocode` | Reverse geocode GPS → district + soil defaults |
| `GET` | `/health` | API health check |
| `GET` | `/` | Root info |

---

### `POST /api/predict`

Predicts crop yield. Only **4 fields are required** — everything else is auto-fetched.

#### Request Body

| Field | Type | Required | Constraints | Auto-Fetched From |
|-------|------|----------|-------------|-------------------|
| `latitude` | float | ✅ | −90 to 90 | — |
| `longitude` | float | ✅ | −180 to 180 | — |
| `crop_type` | string | ✅ | `Wheat` / `Rice` / `Maize` / `Cotton` | — |
| `irrigation_type` | string | ✅ | `Canal` / `Borewell` / `Rainfed` | — |
| `season` | string | ❌ | `Rabi` / `Kharif` | Calendar month |
| `nitrogen` | float | ❌ | ≥ 0, kg/ha | SoilGrids API |
| `phosphorus` | float | ❌ | ≥ 0, kg/ha | Punjab district avg |
| `potassium` | float | ❌ | ≥ 0, kg/ha | Punjab district avg |
| `soil_ph` | float | ❌ | 0 – 14 | SoilGrids API |
| `soil_moisture` | float | ❌ | 0 – 100 % | Estimated from weather |
| `avg_temperature` | float | ❌ | °C | OpenWeatherMap |
| `total_rainfall` | float | ❌ | mm | OpenWeatherMap |
| `humidity` | float | ❌ | 0 – 100 % | OpenWeatherMap |

#### Minimal Request (just GPS + crop)

```json
{
  "latitude": 30.9010,
  "longitude": 75.8573,
  "crop_type": "Wheat",
  "irrigation_type": "Canal"
}
```

#### Full Request (all overrides provided)

```json
{
  "latitude": 30.9010,
  "longitude": 75.8573,
  "crop_type": "Wheat",
  "irrigation_type": "Canal",
  "season": "Rabi",
  "nitrogen": 80,
  "phosphorus": 40,
  "potassium": 40,
  "soil_ph": 7.0,
  "soil_moisture": 25,
  "avg_temperature": 20.5,
  "total_rainfall": 450,
  "humidity": 65
}
```

#### Response `200 OK`

```json
{
  "crop_type": "Wheat",
  "season": "Rabi",
  "location": {
    "district": "Ludhiana",
    "state": "Punjab",
    "latitude": 30.9010,
    "longitude": 75.8573
  },
  "soil": {
    "nitrogen": 220.0,
    "phosphorus": 21.0,
    "potassium": 142.0,
    "soil_ph": 7.7,
    "soil_moisture": 29.0,
    "source": "auto"
  },
  "yield_per_hectare": {
    "lower": 48.2,
    "expected": 52.4,
    "higher": 56.7
  },
  "unit": "quintal/hectare",
  "confidence_note": "Prediction based on GPS location, soil, and weather data"
}
```

> `soil.source` is `"auto"` when values were fetched automatically, or `"user_provided"` when all soil fields were manually supplied.

#### Error Responses

```json
// 400 — Invalid crop_type
{ "detail": "Invalid crop_type. Choose from: Wheat, Rice, Maize, Cotton" }

// 400 — Invalid irrigation_type
{ "detail": "Invalid irrigation_type. Choose from: Canal, Borewell, Rainfed" }

// 400 — Coordinates outside India
{ "detail": "Coordinates are outside India. This API supports India only." }

// 500 — Internal server error
{ "detail": "Prediction failed: <error message>" }
```

---

### `GET /api/crops`

#### Response `200 OK`

```json
{
  "crops": ["Wheat", "Rice", "Maize", "Cotton"],
  "count": 4
}
```

---

### `GET /api/seasons`

#### Response `200 OK`

```json
{
  "seasons": ["Rabi", "Kharif"],
  "current_season": "Rabi",
  "crop_season_mapping": {
    "Wheat": "Rabi",
    "Rice": "Kharif",
    "Maize": "Kharif",
    "Cotton": "Kharif"
  },
  "note": "Season is auto-detected from current date if not provided"
}
```

> `current_season` is live: `Rabi` for Oct–Mar, `Kharif` for Apr–Sep.

---

### `GET /api/irrigation-types`

#### Response `200 OK`

```json
{
  "irrigation_types": ["Canal", "Borewell", "Rainfed"]
}
```

---

### `POST /api/geocode`

Utility to preview district detection and soil defaults for any GPS point.

#### Request (query params)

```
POST /api/geocode?latitude=30.9010&longitude=75.8573
```

#### Response `200 OK`

```json
{
  "latitude": 30.9010,
  "longitude": 75.8573,
  "district": "Ludhiana",
  "state": "Punjab",
  "country": "India",
  "current_season": "Rabi",
  "district_soil_averages": {
    "nitrogen": 220,
    "phosphorus": 21,
    "potassium": 142,
    "soil_ph": 7.7,
    "soil_moisture": 29
  }
}
```

#### Error Responses

```json
// 503 — Geocoding service unavailable
{ "detail": "Geocoding service temporarily unavailable" }
```

---

### `GET /health`

#### Response `200 OK`

```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

### `GET /`

#### Response `200 OK`

```json
{
  "message": "🌾 KhetBuddy Yield Prediction API",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs"
}
```

---

## 🔬 Auto-Fetch Pipeline

```
Farmer sends GPS + crop_type + irrigation_type
           │
           ▼
1. Nominatim Reverse Geocoding → district, state
           │
           ▼
2. Season Auto-Detection from calendar month
   (Rabi: Oct–Mar  |  Kharif: Apr–Sep)
           │
           ▼
3. OpenWeatherMap → temperature, humidity, rainfall
           │
           ▼
4. SoilGrids API → N, pH (GPS-accurate)
   Punjab District Averages → P, K (fallback)
   Moisture estimated from weather
           │
           ▼
5. Feature Engineering → nutrient index, stress indicators
           │
           ▼
6. ML Prediction → yield range (lower / expected / higher)
```

---

## 🛠️ Feature Engineering

| Feature | Formula |
|---------|---------|
| **Nutrient Index** | `(N + P + K) / 3` |
| **Rainfall Category** | Low (<500mm) / Medium (500–1000mm) / High (>1000mm) |
| **Temperature Deviation** | `avg_temp − crop_mean_temp` |
| **Stress Indicator** | Low rain + high temperature |

---

## 🔬 ML Model

### Current Status
The API uses **heuristic-based prediction logic** until a trained model is available.  
The prediction pipeline is ready to accept:
- Trained Random Forest model: `models/yield_model.pkl`
- Label encoders: `models/encoders.pkl`

### Yield Range
- **Lower bound**: `prediction × 0.92`
- **Expected**: `prediction`
- **Upper bound**: `prediction × 1.08`

### Adding a Trained Model

```python
import joblib
joblib.dump(model, 'models/yield_model.pkl')
joblib.dump(encoders, 'models/encoders.pkl')
```

Restart the API — it will automatically detect and use the trained model.

---

## 📊 Data Sources

All data sources are **free and public**:

| Data | Source | How Used |
|------|--------|----------|
| Soil N, pH | [SoilGrids (ISRIC)](https://soilgrids.org) | Per-GPS, no API key |
| Soil P, K | India Soil Health Cards / ICAR | District averages in code |
| Weather | [OpenWeatherMap](https://openweathermap.org/api) | Real-time by GPS |
| Geocoding | [Nominatim (OSM)](https://nominatim.org) | Free, no API key |
| Crop Yield | Govt of India / Kaggle | For model training |
| Historical Weather | [NASA POWER](https://power.larc.nasa.gov) | For model training |

---

## 📁 Project Structure

```
khetBuddy/
├── app/
│   ├── models/                  # Pydantic request/response schemas
│   │   ├── prediction.py
│   │   └── weather.py
│   ├── routes/
│   │   └── prediction.py        # All API endpoints
│   ├── services/
│   │   ├── geocoding_service.py # Nominatim reverse geocoding
│   │   ├── soil_service.py      # SoilGrids + district averages
│   │   ├── weather_service.py   # OpenWeatherMap integration
│   │   └── prediction_service.py
│   ├── utils/
│   │   ├── feature_engineering.py
│   │   └── logger.py
│   ├── config.py                # App settings (pydantic-settings)
│   └── constants.py             # Crops, seasons, districts, irrigation types
├── models/                      # ML model files (add trained models here)
├── main.py                      # FastAPI app entry point
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── render.yaml                  # Render.com deployment config
├── ROADMAP.md
└── README.md
```

---

## ⚙️ Configuration

Edit your `.env` file:

```env
# Application
APP_NAME=KhetBuddy Yield Prediction API
DEBUG=True
PORT=8000

# OpenWeatherMap API (required for live weather)
OPENWEATHER_API_KEY=your_api_key_here

# CORS origins (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# ML model paths
ML_MODEL_PATH=models/yield_model.pkl
ML_ENCODERS_PATH=models/encoders.pkl
```

> If `OPENWEATHER_API_KEY` is not set, the API falls back to default Punjab climate values.

---

## 🧪 Testing

### Health Check
```bash
curl http://localhost:8000/health
```

### Minimal Prediction (GPS only)
```bash
curl -X POST http://localhost:8000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 30.9,
    "longitude": 75.85,
    "crop_type": "Wheat",
    "irrigation_type": "Canal"
  }'
```

### Reverse Geocode
```bash
curl -X POST "http://localhost:8000/api/geocode?latitude=30.9&longitude=75.85"
```

### List Supported Crops
```bash
curl http://localhost:8000/api/crops
```

---

## 🌐 Deployment

The API is deployable on [Render](https://render.com) (free tier):

```bash
# Uses render.yaml configuration
# Set OPENWEATHER_API_KEY in Render dashboard environment variables
```

See [DEPLOY_RENDER.md](DEPLOY_RENDER.md) for step-by-step instructions.

---

## 🗺️ Roadmap

See [ROADMAP.md](ROADMAP.md) for the full development plan:

- **Phase 1:** Multi-state expansion (Haryana, Maharashtra, UP, Karnataka)
- **Phase 2:** Train real ML model (Random Forest → XGBoost)
- **Phase 3:** Crop recommendations, fertilizer optimization, irrigation planning
- **Phase 4:** Database, authentication, mobile app backend

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make changes and test locally
4. Submit a pull request

See [ROADMAP.md](ROADMAP.md) for planned features and contribution guidelines.

---

## 📖 References

- [plan_ml_only.md](plan_ml_only.md) — ML system design
- [data_sources_plan.md](data_sources_plan.md) — Data sources reference
- [SCALABILITY_PLAN.md](SCALABILITY_PLAN.md) — Scaling architecture

---

## 📄 License

Data used is from free and public sources. See individual source licenses for details.

---

**Built with:** FastAPI · scikit-learn · OpenWeatherMap · SoilGrids · Nominatim  
**Scope:** Punjab Crop Yield Prediction (v1.0 MVP)
