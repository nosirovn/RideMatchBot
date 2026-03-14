"""
config.py — Bot configuration, constants, admin settings, and translations.
"""
from __future__ import annotations

import os

# ── Bot token ────────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable not set.")

# ── Admin ────────────────────────────────────────────────────
# Telegram user IDs that have admin privileges (comma-separated env var)
_admin_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS: list[int] = [int(x) for x in _admin_raw.split(",") if x.strip().isdigit()]

# ── Database ─────────────────────────────────────────────────
DB_PATH = "ridematch.db"

# ── Routes ───────────────────────────────────────────────────
ROUTE_MK_MD = "Makkah → Madinah"
ROUTE_MD_MK = "Madinah → Makkah"
ROUTES = [ROUTE_MK_MD, ROUTE_MD_MK]

# ── Anti-spam ────────────────────────────────────────────────
MAX_ACTIVE_POSTS = 3

# ── Ride expiry (hours) ─────────────────────────────────────
RIDE_EXPIRY_HOURS = 24

# ── Cleanup interval (seconds) ──────────────────────────────
CLEANUP_INTERVAL_SECONDS = 1800

# ── Time matching tolerance (hours) ─────────────────────────
TIME_MATCH_TOLERANCE_HOURS = 3

# ── Supported languages ─────────────────────────────────────
LANGUAGES = ["en", "ar", "ur"]
DEFAULT_LANG = "en"

