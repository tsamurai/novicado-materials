#!/usr/bin/env python3
"""
Novicado Marketing — single entrypoint for the fly.io worker.
Runs the scheduler (background thread) and the Telegram control bot (main thread).

Usage:
    python marketing/run_all.py
"""

import signal
import sys
import threading
import time
from pathlib import Path

from dotenv import load_dotenv

# ── Load .env from project root ───────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent  # project root
load_dotenv(ROOT / ".env")

# Add agents dir to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent / "agents"))

# ── Imports after path setup ──────────────────────────────────────────
import schedule  # noqa: E402
from orchestrator import (  # noqa: E402
    scheduled_evening_post,
    scheduled_morning_post,
    scheduled_weekly_article,
)

# ── Scheduler thread ──────────────────────────────────────────────────

_scheduler_stop = threading.Event()


def _run_scheduler_loop():
    """Background thread: run the schedule loop until stopped."""
    schedule.every().day.at("09:00").do(scheduled_morning_post)
    schedule.every().day.at("19:00").do(scheduled_evening_post)
    schedule.every().monday.at("09:00").do(scheduled_weekly_article)

    print("[Scheduler] Started — 09:00 daily, 19:00 daily, Mon 09:00 article")

    while not _scheduler_stop.is_set():
        schedule.run_pending()
        time.sleep(30)

    print("[Scheduler] Stopped")


def start_scheduler_thread():
    """Launch the scheduler in a daemon background thread."""
    thread = threading.Thread(target=_run_scheduler_loop, daemon=True, name="scheduler")
    thread.start()
    return thread


# ── Main ──────────────────────────────────────────────────────────────


def main():
    print("══════════════════════════════════════════════")
    print("  🚀  Novicado Marketing Worker")
    print("══════════════════════════════════════════════\n")

    # Start scheduler in background
    start_scheduler_thread()

    # Handle clean shutdown
    def _shutdown(signum, frame):
        print(f"\n[Worker] Received signal {signum}, shutting down...")
        _scheduler_stop.set()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    # Run Telegram bot in the main thread (blocking)
    print("[Worker] Starting Telegram bot...")
    # Create explicit event loop for Python 3.14 compatibility
    import asyncio  # noqa: E402

    from telegram_bot import main as bot_main  # noqa: E402

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        bot_main()
    except KeyboardInterrupt:
        pass
    finally:
        _scheduler_stop.set()
        print("[Worker] Shutdown complete")


if __name__ == "__main__":
    main()
