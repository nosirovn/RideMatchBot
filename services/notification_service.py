"""
notification_service.py — Sending Telegram notifications.

Covers:
 - New-driver → matching travelers
 - Reservation request → driver
 - Approval/rejection → traveler
 - Ride-completion prompts
 - Admin broadcast
"""
from __future__ import annotations

import logging
from telegram.ext import ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import t
from database import (
    find_matching_search_requests,
    get_ride,
    get_user_lang,
    get_all_user_ids,
)

logger = logging.getLogger(__name__)


async def notify_travelers_of_new_ride(
    context: ContextTypes.DEFAULT_TYPE,
    route: str, date: str,
    driver_username: str, display_date: str,
    time_val: str, seats: int,
) -> None:
    """Notify travelers whose saved search matches the new ride."""
    searchers = find_matching_search_requests(route, date)
    for s in searchers:
        uid = s["user_id"]
        lang = get_user_lang(uid)
        msg = t(
            "new_ride_notif", lang,
            username=driver_username, route=route,
            date=display_date, time=time_val, seats=seats,
        )
        try:
            await context.bot.send_message(chat_id=uid, text=msg, parse_mode="Markdown")
        except Exception as e:
            logger.warning("Could not notify user %s: %s", uid, e)


async def notify_driver_reservation(
    context: ContextTypes.DEFAULT_TYPE,
    driver_id: int,
    reservation_id: int,
    traveler_username: str,
    route: str, display_date: str, seats: int,
) -> None:
    """Send reservation request to driver with Approve/Reject buttons."""
    lang = get_user_lang(driver_id)
    text = t(
        "reservation_request", lang,
        traveler=traveler_username, route=route,
        date=display_date, seats=seats,
    )
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"res_approve:{reservation_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"res_reject:{reservation_id}"),
        ]
    ])
    try:
        await context.bot.send_message(
            chat_id=driver_id, text=text,
            parse_mode="Markdown", reply_markup=keyboard,
        )
    except Exception as e:
        logger.warning("Could not notify driver %s: %s", driver_id, e)


async def notify_reservation_result(
    context: ContextTypes.DEFAULT_TYPE,
    traveler_id: int,
    approved: bool,
    driver_username: str,
    route: str, display_date: str, time_val: str,
) -> None:
    """Notify traveler of approval/rejection."""
    lang = get_user_lang(traveler_id)
    if approved:
        text = t(
            "reservation_approved", lang,
            driver=driver_username, route=route,
            date=display_date, time=time_val,
        )
    else:
        text = t("reservation_rejected", lang)
    try:
        await context.bot.send_message(chat_id=traveler_id, text=text, parse_mode="Markdown")
    except Exception as e:
        logger.warning("Could not notify traveler %s: %s", traveler_id, e)


async def broadcast_message(context: ContextTypes.DEFAULT_TYPE, text: str) -> int:
    """Send text to all non-blocked users. Returns count of successful sends."""
    user_ids = get_all_user_ids()
    sent = 0
    for uid in user_ids:
        try:
            await context.bot.send_message(chat_id=uid, text=text, parse_mode="Markdown")
            sent += 1
        except Exception:
            pass
    return sent
