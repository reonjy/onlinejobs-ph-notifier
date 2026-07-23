# Reliable every-15-minute polls (external cron)

## Why this is needed

GitHub Actions **free-tier `schedule` is best-effort**. It often:

- delays runs by many minutes
- skips slots under load
- or **never fires** on quiet public repos

On this repo, history showed only **manual** (`workflow_dispatch`) runs — **zero** scheduled runs. That matches “I’m not getting Telegram updates every 15 minutes.”

**Fix:** keep using GitHub Actions as the *worker* (scrape + Telegram), but drive the timer with an **external cron** that is actually reliable (cron-job.org, EasyCron, etc.).

---

## Recommended: cron-job.org → GitHub API (free)

### 1. Create a fine-grained GitHub Personal Access Token

1. Open: https://github.com/settings/personal-access-tokens/new  
   (or classic: https://github.com/settings/tokens/new )
2. **Fine-grained** (preferred):
   - **Resource owner:** `reonjy`
   - **Repository access:** Only select **`onlinejobs-ph-notifier`**
   - **Permissions → Repository:**
     - **Actions:** Read and write
     - **Contents:** Read-only is enough for dispatch (or Read and write if you prefer)
   - **Expiration:** 90 days or custom (set a calendar reminder to rotate)
3. Generate and **copy the token once** (`github_pat_...` or `ghp_...`).  
   **Never commit it. Never paste it in chat.**

Classic token alternative: enable scope **`repo`** (private) or **`public_repo`** + **`workflow`** for public repos.

### 2. Create the cron job

1. Sign up at https://cron-job.org (free)
2. **Create cronjob**
3. Settings:

| Field | Value |
|-------|--------|
| **Title** | `OnlineJobs poll every 15m` |
| **URL** | `https://api.github.com/repos/reonjy/onlinejobs-ph-notifier/dispatches` |
| **Schedule** | Every **15 minutes** (or cron expression `*/15 * * * *`) |
| **Request method** | **POST** |
| **Enable** | Yes |

4. **Request headers** (add all three):

| Header | Value |
|--------|--------|
| `Accept` | `application/vnd.github+json` |
| `Authorization` | `Bearer YOUR_GITHUB_PAT_HERE` |
| `X-GitHub-Api-Version` | `2022-11-28` |
| `Content-Type` | `application/json` |

5. **Request body** (raw JSON):

```json
{"event_type": "poll"}
```

6. Save. Use **“Run now”** / test execution once.

### 3. Confirm it works

1. Open: https://github.com/reonjy/onlinejobs-ph-notifier/actions  
2. Within ~30 seconds you should see a new run of **OnlineJobs Telegram Notify**  
3. Click it → event should be **`repository_dispatch`** (not `schedule`)  
4. After the first seed run, **new** OnlineJobs posts appear in Telegram on later polls only

If the Actions tab shows nothing:

- PAT missing Actions write on this repo
- Wrong URL / JSON body
- `Authorization` missing `Bearer ` prefix
- Cron job disabled or failed (check cron-job.org execution history)

### 4. Optional: workflow_dispatch URL instead

Same headers; different URL + body:

**URL:**

```text
https://api.github.com/repos/reonjy/onlinejobs-ph-notifier/actions/workflows/onlinejobs-notify.yml/dispatches
```

**Body:**

```json
{"ref": "main"}
```

Either method is fine. `repository_dispatch` with `{"event_type":"poll"}` is what this workflow listens for via `types: [poll]`.

---

## Alternatives

### A. EasyCron / UptimeRobot / cron-job similar

Any service that can **POST JSON + custom headers** every 15 minutes works the same way.

### B. Your PC (true local timer)

```powershell
cd C:\Users\Peppa\Documents\Programs\onlinejobs-ph-scraper
$env:TELEGRAM_BOT_TOKEN = "..."
$env:TELEGRAM_CHAT_ID = "..."
python notify.py --once
```

Windows **Task Scheduler** every 15 minutes → only works while the PC is on.

### C. Phone / Termux (if always online)

```bash
# every 15 minutes while Termux is running
while true; do
  curl -sS -X POST \
    -H "Accept: application/vnd.github+json" \
    -H "Authorization: Bearer $GITHUB_PAT" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    -H "Content-Type: application/json" \
    https://api.github.com/repos/reonjy/onlinejobs-ph-notifier/dispatches \
    -d '{"event_type":"poll"}'
  sleep 900
done
```

Prefer cron-job.org so it keeps running when your devices sleep.

---

## What still lives on GitHub

| Piece | Role |
|-------|------|
| External cron | **Timer** (every 15m, reliable) |
| GitHub Actions | **Worker** (scrape OnlineJobs + Telegram) |
| Secrets `TELEGRAM_*` | Bot credentials |
| Branch `state` | Seen job IDs (no duplicate spam) |

Built-in GitHub `schedule` remains as a weak backup only. After external cron works, you can ignore it.

---

## Security checklist

- [ ] PAT limited to **this one repo**
- [ ] PAT stored only in cron-job.org (HTTPS)
- [ ] Do not put PAT in the public repo or chat
- [ ] Rotate PAT when it expires or if leaked
- [ ] Telegram tokens stay in **GitHub Actions secrets**, not in cron-job.org
