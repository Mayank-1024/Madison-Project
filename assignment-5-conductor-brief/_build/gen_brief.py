"""Builds the Conductor Brief: brief.md (plain review copy) + Bhadrasen_Mayank_A5_ConductorBrief.pdf.
All content lives in this file; numbers come from A3/A4 result files (see EVIDENCE notes)."""
import html, pathlib, subprocess
ROOT = pathlib.Path(__file__).resolve().parent.parent
e = html.escape

NAME = "Madison Automation Agent"
SENTENCE = (f"{NAME} helps agency marketing-ops leads check every new ad against its platform's rules and hand it to the right "
            "teammate with a ready-to-use fix, so they can ship good ads the same day.")

USER = [
    ("Primary user", "Marketing operations lead (campaign-ops manager) at a 20–80 person digital agency that runs paid social, search and email for 10–30 client brands."),
    ("Their situation", "Every morning a fresh batch of ad variants arrives, written by AI content tools (such as Madison, an open-source marketing framework whose Content Agent drafts ad variants, or Jasper and ChatGPT) or by copywriters. Before each client's launch window they must check every variant against the platform it will run on, decide what ships and what needs fixing, give it to the right channel team, and make sure nobody forgets it."),
    ("What they do right now instead", "Read each variant in a spreadsheet or doc, count characters by hand for Google Ads and email subject lines, paste approved copy into HubSpot or Asana tasks, then ping each channel owner on Slack and chase replies by email. Teams with an approval tool (e.g. Planable) get one place for comments, but a person still has to judge every single ad."),
    ("Why that is not good enough", "Marketers spend about 10 hours a week (26% of their time) on routine manual work like this, roughly $17,000 per employee per year at agency rates (DoubleVerify 2025, 1,970 marketers). And the copy that arrives is not clean: in our own 50-ad test batch, 16 ads broke a channel rule (e.g. a 53-character headline where Google allows 30) and 2 still contained placeholder text such as “[website link]”. Every one of those has to be caught by a tired person reading fast. If it is missed, it gets rejected by the platform, embarrasses the agency in front of the client, or waits a day in someone's inbox."),
]
ORIGIN = ("At VeraAI I shipped genuinely powerful automation (an image-to-3D pipeline, an AI chatbot layer, real payments) and watched adoption depend on whether non-technical people could see what it did for them. "
          "When I started automating my own work in n8n, the same pattern showed up in marketing: AI now writes the ads in seconds, and people still spend hours carrying them to the right place. "
          "I want to build automation that does that last mile and, as a future consultant, sell it in a sentence a marketing lead understands.")
