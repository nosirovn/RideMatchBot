"""
ai_matching_service.py — Smart / AI-driven ride ranking.

Uses a composite scoring model to rank rides for travelers.
Factors: availability, driver rating, time proximity, distance, seat surplus.
"""
from __future__ import annotations

import logging
from services.matching_service import smart_match

logger = logging.getLogger(__name__)


def rank_rides(
    route: str,
    date: str,
    passengers: int,
    preferred_time: str | None = None,
    traveler_lat: float | None = None,
    traveler_lon: float | None = None,
    tolerance_h: int = 3,
) -> list[dict]:
    """
    Delegate to smart_match and return ranked results.
    This service layer exists so future ML models can be plugged in
    without changing handler code.
    """
    return smart_match(
        route=route,
        date=date,
        passengers=passengers,
        preferred_time=preferred_time,
        traveler_lat=traveler_lat,
        traveler_lon=traveler_lon,
        tolerance_h=tolerance_h,
    )
