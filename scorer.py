"""
AuraLynx MVP — Intent Scorer
Uses OpenAI-compatible API endpoint to score Reddit posts for buying intent.
"""

import json
import time
import logging
from openai import OpenAI
from config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, SCORE_PROMPT

log = logging.getLogger("auralynx.scorer")

# Initialize OpenAI-compatible client pointing to custom endpoint
client = OpenAI(
    base_url=LLM_BASE_URL,
    api_key=LLM_API_KEY,
)


def score_post(title: str, body: str, max_retries: int = 3) -> dict | None:
    """
    Score a Reddit post for buying intent using the LLM.

    Returns dict: {score, signal_type, summary, reply_draft}
    Returns None if scoring fails after retries.
    """
    user_message = f"TITLE: {title}\nBODY: {body}"

    for attempt in range(1, max_retries + 1):
        try:
            log.info("Scoring post (attempt %d/%d): %s", attempt, max_retries, title[:60])

            response = client.chat.completions.create(
                model=LLM_MODEL,
                max_tokens=800,
                temperature=0.3,
                messages=[
                    {"role": "system", "content": SCORE_PROMPT},
                    {"role": "user", "content": user_message},
                ],
            )

            raw = response.choices[0].message.content.strip()

            # Clean response — strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1]  # Remove first line
                if raw.endswith("```"):
                    raw = raw[:-3]
                raw = raw.strip()

            result = json.loads(raw)

            # Validate required fields
            required = ["score", "signal_type", "summary", "reply_draft"]
            if not all(k in result for k in required):
                missing = [k for k in required if k not in result]
                log.warning("Missing fields in LLM response: %s", missing)
                continue

            # Ensure score is int 1-10
            result["score"] = max(1, min(10, int(result["score"])))

            log.info("Scored %d/10 [%s]: %s", result["score"], result["signal_type"], title[:60])
            return result

        except json.JSONDecodeError as e:
            log.warning("JSON parse error (attempt %d): %s — raw: %s", attempt, e, raw[:200])
        except Exception as e:
            log.error("Scoring error (attempt %d): %s", attempt, e)

        # Exponential backoff
        if attempt < max_retries:
            wait = 2 ** attempt
            log.info("Retrying in %ds...", wait)
            time.sleep(wait)

    log.error("Failed to score post after %d attempts: %s", max_retries, title[:60])
    return None


def score_reply_intent(reply_body: str, max_retries: int = 2) -> dict | None:
    """
    Score a reply/DM for buying intent (used by inbox monitor).
    Simpler prompt — just checks if someone is interested.

    Returns dict: {score, summary}
    """
    intent_prompt = """You are analyzing a Reddit reply or DM to determine buying intent.
Score how likely this person wants to purchase a cold email / deliverability service.

Return ONLY valid JSON:
{"score": 1-10, "summary": "one sentence description of their intent"}

1-3: Just chatting, no intent
4-6: Curious, asking questions  
7-8: Strong interest, wants help
9-10: Ready to buy, asking for pricing/call"""

    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                max_tokens=200,
                temperature=0.2,
                messages=[
                    {"role": "system", "content": intent_prompt},
                    {"role": "user", "content": reply_body},
                ],
            )

            raw = response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1]
                if raw.endswith("```"):
                    raw = raw[:-3]
                raw = raw.strip()

            result = json.loads(raw)
            result["score"] = max(1, min(10, int(result.get("score", 1))))
            return result

        except Exception as e:
            log.warning("Reply scoring error (attempt %d): %s", attempt, e)
            if attempt < max_retries:
                time.sleep(2)

    return None
