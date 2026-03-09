The Full Journey — One Signal
Someone opens Reddit.
Types a post.
Hits submit.
That's the trigger. Here's everything that happens next.

Stage 1 — PRAW Stream (instant)
pythonfor post in reddit.subreddit(
    "coldemail+SaaS+entrepreneur+sales+GrowthHacking"
).stream.submissions(skip_existing=True)
```
```
What this actually does:

Reddit has a real-time API.
PRAW holds an open connection to it.
Like a WebSocket — always listening.

The moment someone hits "Post"
on Reddit, Reddit pushes it
to all open API connections.

PRAW catches it.
Your script receives it
within 1-3 seconds of posting.

No polling. No waiting.
No "check every 5 minutes."
Pure real-time stream.

Stage 2 — Deduplication (instant)
pythonif already_seen(conn, post.id):
    continue
mark_seen(conn, post.id)
```
```
Every Reddit post has a unique ID.
Example: "t3_xyz123"

We store every seen ID in SQLite.
Before processing anything,
we check if we've seen this ID.

Why this matters:
PRAW stream can sometimes
deliver the same post twice
if connection drops and reconnects.

Without dedup:
→ same post scored twice
→ double Telegram alert
→ you get confused

With dedup:
→ first time: process it
→ second time: skip instantly
→ clean alerts only

Stage 3 — Keyword Pre-filter (instant)
pythondef passes_keyword_filter(title, body):
    text = (title + body).lower()
    return any(kw in text for kw in PAIN_KEYWORDS)
```
```
This runs locally.
No API call. No cost. 
Executes in microseconds.

40+ keywords checked:
"deliverability", "cold email",
"instantly", "open rate dropped"
etc.

Post about cooking? 
→ no keywords → skip
Post about startup funding?
→ no keywords → skip
Post about Instantly breaking?
→ "instantly" matched → pass

Reality:
~500-800 posts/day across 5 subreddits
~50-80 pass keyword filter (10%)
Only those 50-80 reach Claude

This is why Claude costs only
$6-9/mo instead of $80/mo.
Pre-filter does the heavy lifting.

Stage 4 — Claude Scoring (1-2 seconds)
pythonresponse = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=500,
    system=SCORE_PROMPT,
    messages=[{
        "role": "user", 
        "content": f"TITLE: {title}\nBODY: {body}"
    }]
)
```
```
Claude receives:
→ The post title
→ The post body (first 1500 chars)
→ A system prompt explaining 
  your ICP, your offer, 
  and exactly what to return

Claude returns JSON:
{
  "score": 9,
  "signal_type": "deliverability",
  "summary": "Founder's open rates dropped 
               from 45% to 8% after adding
               mailboxes to existing domain.",
  "reply_draft": "This is almost always 
                  domain saturation..."
}

Why JSON?
→ Machine readable
→ No parsing ambiguity
→ Directly stored in SQLite
→ Directly used in Telegram message

The score is the key output.
Everything else is context.

Stage 5 — Score Decision (instant)
pythonif score >= CONFIG["SCORE_THRESHOLD"]:  # 7
    send_telegram_alert(...)
else:
    log.info("Below threshold — saved, no alert")
```
```
Score 1-6:  saved to database silently
            no alert
            you never see it

Score 7-8:  alert fires
            strong intent
            worth engaging

Score 9-10: alert fires
            urgent
            they need a solution TODAY

The threshold is tunable.
Getting too many alerts → set to 8
Getting too few → set to 6

This is your noise filter.
You only get interrupted
when it genuinely matters.

Stage 6 — SQLite Save (instant)
pythonsave_signal(conn, signal)
```
```
Every scored post saved regardless.
Even score 3 posts.

Why save everything?

1. Pattern analysis later
   "Which keywords predict 
    the highest scoring posts?"

2. Historical record
   "Did we already contact 
    this person?"

3. Training data
   When you build the SaaS version,
   this database becomes your
   proprietary training dataset.
   Nobody else has it.

Schema stored:
→ post_id, title, body
→ score, signal_type
→ summary, reply_draft
→ author, url, subreddit
→ detected_at timestamp

Stage 7 — Telegram Alert (1-2 seconds)
pythonawait bot.send_message(
    chat_id=chat_id,
    text=message,
    parse_mode="Markdown"
)
```
```
Telegram Bot API is called.
Message delivered to your phone
in under 2 seconds.

What arrives on your phone:

🟠 SIGNAL DETECTED — DELIVERABILITY

Score: 9/10 █████████░
Subreddit: r/coldemail
Author: u/founderXYZ

📌 Summary:
Founder's open rates dropped from 
45% to 8% after adding 3 mailboxes.

