"""
location_service.py — GPS / distance helpers.

Provides haversine distance calculation and utility to sort
rides by proximity to a given traveler location.
"""

import math


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in km between two coordinate pairs."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def sort_by_distance(rides: list[dict], lat: float, lon: float) -> list[dict]:
    """
    Sort rides by distance from (lat, lon).
    Rides without coordinates are placed at the end.
    """
    def _key(ride: dict) -> float:
        rlat, rlon = ride.get("latitude"), ride.get("longitude")
        if rlat is None or rlon is None:
            return float("inf")
        return haversine(lat, lon, rlat, rlon)

    return sorted(rides, key=_key)
