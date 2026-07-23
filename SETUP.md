# Setup Telegram notifications (required)

Repo: https://github.com/reonjy/onlinejobs-ph-notifier

## 1. Create a Telegram bot

1. Message **@BotFather** on Telegram
2. Send `/newbot` and follow prompts
3. Copy the **bot token**

## 2. Get your chat ID

1. Open your bot and press **Start**
2. Open: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
3. Copy `"chat":{"id": ...}`

## 3. Add GitHub Actions secrets

Go to: https://github.com/reonjy/onlinejobs-ph-notifier/settings/secrets/actions

| Secret | Required |
|--------|----------|
| `TELEGRAM_BOT_TOKEN` | Yes |
| `TELEGRAM_CHAT_ID` | Yes |
| `KEYWORDS` | Optional (default: virtual assistant, VA, Data Entry, Customer Service) |

## 4. Run the workflow

1. Open: https://github.com/reonjy/onlinejobs-ph-notifier/actions
2. Select **OnlineJobs Telegram Notify**
3. **Run workflow**

- First run: seeds existing jobs (no Telegram spam)
- Every 15 minutes after: new matching jobs are sent to Telegram

## Local use

```bash
pip install -r requirements.txt
copy config.example.json config.json
# edit config.json
python scrape.py
python notify.py --test
```