# ── Translation dictionaries ────────────────────────────────
# Keys used throughout the bot; each maps to {lang: text}.
TEXTS: dict[str, dict[str, str]] = {
    "welcome": {
        "en": (
            "Welcome to RideMatch 🚗\n"
            "Match drivers and travelers between Makkah and Madinah.\n\n"
            "Choose an option below:"
        ),
        "ar": (
            "مرحبًا بك في RideMatch 🚗\n"
            "تطابق السائقين والمسافرين بين مكة والمدينة.\n\n"
            "اختر من الخيارات أدناه:"
        ),
        "ur": (
            "RideMatch میں خوش آمدید 🚗\n"
            "مکہ اور مدینہ کے درمیان ڈرائیوروں اور مسافروں کو ملائیں۔\n\n"
            "نیچے سے ایک آپشن منتخب کریں:"
        ),
    },
    "choose_lang": {
        "en": "🌐 Choose your language:",
        "ar": "🌐 اختر لغتك:",
        "ur": "🌐 اپنی زبان منتخب کریں:",
    },
    "driver_mode": {
        "en": "🚗 *Driver mode*\nSelect your route:",
        "ar": "🚗 *وضع السائق*\nاختر مسارك:",
        "ur": "🚗 *ڈرائیور موڈ*\nاپنا راستہ منتخب کریں:",
    },
    "traveler_mode": {
        "en": "🧍 *Traveler mode*\nSelect your route:",
        "ar": "🧍 *وضع المسافر*\nاختر مسارك:",
        "ur": "🧍 *مسافر موڈ*\nاپنا راستہ منتخب کریں:",
    },
    "select_route": {
        "en": "Select your route:",
        "ar": "اختر مسارك:",
        "ur": "اپنا راستہ منتخب کریں:",
    },
    "enter_date": {
        "en": "📅 Enter the date (DD/MM/YYYY):",
        "ar": "📅 أدخل التاريخ (DD/MM/YYYY):",
        "ur": "📅 تاریخ درج کریں (DD/MM/YYYY):",
    },
    "enter_time": {
        "en": "⏰ Enter departure time (HH:MM, 24-hour format):",
        "ar": "⏰ أدخل وقت المغادرة (HH:MM):",
        "ur": "⏰ روانگی کا وقت درج کریں (HH:MM):",
    },
    "enter_seats": {
        "en": "💺 How many seats are available? (1–10):",
        "ar": "💺 كم عدد المقاعد المتاحة؟ (1–10):",
        "ur": "💺 کتنی سیٹیں دستیاب ہیں؟ (1–10):",
    },
    "enter_passengers": {
        "en": "👥 How many passengers? (1–10):",
        "ar": "👥 كم عدد الركاب؟ (1–10):",
        "ur": "👥 کتنے مسافر؟ (1–10):",
    },
    "ride_posted": {
        "en": "✅ *Ride posted!*",
        "ar": "✅ *تم نشر الرحلة!*",
        "ur": "✅ *سواری شائع ہوگئی!*",
    },
    "no_rides_found": {
        "en": "😔 No drivers found for *{route}* on *{date}*.\n\nYour search has been saved — you'll be notified if a driver posts a matching ride.",
        "ar": "😔 لم يتم العثور على سائقين لـ *{route}* في *{date}*.\n\nتم حفظ بحثك — سيتم إبلاغك عند نشر رحلة مطابقة.",
        "ur": "😔 *{route}* کے لیے *{date}* پر کوئی ڈرائیور نہیں ملا۔\n\nآپ کی تلاش محفوظ ہوگئی — مماثل سواری ملنے پر آپ کو مطلع کیا جائے گا۔",
    },
    "rides_found": {
        "en": "🎉 *Found {count} ride(s):*\n",
        "ar": "🎉 *تم العثور على {count} رحلة(رحلات):*\n",
        "ur": "🎉 *{count} سواری(سواریاں) ملیں:*\n",
    },
    "cancelled": {
        "en": "Operation cancelled. Use /start to begin again.",
        "ar": "تم الإلغاء. استخدم /start للبدء مجددًا.",
        "ur": "آپریشن منسوخ۔ دوبارہ شروع کرنے کے لیے /start استعمال کریں۔",
    },
    "spam_limit": {
        "en": "⚠️ You already have 3 active posts. Delete one with /my_posts before posting again.",
        "ar": "⚠️ لديك بالفعل 3 منشورات نشطة. احذف واحدًا باستخدام /my_posts.",
        "ur": "⚠️ آپ کے پاس پہلے سے 3 فعال پوسٹیں ہیں۔ /my_posts سے ایک حذف کریں۔",
    },
    "invalid_date": {
        "en": "Invalid format. Please enter date as DD/MM/YYYY:",
        "ar": "تنسيق غير صالح. أدخل التاريخ كـ DD/MM/YYYY:",
        "ur": "غلط فارمیٹ۔ براہ کرم تاریخ DD/MM/YYYY لکھیں:",
    },
    "past_date": {
        "en": "Date cannot be in the past. Please enter a future date:",
        "ar": "لا يمكن أن يكون التاريخ في الماضي. أدخل تاريخًا مستقبليًا:",
        "ur": "تاریخ ماضی میں نہیں ہوسکتی۔ مستقبل کی تاریخ درج کریں:",
    },
    "invalid_time": {
        "en": "Invalid format. Enter time as HH:MM (e.g. 14:30):",
        "ar": "تنسيق غير صالح. أدخل الوقت كـ HH:MM:",
        "ur": "غلط فارمیٹ۔ وقت HH:MM لکھیں (مثلاً 14:30):",
    },
    "number_1_10": {
        "en": "Please enter a number between 1 and 10:",
        "ar": "أدخل رقمًا بين 1 و 10:",
        "ur": "1 سے 10 کے درمیان نمبر درج کریں:",
    },
    "choose_role_btn": {
        "en": "Please choose an option using the buttons below.",
        "ar": "اختر خيارًا باستخدام الأزرار أدناه.",
        "ur": "نیچے دیے گئے بٹنوں سے ایک آپشن منتخب کریں۔",
    },
    "location_saved": {
        "en": "📍 Location saved! This helps match you with nearby drivers.",
        "ar": "📍 تم حفظ الموقع! هذا يساعد في مطابقتك مع السائقين القريبين.",
        "ur": "📍 مقام محفوظ ہوگیا! اس سے قریبی ڈرائیوروں سے مماثلت میں مدد ملے گی۔",
    },
    "choose_route_btn": {
        "en": "Please select a valid route using the buttons.",
        "ar": "اختر مسارًا صالحًا باستخدام الأزرار.",
        "ur": "بٹنوں سے درست راستہ منتخب کریں۔",
    },
    "no_active_posts": {
        "en": "You have no active posts.",
        "ar": "ليس لديك منشورات نشطة.",
        "ur": "آپ کی کوئی فعال پوسٹ نہیں۔",
    },
    "post_deleted": {
        "en": "✅ Post deleted.",
        "ar": "✅ تم حذف المنشور.",
        "ur": "✅ پوسٹ حذف ہوگئی۔",
    },
    "post_not_found": {
        "en": "❌ Post not found or you don't own it.",
        "ar": "❌ المنشور غير موجود أو لا تملكه.",
        "ur": "❌ پوسٹ نہیں ملی یا آپ کی نہیں۔",
    },
    "new_ride_notif": {
        "en": (
            "🔔 *New ride available!*\n\n"
            "🚗 Driver: {name}\n"
            "📍 Route: {route}\n"
            "📅 Date: {date}\n"
            "⏰ Time: {time}\n"
            "💺 Seats: {seats}\n\n"
            "Contact the driver directly on Telegram."
        ),
        "ar": (
            "🔔 *رحلة جديدة متاحة!*\n\n"
            "🚗 السائق: {name}\n"
            "📍 المسار: {route}\n"
            "📅 التاريخ: {date}\n"
            "⏰ الوقت: {time}\n"
            "💺 المقاعد: {seats}\n\n"
            "تواصل مع السائق مباشرة على تيليجرام."
        ),
        "ur": (
            "🔔 *نئی سواری دستیاب!*\n\n"
            "🚗 ڈرائیور: {name}\n"
            "📍 راستہ: {route}\n"
            "📅 تاریخ: {date}\n"
            "⏰ وقت: {time}\n"
            "💺 سیٹیں: {seats}\n\n"
            "ٹیلیگرام پر ڈرائیور سے براہ راست رابطہ کریں۔"
        ),
    },
    "reservation_request": {
        "en": "🔔 *Seat reservation request*\n\nTraveler: {traveler}\nRoute: {route}\nDate: {date}\nSeats requested: {seats}",
        "ar": "🔔 *طلب حجز مقعد*\n\nالمسافر: {traveler}\nالمسار: {route}\nالتاريخ: {date}\nالمقاعد المطلوبة: {seats}",
        "ur": "🔔 *سیٹ ریزرویشن کی درخواست*\n\nمسافر: {traveler}\nراستہ: {route}\nتاریخ: {date}\nمطلوبہ سیٹیں: {seats}",
    },
    "reservation_approved": {
        "en": "✅ Your reservation has been *approved*!\n\nDriver: {driver}\nRoute: {route}\nDate: {date}\nTime: {time}",
        "ar": "✅ تمت *الموافقة* على حجزك!\n\nالسائق: {driver}\nالمسار: {route}\nالتاريخ: {date}\nالوقت: {time}",
        "ur": "✅ آپ کی ریزرویشن *منظور* ہوگئی!\n\nڈرائیور: {driver}\nراستہ: {route}\nتاریخ: {date}\nوقت: {time}",
    },
    "reservation_rejected": {
        "en": "❌ Your reservation was *rejected* by the driver.",
        "ar": "❌ تم *رفض* حجزك من قبل السائق.",
        "ur": "❌ ڈرائیور نے آپ کی ریزرویشن *مسترد* کردی۔",
    },
    "rate_prompt": {
        "en": "⭐ How was your ride? Please rate the driver (1–5 stars):",
        "ar": "⭐ كيف كانت رحلتك؟ قيّم السائق (1–5 نجوم):",
        "ur": "⭐ آپ کی سواری کیسی رہی؟ ڈرائیور کو ریٹ کریں (1–5 ستارے):",
    },
    "rating_saved": {
        "en": "Thank you! Your rating has been saved. ⭐ {rating}/5",
        "ar": "شكرًا! تم حفظ تقييمك. ⭐ {rating}/5",
        "ur": "شکریہ! آپ کی ریٹنگ محفوظ ہوگئی۔ ⭐ {rating}/5",
    },
    "driver_available_now": {
        "en": "🟢 You are now marked as *Available*.",
        "ar": "🟢 أنت الآن *متاح*.",
        "ur": "🟢 آپ اب *دستیاب* ہیں۔",
    },
    "driver_unavailable": {
        "en": "🔴 You are now marked as *Unavailable*.",
        "ar": "🔴 أنت الآن *غير متاح*.",
        "ur": "🔴 آپ اب *غیر دستیاب* ہیں۔",
    },
    "report_prompt": {
        "en": "Please describe the issue (this will be sent to admins):",
        "ar": "يرجى وصف المشكلة (سيتم إرسالها للمشرفين):",
        "ur": "براہ کرم مسئلے کی وضاحت کریں (یہ ایڈمنز کو بھیجی جائے گی):",
    },
    "report_saved": {
        "en": "✅ Report submitted. Thank you.",
        "ar": "✅ تم إرسال البلاغ. شكرًا.",
        "ur": "✅ رپورٹ جمع ہوگئی۔ شکریہ۔",
    },
    "blocked_user": {
        "en": "🚫 You have been blocked from using this bot.",
        "ar": "🚫 تم حظرك من استخدام هذا البوت.",
        "ur": "🚫 آپ کو اس بوٹ سے بلاک کردیا گیا ہے۔",
    },
    "not_admin": {
        "en": "⛔ You are not authorized to use this command.",
        "ar": "⛔ غير مصرح لك باستخدام هذا الأمر.",
        "ur": "⛔ آپ کو یہ کمانڈ استعمال کرنے کی اجازت نہیں۔",
    },
    "idle_hint": {
        "en": "Use the menu buttons below to get started.",
        "ar": "استخدم أزرار القائمة أدناه للبدء.",
        "ur": "شروع کرنے کے لیے نیچے مینیو بٹن استعمال کریں۔",
    },
    "help_text": {
        "en": (
            "🆘 *RideMatch Help*\n\n"
            "🙋🏻‍♂️ *I need a Ride* — Search for available rides\n"
            "🚙 *I need a Passenger* — Post a ride as a driver\n"
            "📍 *Drop My Pin* — Share your location for better matching\n"
            "🌍 *Language* — Change your language\n"
            "📅 *My Adventures* — View your rides and reservations\n\n"
            "Need more help? Use /report to contact admins."
        ),
        "ar": (
            "🆘 *مساعدة RideMatch*\n\n"
            "🙋🏻‍♂️ *أحتاج سواري* — ابحث عن الرحلات المتاحة\n"
            "🚙 *أحتاج راكب* — انشر رحلة كسائق\n"
            "📍 *حدد موقعي* — شارك موقعك لمطابقة أفضل\n"
            "🌍 *اللغة* — غير لغتك\n"
            "📅 *مغامراتي* — عرض رحلاتك وحجوزاتك\n\n"
            "تحتاج مزيد من المساعدة؟ استخدم /report للتواصل مع المشرفين."
        ),
        "ur": (
            "🆘 *RideMatch مدد*\n\n"
            "🙋🏻‍♂️ *مجھے سواری چاہیے* — دستیاب سواریاں تلاش کریں\n"
            "🚙 *مجھے سوار چاہیے* — بطور ڈرائیور سواری شائع کریں\n"
            "📍 *میرا پن ڈراپ کریں* — بہتر مماثلت کے لیے اپنا مقام شیئر کریں\n"
            "🌍 *زبان* — اپنی زبان تبدیل کریں\n"
            "📅 *میرے ماجرے* — اپنی سواریاں اور ریزرویشنز دیکھیں\n\n"
            "مزید مدد چاہیے؟ /report استعمال کریں ایڈمنز سے رابطہ کرنے کے لیے۔"
        ),
    },
    "no_reservations": {
        "en": "📋 You have no trip reservations.",
        "ar": "📋 ليس لديك حجوزات.",
        "ur": "📋 آپ کی کوئی ریزرویشن نہیں۔",
    },
}


def t(key: str, lang: str = DEFAULT_LANG, **kwargs) -> str:
    """Look up a translated string, falling back to English."""
    text = TEXTS.get(key, {}).get(lang) or TEXTS.get(key, {}).get("en", key)
    if kwargs:
        text = text.format(**kwargs)
    return text
