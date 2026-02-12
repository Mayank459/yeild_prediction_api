from pydantic import BaseModel, Field
from typing import Optional


class WeatherData(BaseModel):
    """Weather data model"""
    temperature: float = Field(..., description="Temperature (°C)")
    feels_like: float = Field(..., description="Feels like temperature (°C)")
    humidity: float = Field(..., description="Humidity (%)")
    pressure: float = Field(..., description="Atmospheric pressure (hPa)")
    rainfall_1h: Optional[float] = Field(None, description="Rainfall in last 1h (mm)")
    rainfall_3h: Optional[float] = Field(None, description="Rainfall in last 3h (mm)")
    description: str = Field(..., description="Weather description")
    
    class Config:
        json_schema_extra = {
            "example": {
                "temperature": 22.5,
                "feels_like": 21.8,
                "humidity": 65,
                "pressure": 1013,
                "rainfall_1h": 0,
                "rainfall_3h": 0,
                "description": "clear sky"
            }
        }


class WeatherResponse(BaseModel):
    """Weather API response"""
    district: str
    coordinates: dict
    current_weather: WeatherData
    
    class Config:
        json_schema_extra = {
            "example": {
                "district": "Ludhiana",
                "coordinates": {"lat": 30.9010, "lon": 75.8573},
                "current_weather": {
                    "temperature": 22.5,
                    "feels_like": 21.8,
                    "humidity": 65,
                    "pressure": 1013,
                    "rainfall_1h": 0,
                    "rainfall_3h": 0,
                    "description": "clear sky"
                }
            }
        }