STORIES = [
    ("Story 1: the core job", "As an <b>agency marketing-ops lead</b>, I want <b>every new ad variant checked against its channel's rules and turned into a task for the right team, with an alert in our team chat</b>, so that <b>good ads go live the same day and I stop copying campaigns between tools.</b>"),
    ("Story 2: a secondary use case", "As a <b>paid-media specialist at the agency</b>, I want <b>the review alert to tell me exactly what is wrong (“headline 53/30 characters”, “‘unbeatable’ is an unproven claim”) and give me a rewrite that already fits</b>, so that <b>I can fix and publish a flagged ad in minutes instead of rewriting it from scratch.</b>"),
    ("Story 3: the edge case or power user", "As an <b>agency head of operations</b>, I want <b>a daily digest showing which mistakes keep recurring across all clients, what each team handled, what it cost, and what to change in the content writer's instructions</b>, so that <b>I can fix problems at the source and show clients the hours we saved.</b>"),
]
DATA = [
    dict(name="Ad copy library (A3 Source 1: HuggingFace “advertisement-copy”)",
         what="CSV · 90 records (100 collected, 10 shuffled duplicates removed) · one-time snapshot of a public dataset released 2023-09-25; refreshed only when we choose new sample ads.",
         rep="The creative itself: the headline, body and call-to-action a content writer hands over. This is exactly what the marketing-ops lead has to read and judge; it stands in for the ads Madison's Content Agent produces every day.",
         good="Every record has a headline of 3+ words, a product name and a body of 8+ words; at least 80% have a call-to-action. Records without a CTA, or with placeholder text (“[website]”, “bit.ly/…”), are kept but tagged, because they are the realistic failures the tool must catch. <i>Measured: headline 90/90 · product 90/90 · body 86/90 · CTA 74/90 (82%) · placeholders 3 tagged.</i>",
         path="data/verified/ad_copy"),
    dict(name="Campaign context (A3 Source 2: HuggingFace “marketing-campaign-performance-200k”)",
         what="CSV · 100 records · one-time snapshot (campaigns dated 2021-01-01 to 2021-04-10) of a public practice dataset (Kaggle mirror).",
         rep="Which client the ad is for and how that account is doing: company, channel (Google Ads, YouTube, Facebook, Instagram, Email, Website), audience, conversion rate and ROI. It answers “who owns this?” and “how urgent is it?”: a strong campaign ships today, a weak one waits.",
         good="Every record has a company, a channel from the six known channels, an audience, a numeric conversion rate and ROI, and a valid YYYY-MM-DD date. The data is synthetic and assigns campaign types at random, so the campaign type is always derived from the channel before use. <i>Measured: 100/100 on every field.</i>",
         path="data/verified/campaign_metadata"),
    dict(name="Market context (A3 Source 3: 4 marketing news feeds: HubSpot Marketing Blog 50, Social Media Examiner 25, Marketing Dive 10, MarTech 10)",
         what="RSS → CSV · 95 articles · refreshed on every collection run (the feeds publish daily); current snapshot 2026-07-22 to 2026-10-02.",
         rep="What is happening in marketing this week: platform changes, holiday-shopping trends, new ad features. Background only: it can raise an ad's priority when it is timely, but an ad is never penalised for not matching the news.",
         good="Every article has a title, a working source URL, a publication date within the last 90 days and a plain-text summary of 20+ words (no HTML, no “The post … appeared first on” footer); no URL appears twice. If a feed is down, the run says so by name and continues. <i>Measured: URL 95/95 · summary 91/95 · 0 duplicate URLs.</i>",
         path="data/verified/industry_briefs"),
    dict(name="New ad variants (the live input, built in A4)",
         what="JSON · one event per new variant, sent by the content agent to the tool's inbox; 834 test events processed so far.",
         rep="“Here is a new ad, ready for handoff”: the creative + its client campaign + optional market context + the content writer's own pass/fail quality check. One event = one decision the marketing-ops lead no longer has to make by hand.",
         good="Every event has its own ID, the campaign brief it belongs to, a variant ID, a headline, body, CTA and a valid creation date; it passed the content writer's own quality check; and that brief + variant pair has never been processed before. Anything else is turned away before any AI runs. <i>Measured in A4: 100% of invalid test events rejected (140 of 400 in the largest run).</i>",
         path="data/verified/variant_events"),
    dict(name="Action log (the tool's memory, built in A4)",
         what="Table (stored inside the automation tool, mirrored to a shared Google Sheet) · one row per decision · 800+ rows · grows with every event.",
         rep="What has already been handled, by whom, and why: decision, priority, owning team, reason, task ID, cost. It stops the same ad being assigned twice and feeds the daily report the head of operations reads.",
         good="Every row has a unique key (campaign brief + variant), a status, a decision, an owning team and a timestamp; every completed live row has a CRM task ID. <i>Measured: all completed live rows have a task ID; known gap: two identical ads arriving in the same second can both be logged (fix planned).</i>",
         path="data/verified/action_log"),
]
GOOD = [
    ("G1 · Step 1: Data ingestion", "All three sources answered, or the report names the one that did not. Record counts are in the expected range (ads 80–100, campaigns 100, articles 50+). Every raw record already has a title or headline, a date and a source name, and text arrives as words, not HTML error pages.", "✓ in pipeline (A3)"),
    ("G2 · Step 2: Data validation (GIGO gate)", "At least 80% of records are complete; 0 duplicates; 100% of dates are real YYYY-MM-DD dates in the past; every live event has all required fields, passed the content writer's quality check, and has not been seen before. Only then may the AI read it.", "✓ in workflow (A4)"),
    ("G3 · Step 3: AI processing / intelligence layer", "Every ad gets exactly one decision (approve / review / block), one owning team that matches its channel, and a reason in plain English. Every risk quotes words that really appear in the ad; every character count matches the real count; the suggested rewrite itself fits the channel's limit. A healthy batch auto-approves roughly a third of all ads (about half of the valid ones) and sends most of the rest to review with evidence and never “everything blocked” or “everything approved”.", "✓ schema + validator · evidence/count re-check planned (5B)"),
    ("G4 · Step 4: Final report or output", "A busy marketer understands each chat alert in five seconds: what the ad is, the decision, who owns it, why, and the fix, with a link to the task. Each CRM task has an action-first title, a due date set by urgency and the fix inside. The daily report opens with one sentence on what the batch means, then three findings backed by numbers and three concrete changes, and every number matches the action log.", "✓ live (Slack, HubSpot, Gmail, Sheets)"),
]
BAD = [
    ("X1 · Step 1: Data ingestion", "A source returns an error page, 0 records or a sudden drop of more than half its usual count; columns are missing or renamed; text arrives as raw HTML.",
     "<b>Log and continue</b> if the ad copy is still available: the run names the missing source and the remaining data is valid. <b>Hard stop</b> if the ad copy itself is missing: with no creative there is nothing to judge, and a report built on two sources would mislead."),
    ("X2 · Step 2: Data validation (GIGO gate)", "An ad with no headline or CTA, a creation date that is unreadable or in the future, the content writer's quality check failed, the same ad sent twice, or placeholder text like “[website link]”. Batch-level warning sign: more than 20% of a batch fails the gate.",
     "<b>Hard stop for that ad</b>: rejected before any AI runs, logged with the reason, the sender is told. <i>(Today the gate rejects missing fields, bad dates, failed quality checks and repeats; placeholder text is still caught one step later by the AI and blocked. Moving it into the gate is a 5B task.)</i> If more than 20% of a batch fails, <b>flag for review</b>: the content writer upstream is probably broken and the team should hear about it before tasks pile up."),
    ("X3 · Step 3: AI processing", "The AI quotes words that are not in the ad, gets a character count wrong, approves an ad that still contains placeholder text, assigns it to the wrong team, returns broken or refused output, or blocks most of a batch (our first instructions blocked 71–84% of valid ads in test batches because the AI treated unrelated news as a mismatch).",
     "Broken or refused output: <b>log and continue</b>: rule-based routing sends the ad to human review with a “AI unavailable” label (proven live in A4). Invented evidence or wrong counts: <b>flag for review</b>, never auto-approve. Placeholder text approved: <b>hard stop</b> on that ad. Batch block rate above 50%: <b>flag for review</b> and pause auto-approval until the instructions are checked."),
    ("X4 · Step 4: Final report or output", "The CRM or chat tool rejects the task or alert; the same ad gets two tasks; the daily report's numbers do not match the action log.",
     "Tool failure: <b>log and continue</b>: retried 3×, then logged as a partial failure so nothing silently disappears. Duplicate task: <b>flag for review</b>. Report mismatch: <b>hard stop</b>, so a report that would mislead a manager is never sent."),
]
COMPETITORS = [
    dict(name="Jasper", cat="AI marketing writer",
         well="Excellent at producing on-brand copy at volume. Its Brand Voice feature is the reason many G2 reviewers stay, and even the Pro plan ($59–69/seat/month) now includes “Agents for core marketing workflows”.",
         short="It stops at writing. It does not check a finished ad against the platform it will run on, decide who on the agency team handles it, or put it into the agency's CRM and chat. Reviewers say output still needs human fact-checking and can feel generic; custom agents need the contact-sales Business plan.",
         src=[("Jasper: official pricing & plan features", "https://www.jasper.ai/pricing"), ("Nicheaitool: Jasper review (1,270+ G2 reviews)", "https://nicheaitool.com/jasper-review"), ("EyeSift: Jasper G2 pros & complaints", "https://www.eyesift.com/blog/jasper-ai-review/"), ("Getaitopia: Jasper 2026 review", "https://getaitopia.io/blog/jasper-ai-review-2026")]),
    dict(name="Planable", cat="Content approval & collaboration",
         well="Agencies love its approval workflow (from optional approval to stacked multi-level chains), with all client feedback in one place instead of email or WhatsApp. It covers social posts plus newsletters, blogs and ads, connects to Slack, and scores around 4.6/5 on G2.",
         short="A person still judges every ad: it organises the review, it does not do it. Its AI can rewrite a post, but it does not tell the reviewer what breaks the channel's rules or why a claim is risky, and nothing lands as a task in the agency's CRM (its pricing page lists no HubSpot or CRM integration).",
         src=[("Planable: official pricing & features", "https://planable.io/pricing/"), ("PostPlanify: Planable reviews (G2 4.6)", "https://postplanify.com/planable-reviews"), ("SocialRails: Planable review 2026", "https://socialrails.com/blog/planable-review"), ("Capterra: Planable", "https://capterra.com/p/171744/Planable/")]),
    dict(name="Zapier Agents", cat="General automation",
         well="Connects 9,000+ apps, so it can move copy into HubSpot, Asana or Slack, and its new agents can be given company knowledge and instructions in plain language.",
         short="It moves data without understanding it. One reviewer: it “knows how to call thousands of APIs and nothing about what your data means”. The agency would have to write and maintain every channel rule itself; reviewers recommend a human approval step before an agent writes to a system of record because its output is not predictable, and multi-step runs burn through task limits quickly.",
         src=[("Zapier: official Agents page", "https://zapier.com/agents"), ("The Startup Flow: Zapier AI Agents review for marketing teams", "https://www.thestartupflow.com/2026/09/zapier-ai-agents-review.html"), ("iMark Infotech: Zapier Agents in 2026", "https://www.imarkinfotech.com/zapier-agents-in-2026-when-ai-agents-inside-your-automation-stack-beat-deterministic-zaps/"), ("Willo: Zapier review 2026", "https://www.willo.ai/blog/zapier-review")]),
]
ALSO = ("Also considered: HubSpot Breeze (Content Agent / Agent Hub): strong inside HubSpot, but it only reasons over HubSpot data, its content agent still needs substantial editing for brand voice, "
        "and agents are gated to Professional/Enterprise tiers.", [("Default: HubSpot Breeze review", "https://www.default.com/post/hubspot-breeze-ai-review-and-pricing"), ("Resolve247: HubSpot Breeze honest review", "https://resolve247.ai/blog/hubspot-breeze/")])
