"""
traveler_handler.py – Traveler flow: find ride, reserve seats, rate driver, report.
"""
from __future__ import annotations

import logging
from datetime import datetime

from telegram import (
    Update,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from config import ROUTES, DEFAULT_LANG, t
from database import (
    save_search_request,
    get_ride,
    get_user_reservations,
    get_user_rides,
    get_user_lang,
    is_user_blocked,
    upsert_user,
    log_event,
    add_rating,
    get_driver_avg_rating,
    save_report,
    get_ride_reservations,
)
from services.ai_matching_service import rank_rides
from services.reservation_service import request_seat, handle_approve, handle_reject
from services.notification_service import (
    notify_driver_reservation,
    notify_reservation_result,
)
from handlers.start_handler import (
    DATE_PATTERN,
    _lang, _clear_state, main_menu_keyboard, route_keyboard,
)
from handlers.calendar_handler import create_calendar_keyboard

logger = logging.getLogger(__name__)


# — /find_ride ——————————————————————————————————————————————————

async def find_ride_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start the traveler search flow."""
    user = update.effective_user
    upsert_user(user.id, user.first_name)

    if is_user_blocked(user.id):
        await update.message.reply_text(t("blocked_user", _lang(context)))
        return

    _clear_state(context)
    context.user_data["role"] = "traveler"
    context.user_data["state"] = "traveler_awaiting_route"
    lang = _lang(context)
    await update.message.reply_text(
        t("traveler_mode", lang),
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(lang),
    )


async def handle_traveler_route(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Traveler selects route, then asked for date."""
    text = update.message.text.strip()
    lang = _lang(context)
    if text not in ROUTES:
        await update.message.reply_text(
            t("choose_route_btn", lang), reply_markup=main_menu_keyboard()
        )
        return
    context.user_data["route"] = text
    context.user_data["state"] = "traveler_awaiting_date_selection"

    now = datetime.utcnow()
    keyboard = create_calendar_keyboard(now.year, now.month)
    await update.message.reply_text(
        "📅 *Select a Date*",
        reply_markup=keyboard,
    )


async def handle_traveler_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Deprecated - date selection now via calendar_handler."""
    pass


async def handle_traveler_passengers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Deprecated — passengers now selected via inline number picker."""
    pass


async def process_traveler_passengers(passengers: int, user_id: int,
                                       context: ContextTypes.DEFAULT_TYPE,
                                       send_message) -> None:
    """Process passenger selection (called from pick_num callback)."""
    lang = _lang(context)
    context.user_data["passengers"] = passengers
    route = context.user_data.get("route")
    date = context.user_data.get("date")
    preferred_time = context.user_data.get("time")

    rides = rank_rides(route, date, passengers, preferred_time=preferred_time)
    save_search_request(user_id, route, date, passengers)
    log_event("search", user_id, route)

    if not rides:
        display_date = datetime.strptime(date, "%Y-%m-%d").strftime("%d/%m/%Y")
        await send_message(
            t("no_rides_found", lang, route=route, date=display_date),
        )
        _clear_state(context)
        return

    display_date = datetime.strptime(date, "%Y-%m-%d").strftime("%d/%m/%Y")
    msg = t("rides_found", lang, count=len(rides))
    buttons = []
    for r in rides:
        time_str = r.get("time") or "N/A"
        avg = r.get("avg_rating", 0)
        rating_str = f" ⭐{avg}" if avg else ""
        driver_id = r.get("driver_id", 0)
        driver_name = r.get("username") or f"Driver #{driver_id}"
        msg += (
            f"\n🚗 [{driver_name}](tg://user?id={driver_id}) — {time_str}"
            f"\n💺 {r['seats_available']} seats{rating_str}\n"
        )
        buttons.append([InlineKeyboardButton(
            f"Reserve {driver_name} ({time_str})",
            callback_data=f"reserve:{r['id']}"
        )])

    keyboard = InlineKeyboardMarkup(buttons)
    await send_message(msg, reply_markup=keyboard)
    _clear_state(context)


# — Reservation callbacks ————————————————————————————————————————————

async def reservation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process seat reservation (inline button: reserve:<ride_id>)."""
    query = update.callback_query
    await query.answer()
    lang = _lang(context)

    ride_id = int(query.data.split(":")[1])
    user = update.effective_user
    passengers = context.user_data.get("passengers", 1)

    res_id = request_seat(ride_id, user.id, passengers)
    if not res_id:
        await query.edit_message_text(
            "❌ *Reservation Failed*\n\n"
            "This ride is full or unavailable."
        )
        return

    ride = get_ride(ride_id)
    try:
        display_date = datetime.strptime(ride["date"], "%Y-%m-%d").strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        display_date = ride.get("date", "?")

    await query.edit_message_text(
        "✅ *Request Sent*\n\n"
        "Waiting for driver approval..."
    )

    await notify_driver_reservation(
        context, ride["driver_id"], res_id,
        user.first_name or "Traveler", ride["route"], display_date, passengers,
        traveler_id=user.id,
    )


async def reservation_decision_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Driver approves or rejects reservation."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("res_approve:"):
        res_id = int(data.split(":")[1])
        res = handle_approve(res_id)
        if res:
            ride = get_ride(res["ride_id"])
            await query.edit_message_text(
                "✅ *Approved*"
            )
            if ride:
                try:
                    display_date = datetime.strptime(ride["date"], "%Y-%m-%d").strftime("%d/%m/%Y")
                except (ValueError, TypeError):
                    display_date = ride.get("date", "?")
                await notify_reservation_result(
                    context, res["traveler_id"], True,
                    ride.get("username") or f"Driver #{ride.get('driver_id', '?')}", ride["route"],
                    display_date, ride.get("time", "N/A"),
                    driver_id=ride.get("driver_id", 0),
                    ride_id=ride.get("id", 0),
                )
        else:
            await query.edit_message_text(
                "❌ *Could Not Approve*\n\n"
                "This reservation was already processed or there aren't enough seats."
            )

    elif data.startswith("res_reject:"):
        res_id = int(data.split(":")[1])
        res = handle_reject(res_id)
        if res:
            await query.edit_message_text(
                "❌ *Rejected*"
            )
            await notify_reservation_result(
                context, res["traveler_id"], False, "", "", "", "",
            )
        else:
            await query.edit_message_text(
                "❌ *Could Not Reject*\n\n"
                "This reservation was already processed."
            )


# — Rating callbacks ————————————————————————————————————————————————

async def rate_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show star-rating buttons for a ride (rate:<ride_id>)."""
    query = update.callback_query
    await query.answer()
    lang = _lang(context)

    ride_id = int(query.data.split(":")[1])
    ride = get_ride(ride_id)
    if not ride:
        await query.answer("Ride not found.", show_alert=True)
        return

    context.user_data["rating_driver_id"] = ride["driver_id"]
    context.user_data["rating_ride_id"] = ride_id

    star = "\u2b50"
    buttons = [
        [InlineKeyboardButton(star * i, callback_data=f"stars:{i}")]
        for i in range(1, 6)
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    await query.edit_message_text(t("rate_prompt", lang), reply_markup=keyboard)


async def stars_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Save star rating (stars:<rating>)."""
    query = update.callback_query
    await query.answer()
    lang = _lang(context)

    rating = int(query.data.split(":")[1])
    driver_id = context.user_data.get("rating_driver_id")
    ride_id = context.user_data.get("rating_ride_id")
    if not driver_id:
        await query.answer("Error: no driver to rate.", show_alert=True)
        return

    add_rating(driver_id, query.from_user.id, ride_id, rating)
    await query.edit_message_text(t("rating_saved", lang, rating=rating))


# — /my_trips (——————————————————————————————————————————————————

async def my_trips_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user\'s rides (as driver) and reservations (as traveler)."""
    user = update.effective_user
    lang = _lang(context)

    rides = get_user_rides(user.id)
    reservations = get_user_reservations(user.id)

    if not rides and not reservations:
        await update.message.reply_text(t("no_active_posts", lang))
        return

    lines = []

    if rides:
        lines.append(
            ""
            "**YOUR POSTED RIDES**\n"
            ""
        )
        for r in rides:
            try:
                dd = datetime.strptime(r["date"], "%Y-%m-%d").strftime("%d %B %Y")
            except ValueError:
                dd = r["date"]
            reservs = get_ride_reservations(r["id"])
            approved_list = [rv for rv in reservs if rv["status"] == "approved"]
            pending_list = [rv for rv in reservs if rv["status"] == "pending"]
            lines.append(
                f"  🚗 *{r['route']}*\n"
                f"  📅 {dd}\n"
                f"  ⏰ {r['time']}\n"
                f"  💺 {r['seats_available']}/{r['seats_total']} seats left\n"
                f"  ✅ {len(approved_list)} approved\n" 
                f"  ⏳ {len(pending_list)} pending\n"
            )
            for rv in approved_list:
                tname = rv.get('traveler_name') or f"Traveler #{rv.get('traveler_id', '?')}"
                tid = rv.get('traveler_id', 0)
                lines.append(f"    ✅ [{tname}](tg://user?id={tid}) ({rv['seats_reserved']} seat)\n")
            for rv in pending_list:
                tname = rv.get('traveler_name') or f"Traveler #{rv.get('traveler_id', '?')}"
                tid = rv.get('traveler_id', 0)
                lines.append(f"    ⏳ [{tname}](tg://user?id={tid}) ({rv['seats_reserved']} seat)\n")
            lines.append(f"  /delete\\_{r['id']}\n")

    if reservations:
        lines.append(
            "\n"
            "**YOUR RESERVATIONS**\n"
            ""
        )
        for res in reservations:
            status_icon = "✅" if res["status"] == "approved" else "⏳" if res["status"] == "pending" else "❌"
            driver_name = res.get('driver_username') or f"Driver #{res.get('driver_id', '?')}"
            driver_id = res.get('driver_id', 0)
            tname = res.get('traveler_name') or f"Passenger #{res.get('traveler_id', '?')}"
            tid = res.get('traveler_id', 0)
            lines.append(
                f"{status_icon} {res['route']} — {res['date']}\n"
                f"   🚗 [{driver_name}](tg://user?id={driver_id}) | {res['status']}\n"
                f"   👤 [{tname}](tg://user?id={tid})\n"
            )

    lines.append("")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# — /report ———————————————————————————————————————————————————

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start report flow."""
    lang = _lang(context)
    context.user_data["state"] = "awaiting_report_text"
    await update.message.reply_text(t("report_prompt", lang))


async def handle_report_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Save report text."""
    user = update.effective_user
    lang = _lang(context)
    report_text = update.message.text.strip()
    save_report(user.id, None, None, report_text)
    await update.message.reply_text(t("report_saved", lang))
    _clear_state(context)


async def my_trips_traveler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show traveler's reservations only."""
    user = update.effective_user
    lang = _lang(context)
    reservations = get_user_reservations(user.id)

    if not reservations:
        await update.message.reply_text(t("no_reservations", lang))
        return

    lines = [
        ""
        "**YOUR RESERVATIONS**\n"
        ""
    ]
    for res in reservations:
        status_icon = "✅" if res["status"] == "approved" else "⏳" if res["status"] == "pending" else "❌"
        driver_name = res.get('driver_username') or f"Driver #{res.get('driver_id', '?')}"
        driver_id = res.get('driver_id', 0)
        tname = res.get('traveler_name') or f"Passenger #{res.get('traveler_id', '?')}"
        tid = res.get('traveler_id', 0)
        lines.append(
            f"{status_icon} {res['route']} — {res['date']}\n"
            f"   🚗 [{driver_name}](tg://user?id={driver_id}) | {res['status']}\n"
            f"   👤 [{tname}](tg://user?id={tid})\n"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
