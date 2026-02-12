"""
Feature Engineering Utilities
Implements feature engineering logic from plan_ml_only.md
"""

from typing import Tuple


def calculate_nutrient_index(nitrogen: float, phosphorus: float, potassium: float) -> float:
    """
    Calculate nutrient index as defined in plan_ml_only.md
    Formula: (N + P + K) / 3
    """
    return (nitrogen + phosphorus + potassium) / 3.0


def categorize_rainfall(total_rainfall: float) -> str:
    """
    Categorize rainfall into Low/Medium/High
    Based on plan_ml_only.md ranges:
    - Low: 0-500 mm/year
    - Medium: 500-1000 mm/year
    - High: >1000 mm/year
    """
    if total_rainfall < 500:
        return "Low"
    elif total_rainfall < 1000:
        return "Medium"
    else:
        return "High"


def calculate_temperature_deviation(avg_temp: float, crop_mean_temp: float) -> float:
    """
    Calculate temperature deviation from crop mean
    Formula: Avg temp - crop mean temp
    """
    return avg_temp - crop_mean_temp


def calculate_stress_indicator(rainfall: float, temperature: float, 
                               rainfall_threshold: float = 500, 
                               temp_threshold: float = 35) -> bool:
    """
    Calculate stress indicator
    Stress = Low rain + high temp
    Returns True if crop is under stress
    """
    low_rain = rainfall < rainfall_threshold
    high_temp = temperature > temp_threshold
    return low_rain and high_temp


def encode_categorical(value: str, category_list: list) -> int:
    """
    Simple label encoding for categorical features
    Returns index of value in category_list
    """
    try:
        return category_list.index(value)
    except ValueError:
        return -1  # Unknown category


def prepare_features(data: dict) -> dict:
    """
    Prepare all features for ML model
    Combines raw features with engineered features
    """
    # Calculate derived features
    nutrient_index = calculate_nutrient_index(
        data.get('nitrogen', 0),
        data.get('phosphorus', 0),
        data.get('potassium', 0)
    )
    
    rainfall_category = categorize_rainfall(data.get('total_rainfall', 0))
    
    # Crop mean temperatures (example values - should be from training data)
    crop_mean_temps = {
        "Wheat": 20,
        "Rice": 28,
        "Maize": 26,
        "Cotton": 30
    }
    crop_mean_temp = crop_mean_temps.get(data.get('crop_type', 'Wheat'), 25)
    temp_deviation = calculate_temperature_deviation(
        data.get('avg_temperature', 25),
        crop_mean_temp
    )
    
    stress_indicator = calculate_stress_indicator(
        data.get('total_rainfall', 0),
        data.get('avg_temperature', 25)
    )
    
    # Combine all features
    features = {
        # Raw features
        'nitrogen': data.get('nitrogen', 0),
        'phosphorus': data.get('phosphorus', 0),
        'potassium': data.get('potassium', 0),
        'soil_ph': data.get('soil_ph', 7.0),
        'soil_moisture': data.get('soil_moisture', 0),
        'avg_temperature': data.get('avg_temperature', 25),
        'total_rainfall': data.get('total_rainfall', 0),
        'humidity': data.get('humidity', 50),
        
        # Engineered features
        'nutrient_index': nutrient_index,
        'rainfall_category': rainfall_category,
        'temperature_deviation': temp_deviation,
        'stress_indicator': int(stress_indicator),
        
        # Categorical (will be encoded later)
        'crop_type': data.get('crop_type', 'Wheat'),
        'season': data.get('season', 'Rabi'),
        'district': data.get('district', 'Ludhiana'),
        'irrigation_type': data.get('irrigation_type', 'Canal')
    }
    
    return features
