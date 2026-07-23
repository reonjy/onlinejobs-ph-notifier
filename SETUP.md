# Setup Telegram notifications (required)

Repo: https://github.com/reonjy/onlinejobs-ph-notifier

## 1. Create a Telegram bot

1. Message **@BotFather** on Telegram
2. Send `/newbot` and follow prompts
3. Copy the **bot token** (looks like `7123456789:AAH...`)

## 2. Get your chat ID (this is what failed if you see "chat not found")

1. Search for **your bot** in Telegram (the one you just created)
2. Press **Start** or send any message (e.g. `hi`) — **required**
3. In a browser open:

   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`

4. Find `"chat": { "id": 123456789, ... }` and copy **only the number**

### Common mistakes

| Wrong | Right |
|-------|--------|
| Bot token used as chat id | Chat id is a **number** only |
| Quotes: `"123456789"` | `123456789` with no quotes |
| Never pressed Start on the bot | Always Start / message first |

## 3. Add GitHub Actions secrets

Go to: https://github.com/reonjy/onlinejobs-ph-notifier/settings/secrets/actions

| Secret | Required | Example |
|--------|----------|---------|
| `TELEGRAM_BOT_TOKEN` | Yes | `7123456789:AAH...` |
| `TELEGRAM_CHAT_ID` | Yes | `123456789` |
| `KEYWORDS` | Optional | empty = all jobs |

### KEYWORDS secret

| Value | Behavior |
|-------|----------|
| **Empty / not set** | **All new jobs** |
| `all` or `*` | Same as empty |
| `virtual assistant,VA,Data Entry` | Only matching keywords |

## 4. Run the workflow once

1. Open: https://github.com/reonjy/onlinejobs-ph-notifier/actions
2. Select **OnlineJobs Telegram Notify**
3. **Run workflow**

- First run: seeds existing jobs (no job spam)
- Later runs: only **new** posts

## 5. External cron every 15 minutes (required for reliability)

**GitHub’s built-in schedule is unreliable** (often never fires).

Follow: **[EXTERNAL_CRON.md](EXTERNAL_CRON.md)**

Quick outline:

1. Create a fine-grained GitHub PAT (Actions write on this repo only)
2. cron-job.org → POST every 15 minutes to  
   `https://api.github.com/repos/reonjy/onlinejobs-ph-notifier/dispatches`  
   Body: `{"event_type":"poll"}`  
   Header: `Authorization: Bearer <PAT>`
3. Confirm Actions shows event **`repository_dispatch`**

## Local use

```bash
pip install -r requirements.txt
copy config.example.json config.json
# edit config.json
python scrape.py
python notify.py --test
```
