export BOT_TOKEN="8477631186:AAHEaJXlgWES9KPafl47yrTAseZ1IgbhKE0"
export ADMIN_IDS="1294613"
python bot.py# RideMatch_Bot 🚗

A production-ready Telegram bot that matches drivers and travelers going between **Makkah** and **Madinah** — a lightweight Uber-style ride-sharing board.

## Features

- **Driver mode** — post a ride with route, date, time, and available seats
- **Traveler mode** — search for matching rides with smart AI-ranked results
- **Seat reservation** — travelers request seats; drivers approve/reject via inline buttons
- **Smart notifications** — travelers are auto-notified when a matching driver posts
- **Driver ratings** — travelers rate drivers ⭐ 1–5 after a ride
- **Multi-language** — English, Arabic, Urdu (selected on first /start)
- **GPS location** — optional location sharing for distance-based matching
- **Real-time availability** — drivers toggle "Available Now" status
- **Anti-spam** — max 3 active posts per user; rides expire after 24 hours
- **Safety** — /report command, admin block/unblock users
- **Admin dashboard** — /admin_stats, /broadcast, delete rides, block users
- **Analytics** — tracks popular routes, busiest hours, demand data
- **SQLite** — lightweight, zero-config database

## Project Structure

```
bot.py                          # Entry point — registers all handlers, starts polling
config.py                       # Configuration, constants, translations
database.py                     # SQLite schema and data-access layer

handlers/
  __init__.py
  start_handler.py              # /start, /cancel, language selection, text router helpers
  driver_handler.py             # /post_driver, /available, driver flow states
  traveler_handler.py           # /find_ride, /my_trips, /report, reservations, ratings
  admin_handler.py              # /admin_stats, /admin_delete_ride, /broadcast, etc.

services/
  __init__.py
  matching_service.py           # Core smart-matching engine
  ai_matching_service.py        # AI/composite-score ranking wrapper
  reservation_service.py        # Seat reservation business logic
  notification_service.py       # Telegram notification delivery
  location_service.py           # Haversine distance & geo-sorting

requirements.txt
README.md
```

## Setup

### 1. Install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Set your bot token

Edit `config.py` and replace `YOUR_BOT_TOKEN_HERE`, or set env vars:

```bash
export BOT_TOKEN="123456:ABC-DEF..."
export ADMIN_IDS="123456789,987654321"   # comma-separated Telegram user IDs
```

### 3. Run the bot

```bash
python bot.py
```

## Bot Commands

| Command | Description |
|---|---|
| `/start` | Welcome, language selection, role picker |
| `/post_driver` | Post a ride as a driver |
| `/find_ride` | Search for available rides |
| `/my_trips` | View your rides (driver) and reservations (traveler) |
| `/available` | Toggle "Available Now" driver status |
| `/report` | Report an issue to admins |
| `/cancel` | Cancel the current operation |

### Admin Commands

| Command | Description |
|---|---|
| `/admin_stats` | Dashboard with analytics |
| `/admin_delete_ride <id>` | Delete any ride |
| `/admin_block_user <id>` | Block a user |
| `/admin_unblock_user <id>` | Unblock a user |
| `/broadcast <message>` | Broadcast to all users (requires `/confirm_broadcast`) |

## Database Tables

| Table | Purpose |
|---|---|
| `users` | Language pref, blocked flag, availability, GPS coords |
| `rides` | Driver-posted rides with seats_total/seats_available |
| `reservations` | Seat requests (pending/approved/rejected) |
| `ratings` | Post-ride driver ratings (1–5 stars) |
| `search_requests` | Saved traveler searches for smart notifications |
| `reports` | User-submitted reports |
| `analytics` | Event log for admin insights |

## Deployment

The bot uses `run_polling()` — works anywhere: VPS, Render, Railway.

For **Render**: create a **Background Worker** service pointing to `python bot.py`.
