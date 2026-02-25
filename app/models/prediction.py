from pydantic import BaseModel, Field, field_validator
from typing import Optional


class YieldRange(BaseModel):
    """Yield prediction range (lower, expected, higher)"""
    lower: float = Field(..., description="Lower bound yield (quintal/hectare)")
    expected: float = Field(..., description="Expected yield (quintal/hectare)")
    higher: float = Field(..., description="Upper bound yield (quintal/hectare)")


class PredictionRequest(BaseModel):
    """
    Input features for yield prediction.
    Provide GPS coordinates from phone — district and state are auto-detected.
    """

    # GPS Location (from phone) — replaces hardcoded district
    latitude: float = Field(
        ..., ge=-90, le=90,
        description="GPS latitude from phone (auto-detects district & state)"
    )
    longitude: float = Field(
        ..., ge=-180, le=180,
        description="GPS longitude from phone (auto-detects district & state)"
    )

    # Crop & Season
    crop_type: str = Field(..., description="Crop type (Wheat, Rice, Maize, Cotton)")
    season: str = Field(..., description="Season (Rabi/Kharif)")

    # Soil Features (Manual Input)
    nitrogen: float = Field(..., ge=0, description="Nitrogen content (kg/ha)")
    phosphorus: float = Field(..., ge=0, description="Phosphorus content (kg/ha)")
    potassium: float = Field(..., ge=0, description="Potassium content (kg/ha)")
    soil_ph: float = Field(..., ge=0, le=14, description="Soil pH value")
    soil_moisture: float = Field(..., ge=0, le=100, description="Soil moisture (%)")
    irrigation_type: str = Field(..., description="Irrigation type (Canal/Borewell/Rainfed)")

    # Weather (optional — auto-fetched from GPS coordinates if not provided)
    avg_temperature: Optional[float] = Field(None, description="Average temperature (°C)")
    total_rainfall: Optional[float] = Field(None, description="Total rainfall (mm)")
    humidity: Optional[float] = Field(None, ge=0, le=100, description="Humidity (%)")

    class Config:
        json_schema_extra = {
            "example": {
                "latitude": 30.9010,
                "longitude": 75.8573,
                "crop_type": "Wheat",
                "season": "Rabi",
                "nitrogen": 80,
                "phosphorus": 40,
                "potassium": 40,
                "soil_ph": 7.0,
                "soil_moisture": 25,
                "irrigation_type": "Canal"
            }
        }


class LocationInfo(BaseModel):
    """Auto-detected location from GPS"""
    district: str
    state: str
    latitude: float
    longitude: float


class PredictionResponse(BaseModel):
    """Yield prediction output"""
    crop_type: str
    season: str
    location: LocationInfo
    yield_per_hectare: YieldRange
    unit: str = "quintal/hectare"
    confidence_note: str = "Prediction based on soil, weather, and location data"

    class Config:
        json_schema_extra = {
            "example": {
                "crop_type": "Wheat",
                "season": "Rabi",
                "location": {
                    "district": "Ludhiana",
                    "state": "Punjab",
                    "latitude": 30.9010,
                    "longitude": 75.8573
                },
                "yield_per_hectare": {
                    "lower": 48.2,
                    "expected": 52.4,
                    "higher": 56.7
                },
                "unit": "quintal/hectare",
                "confidence_note": "Prediction based on soil, weather, and location data"
            }
        }
