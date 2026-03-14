"""
admin_handler.py — Admin commands: stats, delete ride, block user, broadcast.

Access is restricted to user IDs listed in config.ADMIN_IDS.
"""
from __future__ import annotations

import logging
from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_IDS, t, DEFAULT_LANG
from database import (
    get_stats, admin_delete_ride, block_user, unblock_user,
    is_user_blocked, get_user_lang,
)
from services.notification_service import broadcast_message
from handlers.start_handler import _lang, _clear_state

logger = logging.getLogger(__name__)


def _is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ── /admin_stats ─────────────────────────────────────────────

async def admin_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):
        await update.message.reply_text(t("not_admin", _lang(context)))
        return

    s = get_stats()
    text = (
        "📊 *Admin Dashboard*\n\n"
        f"Total rides posted: {s['total_rides']}\n"
        f"Active rides (24h): {s['active_rides']}\n"
        f"Total reservations: {s['total_reservations']}\n"
        f"Approved reservations: {s['approved_reservations']}\n"
        f"Registered users: {s['total_users']}\n"
        f"Ratings submitted: {s['total_ratings']}\n"
        f"Reports filed: {s['total_reports']}\n\n"
        f"🔥 Most popular route: {s['popular_route']}\n"
        f"⏰ Busiest hour: {s['busiest_hour']}\n"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# ── /admin_delete_ride <id> ──────────────────────────────────

async def admin_delete_ride_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):
        await update.message.reply_text(t("not_admin", _lang(context)))
        return

    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("Usage: /admin_delete_ride <ride_id>")
        return

    ride_id = int(args[0])
    if admin_delete_ride(ride_id):
        await update.message.reply_text(f"✅ Ride #{ride_id} deleted.")
    else:
        await update.message.reply_text(f"❌ Ride #{ride_id} not found.")


# ── /admin_block_user <user_id> ──────────────────────────────

async def admin_block_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):
        await update.message.reply_text(t("not_admin", _lang(context)))
        return

    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("Usage: /admin_block_user <user_id>")
        return

    user_id = int(args[0])
    block_user(user_id)
    await update.message.reply_text(f"🚫 User {user_id} has been blocked.")
    logger.info("Admin %s blocked user %s", update.effective_user.id, user_id)


# ── /admin_unblock_user <user_id> ────────────────────────────

async def admin_unblock_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):
        await update.message.reply_text(t("not_admin", _lang(context)))
        return

    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("Usage: /admin_unblock_user <user_id>")
        return

    user_id = int(args[0])
    unblock_user(user_id)
    await update.message.reply_text(f"✅ User {user_id} has been unblocked.")


# ── /broadcast <message> ─────────────────────────────────────

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):
        await update.message.reply_text(t("not_admin", _lang(context)))
        return

    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message text>")
        return

    text = " ".join(context.args)
    _clear_state(context)
    context.user_data["state"] = "admin_broadcast_confirm"
    context.user_data["broadcast_text"] = text
    await update.message.reply_text(
        f"📢 Preview:\n\n{text}\n\nSend /confirm_broadcast to send or /cancel to abort."
    )


async def confirm_broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):
        return
    text = context.user_data.pop("broadcast_text", None)
    _clear_state(context)
    if not text:
        await update.message.reply_text("Nothing to broadcast. Use /broadcast <message> first.")
        return
    sent = await broadcast_message(context, text)
    await update.message.reply_text(f"✅ Broadcast sent to {sent} user(s).")
