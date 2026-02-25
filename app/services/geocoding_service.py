"""
Geocoding Service - Nominatim (OpenStreetMap) Reverse Geocoding
Free, no API key required. Rate limit: 1 request/second.
Converts GPS coordinates (lat, lon) → state + district automatically.
Works for ALL of India — no hardcoded district data needed.
"""

import httpx
from typing import Optional, Dict
from app.utils.logger import logger


class GeocodingService:
    """
    Reverse geocoding using Nominatim (OpenStreetMap).
    Converts GPS lat/lon → district + state for any location in India.
    """

    NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"

    HEADERS = {
        # Nominatim requires a User-Agent header
        "User-Agent": "KhetBuddyAPI/1.0 (agricultural yield prediction)"
    }

    async def reverse_geocode(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Given GPS coordinates, return district and state.

        Args:
            lat: Latitude from phone GPS
            lon: Longitude from phone GPS

        Returns:
            dict with 'district', 'state', 'country' or None on failure
        """
        try:
            params = {
                "lat": lat,
                "lon": lon,
                "format": "json",
                "addressdetails": 1,
                "zoom": 10,          # district-level zoom
                "accept-language": "en"
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.NOMINATIM_URL,
                    params=params,
                    headers=self.HEADERS,
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()

            address = data.get("address", {})

            # Nominatim uses different keys for district-level
            # Try multiple keys in order of preference
            district = (
                address.get("county") or          # most common for India
                address.get("state_district") or
                address.get("district") or
                address.get("city_district") or
                address.get("city") or
                address.get("town") or
                address.get("village") or
                "Unknown District"
            )

            state = address.get("state", "Unknown State")
            country = address.get("country", "Unknown")

            result = {
                "district": district,
                "state": state,
                "country": country,
                "raw_address": address
            }

            logger.info(f"Reverse geocoded ({lat}, {lon}) → {district}, {state}")
            return result

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during reverse geocoding: {e}")
            return None
        except Exception as e:
            logger.error(f"Error during reverse geocoding: {e}")
            return None

    def is_india(self, geocode_result: Dict) -> bool:
        """Check if the coordinates are within India"""
        country = geocode_result.get("country", "").lower()
        return "india" in country


# Global instance
geocoding_service = GeocodingService()
