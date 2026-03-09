# Reddit API Access Submission Details

**App Name**: AuraLynx Signal Monitor
**Developer**: Responsible-Fix6695
**Email**: enosktl1@gmail.com

## Purpose & Benefit to Redditors
Personal signal monitoring tool that tracks keyword mentions across specific subreddits to surface relevant discussions for my niche. **Read-only access** — no automated posting or commenting.

## Detailed Description of Bot Activity
1. **Real-time Streaming**: The app uses the PRAW `stream.submissions()` generator to listen for new posts across five specific subreddits (`r/coldemail`, `r/SaaS`, `r/entrepreneur`, `r/sales`, `r/GrowthHacking`).
2. **Local Deduplication**: Every incoming post ID is checked against a local SQLite database (`seen_posts` table) to ensure it hasn't been processed before, preventing duplicate alerts or redundant API calls.
3. **Keyword Pre-Filtering**: The post title and body are matched against 40+ pre-defined "pain point" keywords (e.g., "deliverability", "cold email", "instantly") locally. Only posts with at least one keyword match proceed to the next stage.
4. **LLM Analysis (External)**: Matching posts are sent to an external OpenAI-compatible API (Claude) with a specific system prompt to determine the user's "buying intent" (scored 1-10) and generate a brief summary.
5. **Inbox Monitoring**: Parallel to the post stream, the app monitors the bot's own Reddit inbox for replies and DMs to identify and alert on direct engagement from users.
6. **Result Delivery**: If a post or inbox item reaches a specific intent threshold (default 7/10), a formatted alert is sent via the Telegram Bot API to a private chat.
7. **Read-Only**: The app strictly reads public data and inbox items. It does NOT contain code to create submissions, post comments, or send automated messages. All engagement following an alert is handled manually by a human through the standard Reddit interface.

## Why not build on Devvit?
1. **External API Requirements**: This app requires calling a third-party LLM API for text analysis and sending alerts via the Telegram Bot API. These external network requests are restricted within the Devvit sandbox.
2. **Persistent Background Execution**: The app needs to run as a persistent background process on an external VPS/server to maintain a high-frequency, real-time stream across multiple subreddits simultaneously.
3. **Read-Only Nature**: The app is strictly read-only. It only reads public posts and inbox messages (to alert on direct inquiries). It does **not** create any content, post any comments, or send any automated messages on the Reddit platform.

## Source Code Link
Provide a link to your public repository here (e.g., GitHub or GitLab) for Reddit's review:
`https://github.com/abidktl/Auralynx-MVP`

## Subreddits
- r/coldemail
- r/SaaS
- r/entrepreneur
- r/sales
- r/GrowthHacking
