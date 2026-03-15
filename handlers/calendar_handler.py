"""calendar_handler.py — Interactive calendar and hour selector for date/time picking.
Black, white & golden premium design inspired by BookingCard UI.
"""
from __future__ import annotations

import logging
import calendar as cal
from datetime import datetime, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from config import t, DEFAULT_LANG
from handlers.start_handler import _lang

logger = logging.getLogger(__name__)


def create_calendar_keyboard(year: int, month: int) -> InlineKeyboardMarkup:
    """Black/white/golden calendar grid."""
    kb = []

    prev_m = month - 1 if month > 1 else 12
    prev_y = year if month > 1 else year - 1
    next_m = month + 1 if month < 12 else 1
    next_y = year if month < 12 else year + 1

    # ── Title row ──
    kb.append([
        InlineKeyboardButton("◀️", callback_data=f"cal:prev:{prev_y}:{prev_m}"),
        InlineKeyboardButton(
            f"**{cal.month_name[month].upper()} {year}**",
            callback_data="cal:noop",
        ),
        InlineKeyboardButton("▶️", callback_data=f"cal:next:{next_y}:{next_m}"),
    ])

    # ── Day-of-week header ──
    kb.append([
        InlineKeyboardButton(d, callback_data="cal:noop")
        for d in ["S", "M", "T", "W", "T", "F", "S"]
    ])

    # ── Day grid (Sunday-first) ──
    today = datetime.utcnow().date()
    month_cal = cal.Calendar(firstweekday=6).monthdayscalendar(year, month)

    for week in month_cal:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(" ", callback_data="cal:noop"))
            else:
                d = datetime(year, month, day).date()
                if d < today:
                    # Past — dark
                    row.append(InlineKeyboardButton(
                        f"  {day}  ", callback_data="cal:noop"
                    ))
                elif d == today:
                    # Today — golden highlight
                    row.append(InlineKeyboardButton(
                        f"◈ {day} ◈",
                        callback_data=f"select_day:{year}:{month}:{day}",
                    ))
                else:
                    # Future — selectable white
                    row.append(InlineKeyboardButton(
                        f" {day} ",
                        callback_data=f"select_day:{year}:{month}:{day}",
                    ))
        kb.append(row)

    return InlineKeyboardMarkup(kb)


def create_hour_keyboard() -> InlineKeyboardMarkup:
    """Black/golden time picker — grouped by time of day, 4-column grid."""
    kb = []

    # Header
    kb.append([
        InlineKeyboardButton("**SELECT TIME**", callback_data="cal:noop")
    ])

    sections = [
        ("☀️ Morning",  range(5, 12)),
        ("🌤 Afternoon", range(12, 18)),
        ("🌙 Evening",   range(18, 24)),
        ("🌑 Night",     range(0, 5)),
    ]

    for label, hours in sections:
        kb.append([InlineKeyboardButton(f"─── {label} ───", callback_data="cal:noop")])
        row = []
        for h in hours:
            row.append(InlineKeyboardButton(
                f"{h:02d}:00",
                callback_data=f"select_hour:{h}",
            ))
            if len(row) == 4:
                kb.append(row)
                row = []
        if row:
            kb.append(row)

    return InlineKeyboardMarkup(kb)


def create_number_picker(max_num: int = 7) -> InlineKeyboardMarkup:
    """Golden-themed inline number picker (1 to max_num)."""
    kb = []
    row = []
    for n in range(1, max_num + 1):
        row.append(InlineKeyboardButton(
            f" {n} ",
            callback_data=f"pick_num:{n}",
        ))
        if len(row) == 4:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    return InlineKeyboardMarkup(kb)


# ═══════════════════════════════════════════════════════════════
# Callback handlers
# ═══════════════════════════════════════════════════════════════

async def calendar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle calendar navigation (next/prev month)."""
    query = update.callback_query
    await query.answer()

    data = query.data
    if data == "cal:noop":
        return

    parts = data.split(":")
    if len(parts) < 4:
        return

    year = int(parts[2])
    month = int(parts[3])
    if month < 1 or month > 12:
        return

    keyboard = create_calendar_keyboard(year, month)
    await query.edit_message_reply_markup(reply_markup=keyboard)


async def select_day_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle day selection from calendar."""
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    if len(parts) != 4:
        return

    try:
        year, month, day = int(parts[1]), int(parts[2]), int(parts[3])
        date_obj = datetime(year, month, day)
        if date_obj.date() < datetime.utcnow().date():
            await query.answer(text="❌ Cannot select past dates", show_alert=True)
            return
    except (ValueError, IndexError):
        await query.answer(text="❌ Invalid date", show_alert=True)
        return

    date_str = f"{year:04d}-{month:02d}-{day:02d}"
    context.user_data["date"] = date_str

    role = context.user_data.get("role", "driver")
    context.user_data["state"] = (
        "traveler_awaiting_time_selection" if role == "traveler"
        else "driver_awaiting_time_selection"
    )

    display_date = date_obj.strftime("%d %B %Y")
    keyboard = create_hour_keyboard()

    await query.edit_message_text(
        text=(
            f""
            f"**DATE CONFIRMED**\n"
            f"\n"
            f"  📅  {display_date}\n\n"
            f"Now select your departure time:"
        ),
        reply_markup=keyboard,
    )


async def select_hour_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle hour selection."""
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    if len(parts) != 2:
        return

    try:
        hour = int(parts[1])
        if not (0 <= hour <= 23):
            raise ValueError
    except (ValueError, IndexError):
        await query.answer(text="❌ Invalid hour", show_alert=True)
        return

    date_str = context.user_data.get("date")
    if not date_str:
        await query.answer(text="❌ Date not set", show_alert=True)
        return

    time_str = f"{hour:02d}:00"
    context.user_data["time"] = time_str

    try:
        display_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%d %B %Y")
    except ValueError:
        display_date = date_str

    lang = _lang(context)
    role = context.user_data.get("role", "driver")

    if role == "traveler":
        context.user_data["state"] = "traveler_awaiting_passengers"
        prompt = t("enter_passengers", lang)
    else:
        context.user_data["state"] = "driver_awaiting_seats"
        prompt = t("enter_seats", lang)

    number_kb = create_number_picker(7)

    await query.edit_message_text(
        text=(
            f""
            f"**BOOKING SUMMARY**\n"
            f"\n"
            f"  📅  {display_date}\n"
            f"  ⏰  {time_str}\n\n"
            f"\n"
            f"⚠️ *Attention:* Please ensure your Name\n"
            f"and Phone Number are visible in your\n"
            f"Telegram profile settings.\n\n"
            f"\n"
            f"{prompt}"
        ),
        parse_mode="Markdown",
        reply_markup=number_kb,
    )
