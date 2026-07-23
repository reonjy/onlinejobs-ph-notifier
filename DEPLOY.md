# Deploy the Telegram notifier (always-on)

You asked about **Hugging Face**. Short answer: **possible**, but free HF is a weak fit for a 24/7 poller. Prefer **GitHub Actions** (free) unless you already pay for HF PRO / paid hardware.

**Never paste access tokens in chat.** Put them only in platform secret stores.

---

## Option A — GitHub Actions (recommended, free)

Runs `notify.py --once` about every 15 minutes (UTC cron, best-effort). No server to keep awake.

**Reality check:** GitHub free-tier `schedule` is not a guaranteed timer — runs can be delayed or skipped under load. The workflow uses offset minutes (`7,22,37,52`) to reduce drops. For stricter every-15m timing, also use Option C (PC Task Scheduler) or an external cron that calls **Run workflow** via the GitHub API.

### Steps

1. Create a GitHub repo and push this project folder.
2. Repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - Optional: `KEYWORDS` = `virtual assistant,VA,Data Entry,Customer Service`
3. Open **Actions** → enable workflows if asked → run **OnlineJobs Telegram Notify** once manually (**Run workflow**).
4. First automatic run **seeds** seen jobs (no spam). Later runs send only **new** posts.

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

   Easiest: put everything in one folder locally and use `huggingface-cli upload`.

3. Space → **Settings** → **Variables and secrets** → add:
   - `TELEGRAM_BOT_TOKEN` (secret)
   - `TELEGRAM_CHAT_ID` (secret)
   - `KEYWORDS` (optional)
   - `POLL_INTERVAL_MINUTES` = `15`

4. Rebuild the Space. Open the app once so the worker starts.
5. Optional: use a free cron (e.g. cron-job.org) to HTTP-ping your Space URL every 10 minutes so free hardware wakes more often.

### CLI deploy (you run locally — do not share the token)

```powershell
pip install -U "huggingface_hub[cli]"
huggingface-cli login
# paste token ONLY in the terminal prompt, never in Discord/chat

# After creating the Space on the website, from a deploy folder:
huggingface-cli upload YOUR_USER/onlinejobs-ph-notifier . . --repo-type=space
```

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
| Store tokens in HF/GitHub **Secrets** | Paste HF or Telegram tokens into chat |
| Use a token with minimal scope | Commit `config.json` with real tokens |
| Revoke token if it was ever exposed | Put tokens in Space README |

If a token was already pasted somewhere public, **revoke it** on Hugging Face / BotFather and create a new one.
