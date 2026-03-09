"""
AuraLynx MVP — Main Orchestrator
Ties all modules together: Reddit stream → Claude scoring → Telegram alerts.
Runs signal monitor and inbox monitor concurrently.
"""

import sys
import time
import signal
import logging
import threading
from datetime import datetime, timezone

from config import SCORE_THRESHOLD, SUMMARY_HOUR_UTC
from database import (
    get_connection, init_db,
    already_seen, mark_seen, save_signal,
    get_signals_since, get_top_signals, get_signal_counts,
)
from reddit_stream import create_reddit_client, stream_submissions
from scorer import score_post
from telegram_bot import send_alert, send_daily_summary
from inbox_monitor import monitor_inbox

# ─── Logging Setup ────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-20s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("auralynx.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("auralynx")

# ─── Globals ──────────────────────────────────────────────────
shutdown_event = threading.Event()
last_summary_day = -1


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    log.info("Shutdown signal received — stopping...")
    shutdown_event.set()


def check_daily_summary(conn):
    """Send 6AM daily summary if it hasn't been sent today."""
    global last_summary_day
    now = datetime.now(timezone.utc)

    if now.hour == SUMMARY_HOUR_UTC and now.day != last_summary_day:
        log.info("Sending daily summary...")
        signals = get_signals_since(conn, hours=24)
        counts = get_signal_counts(conn, hours=24)
        top = get_top_signals(conn, n=3, hours=24)

        send_daily_summary(signals, counts, top)
        last_summary_day = now.day
        log.info("Daily summary sent — %d signals in last 24h", len(signals))


def run_signal_monitor(reddit, conn):
    """
    Main signal monitoring loop.
    
    PRAW stream → dedup → keyword filter → Claude score → save → alert
    """
    log.info("=" * 60)
    log.info("  AURALYNX SIGNAL MONITOR — STARTING")
    log.info("=" * 60)

    processed = 0
    alerted = 0

    try:
        for post in stream_submissions(reddit):
            if shutdown_event.is_set():
                break

            # Dedup check
            if already_seen(conn, post["post_id"]):
                log.debug("Already seen: %s", post["post_id"])
                continue
            mark_seen(conn, post["post_id"])

            # Score with Claude
            result = score_post(post["title"], post["body"])
            if not result:
                log.warning("Scoring failed for: %s", post["title"][:60])
                continue

            # Build signal record
            signal_data = {
                "post_id": post["post_id"],
                "title": post["title"],
                "body": post["body"],
                "author": post["author"],
                "url": post["url"],
                "subreddit": post["subreddit"],
                "score": result["score"],
                "signal_type": result["signal_type"],
                "summary": result["summary"],
                "reply_draft": result["reply_draft"],
                "source": "reddit",
                "alerted": 0,
            }

            # Score decision
            if result["score"] >= SCORE_THRESHOLD:
                signal_data["alerted"] = 1
                send_alert(signal_data)
                alerted += 1
                log.info(
                    "🚨 ALERT SENT — Score %d/10 [%s] by u/%s",
                    result["score"], result["signal_type"], post["author"]
                )
            else:
                log.info(
                    "   Saved (no alert) — Score %d/10 [%s]",
                    result["score"], result["signal_type"]
                )

            # Save to database (every signal, regardless of score)
            save_signal(conn, signal_data)
            processed += 1

            # Check for daily summary
            check_daily_summary(conn)

            log.info("Stats: %d processed, %d alerted", processed, alerted)

    except Exception as e:
        log.error("Signal monitor error: %s", e)
        raise


def run_inbox_monitor(reddit, conn):
    """Run inbox monitor in a separate thread."""
    try:
        monitor_inbox(reddit, conn)
    except Exception as e:
        log.error("Inbox monitor thread error: %s", e)


def main():
    """Main entry point — start both monitors."""
    # Register shutdown handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Initialize database
    conn = get_connection()
    init_db(conn)

    # Initialize Reddit client
    reddit = create_reddit_client()

    # Start inbox monitor in background thread
    inbox_conn = get_connection()  # Separate connection for thread safety
    inbox_thread = threading.Thread(
        target=run_inbox_monitor,
        args=(reddit, inbox_conn),
        daemon=True,
        name="inbox-monitor",
    )
    inbox_thread.start()
    log.info("Inbox monitor thread started")

    # Run signal monitor in main thread (blocking)
    try:
        while not shutdown_event.is_set():
            try:
                run_signal_monitor(reddit, conn)
            except Exception as e:
                log.error("Signal monitor crashed: %s — restarting in 10s...", e)
                time.sleep(10)
    finally:
        log.info("Shutting down...")
        conn.close()
        inbox_conn.close()
        log.info("AuraLynx stopped. Goodbye.")


if __name__ == "__main__":
    main()