GAP = ("Writers write, approval tools wait for a person, and automation tools move data without judging it. None of them takes a finished ad, judges it against the real rules of the channel it will run on, "
       "and delivers the verdict (with the exact evidence, a fix that fits, and an owner) into the CRM and chat the agency already uses. That last mile between “an ad exists” and “the right person is doing the right thing with it” is still manual.")
ONE = (f"Our tool is the only <b>ad-handoff assistant</b> that <b>delivers an explained verdict on every finished ad, checked against its channel's real rules, straight to the teammate who owns it, inside the agency's own CRM and chat,</b> "
       "for <b>agency marketing-ops leads</b> without <b>making them switch content platforms or read every ad themselves</b>.")
WHY = ("This removes exactly the work described in Part 2. In our live 50-ad test, 15 broken ads were stopped before anyone saw them, 16 good ads were approved and assigned automatically, and 18 reached a person already "
       "carrying the quoted problem and a rewrite: 35 tasks and 35 alerts in 28 seconds, for about half a cent per ad, replacing roughly 3.5 hours of handoff. The marketing-ops lead only spends attention where judgment is actually needed.")
DEFEND = [
    "<b>It is a loop, not a feature.</b> A quality gate that refuses bad input before any AI runs, channel-rule judgment, delivery into the agency's own tools, and an action log that remembers every decision and feeds a daily report back to the content writer. Copying one piece does not reproduce the result.",
    "<b>The judgment is calibrated, and the calibration compounds.</b> Our first version blocked 71–84% of valid ads; the severity rules were rebuilt from what went wrong (placeholders and false claims are serious, ordinary marketing adjectives are not). The instructions could be copied in a week; the channel rulebook and the growing log of explained decisions, which becomes the test set for every future change, cannot.",
    "<b>It is designed to fail safely.</b> When the AI is unavailable the ad is still routed to a person with a clear label (proven live), duplicates are refused, and every outcome is logged. Trust is what lets an agency let it run unattended, and trust takes evidence to earn, not a week of coding.",
    "<b>It sits between tools rather than inside one.</b> Jasper, Planable and HubSpot are each built around their own platform; judging and routing work across a client's mixed stack runs against their business model.",
]
NEXT = [("5A / 5B", "Part 1 becomes the interface description and recipe summary; Parts 4–5 become the input validation, phase gates and GIGO rules; Part 3 becomes brand_config.json."),
        ("A6", "Part 6 is the positioning for naming and brand identity; the working name “Madison Automation Agent” will be replaced there."),
        ("Weeks 7–12", "Part 1 → headline · Part 2 → origin story · Part 6 → pitch.")]

# ---------------------------------------------------------------- markdown review copy
md = [f"# The Conductor Brief: {NAME}", "Mayank Bhadrasen · INFO7375 Branding & AI · Assignment 5 · October 2026", "",
      "## Part 1: The tool in one sentence", f"> {SENTENCE}", "", "## Part 2A: The user and their situation"]
