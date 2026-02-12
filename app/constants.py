"""
Constants for KhetBuddy Yield Prediction System
Aligned with plan_ml_only.md
"""

# Punjab Districts
PUNJAB_DISTRICTS = [
    "Amritsar", "Barnala", "Bathinda", "Faridkot", "Fatehgarh Sahib",
    "Fazilka", "Ferozepur", "Gurdaspur", "Hoshiarpur", "Jalandhar",
    "Kapurthala", "Ludhiana", "Mansa", "Moga", "Muktsar",
    "Nawanshahr", "Pathankot", "Patiala", "Rupnagar", "Sangrur",
    "SAS Nagar (Mohali)", "Tarn Taran"
]

# Crops (Initial scope from plan_ml_only.md)
CROPS = ["Wheat", "Rice", "Maize", "Cotton"]

# Seasons
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
    "Low": (0, 500),      # mm/year
    "Medium": (500, 1000),
    "High": (1000, float('inf'))
}

# Default yield ranges (quintal/hectare) - for validation
YIELD_RANGES = {
    "Wheat": {"min": 30, "max": 70},
    "Rice": {"min": 35, "max": 75},
    "Maize": {"min": 25, "max": 60},
    "Cotton": {"min": 15, "max": 40}
}

# Punjab coordinates (for weather API)
PUNJAB_COORDINATES = {
    "Amritsar": {"lat": 31.6340, "lon": 74.8723},
    "Barnala": {"lat": 30.3783, "lon": 75.5466},
    "Bathinda": {"lat": 30.2110, "lon": 74.9455},
    "Faridkot": {"lat": 30.6704, "lon": 74.7579},
    "Fatehgarh Sahib": {"lat": 30.6446, "lon": 76.3950},
    "Fazilka": {"lat": 30.4028, "lon": 74.0281},
    "Ferozepur": {"lat": 30.9257, "lon": 74.6142},
    "Gurdaspur": {"lat": 32.0407, "lon": 75.4045},
    "Hoshiarpur": {"lat": 31.5346, "lon": 75.9119},
    "Jalandhar": {"lat": 31.3260, "lon": 75.5762},
    "Kapurthala": {"lat": 31.3800, "lon": 75.3800},
    "Ludhiana": {"lat": 30.9010, "lon": 75.8573},
    "Mansa": {"lat": 29.9988, "lon": 75.3933},
    "Moga": {"lat": 30.8158, "lon": 75.1705},
    "Muktsar": {"lat": 30.4756, "lon": 74.5157},
    "Nawanshahr": {"lat": 31.1245, "lon": 76.1162},
    "Pathankot": {"lat": 32.2746, "lon": 75.6521},
    "Patiala": {"lat": 30.3398, "lon": 76.3869},
    "Rupnagar": {"lat": 30.9645, "lon": 76.5271},
    "Sangrur": {"lat": 30.2450, "lon": 75.8450},
    "SAS Nagar (Mohali)": {"lat": 30.7046, "lon": 76.7179},
    "Tarn Taran": {"lat": 31.4519, "lon": 74.9278}
}
