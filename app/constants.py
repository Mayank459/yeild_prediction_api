"""
Constants for KhetBuddy Yield Prediction System
Aligned with plan_ml_only.md

NOTE: District coordinates have been REMOVED.
      Districts and states are now auto-detected from GPS via reverse geocoding.
      This makes the API work for ALL of India without any hardcoding.
"""

# Supported Crops (Initial scope from plan_ml_only.md)
CROPS = ["Wheat", "Rice", "Maize", "Cotton"]

# Crop Seasons
SEASONS = ["Rabi", "Kharif"]

# Irrigation Types
IRRIGATION_TYPES = ["Canal", "Borewell", "Rainfed"]

# Crop-Season Mapping (from data_sources_plan.md)
CROP_SEASON_MAP = {
    "Wheat": "Rabi",
    "Rice": "Kharif",
    "Maize": "Kharif",
    "Cotton": "Kharif"
}

# Rainfall Categories (for feature engineering)
RAINFALL_CATEGORIES = {
    "Low": (0, 500),        # mm/year
    "Medium": (500, 1000),
    "High": (1000, float("inf"))
}

# Default yield ranges (quintal/hectare) — for validation only
YIELD_RANGES = {
    "Wheat": {"min": 30, "max": 70},
    "Rice": {"min": 35, "max": 75},
    "Maize": {"min": 25, "max": 60},
    "Cotton": {"min": 15, "max": 40}
}