md += [f"**{k}:** {v}" + "\n" for k, v in USER]
md += ["## Part 2B: Three user stories"] + [f"**{t}:** {s.replace('<b>', '**').replace('</b>', '**')}\n" for t, s in STORIES]
md += ["## Part 3: The data contract"]
for i, d in enumerate(DATA, 1):
    md += [f"### Data Source {i}", f"- **Name:** {d['name']}", f"- **What it is:** {d['what']}", f"- **What it represents:** {d['rep']}",
           f"- **How we know it is good:** {d['good'].replace('<i>', '_').replace('</i>', '_')}", f"- **Local path:** `{d['path']}`", ""]
md += ["## Part 4: What good looks like"] + [f"**{s}** ({st})  \nGood looks like: {g}\n" for s, g, st in GOOD]
md += ["## Part 5: What bad looks like"] + [f"**{s}**  \nBad looks like: {b}  \nResponse: {r.replace('<b>', '**').replace('</b>', '**')}\n" for s, b, r in BAD]
md += ["## Part 6A: Competitive evidence"]
for i, c in enumerate(COMPETITORS, 1):
    md += [f"**Competitor {i}: {c['name']}** ({c['cat']})", f"- What they do well: {c['well']}", f"- Where they fall short for our user: {c['short']}",
           "- Source: " + "; ".join(f"[{t}]({u})" for t, u in c['src']), ""]
md += [ALSO[0] + " Sources: " + "; ".join(f"[{t}]({u})" for t, u in ALSO[1]), "", f"**The gap all three share:** {GAP}", "",
       "## Part 6B: The one thing", f"> {ONE.replace('<b>', '**').replace('</b>', '**')}", "", f"**Why this matters to our user:** {WHY}", "",
       "**Why this is defensible:**"] + [f"- {d.replace('<b>', '**').replace('</b>', '**')}" for d in DEFEND]
(ROOT / "brief.md").write_text("\n".join(md) + "\n", encoding="utf-8")

# ---------------------------------------------------------------- PDF
CSS = """@page { size: Letter; margin: 0.65in 0.7in; }
:root { --ink:#1f1b16; --text:#3a342c; --muted:#776d61; --line:#e6ddd0; --accent:#a8472a; --soft:#f6e9e0; --bg:#f3eee6; --warn:#8a6418; --bad:#9b2c1f; --good:#5c6b45; --paper:#fbf8f3; }
* { box-sizing:border-box; } body { margin:0; font-family:-apple-system,"SF Pro Text","Helvetica Neue",Arial,sans-serif; color:var(--text); font-size:9.9pt; line-height:1.5; background:var(--paper); }
@page { background:#fbf8f3; } html { background:#fbf8f3; -webkit-print-color-adjust:exact; print-color-adjust:exact; }
h1,h2,h3 { font-family:"Iowan Old Style","Palatino","Georgia",serif; font-weight:700; } .quote, .hero { font-family:"Iowan Old Style","Palatino","Georgia",serif; }
h1,h2,h3 { color:var(--ink); margin:0; line-height:1.2; } section { break-before:page; } p { margin:6px 0; }
.k { color:var(--accent); font-weight:700; letter-spacing:.14em; font-size:8.4pt; text-transform:uppercase; }
h2 { font-size:17pt; margin:4px 0 4px; } h2 .n { color:var(--accent); margin-right:8px; } .lead { color:var(--muted); margin:0 0 14px; }
h3 { font-size:11pt; margin:14px 0 6px; break-after:avoid; }
.cover { height:9.5in; display:flex; flex-direction:column; justify-content:space-between; }
.cover h1 { font-size:34pt; margin:12px 0 6px; letter-spacing:-.01em; } .cover .sub { font-size:13pt; color:var(--muted); }
.hero { margin-top:34px; background:var(--ink); color:#fff; border-radius:10px; padding:26px 30px; font-size:16.5pt; line-height:1.45; font-weight:500; }
.hero .k { color:#e8b89c; display:block; margin-bottom:10px; }
.pillars { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-top:22px; }
.pillar { border:1px solid var(--line); border-top:3px solid var(--accent); border-radius:6px; padding:12px 14px; font-size:9.2pt; } .pillar b { color:var(--ink); display:block; font-size:10pt; margin-bottom:3px; }
.meta { border-top:1px solid var(--line); padding-top:12px; display:grid; grid-template-columns:1fr 1fr; gap:4px 24px; font-size:9.3pt; } .meta b { color:var(--ink); }
.toc { columns:2; font-size:9.6pt; margin-top:22px; } .toc div { padding:3px 0; border-bottom:1px dotted var(--line); } .toc span { color:var(--accent); font-weight:700; margin-right:6px; }
.quote { border-left:4px solid var(--accent); background:var(--soft); padding:16px 20px; border-radius:0 8px 8px 0; font-size:14pt; color:var(--ink); line-height:1.45; font-weight:500; margin:10px 0 14px; }
.anatomy { display:grid; grid-template-columns:repeat(4,1fr); gap:8px; margin:6px 0 12px; }
.anatomy div { border:1px solid var(--line); border-radius:6px; padding:8px 10px; font-size:8.8pt; background:var(--bg); } .anatomy b { display:block; color:var(--accent); font-size:7.8pt; letter-spacing:.08em; text-transform:uppercase; }
.check { font-size:9pt; } .check td { padding:5px 8px; border-bottom:1px solid var(--line); vertical-align:top; } .check td:first-child { width:24px; color:var(--good); font-weight:700; }
table { width:100%; border-collapse:collapse; } .profile td { padding:9px 10px; border-bottom:1px solid var(--line); vertical-align:top; } .profile td:first-child { width:1.75in; font-weight:700; color:var(--ink); }
.story { border:1px solid var(--line); border-left:4px solid var(--accent); border-radius:6px; padding:10px 14px; margin:8px 0; break-inside:avoid; } .story .k { display:block; margin-bottom:3px; } .story p { margin:0; font-size:10.4pt; }
.ds { border:1px solid var(--line); border-radius:8px; margin:9px 0; break-inside:avoid; overflow:hidden; }
.ds .hd { background:var(--ink); color:#fff; padding:7px 12px; font-weight:600; font-size:9.6pt; } .ds .hd span { color:#e8b89c; margin-right:8px; }
.ds table td { padding:5px 12px; border-bottom:1px solid var(--line); vertical-align:top; font-size:9pt; } .ds table td:first-child { width:1.45in; color:var(--muted); font-weight:600; }
.ds code { background:var(--bg); padding:1px 5px; border-radius:3px; font-size:8.6pt; color:#5a4f43; }
.gate { display:grid; grid-template-columns:1.35in 1fr 1.35in; border:1px solid var(--line); border-radius:6px; margin:8px 0; break-inside:avoid; overflow:hidden; }
.gate > div { padding:7px 11px; } .gate.bad { font-size:9.3pt; line-height:1.42; } .gate.bad .resp { font-size:8.8pt; } .gate .s { background:#ecefe4; color:var(--good); font-weight:700; } .gate .st { background:var(--bg); font-size:8.3pt; color:var(--muted); }
.gate.bad .s { background:#f7e4dd; color:var(--bad); }
.resp { margin-top:5px; padding-top:5px; border-top:1px dashed var(--line); font-size:9pt; } .resp b { color:var(--ink); }
.comp { border:1px solid var(--line); border-radius:8px; padding:8px 13px; margin:7px 0; break-inside:avoid; }
.comp h3 { margin:0 0 4px; } .comp h3 small { color:var(--muted); font-weight:500; font-size:9pt; margin-left:6px; }
.comp .two { display:grid; grid-template-columns:1fr 1fr; gap:14px; font-size:8.9pt; line-height:1.42; } .comp .lab { font-size:7.8pt; font-weight:700; letter-spacing:.08em; text-transform:uppercase; }
.lab.g { color:var(--good); } .lab.r { color:var(--bad); } .src { font-size:7.9pt; color:var(--muted); margin-top:6px; } .src a { color:var(--accent); text-decoration:underline; text-underline-offset:2px; } .srclist li { margin:4px 0; font-size:8.8pt; line-height:1.4; } .srclist a { color:var(--accent); word-break:break-all; } .srclist b { color:var(--ink); }
.gapbox { font-size:9.4pt; background:#f6eedb; border:1px solid #e3cf9f; border-radius:8px; padding:12px 16px; margin-top:10px; } .gapbox .k { color:var(--warn); }
.matrix td, .matrix th { padding:4px 8px; border-bottom:1px solid var(--line); font-size:8.8pt; text-align:center; } .matrix th { background:var(--ink); color:#fbf8f3; font-size:8.2pt; } .matrix td:first-child { text-align:left; } .matrix .no { color:#b9ad9e; } .matrix .us { background:var(--soft); font-weight:700; color:var(--ink); }
.def { margin:4px 0; padding-left:18px; font-size:9.4pt; } .def li { margin:3px 0; line-height:1.4; } .proof { display:grid; grid-template-columns:repeat(4,1fr); gap:8px; margin:10px 0; }
.proof div { border:1px solid var(--line); border-top:3px solid var(--accent); border-radius:6px; padding:8px 10px; } .proof b { display:block; font-size:15pt; color:var(--ink); } .proof span { font-size:8.2pt; color:var(--muted); }
.foot { font-size:8pt; color:var(--muted); margin-top:10px; }"""

