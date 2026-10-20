# The Conductor Brief: Madison Automation Agent
Mayank Bhadrasen · INFO7375 Branding & AI · Assignment 5 · October 2026

## Part 1: The tool in one sentence
> Madison Automation Agent helps agency marketing-ops leads check every new ad against its platform's rules and hand it to the right teammate with a ready-to-use fix, so they can ship good ads the same day.

## Part 2A: The user and their situation
**Primary user:** Marketing operations lead (campaign-ops manager) at a 20–80 person digital agency that runs paid social, search and email for 10–30 client brands.

**Their situation:** Every morning a fresh batch of ad variants arrives, written by AI content tools (such as Madison, an open-source marketing framework whose Content Agent drafts ad variants, or Jasper and ChatGPT) or by copywriters. Before each client's launch window they must check every variant against the platform it will run on, decide what ships and what needs fixing, give it to the right channel team, and make sure nobody forgets it.

**What they do right now instead:** Read each variant in a spreadsheet or doc, count characters by hand for Google Ads and email subject lines, paste approved copy into HubSpot or Asana tasks, then ping each channel owner on Slack and chase replies by email. Teams with an approval tool (e.g. Planable) get one place for comments, but a person still has to judge every single ad.

**Why that is not good enough:** Marketers spend about 10 hours a week (26% of their time) on routine manual work like this, roughly $17,000 per employee per year at agency rates (DoubleVerify 2025, 1,970 marketers). And the copy that arrives is not clean: in our own 50-ad test batch, 16 ads broke a channel rule (e.g. a 53-character headline where Google allows 30) and 2 still contained placeholder text such as “[website link]”. Every one of those has to be caught by a tired person reading fast. If it is missed, it gets rejected by the platform, embarrasses the agency in front of the client, or waits a day in someone's inbox.

## Part 2B: Three user stories
**Story 1: the core job:** As an **agency marketing-ops lead**, I want **every new ad variant checked against its channel's rules and turned into a task for the right team, with an alert in our team chat**, so that **good ads go live the same day and I stop copying campaigns between tools.**

**Story 2: a secondary use case:** As a **paid-media specialist at the agency**, I want **the review alert to tell me exactly what is wrong (“headline 53/30 characters”, “‘unbeatable’ is an unproven claim”) and give me a rewrite that already fits**, so that **I can fix and publish a flagged ad in minutes instead of rewriting it from scratch.**

**Story 3: the edge case or power user:** As an **agency head of operations**, I want **a daily digest showing which mistakes keep recurring across all clients, what each team handled, what it cost, and what to change in the content writer's instructions**, so that **I can fix problems at the source and show clients the hours we saved.**

## Part 3: The data contract
### Data Source 1
- **Name:** Ad copy library (A3 Source 1: HuggingFace “advertisement-copy”)
- **What it is:** CSV · 90 records (100 collected, 10 shuffled duplicates removed) · one-time snapshot of a public dataset released 2023-09-25; refreshed only when we choose new sample ads.
- **What it represents:** The creative itself: the headline, body and call-to-action a content writer hands over. This is exactly what the marketing-ops lead has to read and judge; it stands in for the ads Madison's Content Agent produces every day.
- **How we know it is good:** Every record has a headline of 3+ words, a product name and a body of 8+ words; at least 80% have a call-to-action. Records without a CTA, or with placeholder text (“[website]”, “bit.ly/…”), are kept but tagged, because they are the realistic failures the tool must catch. _Measured: headline 90/90 · product 90/90 · body 86/90 · CTA 74/90 (82%) · placeholders 3 tagged._
- **Local path:** `data/verified/ad_copy`

