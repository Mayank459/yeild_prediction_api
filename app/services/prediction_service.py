"""
Prediction Service - ML Model Integration
Implements yield prediction pipeline from plan_ml_only.md
"""

import os
import joblib
import numpy as np
from pathlib import Path
from typing import Dict, Optional
from app.config import settings
from app.constants import CROPS, SEASONS, IRRIGATION_TYPES
from app.models.prediction import YieldRange
from app.utils.feature_engineering import prepare_features, encode_categorical
from app.utils.logger import logger


class PredictionService:
    """Yield prediction service with ML model integration"""
    
    def __init__(self):
        self.model = None
        self.encoders = None
        self.model_loaded = False
        self._load_models()
    
    def _load_models(self):
        """
        Load trained ML model and encoders
        Falls back to placeholder logic if model files don't exist
        """
        model_path = Path(settings.ml_model_path)
        encoders_path = Path(settings.ml_encoders_path)
        
        if model_path.exists() and encoders_path.exists():
            try:
                self.model = joblib.load(model_path)
                self.encoders = joblib.load(encoders_path)
                self.model_loaded = True
                logger.info("ML model and encoders loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load ML model: {e}. Using placeholder prediction.")
                self.model_loaded = False
        else:
            logger.info("ML model files not found. Using placeholder prediction logic.")
            self.model_loaded = False
    
    def predict_yield(self, features: Dict) -> YieldRange:
        """
        Predict crop yield using ML model or placeholder logic
        
        Args:
            features: Prepared feature dictionary
            
        Returns:
            YieldRange with lower, expected, higher bounds
        """
        if self.model_loaded and self.model is not None:
            return self._predict_with_model(features)
        else:
            return self._placeholder_prediction(features)
    
    def _predict_with_model(self, features: Dict) -> YieldRange:
        """
        Predict using trained Random Forest model
        """
        try:
            # Encode categorical features
            features_encoded = features.copy()
            features_encoded['crop_type'] = encode_categorical(features['crop_type'], CROPS)
            features_encoded['season'] = encode_categorical(features['season'], SEASONS)
            # district comes from reverse geocoding — encode via stable hash (no fixed list needed)
            features_encoded['district'] = abs(hash(features.get('district', ''))) % 1000
            features_encoded['irrigation_type'] = encode_categorical(features['irrigation_type'], IRRIGATION_TYPES)
            
            # Prepare feature vector (order should match training)
            feature_vector = np.array([
                features_encoded['nitrogen'],
                features_encoded['phosphorus'],
                features_encoded['potassium'],
                features_encoded['soil_ph'],
                features_encoded['soil_moisture'],
                features_encoded['avg_temperature'],
                features_encoded['total_rainfall'],
                features_encoded['humidity'],
                features_encoded['nutrient_index'],
                features_encoded['temperature_deviation'],
                features_encoded['stress_indicator'],
                features_encoded['crop_type'],
                features_encoded['season'],
                features_encoded['district'],
                features_encoded['irrigation_type']
            ]).reshape(1, -1)
            
            # Predict
            prediction = self.model.predict(feature_vector)[0]
            
            # Calculate yield range (as per plan_ml_only.md)
            return self._calculate_yield_range(prediction)
            
        except Exception as e:
            logger.error(f"Error in model prediction: {e}. Falling back to placeholder.")
            return self._placeholder_prediction(features)
    
    def _placeholder_prediction(self, features: Dict) -> YieldRange:
        """
        Placeholder prediction logic (until trained model is available)
        Uses heuristic-based estimation considering:
        - Crop type baseline yields
        - Soil nutrients (NPK)
        - Weather conditions
        - Irrigation type
        """
        crop_type = features.get('crop_type', 'Wheat')
        
        # Base yields (quintal/hectare) for different crops
        base_yields = {
            "Wheat": 50.0,
            "Rice": 55.0,
            "Maize": 45.0,
            "Cotton": 25.0
        }
        base_yield = base_yields.get(crop_type, 50.0)
        
        # Adjust for soil nutrients
        nutrient_index = features.get('nutrient_index', 50)
        nutrient_factor = 1.0 + (nutrient_index - 50) / 100  # ±20% based on nutrients
        
        # Adjust for weather
        rainfall_category = features.get('rainfall_category', 'Medium')
        rainfall_factors = {"Low": 0.85, "Medium": 1.0, "High": 1.1}
        rainfall_factor = rainfall_factors.get(rainfall_category, 1.0)
        
        # Adjust for stress
        stress = features.get('stress_indicator', 0)
        stress_factor = 0.9 if stress else 1.0
        
        # Adjust for irrigation
        irrigation = features.get('irrigation_type', 'Canal')
        irrigation_factors = {"Canal": 1.05, "Borewell": 1.1, "Rainfed": 0.9}
        irrigation_factor = irrigation_factors.get(irrigation, 1.0)
        
        # Calculate expected yield
        expected_yield = base_yield * nutrient_factor * rainfall_factor * stress_factor * irrigation_factor
        
        # Ensure reasonable bounds
        expected_yield = max(10, min(expected_yield, 100))
        
        return self._calculate_yield_range(expected_yield)
    
    def _calculate_yield_range(self, expected_yield: float) -> YieldRange:
        """
        Calculate yield range from expected value
        As per plan_ml_only.md:
        - Lower: prediction × 0.92
        - Expected: prediction
        - Upper: prediction × 1.08
        """
        return YieldRange(
            lower=round(expected_yield * 0.92, 2),
            expected=round(expected_yield, 2),
            higher=round(expected_yield * 1.08, 2)
        )
    
    async def predict(self, request_data: Dict) -> YieldRange:
        """
        Main prediction pipeline
        
        Args:
            request_data: Raw request data with all features
            
        Returns:
            YieldRange prediction
        """
        # Prepare features (includes feature engineering)
        features = prepare_features(request_data)
        
        # Predict yield
        yield_range = self.predict_yield(features)
        
        logger.info(f"Prediction for {request_data.get('crop_type')} in {request_data.get('district')}: {yield_range.expected} quintal/ha")
        
        return yield_range


# Global prediction service instance
prediction_service = PredictionService()