pillars = [("Who", "Agency marketing-ops leads juggling 10–30 client brands"), ("What it does", "Checks every new ad, decides what ships, hands it to the right teammate with a fix"),
           ("Why it matters", "Same-day launches, fewer rejected or embarrassing ads, ~10 h/week back")]
toc = ["The tool in one sentence", "The user and the problem", "The data contract", "What good looks like", "What bad looks like", "The one thing"]
pages = []
pages.append(f"""<div class="cover"><div><div class="k">INFO7375 Branding &amp; AI · Assignment 5 · The Conductor Brief</div>
<h1>{NAME}</h1><div class="sub">Strategic brief: what the tool is, who it is for, what it trusts, and what good looks like.</div>
<div class="hero"><span class="k">The Tool In One Sentence</span>{e(SENTENCE)}</div>
<div class="pillars">{''.join(f'<div class="pillar"><b>{e(a)}</b>{e(b)}</div>' for a, b in pillars)}</div>
<div class="toc">{''.join(f'<div><span>{i}</span>{e(t)}</div>' for i, t in enumerate(toc, 1))}</div></div>
<div class="meta"><div><b>Author</b> Mayank Bhadrasen · MS Information Systems</div><div><b>Instructors</b> Professors Nina Harris &amp; Nik Brown</div>
<div><b>Builds on</b> A1 profile · A2 PRD · A3 data · A4 intelligence layer</div></div></div>""")

pages.append(f"""<section><div class="k">Part 1</div><h2><span class="n">1</span>The tool in one sentence</h2>
<p class="lead">If someone forgets everything else in this brief, this is what they should remember.</p>
<div class="quote">{e(SENTENCE)}</div>
<div class="anatomy"><div><b>Tool</b>{NAME}</div><div><b>Specific user</b>agency marketing-ops leads</div>
<div><b>Specific action</b>check every new ad against its platform's rules and hand it to the right teammate with a ready-to-use fix</div>
<div><b>Specific outcome</b>ship good ads the same day, instead of losing hours to copy-paste and chasing approvals</div></div>
<h3>Shorter forms (for later)</h3><table class="check">
<tr><td>→</td><td><b>Tagline:</b> Every ad checked, owned and moving. The same day.</td></tr>
<tr><td>→</td><td><b>Spoken:</b> “It's the step between ‘the ad is written’ and ‘the right person is working on it’, done in seconds.”</td></tr></table>
<h3>Plain-English glossary (for readers who have not seen the PRD)</h3><table class="check">
<tr><td>·</td><td><b>Ad variant</b>: one version of an ad: headline, body text and call-to-action (“Shop now”). Agencies test several per campaign.</td></tr>
<tr><td>·</td><td><b>Madison</b>: an open-source marketing framework whose Content Agent writes ad variants. This tool picks up where Madison stops.</td></tr>
<tr><td>·</td><td><b>Channel rules</b>: each platform's limits, e.g. a Google Ads headline is at most 30 characters; an email subject line should stay under 60.</td></tr>
<tr><td>·</td><td><b>CRM</b>: the agency's customer and task system (here HubSpot). <b>Team chat</b>: Slack.</td></tr>
<tr><td>·</td><td><b>Quality gate</b>: a check that must pass before the next step is allowed to run. <b>GIGO</b>: “garbage in, garbage out”.</td></tr>
<tr><td>·</td><td><b>Action log</b>: the tool's record of every decision, so nothing is done twice and every number can be traced.</td></tr></table></section>""")

