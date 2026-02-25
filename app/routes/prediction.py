"""
API Routes - Prediction Endpoints
GPS coordinates auto-detect district and state via reverse geocoding.
No hardcoded district list needed — works for all of India.
"""

from fastapi import APIRouter, HTTPException, status
from app.models.prediction import PredictionRequest, PredictionResponse, LocationInfo
from app.constants import CROPS, SEASONS, IRRIGATION_TYPES, CROP_SEASON_MAP
from app.services.prediction_service import prediction_service
from app.services.weather_service import weather_service
from app.services.geocoding_service import geocoding_service
from app.utils.logger import logger

router = APIRouter(prefix="/api", tags=["Yield Prediction"])


@router.post("/predict", response_model=PredictionResponse, status_code=status.HTTP_200_OK)
async def predict_yield(request: PredictionRequest):
    """
    Predict crop yield using GPS coordinates.

    - **latitude / longitude**: from phone GPS (auto-detects district & state)
    - **crop_type**: Wheat, Rice, Maize, Cotton
    - **season**: Rabi or Kharif
    - **soil params**: nitrogen, phosphorus, potassium, pH, moisture
    - **irrigation_type**: Canal / Borewell / Rainfed

    Returns yield prediction with lower, expected, and higher bounds (quintal/hectare).
    """

    # Validate crop type
    if request.crop_type not in CROPS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid crop type. Must be one of: {', '.join(CROPS)}"
        )

    # Validate season
    if request.season not in SEASONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid season. Must be one of: {', '.join(SEASONS)}"
        )

    # Validate irrigation type
    if request.irrigation_type not in IRRIGATION_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid irrigation type. Must be one of: {', '.join(IRRIGATION_TYPES)}"
        )

    # Warn on unusual crop-season combo
    expected_season = CROP_SEASON_MAP.get(request.crop_type)
    if expected_season and request.season != expected_season:
        logger.warning(
            f"Unusual crop-season: {request.crop_type} in {request.season} "
            f"(typical: {expected_season})"
        )

    try:
        # ── Step 1: Reverse geocode GPS → district + state ──────────────────
        logger.info(f"Reverse geocoding ({request.latitude}, {request.longitude})")
        geo_result = await geocoding_service.reverse_geocode(
            request.latitude, request.longitude
        )

        if geo_result is None:
            # Fallback: use coordinates as-is with generic labels
            district = "Unknown District"
            state = "Unknown State"
            logger.warning("Geocoding failed — using fallback location labels")
        else:
            if not geocoding_service.is_india(geo_result):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Coordinates are outside India. This API currently supports India only."
                )
            district = geo_result["district"]
            state = geo_result["state"]

        location = LocationInfo(
            district=district,
            state=state,
            latitude=request.latitude,
            longitude=request.longitude
        )

        # ── Step 2: Fetch weather via GPS coords (no district lookup needed) ─
        request_data = request.model_dump()

        if request.avg_temperature is None or request.total_rainfall is None:
            logger.info(f"Fetching weather for {district}, {state} via GPS")
            weather_response = await weather_service.get_weather_by_coords(
                lat=request.latitude,
                lon=request.longitude,
                location_name=f"{district}, {state}"
            )

            if weather_response:
                weather_features = weather_service.extract_weather_features(weather_response)
                request_data["avg_temperature"] = weather_features["avg_temperature"]
                request_data["total_rainfall"] = weather_features["total_rainfall"]
                request_data["humidity"] = weather_features["humidity"]
            else:
                request_data["avg_temperature"] = 25.0
                request_data["total_rainfall"] = 500.0
                request_data["humidity"] = 60.0

        # Add location to features for ML model
        request_data["district"] = district
        request_data["state"] = state

        # ── Step 3: Predict yield ────────────────────────────────────────────
        yield_range = await prediction_service.predict(request_data)

        return PredictionResponse(
            crop_type=request.crop_type,
            season=request.season,
            location=location,
            yield_per_hectare=yield_range
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in yield prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@router.get("/crops", status_code=status.HTTP_200_OK)
async def get_crops():
    """Get list of supported crops"""
    return {"crops": CROPS, "count": len(CROPS)}


@router.get("/seasons", status_code=status.HTTP_200_OK)
async def get_seasons():
    """Get list of crop seasons with crop-season mapping"""
    return {"seasons": SEASONS, "crop_season_mapping": CROP_SEASON_MAP}


@router.get("/irrigation-types", status_code=status.HTTP_200_OK)
async def get_irrigation_types():
    """Get list of supported irrigation types"""
    return {"irrigation_types": IRRIGATION_TYPES}


@router.post("/geocode", status_code=status.HTTP_200_OK)
async def reverse_geocode(latitude: float, longitude: float):
    """
    Utility endpoint: Reverse geocode GPS coordinates → district + state.
    Useful for testing from the mobile app.
    """
    result = await geocoding_service.reverse_geocode(latitude, longitude)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Geocoding service temporarily unavailable"
        )
    return {
        "latitude": latitude,
        "longitude": longitude,
        "district": result["district"],
        "state": result["state"],
        "country": result["country"]
    }
