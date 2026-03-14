
"""
database.py — SQLite database layer for RideMatch bot.

Manages schema creation, CRUD for rides / reservations / ratings / users,
cleanup of expired data, and analytics queries.
"""
from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timedelta

from config import DB_PATH, RIDE_EXPIRY_HOURS, MAX_ACTIVE_POSTS

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# Connection helper
# ═══════════════════════════════════════════════════════════════

def get_connection() -> sqlite3.Connection:
    """
    Create a safe SQLite connection for concurrent Telegram updates.
    """

    conn = sqlite3.connect(
        DB_PATH,
        check_same_thread=False,
        timeout=30
    )

    conn.row_factory = sqlite3.Row

    # safer for cloud deployments
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.execute("PRAGMA foreign_keys=ON")

    return conn


# ═══════════════════════════════════════════════════════════════
# Schema initialisation
# ═══════════════════════════════════════════════════════════════

def init_db() -> None:
    """Create all tables if they do not exist."""
    conn = get_connection()

    # -- users (language pref, blocked flag, availability) --
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id       INTEGER PRIMARY KEY,
            username      TEXT,
            lang          TEXT    DEFAULT 'en',
            is_blocked    INTEGER DEFAULT 0,
            available_now INTEGER DEFAULT 0,
            latitude      REAL,
            longitude     REAL,
            created_at    TEXT    NOT NULL
        )
        """
    )

    # -- rides (upgraded: seats_total / seats_available, location) --
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS rides (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_id       INTEGER NOT NULL,
            username        TEXT,
            route           TEXT    NOT NULL,
            date            TEXT    NOT NULL,
            time            TEXT,
            seats_total     INTEGER NOT NULL DEFAULT 1,
            seats_available INTEGER NOT NULL DEFAULT 1,
            latitude        REAL,
            longitude       REAL,
            created_at      TEXT    NOT NULL
        )
        """
    )

    # -- reservations --
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reservations (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            ride_id        INTEGER NOT NULL,
            traveler_id    INTEGER NOT NULL,
            seats_reserved INTEGER NOT NULL DEFAULT 1,
            status         TEXT    NOT NULL DEFAULT 'pending',
            created_at     TEXT    NOT NULL,
            FOREIGN KEY (ride_id) REFERENCES rides(id) ON DELETE CASCADE
        )
        """
    )

    # -- ratings --
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ratings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_id   INTEGER NOT NULL,
            traveler_id INTEGER NOT NULL,
            ride_id     INTEGER,
            rating      INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
            comment     TEXT,
            created_at  TEXT    NOT NULL
        )
        """
    )

    # -- search_requests (for smart notifications) --
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS search_requests (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            route       TEXT    NOT NULL,
            date        TEXT    NOT NULL,
            passengers  INTEGER NOT NULL DEFAULT 1,
            created_at  TEXT    NOT NULL
        )
        """
    )

    # -- reports --
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            reporter_id   INTEGER NOT NULL,
            reported_id   INTEGER,
            ride_id       INTEGER,
            reason        TEXT,
            created_at    TEXT    NOT NULL
        )
        """
    )

    # -- analytics_events (generic event log) --
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS analytics (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            event      TEXT    NOT NULL,
            user_id    INTEGER,
            route      TEXT,
            extra      TEXT,
            created_at TEXT    NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()
    logger.info("Database initialised.")


# ═══════════════════════════════════════════════════════════════
# User helpers
# ═══════════════════════════════════════════════════════════════

def upsert_user(user_id: int, username: str | None = None, lang: str = "en") -> None:
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO users (user_id, username, lang, created_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET username=excluded.username
        """,
        (user_id, username, lang, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def set_user_lang(user_id: int, lang: str) -> None:
    conn = get_connection()
    conn.execute("UPDATE users SET lang=? WHERE user_id=?", (lang, user_id))
    conn.commit()
    conn.close()


def get_user_lang(user_id: int) -> str:
    conn = get_connection()
    row = conn.execute("SELECT lang FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return row["lang"] if row else "en"


def is_user_blocked(user_id: int) -> bool:
    conn = get_connection()
    row = conn.execute("SELECT is_blocked FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return bool(row and row["is_blocked"])


def block_user(user_id: int) -> None:
    conn = get_connection()
    conn.execute("UPDATE users SET is_blocked=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()


def unblock_user(user_id: int) -> None:
    conn = get_connection()
    conn.execute("UPDATE users SET is_blocked=0 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()


def set_available_now(user_id: int, available: bool) -> None:
    conn = get_connection()
    conn.execute("UPDATE users SET available_now=? WHERE user_id=?", (int(available), user_id))
    conn.commit()
    conn.close()


def set_user_location(user_id: int, lat: float, lon: float) -> None:
    conn = get_connection()
    conn.execute("UPDATE users SET latitude=?, longitude=? WHERE user_id=?", (lat, lon, user_id))
    conn.commit()
    conn.close()


def get_all_user_ids() -> list[int]:
    """Return all non-blocked user IDs (for broadcast)."""
    conn = get_connection()
    rows = conn.execute("SELECT user_id FROM users WHERE is_blocked=0").fetchall()
    conn.close()
    return [r["user_id"] for r in rows]


# ═══════════════════════════════════════════════════════════════
# Ride CRUD
# ═══════════════════════════════════════════════════════════════

def _cutoff() -> str:
    return (datetime.utcnow() - timedelta(hours=RIDE_EXPIRY_HOURS)).isoformat()


def count_active_posts(user_id: int) -> int:
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) AS cnt FROM rides WHERE driver_id=? AND created_at>?",
        (user_id, _cutoff()),
    ).fetchone()
    conn.close()
    return row["cnt"]


def can_post(user_id: int) -> bool:
    return count_active_posts(user_id) < MAX_ACTIVE_POSTS


def add_ride(driver_id: int, username: str, route: str,
             date: str, time: str, seats: int,
             lat: float | None = None, lon: float | None = None) -> int:
    conn = get_connection()
    cur = conn.execute(
        """
        INSERT INTO rides (driver_id, username, route, date, time,
                           seats_total, seats_available, latitude, longitude, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (driver_id, username, route, date, time, seats, seats,
         lat, lon, datetime.utcnow().isoformat()),
    )
    conn.commit()
    ride_id = cur.lastrowid
    conn.close()
    return ride_id


def get_ride(ride_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM rides WHERE id=?", (ride_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def find_drivers(route: str, date: str, passengers: int) -> list[dict]:
    """Return matching driver rides with enough seats, not expired."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT r.*, u.available_now,
               COALESCE((SELECT ROUND(AVG(rt.rating),1) FROM ratings rt WHERE rt.driver_id=r.driver_id), 0) AS avg_rating
        FROM rides r
        LEFT JOIN users u ON u.user_id = r.driver_id
        WHERE r.route = ?
          AND r.date = ?
          AND r.seats_available >= ?
          AND r.created_at > ?
        ORDER BY u.available_now DESC, r.time ASC
        """,
        (route, date, passengers, _cutoff()),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def find_drivers_time_window(route: str, date: str, passengers: int,
                              ref_time: str | None, tolerance_h: int = 3) -> list[dict]:
    """
    Same as find_drivers but optionally filters by ±tolerance_h around ref_time.
    If ref_time is None behaves like find_drivers.
    """
    base = find_drivers(route, date, passengers)
    if not ref_time:
        return base

    try:
        ref_minutes = int(ref_time.split(":")[0]) * 60 + int(ref_time.split(":")[1])
    except (ValueError, IndexError):
        return base

    tol = tolerance_h * 60
    filtered = []
    for d in base:
        if not d.get("time"):
            filtered.append(d)
            continue
        try:
            dm = int(d["time"].split(":")[0]) * 60 + int(d["time"].split(":")[1])
        except (ValueError, IndexError):
            filtered.append(d)
            continue
        if abs(dm - ref_minutes) <= tol:
            filtered.append(d)
    return filtered


def get_user_rides(user_id: int) -> list[dict]:
    """Active driver rides for a user."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM rides WHERE driver_id=? AND created_at>? ORDER BY created_at DESC",
        (user_id, _cutoff()),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_ride(ride_id: int, user_id: int) -> bool:
    conn = get_connection()
    cur = conn.execute("DELETE FROM rides WHERE id=? AND driver_id=?", (ride_id, user_id))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted


def admin_delete_ride(ride_id: int) -> bool:
    conn = get_connection()
    cur = conn.execute("DELETE FROM rides WHERE id=?", (ride_id,))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted


# ═══════════════════════════════════════════════════════════════
# Reservations
# ═══════════════════════════════════════════════════════════════

def create_reservation(ride_id: int, traveler_id: int, seats: int) -> int:
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO reservations (ride_id, traveler_id, seats_reserved, status, created_at) VALUES (?,?,?,'pending',?)",
        (ride_id, traveler_id, seats, datetime.utcnow().isoformat()),
    )
    conn.commit()
    res_id = cur.lastrowid
    conn.close()
    return res_id


def approve_reservation(reservation_id: int) -> dict | None:
    """Approve reservation and decrease seats_available. Returns reservation dict or None."""
    conn = get_connection()
    res = conn.execute("SELECT * FROM reservations WHERE id=? AND status='pending'", (reservation_id,)).fetchone()
    if not res:
        conn.close()
        return None
    res = dict(res)
    ride = conn.execute("SELECT * FROM rides WHERE id=?", (res["ride_id"],)).fetchone()
    if not ride or ride["seats_available"] < res["seats_reserved"]:
        conn.close()
        return None
    conn.execute("UPDATE reservations SET status='approved' WHERE id=?", (reservation_id,))
    conn.execute(
        "UPDATE rides SET seats_available = seats_available - ? WHERE id=?",
        (res["seats_reserved"], res["ride_id"]),
    )
    conn.commit()
    conn.close()
    return res


def reject_reservation(reservation_id: int) -> dict | None:
    conn = get_connection()
    res = conn.execute("SELECT * FROM reservations WHERE id=? AND status='pending'", (reservation_id,)).fetchone()
    if not res:
        conn.close()
        return None
    conn.execute("UPDATE reservations SET status='rejected' WHERE id=?", (reservation_id,))
    conn.commit()
    conn.close()
    return dict(res)


def get_reservation(reservation_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM reservations WHERE id=?", (reservation_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_reservations(user_id: int) -> list[dict]:
    """Reservations made BY a traveler (with ride info)."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT res.*, r.route, r.date, r.time, r.username AS driver_username
        FROM reservations res
        JOIN rides r ON r.id = res.ride_id
        WHERE res.traveler_id = ?
        ORDER BY res.created_at DESC
        """,
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_ride_reservations(ride_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM reservations WHERE ride_id=? ORDER BY created_at DESC",
        (ride_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_approved_reservations_for_completion(cutoff_iso: str) -> list[dict]:
    """
    Return approved reservations whose ride date+time has passed
    and which haven't been rated yet.
    """
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT res.*, r.route, r.date, r.time, r.driver_id, r.username AS driver_username
        FROM reservations res
        JOIN rides r ON r.id = res.ride_id
        WHERE res.status = 'approved'
          AND (r.date || 'T' || COALESCE(r.time,'23:59')) < ?
          AND res.id NOT IN (SELECT DISTINCT rt.ride_id FROM ratings rt WHERE rt.ride_id IS NOT NULL)
        LIMIT 50
        """,
        (cutoff_iso,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════════
# Ratings
# ═══════════════════════════════════════════════════════════════

def add_rating(driver_id: int, traveler_id: int, ride_id: int | None,
               rating: int, comment: str | None = None) -> int:
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO ratings (driver_id, traveler_id, ride_id, rating, comment, created_at) VALUES (?,?,?,?,?,?)",
        (driver_id, traveler_id, ride_id, rating, comment, datetime.utcnow().isoformat()),
    )
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return rid


def get_driver_avg_rating(driver_id: int) -> float:
    conn = get_connection()
    row = conn.execute(
        "SELECT ROUND(AVG(rating),1) AS avg FROM ratings WHERE driver_id=?",
        (driver_id,),
    ).fetchone()
    conn.close()
    return row["avg"] if row and row["avg"] else 0.0


# ═══════════════════════════════════════════════════════════════
# Search requests (smart notifications)
# ═══════════════════════════════════════════════════════════════

def save_search_request(user_id: int, route: str, date: str, passengers: int) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO search_requests (user_id, route, date, passengers, created_at) VALUES (?,?,?,?,?)",
        (user_id, route, date, passengers, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def find_matching_search_requests(route: str, date: str) -> list[dict]:
    """Return unique user_ids who searched for this route+date."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT user_id FROM search_requests WHERE route=? AND date=? AND created_at>?",
        (route, date, _cutoff()),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════════
# Reports
# ═══════════════════════════════════════════════════════════════

def save_report(reporter_id: int, reported_id: int | None,
                ride_id: int | None, reason: str) -> int:
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO reports (reporter_id, reported_id, ride_id, reason, created_at) VALUES (?,?,?,?,?)",
        (reporter_id, reported_id, ride_id, reason, datetime.utcnow().isoformat()),
    )
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return rid


# ═══════════════════════════════════════════════════════════════
# Analytics
# ═══════════════════════════════════════════════════════════════

def log_event(event: str, user_id: int | None = None,
              route: str | None = None, extra: str | None = None) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO analytics (event, user_id, route, extra, created_at) VALUES (?,?,?,?,?)",
        (event, user_id, route, extra, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def get_stats() -> dict:
    """Return aggregate statistics for admin dashboard."""
    conn = get_connection()
    stats = {}
    stats["total_rides"] = conn.execute("SELECT COUNT(*) FROM rides").fetchone()[0]
    stats["active_rides"] = conn.execute(
        "SELECT COUNT(*) FROM rides WHERE created_at>?", (_cutoff(),)
    ).fetchone()[0]
    stats["total_reservations"] = conn.execute("SELECT COUNT(*) FROM reservations").fetchone()[0]
    stats["approved_reservations"] = conn.execute(
        "SELECT COUNT(*) FROM reservations WHERE status='approved'"
    ).fetchone()[0]
    stats["total_users"] = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    stats["total_ratings"] = conn.execute("SELECT COUNT(*) FROM ratings").fetchone()[0]
    stats["total_reports"] = conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]

    # Most popular route
    row = conn.execute(
        "SELECT route, COUNT(*) AS cnt FROM rides GROUP BY route ORDER BY cnt DESC LIMIT 1"
    ).fetchone()
    stats["popular_route"] = row["route"] if row else "N/A"

    # Busiest hour
    row = conn.execute(
        "SELECT SUBSTR(time,1,2) AS hr, COUNT(*) AS cnt FROM rides WHERE time IS NOT NULL GROUP BY hr ORDER BY cnt DESC LIMIT 1"
    ).fetchone()
    stats["busiest_hour"] = f"{row['hr']}:00" if row else "N/A"

    conn.close()
    return stats


# ═══════════════════════════════════════════════════════════════
# Cleanup
# ═══════════════════════════════════════════════════════════════

def cleanup_expired_rides() -> int:
    conn = get_connection()
    cur = conn.execute("DELETE FROM rides WHERE created_at <= ?", (_cutoff(),))
    # Also clean old search requests
    conn.execute("DELETE FROM search_requests WHERE created_at <= ?", (_cutoff(),))
    conn.commit()
    deleted = cur.rowcount
    conn.close()
    return deleted
