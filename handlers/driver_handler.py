"""
    driver_handler.py — Driver flow: post ride, my trips, delete, availability toggle.
    NOW USES CALENDAR + HOUR PICKER INSTEAD OF TEXT INPUT.
    """
from __future__ import annotations

import logging
import re
from datetime import datetime

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes

from config import ROUTES, DEFAULT_LANG, t
from database import (
        can_post, add_ride, get_user_rides, delete_ride,
        get_ride_reservations, get_user_lang, is_user_blocked,
        set_available_now, upsert_user, log_event,
        get_driver_avg_rating,
    )
from services.notification_service import notify_travelers_of_new_ride
from handlers.start_handler import (
        route_keyboard, _lang, _clear_state,
    )
from handlers.calendar_handler import create_calendar_keyboard, create_hour_keyboard

logger = logging.getLogger(__name__)


    # ── /post_driver ─────────────────────────────────────────────

async def post_driver_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    upsert_user(user.id, user.first_name)
    if is_user_blocked(user.id):
        await update.message.reply_text(t("blocked_user", _lang(context)))
        return

    _clear_state(context)
    context.user_data["state"] = "awaiting_role"
    context.user_data["role"] = "driver"
    lang = _lang(context)
    await update.message.reply_text(
        t("driver_mode", lang),
        parse_mode="Markdown",
        reply_markup=route_keyboard(),
    )


    # ── /my_trips (driver side) ──────────────────────────────────

async def my_trips_driver(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show driver's posted rides and reservation status."""
    user_id = update.effective_user.id
    lang = _lang(context)
    rides = get_user_rides(user_id)

    if not rides:
        await update.message.reply_text(t("no_active_posts", lang))
        return

    lines = ["📋 *Your posted rides:*\n"]
    for r in rides:
        try:
            dd = datetime.strptime(r["date"], "%Y-%m-%d").strftime("%d %B %Y")
        except ValueError:
            dd = r["date"]
        reservations = get_ride_reservations(r["id"])
        approved = sum(1 for rv in reservations if rv["status"] == "approved")
        pending = sum(1 for rv in reservations if rv["status"] == "pending")
        lines.append(
            f"🚗 *{r['route']}*\n"
            f" 📅 {dd} ⏰ {r['time']}\n"
            f" 💺 {r['seats_available']}/{r['seats_total']} seats left\n"
            f" ✅ {approved} approved · ⏳ {pending} pending\n"
            f" /delete\\_{r['id']}\n"
        )
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ── /available ───────────────────────────────────────────────

async def available_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggle driver availability status."""
    user_id = update.effective_user.id
    lang = _lang(context)
    from database import get_connection
    conn = get_connection()
    row = conn.execute("SELECT available_now FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    current = bool(row and row["available_now"]) if row else False
    new_val = not current
    set_available_now(user_id, new_val)

    if new_val:
        await update.message.reply_text(t("driver_available_now", lang), parse_mode="Markdown")
    else:
        await update.message.reply_text(t("driver_unavailable", lang), parse_mode="Markdown")


# ── /delete_<id> ─────────────────────────────────────────────

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()
    lang = _lang(context)
    match = re.match(r"^/delete_(\d+)$", text)
    if not match:
        return
    ride_id = int(match.group(1))
    user_id = update.effective_user.id

    if delete_ride(ride_id, user_id):
        await update.message.reply_text(t("post_deleted", lang))
    else:
        await update.message.reply_text(t("post_not_found", lang))


# ═══════════════════════════════════════════════════════════════
# Text-state handlers called from the main router
# ═══════════════════════════════════════════════════════════════

async def handle_driver_route(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()
    lang = _lang(context)
    if text not in ROUTES:
        await update.message.reply_text(t("choose_route_btn", lang), reply_markup=route_keyboard())
        return
    context.user_data["route"] = text
    context.user_data["state"] = "driver_awaiting_date_selection"

    now = datetime.utcnow()
    keyboard = create_calendar_keyboard(now.year, now.month)

    await update.message.reply_text(
        "📅 Select your travel date:",
        reply_markup=keyboard,
    )


async def handle_driver_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Deprecated - date selection now via calendar_handler"""
    pass


async def handle_driver_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Deprecated - time selection now via calendar_handler"""
    pass


async def handle_driver_seats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()
    lang = _lang(context)
    if not text.isdigit() or not (1 <= int(text) <= 10):
        await update.message.reply_text(t("number_1_10", lang))
        return

    seats = int(text)
    user = update.effective_user
    user_id = user.id
    name = user.first_name or "Driver"

    if not can_post(user_id):
        await update.message.reply_text(t("spam_limit", lang))
        _clear_state(context)
        return

    route = context.user_data.get("route")
    date = context.user_data.get("date")
    time_val = context.user_data.get("time")

    if not all([route, date, time_val]):
        await update.message.reply_text("❌ Error: Missing ride data. Please try again.")
        _clear_state(context)
        return

    ride_id = add_ride(user_id, name, route, date, time_val, seats)
    log_event("ride_posted", user_id, route)

    display_date = datetime.strptime(date, "%Y-%m-%d").strftime("%d %B %Y")
    avg = get_driver_avg_rating(user_id)
    rating_str = f"⭐ {avg}/5" if avg else "No ratings yet"

    await update.message.reply_text(
        f"✅ Ride posted!\n\n"
        f"🚗 Driver: {name}\n"
        f"📍 Route: {route}\n"
        f"📅 Date: {display_date}\n"
        f"⏰ Time: {time_val}\n"
        f"💺 Seats: {seats}\n"
        f"Rating: {rating_str}\n\n"
        f"Travelers can find your ride now.",
        parse_mode="Markdown",
    )

    await notify_travelers_of_new_ride(
        context, route, date, name, display_date, time_val, seats,
    )
    _clear_state(context)
