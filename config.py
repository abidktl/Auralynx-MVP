"""
AuraLynx MVP — Configuration
All settings, credentials, keywords, and prompts.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── Reddit API ───────────────────────────────────────────────
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME", "")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD", "")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "AuraLynx Signal Monitor v1.0")

# ─── LLM API (OpenAI-compatible endpoint) ────────────────────
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "ag/Claude Opus 4.6 Thinking")

# ─── Telegram ─────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# ─── Monitoring Config ────────────────────────────────────────
SUBREDDITS = os.getenv(
    "SUBREDDITS",
    "coldemail+SaaS+entrepreneur+sales+GrowthHacking"
)
SCORE_THRESHOLD = int(os.getenv("SCORE_THRESHOLD", "7"))
SUMMARY_HOUR_UTC = int(os.getenv("SUMMARY_HOUR_UTC", "6"))
MAX_BODY_LENGTH = 1500  # Truncate post body for scoring

# Competitor Review Monitoring
TRUSTPILOT_URLS = [
    "https://www.trustpilot.com/review/instantly.ai",
    "https://www.trustpilot.com/review/smartlead.ai"
]
REVIEW_CHECK_INTERVAL_MIN = int(os.getenv("REVIEW_CHECK_INTERVAL_MIN", "60"))

# ─── Database ─────────────────────────────────────────────────
DB_PATH = os.getenv("DB_PATH", "auralynx.db")

# ─── Pain / Intent Keywords (40+) ────────────────────────────
PAIN_KEYWORDS = [
    # Deliverability
    "deliverability", "open rate", "open rates", "bounce rate",
    "spam folder", "landing in spam", "going to spam", "spam filter",
    "email warmup", "warm up", "warm-up", "warmed up",
    "blacklisted", "blacklist", "blocklist",
    "domain reputation", "sender reputation",
    "dkim", "dmarc", "spf",
    # Cold email tools
    "cold email", "cold outreach", "cold emailing",
    "instantly", "smartlead", "lemlist", "woodpecker",
    "mailshake", "reply.io", "apollo",
    "salesloft", "outreach.io",
    # Pain signals
    "open rate dropped", "rates dropped", "not getting replies",
    "low response", "low reply rate", "no responses",
    "emails not landing", "not reaching inbox",
    "domain setup", "dns setup", "mailbox setup",
    "new domain", "secondary domain",
    # Buying intent
    "which tool", "best tool", "recommend a tool",
    "alternative to", "switching from", "moved from",
    "looking for", "need help with", "struggling with",
    "anyone using", "has anyone tried",
    # Scale / growth
    "scale outreach", "scaling cold email", "sending volume",
    "how many mailboxes", "mailbox limit", "daily limit",
    "sending limit",
]

# ─── Claude Scoring Prompt ────────────────────────────────────
SCORE_PROMPT = """You are an intent-scoring AI for AuraLynx, a cold email deliverability and outreach agency.

YOUR ICP (Ideal Customer Profile):
- Founders, agency owners, and sales leaders
- Running cold email campaigns
- Experiencing deliverability problems OR scaling outreach
- Using tools like Instantly, Smartlead, Lemlist, Apollo
- Revenue: $10K-$500K/month
- Pain: emails landing in spam, low open rates, domain issues, need expert setup

YOUR OFFER:
- Cold email infrastructure setup and management
- Domain & mailbox architecture
- Deliverability optimization
- Done-for-you outreach systems

TASK:
Analyze the Reddit post below and return a JSON object with:
1. "score" (1-10): How likely this person is a qualified lead
   - 1-3: Not relevant, just discussion
   - 4-6: Somewhat relevant, general question
   - 7-8: Strong intent, actively needs solution
   - 9-10: Urgent need, ready to buy TODAY
2. "signal_type": One of ["deliverability", "tool_selection", "scaling", "setup", "general"]
3. "summary": 1-2 sentence summary of their specific situation
4. "reply_draft": A helpful, non-salesy Reddit reply (2-3 paragraphs) that:
   - Addresses their specific problem
   - Provides genuine value/advice
   - Subtly positions expertise
   - Does NOT pitch or link anything
   - Sounds human, not corporate

RETURN ONLY VALID JSON. No markdown, no code fences, no extra text.

Example output:
{"score": 8, "signal_type": "deliverability", "summary": "Founder's open rates dropped from 45% to 8% after adding mailboxes.", "reply_draft": "This is almost always domain saturation..."}"""

