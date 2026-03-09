"""
AuraLynx MVP — Reddit Stream
Real-time post monitoring with PRAW + keyword pre-filter.
"""

import logging
import praw
from config import (
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET,
    REDDIT_USERNAME, REDDIT_PASSWORD, REDDIT_USER_AGENT,
    SUBREDDITS, PAIN_KEYWORDS, MAX_BODY_LENGTH
)

log = logging.getLogger("auralynx.reddit")


def create_reddit_client() -> praw.Reddit:
    """Initialize and return a PRAW Reddit client."""
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        username=REDDIT_USERNAME,
        password=REDDIT_PASSWORD,
        user_agent=REDDIT_USER_AGENT,
    )
    log.info("Reddit client initialized as u/%s", REDDIT_USERNAME)
    return reddit


def passes_keyword_filter(title: str, body: str) -> bool:
    """
    Check if post contains any pain/intent keywords.
    Runs locally — no API call, no cost, microseconds.
    """
    text = (title + " " + body).lower()
    return any(kw in text for kw in PAIN_KEYWORDS)


def get_matching_keywords(title: str, body: str) -> list:
    """Return all matching keywords found in the post."""
    text = (title + " " + body).lower()
    return [kw for kw in PAIN_KEYWORDS if kw in text]


def stream_submissions(reddit: praw.Reddit):
    """
    Generator that yields filtered Reddit submissions.

    Uses PRAW's real-time stream — no polling.
    skip_existing=True means it only catches NEW posts.

    Yields dicts with: post_id, title, body, author, url, subreddit
    """
    subreddit = reddit.subreddit(SUBREDDITS)
    log.info("Streaming submissions from: r/%s", SUBREDDITS)

    for post in subreddit.stream.submissions(skip_existing=True):
        title = post.title or ""
        body = post.selftext or ""

        # Keyword pre-filter — skip irrelevant posts instantly
        if not passes_keyword_filter(title, body):
            log.debug("Filtered out: %s", title[:80])
            continue

        keywords = get_matching_keywords(title, body)
        log.info("Keyword match [%s]: %s", ", ".join(keywords[:3]), title[:80])

        yield {
            "post_id": post.id,
            "title": title,
            "body": body[:MAX_BODY_LENGTH],  # Truncate for Claude
            "author": str(post.author) if post.author else "[deleted]",
            "url": f"https://reddit.com{post.permalink}",
            "subreddit": str(post.subreddit),
        }
