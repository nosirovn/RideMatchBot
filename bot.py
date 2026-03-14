"""bot.py — Entry point for the RideMatch Telegram bot.
Registers all command handlers, callback-query handlers, the text router, 
location handler, periodic cleanup & completion jobs, and starts long-polling.
"""
from __future__ import annotations
import asyncio
import logging
from telegram import BotCommand, Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from config import BOT_TOKEN, CLEANUP_INTERVAL_SECONDS, ROUTES, t, DEFAULT_LANG
from database import (
    init_db,
    cleanup_expired_rides,
    set_user_location,
    is_user_blocked,
    get_user_lang,
    log_event,
)

from handlers.start_handler import (
    start_command,
    cancel_command,
    language_callback,
    _lang,
    _clear_state,
    role_keyboard,
    main_menu_keyboard,
    route_keyboard,
    LANG_KEYBOARD,
)
from handlers.driver_handler import (
    post_driver_command,
    available_command,
    delete_command,
    handle_driver_route,
    handle_driver_seats,
    process_driver_seats,
    my_trips_driver,
)
from handlers.traveler_handler import (
    find_ride_command,
    my_trips_command,
    report_command,
    handle_report_text,
    handle_traveler_route,
    handle_traveler_passengers,
    process_traveler_passengers,
    reservation_callback,
    reservation_decision_callback,
    rate_callback,
    stars_callback,
    my_trips_traveler,
)
from handlers.admin_handler import (
    admin_stats_command,
    admin_delete_ride_command,
    admin_block_user_command,
    admin_unblock_user_command,
    broadcast_command,
    confirm_broadcast_command,
)
from handlers.calendar_handler import (
    calendar_callback,
    select_day_callback,
    select_hour_callback,
)

logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
)
logger = logging.getLogger(__name__)

