# AuraLynx — Signal Detection MVP

Real-time Reddit monitoring → AI intent scoring → Telegram alerts.

Detects buying-intent signals in cold email / SaaS subreddits and delivers scored alerts with pre-written reply drafts to your phone in under 10 seconds.

## Architecture

```
Reddit (PRAW stream)
    → Keyword pre-filter (40+ pain keywords)
    → LLM scoring (OpenAI-compatible API)
    → SQLite (all signals saved)
    → Telegram alert (score ≥ 7)
```

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure credentials

```bash
cp .env.example .env
# Edit .env with your API keys
```

You need:
- **Reddit**: Create an app at [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps/) (script type)
- **Telegram**: Create a bot via [@BotFather](https://t.me/BotFather), get your chat ID via [@userinfobot](https://t.me/userinfobot)
- **LLM**: Already pre-configured with the custom endpoint

### 3. Run

```bash
python main.py
```

The system will:
- Stream Reddit posts in real-time from 5 subreddits
- Filter through 40+ pain/intent keywords (free, instant)
- Score matching posts with AI (1-10 buying intent)
- Send Telegram alerts for scores ≥ 7
- Monitor your Reddit inbox for replies and DMs
- Send a daily summary at 6AM UTC

## Modules

| File | Purpose |
|------|---------|
| `config.py` | Settings, credentials, keywords, scoring prompt |
| `database.py` | SQLite schema, dedup, signal CRUD |
| `reddit_stream.py` | PRAW real-time stream + keyword filter |
| `scorer.py` | LLM intent scoring (OpenAI-compatible) |
| `telegram_bot.py` | Alert formatting + delivery |
| `inbox_monitor.py` | Reddit reply/DM tracking |
| `main.py` | Orchestrator — runs everything |

## Tuning

- **Too many alerts?** → Set `SCORE_THRESHOLD=8` in `.env`
- **Too few alerts?** → Set `SCORE_THRESHOLD=6`
- **Add subreddits** → Edit `SUBREDDITS` (plus-separated)
- **Add keywords** → Edit `PAIN_KEYWORDS` in `config.py`

## Cost

- Reddit API: **Free**
- Telegram API: **Free**
- LLM: **~$0.01/post** (~$6-9/mo for 50-80 posts/day)
- VPS: **$5/mo** (Hetzner CX11)
- **Total: ~$13/mo**
