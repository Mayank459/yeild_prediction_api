from pydantic import BaseModel, Field
from typing import Optional


class YieldRange(BaseModel):
    """Yield prediction range (lower, expected, higher)"""
    lower: float = Field(..., description="Lower bound yield (quintal/hectare)")
    expected: float = Field(..., description="Expected yield (quintal/hectare)")
    higher: float = Field(..., description="Upper bound yield (quintal/hectare)")


class PredictionRequest(BaseModel):
    """
    Input for yield prediction.

    Only REQUIRED from the farmer:
      - GPS coordinates (from phone)
      - crop_type
      - irrigation_type

    Everything else (soil N/P/K/pH, moisture, season, weather) is AUTO-FETCHED.
    You can still override any auto-fetched value by providing it explicitly.
    """

    # ── Required from phone ──────────────────────────────────────────────────
    latitude: float = Field(
        ..., ge=-90, le=90,
        description="GPS latitude (auto-detects district, state, season, soil & weather)"
    )
    longitude: float = Field(
        ..., ge=-180, le=180,
        description="GPS longitude"
    )

    # ── Required from farmer ─────────────────────────────────────────────────
    crop_type: str = Field(..., description="Crop type: Wheat, Rice, Maize, Cotton")
    irrigation_type: str = Field(..., description="Canal / Borewell / Rainfed")

    # ── Optional overrides (auto-fetched if not provided) ────────────────────
    season: Optional[str] = Field(
        None,
        description="Rabi / Kharif — auto-detected from current date if omitted"
    )

    # Soil (auto-fetched from SoilGrids + Punjab district averages if omitted)
    nitrogen: Optional[float] = Field(None, ge=0, description="Nitrogen (kg/ha)")
    phosphorus: Optional[float] = Field(None, ge=0, description="Phosphorus (kg/ha)")
    potassium: Optional[float] = Field(None, ge=0, description="Potassium (kg/ha)")
    soil_ph: Optional[float] = Field(None, ge=0, le=14, description="Soil pH")
    soil_moisture: Optional[float] = Field(None, ge=0, le=100, description="Soil moisture (%)")

    # Weather (auto-fetched from OpenWeatherMap via GPS if omitted)
    avg_temperature: Optional[float] = Field(None, description="Avg temperature (°C)")
    total_rainfall: Optional[float] = Field(None, description="Total rainfall (mm)")
    humidity: Optional[float] = Field(None, ge=0, le=100, description="Humidity (%)")

    class Config:
        json_schema_extra = {
            "example": {
                "latitude": 30.9010,
                "longitude": 75.8573,
                "crop_type": "Wheat",
                "irrigation_type": "Canal",
                "_comment": "All other fields are auto-fetched from GPS + date"
            }
        }


class SoilInfo(BaseModel):
    """Soil parameters used for prediction (auto-fetched or provided)"""
    nitrogen: float
    phosphorus: float
    potassium: float
    soil_ph: float
    soil_moisture: float
    source: str = "auto"   # 'auto' or 'user_provided'


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
    soil: SoilInfo
    yield_per_hectare: YieldRange
    unit: str = "quintal/hectare"
    confidence_note: str = "Prediction based on GPS location, soil, and weather data"

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
                "soil": {
                    "nitrogen": 220,
                    "phosphorus": 21,
                    "potassium": 142,
                    "soil_ph": 7.7,
                    "soil_moisture": 29,
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
        }
