from pydantic import BaseModel, Field
from typing import Optional


class YieldRange(BaseModel):
    """Yield prediction range (lower, expected, higher)"""
    lower: float = Field(..., description="Lower bound yield (quintal/hectare)")
    expected: float = Field(..., description="Expected yield (quintal/hectare)")
    higher: float = Field(..., description="Upper bound yield (quintal/hectare)")


class PredictionRequest(BaseModel):
    """Input features for yield prediction"""
    
    # Crop & Location
    crop_type: str = Field(..., description="Crop type (Wheat, Rice, Maize, Cotton)")
    season: str = Field(..., description="Season (Rabi/Kharif)")
    district: str = Field(..., description="Punjab district")
    
    # Soil Features (Manual Input)
    nitrogen: float = Field(..., ge=0, description="Nitrogen content (kg/ha)")
    phosphorus: float = Field(..., ge=0, description="Phosphorus content (kg/ha)")
    potassium: float = Field(..., ge=0, description="Potassium content (kg/ha)")
    soil_ph: float = Field(..., ge=0, le=14, description="Soil pH value")
    soil_moisture: float = Field(..., ge=0, le=100, description="Soil moisture (%)")
    irrigation_type: str = Field(..., description="Irrigation type (Canal/Borewell/Rainfed)")
    
    # Weather data (optional - will be fetched from API if not provided)
    avg_temperature: Optional[float] = Field(None, description="Average temperature (°C)")
    total_rainfall: Optional[float] = Field(None, description="Total rainfall (mm)")
    humidity: Optional[float] = Field(None, ge=0, le=100, description="Humidity (%)")
    
    class Config:
        json_schema_extra = {
            "example": {
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
        }


class PredictionResponse(BaseModel):
    """Yield prediction output"""
    crop_type: str
    district: str
    season: str
    yield_per_hectare: YieldRange
    unit: str = "quintal/hectare"
    confidence_note: str = "Prediction based on soil, weather, and historical data"
    
    class Config:
        json_schema_extra = {
            "example": {
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
        }
