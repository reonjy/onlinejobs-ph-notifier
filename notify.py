"""
OnlineJobs.ph → Telegram Notifier
=================================
Polls OnlineJobs.ph for keyword matches and sends NEW job posts
to a Telegram chat via a bot you create.

Setup (one-time):
  1. Message @BotFather on Telegram → /newbot → copy the bot token
  2. Start a chat with your bot (press Start)
  3. Open: https://api.telegram.org/bot<TOKEN>/getUpdates
     and copy your "chat":{"id": ...} number
  4. Copy config.example.json → config.json and fill in token + chat_id
  5. python notify.py

First run by default only seeds known job IDs (no flood).
Later runs send only jobs not seen before.

Usage:
    python notify.py
    python notify.py --once
    python notify.py --config config.json --interval 10
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

from scrape import (
    DEFAULT_DELAY,
    DEFAULT_KEYWORDS,
    dedupe_jobs,
    enrich_from_detail,
    make_session,
    scrape_keyword,
    sort_jobs_latest_first,
)

ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG = ROOT / "config.json"
STATE_FILE = ROOT / "state" / "seen_jobs.json"
TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


# ──────────────────────────────────────────────
# Config / state
# ──────────────────────────────────────────────

def _env(name: str, default: str | None = None) -> str | None:
    val = os.environ.get(name)
    if val is None or str(val).strip() == "":
        return default
    return str(val).strip()


def load_config(path: Path) -> dict:
    """
    Load settings from config.json if present, then override with env vars.

    Env (useful for Hugging Face Spaces / GitHub Actions secrets):
      TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
      KEYWORDS (comma-separated)
      POLL_INTERVAL_MINUTES, PAGES_PER_KEYWORD, REQUEST_DELAY_SECONDS
      OPEN_DETAIL_PAGES (true/false), SEND_ON_FIRST_RUN (true/false)
    """
    cfg: dict = {}
    if path.exists():
        with path.open(encoding="utf-8") as f:
            cfg = json.load(f)
    else:
        # Cloud deploys often use env only — don't hard-fail if secrets exist
        has_env = bool(_env("TELEGRAM_BOT_TOKEN") and _env("TELEGRAM_CHAT_ID"))
        if not has_env:
            example = ROOT / "config.example.json"
            print("=" * 60)
            print("Missing config file and Telegram env secrets.")
            print(f"  Local: copy {example.name} → {path.name} and fill tokens")
            print("  Cloud: set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID secrets")
            print("=" * 60)
            if example.exists() and path.name == "config.json" and sys.stdin.isatty():
                try:
                    raw = input(f"Create {path.name} from example now? [Y/n]: ").strip().lower()
                except EOFError:
                    raw = "n"
                if raw in ("", "y", "yes"):
                    path.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
                    print(f"Created {path}. Edit it with your token/chat_id, then re-run.")
            sys.exit(1)

    token = (_env("TELEGRAM_BOT_TOKEN") or cfg.get("telegram_bot_token") or "").strip()
    chat_id = str(_env("TELEGRAM_CHAT_ID") or cfg.get("telegram_chat_id") or "").strip()
    if not token or "PASTE_" in token:
        print("ERROR: Set TELEGRAM_BOT_TOKEN env or telegram_bot_token in config.json.")
        sys.exit(1)
    if not chat_id or "PASTE_" in chat_id:
        print("ERROR: Set TELEGRAM_CHAT_ID env or telegram_chat_id in config.json.")
        print("  Tip: message your bot, then open getUpdates on the Telegram API.")
        sys.exit(1)

    cfg["telegram_bot_token"] = token
    cfg["telegram_chat_id"] = chat_id

    kw_env = _env("KEYWORDS")
    if kw_env:
        cfg["keywords"] = [k.strip() for k in kw_env.split(",") if k.strip()]
    else:
        cfg.setdefault("keywords", DEFAULT_KEYWORDS)

    if _env("POLL_INTERVAL_MINUTES"):
        cfg["poll_interval_minutes"] = float(_env("POLL_INTERVAL_MINUTES"))  # type: ignore[arg-type]
    else:
        cfg.setdefault("poll_interval_minutes", 15)

    if _env("PAGES_PER_KEYWORD"):
        cfg["pages_per_keyword"] = int(_env("PAGES_PER_KEYWORD"))  # type: ignore[arg-type]
    else:
        cfg.setdefault("pages_per_keyword", 1)

    if _env("REQUEST_DELAY_SECONDS"):
        cfg["request_delay_seconds"] = float(_env("REQUEST_DELAY_SECONDS"))  # type: ignore[arg-type]
    else:
        cfg.setdefault("request_delay_seconds", DEFAULT_DELAY)

    if _env("OPEN_DETAIL_PAGES") is not None:
        cfg["open_detail_pages"] = _env("OPEN_DETAIL_PAGES", "true").lower() in (
            "1",
            "true",
            "yes",
            "y",
        )
    else:
        cfg.setdefault("open_detail_pages", True)

    if _env("SEND_ON_FIRST_RUN") is not None:
        cfg["send_on_first_run"] = _env("SEND_ON_FIRST_RUN", "false").lower() in (
            "1",
            "true",
            "yes",
            "y",
        )
    else:
        cfg.setdefault("send_on_first_run", False)

    # Persistent state path (HF Spaces: use /data if mounted, else local state/)
    state_override = _env("STATE_FILE")
    if state_override:
        cfg["state_file"] = state_override
    else:
        data_dir = Path("/data")
        if data_dir.is_dir() and os.access(data_dir, os.W_OK):
            cfg["state_file"] = str(data_dir / "seen_jobs.json")
        else:
            cfg["state_file"] = str(STATE_FILE)

    return cfg


def load_seen(path: Path) -> set[str]:
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return set(data.get("seen_ids", []))
    except (json.JSONDecodeError, OSError):
        return set()


def save_seen(path: Path, seen: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Keep list size reasonable (newest-ish order not critical)
    ids = sorted(seen)[-5000:]
    payload = {
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "count": len(ids),
        "seen_ids": ids,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


# ──────────────────────────────────────────────
# Telegram
# ──────────────────────────────────────────────

def telegram_call(token: str, method: str, payload: dict) -> dict:
    url = TELEGRAM_API.format(token=token, method=method)
    resp = requests.post(url, json=payload, timeout=30)
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API error: {data}")
    return data


def send_telegram_message(token: str, chat_id: str, text: str) -> None:
    telegram_call(
        token,
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        },
    )


def html_escape(text: str) -> str:
    return (
        (text or "")
        .replace("&", "&")
        .replace("<", "<")
        .replace(">", ">")
    )


def format_job_message(job: dict) -> str:
    title = html_escape(job.get("Job Post Title") or "Untitled job")
    salary = html_escape(job.get("Salary") or "Not stated")
    skills = html_escape(job.get("Skill Requirements") or "Not listed")
    employer = html_escape(job.get("Employer Info") or "Hidden / not public")
    updated = html_escape(job.get("Date Updated") or job.get("Posted Date") or "—")
    etype = html_escape(job.get("Employment Type") or "—")
    keyword = html_escape(job.get("Matched Keyword") or "—")
    link = job.get("Link") or ""

    return (
        f"🆕 <b>{title}</b>\n"
        f"💰 <b>Salary:</b> {salary}\n"
        f"🛠 <b>Skills:</b> {skills}\n"
        f"🏢 <b>Employer:</b> {employer}\n"
        f"📅 <b>Updated:</b> {updated}\n"
        f"⏱ <b>Type:</b> {etype}\n"
        f"🏷 <b>Keyword:</b> {keyword}\n"
        f'🔗 <a href="{html_escape(link)}">Open job post</a>'
    )


def test_telegram(token: str, chat_id: str) -> None:
    send_telegram_message(
        token,
        chat_id,
        "✅ OnlineJobs.ph notifier is connected.\n"
        "You will get messages when new matching jobs appear.",
    )


# ──────────────────────────────────────────────
# Poll cycle
# ──────────────────────────────────────────────

def collect_jobs(cfg: dict) -> list[dict]:
    session = make_session()
    keywords = cfg["keywords"]
    delay = float(cfg["request_delay_seconds"])
    pages = int(cfg["pages_per_keyword"])
    collected: list[dict] = []

    for kw in keywords:
        print(f"  Checking keyword: {kw!r}")
        try:
            collected.extend(
                scrape_keyword(
                    session,
                    kw,
                    max_pages=pages,
                    delay=delay,
                    stop_after=pages * 30,
                )
            )
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            print(f"  [warn] keyword {kw!r} failed: {exc}")

    jobs = dedupe_jobs(collected)
    jobs = sort_jobs_latest_first(jobs)

    if cfg.get("open_detail_pages"):
        # Only enrich a small newest set to limit traffic
        limit = min(len(jobs), max(10, pages * 30))
        for i, job in enumerate(jobs[:limit], start=1):
            print(f"  Detail [{i}/{limit}] {(job.get('Job Post Title') or '')[:50]}")
            try:
                enrich_from_detail(session, job, delay=delay)
            except Exception as exc:
                print(f"  [warn] detail failed: {exc}")

    return jobs


def run_once(cfg: dict, seen: set[str], state_path: Path) -> set[str]:
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Polling OnlineJobs.ph…")
    jobs = collect_jobs(cfg)
    print(f"  Found {len(jobs)} unique listings this poll")

    new_jobs = [j for j in jobs if (j.get("job_id") or j.get("Link")) not in seen]
    # Newest first for notifications
    new_jobs = sort_jobs_latest_first(new_jobs)

    first_run = len(seen) == 0
    send_on_first = bool(cfg.get("send_on_first_run"))

    if first_run and not send_on_first:
        print(
            f"  First run: seeding {len(jobs)} job IDs (no Telegram spam). "
            "New posts from the next poll will be sent."
        )
        for j in jobs:
            jid = j.get("job_id") or j.get("Link")
            if jid:
                seen.add(str(jid))
        save_seen(state_path, seen)
        return seen

    if not new_jobs:
        print("  No new jobs.")
        # still refresh seen with anything current so we don't re-notify
        for j in jobs:
            jid = j.get("job_id") or j.get("Link")
            if jid:
                seen.add(str(jid))
        save_seen(state_path, seen)
        return seen

    print(f"  New jobs: {len(new_jobs)} — sending to Telegram…")
    token = cfg["telegram_bot_token"]
    chat_id = cfg["telegram_chat_id"]

    sent = 0
    for job in new_jobs:
        jid = str(job.get("job_id") or job.get("Link"))
        try:
            send_telegram_message(token, chat_id, format_job_message(job))
            sent += 1
            seen.add(jid)
            time.sleep(0.4)  # avoid Telegram flood limits
        except Exception as exc:
            print(f"  [warn] failed to send {jid}: {exc}")
            # still mark seen? better not — retry next poll
            continue

    # Mark remaining current IDs as seen so old ones don't resurface later
    for j in jobs:
        jid = j.get("job_id") or j.get("Link")
        if jid:
            seen.add(str(jid))

    save_seen(state_path, seen)
    print(f"  Sent {sent} Telegram message(s). Seen IDs stored: {len(seen)}")
    return seen


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Notify Telegram of new OnlineJobs.ph posts.")
    p.add_argument("--config", default=str(DEFAULT_CONFIG), help="Path to config.json")
    p.add_argument(
        "--once",
        action="store_true",
        help="Run a single poll then exit (good for Task Scheduler).",
    )
    p.add_argument(
        "--interval",
        type=float,
        default=None,
        help="Minutes between polls (overrides config).",
    )
    p.add_argument(
        "--test",
        action="store_true",
        help="Only send a test Telegram message and exit.",
    )
    p.add_argument(
        "--send-existing",
        action="store_true",
        help="On first run, send current matches instead of only seeding IDs.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cfg = load_config(Path(args.config))

    if args.send_existing:
        cfg["send_on_first_run"] = True

    token = cfg["telegram_bot_token"]
    chat_id = cfg["telegram_chat_id"]

    if args.test:
        print("Sending test message…")
        test_telegram(token, chat_id)
        print("OK — check Telegram.")
        return 0

    interval = args.interval if args.interval is not None else float(cfg["poll_interval_minutes"])
    if interval < 5:
        print("WARNING: interval under 5 minutes is aggressive; consider 10–15+.")

    state_path = Path(cfg.get("state_file") or STATE_FILE)
    seen = load_seen(state_path)

    print("OnlineJobs.ph → Telegram notifier")
    print(f"  Config   : {args.config}")
    print(f"  Keywords : {cfg['keywords']}")
    print(f"  Interval : {interval} min" + (" (single run)" if args.once else ""))
    print(f"  State    : {state_path}")
    print(f"  Seen IDs : {len(seen)} already stored")
    print("  Press Ctrl+C to stop.\n")

    try:
        test_telegram(token, chat_id)
        print("Telegram connection OK.\n")
    except Exception as exc:
        print(f"ERROR: Could not message Telegram: {exc}")
        return 1

    try:
        while True:
            try:
                seen = run_once(cfg, seen, state_path)
            except KeyboardInterrupt:
                raise
            except Exception as exc:
                print(f"  [error] poll failed: {exc}")

            if args.once:
                break

            print(f"  Sleeping {interval} minute(s)…")
            time.sleep(interval * 60)
    except KeyboardInterrupt:
        print("\nStopped.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
