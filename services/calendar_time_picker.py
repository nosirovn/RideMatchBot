from datetime import datetime
import calendar
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def build_calendar(year=None, month=None):

    now = datetime.now()

    if year is None:
        year = now.year
    if month is None:
        month = now.month

    keyboard = []

    # Month navigation
    keyboard.append([
        InlineKeyboardButton("◀", callback_data=f"cal_prev:{year}:{month}"),
        InlineKeyboardButton(f"{calendar.month_name[month]} {year}", callback_data="ignore"),
        InlineKeyboardButton("▶", callback_data=f"cal_next:{year}:{month}")
    ])

    # Week days
    keyboard.append([
        InlineKeyboardButton(day, callback_data="ignore")
        for day in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
    ])

    month_days = calendar.monthcalendar(year, month)

    for week in month_days:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(" ", callback_data="ignore"))
            else:
                row.append(
                    InlineKeyboardButton(
                        str(day),
                        callback_data=f"day:{year}:{month}:{day}"
                    )
                )
        keyboard.append(row)

    # Hour selection
    hours = list(range(8, 21))  # 08–20

    keyboard.append([InlineKeyboardButton("Select hour", callback_data="ignore")])

    row = []
    for h in hours:
        row.append(
            InlineKeyboardButton(
                f"{h:02d}",
                callback_data=f"hour:{h:02d}"
            )
        )
        if len(row) == 4:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)