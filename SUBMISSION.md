# Reddit API Access Submission Details

**App Name**: AuraLynx Signal Monitor
**Developer**: Responsible-Fix6695
**Email**: enosktl1@gmail.com

## Purpose & Benefit to Redditors
Personal signal monitoring tool that tracks keyword mentions across specific subreddits to surface relevant discussions for my niche. **Read-only access** — no automated posting or commenting.

## Detailed Description
The application streams public posts from targeted subreddits (r/coldemail, r/SaaS, r/entrepreneur, r/sales, r/GrowthHacking) using a real-time PRAW connection. It filters these posts against a list of "pain point" keywords to identify relevant discussions. Matching posts are then analyzed by an external LLM to score their "buying intent" for my specific service (cold email deliverability). Scored alerts, including a summary and a manual reply draft, are sent to my phone via Telegram.

## Why not build on Devvit?
1. **External API Requirements**: This app requires calling a third-party LLM API for text analysis and sending alerts via the Telegram Bot API. These external network requests are restricted within the Devvit sandbox.
2. **Persistent Background Execution**: The app needs to run as a persistent background process on an external VPS/server to maintain a high-frequency, real-time stream across multiple subreddits simultaneously.
3. **Read-Only Nature**: The app is strictly read-only. It only reads public posts and inbox messages (to alert on direct inquiries). It does **not** create any content, post any comments, or send any automated messages on the Reddit platform.

## Subreddits
- r/coldemail
- r/SaaS
- r/entrepreneur
- r/sales
- r/GrowthHacking
