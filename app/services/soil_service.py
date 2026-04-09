"""
Soil Service - Auto-fetch soil parameters from:
1. SoilGrids API (ISRIC) - Nitrogen + pH from GPS (free, no key)
2. Punjab District Averages - P, K, and fallback values (from Soil Health Cards)
3. Soil moisture estimation from weather data
"""

import httpx
from typing import Dict, Optional
from app.utils.logger import logger


# ─────────────────────────────────────────────────────────────────────────────
# Punjab District Soil Averages
# Source: India Soil Health Card data / ICAR Punjab averages
# Values: N (kg/ha), P (kg/ha), K (kg/ha), pH, moisture_pct
# ─────────────────────────────────────────────────────────────────────────────
PUNJAB_SOIL_AVERAGES: Dict[str, Dict] = {
    "Amritsar":           {"nitrogen": 210, "phosphorus": 18, "potassium": 135, "soil_ph": 7.9, "soil_moisture": 28},
    "Barnala":            {"nitrogen": 195, "phosphorus": 14, "potassium": 120, "soil_ph": 8.1, "soil_moisture": 24},
    "Bathinda":           {"nitrogen": 175, "phosphorus": 12, "potassium": 110, "soil_ph": 8.3, "soil_moisture": 20},
    "Faridkot":           {"nitrogen": 180, "phosphorus": 13, "potassium": 115, "soil_ph": 8.2, "soil_moisture": 22},
    "Fatehgarh Sahib":    {"nitrogen": 220, "phosphorus": 20, "potassium": 140, "soil_ph": 7.8, "soil_moisture": 30},
    "Fazilka":            {"nitrogen": 165, "phosphorus": 11, "potassium": 105, "soil_ph": 8.4, "soil_moisture": 18},
    "Ferozepur":          {"nitrogen": 185, "phosphorus": 14, "potassium": 120, "soil_ph": 8.1, "soil_moisture": 22},
    "Gurdaspur":          {"nitrogen": 225, "phosphorus": 22, "potassium": 150, "soil_ph": 7.5, "soil_moisture": 32},
    "Hoshiarpur":         {"nitrogen": 230, "phosphorus": 24, "potassium": 155, "soil_ph": 7.3, "soil_moisture": 35},
    "Jalandhar":          {"nitrogen": 215, "phosphorus": 19, "potassium": 138, "soil_ph": 7.8, "soil_moisture": 28},
    "Kapurthala":         {"nitrogen": 210, "phosphorus": 18, "potassium": 135, "soil_ph": 7.9, "soil_moisture": 27},
    "Ludhiana":           {"nitrogen": 220, "phosphorus": 21, "potassium": 142, "soil_ph": 7.7, "soil_moisture": 29},
    "Mansa":              {"nitrogen": 170, "phosphorus": 11, "potassium": 108, "soil_ph": 8.3, "soil_moisture": 20},
    "Moga":               {"nitrogen": 200, "phosphorus": 16, "potassium": 128, "soil_ph": 8.0, "soil_moisture": 25},
    "Muktsar":            {"nitrogen": 168, "phosphorus": 11, "potassium": 106, "soil_ph": 8.4, "soil_moisture": 19},
    "Nawanshahr":         {"nitrogen": 225, "phosphorus": 22, "potassium": 148, "soil_ph": 7.6, "soil_moisture": 33},
    "Pathankot":          {"nitrogen": 228, "phosphorus": 23, "potassium": 152, "soil_ph": 7.4, "soil_moisture": 34},
    "Patiala":            {"nitrogen": 205, "phosphorus": 17, "potassium": 130, "soil_ph": 7.9, "soil_moisture": 26},
    "Rupnagar":           {"nitrogen": 222, "phosphorus": 21, "potassium": 145, "soil_ph": 7.6, "soil_moisture": 31},
    "Sangrur":            {"nitrogen": 190, "phosphorus": 15, "potassium": 122, "soil_ph": 8.1, "soil_moisture": 23},
    "SAS Nagar":          {"nitrogen": 215, "phosphorus": 19, "potassium": 138, "soil_ph": 7.8, "soil_moisture": 28},
    "Mohali":             {"nitrogen": 215, "phosphorus": 19, "potassium": 138, "soil_ph": 7.8, "soil_moisture": 28},
    "Tarn Taran":         {"nitrogen": 208, "phosphorus": 17, "potassium": 133, "soil_ph": 7.9, "soil_moisture": 27},
}

