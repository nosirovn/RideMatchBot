"""
traveler_handler.py – Traveler flow: find ride, reserve seats, rate driver, report.
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
from handlers.calendar_handler import (
    create_calendar_keyboard,
    create_hour_keyboard,
)

logger = logging.getLogger(__name__)


# — /find_ride ————————————————————————————————————————————————

async def find_ride_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Find ride by from→to location and date."""
        user = update.effective_user
        upsert_user(user.id, user.first_name, user.last_name)

    lang = get_user_lang(user.id)
    context.user_data["lang"] = lang
    context.user_data["state"] = "find_ride_start"

    msg = t(lang, "find_ride_request")  # "Enter departure city:"
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())


async def handle_traveler_route(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Traveler enters departure and destination."""
        state = context.user_data.get("state")
        lang = context.user_data.get("lang", DEFAULT_LANG)

    if not state:
                context.user_data["state"] = "find_route_dep"
                msg = t(lang, "enter_departure")
                await update.message.reply_text(msg)
                return

    if state == "find_route_dep":
                departure = update.message.text
                context.user_data["departure"] = departure
                context.user_data["state"] = "find_route_dest"
                msg = t(lang, "enter_destination")
                await update.message.reply_text(msg)

elif state == "find_route_dest":
            destination = update.message.text
            context.user_data["destination"] = destination
            context.user_data["state"] = "find_route_date"

        # Show calendar for date selection
            keyboard = create_calendar_keyboard()
            msg = t(lang, "select_date")
            await update.message.reply_text(msg, reply_markup=keyboard)


async def handle_traveler_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Callback for calendar date selection (replaces text-based input)."""
        query = update.callback_query
        await query.answer()

    lang = context.user_data.get("lang", DEFAULT_LANG)
    prefix, value = query.data.split(":", 1)

    if prefix == "select_day":
                # Date selected
                context.user_data["date"] = value  # YYYY-MM-DD format
        context.user_data["state"] = "find_route_time"

        # Show hour picker
        keyboard = create_hour_keyboard()
        msg = t(lang, "select_time")
        await query.edit_message_text(msg, reply_markup=keyboard)

elif prefix == "select_hour":
        # Time selected
        context.user_data["time"] = value  # HH:00 format
        context.user_data["state"] = "search_rides"

        # Now search for rides
        await search_rides(update, context)


async def search_rides(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Search for available rides matching traveler criteria."""
        query = update.callback_query
        lang = context.user_data.get("lang", DEFAULT_LANG)

    departure = context.user_data.get("departure")
    destination = context.user_data.get("destination")
    ride_date = context.user_data.get("date")
    ride_time = context.user_data.get("time", "00:00")

    if not all([departure, destination, ride_date]):
                msg = t(lang, "missing_search_params")
                await query.answer(msg)
                return

    # Save search request for analytics
    save_search_request(
                user_id=query.from_user.id,
                departure=departure,
                destination=destination,
                search_date=ride_date,
                search_time=ride_time,
    )

    # Get rides and rank them
    from database import find_drivers
    available_rides = find_drivers(departure, destination, ride_date)

    if not available_rides:
                msg = t(lang, "no_rides_found")
                await query.edit_message_text(msg)
                return

    # Rank rides by AI service
    ranked = rank_rides(available_rides, ride_time)

    # Display top 5 results
    keyboard_buttons = []
    for i, ride in enumerate(ranked[:5], 1):
                btn = InlineKeyboardButton(
                                text=f"{i}. {ride['departure']}→{ride['destination']} {ride['ride_time']} (${ride['price_per_seat']})",
                                callback_data=f"select_ride:{ride['ride_id']}"
                )
                keyboard_buttons.append([btn])

    keyboard = InlineKeyboardMarkup(keyboard_buttons)
    msg = t(lang, "available_rides")
    await query.edit_message_text(msg, reply_markup=keyboard)

    context.user_data["available_rides"] = ranked


async def handle_traveler_passing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Traveler selects a ride and requests seats."""
        query = update.callback_query
        await query.answer()

    lang = context.user_data.get("lang", DEFAULT_LANG)
    _, ride_id = query.data.split(":")
    ride_id = int(ride_id)

    ride = get_ride(ride_id)
    if not ride or ride["available_seats"] <= 0:
                msg = t(lang, "ride_no_longer_available")
                await query.answer(msg, show_alert=True)
                return

    context.user_data["selected_ride_id"] = ride_id
    context.user_data["state"] = "request_seats"

    # Ask how many seats
    keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(text=str(i), callback_data=f"seats:{i}")]
                for i in range(1, min(ride["available_seats"] + 1, 7))
    ])

    msg = t(lang, "how_many_seats")
    await query.edit_message_text(msg, reply_markup=keyboard)


