Page_Down"""
bot.py — Entry point for the RideMatch Telegram bot.
Registers all command handlers, callback-query handlers, the text router, 
location handler, periodic cleanup & completion jobs, and starts long-polling.
"""
from __future__ import annotations
import asyncio
import logging
from telegram import Update
from telegram.ext import (
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
    route_keyboard,
)
from handlers.driver_handler import (
    post_driver_command,
    available_command,
    delete_command,
    handle_driver_route,
    handle_driver_date,
    handle_driver_time,
    handle_driver_seats,
)
from handlers.traveler_handler import (
    find_ride_command,
    my_trips_command,
    report_command,
    handle_report_text,
    handle_traveler_route,
    handle_traveler_date,
    handle_traveler_passengers,
    reservation_callback,
    reservation_decision_callback,
    rate_callback,
    stars_callback,
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

    if state == "awaiting_role":
                if text == "🚗 Driver":
                                context.user_data["role"] = "driver"
                                context.user_data["state"] = "driver_awaiting_route"
                                lang = _lang(context)
                                await update.message.reply_text(t("select_route", lang), reply_markup=route_keyboard())
    elif text == "🧍 Traveler":
            context.user_data["role"] = "traveler"
            context.user_data["state"] = "traveler_awaiting_route"
            lang = _lang(context)
            await update.message.reply_text(t("select_route", lang), reply_markup=route_keyboard())
else:
            lang = _lang(context)
                await update.message.reply_text(t("choose_role_btn", lang), reply_markup=role_keyboard(lang))
        return

    if state == "driver_awaiting_route" or (state == "awaiting_route" and context.user_data.get("role") == "driver"):
                context.user_data["state"] = "driver_awaiting_route"
                return await handle_driver_route(update, context)
            if state == "driver_awaiting_date":
                        return await handle_driver_date(update, context)
                    if state == "driver_awaiting_time":
                                return await handle_driver_time(update, context)
                            if state == "driver_awaiting_seats":
                                        return await handle_driver_seats(update, context)

    if state == "traveler_awaiting_route" or (state == "awaiting_route" and context.user_data.get("role") == "traveler"):
                context.user_data["state"] = "traveler_awaiting_route"
                return await handle_traveler_route(update, context)
            if state == "traveler_awaiting_date":
                        return await handle_traveler_date(update, context)
                    if state == "traveler_awaiting_passengers":
                                return await handle_traveler_passengers(update, context)

    if state == "awaiting_report_text":
                return await handle_report_text(update, context)

    lang = _lang(context)
    await update.message.reply_text(t("idle_hint", lang))


async def callback_dispatcher(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        data = update.callback_query.data or ""

    if data.startswith("lang:"):
                return await language_callback(update, context)

    if data.startswith("cal:"):
                return await calendar_callback(update, context)
            if data.startswith("select_day:"):
                        state = context.user_data.get("state")
                        if state == "driver_awaiting_date_selection":
                                        return await select_day_callback(update, context)
                                    return
    if data.startswith("select_hour:"):
                return await select_hour_callback(update, context)

    if data.startswith("reserve:"):
                return await reservation_callback(update, context)
    if data.startswith("res_approve:") or data.startswith("res_reject:"):
                return await reservation_decision_callback(update, context)

    if data.startswith("rate:"):
                return await rate_callback(update, context)
    if data.startswith("stars:"):
                return await stars_callback(update, context)

    await update.callback_query.answer()


async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        loc = update.message.location
    if loc:
                set_user_location(update.effective_user.id, loc.latitude, loc.longitude)
        await update.message.reply_text("📍 Location saved!")


async def cleanup_job(context: ContextTypes.DEFAULT_TYPE) -> None:
        deleted = cleanup_expired_rides()
    if deleted:
                logger.info("Cleanup: removed %d expired ride(s).", deleted)


def main() -> None:
        init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

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
        asyncio.set_event_loop(asyncio.new_event_loop())
    main()
