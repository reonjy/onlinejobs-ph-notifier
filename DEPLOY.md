# Deploy the Telegram notifier (always-on)

**Never paste access tokens in chat.** Put them only in platform secret stores.

---

## Option A — GitHub Actions + external cron (recommended)

GitHub Actions runs the scrape + Telegram send.  
**Do not rely on GitHub’s built-in schedule** — free-tier cron often skips or never fires.

Use a free external timer (cron-job.org) to call the GitHub API every **15 minutes**.

**Full steps:** [EXTERNAL_CRON.md](EXTERNAL_CRON.md)

Summary:

1. Secrets on the repo: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, optional `KEYWORDS`
2. Fine-grained PAT with **Actions: write** on this repo only
3. cron-job.org POST every 15m to:

   `https://api.github.com/repos/reonjy/onlinejobs-ph-notifier/dispatches`

   Body: `{"event_type":"poll"}`

4. Confirm Actions shows event type **`repository_dispatch`**

Workflow file: `.github/workflows/onlinejobs-notify.yml`

---

## Option B — Hugging Face Spaces

### Reality check (2026)

- Free Spaces **sleep** when idle → poller stops until someone opens the Space.
- Creating **Gradio / Docker** Spaces often requires **HF PRO / paid** compute now.
- Static Spaces cannot run Python workers.

Use HF only if you have PRO (or paid hardware) **and** accept possible sleep, or you add an external keep-alive pinger.

### Deploy steps

1. Create a Space (SDK: **Gradio**) under your account.
2. Upload / push these files into the Space root (flatten `hf-space` + project):

   | Space file | From |
   |------------|------|
   | `app.py` | `hf-space/app.py` (edit path imports if needed) |
   | `scrape.py` | project root |
   | `notify.py` | project root |
   | `requirements.txt` | `hf-space/requirements.txt` |
   | `README.md` | `hf-space/README.md` (with YAML header) |

3. Space → **Settings** → **Variables and secrets** → add:
   - `TELEGRAM_BOT_TOKEN` (secret)
   - `TELEGRAM_CHAT_ID` (secret)
   - `KEYWORDS` (optional)
   - `POLL_INTERVAL_MINUTES` = `15`

4. Rebuild the Space. Open the app once so the worker starts.
5. Optional: free cron (cron-job.org) HTTP-ping your Space URL every 10 minutes so free hardware wakes more often.

---

## Option C — Your PC (simplest true always-on if PC is on)

```powershell
python notify.py
```

Or Windows **Task Scheduler** every 15 minutes:

- Program: `python`
- Arguments: `"C:\Users\Peppa\Documents\Programs\onlinejobs-ph-scraper\notify.py" --once`
- Start in: that folder

---

## Security

| Do | Don't |
|----|--------|
| Store Telegram tokens in GitHub **Secrets** | Paste tokens into chat |
| Store PAT only in cron-job.org | Commit PAT / `config.json` with real tokens |
| Scope PAT to this one repo | Put tokens in Space README |
| Revoke if ever exposed | Use bot token as chat id |
