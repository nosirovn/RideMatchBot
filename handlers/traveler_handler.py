"""
traveler_handler.py — Traveler flow: find ride, reserve seat, rate driver, report.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime

from telegram import (
    Update,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from config import ROUTES, DEFAULT_LANG, t, TIME_MATCH_TOLERANCE_HOURS
from database import (
    save_search_request,
    get_ride,
    get_user_reservations,
    get_user_lang,
    is_user_blocked,
    upsert_user,
    log_event,
    add_rating,
    get_driver_avg_rating,
    save_report,
)
from services.ai_matching_service import rank_rides
from services.reservation_service import request_seat, handle_approve, handle_reject
from services.notification_service import (
    notify_driver_reservation,
    notify_reservation_result,
)
from handlers.start_handler import (
    route_keyboard, DATE_PATTERN, TIME_PATTERN,
    _lang, _clear_state,
)

logger = logging.getLogger(__name__)


# ── /find_ride ───────────────────────────────────────────────

async def find_ride_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    upsert_user(user.id, user.username)
    if is_user_blocked(user.id):
        await update.message.reply_text(t("blocked_user", _lang(context)))
        return

    _clear_state(context)
    context.user_data["state"] = "traveler_awaiting_route"
    context.user_data["role"] = "traveler"
    lang = _lang(context)
    await update.message.reply_text(
        t("traveler_mode", lang),
        parse_mode="Markdown",
        reply_markup=route_keyboard(),
    )


# ── /my_trips (traveler side) ────────────────────────────────

async def my_trips_traveler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    lang = _lang(context)
    reservations = get_user_reservations(user_id)

    if not reservations:
        await update.message.reply_text("You have no reservations yet.")
        return

    lines = ["📋 *Your reservations:*\n"]
    for rv in reservations:
        status_icon = {"pending": "⏳", "approved": "✅", "rejected": "❌"}.get(rv["status"], "❓")
        try:
            dd = datetime.strptime(rv["date"], "%Y-%m-%d").strftime("%d %B %Y")
        except ValueError:
            dd = rv["date"]
        lines.append(
            f"{status_icon} *{rv['route']}*\n"
            f"  📅 {dd}  ⏰ {rv.get('time', '-')}\n"
            f"  🚗 Driver: @{rv.get('driver_username', '?')}\n"
            f"  💺 Seats: {rv['seats_reserved']}  Status: {rv['status']}\n"
        )
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ── /my_trips unified router ────────────────────────────────

async def my_trips_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show both driver and traveler trips."""
    from handlers.driver_handler import my_trips_driver
    await my_trips_driver(update, context)
    await my_trips_traveler(update, context)


# ── /report ──────────────────────────────────────────────────

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = _lang(context)
    _clear_state(context)
    context.user_data["state"] = "awaiting_report_text"
    await update.message.reply_text(t("report_prompt", lang))


async def handle_report_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()
    lang = _lang(context)
    user_id = update.effective_user.id
    save_report(user_id, None, None, text)
    log_event("report", user_id, extra=text[:200])
    await update.message.reply_text(t("report_saved", lang))
    _clear_state(context)


# ═══════════════════════════════════════════════════════════════
# Traveler text-state handlers
# ═══════════════════════════════════════════════════════════════

async def handle_traveler_route(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()
    lang = _lang(context)
    if text not in ROUTES:
        await update.message.reply_text(t("choose_route_btn", lang), reply_markup=route_keyboard())
        return
    context.user_data["route"] = text
    context.user_data["state"] = "traveler_awaiting_date"
    await update.message.reply_text(t("enter_date", lang), reply_markup=ReplyKeyboardRemove())


async def handle_traveler_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()
    lang = _lang(context)
    m = DATE_PATTERN.match(text)
    if not m:
        await update.message.reply_text(t("invalid_date", lang))
        return
    day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
    try:
        parsed = datetime(year, month, day)
    except ValueError:
        await update.message.reply_text(t("invalid_date", lang))
        return
    if parsed.date() < datetime.utcnow().date():
        await update.message.reply_text(t("past_date", lang))
        return
    context.user_data["date"] = parsed.strftime("%Y-%m-%d")
    context.user_data["state"] = "traveler_awaiting_passengers"
    await update.message.reply_text(t("enter_passengers", lang))


async def handle_traveler_passengers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()
    lang = _lang(context)
    if not text.isdigit() or not (1 <= int(text) <= 10):
        await update.message.reply_text(t("number_1_10", lang))
        return

    passengers = int(text)
    context.user_data["passengers"] = passengers
    user = update.effective_user
    route = context.user_data["route"]
    date = context.user_data["date"]

    # Save the search request for smart notifications
    save_search_request(user.id, route, date, passengers)
    log_event("search", user.id, route)

    # Use AI matching service
    matches = rank_rides(
        route=route,
        date=date,
        passengers=passengers,
        tolerance_h=TIME_MATCH_TOLERANCE_HOURS,
    )

    display_date = datetime.strptime(date, "%Y-%m-%d").strftime("%d %B %Y")

    if not matches:
        await update.message.reply_text(
            t("no_rides_found", lang, route=route, date=display_date),
            parse_mode="Markdown",
        )
        _clear_state(context)
        return

    # Show results with inline buttons
    for i, d in enumerate(matches[:10]):  # limit to 10 results
        try:
            dd = datetime.strptime(d["date"], "%Y-%m-%d").strftime("%d %B %Y")
        except ValueError:
            dd = d["date"]
        avg = d.get("avg_rating", 0)
        rating_str = f"⭐ {avg}/5" if avg else "No ratings"
        avail = "🟢 Available now" if d.get("available_now") else ""
        dist = f"📏 {d['distance_km']} km" if d.get("distance_km") else ""

        card = (
            f"🚗 Driver: @{d['username']}\n"
            f"📍 Route: {d['route']}\n"
            f"📅 Date: {dd}\n"
            f"⏰ Time: {d['time']}\n"
            f"💺 Seats available: {d['seats_available']}\n"
            f"Rating: {rating_str}\n"
            f"{avail}\n{dist}"
        ).strip()

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                f"🪑 Request {passengers} seat(s)",
                callback_data=f"reserve:{d['id']}:{passengers}",
            )]
        ])
        await update.message.reply_text(card, reply_markup=keyboard)

    _clear_state(context)


