# OnlineJobs.ph Notifier

Polls [OnlineJobs.ph](https://www.onlinejobs.ph/jobseekers/jobsearch) for keyword matches and sends **new** jobs to your Telegram bot via GitHub Actions (every 15 minutes).

**Repo:** https://github.com/reonjy/onlinejobs-ph-notifier

## One-time setup (required)

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
| `KEYWORDS` | Optional (default: virtual assistant, VA, Data Entry, Customer Service) |

### 3. Run the workflow

1. Open [Actions](https://github.com/reonjy/onlinejobs-ph-notifier/actions)  
2. Select **OnlineJobs Telegram Notify**  
3. **Run workflow**

- **First run:** seeds existing job IDs (no Telegram spam)  
- **Every 15 minutes after:** only **new** matching posts are sent

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
| `.github/workflows/onlinejobs-notify.yml` | Cron every 15 min |
| `SETUP.md` | Short setup checklist |
| `DEPLOY.md` | Deploy options |

Personal job-hunting use only. Respect OnlineJobs.ph Terms of Service.
