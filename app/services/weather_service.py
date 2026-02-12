"""
Weather Service - OpenWeatherMap API Integration
Uses free tier API as specified in data_sources_plan.md
"""

import httpx
from typing import Optional, Dict
from app.config import settings
from app.constants import PUNJAB_COORDINATES
from app.models.weather import WeatherData, WeatherResponse
from app.utils.logger import logger


class WeatherService:
    """OpenWeatherMap API service for fetching weather data"""
    
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
    
    def __init__(self):
        self.api_key = settings.openweather_api_key
        if not self.api_key or self.api_key == "your_api_key_here":
            logger.warning("OpenWeatherMap API key not configured. Weather features will use default values.")
    
    async def get_weather_by_district(self, district: str) -> Optional[WeatherResponse]:
        """
        Fetch current weather for a Punjab district
        
        Args:
            district: Punjab district name
            
        Returns:
            WeatherResponse or None if API call fails
        """
        # Get coordinates for district
        coords = PUNJAB_COORDINATES.get(district)
        if not coords:
            logger.error(f"Coordinates not found for district: {district}")
            return None
        
        # Check if API key is configured
        if not self.api_key or self.api_key == "your_api_key_here":
            logger.warning(f"Using default weather values for {district} (API key not configured)")
            return self._get_default_weather(district, coords)
        
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "lat": coords["lat"],
                    "lon": coords["lon"],
                    "appid": self.api_key,
                    "units": "metric"  # Celsius
                }
                
                response = await client.get(self.BASE_URL, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                # Parse weather data
                weather_data = WeatherData(
                    temperature=data["main"]["temp"],
                    feels_like=data["main"]["feels_like"],
                    humidity=data["main"]["humidity"],
                    pressure=data["main"]["pressure"],
                    rainfall_1h=data.get("rain", {}).get("1h", 0),
                    rainfall_3h=data.get("rain", {}).get("3h", 0),
                    description=data["weather"][0]["description"]
                )
                
                return WeatherResponse(
                    district=district,
                    coordinates=coords,
                    current_weather=weather_data
                )
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching weather for {district}: {e}")
            return self._get_default_weather(district, coords)
        except Exception as e:
            logger.error(f"Error fetching weather for {district}: {e}")
            return self._get_default_weather(district, coords)
    
    def _get_default_weather(self, district: str, coords: Dict) -> WeatherResponse:
        """
        Return default weather values when API is unavailable
        Uses typical Punjab climate values
        """
        default_weather = WeatherData(
            temperature=25.0,
            feels_like=24.5,
            humidity=60.0,
            pressure=1013.0,
            rainfall_1h=0.0,
            rainfall_3h=0.0,
            description="default values (API unavailable)"
        )
        
        return WeatherResponse(
            district=district,
            coordinates=coords,
            current_weather=default_weather
        )
    
    def extract_weather_features(self, weather_response: WeatherResponse) -> Dict:
        """
        Extract relevant features from weather response for ML model
        
        Returns:
            dict with avg_temperature, total_rainfall, humidity
        """
        weather = weather_response.current_weather
        
        # For current weather, use current temperature
        # In production, you might want to fetch historical averages
        return {
            "avg_temperature": weather.temperature,
            "total_rainfall": (weather.rainfall_1h or 0) + (weather.rainfall_3h or 0),
            "humidity": weather.humidity
        }


# Global weather service instance
weather_service = WeatherService()
