"""
AuraLynx MVP — Inbox Monitor
Watches Reddit inbox for replies and DMs on monitored threads.
"""

import logging
import praw
from database import already_seen_inbox, mark_seen_inbox
from scorer import score_reply_intent
from telegram_bot import send_reply_alert, send_dm_alert
from config import SCORE_THRESHOLD

log = logging.getLogger("auralynx.inbox")


def monitor_inbox(reddit: praw.Reddit, conn):
    """
    Stream the Reddit inbox for replies and DMs.
    
    - Comment replies: score for buying intent, alert if >= threshold
    - DMs: immediately alert as warm lead
    
    This runs as a blocking loop — intended to run in a separate thread.
    """
    log.info("Inbox monitor started — watching for replies and DMs")

    try:
        for item in reddit.inbox.stream(skip_existing=True):
            try:
                item_id = item.id if hasattr(item, "id") else str(item)

                # Dedup
                if already_seen_inbox(conn, item_id):
                    continue
                mark_seen_inbox(conn, item_id)

                author = str(item.author) if item.author else "[deleted]"
                body = item.body if hasattr(item, "body") else ""

                # ─── Comment Reply ────────────────────────
                if isinstance(item, praw.models.Comment):
                    log.info("Reply from u/%s: %s", author, body[:80])

                    # Score reply for buying intent
                    result = score_reply_intent(body)
                    if result and result.get("score", 0) >= SCORE_THRESHOLD:
                        context_url = f"https://reddit.com{item.context}" if hasattr(item, "context") else ""
                        send_reply_alert(
                            author=author,
                            body=body,
                            intent_score=result["score"],
                            context_url=context_url,
                            summary=result.get("summary", ""),
                        )
                        log.info("Reply alert sent — u/%s scored %d", author, result["score"])
                    else:
                        score = result["score"] if result else 0
                        log.debug("Reply below threshold — u/%s scored %d", author, score)

                # ─── Direct Message ───────────────────────
                elif isinstance(item, praw.models.Message):
                    log.info("🔥 DM from u/%s: %s", author, body[:80])
                    send_dm_alert(author=author, body=body)
                    log.info("DM alert sent for u/%s", author)

            except Exception as e:
                log.error("Error processing inbox item: %s", e)
                continue

    except Exception as e:
        log.error("Inbox monitor stream error: %s", e)
        raise