async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return
    user_id = update.effective_user.id
    if is_user_blocked(user_id):
        lang = get_user_lang(user_id)
        await update.message.reply_text(t("blocked_user", lang))
        return
    state = context.user_data.get("state")
    text = update.message.text.strip()

    # ── Main menu button handling (works from any state) ──
    if text == "🙋🏻‍♂️ I need a Ride":
        _clear_state(context)
        context.user_data["role"] = "traveler"
        context.user_data["state"] = "traveler_awaiting_route"
        lang = _lang(context)
        await update.message.reply_text(t("select_route", lang), reply_markup=route_keyboard())
        return
    if text == "🚙 I need a Passenger":
        _clear_state(context)
        context.user_data["role"] = "driver"
        context.user_data["state"] = "driver_awaiting_route"
        lang = _lang(context)
        await update.message.reply_text(t("select_route", lang), reply_markup=route_keyboard())
        return
    if text == "📅 My Adventures":
        return await my_trips_command(update, context)
    if text == "📍 Drop My Pin":
        lang = _lang(context)
        await update.message.reply_text(t("location_saved", lang), reply_markup=main_menu_keyboard(lang))
        return
    if text == "🌍 Language":
        lang = _lang(context)
        await update.message.reply_text(
            t("choose_lang", lang),
            reply_markup=LANG_KEYBOARD,
        )
        return
    if text == "🆘 Help":
        lang = _lang(context)
        await update.message.reply_text(
            t("help_text", lang),
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(lang),
        )
        return

    if state == "driver_awaiting_route":
        return await handle_driver_route(update, context)

    if state == "traveler_awaiting_route":
        return await handle_traveler_route(update, context)

    if state == "awaiting_report_text":
        return await handle_report_text(update, context)

    # Calendar/hour/number picker is active — remind user to use the inline buttons
    if state in ("driver_awaiting_date_selection", "traveler_awaiting_date_selection",
                 "driver_awaiting_time_selection", "traveler_awaiting_time_selection",
                 "driver_awaiting_seats", "traveler_awaiting_passengers"):
        await update.message.reply_text(
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "✦  USE BUTTONS  ✦\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⬆️ Please use the inline buttons above.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        )
        return

    lang = _lang(context)
    await update.message.reply_text(t("idle_hint", lang), reply_markup=main_menu_keyboard(lang))


async def callback_dispatcher(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = update.callback_query.data or ""

    if data.startswith("lang:"):
        return await language_callback(update, context)

    if data.startswith("cal:"):
        return await calendar_callback(update, context)
    if data.startswith("select_day:"):
        return await select_day_callback(update, context)
    if data.startswith("select_hour:"):
        return await select_hour_callback(update, context)

    if data.startswith("pick_num:"):
        return await pick_num_callback(update, context)

    if data.startswith("reserve:"):
        return await reservation_callback(update, context)
    if data.startswith("res_approve:") or data.startswith("res_reject:"):
        return await reservation_decision_callback(update, context)

    if data.startswith("rate:"):
        return await rate_callback(update, context)
    if data.startswith("stars:"):
        return await stars_callback(update, context)

    await update.callback_query.answer()


async def pick_num_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle number picker selection for seats/passengers."""
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    if len(parts) != 2:
        return
    try:
        num = int(parts[1])
        if not (1 <= num <= 7):
            raise ValueError
    except (ValueError, IndexError):
        await query.answer(text="❌ Invalid selection", show_alert=True)
        return

    state = context.user_data.get("state")
    user = update.effective_user

    async def send_msg(text, reply_markup=None):
        await context.bot.send_message(
            chat_id=user.id, text=text,
            parse_mode="Markdown", reply_markup=reply_markup,
        )

    # Remove the inline keyboard
    await query.edit_message_text(
        text=query.message.text + f"\n\n━━━━━━━━━━━━━━━━━━━━━━\n✅ Selected: *{num}*\n━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown",
    )

    if state == "driver_awaiting_seats":
        await process_driver_seats(num, user.id, user.first_name, context, send_msg)
    elif state == "traveler_awaiting_passengers":
        await process_traveler_passengers(num, user.id, context, send_msg)
    else:
        await send_msg(
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "✦  ERROR ❌  ✦\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Unexpected state. Use /start to begin again.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        )


async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    loc = update.message.location
    if loc:
        set_user_location(update.effective_user.id, loc.latitude, loc.longitude)
        lang = _lang(context)
        await update.message.reply_text(
            t("location_saved", lang),
            reply_markup=main_menu_keyboard(lang),
        )


async def cleanup_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    deleted = cleanup_expired_rides()
    if deleted:
        logger.info("Cleanup: removed %d expired ride(s).", deleted)


async def post_init(application: Application) -> None:
    """Set the bot menu button with /start command."""
    await application.bot.set_my_commands([
        BotCommand("start", "Open main menu"),
    ])


def main() -> None:
    init_db()

    # Fix for Python 3.14+ event loop compatibility
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Event loop is closed")
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(CommandHandler("post_driver", post_driver_command))
    app.add_handler(CommandHandler("find_ride", find_ride_command))
    app.add_handler(CommandHandler("my_trips", my_trips_command))
    app.add_handler(CommandHandler("my_posts", my_trips_command))
    app.add_handler(CommandHandler("available", available_command))
    app.add_handler(CommandHandler("report", report_command))

    app.add_handler(CommandHandler("admin_stats", admin_stats_command))
    app.add_handler(CommandHandler("admin_delete_ride", admin_delete_ride_command))
    app.add_handler(CommandHandler("admin_block_user", admin_block_user_command))
    app.add_handler(CommandHandler("admin_unblock_user", admin_unblock_user_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CommandHandler("confirm_broadcast", confirm_broadcast_command))

    app.add_handler(MessageHandler(filters.Regex(r"^/delete_\d+$"), delete_command))
    app.add_handler(CallbackQueryHandler(callback_dispatcher))
    app.add_handler(MessageHandler(filters.LOCATION, location_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    app.job_queue.run_repeating(cleanup_job, interval=CLEANUP_INTERVAL_SECONDS, first=10)

    logger.info("🚀 RideMatch bot starting…")
    app.run_polling()


if __name__ == "__main__":
    main()
