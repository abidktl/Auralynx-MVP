"""
AuraLynx MVP — Telegram Bot
Alert delivery and daily summaries via Telegram.
"""

import logging
import asyncio
from telegram import Bot
from telegram.constants import ParseMode
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

log = logging.getLogger("auralynx.telegram")

# Initialize bot
bot = Bot(token=TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else None


def _score_bar(score: int) -> str:
    """Generate a visual score bar: █████░░░░░"""
    filled = "█" * score
    empty = "░" * (10 - score)
    return f"{filled}{empty}"


def _score_emoji(score: int) -> str:
    """Get emoji based on score level."""
    if score >= 9:
        return "🔴"
    elif score >= 7:
        return "🟠"
    elif score >= 5:
        return "🟡"
    else:
        return "⚪"


def _format_alert_message(signal: dict) -> str:
    """Format a signal into a Telegram alert message."""
    score = signal.get("score", 0)
    emoji = _score_emoji(score)
    bar = _score_bar(score)
    signal_type = signal.get("signal_type", "general").upper()
    subreddit = signal.get("subreddit", "unknown")
    author = signal.get("author", "unknown")
    summary = signal.get("summary", "No summary")
    reply_draft = signal.get("reply_draft", "No draft available")
    url = signal.get("url", "")

    # Escape markdown special chars in user content
    summary = summary.replace("_", "\\_").replace("*", "\\*").replace("`", "\\`")
    reply_draft = reply_draft.replace("_", "\\_").replace("*", "\\*").replace("`", "\\`")

    message = (
        f"{emoji} *SIGNAL DETECTED — {signal_type}*\n"
        f"\n"
        f"Score: {score}/10 {bar}\n"
        f"Subreddit: r/{subreddit}\n"
        f"Author: u/{author}\n"
        f"\n"
        f"📌 *Summary:*\n"
        f"{summary}\n"
        f"\n"
        f"💬 *Suggested Reply:*\n"
        f"{reply_draft}\n"
        f"\n"
        f"🔗 {url}"
    )
    return message


async def _send_message_async(text: str, chat_id: str = None):
    """Send a message via Telegram Bot API."""
    if not bot:
        log.warning("Telegram bot not configured — skipping alert")
        return

    target = chat_id or TELEGRAM_CHAT_ID
    if not target:
        log.warning("No Telegram chat ID configured — skipping alert")
        return

    try:
        await bot.send_message(
            chat_id=target,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
        )
        log.info("Telegram alert sent to %s", target)
    except Exception as e:
        log.error("Failed to send Telegram message: %s", e)
        # Try without markdown if parsing fails
        try:
            await bot.send_message(
                chat_id=target,
                text=text,
            )
            log.info("Telegram alert sent (plain text fallback) to %s", target)
        except Exception as e2:
            log.error("Telegram plain text fallback also failed: %s", e2)


def send_alert(signal: dict):
    """Send a signal alert to Telegram (sync wrapper)."""
    message = _format_alert_message(signal)
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_send_message_async(message))
    except RuntimeError:
        asyncio.run(_send_message_async(message))


def send_dm_alert(author: str, body: str):
    """Send a DM received alert to Telegram."""
    body_escaped = body.replace("_", "\\_").replace("*", "\\*").replace("`", "\\`")
    message = (
        f"🔥 *DIRECT MESSAGE RECEIVED*\n"
        f"\n"
        f"From: u/{author}\n"
        f"Said: {body_escaped[:500]}\n"
        f"\n"
        f"→ This is a warm lead\n"
        f"→ Respond within 1 hour"
    )
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_send_message_async(message))
    except RuntimeError:
        asyncio.run(_send_message_async(message))


def send_reply_alert(author: str, body: str, intent_score: int, context_url: str, summary: str = ""):
    """Send a reply-with-intent alert to Telegram."""
    body_escaped = body.replace("_", "\\_").replace("*", "\\*").replace("`", "\\`")[:400]
    bar = _score_bar(intent_score)
    message = (
        f"💬 *REPLY WITH INTENT*\n"
        f"\n"
        f"Intent Score: {intent_score}/10 {bar}\n"
        f"From: u/{author}\n"
        f"Said: {body_escaped}\n"
    )
    if summary:
        message += f"\n📌 {summary}\n"
    message += f"\n🔗 {context_url}"

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_send_message_async(message))
    except RuntimeError:
        asyncio.run(_send_message_async(message))


def send_daily_summary(signals: list, counts: dict, top_signals: list):
    """Send the 6AM daily summary to Telegram."""
    total = len(signals)
    high = sum(1 for s in signals if s.get("score", 0) >= 7)
    alerted = sum(1 for s in signals if s.get("alerted"))

    message = (
        f"📊 *AURALYNX DAILY SUMMARY*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"\n"
        f"*Last 24 Hours:*\n"
        f"  Signals detected: {total}\n"
        f"  High intent (7+): {high}\n"
        f"  Alerts sent: {alerted}\n"
        f"\n"
    )

    if counts:
        message += "*By Type:*\n"
        for sig_type, data in counts.items():
            message += f"  {sig_type}: {data['count']} (avg {data['avg_score']})\n"
        message += "\n"

    if top_signals:
        message += "*Top Signals:*\n"
        for i, sig in enumerate(top_signals, 1):
            score = sig.get('score', 0)
            emoji = _score_emoji(score)
            title = sig.get('title', 'No title')[:60]
            title = title.replace("_", "\\_").replace("*", "\\*")
            message += f"  {i}. {emoji} {score}/10 — {title}\n"

    message += f"\n━━━━━━━━━━━━━━━━━━━━━━"

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_send_message_async(message))
    except RuntimeError:
        asyncio.run(_send_message_async(message))