async def reservation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Process seat reservation."""
        query = update.callback_query
        await query.answer()

    lang = context.user_data.get("lang", DEFAULT_LANG)
    _, seats_str = query.data.split(":")
    seats_requested = int(seats_str)

    ride_id = context.user_data.get("selected_ride_id")
    if not ride_id:
                msg = t(lang, "error_no_ride_selected")
                await query.answer(msg, show_alert=True)
                return

    try:
                # Request seat through reservation service
                reservation = request_seat(
                                ride_id=ride_id,
                                traveler_id=query.from_user.id,
                                seats_requested=seats_requested
                )

        msg = t(lang, "reservation_pending")
        await query.edit_message_text(msg)

        # Notify driver
        ride = get_ride(ride_id)
        notify_driver_reservation(
                        driver_id=ride["driver_id"],
                        reservation=reservation,
                        ride=ride,
        )

        context.user_data["state"] = "reservation_pending"
        context.user_data["reservation_id"] = reservation["reservation_id"]

except ValueError as e:
        msg = t(lang, "reservation_failed") + f"\n{str(e)}"
        await query.answer(msg, show_alert=True)


async def reservation_decision_call(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Driver approves or rejects reservation."""
        query = update.callback_query
        await query.answer()

    lang = context.user_data.get("lang", DEFAULT_LANG)
    action, res_id = query.data.split(":")
    res_id = int(res_id)

    if action == "approve":
                handle_approve(res_id)
                msg = t(lang, "reservation_approved")
elif action == "reject":
            handle_reject(res_id)
            msg = t(lang, "reservation_rejected")
else:
            msg = t(lang, "unknown_action")

    await query.edit_message_text(msg)


async def rate_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Traveler rates driver (1-5 stars)."""
        query = update.callback_query
        await query.answer()

    lang = context.user_data.get("lang", DEFAULT_LANG)
    _, rating = query.data.split(":")
    rating = int(rating)

    ride_id = context.user_data.get("selected_ride_id")
    ride = get_ride(ride_id)

    if not ride:
                await query.answer(t(lang, "error_ride_not_found"), show_alert=True)
                return

    # Save rating
    add_rating(
                from_user_id=query.from_user.id,
                to_user_id=ride["driver_id"],
                ride_id=ride_id,
                rating_value=rating,
    )

    msg = t(lang, "rating_saved")
    await query.edit_message_text(msg)

    context.user_data["state"] = "rating_done"


async def stars_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Inline button callback for star ratings."""
        await rate_callback(update, context)


async def my_trips_traveler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show traveler's reservations / trips."""
        user = update.effective_user
        lang = get_user_lang(user.id)

    reservations = get_user_reservations(user.id)

    if not reservations:
                msg = t(lang, "no_trips")
                await update.message.reply_text(msg)
                return

    msg = t(lang, "your_reservations") + "\n\n"
    for res in reservations:
                ride = get_ride(res["ride_id"])
                msg += f"🚗 {ride['departure']}→{ride['destination']} {ride['ride_date']} {ride['ride_time']}\n"
                msg += f"   Status: {res['status']}\n\n"

    await update.message.reply_text(msg)


async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Traveler reports a driver or ride issue."""
        user = update.effective_user
        lang = get_user_lang(user.id)

    context.user_data["state"] = "report_start"
    msg = t(lang, "describe_issue")
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())


async def handle_report_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Traveler submits report text."""
        user = update.effective_user
        lang = context.user_data.get("lang", DEFAULT_LANG)
        report_text = update.message.text

    save_report(
                user_id=user.id,
                report_text=report_text,
                ride_id=context.user_data.get("selected_ride_id"),
    )

    msg = t(lang, "report_submitted")
    await update.message.reply_text(msg)
    context.user_data["state"] = None
