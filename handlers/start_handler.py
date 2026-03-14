"""
start_handler.py — /start, /cancel, language selection, and the main text router.

On first /start the user picks a language, then sees the role selection.
Subsequent /start calls skip language selection if already set.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import ContextTypes

from config import (
    ROUTES, ROUTE_MK_MD, ROUTE_MD_MK,
    LANGUAGES, DEFAULT_LANG, t,
)
from database import (
    upsert_user, set_user_lang, get_user_lang, is_user_blocked,
    log_event,
)

logger = logging.getLogger(__name__)

# ── Keyboards ────────────────────────────────────────────────

LANG_KEYBOARD = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("العربية 🇸🇦", callback_data="lang:ar"),
        InlineKeyboardButton("English 🇬🇧", callback_data="lang:en"),
        InlineKeyboardButton("Deutsch 🇩🇪", callback_data="lang:de"),
    ],
    [
        InlineKeyboardButton("Français 🇫🇷", callback_data="lang:fr"),
        InlineKeyboardButton("Русский 🇷🇺", callback_data="lang:ru"),
        InlineKeyboardButton("Oʻzbek 🇺🇿", callback_data="lang:uz"),
    ],
])


def main_menu_keyboard(lang: str = "en") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            ["🙋🏻‍♂️ I need a Ride", KeyboardButton("📍 Drop My Pin", request_location=True)],
            ["🚙 I need a Passenger", "🌍 Language"],
            ["📅 My Adventures", "🆘 Help"],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def role_keyboard(lang: str = "en") -> ReplyKeyboardMarkup:
    """Alias for backward compatibility."""
    return main_menu_keyboard(lang)


def route_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[ROUTE_MK_MD], [ROUTE_MD_MK]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


# ── Helpers ──────────────────────────────────────────────────

DATE_PATTERN = re.compile(r"^(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})$")
TIME_PATTERN = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")


def _lang(context: ContextTypes.DEFAULT_TYPE) -> str:
    return context.user_data.get("lang", DEFAULT_LANG)


def _clear_state(context: ContextTypes.DEFAULT_TYPE) -> None:
    for key in ("state", "role", "route", "date", "time", "seats",
                "passengers", "selected_ride", "rating_driver_id",
                "rating_ride_id", "report_text"):
        context.user_data.pop(key, None)


# ── /start ───────────────────────────────────────────────────

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    upsert_user(user.id, user.first_name)
    log_event("start", user.id)

    if is_user_blocked(user.id):
        await update.message.reply_text(t("blocked_user", _lang(context)))
        return

    _clear_state(context)

    # If no language set yet, ask for language first
    stored_lang = get_user_lang(user.id)
    if stored_lang and stored_lang in LANGUAGES:
        context.user_data["lang"] = stored_lang
        await _show_role_selection(update, context)
    else:
        await update.message.reply_text(
            t("choose_lang", DEFAULT_LANG),
            reply_markup=LANG_KEYBOARD,
        )


async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button press for language selection."""
    query = update.callback_query
    await query.answer()
    data = query.data  # "lang:en" / "lang:ar" / "lang:ur"
    if not data.startswith("lang:"):
        return
    lang = data.split(":")[1]
    if lang not in LANGUAGES:
        lang = DEFAULT_LANG

    user_id = update.effective_user.id
    set_user_lang(user_id, lang)
    context.user_data["lang"] = lang

    await query.edit_message_text(f"Language set! ✅")
    # Now show main menu in the chat
    await context.bot.send_message(
        chat_id=user_id,
        text=t("welcome", lang),
        reply_markup=main_menu_keyboard(lang),
    )
    context.user_data["state"] = "main_menu"


async def _show_role_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = _lang(context)
    await update.message.reply_text(
        t("welcome", lang),
        reply_markup=main_menu_keyboard(lang),
    )
    context.user_data["state"] = "main_menu"


# ── /cancel ──────────────────────────────────────────────────

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _clear_state(context)
    lang = _lang(context)
    await update.message.reply_text(
        t("cancelled", lang),
        reply_markup=ReplyKeyboardRemove(),
    )