pages.append(f"""<section><div class="k">Part 2</div><h2><span class="n">2</span>The user and the problem</h2>
<p class="lead">A: the person and their situation · B: three user stories, each describing something the tool does today.</p>
<h3>A · The user and their situation</h3><table class="profile">{''.join(f'<tr><td>{e(k)}</td><td>{e(v)}</td></tr>' for k, v in USER)}</table>
<div class="gapbox" style="margin-top:12px"><div class="k">Why I built this (from Assignment 1)</div>{e(ORIGIN)}</div>
</section><section><div class="k">Part 2B</div><h2><span class="n">2</span>Three user stories</h2><p class="lead">Standard format: As a [role], I want [capability] so that [outcome]. Each describes something the tool does today.</p>{''.join(f'<div class="story"><span class="k">{e(t)}</span><p>{s}</p></div>' for t, s in STORIES)}
</section>""")

ds_html = "".join(f"""<div class="ds"><div class="hd"><span>Data Source {i} · DS{i}</span>{e(d['name'])}</div><table>
<tr><td>What it is</td><td>{e(d['what'])}</td></tr><tr><td>What it represents</td><td>{e(d['rep'])}</td></tr>
<tr><td>How we know it is good</td><td>{d['good']}</td></tr><tr><td>Local path</td><td><code>{d['path']}</code></td></tr></table></div>""" for i, d in enumerate(DATA, 1))
pages.append(f"""<section><div class="k">Part 3</div><h2><span class="n">3</span>The data contract</h2>
<p class="lead">What goes in, what it means for the user's problem, and a quality standard a person could check by opening the file. Sources 1–3 are the three Assignment 3 sources; 4–5 are what the tool reads while it runs.</p>{ds_html}</section>""")

gates = "".join(f'<div class="gate"><div class="s">{e(s)}</div><div>{e(g)}</div><div class="st">{e(st)}</div></div>' for s, g, st in GOOD)
pages.append(f"""<section><div class="k">Part 4 · Phase gates</div><h2><span class="n">4</span>What good looks like</h2>
<p class="lead">At each step, what a person checks before letting the next step run. Gate IDs G1–G4 are reused as the phase gates in 5B; right column: enforced today vs planned for 5B. Each gate reads the data sources defined in Part 3 (DS1–DS5).</p>{gates}
<div class="proof"><div><b>94.4%</b><span>A3 records complete (gate ≥ 80%)</span></div><div><b>0</b><span>duplicates · bad dates in A3 data</span></div>
<div><b>46%</b><span>of valid ads auto-approved in the live 50-ad batch</span></div><div><b>5 s</b><span>target time to understand one alert</span></div></div></section>""")

BAD_ST = ["✓ source status logged (A3) · ad-copy hard stop planned (5B)", "✓ gate live (A4) · placeholder + 20% batch alarm planned (5B)",
          "✓ fallback live (A4) · evidence/count re-check + 50% block alarm planned (5B)", "✓ retries + partial-failure log live (A4) · report reconciliation planned (5B)"]
bads = "".join(f'<div class="gate bad"><div class="s">{e(s)}</div><div>{e(b)}<div class="resp"><b>Response:</b> {r}</div></div><div class="st">{e(st)}</div></div>' for (s, b, r), st in zip(BAD, BAD_ST))
pages.append(f"""<section><div class="k">Part 5 · GIGO layer</div><h2><span class="n">5</span>What bad looks like</h2>
<p class="lead">What garbage looks like for this tool, and what happens when it appears. Rule of thumb: stop whatever could mislead a client or a manager; label and continue whatever a person can safely finish. IDs X1–X4 mirror gates G1–G4 in Part 4; right column: enforced today vs planned for 5B.</p>{bads}
<p class="foot">Live evidence (A4): 140 of 400 invalid events rejected before any AI ran · duplicate re-send refused in 0.19 s · AI made unreachable on purpose → ad still routed to review with an “AI unavailable” label, no crash.</p></section>""")

comps = "".join(f"""<div class="comp"><h3>Competitor {i}: {e(c['name'])}<small>{e(c['cat'])}</small></h3><div class="two">
<div><div class="lab g">What they do well</div>{e(c['well'])}</div><div><div class="lab r">Where they fall short for our user</div>{e(c['short'])}</div></div>
<div class="src"><b>Source:</b> vendor page (checked 2026-10-16) + user reviews (G2/Capterra) as summarised in: {' · '.join(f'<a href="{u}">{e(t)}</a>' for t, u in c['src'])}</div></div>""" for i, c in enumerate(COMPETITORS, 1))
matrix = """<table class="matrix"><tr><th>Does it…</th><th>Jasper</th><th>Planable</th><th>Zapier Agents</th><th>Madison Automation Agent</th></tr>
<tr><td>Write the ad</td><td>✓</td><td class="no">·</td><td class="no">·</td><td class="us">No (receives it)</td></tr>
<tr><td>Judge a finished ad against its channel's rules</td><td class="no">·</td><td>person does it</td><td>only if you build it</td><td class="us">✓</td></tr>
<tr><td>Quote the exact problem + give a fix that fits</td><td class="no">·</td><td>rewrite only</td><td class="no">·</td><td class="us">✓</td></tr>
<tr><td>Assign to the right team in the agency's CRM + chat</td><td class="no">·</td><td>chat only (no CRM)</td><td>✓ (no judgment)</td><td class="us">✓</td></tr>
<tr><td>Refuse broken / duplicate input before acting</td><td class="no">·</td><td class="no">·</td><td class="no">·</td><td class="us">✓</td></tr>
<tr><td>Daily report of recurring mistakes across clients</td><td class="no">·</td><td class="no">·</td><td class="no">·</td><td class="us">✓</td></tr></table>"""
pages.append(f"""<section><div class="k">Part 6A</div><h2><span class="n">6</span>The one thing: competitive evidence</h2>
<p class="lead">Three tools an agency marketing-ops lead would realistically reach for today.</p>{comps}
<p class="src">{e(ALSO[0])} Sources: {' · '.join(f'<a href="{u}">{e(t)}</a>' for t, u in ALSO[1])}</p>
<div class="gapbox"><div class="k">The gap all three share</div>{e(GAP)}</div></section>""")

