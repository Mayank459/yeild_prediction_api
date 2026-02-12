"""
API Routes - Prediction Endpoints
"""

from fastapi import APIRouter, HTTPException, status
from app.models.prediction import PredictionRequest, PredictionResponse
from app.constants import CROPS, PUNJAB_DISTRICTS, SEASONS, CROP_SEASON_MAP
from app.services.prediction_service import prediction_service
from app.services.weather_service import weather_service
from app.utils.logger import logger

router = APIRouter(prefix="/api", tags=["Yield Prediction"])


@router.post("/predict", response_model=PredictionResponse, status_code=status.HTTP_200_OK)
async def predict_yield(request: PredictionRequest):
    """
    Predict crop yield for Punjab districts
    
    Input: Soil parameters, crop type, season, district, weather (optional)
    Output: Yield prediction with lower, expected, and higher bounds (quintal/hectare)
    """
    # Validate crop type
    if request.crop_type not in CROPS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid crop type. Must be one of: {', '.join(CROPS)}"
        )
    
    # Validate district
    if request.district not in PUNJAB_DISTRICTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid district. Must be a Punjab district."
        )
    
    # Validate season
    if request.season not in SEASONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid season. Must be one of: {', '.join(SEASONS)}"
        )
    
    # Validate crop-season combination
    expected_season = CROP_SEASON_MAP.get(request.crop_type)
    if expected_season and request.season != expected_season:
        logger.warning(f"Unusual crop-season combination: {request.crop_type} in {request.season} (expected {expected_season})")
    
    try:
        # Prepare request data
        request_data = request.model_dump()
        
        # Fetch weather data if not provided
        if request.avg_temperature is None or request.total_rainfall is None:
            logger.info(f"Fetching weather data for {request.district}")
            weather_response = await weather_service.get_weather_by_district(request.district)
            
            if weather_response:
                weather_features = weather_service.extract_weather_features(weather_response)
                request_data['avg_temperature'] = weather_features['avg_temperature']
                request_data['total_rainfall'] = weather_features['total_rainfall']
                request_data['humidity'] = weather_features['humidity']
            else:
                # Use default values
                request_data['avg_temperature'] = 25.0
                request_data['total_rainfall'] = 500.0
                request_data['humidity'] = 60.0
        
        # Get prediction
        yield_range = await prediction_service.predict(request_data)
        
        # Build response
        response = PredictionResponse(
            crop_type=request.crop_type,
            district=request.district,
            season=request.season,
            yield_per_hectare=yield_range
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error in yield prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@router.get("/crops", status_code=status.HTTP_200_OK)
async def get_crops():
    """
    Get list of supported crops
    """
    return {
        "crops": CROPS,
        "count": len(CROPS)
    }


@router.get("/districts", status_code=status.HTTP_200_OK)
async def get_districts():
    """
    Get list of Punjab districts
    """
    return {
        "districts": PUNJAB_DISTRICTS,
        "count": len(PUNJAB_DISTRICTS)
    }


@router.get("/seasons", status_code=status.HTTP_200_OK)
async def get_seasons():
    """
    Get list of crop seasons
    """
    return {
        "seasons": SEASONS,
        "crop_season_mapping": CROP_SEASON_MAP
    }
