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

   Example: `https://api.telegram.org/bot7123456789:AAHxxx/getUpdates`

4. Find a block like:

   ```json
   "chat": { "id": 123456789, "first_name": "You", "type": "private" }
   ```

5. Copy **only the number** `123456789`  
   - Private chats: positive number  
   - Groups: often **negative** (e.g. `-1001234567890`)  
   - If `"result": []` is empty: you have not messaged the bot yet — go back to step 2

### Common mistakes

| Wrong | Right |
|-------|--------|
| Bot token used as chat id | Chat id is a short/long **number** only |
| Quotes: `"123456789"` | `123456789` with no quotes |
| Spaces or newlines in the secret | Trimmed number only |
| Never pressed Start on the bot | Always Start / message first |
| Group id but bot not in the group | Add bot to group, then getUpdates again |

Optional helper bot: message **@userinfobot** or **@getidsbot** — they reply with your user id (works for private chats).

## 3. Add GitHub Actions secrets

Go to: https://github.com/reonjy/onlinejobs-ph-notifier/settings/secrets/actions

| Secret | Required | Example |
|--------|----------|---------|
| `TELEGRAM_BOT_TOKEN` | Yes | `7123456789:AAH...` |
| `TELEGRAM_CHAT_ID` | Yes | `123456789` |
| `KEYWORDS` | Optional | See below |

### KEYWORDS secret

| Value | Behavior |
|-------|----------|
| **Empty / not set** | **All new jobs** (no filter) — any new post on the latest listing |
| `all` or `*` | Same as empty — all new jobs |
| `virtual assistant,VA,Data Entry` | Only jobs matching those keywords |

After changing a secret, **re-run** the workflow (secrets are only read at start of a run).

## 4. Run the workflow

1. Open: https://github.com/reonjy/onlinejobs-ph-notifier/actions
2. Select **OnlineJobs Telegram Notify**
3. **Run workflow**

- First run: seeds existing jobs (no job spam). A ✅ connection message is only sent with `python notify.py --test` or when you intentionally test Telegram.
- About every 15 minutes after: only **new** matching posts
- **If polls feel rare:** GitHub Actions free-tier cron is best-effort (can skip). Check the Actions tab for run history, use **Run workflow** manually, or run `python notify.py` on your PC (Option C in DEPLOY.md) for a true timer.

## Local use

```bash
pip install -r requirements.txt
copy config.example.json config.json
# edit config.json
python scrape.py
python notify.py --test
```
