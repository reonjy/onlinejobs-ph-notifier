# OnlineJobs.ph Notifier

Polls [OnlineJobs.ph](https://www.onlinejobs.ph/jobseekers/jobsearch) and sends **new** jobs to your Telegram bot.

**Repo:** https://github.com/reonjy/onlinejobs-ph-notifier

## Important: use external cron for every-15-minute reliability

GitHub free-tier **scheduled Actions often skip or never run**.  
For real ~15 minute polls, set up **external cron** (cron-job.org → GitHub API):

**→ Full guide: [EXTERNAL_CRON.md](EXTERNAL_CRON.md)**

Flow:

```text
cron-job.org (every 15m)  →  GitHub Actions (scrape + Telegram)
```

---

## One-time setup

### 1. Telegram bot

1. Message **@BotFather** → `/newbot` → copy the bot token  
2. Open your bot and press **Start**  
3. Open `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`  
4. Copy `"chat":{"id": ...}` (your chat id)

### 2. GitHub Actions secrets

Open: [Settings → Secrets and variables → Actions](https://github.com/reonjy/onlinejobs-ph-notifier/settings/secrets/actions)

| Secret | Required |
|--------|----------|
| `TELEGRAM_BOT_TOKEN` | Yes |
| `TELEGRAM_CHAT_ID` | Yes |
| `KEYWORDS` | Optional — empty = **all** new jobs |

### 3. Run once manually

1. Open [Actions](https://github.com/reonjy/onlinejobs-ph-notifier/actions)  
2. **OnlineJobs Telegram Notify** → **Run workflow**

- **First run:** seeds existing job IDs (no spam)  
- **Later runs:** only **new** posts

### 4. External cron (required for reliable 15m)

Follow **[EXTERNAL_CRON.md](EXTERNAL_CRON.md)** (cron-job.org + fine-grained PAT).

After that, Actions history should show runs with event **`repository_dispatch`** about every 15 minutes.

## Local use

```bash
pip install -r requirements.txt
copy config.example.json config.json
# edit config.json with token + chat_id
python scrape.py          # Excel export
python notify.py --test   # test Telegram
python notify.py --once   # one poll
```

## Files

| File | Purpose |
|------|---------|
| `scrape.py` | Keyword scrape → Excel |
| `notify.py` | Poll + Telegram notify |
| `.github/workflows/onlinejobs-notify.yml` | Worker (manual / external / backup schedule) |
| `EXTERNAL_CRON.md` | **Reliable 15-minute timer setup** |
| `SETUP.md` | Telegram + secrets checklist |
| `DEPLOY.md` | Other deploy options |

Personal job-hunting use only. Respect OnlineJobs.ph Terms of Service.
