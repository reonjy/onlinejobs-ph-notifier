"""
Hugging Face Spaces entrypoint for OnlineJobs.ph → Telegram notifier.

Runs a background poll loop and a small Gradio status panel.

Secrets (Space Settings → Variables and secrets):
  TELEGRAM_BOT_TOKEN
  TELEGRAM_CHAT_ID
  KEYWORDS (optional, comma-separated)
  POLL_INTERVAL_MINUTES (optional, default 15)
"""

from __future__ import annotations

import os
import sys
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path

import gradio as gr

# Support both monorepo layout (hf-space/app.py) and flat HF Space root.
_here = Path(__file__).resolve().parent
_candidates = [_here, _here.parent]
for _root in _candidates:
    if (_root / "notify.py").exists() and (_root / "scrape.py").exists():
        if str(_root) not in sys.path:
            sys.path.insert(0, str(_root))
        break
else:
    # Fallback: current dir
    if str(_here) not in sys.path:
        sys.path.insert(0, str(_here))

from notify import (  # noqa: E402
    DEFAULT_CONFIG,
    load_config,
    load_seen,
    run_once,
    test_telegram,
)

STATUS = {
    "running": False,
    "last_poll": "—",
    "last_error": "",
    "polls": 0,
    "started_at": "",
    "seen_count": 0,
}
_lock = threading.Lock()


def _status_text() -> str:
    with _lock:
        return (
            f"**Notifier status**\n\n"
            f"- Running: `{STATUS['running']}`\n"
            f"- Started: `{STATUS['started_at'] or '—'}`\n"
            f"- Polls completed: `{STATUS['polls']}`\n"
            f"- Last poll: `{STATUS['last_poll']}`\n"
            f"- Seen job IDs: `{STATUS['seen_count']}`\n"
            f"- Last error: `{STATUS['last_error'] or 'none'}`\n\n"
            f"Keywords: `{os.environ.get('KEYWORDS', '(from config defaults)')}`\n"
            f"Interval: `{os.environ.get('POLL_INTERVAL_MINUTES', '15')}` minutes\n"
        )


def poll_loop() -> None:
    try:
        cfg = load_config(DEFAULT_CONFIG if DEFAULT_CONFIG.exists() else Path("config.json"))
    except SystemExit:
        with _lock:
            STATUS["last_error"] = "Missing TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID secrets"
            STATUS["running"] = False
        return
    except Exception as exc:
        with _lock:
            STATUS["last_error"] = str(exc)
            STATUS["running"] = False
        return

    state_path = Path(cfg["state_file"])
    seen = load_seen(state_path)
    interval = float(cfg.get("poll_interval_minutes") or 15)

    try:
        test_telegram(cfg["telegram_bot_token"], cfg["telegram_chat_id"])
    except Exception as exc:
        with _lock:
            STATUS["last_error"] = f"Telegram test failed: {exc}"
            STATUS["running"] = False
        return

    with _lock:
        STATUS["running"] = True
        STATUS["started_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        STATUS["seen_count"] = len(seen)
        STATUS["last_error"] = ""

    while True:
        try:
            seen = run_once(cfg, seen, state_path)
            with _lock:
                STATUS["polls"] += 1
                STATUS["last_poll"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                STATUS["seen_count"] = len(seen)
                STATUS["last_error"] = ""
        except Exception as exc:
            with _lock:
                STATUS["last_error"] = f"{exc}\n{traceback.format_exc()[:500]}"
        time.sleep(max(interval, 5) * 60)


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="OnlineJobs.ph Telegram Notifier") as demo:
        gr.Markdown(
            "# OnlineJobs.ph → Telegram Notifier\n"
            "Background worker polls OnlineJobs.ph and sends **new** matching jobs to Telegram.\n\n"
            "Set secrets in **Settings → Variables and secrets**: "
            "`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, optional `KEYWORDS`."
        )
        status = gr.Markdown(_status_text())
        refresh = gr.Button("Refresh status")
        refresh.click(fn=_status_text, outputs=status)
        demo.load(fn=_status_text, outputs=status)
    return demo


# Start poller when Space boots
_thread = threading.Thread(target=poll_loop, name="oj-poller", daemon=True)
_thread.start()

demo = build_ui()

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", "7860")))
