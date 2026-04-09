"""
API Routes - Prediction Endpoints
Full auto-fetch pipeline:
  GPS -> district/state -> soil data -> weather -> season -> predict
Farmer only needs: GPS + crop_type + irrigation_type
"""

from fastapi import APIRouter, HTTPException, status
from app.models.prediction import (
    PredictionRequest, PredictionResponse,
    LocationInfo, SoilInfo
)
from app.constants import CROPS, SEASONS, IRRIGATION_TYPES, CROP_SEASON_MAP
from app.services.prediction_service import prediction_service
from app.services.weather_service import weather_service
from app.services.geocoding_service import geocoding_service
from app.services.soil_service import soil_service
from app.utils.logger import logger

router = APIRouter(prefix="/api", tags=["Yield Prediction"])


@router.post("/predict", response_model=PredictionResponse, status_code=status.HTTP_200_OK)
async def predict_yield(request: PredictionRequest):
    """
    Predict crop yield using GPS coordinates.

    **Minimum required from farmer:**
    - `latitude` / `longitude` — from phone GPS
    - `crop_type` — Wheat / Rice / Maize / Cotton
    - `irrigation_type` — Canal / Borewell / Rainfed

    **Auto-fetched from GPS + date:**
    - District & State (Nominatim reverse geocoding)
    - Season (from current calendar month)
    - Soil N, P, K, pH (SoilGrids API + Punjab district averages)
    - Soil moisture (estimated from weather)
    - Temperature, rainfall, humidity (OpenWeatherMap)

    You can override any auto-fetched value by including it in the request.
    """

    # Validate crop
    if request.crop_type not in CROPS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid crop_type. Choose from: {', '.join(CROPS)}"
        )

    # Validate irrigation
    if request.irrigation_type not in IRRIGATION_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid irrigation_type. Choose from: {', '.join(IRRIGATION_TYPES)}"
        )

    try:
        # ── Step 1: Reverse geocode GPS -> district + state ───────────────────
        logger.info(f"Reverse geocoding ({request.latitude}, {request.longitude})")
        geo_result = await geocoding_service.reverse_geocode(request.latitude, request.longitude)

        if geo_result is None:
            district, state = "Unknown District", "Unknown State"
            logger.warning("Geocoding failed — using fallback location labels")
        else:
            if not geocoding_service.is_india(geo_result):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Coordinates are outside India. This API supports India only."
                )
            district = geo_result["district"]
            state = geo_result["state"]

        location = LocationInfo(
            district=district,
            state=state,
            latitude=request.latitude,
            longitude=request.longitude
        )

        # ── Step 2: Auto-detect season from date (override if user provided) ─
        auto_detected_season = soil_service.get_season_from_date()
        season = request.season or auto_detected_season

        # Validate season if user explicitly provided it
        if request.season and request.season not in SEASONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid season. Choose from: {', '.join(SEASONS)}"
            )

        # Correct season to match crop's canonical season
        expected_season = CROP_SEASON_MAP.get(request.crop_type)
        if expected_season and season != expected_season:
            if not request.season:
                # Season was auto-detected: silently correct it to match the crop
                logger.info(
                    f"Auto-correcting season for {request.crop_type}: "
                    f"{season} -> {expected_season} (crop-canonical season)"
                )
                season = expected_season
            else:
                # User explicitly provided a non-canonical season: warn but respect it
                logger.warning(
                    f"User-provided season '{season}' is unusual for {request.crop_type} "
                    f"(typical: {expected_season}). Proceeding with user input."
                )

        # ── Step 3: Fetch weather via GPS ────────────────────────────────────
        weather_auto = (
            request.avg_temperature is None
            or request.total_rainfall is None
            or request.humidity is None
        )
        if weather_auto:
            logger.info(f"Fetching weather for {district}, {state}")
            weather_response = await weather_service.get_weather_by_coords(
                lat=request.latitude,
                lon=request.longitude,
                location_name=f"{district}, {state}"
            )
            if weather_response:
                wf = weather_service.extract_weather_features(weather_response)
            else:
                wf = {"avg_temperature": 25.0, "total_rainfall": 0.0, "humidity": 60.0}
        else:
            wf = {
                "avg_temperature": request.avg_temperature,
                "total_rainfall": request.total_rainfall,
                "humidity": request.humidity,
            }

        # ── Step 4: Fetch soil data (auto + optional user override) ──────────
        soil_auto = any(v is None for v in [
            request.nitrogen, request.phosphorus, request.potassium,
            request.soil_ph, request.soil_moisture
        ])

        if soil_auto:
            logger.info(f"Fetching soil data for ({request.latitude}, {request.longitude})")
            fetched_soil = await soil_service.get_soil_data(
                lat=request.latitude,
                lon=request.longitude,
                district=district
            )
        else:
            fetched_soil = {}

        # Merge: user-provided values take priority over auto-fetched
        nitrogen     = request.nitrogen     or fetched_soil.get("nitrogen",     205)
        phosphorus   = request.phosphorus   or fetched_soil.get("phosphorus",   17)
        potassium    = request.potassium    or fetched_soil.get("potassium",     130)
        soil_ph      = request.soil_ph      or fetched_soil.get("soil_ph",      7.9)

        # Soil moisture: user > fetched > weather-estimated
        if request.soil_moisture is not None:
            soil_moisture = request.soil_moisture
        elif "soil_moisture" in fetched_soil:
            soil_moisture = fetched_soil["soil_moisture"]
        else:
            soil_moisture = soil_service.estimate_soil_moisture(
                humidity=wf["humidity"],
                recent_rainfall=wf["total_rainfall"]
            )

        soil_source = "user_provided" if not soil_auto else "auto"
        soil = SoilInfo(
            nitrogen=nitrogen,
            phosphorus=phosphorus,
            potassium=potassium,
            soil_ph=soil_ph,
            soil_moisture=soil_moisture,
            source=soil_source
        )

        # ── Step 5: Assemble feature dict and predict ────────────────────────
        request_data = {
            "latitude":       request.latitude,
            "longitude":      request.longitude,
            "crop_type":      request.crop_type,
            "season":         season,
            "district":       district,
            "state":          state,
            "nitrogen":       nitrogen,
            "phosphorus":     phosphorus,
            "potassium":      potassium,
            "soil_ph":        soil_ph,
            "soil_moisture":  soil_moisture,
            "irrigation_type": request.irrigation_type,
            "avg_temperature": wf["avg_temperature"],
            "total_rainfall":  wf["total_rainfall"],
            "humidity":        wf["humidity"],
        }

        yield_range = await prediction_service.predict(request_data)

        return PredictionResponse(
            crop_type=request.crop_type,
            season=season,
            location=location,
            soil=soil,
            yield_per_hectare=yield_range
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@router.get("/crops", status_code=status.HTTP_200_OK)
async def get_crops():
    """Supported crops"""
    return {"crops": CROPS, "count": len(CROPS)}


@router.get("/seasons", status_code=status.HTTP_200_OK)
async def get_seasons():
    """Seasons with auto-detection note"""
    return {
        "seasons": SEASONS,
        "current_season": soil_service.get_season_from_date(),
        "crop_season_mapping": CROP_SEASON_MAP,
        "note": "Season is auto-detected from current date if not provided"
    }


@router.get("/irrigation-types", status_code=status.HTTP_200_OK)
async def get_irrigation_types():
    """Supported irrigation types"""
    return {"irrigation_types": IRRIGATION_TYPES}


@router.post("/geocode", status_code=status.HTTP_200_OK)
async def reverse_geocode(latitude: float, longitude: float):
    """
    Utility: Reverse geocode GPS -> district + state.
    Also returns current auto-detected season and district soil averages.
    """
    result = await geocoding_service.reverse_geocode(latitude, longitude)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Geocoding service temporarily unavailable"
        )

    district = result["district"]
    soil_defaults = soil_service._get_district_averages(district)

    return {
        "latitude": latitude,
        "longitude": longitude,
        "district": district,
        "state": result["state"],
        "country": result["country"],
        "current_season": soil_service.get_season_from_date(),
        "district_soil_averages": soil_defaults
    }
