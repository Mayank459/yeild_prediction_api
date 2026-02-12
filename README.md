# 🌾 KhetBuddy Yield Prediction API

A FastAPI-based ML system for predicting crop yields in Punjab, India. Built strictly for **ML-only scope** as defined in the project plans.

## 📋 Overview

This API predicts crop yield (quintal/hectare) based on:
- **Soil parameters**: Nitrogen, Phosphorus, Potassium, pH, moisture
- **Crop type**: Wheat, Rice, Maize, Cotton
- **Season**: Rabi, Kharif
- **District**: Punjab districts
- **Weather**: Real-time data from OpenWeatherMap API

## 🎯 Scope

**ML-Only Features:**
- ✅ Yield prediction pipeline
- ✅ Feature engineering (nutrient index, rainfall categories, stress indicators)
- ✅ Weather API integration (OpenWeatherMap)
- ✅ REST API endpoints
- ✅ Docker support

**Out of Scope:**
- ❌ Authentication/Authorization
- ❌ Database integration
- ❌ Recommendation systems
- ❌ Irrigation/fertilizer optimization
- ❌ Disease detection

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- OpenWeatherMap API key (free tier: https://openweathermap.org/api)

### Local Setup

1. **Clone and navigate to project**
   ```bash
   cd d:\API\khetBuddy
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   copy .env.example .env
   # Edit .env and add your OpenWeatherMap API key
   ```

5. **Run the API**
   ```bash
   python main.py
   ```

   API will be available at: http://localhost:8000

### Docker Setup

1. **Set environment variables**
   ```bash
   # Create .env file with your API key
   echo OPENWEATHER_API_KEY=your_key_here > .env
   ```

2. **Build and run**
   ```bash
   docker-compose up --build
   ```

   API will be available at: http://localhost:8000

## 📚 API Documentation

### Interactive Docs
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Endpoints

#### 1. Predict Yield
**POST** `/api/predict`

Predicts crop yield based on input features.

**Request Body:**
```json
{
  "crop_type": "Wheat",
  "season": "Rabi",
  "district": "Ludhiana",
  "nitrogen": 80,
  "phosphorus": 40,
  "potassium": 40,
  "soil_ph": 7.0,
  "soil_moisture": 25,
  "irrigation_type": "Canal",
  "avg_temperature": 20.5,
  "total_rainfall": 450,
  "humidity": 65
}
```

**Response:**
```json
{
  "crop_type": "Wheat",
  "district": "Ludhiana",
  "season": "Rabi",
  "yield_per_hectare": {
    "lower": 48.2,
    "expected": 52.4,
    "higher": 56.7
  },
  "unit": "quintal/hectare",
  "confidence_note": "Prediction based on soil, weather, and historical data"
}
```

#### 2. Get Crops
**GET** `/api/crops`

Returns list of supported crops.

#### 3. Get Districts
**GET** `/api/districts`

Returns list of Punjab districts.

#### 4. Get Seasons
**GET** `/api/seasons`

Returns crop seasons and crop-season mapping.

#### 5. Health Check
**GET** `/health`

API health status.

## 🔬 ML Model

### Current Status
The API uses **placeholder prediction logic** until a trained model is available. The prediction pipeline is ready to accept:
- Trained Random Forest model: `models/yield_model.pkl`
- Encoders: `models/encoders.pkl`

### Placeholder Logic
The current implementation uses heuristic-based estimation considering:
- Crop-specific base yields
- Soil nutrient adjustments (NPK index)
- Weather conditions (rainfall, temperature)
- Irrigation type factors
- Stress indicators

### Yield Range Calculation
As per `plan_ml_only.md`:
- **Lower bound**: prediction × 0.92
- **Expected**: prediction
- **Upper bound**: prediction × 1.08

## 📊 Data Sources

All data sources are **free and public**:

| Data Type | Source | Status |
|-----------|--------|--------|
| Crop Yield | Govt of India / Kaggle | Offline |
| Weather (current) | OpenWeatherMap | Online |
| Weather (historical) | NASA POWER | Offline |
| Soil (NPK, pH) | Soil Health Card | Offline |

See [data_sources_plan.md](data_sources_plan.md) for details.

## 🛠️ Feature Engineering

Implemented features from `plan_ml_only.md`:

1. **Nutrient Index**: `(N + P + K) / 3`
2. **Rainfall Category**: Low (<500mm) / Medium (500-1000mm) / High (>1000mm)
3. **Temperature Deviation**: `Avg temp - crop mean temp`
4. **Stress Indicator**: `Low rain + high temp`

## 🌐 Weather Integration

- **Primary API**: OpenWeatherMap (free tier: 60 calls/minute)
- **Fallback**: Default typical Punjab climate values
- **Features extracted**: Temperature, rainfall, humidity

## 📁 Project Structure

```
khetBuddy/
├── app/
│   ├── models/           # Pydantic schemas
│   │   ├── prediction.py
│   │   └── weather.py
│   ├── routes/           # API endpoints
│   │   └── prediction.py
│   ├── services/         # Business logic
│   │   ├── prediction_service.py
│   │   └── weather_service.py
│   ├── utils/            # Utilities
│   │   ├── feature_engineering.py
│   │   └── logger.py
│   ├── config.py         # Settings
│   └── constants.py      # Static data
├── models/               # ML models (add trained models here)
├── main.py               # FastAPI app
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🧪 Testing

### Manual Testing

1. **Health check:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Get crops:**
   ```bash
   curl http://localhost:8000/api/crops
   ```

3. **Predict yield:**
   ```bash
   curl -X POST http://localhost:8000/api/predict \
     -H "Content-Type: application/json" \
     -d '{
       "crop_type": "Wheat",
       "season": "Rabi",
       "district": "Ludhiana",
       "nitrogen": 80,
       "phosphorus": 40,
       "potassium": 40,
       "soil_ph": 7.0,
       "soil_moisture": 25,
       "irrigation_type": "Canal"
     }'
   ```

## 📝 Adding a Trained Model

1. Train your Random Forest model using the feature engineering pipeline
2. Save the model:
   ```python
   import joblib
   joblib.dump(model, 'models/yield_model.pkl')
   joblib.dump(encoders, 'models/encoders.pkl')
   ```
3. Restart the API - it will automatically load and use the trained model

## 🔄 API Configuration

Edit `.env` file:

```env
# Application
APP_NAME=KhetBuddy Yield Prediction API
DEBUG=True
PORT=8000

# OpenWeatherMap API
OPENWEATHER_API_KEY=your_api_key_here

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Model paths
MODEL_PATH=models/yield_model.pkl
ENCODERS_PATH=models/encoders.pkl
```

## 📖 References

- **Plan Documents**:
  - [plan_ml_only.md](plan_ml_only.md) - ML system design
  - [data_sources_plan.md](data_sources_plan.md) - Data sources reference

- **Data Sources**:
  - [OpenWeatherMap API](https://openweathermap.org/api)
  - [NASA POWER](https://power.larc.nasa.gov)
  - [Govt of India Agriculture Statistics](https://agricoop.gov.in/en/statistics)

## 🤝 Contributing

This is an ML-only MVP. Future enhancements outside the ML scope should be planned separately.

## 📄 License

This project uses free and public data sources. See individual data source licenses for details.

---

**Built with:** FastAPI, scikit-learn, OpenWeatherMap API  
**For:** Punjab Crop Yield Prediction (ML-Only Scope)