### Data Source 2
- **Name:** Campaign context (A3 Source 2: HuggingFace “marketing-campaign-performance-200k”)
- **What it is:** CSV · 100 records · one-time snapshot (campaigns dated 2021-01-01 to 2021-04-10) of a public practice dataset (Kaggle mirror).
- **What it represents:** Which client the ad is for and how that account is doing: company, channel (Google Ads, YouTube, Facebook, Instagram, Email, Website), audience, conversion rate and ROI. It answers “who owns this?” and “how urgent is it?”: a strong campaign ships today, a weak one waits.
- **How we know it is good:** Every record has a company, a channel from the six known channels, an audience, a numeric conversion rate and ROI, and a valid YYYY-MM-DD date. The data is synthetic and assigns campaign types at random, so the campaign type is always derived from the channel before use. _Measured: 100/100 on every field._
- **Local path:** `data/verified/campaign_metadata`

### Data Source 3
- **Name:** Market context (A3 Source 3: 4 marketing news feeds: HubSpot Marketing Blog 50, Social Media Examiner 25, Marketing Dive 10, MarTech 10)
- **What it is:** RSS → CSV · 95 articles · refreshed on every collection run (the feeds publish daily); current snapshot 2026-07-22 to 2026-10-02.
- **What it represents:** What is happening in marketing this week: platform changes, holiday-shopping trends, new ad features. Background only: it can raise an ad's priority when it is timely, but an ad is never penalised for not matching the news.
- **How we know it is good:** Every article has a title, a working source URL, a publication date within the last 90 days and a plain-text summary of 20+ words (no HTML, no “The post … appeared first on” footer); no URL appears twice. If a feed is down, the run says so by name and continues. _Measured: URL 95/95 · summary 91/95 · 0 duplicate URLs._
- **Local path:** `data/verified/industry_briefs`

### Data Source 4
- **Name:** New ad variants (the live input, built in A4)
- **What it is:** JSON · one event per new variant, sent by the content agent to the tool's inbox; 834 test events processed so far.
- **What it represents:** “Here is a new ad, ready for handoff”: the creative + its client campaign + optional market context + the content writer's own pass/fail quality check. One event = one decision the marketing-ops lead no longer has to make by hand.
- **How we know it is good:** Every event has its own ID, the campaign brief it belongs to, a variant ID, a headline, body, CTA and a valid creation date; it passed the content writer's own quality check; and that brief + variant pair has never been processed before. Anything else is turned away before any AI runs. _Measured in A4: 100% of invalid test events rejected (140 of 400 in the largest run)._
- **Local path:** `data/verified/variant_events`