pages.append(f"""<section><div class="k">Part 6B</div><h2><span class="n">6</span>The one thing</h2>
<div class="quote" style="font-size:12.2pt;padding:12px 18px">{ONE}</div>{matrix}
<h3>Why this matters to our user</h3><p>{e(WHY)}</p>
<div class="proof"><div><b>15</b><span>broken ads stopped before anyone saw them</span></div><div><b>16</b><span>good ads approved &amp; assigned automatically</span></div>
<div><b>18</b><span>reached a person with the problem quoted + a rewrite</span></div><div><b>28 s</b><span>for the whole 50-ad batch (≈3.5 h by hand)</span></div></div>
<h3>Why this is defensible</h3><ul class="def">{''.join(f'<li>{d}</li>' for d in DEFEND)}</ul>
</section><section><div class="k">Closing</div><h2>Where this brief goes next</h2><p class="lead">The Conductor Brief is the strategic source for everything that follows. Each part below is written so it can be lifted directly into the next assignment.</p>
<table class="matrix" style="margin-bottom:10px"><tr><th style="text-align:left">Brief part</th><th>5A · Interface (Path A)</th><th>5B · Recipe (Path B)</th><th>A6 · Brand identity</th><th>Weeks 7–12</th></tr>
<tr><td>1 · One sentence</td><td>Interface description</td><td>Recipe executive summary</td><td>Tagline seed</td><td>Headline</td></tr>
<tr><td>2 · User &amp; problem</td><td>Who the screen is for</td><td>Recipe audience</td><td>Persona</td><td>Origin story</td></tr>
<tr><td>3 · Data contract DS1–DS5</td><td>Input fields</td><td><b>brand_config.json</b> (draft ready)</td><td class="no">·</td><td>Proof points</td></tr>
<tr><td>4 · Gates G1–G4</td><td>Output formatting (G4)</td><td>Phase-gate criteria</td><td class="no">·</td><td class="no">·</td></tr>
<tr><td>5 · GIGO X1–X4</td><td>Input validation &amp; error states</td><td>GIGO definitions</td><td class="no">·</td><td>Trust story</td></tr>
<tr><td>6 · The one thing</td><td>Hero message</td><td class="no">·</td><td><b>Positioning foundation</b></td><td>Pitch</td></tr></table><table class="check">{''.join(f'<tr><td>→</td><td><b>{e(a)}:</b> {e(b)}</td></tr>' for a, b in NEXT)}<tr><td>→</td><td><b>Companion file (project folder, not part of this PDF):</b> <code>brand_config.draft.json</code>: Part 3 plus the G1–G4 / X1–X4 thresholds and channel rules in machine-readable form, ready for 5B.</td></tr></table>
<h3>Summary for the conductor</h3>
<table class="check"><tr><td>1</td><td><b>User:</b> agency marketing-ops lead, 10–30 client brands, drowning in ad handoffs.</td></tr>
<tr><td>2</td><td><b>Inputs it trusts:</b> ad copy, campaign context, market context, new-ad events, its own action log, each with a checkable standard (Part 3).</td></tr>
<tr><td>3</td><td><b>Gates:</b> nothing reaches the AI unless it passes validation; nothing reaches a client unless a decision is explained (Parts 4–5).</td></tr>
<tr><td>4</td><td><b>Position:</b> the only ad-handoff assistant that delivers an explained verdict on every finished ad straight to the teammate who owns it, inside the agency's own CRM and chat (Part 6).</td></tr></table><p class="foot">Evidence: A4 live run v2-50 (2026-10-09) and load tests: Assignment_4/scale_test_results.md, workflow_run_and_error_handling.md. Time saved assumes 6 minutes of manual handoff per ad. Market figures: DoubleVerify 2025 Global Insights.</p></section>""")

SRC_ALL = [(c["name"], c["src"]) for c in COMPETITORS] + [("HubSpot Breeze (also considered)", ALSO[1])]
other = [("DoubleVerify 2025 Global Insights (problem cost, Part 2A)", "https://doubleverify.com/newsroom"),
         ("Project evidence (Parts 3–6)", "Assignment_3/madison_a3_records.csv · Assignment_4/scale_test_results.md · Assignment_4/workflow_run_and_error_handling.md")]
items = "".join(f"<li><b>{e(n)}</b><ul>" + "".join(f'<li>{e(t)}: <a href="{u}">{e(u)}</a></li>' for t, u in srcs) + "</ul></li>" for n, srcs in SRC_ALL)
pages.append(f"""<section><div class="k">References</div><h2>Sources</h2>
<p class="lead">Every competitor claim in Part 6A, with the full address. Vendor pages were checked on 2026-10-16; review sites summarise G2 and Capterra user reviews.</p>
<ol class="srclist">{items}</ol>
<h3>Other evidence</h3><ul class="srclist"><li><b>{e(other[0][0])}</b>: survey of 1,970 marketers, as cited in the Assignment 2 PRD.</li><li><b>{e(other[1][0])}</b>: {e(other[1][1])}</li></ul></section>""")
doc = f"<!doctype html><html><head><meta charset='utf-8'><title>Bhadrasen_Mayank_A5_ConductorBrief</title><style>{CSS}</style></head><body>{''.join(pages)}</body></html>"
h = ROOT / "_build" / "brief.html"; h.write_text(doc, encoding="utf-8")
pdf = ROOT / "Bhadrasen_Mayank_A5_ConductorBrief.pdf"
subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--headless", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={pdf}", h.as_uri()], check=True, capture_output=True)
print("wrote", pdf.name, "and brief.md")

