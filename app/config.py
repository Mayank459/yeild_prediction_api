from pydantic_settings import BaseSettings
from typing import List, Union
from pydantic import field_validator


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Application
    app_name: str = "KhetBuddy Yield Prediction API"
    app_version: str = "1.0.0"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    # OpenWeatherMap API
    openweather_api_key: str = ""
    
    # CORS - can be a comma-separated string or list
    cors_origins: Union[str, List[str]] = "http://localhost:3000,http://localhost:8000"
    
    # Model paths (use custom prefix to avoid protected namespace warning)
    ml_model_path: str = "models/yield_model.pkl"
    ml_encoders_path: str = "models/encoders.pkl"
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            # Split comma-separated string into list
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        protected_namespaces = ('settings_',)  # Fix protected namespace warning


# Global settings instance
settings = Settings()
