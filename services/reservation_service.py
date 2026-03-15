"""
reservation_service.py — Seat reservation business logic.
"""
from __future__ import annotations

import logging
from database import (
    create_reservation,
    approve_reservation,
    reject_reservation,
    get_reservation,
    get_ride,
)

logger = logging.getLogger(__name__)


def request_seat(ride_id: int, traveler_id: int, seats: int) -> int | None:
    """
    Create a pending reservation.
    Returns reservation ID or None if ride doesn't exist / not enough seats.
    """
    ride = get_ride(ride_id)
    if not ride:
        logger.warning("Reservation attempted for non-existent ride %d", ride_id)
        return None
    if ride["seats_available"] < seats:
        return None
    return create_reservation(ride_id, traveler_id, seats)


def handle_approve(reservation_id: int) -> dict | None:
    """Approve reservation, decreasing available seats."""
    return approve_reservation(reservation_id)


def handle_reject(reservation_id: int) -> dict | None:
    """Reject reservation."""
    return reject_reservation(reservation_id)