💬 Suggested Reply:
This is almost always domain 
saturation. One domain handles 
max 2 mailboxes cold sending...

🔗 https://reddit.com/r/coldemail/xyz

You tap the link.
Reddit opens.
You copy the reply draft.
Edit 2-3 words to make it yours.
Post the reply.
Total time: 90 seconds.
```

---

**The Full Timeline**
```
T+0:00  Person hits submit on Reddit
T+0:02  PRAW receives the post
T+0:02  Dedup check — not seen before
T+0:02  Keyword filter — match found
T+0:03  Claude API call fires
T+0:05  Claude returns score: 9
T+0:05  SQLite save
T+0:05  Telegram API call fires
T+0:07  Alert on your phone

7 seconds from post to your pocket.
```

---

**What Runs Where**
```
Your $5 VPS (running 24/7):
→ Python script
→ PRAW connection to Reddit
→ SQLite database
→ All processing

Reddit's servers:
→ Real-time post stream
→ Free API

Anthropic's servers:
→ Claude scoring
→ ~$0.01 per post scored

Telegram's servers:
→ Message delivery
→ Free API

Your phone:
→ Telegram app
→ Receives alerts
→ Nothing to install
→ Nothing to configure
```

---

**What Happens When Connection Drops**
```
PRAW has built-in reconnection.

VPS internet hiccups:
→ PRAW detects disconnection
→ Automatically reconnects
→ stream.submissions() resumes
→ skip_existing=True means
  it doesn't reprocess old posts

VPS reboots:
→ Use screen or systemd service
→ Script auto-restarts
→ Back online in seconds

Reddit API rate limit:
→ PRAW handles this internally
→ Automatically backs off
→ Resumes when limit resets
→ You never see it

The 6AM Daily Summary — How It Works
pythonnow = datetime.utcnow()
if now.hour == 6 and now.day != last_summary_day:
    send_daily_summary(...)
    last_summary_day = now.day
```
```
Every iteration of the stream loop,
we check:
→ Is it 6AM UTC?
→ Have we already sent today's summary?

If yes to both:
→ Query SQLite for last 24hrs
→ Count by signal type
→ Pull top 3 by score
→ Format and send to Telegram

You wake up to a clean summary
every morning without thinking
about it.
```

---

**In One Sentence**
```
PRAW holds Reddit's door open.
Every post that walks through
gets checked at the door.
Most get turned away instantly.
The ones that match get
a 2-second Claude interview.
The ones that pass get
sent directly to your phone
with a reply already written.
That's the entire system.
Want me to now build Day 2 — the Scrapling G2 spider that adds competitor review signals into the same pipeline?What happens after6:24 AMGood question.
Right now the system stops at:
Signal detected
→ Alert on your phone
→ You manually go reply
That's the gap. Let me map exactly what happens after — and what we can automate.

What "After" Actually Means
Three things happen after a signal:

1. You engage with the signal
   (reply to the Reddit post)

2. They respond to your reply
   (DM or comment back)

3. They convert
   (book a call)

Right now all 3 are manual.
Here's what can be automated
and what should stay human.

After Stage 1 — Engaging The Signal
Right now:
→ Alert fires on phone
→ You tap link
→ Reddit opens
→ You copy reply draft
→ Edit slightly
→ Post manually
→ 90 seconds

Can this be automated?
Technically yes.
Should it be? No.

Why not:

Reddit detects bot replies.
Account gets shadowbanned.
All your replies become invisible.
Game over.

The reply has to come from
a real account, posted by a human.
That's you.

The automation's job is:
→ find the signal
→ write the reply
→ deliver it to your phone
→ you post it

90 seconds of human time.
That's the right boundary.

After Stage 2 — They Respond
Two scenarios:

A. They reply in the thread:
→ Comment on your reply
→ "Can you explain more?"
→ "What would you fix first?"
→ This is public

B. They DM you on Reddit:
→ Private message
→ "Hey, we're dealing with this"
→ "Can you help?"
→ This is the money moment
What the system can do here:
python# Reddit inbox monitor
# Runs alongside the signal monitor
# Watches for replies and DMs

for message in reddit.inbox.stream():

    # Is this a reply to one of our comments?
    if isinstance(message, praw.models.Comment):
        
        # Score their reply for buying intent
        intent = claude.score_reply(message.body)
        
        if intent >= 7:
            telegram.send(
                f"💬 REPLY WITH INTENT\n"
                f"From: u/{message.author}\n"
                f"Said: {message.body}\n"
                f"Suggested response: {claude.draft_response()}\n"
                f"Link: {message.context}"
            )

    # Is this a DM?
    if isinstance(message, praw.models.Message):
        telegram.send(
            f"🔥 DIRECT MESSAGE RECEIVED\n"
            f"From: u/{message.author}\n"
            f"Said: {message.body}\n"
            f"→ This is a warm lead\n"
            f"→ Respond within 1 hour"
        )