# Punjab state-wide average (fallback if district not matched)
PUNJAB_DEFAULT_SOIL = {
    "nitrogen": 205,
    "phosphorus": 17,
    "potassium": 130,
    "soil_ph": 7.9,
    "soil_moisture": 26,
}


class SoilService:
    """
    Provides soil parameters for a GPS location.
    Combines SoilGrids API (for real N + pH) with
    Punjab district averages (for P, K fallback).
    """

    SOILGRIDS_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"

    async def get_soil_data(
        self,
        lat: float,
        lon: float,
        district: str = ""
    ) -> Dict:
        """
        Get soil parameters for a GPS location.
        Priority:
          1. SoilGrids API  -> N, pH (most accurate for specific GPS point)
          2. Punjab district averages -> P, K (district-level data)
          3. Punjab state default -> if district not recognized

        Args:
            lat: GPS latitude
            lon: GPS longitude
            district: district name from geocoding (for district averages)

        Returns:
            dict with nitrogen, phosphorus, potassium, soil_ph, soil_moisture
        """
        # Start with district / state averages as base
        base = self._get_district_averages(district)

        # Try to refine N and pH from SoilGrids API
        soilgrid_data = await self._fetch_soilgrids(lat, lon)
        if soilgrid_data:
            base.update(soilgrid_data)
            logger.info(f"SoilGrids data applied for ({lat}, {lon})")
        else:
            logger.info(f"SoilGrids unavailable — using district averages for {district}")

        return base

    def _get_district_averages(self, district: str) -> Dict:
        """
        Return Punjab district soil averages.
        Fuzzy-matches district name (handles variants like 'Ludhiana (West) Tahsil').
        """
        district_clean = district.lower()

        for key, values in PUNJAB_SOIL_AVERAGES.items():
            if key.lower() in district_clean or district_clean.startswith(key.lower()):
                logger.info(f"Matched district soil data: {key}")
                return values.copy()

        # Fallback to Punjab state average
        logger.warning(f"District '{district}' not in soil DB — using Punjab state average")
        return PUNJAB_DEFAULT_SOIL.copy()

    async def _fetch_soilgrids(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Fetch soil data from SoilGrids REST API (ISRIC).
        Returns nitrogen (kg/ha) and pH.
        Free, no API key required.
        """
        try:
            params = {
                "lon": lon,
                "lat": lat,
                "property": ["nitrogen", "phh2o"],
                "depth": "0-30cm",
                "value": "mean"
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.SOILGRIDS_URL,
                    params=params,
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()

            result = {}
            properties = data.get("properties", {}).get("layers", [])

            for layer in properties:
                name = layer.get("name")
                depths = layer.get("depths", [])
                if not depths:
                    continue
                # Get mean value at 0-30cm
                mean_val = depths[0].get("values", {}).get("mean")
                if mean_val is None:
                    continue

                if name == "nitrogen":
                    # SoilGrids nitrogen is in cg/kg, convert to kg/ha (×0.2 approx for 0-30cm)
                    result["nitrogen"] = round(mean_val * 0.2, 1)
                elif name == "phh2o":
                    # SoilGrids pH is ×10 encoded
                    result["soil_ph"] = round(mean_val / 10, 1)

            return result if result else None

        except httpx.HTTPError as e:
            logger.warning(f"SoilGrids HTTP error: {e}")
            return None
        except Exception as e:
            logger.warning(f"SoilGrids fetch failed: {e}")
            return None

    @staticmethod
    def estimate_soil_moisture(humidity: float, recent_rainfall: float) -> float:
        """
        Estimate soil moisture (%) from weather data.
        Simple heuristic: weighted combination of humidity and rainfall.

        Args:
            humidity: Current humidity (%)
            recent_rainfall: Recent rainfall mm (1h + 3h)

        Returns:
            Estimated soil moisture (%)
        """
        moisture = (humidity * 0.35) + min(recent_rainfall * 2.0, 25)
        return round(min(max(moisture, 5), 90), 1)

    @staticmethod
    def get_season_from_date() -> str:
        """
        Auto-detect agricultural season from current calendar month.
        Rabi (winter): October – March
        Kharif (monsoon): April – September
        """
        from datetime import date
        month = date.today().month
        return "Rabi" if month in [10, 11, 12, 1, 2, 3] else "Kharif"


# Global instance
soil_service = SoilService()
