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
ROUTE_MK_MD = "Mecca → Medina"
ROUTE_MD_MK = "Medina → Mecca"
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
LANGUAGES = ["en", "ar", "de", "fr", "ru", "uz"]
DEFAULT_LANG = "en"

# ── Translation dictionaries ────────────────────────────────
# Keys used throughout the bot; each maps to {lang: text}.
TEXTS: dict[str, dict[str, str]] = {
    "welcome": {
        "en": (
            " \n"
            "**MECCA <> MEDINA**\n"
            " \n\n"
            "🚗 Find drivers & travelers\n"
            "between Mecca and Medina.\n\n"
            "Choose an option below:"
        ),
        "ar": (
            " \n"
            "**MECCA <> MEDINA**\n"
            " \n\n"
            "🚗 ابحث عن سائقين ومسافرين\n"
            "بين مكة والمدينة.\n\n"
            "اختر أحد الخيارات أدناه:"
        ),
        "de": (
            " \n"
            "**MECCA <> MEDINA**\n"
            " \n\n"
            "🚗 Finde Fahrer und Mitreisende\n"
            "zzwischen Mekka und Medina.\n\n"
            "Wähle eine Option unten:"
        ),
        "fr": (
            " \n"
            "**MECCA <> MEDINA**\n"
            " \n\n"
            "🚗 ConTrouvez des conducteurs et passagers\n"
            "entre La Mecque et Médine.\n\n"
            "Choisissez une option ci-dessous :"
        ),
        "ru": (
            " \n"
            "**MECCA <> MEDINA**\n"
            " \n\n"
            "🚗 Найдите водителей и попутчиков\n"
            "между Меккой и Мединой.\n\n"
            "Выберите опцию ниже:"
        ),
        "uz": (
            " \n"
            "**MECCA <> MEDINA**\n"
            " \n\n"
            "🚗 Makka va Madina o‘rtasida\n"
            "Meccaaydovchilar va yo‘lovchilarni toping.\n\n"
            "Quyidagi variantlardan birini tanlang:"
        ),
    },
    "choose_lang": {
        "en": " \n**SELECT LANGUAGE**\n ",
        "ar": " \n**اختر اللغة**\n ",
        "de": " \n**SPRACHE WÄHLEN**\n ",
        "fr": " \n**CHOISIR LA LANGUE**\n ",
        "ru": " \n**ВЫБЕРИТЕ ЯЗЫК**\n ",
        "uz": " \n**TILNI TANLANG**\n ",
    },
    "driver_mode": {
        "en": " \n**DRIVER MODE**\n \n\nSelect your route:",
        "ar": " \n**وضع السائق**\n \n\nاختر مسارك:",
        "de": " \n**FAHRERMODUS**\n \n\nWähle deine Route:",
        "fr": " \n**MODE CONDUCTEUR**\n \n\nSélectionnez votre itinéraire :",
        "ru": " \n**РЕЖИМ ВОДИТЕЛЯ**\n \n\nВыберите маршрут:",
        "uz": " \n**HAYDOVCHI REJIMI**\n \n\nYoʻnalingizni tanlang:",
    },
    "traveler_mode": {
        "en": " \n**TRAVELER MODE**\n \n\nSelect your route:",
        "ar": " \n**وضع المسافر**\n \n\nاختر مسارك:",
        "de": " \n**REISENDENMODUS**\n \n\nWähle deine Route:",
        "fr": " \n**MODE VOYAGEUR**\n \n\nSélectionnez votre itinéraire :",
        "ru": " \n**РЕЖИМ ПОПУТЧИКА**\n \n\nВыберите маршрут:",
        "uz": " \n**SAYOHATCHI REJIMI**\n \n\nYoʻnalingizni tanlang:",
    },
    "select_route": {
        "en": " \n**SELECT ROUTE**\n ",
        "ar": " \n**اختر المسار**\n ",
        "de": " \n**ROUTE WÄHLEN**\n ",
        "fr": " \n**CHOISIR L'ITINÉRAIRE**\n ",
        "ru": " \n**ВЫБЕРИТЕ МАРШРУТ**\n ",
        "uz": " \n**YOʻNALISHNI TANLANG**\n ",
    },
    "enter_date": {
        "en": "📅 Enter the date (DD/MM/YYYY):",
        "ar": "📅 أدخل التاريخ (DD/MM/YYYY):",
        "de": "📅 Datum eingeben (TT/MM/JJJJ):",
        "fr": "📅 Entrez la date (JJ/MM/AAAA) :",
        "ru": "📅 Введите дату (ДД/ММ/ГГГГ):",
        "uz": "📅 Sanani kiriting (KK/OO/YYYY):",
    },
    "enter_time": {
        "en": "⏰ Enter departure time (HH:MM, 24-hour format):",
        "ar": "⏰ أدخل وقت المغادرة (HH:MM):",
        "de": "⏰ Abfahrtszeit eingeben (HH:MM, 24h):",
        "fr": "⏰ Heure de départ (HH:MM, format 24h) :",
        "ru": "⏰ Время отправления (ЧЧ:ММ, 24ч):",
        "uz": "⏰ Joʻnash vaqtini kiriting (SS:DD, 24s):",
    },
    "enter_seats": {
        "en": " \n**AVAILABLE SEATS**\n \n\n💺 Select number of seats:",
        "ar": " \n**المقاعد المتاحة**\n \n\n💺 اختر عدد المقاعد:",
        "de": " \n**VERFÜGBARE SITZE**\n \n\n💺 Sitzanzahl wählen:",
        "fr": " \n**PLACES DISPONIBLES**\n \n\n💺 Sélectionnez le nombre de places :",
        "ru": " \n**ДОСТУПНЫЕ МЕСТА**\n \n\n💺 Выберите количество мест:",
        "uz": " \n**BOʻSH OʻRINDIQLAR**\n \n\n💺 Oʻrindiqlar sonini tanlang:",
    },
    "enter_passengers": {
        "en": " \n**PASSENGERS**\n \n\n👥 Select number of passengers:",
        "ar": " \n**الركاب**\n \n\n👥 اختر عدد الركاب:",
        "de": " \n**PASSAGIERE**\n \n\n👥 Passagieranzahl wählen:",
        "fr": " \n**PASSAGERS**\n \n\n👥 Sélectionnez le nombre de passagers :",
        "ru": " \n**ПАССАЖИРЫ**\n \n\n👥 Выберите количество пассажиров:",
        "uz": " \n**YOʻLOVCHILAR**\n \n\n👥 Yoʻlovchilar sonini tanlang:",
    },
    "ride_posted": {
        "en": "✅ *Ride posted!*",
        "ar": "✅ *تم نشر الرحلة!*",
        "de": "✅ *Fahrt veröffentlicht!*",
        "fr": "✅ *Trajet publié !*",
        "ru": "✅ *Поездка опубликована!*",
        "uz": "✅ *Safar eʼlon qilindi!*",
    },
    "no_rides_found": {
        "en": (
            " \n"
            "**NO RIDES FOUND**\n"
            " \n\n"
            "😔 No drivers for *{route}*\n"
            "on *{date}*.\n\n"
            "Your search has been saved —\n"
            "you'll be notified when a match appears."
        ),
        "ar": (
            " \n"
            "**لا رحلات**\n"
            " \n\n"
            "😔 لم يتم العثور على سائقين لـ *{route}*\n"
            "في *{date}*.\n\n"
            "تم حفظ بحثك — سيتم إبلاغك عند توفر رحلة مطابقة."
        ),
        "de": (
            " \n"
            "**KEINE FAHRTEN**\n"
            " \n\n"
            "😔 Keine Fahrer für *{route}*\n"
            "am *{date}*.\n\n"
            "Suche gespeichert — du wirst benachrichtigt."
        ),
        "fr": (
            " \n"
            "**AUCUN TRAJET**\n"
            " \n\n"
            "😔 Aucun conducteur pour *{route}*\n"
            "le *{date}*.\n\n"
            "Recherche sauvegardée — vous serez notifié."
        ),
        "ru": (
            " \n"
            "**ПОЕЗДКИ НЕ НАЙДЕНЫ**\n"
            " \n\n"
            "😔 Нет водителей на *{route}*\n"
            "на *{date}*.\n\n"
            "Поиск сохранён — вы получите уведомление."
        ),
        "uz": (
            " \n"
            "**SAFAR TOPILMADI**\n"
            " \n\n"
            "😔 *{route}* boʻyicha *{date}*\n"
            "da haydovchi topilmadi.\n\n"
            "Qidiruvingiz saqlandi — mos safar chiqqanda xabar beramiz."
        ),
    },
    "rides_found": {
        "en": " \n**{count} RIDE(S) FOUND**\n \n",
        "ar": " \n**{count} رحلة متاحة**\n \n",
        "de": " \n**{count} FAHRT(EN)**\n \n",
        "fr": " \n**{count} TRAJET(S)**\n \n",
        "ru": " \n**НАЙДЕНО {count}**\n \n",
        "uz": " \n**{count} SAFAR TOPILDI**\n \n",
    },
    "cancelled": {
        "en": " \n**CANCELLED**\n \n\nUse /start to begin again.",
        "ar": " \n**تم الإلغاء**\n \n\nاستخدم /start للبدء مجددًا.",
        "de": " \n**ABGEBROCHEN**\n \n\nVerwende /start um neu zu beginnen.",
        "fr": " \n**ANNULÉ**\n \n\nUtilisez /start pour recommencer.",
        "ru": " \n**ОТМЕНЕНО**\n \n\nИспользуйте /start для начала.",
        "uz": " \n**BEKOR QILINDI**\n \n\nQaytadan boshlash uchun /start yozing.",
    },
    "spam_limit": {
        "en": " \n**LIMIT REACHED ⚠️**\n \n\nYou have 3 active posts.\nDelete one with /my_posts first.\n\n ",
        "ar": " \n**تم بلوغ الحد ⚠️**\n \n\nلديك 3 منشورات نشطة.\nاحذف واحدًا أولاً بـ /my_posts.\n\n ",
        "de": " \n**LIMIT ERREICHT ⚠️**\n \n\nDu hast 3 aktive Posts.\nLösche einen mit /my_posts.\n\n ",
        "fr": " \n**LIMITE ATTEINTE ⚠️**\n \n\nVous avez 3 publications actives.\nSupprimez-en une avec /my_posts.\n\n ",
        "ru": " \n**ЛИМИТ ДОСТИГНУТ ⚠️**\n \n\nУ вас 3 активных поездки.\nУдалите одну через /my_posts.\n\n ",
        "uz": " \n**CHEGARAGA YETILDI ⚠️**\n \n\nSizda 3 ta faol post bor.\n/my_posts orqali birini oʻchiring.\n\n ",
    },
    "invalid_date": {
        "en": "Invalid format. Please enter date as DD/MM/YYYY:",
        "ar": "تنسيق غير صالح. أدخل التاريخ كـ DD/MM/YYYY:",
        "de": "Ungültiges Format. Bitte TT/MM/JJJJ eingeben:",
        "fr": "Format invalide. Entrez la date au format JJ/MM/AAAA :",
        "ru": "Неверный формат. Введите дату ДД/ММ/ГГГГ:",
        "uz": "Notoʻgʻri format. Sanani KK/OO/YYYY shaklida kiriting:",
    },
    "past_date": {
        "en": "Date cannot be in the past. Please enter a future date:",
        "ar": "لا يمكن أن يكون التاريخ في الماضي. أدخل تاريخًا مستقبليًا:",
        "de": "Datum darf nicht in der Vergangenheit liegen:",
        "fr": "La date ne peut pas être dans le passé :",
        "ru": "Дата не может быть в прошлом:",
        "uz": "Sana oʻtgan bo'lishi mumkin emas:",
    },
    "invalid_time": {
        "en": "Invalid format. Enter time as HH:MM (e.g. 14:30):",
        "ar": "تنسيق غير صالح. أدخل الوقت كـ HH:MM:",
        "de": "Ungültiges Format. Zeit als HH:MM eingeben:",
        "fr": "Format invalide. Entrez l'heure au format HH:MM :",
        "ru": "Неверный формат. Введите время ЧЧ:ММ:",
        "uz": "Notoʻgʻri format. Vaqtni SS:DD shaklida kiriting:",
    },
    "number_1_10": {
        "en": "Please select a number using the buttons above.",
        "ar": "يرجى اختيار رقم باستخدام الأزرار أعلاه.",
        "de": "Bitte wähle eine Nummer mit den Buttons oben.",
        "fr": "Veuillez sélectionner un nombre avec les boutons ci-dessus.",
        "ru": "Выберите число с помощью кнопок выше.",
        "uz": "Iltimos, yuqoridagi tugmalardan raqam tanlang.",
    },
    "choose_role_btn": {
        "en": " \n**RIDEMATCH**\n \n\nPlease choose an option using the buttons below.\n\n ",
        "ar": " \n**RIDEMATCH**\n \n\nاختر خيارًا باستخدام الأزرار أدناه.\n\n ",
        "de": " \n**RIDEMATCH**\n \n\nBitte wähle eine Option mit den Buttons unten.\n\n ",
        "fr": " \n**RIDEMATCH**\n \n\nVeuillez choisir une option ci-dessous.\n\n ",
        "ru": " \n**RIDEMATCH**\n \n\nВыберите опцию с помощью кнопок ниже.\n\n ",
        "uz": " \n**RIDEMATCH**\n \n\nQuyidagi tugmalardan variantni tanlang.\n\n ",
    },
    "location_saved": {
        "en": " \n**LOCATION SAVED**\n \n\n📍 This helps match you with nearby drivers.\n\n ",
        "ar": " \n**تم حفظ الموقع**\n \n\n📍 يساعد في مطابقتك مع السائقين القريبين.\n\n ",
        "de": " \n**STANDORT GESPEICHERT**\n \n\n📍 Hilft bei der Zuordnung zu nahen Fahrern.\n\n ",
        "fr": " \n**POSITION ENREGISTRÉE**\n \n\n📍 Aide à vous connecter avec des conducteurs proches.\n\n ",
        "ru": " \n**МЕСТОПОЛОЖЕНИЕ СОХРАНЕНО**\n \n\n📍 Поможет найти ближайших водителей.\n\n ",
        "uz": " \n**JOYLASHUV SAQLANDI**\n \n\n📍 Yaqin haydovchilarni topishga yordam beradi.\n\n ",
    },
    "choose_route_btn": {
        "en": " \n**SELECT ROUTE**\n \n\nPlease select a valid route using the buttons.\n\n ",
        "ar": " \n**اختر المسار**\n \n\nاختر مسارًا صالحًا باستخدام الأزرار.\n\n ",
        "de": " \n**ROUTE WÄHLEN**\n \n\nBitte wähle eine gültige Route mit den Buttons.\n\n ",
        "fr": " \n**CHOISIR L'ITINÉRAIRE**\n \n\nVeuillez sélectionner un itinéraire valide.\n\n ",
        "ru": " \n**ВЫБЕРИТЕ МАРШРУТ**\n \n\nВыберите маршрут с помощью кнопок.\n\n ",
        "uz": " \n**YOʻNALISHNI TANLANG**\n \n\nTugmalar yordamida yoʻnalish tanlang.\n\n ",
    },
    "no_active_posts": {
        "en": " \n**NO ACTIVE POSTS**\n \n\n📋 You have no active posts.\n\n ",
        "ar": " \n**لا منشورات**\n \n\n📋 ليس لديك منشورات نشطة.\n\n ",
        "de": " \n**KEINE AKTIVEN POSTS**\n \n\n📋 Keine aktiven Posts vorhanden.\n\n ",
        "fr": " \n**AUCUNE PUBLICATION**\n \n\n📋 Aucune publication active.\n\n ",
        "ru": " \n**НЕТ АКТИВНЫХ ПОЕЗДОК**\n \n\n📋 У вас нет активных поездок.\n\n ",
        "uz": " \n**FAOL POSTLAR YOʻQ**\n \n\n📋 Sizda faol postlar yoʻq.\n\n ",
    },
    "post_deleted": {
        "en": " \n**POST DELETED ✅**\n ",
        "ar": " \n**تم الحذف ✅**\n ",
        "de": " \n**POST GELÖSCHT ✅**\n ",
        "fr": " \n**SUPPRIMÉ ✅**\n ",
        "ru": " \n**УДАЛЕНО ✅**\n ",
        "uz": " \n**OʻCHIRILDI ✅**\n ",
    },
    "post_not_found": {
        "en": " \n**NOT FOUND ❌**\n \n\nPost not found or you don't own it.\n\n ",
        "ar": " \n**غير موجود ❌**\n \n\nالمنشور غير موجود أو لا تملكه.\n\n ",
        "de": " \n**NICHT GEFUNDEN ❌**\n \n\nPost nicht gefunden oder gehört dir nicht.\n\n ",
        "fr": " \n**INTROUVABLE ❌**\n \n\nPublication introuvable ou ne vous appartient pas.\n\n ",
        "ru": " \n**НЕ НАЙДЕНО ❌**\n \n\nПоездка не найдена или не ваша.\n\n ",
        "uz": " \n**TOPILMADI ❌**\n \n\nPost topilmadi yoki sizga tegishli emas.\n\n ",
    },
    "new_ride_notif": {
        "en": (
            " \n"
            "**NEW RIDE**\n"
            " \n\n"
            "🚗 Driver: [{name}](tg://user?id={driver_id})\n"
            "📍 Route: {route}\n"
            "📅 Date: {date}\n"
            "⏰ Time: {time}\n"
            "💺 Seats: {seats}\n\n"
            " "
        ),
        "ar": (
            " \n"
            "**رحلة جديدة**\n"
            " \n\n"
            "🚗 السائق: [{name}](tg://user?id={driver_id})\n"
            "📍 المسار: {route}\n"
            "📅 التاريخ: {date}\n"
            "⏰ الوقت: {time}\n"
            "💺 المقاعد: {seats}\n\n"
            " "
        ),
        "de": (
            " \n"
            "**NEUE FAHRT**\n"
            " \n\n"
            "🚗 Fahrer: [{name}](tg://user?id={driver_id})\n"
            "📍 Route: {route}\n"
            "📅 Datum: {date}\n"
            "⏰ Zeit: {time}\n"
            "💺 Sitze: {seats}\n\n"
            " "
        ),
        "fr": (
            " \n"
            "**NOUVEAU TRAJET**\n"
            " \n\n"
            "🚗 Conducteur: [{name}](tg://user?id={driver_id})\n"
            "📍 Itinéraire: {route}\n"
            "📅 Date: {date}\n"
            "⏰ Heure: {time}\n"
            "💺 Places: {seats}\n\n"
            " "
        ),
        "ru": (
            " \n"
            "**НОВАЯ ПОЕЗДКА**\n"
            " \n\n"
            "🚗 Водитель: [{name}](tg://user?id={driver_id})\n"
            "📍 Маршрут: {route}\n"
            "📅 Дата: {date}\n"
            "⏰ Время: {time}\n"
            "💺 Места: {seats}\n\n"
            " "
        ),
        "uz": (
            " \n"
            "**YANGI SAFAR**\n"
            " \n\n"
            "🚗 Haydovchi: [{name}](tg://user?id={driver_id})\n"
            "📍 Yoʻnalish: {route}\n"
            "📅 Sana: {date}\n"
            "⏰ Vaqt: {time}\n"
            "💺 Oʻrinlar: {seats}\n\n"
            " "
        ),
    },
    "reservation_request": {
        "en": (
            " \n"
            "**RESERVATION REQUEST**\n"
            " \n\n"
            "👤 Traveler: [{traveler}](tg://user?id={traveler_id})\n"
            "📍 Route: {route}\n"
            "📅 Date: {date}\n"
            "💺 Seats: {seats}"
        ),
        "ar": (
            " \n"
            "**طلب حجز**\n"
            " \n\n"
            "👤 المسافر: [{traveler}](tg://user?id={traveler_id})\n"
            "📍 المسار: {route}\n"
            "📅 التاريخ: {date}\n"
            "💺 المقاعد: {seats}"
        ),
        "de": (
            " \n"
            "**RESERVIERUNGSANFRAGE**\n"
            " \n\n"
            "👤 Reisender: [{traveler}](tg://user?id={traveler_id})\n"
            "📍 Route: {route}\n"
            "📅 Datum: {date}\n"
            "💺 Sitze: {seats}"
        ),
        "fr": (
            " \n"
            "**DEMANDE DE RÉSERVATION**\n"
            " \n\n"
            "👤 Voyageur: [{traveler}](tg://user?id={traveler_id})\n"
            "📍 Itinéraire: {route}\n"
            "📅 Date: {date}\n"
            "💺 Places: {seats}"
        ),
        "ru": (
            " \n"
            "**ЗАПРОС БРОНИ**\n"
            " \n\n"
            "👤 Попутчик: [{traveler}](tg://user?id={traveler_id})\n"
            "📍 Маршрут: {route}\n"
            "📅 Дата: {date}\n"
            "💺 Места: {seats}"
        ),
        "uz": (
            " \n"
            "**BAND QILISH SOʻROVI**\n"
            " \n\n"
            "👤 Sayohatchi: [{traveler}](tg://user?id={traveler_id})\n"
            "📍 Yoʻnalish: {route}\n"
            "📅 Sana: {date}\n"
            "💺 Oʻrinlar: {seats}"
        ),
    },
    "reservation_approved": {
        "en": (
            " \n"
            "**APPROVED ✅**\n"
            " \n\n"
            "🚗 Driver: [{driver}](tg://user?id={driver_id})\n"
            "📍 Route: {route}\n"
            "📅 Date: {date}\n"
            "⏰ Time: {time}\n\n"
            " "
        ),
        "ar": (
            " \n"
            "**تمت الموافقة ✅**\n"
            " \n\n"
            "🚗 السائق: [{driver}](tg://user?id={driver_id})\n"
            "📍 المسار: {route}\n"
            "📅 التاريخ: {date}\n"
            "⏰ الوقت: {time}\n\n"
            " "
        ),
        "de": (
            " \n"
            "**GENEHMIGT ✅**\n"
            " \n\n"
            "🚗 Fahrer: [{driver}](tg://user?id={driver_id})\n"
            "📍 Route: {route}\n"
            "📅 Datum: {date}\n"
            "⏰ Zeit: {time}\n\n"
            " "
        ),
        "fr": (
            " \n"
            "**APPROUVÉ ✅**\n"
            " \n\n"
            "🚗 Conducteur: [{driver}](tg://user?id={driver_id})\n"
            "📍 Itinéraire: {route}\n"
            "📅 Date: {date}\n"
            "⏰ Heure: {time}\n\n"
            " "
        ),
        "ru": (
            " \n"
            "**ОДОБРЕНО ✅**\n"
            " \n\n"
            "🚗 Водитель: [{driver}](tg://user?id={driver_id})\n"
            "📍 Маршрут: {route}\n"
            "📅 Дата: {date}\n"
            "⏰ Время: {time}\n\n"
            " "
        ),
        "uz": (
            " \n"
            "**TASDIQLANDI ✅**\n"
            " \n\n"
            "🚗 Haydovchi: [{driver}](tg://user?id={driver_id})\n"
            "📍 Yoʻnalish: {route}\n"
            "📅 Sana: {date}\n"
            "⏰ Vaqt: {time}\n\n"
            " "
        ),
    },
    "reservation_rejected": {
        "en": " \n**REJECTED ❌**\n \n\nYour reservation was rejected by the driver.",
        "ar": " \n**مرفوض ❌**\n \n\nتم رفض حجزك من قبل السائق.",
        "de": " \n**ABGELEHNT ❌**\n \n\nDeine Reservierung wurde vom Fahrer abgelehnt.",
        "fr": " \n**REFUSÉ ❌**\n \n\nVotre réservation a été refusée par le conducteur.",
        "ru": " \n**ОТКАЗАНО ❌**\n \n\nВаша бронь отклонена водителем.",
        "uz": " \n**RAD ETILDI ❌**\n \n\nBand qilish haydovchi tomonidan rad etildi.",
    },
    "rate_prompt": {
        "en": " \n**RATE YOUR RIDE**\n \n\n⭐ How was your ride? (1–5 stars):",
        "ar": " \n**قيّم رحلتك**\n \n\n⭐ كيف كانت رحلتك؟ (1–5 نجوم):",
        "de": " \n**BEWERTE DEINE FAHRT**\n \n\n⭐ Wie war deine Fahrt? (1–5 Sterne):",
        "fr": " \n**NOTEZ VOTRE TRAJET**\n \n\n⭐ Comment était votre trajet ? (1–5 étoiles) :",
        "ru": " \n**ОЦЕНИТЕ ПОЕЗДКУ**\n \n\n⭐ Как прошла поездка? (1–5 звёзд):",
        "uz": " \n**SAFARNI BAHOLANG**\n \n\n⭐ Safar qanday boʻldi? (1–5 yulduz):",
    },
    "rating_saved": {
        "en": " \n**RATING SAVED ✅**\n \n\nThank you! ⭐ {rating}/5\n\n ",
        "ar": " \n**تم حفظ التقييم ✅**\n \n\nشكرًا! ⭐ {rating}/5\n\n ",
        "de": " \n**BEWERTUNG GESPEICHERT ✅**\n \n\nDanke! ⭐ {rating}/5\n\n ",
        "fr": " \n**NOTE ENREGISTRÉE ✅**\n \n\nMerci ! ⭐ {rating}/5\n\n ",
        "ru": " \n**ОЦЕНКА СОХРАНЕНА ✅**\n \n\nСпасибо! ⭐ {rating}/5\n\n ",
        "uz": " \n**BAHO SAQLANDI ✅**\n \n\nRahmat! ⭐ {rating}/5\n\n ",
    },
    "driver_available_now": {
        "en": " \n**AVAILABLE 🟢**\n \n\nYou are now marked as *Available*.\n\n ",
        "ar": " \n**متاح 🟢**\n \n\nأنت الآن *متاح*.\n\n ",
        "de": " \n**VERFÜGBAR 🟢**\n \n\nDu bist jetzt als *Verfügbar* markiert.\n\n ",
        "fr": " \n**DISPONIBLE 🟢**\n \n\nVous êtes maintenant marqué comme *Disponible*.\n\n ",
        "ru": " \n**ДОСТУПЕН 🟢**\n \n\nВы отмечены как *Доступен*.\n\n ",
        "uz": " \n**MAVJUD 🟢**\n \n\nSiz hozir *Mavjud* deb belgilandingiz.\n\n ",
    },
    "driver_unavailable": {
        "en": " \n**UNAVAILABLE 🔴**\n \n\nYou are now marked as *Unavailable*.\n\n ",
        "ar": " \n**غير متاح 🔴**\n \n\nأنت الآن *غير متاح*.\n\n ",
        "de": " \n**NICHT VERFÜGBAR 🔴**\n \n\nDu bist jetzt als *Nicht verfügbar* markiert.\n\n ",
        "fr": " \n**INDISPONIBLE 🔴**\n \n\nVous êtes maintenant marqué comme *Indisponible*.\n\n ",
        "ru": " \n**НЕДОСТУПЕН 🔴**\n \n\nВы отмечены как *Недоступен*.\n\n ",
        "uz": " \n**MAVJUD EMAS 🔴**\n \n\nSiz hozir *Mavjud emas* deb belgilandingiz.\n\n ",
    },
    "report_prompt": {
        "en": " \n**REPORT ISSUE**\n \n\nDescribe the issue (sent to admins):",
        "ar": " \n**إبلاغ**\n \n\nيرجى وصف المشكلة (سيتم إرسالها للمشرفين):",
        "de": " \n**PROBLEM MELDEN**\n \n\nBeschreibe das Problem (wird an Admins gesendet):",
        "fr": " \n**SIGNALEMENT**\n \n\nDécrivez le problème (envoyé aux admin) :",
        "ru": " \n**ЖАЛОБА**\n \n\nОпишите проблему (будет отправлено админам):",
        "uz": " \n**HISOBOT**\n \n\nMuammoni tavsiflang (adminlarga yuboriladi):",
    },
    "report_saved": {
        "en": " \n**REPORT SENT ✅**\n \n\nThank you. Your report has been submitted.\n\n ",
        "ar": " \n**تم الإرسال ✅**\n \n\nشكرًا. تم إرسال بلاغك.\n\n ",
        "de": " \n**BERICHT GESENDET ✅**\n \n\nDanke. Dein Bericht wurde gesendet.\n\n ",
        "fr": " \n**SIGNALEMENT ENVOYÉ ✅**\n \n\nMerci. Votre signalement a été envoyé.\n\n ",
        "ru": " \n**ЖАЛОБА ОТПРАВЛЕНА ✅**\n \n\nСпасибо. Жалоба отправлена.\n\n ",
        "uz": " \n**HISOBOT YUBORILDI ✅**\n \n\nRahmat. Hisobotingiz yuborildi.\n\n ",
    },
    "blocked_user": {
        "en": " \n**BLOCKED 🚫**\n \n\nYou have been blocked from using this bot.\n\n ",
        "ar": " \n**محظور 🚫**\n \n\nتم حظرك من استخدام هذا البوت.\n\n ",
        "de": " \n**GESPERRT 🚫**\n \n\nDu wurdest für diesen Bot gesperrt.\n\n ",
        "fr": " \n**BLOQUÉ 🚫**\n \n\nVous avez été bloqué de ce bot.\n\n ",
        "ru": " \n**ЗАБЛОКИРОВАНО 🚫**\n \n\nВы заблокированы в этом боте.\n\n ",
        "uz": " \n**BLOKLANGAN 🚫**\n \n\nSiz ushbu botdan bloklangansiz.\n\n ",
    },
    "not_admin": {
        "en": " \n**ACCESS DENIED ⛔**\n \n\nYou are not authorized to use this command.\n\n ",
        "ar": " \n**غير مصرح ⛔**\n \n\nغير مصرح لك باستخدام هذا الأمر.\n\n ",
        "de": " \n**ZUGRIFF VERWEIGERT ⛔**\n \n\nDu bist nicht berechtigt.\n\n ",
        "fr": " \n**ACCÈS REFUSÉ ⛔**\n \n\nVous n'êtes pas autorisé à utiliser cette commande.\n\n ",
        "ru": " \n**ДОСТУП ЗАПРЕЩЁН ⛔**\n \n\nУ вас нет прав для этой команды.\n\n ",
        "uz": " \n**RUXSAT YOʻQ ⛔**\n \n\nSizga bu buyruqdan foydalanishga ruxsat yoʻq.\n\n ",
    },
    "idle_hint": {
        "en": " \n**RIDEMATCH**\n \n\nUse the menu buttons below to get started.\n\n ",
        "ar": " \n**RIDEMATCH**\n \n\nاستخدم أزرار القائمة أدناه للبدء.\n\n ",
        "de": " \n**RIDEMATCH**\n \n\nVerwende die Menü-Buttons unten.\n\n ",
        "fr": " \n**RIDEMATCH**\n \n\nUtilisez les boutons du menu ci-dessous.\n\n ",
        "ru": " \n**RIDEMATCH**\n \n\nИспользуйте кнопки меню ниже.\n\n ",
        "uz": " \n**RIDEMATCH**\n \n\nBoshlash uchun quyidagi menyu tugmalarini ishlating.\n\n ",
    },
    "help_text": {
        "en": (
            " \n"
            "**RIDEMATCH HELP**\n"
            " \n\n"
            "🙋🏻‍♂️ *I need a Ride* — Search for rides\n"
            "🚙 *I need a Passenger* — Post a ride\n"
            "📍 *Drop My Pin* — Share location\n"
            "🌍 *Language* — Change language\n"
            "📅 *My Adventures* — Your trips\n\n"
            " \n"
            "**RATING SYSTEM**\n"
            " \n\n"
            "⭐ After each ride, travelers can rate\n"
            "the driver from 1 to 5 stars.\n"
            "Ratings are shown next to the driver's\n"
            "name in search results.\n"
            "Higher ratings = more visibility.\n\n"
            " \n"
            "**BONUS SYSTEM**\n"
            " \n\n"
            "🏆 *Active Driver Bonus:*\n"
            "Post 5+ rides → priority in search.\n\n"
            "🌟 *Top Rated Bonus:*\n"
            "Keep 4.5+ avg rating → gold badge.\n\n"
            "🎯 *Referral Bonus:*\n"
            "Invite friends → unlock premium features.\n\n"
            "Need help? Use /report\n"
            " "
        ),
        "ar": (
            " \n"
            "**مساعدة RIDEMATCH**\n"
            " \n\n"
            "🙋🏻‍♂️ *أحتاج سواري* — البحث عن رحلات\n"
            "🚙 *أحتاج راكب* — نشر رحلة\n"
            "📍 *حدد موقعي* — مشاركة الموقع\n"
            "🌍 *اللغة* — تغيير اللغة\n"
            "📅 *مغامراتي* — رحلاتك\n\n"
            " \n"
            "**نظام التقييم**\n"
            " \n\n"
            "⭐ بعد كل رحلة، يمكن للمسافرين\n"
            "تقييم السائق من 1 إلى 5 نجوم.\n"
            "يظهر التقييم بجوار اسم السائق\n"
            "في نتائج البحث.\n"
            "تقييم أعلى = ظهور أكثر.\n\n"
            " \n"
            "**نظام المكافآت**\n"
            " \n\n"
            "🏆 *مكافأة السائق النشط:*\n"
            "انشر 5+ رحلات → أولوية في البحث.\n\n"
            "🌟 *مكافأة الأعلى تقييماً:*\n"
            "حافظ على 4.5+ → شارة ذهبية.\n\n"
            "🎯 *مكافأة الإحالة:*\n"
            "ادعُ أصدقاء → ميزات مميزة.\n\n"
            "تحتاج مساعدة؟ استخدم /report\n"
            " "
        ),
        "de": (
            " \n"
            "**RIDEMATCH HILFE**\n"
            " \n\n"
            "🙋🏻‍♂️ *Ich brauche eine Fahrt* — Suchen\n"
            "🚙 *Ich brauche einen Passagier* — Anbieten\n"
            "📍 *Meinen Pin setzen* — Standort teilen\n"
            "🌍 *Sprache* — Sprache ändern\n"
            "📅 *Meine Abenteuer* — Deine Fahrten\n\n"
            " \n"
            "**BEWERTUNGSSYSTEM**\n"
            " \n\n"
            "⭐ Nach jeder Fahrt können Reisende\n"
            "den Fahrer mit 1–5 Sternen bewerten.\n"
            "Bewertungen erscheinen neben dem\n"
            "Namen in den Suchergebnissen.\n"
            "Höhere Bewertung = mehr Sichtbarkeit.\n\n"
            " \n"
            "**BONUSSYSTEM**\n"
            " \n\n"
            "🏆 *Aktiver Fahrer Bonus:*\n"
            "5+ Fahrten → Priorität in der Suche.\n\n"
            "🌟 *Top-Bewertung Bonus:*\n"
            "4.5+ Durchschnitt → goldenes Abzeichen.\n\n"
            "🎯 *Empfehlungsbonus:*\n"
            "Freunde einladen → Premium-Features.\n\n"
            "Hilfe? Verwende /report\n"
            " "
        ),
        "fr": (
            " \n"
            "**AIDE RIDEMATCH**\n"
            " \n\n"
            "🙋🏻‍♂️ *J'ai besoin d'un trajet* — Chercher\n"
            "🚙 *J'ai besoin d'un passager* — Publier\n"
            "📍 *Mon emplacement* — Partager la position\n"
            "🌍 *Langue* — Changer la langue\n"
            "📅 *Mes aventures* — Vos trajets\n\n"
            " \n"
            "**SYSTÈME DE NOTATION**\n"
            " \n\n"
            "⭐ Après chaque trajet, les voyageurs\n"
            "peuvent noter le conducteur de 1 à 5.\n"
            "Les notes s'affichent dans les résultats.\n"
            "Meilleure note = plus de visibilité.\n\n"
            " \n"
            "**SYSTÈME DE BONUS**\n"
            " \n\n"
            "🏆 *Bonus conducteur actif :*\n"
            "5+ trajets → priorité dans les résultats.\n\n"
            "🌟 *Bonus meilleure note :*\n"
            "Moyenne 4.5+ → badge doré.\n\n"
            "🎯 *Bonus parrainage :*\n"
            "Invitez des amis → fonctions premium.\n\n"
            "Besoin d'aide ? Utilisez /report\n"
            " "
        ),
        "ru": (
            " \n"
            "**ПОМОЩЬ RIDEMATCH**\n"
            " \n\n"
            "🙋🏻‍♂️ *Мне нужна поездка* — Поиск\n"
            "🚙 *Мне нужен пассажир* — Предложить\n"
            "📍 *Мой пин* — Отправить геолокацию\n"
            "🌍 *Язык* — Сменить язык\n"
            "📅 *Мои приключения* — Ваши поездки\n\n"
            " \n"
            "**СИСТЕМА РЕЙТИНГА**\n"
            " \n\n"
            "⭐ После каждой поездки попутчик\n"
            "может оценить водителя (1–5 звёзд).\n"
            "Рейтинг отображается в результатах.\n"
            "Выше рейтинг = больше видимость.\n\n"
            " \n"
            "**БОНУСНАЯ СИСТЕМА**\n"
            " \n\n"
            "🏆 *Бонус активного водителя:*\n"
            "5+ поездок → приоритет в поиске.\n\n"
            "🌟 *Бонус высокого рейтинга:*\n"
            "Средняя 4.5+ → золотой значок.\n\n"
            "🎯 *Реферальный бонус:*\n"
            "Пригласите друзей → премиум-функции.\n\n"
            "Нужна помощь? Используйте /report\n"
            " "
        ),
        "uz": (
            " \n"
            "**RIDEMATCH YORDAM**\n"
            " \n\n"
            "🙋🏻‍♂️ *Menga safar kerak* — Qidirish\n"
            "🚙 *Menga yoʻlovchi kerak* — Eʼlon berish\n"
            "📍 *Joylashuvim* — Joylashuvni ulashish\n"
            "🌍 *Til* — Tilni oʻzgartirish\n"
            "📅 *Sarguzashtlarim* — Safarlaringiz\n\n"
            " \n"
            "**REYTING TIZIMI**\n"
            " \n\n"
            "⭐ Har safardan soʻng sayohatchi\n"
            "haydovchini 1–5 yulduz bilan baholaydi.\n"
            "Reyting qidiruv natijalarida koʻrinadi.\n"
            "Yuqori reyting = koʻproq koʻrinish.\n\n"
            " \n"
            "**BONUS TIZIMI**\n"
            " \n\n"
            "🏆 *Faol haydovchi bonusi:*\n"
            "5+ safar → qidiruvda ustuvorlik.\n\n"
            "🌟 *Yuqori reyting bonusi:*\n"
            "Oʻrtacha 4.5+ → oltin nishon.\n\n"
            "🎯 *Tavsiya bonusi:*\n"
            "Doʻstlarni taklif qiling → premium imkoniyatlar.\n\n"
            "Yordam kerakmi? /report yozing\n"
            " "
        ),
    },
    "no_reservations": {
        "en": " \n**NO RESERVATIONS**\n \n\n📋 You have no trip reservations.",
        "ar": " \n**لا حجوزات**\n \n\n📋 ليس لديك حجوزات.",
        "de": " \n**KEINE RESERVIERUNGEN**\n \n\n📋 Keine Reservierungen vorhanden.",
        "fr": " \n**AUCUNE RÉSERVATION**\n \n\n📋 Aucune réservation.",
        "ru": " \n**НЕТ БРОНЕЙ**\n \n\n📋 У вас нет бронирований.",
        "uz": " \n**BAND QILISHLAR YOʻQ**\n \n\n📋 Sizda band qilishlar yoʻq.",
    },
}


def t(key: str, lang: str = DEFAULT_LANG, **kwargs) -> str:
    """Look up a translated string, falling back to English."""
    text = TEXTS.get(key, {}).get(lang) or TEXTS.get(key, {}).get("en", key)
    if kwargs:
        text = text.format(**kwargs)
    return text
