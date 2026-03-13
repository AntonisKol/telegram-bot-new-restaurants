# Telegram Berlin Restaurants Bot

This bot tracks new restaurants in Berlin from OpenStreetMap (via the Overpass API) and sends daily updates to a Telegram chat. It is fully automated and can run via GitHub Actions.

---

## Features

- Fetches restaurants added in the last 24 hours.
- Sends updates to a Telegram chat using a bot token.
- Can be scheduled to run daily via GitHub Actions.
- Fully automated with secrets (no need to store tokens in the code).

---

## Setup

### 1. Telegram Bot

1. Create a bot using [@BotFather](https://t.me/BotFather) on Telegram.
2. Save your bot token.
3. Get your chat ID using a test message.

---

### 2. GitHub Repository

1. Push your bot code to GitHub.
2. Add **Secrets** in the repository:

   | Name                 | Value                                          |
   | -------------------- | ---------------------------------------------- |
   | `TELEGRAM_BOT_TOKEN` | Your Telegram bot token                        |
   | `TELEGRAM_CHAT_ID`   | Your Telegram chat ID (integer, no minus sign) |

---

### 3. GitHub Actions

- The workflow (`.github/workflows/daily_check.yml`) runs:
  - On schedule: `00:02 Berlin time` daily.
  - On manual trigger (`workflow_dispatch`).
  - On every push (optional).

- It installs dependencies and runs `restaurant_bot.py`.

---

### 4. Local Run (Optional)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install requests pytz
python restaurant_bot.py
```
