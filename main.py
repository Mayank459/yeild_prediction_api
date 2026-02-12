"""
KhetBuddy Yield Prediction API
Main FastAPI application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import prediction
from app.utils.logger import logger


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    🌾 **Crop Yield Prediction API for Punjab**
    
    This API predicts crop yield (quintal/hectare) based on:
    - Soil parameters (NPK, pH, moisture)
    - Crop type and season
    - District location
    - Weather conditions (real-time from OpenWeatherMap or manual input)
    
    **Supported Crops:** Wheat, Rice, Maize, Cotton
    
    **Data Sources:**
    - Weather: OpenWeatherMap API (free tier)
    - Soil & Yield: Government of India Agriculture Statistics
    - Model: Random Forest Regressor (placeholder logic until trained)
    
    **ML-Only Scope:** As per plan_ml_only.md
    """,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(prediction.router)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "🌾 KhetBuddy Yield Prediction API",
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.app_version
    }


@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")
    
    # Check if OpenWeatherMap API key is configured
    if not settings.openweather_api_key or settings.openweather_api_key == "your_api_key_here":
        logger.warning("⚠️  OpenWeatherMap API key not configured. Using default weather values.")
        logger.warning("   Sign up at: https://openweathermap.org/api")
    else:
        logger.info("✓ OpenWeatherMap API key configured")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info(f"Shutting down {settings.app_name}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