### Data Source 5
- **Name:** Action log (the tool's memory, built in A4)
- **What it is:** Table (stored inside the automation tool, mirrored to a shared Google Sheet) · one row per decision · 800+ rows · grows with every event.
- **What it represents:** What has already been handled, by whom, and why: decision, priority, owning team, reason, task ID, cost. It stops the same ad being assigned twice and feeds the daily report the head of operations reads.
- **How we know it is good:** Every row has a unique key (campaign brief + variant), a status, a decision, an owning team and a timestamp; every completed live row has a CRM task ID. _Measured: all completed live rows have a task ID; known gap: two identical ads arriving in the same second can both be logged (fix planned)._
- **Local path:** `data/verified/action_log`

## Part 4: What good looks like
**G1 · Step 1: Data ingestion** (✓ in pipeline (A3))  
Good looks like: All three sources answered, or the report names the one that did not. Record counts are in the expected range (ads 80–100, campaigns 100, articles 50+). Every raw record already has a title or headline, a date and a source name, and text arrives as words, not HTML error pages.

**G2 · Step 2: Data validation (GIGO gate)** (✓ in workflow (A4))  
Good looks like: At least 80% of records are complete; 0 duplicates; 100% of dates are real YYYY-MM-DD dates in the past; every live event has all required fields, passed the content writer's quality check, and has not been seen before. Only then may the AI read it.

**G3 · Step 3: AI processing / intelligence layer** (✓ schema + validator · evidence/count re-check planned (5B))  
Good looks like: Every ad gets exactly one decision (approve / review / block), one owning team that matches its channel, and a reason in plain English. Every risk quotes words that really appear in the ad; every character count matches the real count; the suggested rewrite itself fits the channel's limit. A healthy batch auto-approves roughly a third of all ads (about half of the valid ones) and sends most of the rest to review with evidence and never “everything blocked” or “everything approved”.

**G4 · Step 4: Final report or output** (✓ live (Slack, HubSpot, Gmail, Sheets))  
Good looks like: A busy marketer understands each chat alert in five seconds: what the ad is, the decision, who owns it, why, and the fix, with a link to the task. Each CRM task has an action-first title, a due date set by urgency and the fix inside. The daily report opens with one sentence on what the batch means, then three findings backed by numbers and three concrete changes, and every number matches the action log.

## Part 5: What bad looks like
**X1 · Step 1: Data ingestion**  
Bad looks like: A source returns an error page, 0 records or a sudden drop of more than half its usual count; columns are missing or renamed; text arrives as raw HTML.  
Response: **Log and continue** if the ad copy is still available: the run names the missing source and the remaining data is valid. **Hard stop** if the ad copy itself is missing: with no creative there is nothing to judge, and a report built on two sources would mislead.

**X2 · Step 2: Data validation (GIGO gate)**  
Bad looks like: An ad with no headline or CTA, a creation date that is unreadable or in the future, the content writer's quality check failed, the same ad sent twice, or placeholder text like “[website link]”. Batch-level warning sign: more than 20% of a batch fails the gate.  
Response: **Hard stop for that ad**: rejected before any AI runs, logged with the reason, the sender is told. <i>(Today the gate rejects missing fields, bad dates, failed quality checks and repeats; placeholder text is still caught one step later by the AI and blocked. Moving it into the gate is a 5B task.)</i> If more than 20% of a batch fails, **flag for review**: the content writer upstream is probably broken and the team should hear about it before tasks pile up.

**X3 · Step 3: AI processing**  
Bad looks like: The AI quotes words that are not in the ad, gets a character count wrong, approves an ad that still contains placeholder text, assigns it to the wrong team, returns broken or refused output, or blocks most of a batch (our first instructions blocked 71–84% of valid ads in test batches because the AI treated unrelated news as a mismatch).  
Response: Broken or refused output: **log and continue**: rule-based routing sends the ad to human review with a “AI unavailable” label (proven live in A4). Invented evidence or wrong counts: **flag for review**, never auto-approve. Placeholder text approved: **hard stop** on that ad. Batch block rate above 50%: **flag for review** and pause auto-approval until the instructions are checked.

**X4 · Step 4: Final report or output**  
Bad looks like: The CRM or chat tool rejects the task or alert; the same ad gets two tasks; the daily report's numbers do not match the action log.  
Response: Tool failure: **log and continue**: retried 3×, then logged as a partial failure so nothing silently disappears. Duplicate task: **flag for review**. Report mismatch: **hard stop**, so a report that would mislead a manager is never sent.

## Part 6A: Competitive evidence
**Competitor 1: Jasper** (AI marketing writer)
- What they do well: Excellent at producing on-brand copy at volume. Its Brand Voice feature is the reason many G2 reviewers stay, and even the Pro plan ($59–69/seat/month) now includes “Agents for core marketing workflows”.
- Where they fall short for our user: It stops at writing. It does not check a finished ad against the platform it will run on, decide who on the agency team handles it, or put it into the agency's CRM and chat. Reviewers say output still needs human fact-checking and can feel generic; custom agents need the contact-sales Business plan.
- Source: [Jasper: official pricing & plan features](https://www.jasper.ai/pricing); [Nicheaitool: Jasper review (1,270+ G2 reviews)](https://nicheaitool.com/jasper-review); [EyeSift: Jasper G2 pros & complaints](https://www.eyesift.com/blog/jasper-ai-review/); [Getaitopia: Jasper 2026 review](https://getaitopia.io/blog/jasper-ai-review-2026)

**Competitor 2: Planable** (Content approval & collaboration)
- What they do well: Agencies love its approval workflow (from optional approval to stacked multi-level chains), with all client feedback in one place instead of email or WhatsApp. It covers social posts plus newsletters, blogs and ads, connects to Slack, and scores around 4.6/5 on G2.
- Where they fall short for our user: A person still judges every ad: it organises the review, it does not do it. Its AI can rewrite a post, but it does not tell the reviewer what breaks the channel's rules or why a claim is risky, and nothing lands as a task in the agency's CRM (its pricing page lists no HubSpot or CRM integration).
- Source: [Planable: official pricing & features](https://planable.io/pricing/); [PostPlanify: Planable reviews (G2 4.6)](https://postplanify.com/planable-reviews); [SocialRails: Planable review 2026](https://socialrails.com/blog/planable-review); [Capterra: Planable](https://capterra.com/p/171744/Planable/)

**Competitor 3: Zapier Agents** (General automation)
- What they do well: Connects 9,000+ apps, so it can move copy into HubSpot, Asana or Slack, and its new agents can be given company knowledge and instructions in plain language.
- Where they fall short for our user: It moves data without understanding it. One reviewer: it “knows how to call thousands of APIs and nothing about what your data means”. The agency would have to write and maintain every channel rule itself; reviewers recommend a human approval step before an agent writes to a system of record because its output is not predictable, and multi-step runs burn through task limits quickly.
- Source: [Zapier: official Agents page](https://zapier.com/agents); [The Startup Flow: Zapier AI Agents review for marketing teams](https://www.thestartupflow.com/2026/09/zapier-ai-agents-review.html); [iMark Infotech: Zapier Agents in 2026](https://www.imarkinfotech.com/zapier-agents-in-2026-when-ai-agents-inside-your-automation-stack-beat-deterministic-zaps/); [Willo: Zapier review 2026](https://www.willo.ai/blog/zapier-review)

Also considered: HubSpot Breeze (Content Agent / Agent Hub): strong inside HubSpot, but it only reasons over HubSpot data, its content agent still needs substantial editing for brand voice, and agents are gated to Professional/Enterprise tiers. Sources: [Default: HubSpot Breeze review](https://www.default.com/post/hubspot-breeze-ai-review-and-pricing); [Resolve247: HubSpot Breeze honest review](https://resolve247.ai/blog/hubspot-breeze/)

**The gap all three share:** Writers write, approval tools wait for a person, and automation tools move data without judging it. None of them takes a finished ad, judges it against the real rules of the channel it will run on, and delivers the verdict (with the exact evidence, a fix that fits, and an owner) into the CRM and chat the agency already uses. That last mile between “an ad exists” and “the right person is doing the right thing with it” is still manual.

## Part 6B: The one thing
> Our tool is the only **ad-handoff assistant** that **delivers an explained verdict on every finished ad, checked against its channel's real rules, straight to the teammate who owns it, inside the agency's own CRM and chat,** for **agency marketing-ops leads** without **making them switch content platforms or read every ad themselves**.

**Why this matters to our user:** This removes exactly the work described in Part 2. In our live 50-ad test, 15 broken ads were stopped before anyone saw them, 16 good ads were approved and assigned automatically, and 18 reached a person already carrying the quoted problem and a rewrite: 35 tasks and 35 alerts in 28 seconds, for about half a cent per ad, replacing roughly 3.5 hours of handoff. The marketing-ops lead only spends attention where judgment is actually needed.

**Why this is defensible:**
- **It is a loop, not a feature.** A quality gate that refuses bad input before any AI runs, channel-rule judgment, delivery into the agency's own tools, and an action log that remembers every decision and feeds a daily report back to the content writer. Copying one piece does not reproduce the result.
- **The judgment is calibrated, and the calibration compounds.** Our first version blocked 71–84% of valid ads; the severity rules were rebuilt from what went wrong (placeholders and false claims are serious, ordinary marketing adjectives are not). The instructions could be copied in a week; the channel rulebook and the growing log of explained decisions, which becomes the test set for every future change, cannot.
- **It is designed to fail safely.** When the AI is unavailable the ad is still routed to a person with a clear label (proven live), duplicates are refused, and every outcome is logged. Trust is what lets an agency let it run unattended, and trust takes evidence to earn, not a week of coding.
- **It sits between tools rather than inside one.** Jasper, Planable and HubSpot are each built around their own platform; judging and routing work across a client's mixed stack runs against their business model.
