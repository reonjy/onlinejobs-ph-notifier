---
title: OnlineJobs PH Telegram Notifier
emoji: 🛎️
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: "4.44.0"
app_file: app.py
pinned: false
---

# OnlineJobs.ph → Telegram Notifier (HF Space)

Polls OnlineJobs.ph for keyword matches and sends **new** jobs to your Telegram bot.

## Important limits

- **Free Hugging Face Spaces sleep** when unused, so notifications can pause.
- **Gradio/Docker Spaces may require a paid/PRO plan** on Hugging Face (policy changed mid‑2026).
- For free, reliable always-on polling, prefer **GitHub Actions** (see main project README).

## Secrets (required)

Space → **Settings** → **Variables and secrets** → **New secret**:

| Name | Example |
|------|---------|
| `TELEGRAM_BOT_TOKEN` | from @BotFather |
| `TELEGRAM_CHAT_ID` | your numeric chat id |
| `KEYWORDS` | `virtual assistant,VA,Data Entry,Customer Service` |
| `POLL_INTERVAL_MINUTES` | `15` |
| `OPEN_DETAIL_PAGES` | `true` |
| `SEND_ON_FIRST_RUN` | `false` |

Do **not** put secrets in code or git.

## Files expected in the Space repo root

Upload (or push) these from the project:

- `app.py` (this folder’s app, as Space root `app.py`)
- `scrape.py`
- `notify.py`
- `requirements.txt`

Or push the whole monorepo and set `app_file` / path accordingly.
