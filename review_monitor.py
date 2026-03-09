"""
AuraLynx MVP — Competitor Review Monitor
Uses Scrapling to monitor Trustpilot reviews for competitor pain signals.
"""

import time
import logging
import threading
from scrapling import Stealer
from config import TRUSTPILOT_URLS, REVIEW_CHECK_INTERVAL_MIN, SCORE_THRESHOLD
from database import already_seen_review, mark_seen_review, save_signal, get_connection
from scorer import score_review
from telegram_bot import send_alert

log = logging.getLogger("auralynx.reviews")

def scrape_trustpilot(url: str):
    """Scrape the latest reviews from a Trustpilot URL."""
    stealer = Stealer()
    try:
        log.info(f"Scraping reviews from: {url}")
        # Stealer fetches and parses the page
        page = stealer.get(url)
        
        # Trustpilot review card selector (might need adjustment based on live DOM)
        # Usually they are within articles or divs with specific classes
        # We'll use a likely selector based on Trustpilot's structure
        reviews = []
        
        # This is a generic approach; in a real scenario, we'd inspect the actual DOM.
        # Trustpilot often uses [data-review-content] or similar.
        review_elements = page.css('[data-service-review-card-paper="true"]')
        
        for el in review_elements:
            try:
                # Extract review ID
                review_id = el.css('a[data-review-title-link="true"]::attr(href)').first().split('/')[-1]
                
                # Extract rating
                rating_img = el.css('img[alt^="Rated"]::attr(alt)').first()
                rating = int(rating_img.split(' ')[1]) if rating_img else 0
                
                # Extract text
                title = el.css('[data-review-title-typography="true"]::text').first() or ""
                body = el.css('[data-service-review-body-typography="true"]::text').first() or ""
                author = el.css('[data-consumer-name-typography="true"]::text').first() or "Unknown"
                
                full_text = f"{title}\n{body}".strip()
                
                reviews.append({
                    "id": review_id,
                    "rating": rating,
                    "text": full_text,
                    "author": author,
                    "url": f"https://www.trustpilot.com/reviews/{review_id}"
                })
            except Exception as e:
                log.debug(f"Error parsing review element: {e}")
                continue
                
        return reviews
    except Exception as e:
        log.error(f"Failed to scrape {url}: {e}")
        return []

def monitor_reviews():
    """Main loop for monitoring competitor reviews."""
    log.info("Review monitor started — checking competitors every %d minutes", REVIEW_CHECK_INTERVAL_MIN)
    
    while True:
        conn = get_connection()
        try:
            for url in TRUSTPILOT_URLS:
                competitor = url.split('/')[-1]
                reviews = scrape_trustpilot(url)
                
                for rev in reviews:
                    if already_seen_review(conn, rev["id"]):
                        continue
                    
                    # Pre-filter: Focus on low ratings (1-3) or specific keywords
                    # If high rating, maybe skip unless keywords match (less likely for pain)
                    if rev["rating"] > 3:
                        # Skip high ratings for now as they aren't "pain" signals
                        mark_seen_review(conn, rev["id"])
                        continue
                        
                    log.info(f"New pain review from u/{rev['author']} on {competitor} ({rev['rating']} stars)")
                    
                    # Score with AI
                    result = score_review(rev["text"], rev["rating"], competitor)
                    if not result:
                        continue
                        
                    # Build signal record
                    signal_data = {
                        "post_id": rev["id"],
                        "title": f"Review for {competitor} ({rev['rating']} stars)",
                        "body": rev["text"],
                        "author": rev["author"],
                        "url": rev["url"],
                        "subreddit": competitor, # Repurpose subreddit field for competitor name
                        "score": result["score"],
                        "signal_type": result["signal_type"],
                        "summary": result["summary"],
                        "reply_draft": result["reply_draft"],
                        "source": "trustpilot",
                        "alerted": 0,
                    }
                    
                    # Score decision
                    if result["score"] >= SCORE_THRESHOLD:
                        signal_data["alerted"] = 1
                        send_alert(signal_data)
                        log.info(f"🚨 REVIEW ALERT SENT — Score {result['score']}/10 for {competitor}")
                    
                    save_signal(conn, signal_data)
                    mark_seen_review(conn, rev["id"])
                    
                time.sleep(5) # Slow down between competitor URLs
                
        except Exception as e:
            log.error(f"Error in review monitor loop: {e}")
        finally:
            conn.close()
            
        time.sleep(REVIEW_CHECK_INTERVAL_MIN * 60)

if __name__ == "__main__":
    # For testing isolation
    logging.basicConfig(level=logging.INFO)
    monitor_reviews()
