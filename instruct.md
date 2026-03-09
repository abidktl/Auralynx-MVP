Stage 1 — MVP (Month 1-2)
Just AuraLynx. Prove it works.
Signal Detection:
→ PRAW (Reddit)          Python
→ Scrapling (G2/web)     Python

Intent Scoring:
→ Claude API             Anthropic

Storage:
→ SQLite                 Zero config
                         Zero cost
                         Single file
                         Perfect for MVP

Alerts:
→ Telegram Bot API       Free
                         Already on phone
                         No app to build

Orchestration:
→ Single Python script   Cron on VPS
→ Screen/tmux            Stays running

Hosting:
→ Hetzner CX11           $5/mo
                         Ubuntu 24.04
                         Enough for 3-5 clients

Cost: $13/mo total
Build time: 3 days

Stage 2 — Agency Tool (Month 2-4)
3-10 paying clients. Still fast.
Signal Detection:
→ PRAW                   Python (same)
→ Scrapling              Python (same)
→ Reddit RSS             feedparser
                         backup stream

Intent Scoring:
→ Claude API             same
→ Add prompt versioning  simple dict
                         per client

Storage:
→ PostgreSQL             upgrade from SQLite
→ Supabase               $25/mo
                         managed postgres
                         built-in REST API
                         auth included
                         realtime built in

Why Supabase over raw Postgres:
→ dashboard out of box
→ row-level security per client
→ REST API auto-generated
→ saves 2 weeks of backend work

Orchestration:
→ n8n (self-hosted)      $0
                         visual workflows
                         webhook handling
                         Cal.com integration
                         Slack integration

Queue:
→ Redis + RQ             simple job queue
                         async Claude calls
                         retry on failure
                         $0 (self-hosted)

Hosting:
→ Hetzner CX21           $10/mo
                         2 cores, 4GB RAM
                         handles 10 clients

Cost: $35-50/mo
Build time: 3-4 weeks

Stage 3 — SaaS Product (Month 4-6)
Self-serve. 10-100 clients.
Backend:
Language:
→ Python (FastAPI)

Why FastAPI not Node:
→ You're already in Python
→ PRAW is Python
→ Scrapling is Python
→ No context switching
→ Async native
→ Fast enough for this scale

API Framework:
→ FastAPI                async
                         auto docs
                         type hints
                         pydantic validation

Auth:
→ Supabase Auth          already in stack
                         JWT built in
                         social login free
                         row level security

Background Jobs:
→ Celery + Redis         production grade
                         per-client workers
                         scheduled tasks
                         retry logic

Database:
→ Supabase (Postgres)    same as Stage 2
                         just bigger plan

File Storage:
→ Supabase Storage       signal exports
                         client configs
                         audit logs

Frontend:
Framework:
→ Next.js 14             React based
                         server components
                         fast by default
                         Vercel deploy

Why Next.js not pure React:
→ SEO for marketing site
→ Server components = faster
→ API routes built in
→ One framework for all

Styling:
→ Tailwind CSS           utility first
                         fast to build
                         no CSS files

Components:
→ shadcn/ui              copy-paste components
                         built on Radix
                         accessible
                         Tailwind compatible
                         free forever

Charts/Analytics:
→ Recharts               signal volume graphs
                         score distributions
                         lead pipeline

State:
→ Zustand                simpler than Redux
                         tiny bundle
                         perfect for this

Forms:
→ React Hook Form        validation
→ Zod                    schema validation

Infrastructure:
Hosting (backend):
→ Railway.app            $5-20/mo
                         Git deploy
                         auto scaling
                         managed Redis
                         managed Postgres
                         zero DevOps

Why Railway not AWS:
→ AWS = 40hrs of config
→ Railway = 20 minutes
→ Same reliability at this scale
→ Switch to AWS at 500+ clients

Hosting (frontend):
→ Vercel                 free tier works
                         Git deploy
                         edge network
                         preview deploys

Redis:
→ Railway managed        $5/mo
                         or Upstash free tier
                         serverless Redis

Email (transactional):
→ Resend                 $0-20/mo
                         developer first
                         React email templates
                         reliable delivery

Payments:
→ Stripe                 industry standard
                         subscription billing
                         usage-based billing
                         metered API calls

Domain + DNS:
→ Cloudflare             free DNS
                         DDoS protection
                         proxy + SSL free

Monitoring:
→ Sentry                 error tracking
                         free tier enough
→ PostHog                product analytics
                         self-hostable
                         free tier good

Cost: $50-100/mo for infrastructure
      scales with revenue

The Signal Processing Architecture
CLIENT ONBOARDS
      ↓
Config stored in Postgres:
{
  client_id: "abc123"
  subreddits: ["coldemail", "SaaS"]
  keywords: ["deliverability", ...]
  icp_description: "..."
  offer_description: "..."
  score_threshold: 7
  telegram_chat_id: "..."
}
      ↓
Celery worker spawned per client
      ↓
PRAW stream opened per client
      ↓
Post detected
      ↓
Keyword filter (local)
      ↓
Claude scoring job queued in Redis
      ↓
Claude returns score
      ↓
Postgres save
      ↓
Score >= threshold?
      ↓
Telegram alert fires
      ↓
Dashboard updates realtime
(Supabase realtime websocket)

Database Schema
sql-- Clients
CREATE TABLE clients (
  id            UUID PRIMARY KEY,
  name          TEXT,
  email         TEXT,
  plan          TEXT,        -- starter/growth/scale
  created_at    TIMESTAMP,
  stripe_id     TEXT
);

