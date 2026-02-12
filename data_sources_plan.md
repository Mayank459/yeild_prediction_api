# 🌾 Yield Prediction System – Free APIs & Dataset Plan (Punjab)

This document lists **100% FREE data sources** (APIs + datasets) required to build the **Yield Prediction ML system**, strictly limited to the **ML-only scope** and aligned with the project PDF.

---

## 1. Data Requirements Overview

### Required Data Categories
1. Crop yield (historical)
2. Weather & climate (real-time + historical)
3. Soil health parameters
4. Crop & season metadata

All sources below are **free**, **public**, and suitable for academic + demo projects.

---

## 2. Crop Yield Datasets (FREE)

### 2.1 Government of India – Agriculture Statistics

**Source**  
- Ministry of Agriculture & Farmers Welfare (India)

**Access**  
- https://agricoop.gov.in/en/statistics

**Data Available**
- State-wise & district-wise crop yield
- Crop-wise production
- Area sown
- Yearly yield (quintal/hectare)

**Why use this**
- Official and reliable
- Perfect for Punjab-focused modeling

---

### 2.2 Punjab Agriculture Department

**Source**  
- Punjab Agriculture Official Portal

**Access**  
- https://agripb.gov.in

**Data Available**
- District-wise crop yield
- Crop seasons (Rabi/Kharif)

---

### 2.3 Kaggle (Curated Free Datasets)

**Recommended Datasets**
- India Crop Yield Dataset
- Crop Production in India (1997–2015)

**Access**  
- https://www.kaggle.com

**How to use**
- Filter for Punjab districts only
- Merge with weather data by year

---

## 3. Weather & Climate APIs (FREE)

### 3.1 OpenWeatherMap API (Primary – Recommended)

**Why**
- Free tier available
- Easy to integrate
- Real-time + forecast support

**Signup**  
- https://openweathermap.org/api

**Free Tier Limits**
- 60 calls/minute
- Current weather + 5-day forecast

---

### 3.2 Meteostat (Best for Historical Weather)

**Why**
- Completely free
- Excellent historical coverage
- No API key required

**Access**  
- https://meteostat.net

**Data Available**
- Historical temperature
- Rainfall
- Weather station data

---

### 3.3 NASA POWER (Highly Recommended for ML)

**Why**
- Free & scientific-grade
- Long-term climate data
- Ideal for agriculture ML

**Access**  
- https://power.larc.nasa.gov

**Data Available**
- Daily temperature
- Rainfall
- Humidity
- Solar radiation

---

## 4. Soil Health Datasets (FREE)

### 4.1 Soil Health Card Dataset (India)

**Source**  
- Government of India – Soil Health Card Scheme

**Access**  
- https://soilhealth.dac.gov.in

**Data Available**
- Nitrogen (N)
- Phosphorus (P)
- Potassium (K)
- pH value
- District-wise soil health

**Usage**
- Use district-level averages for MVP

---

### 4.2 ICAR Soil Resources (Optional)

**Source**  
- Indian Council of Agricultural Research

**Access**  
- https://icar.org.in

**Data Available**
- Soil type classification
- Agro-climatic zones

---

## 5. Crop & Season Metadata

### 5.1 Crop Season Mapping

**Source**  
- ICAR / Agriculture Textbooks (Public)

**Mapping Example**
- Wheat → Rabi
- Rice → Kharif
- Maize → Kharif

---

## 6. Data Integration Plan

### 6.1 Offline (Training Phase)

```
Crop Yield Dataset (Punjab)
   +
Historical Weather Data (NASA POWER / Meteostat)
   +
Soil Health Data (SHC)
   ↓
Final Training Dataset
```

---

### 6.2 Online (Inference Phase)

```
User Input
   ↓
Weather API Call (OpenWeatherMap)
   ↓
Feature Engineering
   ↓
Yield Prediction Model
```

---

## 7. API Usage Summary

| Data Type | Source | Mode |
|--------|------|------|
Yield | Govt / Kaggle | Offline |
Weather (current) | OpenWeatherMap | Online |
Weather (historical) | NASA POWER | Offline |
Soil (NPK, pH) | Soil Health Card | Offline |

---

## 8. What You Can Clearly Claim in Review

> "All datasets and APIs used in this project are publicly available and free. Government agricultural statistics, NASA climate data, and OpenWeatherMap APIs ensure scientific validity and reproducibility."

---

## 9. Outcome

With these sources, you can build:
- A **realistic ML yield prediction system**
- Without paid APIs
- Without legal or licensing issues
- Fully aligned with your project design

---

✅ This document can be committed as **data_sources_plan.md** alongside `plan.md` in your repository.