# ═══════════════════════════════════════════════════════════════
# Inline callback handlers (reservation + rating)
# ═══════════════════════════════════════════════════════════════

async def reservation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle reserve:<ride_id>:<seats> callback."""
    query = update.callback_query
    await query.answer()
    data = query.data  # "reserve:42:2"
    parts = data.split(":")
    if len(parts) != 3:
        return
    ride_id, seats = int(parts[1]), int(parts[2])
    traveler = update.effective_user
    lang = get_user_lang(traveler.id)

    res_id = request_seat(ride_id, traveler.id, seats)
    if res_id is None:
        await query.edit_message_text("❌ Not enough seats available or ride not found.")
        return

    ride = get_ride(ride_id)
    try:
        dd = datetime.strptime(ride["date"], "%Y-%m-%d").strftime("%d %B %Y")
    except (ValueError, TypeError):
        dd = ride["date"] if ride else "?"

    await query.edit_message_text(
        f"✅ Reservation request sent!\n"
        f"Waiting for driver approval…"
    )

    # Notify the driver
    await notify_driver_reservation(
        context,
        driver_id=ride["driver_id"],
        reservation_id=res_id,
        traveler_username=traveler.username or "no_username",
        route=ride["route"],
        display_date=dd,
        seats=seats,
    )


async def reservation_decision_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle res_approve:<id> / res_reject:<id> callback from driver."""
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("res_approve:"):
        res_id = int(data.split(":")[1])
        res = handle_approve(res_id)
        if not res:
            await query.edit_message_text("❌ Could not approve (already handled or not enough seats).")
            return
        ride = get_ride(res["ride_id"])
        driver_username = ride["username"] if ride else "?"
        try:
            dd = datetime.strptime(ride["date"], "%Y-%m-%d").strftime("%d %B %Y")
        except (ValueError, TypeError):
            dd = "?"
        await query.edit_message_text(f"✅ Reservation #{res_id} approved.")
        await notify_reservation_result(
            context, res["traveler_id"], True,
            driver_username, ride["route"] if ride else "?",
            dd, ride["time"] if ride else "?",
        )

    elif data.startswith("res_reject:"):
        res_id = int(data.split(":")[1])
        res = handle_reject(res_id)
        if not res:
            await query.edit_message_text("❌ Could not reject (already handled).")
            return
        ride = get_ride(res["ride_id"])
        driver_username = ride["username"] if ride else "?"
        try:
            dd = datetime.strptime(ride["date"], "%Y-%m-%d").strftime("%d %B %Y")
        except (ValueError, TypeError):
            dd = "?"
        await query.edit_message_text(f"❌ Reservation #{res_id} rejected.")
        await notify_reservation_result(
            context, res["traveler_id"], False,
            driver_username, ride["route"] if ride else "?",
            dd, ride["time"] if ride else "?",
        )


# ═══════════════════════════════════════════════════════════════
# Rating flow
# ═══════════════════════════════════════════════════════════════

async def rate_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle rate:<driver_id>:<ride_id> callback — ask for 1–5 stars."""
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")
    if len(parts) != 3:
        return
    driver_id, ride_id = int(parts[1]), int(parts[2])
    context.user_data["rating_driver_id"] = driver_id
    context.user_data["rating_ride_id"] = ride_id
    context.user_data["state"] = "awaiting_rating"

    stars_kb = InlineKeyboardMarkup([[
        InlineKeyboardButton(f"{'⭐' * i}", callback_data=f"stars:{i}")
        for i in range(1, 6)
    ]])
    lang = _lang(context)
    await query.edit_message_text(t("rate_prompt", lang), reply_markup=stars_kb)


async def stars_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle stars:N callback."""
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")
    if len(parts) != 2:
        return
    rating = int(parts[1])
    driver_id = context.user_data.pop("rating_driver_id", None)
    ride_id = context.user_data.pop("rating_ride_id", None)
    if not driver_id:
        return
    traveler_id = update.effective_user.id
    add_rating(driver_id, traveler_id, ride_id, rating)
    lang = _lang(context)
    await query.edit_message_text(t("rating_saved", lang, rating=rating))
    context.user_data.pop("state", None)