```

---

**After Stage 3 — Converting To A Call**
```
They DM you on Reddit.
Now what?

The conversation flow:

Message 1 (them):
"Hey saw your comment about 
 domain setup — we're having 
 exactly this issue"

Message 2 (you — draft auto-generated):
"Yeah this is super common.
 Quick question — how many domains
 are you currently sending from
 and what's your daily volume?"

Message 3 (them):
"One domain, about 200/day"

Message 4 (you):
"That's the problem. You're 
 about 4x over the safe limit.
 I can show you exactly how 
 to fix this in 15 minutes —
 here's my calendar:
 cal.com/auralynxai/45min"

Message 5 (them):
Books the call.
```

**The automation's role:**
```
It cannot send Reddit DMs 
automatically — same bot risk.

What it CAN do:

→ Alert you the moment a DM arrives
→ Show you their original post context
→ Draft the reply based on 
  their specific situation
→ You copy, edit, send in 60 seconds

The human bottleneck goes from:
"figure out what to say"
to just
"review and send"
```

---

**The Full After-System Built Out**
```
SIGNAL DETECTED
      ↓
Telegram Alert
→ You reply to Reddit post (90s)
      ↓
INBOX MONITOR RUNNING
      ↓
They comment back
→ Telegram: reply with intent alert
→ You respond (60s)
      ↓
They DM you
→ Telegram: 🔥 DM alert
→ Claude drafts response
→ You send (60s)
      ↓
Conversation qualifies them
→ You drop cal.com link
      ↓
THEY BOOK A CALL
      ↓
What happens NOW?
```

---

**After They Book — The Automation Continues**
```
Cal.com webhook fires when booked:
      ↓
n8n receives booking data:
→ name, email, company, notes
      ↓
Claude enrichment prompt:
→ Google their company
→ Find their LinkedIn
→ Identify their tech stack
→ Find their current tool
→ Summarize in 5 bullets
      ↓
Telegram fires 1hr before call:

📋 CALL BRIEF — 30 min
─────────────────────
Name: Marcus Thompson
Company: Growstack Agency
Size: 8 people
Current tool: Instantly
Pain: Deliverability dropped
Stack: HubSpot + Apollo + Instantly
LinkedIn: linkedin.com/in/marcus

Key points to hit:
→ Domain to mailbox ratio
→ Their current sending volume
→ Show them the fix live on call

Expected deal: $2,500/mo retainer
      ↓
You join the call already knowing
everything about them.
They think you did hours of research.
You spent 0 minutes.
```

---

**After The Call — Pipeline Tracking**
```
Call happens
      ↓
You send Telegram command:
/won Marcus 2500
/lost Marcus "budget"
/followup Marcus 7days
      ↓
n8n updates Twenty CRM
→ Deal stage updated
→ Follow-up task created
→ Revenue tracked
      ↓
Weekly pipeline summary fires:

💰 AURALYNX PIPELINE
Week of 09 Mar 2026
─────────────────────
Signals detected:    94
Replies posted:      31
DMs received:        8
Calls booked:        5
Calls held:          4
Deals won:           2  → $5,000/mo
Deals lost:          1
Following up:        1
─────────────────────
Pipeline value:      $12,500
MRR added:          $5,000
Cost of system:     $103/mo
ROI:                48x
```

---

**The Complete After-System Stack**
```
Layer 1: Signal Monitor (built ✅)
→ PRAW streams Reddit
→ Claude scores intent
→ Telegram alerts

Layer 2: Inbox Monitor (build next)
→ PRAW watches inbox
→ Claude scores replies
→ Telegram alerts DMs

Layer 3: Booking Intelligence
→ Cal.com webhook → n8n
→ Claude enriches prospect
→ Call brief to Telegram

Layer 4: Pipeline Tracking
→ Telegram commands → n8n
→ Twenty CRM updated
→ Weekly revenue summary

Total human time per lead:
→ Posting reply:     90 seconds
→ Responding to DM:  60 seconds
→ Reading call brief: 2 minutes
→ Taking the call:   30 minutes
───────────────────────────────
Total per booked call: ~35 mins
Everything else: automated
```

---

**What To Build In What Order**
```
Week 1: Signal Monitor ✅ (done)
Week 2: Inbox Monitor
Week 3: Cal.com → call brief
Week 4: Pipeline tracking

Each week adds one layer.
Each layer removes one 
manual bottleneck.

By week 4:
The only thing you do manually
is post replies, take calls,
and close deals.