-- Client configs (one per niche)
CREATE TABLE configs (
  id              UUID PRIMARY KEY,
  client_id       UUID REFERENCES clients,
  name            TEXT,      -- "Cold Email ICP"
  subreddits      TEXT[],
  keywords        TEXT[],
  icp_description TEXT,
  offer           TEXT,
  threshold       INT DEFAULT 7,
  telegram_id     TEXT,
  active          BOOLEAN DEFAULT true
);

-- Signals
CREATE TABLE signals (
  id           UUID PRIMARY KEY,
  client_id    UUID REFERENCES clients,
  config_id    UUID REFERENCES configs,
  source       TEXT,         -- reddit/g2/linkedin
  post_id      TEXT,
  title        TEXT,
  body         TEXT,
  author       TEXT,
  url          TEXT,
  score        INT,
  signal_type  TEXT,
  summary      TEXT,
  reply_draft  TEXT,
  alerted      BOOLEAN,
  replied      BOOLEAN,
  converted    BOOLEAN,      -- became a lead?
  detected_at  TIMESTAMP
);

-- Leads (converted signals)
CREATE TABLE leads (
  id           UUID PRIMARY KEY,
  client_id    UUID REFERENCES clients,
  signal_id    UUID REFERENCES signals,
  name         TEXT,
  company      TEXT,
  reddit_user  TEXT,
  email        TEXT,
  status       TEXT,         -- new/contacted/called/won/lost
  deal_value   NUMERIC,
  notes        TEXT,
  created_at   TIMESTAMP
);
```

---

**The Dashboard — What Clients See**
```
┌─────────────────────────────────────┐
│  SIGNAL FEED          LIVE    ●     │
├─────────────────────────────────────┤
│  🔴 9/10  r/coldemail  2min ago     │
│  Deliverability crisis — Instantly  │
│  [View] [Reply Draft] [Mark Lead]   │
├─────────────────────────────────────┤
│  🟠 8/10  r/SaaS  14min ago         │
│  Just hired first SDR, need setup   │
│  [View] [Reply Draft] [Mark Lead]   │
├─────────────────────────────────────┤
│  🟡 7/10  r/entrepreneur  1hr ago   │
│  Switching from Lemlist, advice?    │
│  [View] [Reply Draft] [Mark Lead]   │
└─────────────────────────────────────┘

┌──────────────┬──────────────────────┐
│  This Week   │  Pipeline            │
│              │                      │
│  Signals: 94 │  New leads:    8     │
│  High:    23 │  Contacted:    5     │
│  Replied: 12 │  Calls booked: 3     │
│  Leads:    8 │  Won:          1     │
│              │  Value: $2,500/mo    │
└──────────────┴──────────────────────┘
```

---

**Pricing Tiers That Match The Stack**
```
STARTER — $299/mo
→ 1 niche config
→ 5 subreddits
→ Telegram alerts only
→ 500 signals/mo
→ No dashboard

GROWTH — $499/mo
→ 3 niche configs
→ Unlimited subreddits
→ Dashboard included
→ 2,000 signals/mo
→ Inbox monitor
→ Call brief generation

SCALE — $999/mo
→ Unlimited configs
→ White label
→ API access
→ Unlimited signals
→ Priority support
→ Custom integrations
```

---

**Build Order — Exact Sequence**
```
Week 1: MVP Python script (done ✅)
Week 2: Add inbox monitor
Week 3: Add Scrapling (G2 + Crunchbase)
Week 4: First 2 paying clients
         manual config per client
         charge $300/mo each

Month 2: 
→ Supabase setup
→ Multi-client Python backend
→ Celery workers per client
→ 5 clients

Month 3:
→ Next.js dashboard
→ Signal feed realtime
→ Basic pipeline tracking
→ Stripe subscriptions
→ Self-serve onboarding
→ 10 clients

Month 4:
→ Inbox monitor in dashboard
→ Call brief automation
→ Analytics
→ 20+ clients

Month 5-6:
→ G2 + Crunchbase signals
→ LinkedIn signals
→ API for agencies
→ White label
→ 50+ clients
```

---

**The Full Stack Summary**
```
LAYER          TOOL              COST
──────────────────────────────────────
Signal detect  PRAW + Scrapling  $0
Intent score   Claude API        $10/client/mo
Database       Supabase          $25/mo flat
Queue          Redis (Railway)   $5/mo
Backend        FastAPI/Railway   $20/mo
Frontend       Next.js/Vercel    $0-20/mo
Auth           Supabase Auth     included
Payments       Stripe            2.9% + $0.30
Email          Resend            $0-20/mo
Monitoring     Sentry + PostHog  $0
──────────────────────────────────────
TOTAL INFRA:   ~$80-100/mo

BREAKEVEN:     1 client at $299/mo
PROFIT at 10:  $2,900 - $100 = $2,800/mo
PROFIT at 50:  $14,500 - $300 = $14,200/mo
```

---

**The One Decision That Matters Most**
```
Don't build the SaaS first.

Build the script.
Get 3 paying clients.
Run it manually.
Prove the outcome.

Then build the SaaS
around what actually works.

The tech stack above is correct
for where this is going.

But the next thing to build
is still just:
→ the inbox monitor
→ one more paying client

Everything else comes after
the outcome is proven.