# ---------------------------------------------------------------- brand_config.draft.json (for 5B)
import json
CONFIG = {
  "_note": "Draft generated from Conductor Brief Part 3-5 (A5). Thresholds are the human-checkable standards in the brief; 'enforced' marks what workflow_v2 already checks.",
  "tool": {"name": NAME, "one_sentence": SENTENCE, "primary_user": USER[0][1], "one_thing": html.unescape(ONE.replace("<b>", "").replace("</b>", ""))},
  "data_sources": [
    {"id": "DS1", "name": "ad_copy", "path": "data/verified/ad_copy/ad_copy.csv", "format": "csv", "records": 90, "refresh": "static snapshot (dataset 2023-09-25)",
     "required_fields": ["title_or_headline", "body_text", "brand_or_product"], "checks": {"headline_min_words": 3, "body_min_words": 8, "cta_present_min_pct": 80, "placeholders": "tag, do not drop"}},
    {"id": "DS2", "name": "campaign_metadata", "path": "data/verified/campaign_metadata/campaign_metadata.csv", "format": "csv", "records": 100, "refresh": "static snapshot (2021-01-01..2021-04-10)",
     "required_fields": ["brand_or_product", "channel", "audience", "published_date"], "checks": {"allowed_channels": ["Google Ads", "YouTube", "Facebook", "Instagram", "Email", "Website"], "date_format": "YYYY-MM-DD", "derive_campaign_type_from_channel": True}},
    {"id": "DS3", "name": "industry_briefs", "path": "data/verified/industry_briefs/industry_briefs.csv", "format": "csv (from RSS)", "records": 95, "refresh": "every collection run",
     "required_fields": ["title_or_headline", "source_url", "published_date", "body_text"], "checks": {"max_age_days": 90, "summary_min_words": 20, "no_html": True, "unique_url": True, "role": "context only - never penalise an ad for not matching"}},
    {"id": "DS4", "name": "variant_events", "path": "data/verified/variant_events/", "format": "jsonl / webhook JSON", "records": "1 per new ad", "refresh": "real time",
     "required_fields": ["event_id", "brief_id", "variant_id", "headline", "body", "cta", "popper_pass", "created_at"], "checks": {"popper_pass": True, "created_at_valid_past": True, "idempotency_key": "brief_id:variant_id unseen"}},
    {"id": "DS5", "name": "action_log", "path": "data/verified/action_log/", "format": "n8n Data Table + Google Sheet", "records": "1 per decision", "refresh": "real time",
     "required_fields": ["idempotency_key", "status", "decision", "owner_team", "createdAt"], "checks": {"unique_key": True, "live_completed_has_task_id": True}},
  ],
  "phase_gates": [
    {"id": "G1", "step": "data ingestion", "pass_if": ["all 3 A3 sources answered or named as unavailable", "ads 80-100, campaigns 100, articles >=50", "no raw HTML"], "enforced": True},
    {"id": "G2", "step": "data validation", "pass_if": [">=80% complete", "0 duplicates", "100% valid past YYYY-MM-DD dates", "event has required fields, passed quality check, unseen key"], "enforced": True},
    {"id": "G3", "step": "AI processing", "pass_if": ["one decision + owner + plain-English reason", "quoted evidence appears in the ad", "char counts correct", "rewrite fits channel limit", "batch: not all blocked / not all approved"], "enforced": "schema+enums yes; evidence/count re-check planned"},
    {"id": "G4", "step": "final output", "pass_if": ["alert readable in 5 s", "task has action title + due date + fix", "report numbers match action log"], "enforced": "partly"},
  ],
  "gigo_rules": [
    {"id": "X1", "trigger": "source error/empty/drop >50%/raw HTML", "response": "log_and_continue", "except": {"if": "DS1 missing", "response": "hard_stop"}},
    {"id": "X2", "trigger": "missing headline/CTA, bad date, failed quality check, duplicate, placeholder text", "response": "hard_stop_item", "batch": {"if_fail_rate_over_pct": 20, "response": "flag_for_review"}},
    {"id": "X3", "trigger": "malformed/refused AI output", "response": "log_and_continue (fallback router)",
     "also": [{"if": "invented evidence or wrong counts", "response": "flag_for_review"}, {"if": "placeholder approved", "response": "hard_stop_item"}, {"if": "batch block rate over 50%", "response": "flag_for_review + pause auto-approve"}]},
    {"id": "X4", "trigger": "CRM/chat rejects, duplicate task, report mismatch", "response": "log_and_continue (3 retries)", "also": [{"if": "duplicate task", "response": "flag_for_review"}, {"if": "report mismatch", "response": "hard_stop"}]},
  ],
  "channel_rules": {"Google Ads": {"headline_max_chars": 30, "description_max_chars": 90, "emoji": False, "hashtags": False},
                    "Email": {"subject_max_chars": 60, "hashtags": False}, "Facebook": {"hook_chars": 40, "truncate_at": 125},
                    "Instagram": {"hook_chars": 40, "truncate_at": 125, "hashtags": True}, "YouTube": {"needs_spoken_hook": True}, "Website": {"clarity_over_hype": True}},
  "brand": {"palette": {"paper": "#fbf8f3", "ink": "#1f1b16", "accent": "#a8472a", "good": "#5c6b45", "bad": "#9b2c1f", "highlight": "#8a6418"}, "heading_font": "Iowan Old Style / Georgia"},
}
(ROOT / "brand_config.draft.json").write_text(json.dumps(CONFIG, indent=2, ensure_ascii=False))
print("wrote brand_config.draft.json")
