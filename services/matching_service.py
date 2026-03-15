"""
matching_service.py — Core ride-matching logic.

Provides smart matching that prioritises available-now drivers,
higher ratings, closer departure time, and optional geo-distance.
"""
from __future__ import annotations

import math
import logging
from datetime import datetime

from database import find_drivers, find_drivers_time_window, get_driver_avg_rating

logger = logging.getLogger(__name__)


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in km between two lat/lon points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _time_diff_minutes(t1: str | None, t2: str | None) -> int:
    """Return absolute difference in minutes between two HH:MM strings."""
    if not t1 or not t2:
        return 0
    try:
        m1 = int(t1.split(":")[0]) * 60 + int(t1.split(":")[1])
        m2 = int(t2.split(":")[0]) * 60 + int(t2.split(":")[1])
        return abs(m1 - m2)
    except (ValueError, IndexError):
        return 0


def smart_match(
    route: str,
    date: str,
    passengers: int,
    preferred_time: str | None = None,
    traveler_lat: float | None = None,
    traveler_lon: float | None = None,
    tolerance_h: int = 3,
) -> list[dict]:
    """
    Return matching rides sorted by a composite score:
      1. available_now  (bool, higher = better)
      2. avg_rating     (0-5, higher = better)
      3. time_proximity (lower diff = better)
      4. geo distance   (lower = better, optional)
    """
    rides = find_drivers_time_window(route, date, passengers, preferred_time, tolerance_h)

    for r in rides:
        score = 0.0
        # Availability bonus
        if r.get("available_now"):
            score += 100

        # Rating (0–5 → 0–50)
        avg = r.get("avg_rating") or 0
        score += avg * 10

        # Time proximity bonus (max 30 points for exact match)
        tdiff = _time_diff_minutes(preferred_time, r.get("time"))
        score += max(0, 30 - tdiff / 6)

        # Seats surplus bonus (more spare seats = slightly better)
        score += min(r.get("seats_available", 0), 5)

        # Distance penalty (only if both sides have coords)
        if (traveler_lat is not None and traveler_lon is not None
                and r.get("latitude") is not None and r.get("longitude") is not None):
            km = _haversine(traveler_lat, traveler_lon, r["latitude"], r["longitude"])
            score -= min(km, 50)  # cap penalty at 50
            r["distance_km"] = round(km, 1)

        r["match_score"] = round(score, 1)

    rides.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    return rides
