---
status: RUNNABLE LIVE (dry run)
todos_open: 8
last_gate: LAST_GATE
attestation: Mayank Bhadrasen (human conductor)
recipe_version: 1.0.0
---

# Madison Ad Handoff: Channel-Rule Check and Team Routing

RECIPE: Madison Automation Agent (workflow `madison-ad-handoff`)
Version: 1.0 | Last run: LAST_RUN | Run frequency: Daily (each morning before client launch windows) and on demand

--- EXECUTIVE SUMMARY ---
This recipe takes a batch of new ad variants, checks each one against the real rules of the channel it will run on (Google Ads, Facebook, Instagram, YouTube, Email, Website), decides whether it can ship, needs a fix or must not be published, and assigns it to the owning team with a ready-to-use fix. It is run by the agency's marketing-ops lead, or by a conductor (Claude Code or a colleague) on their behalf, once a day or whenever a new batch arrives. It reads three verified sources (ad copy, client campaign context, current marketing news) and calls the Assignment 4 Routing Agent (Claude Haiku 4.5). A successful run produces a one-page handoff report in `logs/reports/` that tells the lead what ships today, what each team must fix and why, and which verdicts need a manual check, plus a run log and a record of every gate decision.

## Purpose
An agency marketing-ops lead receives more AI-written and copywriter ads than they can read carefully before launch. This pipeline answers one question for every new ad: *can it go live on its channel today, and if not, who must fix what?* It replaces the manual routine of counting characters, spotting unproven claims or unfinished links, and copying ads into tasks for the right team. It does not write ads and it does not publish them.

## Inputs

| Input | Type | Source | Required? |
|---|---|---|---|
| Ad copy library | JSON (HF datasets-server rows) | `https://datasets-server.huggingface.co/rows?dataset=jaykin01/advertisement-copy&config=default&split=train&offset=0&length=100` | Yes (hard stop if missing) |
| Campaign context | JSON (HF datasets-server rows) | `https://datasets-server.huggingface.co/rows?dataset=federicomoreno/marketing-campaign-performance-200k&config=default&split=train&offset=0&length=100` | Yes |
| Market context | RSS 2.0 XML (4 feeds) | `https://blog.hubspot.com/marketing/rss.xml` · `https://www.socialmediaexaminer.com/feed/` · `https://www.marketingdive.com/feeds/news/` · `https://martech.org/feed/` | No (context only; run continues if a feed is down) |
| Routing Agent endpoint | HTTPS webhook (n8n, Claude Haiku 4.5) | env `MADISON_WEBHOOK_URL` + `MADISON_WEBHOOK_KEY` (never in files) | Yes for live; not used in `--sample` |
| Offline fixture | CSV | `fixtures/a3_snapshot.csv` (Assignment 3 output) | Only for `--sample` |
| Config | JSON | `brand_config.json` (thresholds, gates, judgment types) | Yes |

## Phase Gates
Every gate prints its checks, states the recipe response, and **waits for the human's typed decision** (approve / stop). Decisions are written to `logs/gate-decisions/<run_id>-gate<N>.json`.

0. Run approval: the plan is shown before anything is fetched; dry run (no HubSpot/Slack writes); batch ≤ 50 ads; AI credentials present for live mode. Test: `python3 scripts/run_pipeline.py` prints Gate 0 checks; `test -f logs/gate-decisions/<run_id>-gate0.json`. Human capacity: [PA].
1. Ingest: ad_copy 80–100 raw records, campaign_metadata 100, industry_briefs ≥ 50; every endpoint answered or is named as unavailable. Test: `python3 -c "import json,glob;[print(f,json.load(open(f))['record_count']) for f in glob.glob('data/raw/*/*.json')]"`. Human capacity: [IJ].
2. GIGO: ≥ 25 verified records per source; reject rate ≤ 20% per source; ad_copy ≥ 80% complete; every reject has a reason. Test: `head -20 data/verified/README.md && ls data/raw/rejected/*/`. Human capacity: [IJ].
3. AI output review: every reviewed ad has one decision, an owner and a reason; quoted evidence is found in the ad; character counts within ±2 of the real length; no placeholder text approved; block rate ≤ 50%; batch not 100% approved. Test: `python3 -c "import json,glob;d=json.load(open(sorted(glob.glob('logs/*-decisions.json'))[-1]));print(sum(1 for r in d['results'] if r['problems']),'flagged')"`. Human capacity: [TO].
4. Report exceptions: report totals reconcile with the routing results (ship + fix + do-not-publish + sent-back + errored = checked); no ad appears twice; fallback or flagged verdicts are listed under "Needs a manual check". Test: `grep -c "^## " logs/reports/madison-ad-handoff-<run_id>.md` (= 9 sections) and Gate 4 reconciliation check. Human capacity: [EI].
PF. Pipeline failure: any step raising an error, missing credentials, or the AI answering for no ad. Test: run log `status: stopped` with `stop_conditions` set; `test -f logs/gate-decisions/<run_id>-gatePF.json`. Human capacity: [PF].

## Steps

--- LAYER 1: EXTERNAL SOURCES → data/raw/ ---

Step 1.1  Ad copy library. Labor: AI.
  Action:  Fetch the first 100 rows from the HuggingFace datasets-server rows API (no key). Save exactly as received inside a fetch envelope.
  Script called: `scripts/ingest/madison-ad-handoff-ingest-sources.py`
  Input: Inputs table row 1.
  Output: `data/raw/ad_copy/ad_copy-<run_id>.json`: {source, mode, fetched_at, endpoints[{endpoint, http_status, ok, error}], status, record_count, records[{product, description, ad, _row_idx}]}
  TODO:    RESOLVED: public endpoint, no credential; verified live on 2026-10-18 (100 rows).

Step 1.2  Campaign context. Labor: AI.
  Action:  Same API, campaign dataset, first 100 rows.
  Script called: same script.
  Output: `data/raw/campaign_metadata/campaign_metadata-<run_id>.json`: records[{Campaign_ID, Company, Campaign_Type, Target_Audience, Customer_Segment, Channel_Used, Conversion_Rate, ROI, Engagement_Score, Date, ...}]
  TODO:    RESOLVED: verified live on 2026-10-18 (100 rows).

Step 1.3  Market context. Labor: AI.
  Action:  Fetch 4 RSS feeds; parse every `<item>`; one failed feed is logged and skipped.
  Script called: same script.
  Output: `data/raw/industry_briefs/industry_briefs-<run_id>.json`: records[{feed, title, link, pubDate, description, categories[]}]
  TODO:    [TODO: DATA SOURCE] MarTech refuses the connection from macOS's built-in Python 3.9 (old TLS: `TLSV1_ALERT_PROTOCOL_VERSION`). Run with Homebrew/python.org Python 3.11+ to include it, or accept 3 feeds. Blocks nothing (context only).

PHASE GATE 1 | Judgment type: [IJ] Ingest Judgment
  Good looks like: All three sources answered, or the log names the one that did not; ads 80–100, campaigns 100, articles 50 or more; text arrives as words, not HTML error pages. (Conductor Brief Part 4, G1)
  Bad looks like:  A source returns an error page, 0 records or less than half its usual count, columns are missing, or text arrives as raw HTML. (Part 5, X1)
  Response:        Log and continue for a market-context feed; Flag for review if a count is out of range; Hard stop if the ad copy source is missing.

--- LAYER 2: data/raw/ → data/verified/ ---

Step 2.1  Validate ad copy. Labor: AI with Human gate.
  Action:  Split each ad into headline (first sentence), body and call-to-action (closing sentence with an action verb); strip HTML and hashtags. Reject if headline < 3 words, no product, body < 8 words, or duplicate product. Tag (keep) `missing_cta` and `placeholder_text`.
  Script called: `scripts/gigo/madison-ad-handoff-validate-records.py`
  Output: `data/verified/ad_copy/ad_copy.json|csv`: {record_id, product, headline, body, cta, hashtags, flags[], source, dataset_date}
  Rejects: `data/raw/rejected/ad_copy/rejects-<run_id>.json` with {raw_index, reason, record}

Step 2.2  Validate campaign context. Labor: AI with Human gate.
  Action:  Reject if no company, channel not one of the 6 known, no audience, conversion rate or ROI not numeric, missing/invalid/future date, or duplicate campaign ID. Derive campaign_type from channel (the dataset assigns it at random).
  Output: `data/verified/campaign_metadata/campaign_metadata.json|csv`: {record_id, company, channel, campaign_type, audience, conversion_rate, roi, engagement_score, date, source_campaign_type}
  Rejects: `data/raw/rejected/campaign_metadata/rejects-<run_id>.json`

Step 2.3  Validate market context. Labor: AI with Human gate.
  Action:  Decode HTML entities, strip tags and "The post … appeared first on" footers. Reject if no title, no http(s) URL, invalid date, older than 90 days, summary < 20 words, or duplicate URL. Truncate summaries at 600 characters.
  Output: `data/verified/industry_briefs/industry_briefs.json|csv`: {record_id, feed, title, url, date, summary, categories}
  Rejects: `data/raw/rejected/industry_briefs/rejects-<run_id>.json`
  Also writes: `data/verified/README.md` (record counts, update date, gate applied, rejects by reason).

PHASE GATE 2 | Judgment type: [IJ] Ingest Judgment
  Good looks like: At least 80% of records complete, 0 duplicates, 100% valid past YYYY-MM-DD dates, at least 25 verified records per source, every rejected record has a logged reason. (Part 4, G2)
  Bad looks like:  More than 20% of a source fails the gate, a source has fewer than 25 verified records, or a duplicate or future-dated record reaches data/verified. (Part 5, X2)
  Response:        Flag for review if a reject rate exceeds 20% (the upstream writer is probably broken); Hard stop if any source has fewer than 25 verified records.

--- LAYER 3: TOOL / AI PROCESSING ---

Step 3.1  Route ads with the Routing Agent. Labor: AI with Human gate.
  Action:  Build N variant events (default 20): verified ad + a client campaign + a news article as optional context. An ad tagged `missing_cta` is sent with `popper_pass=false` so the Gatekeeper sends it back. POST each event in `dry_run` mode to the n8n Routing Agent (5 at a time); it returns decision, priority, owner_team, channel_fit {score, note}, risk_flags [{type, severity, evidence}], rationale, suggested_fix, hubspot_task, slack_message, confidence.
  Model:   Claude Haiku 4.5 (`claude-haiku-4-5`) behind the A4 n8n workflow, with strict JSON schema output. Chosen for cost and speed at batch scale: about $0.0045 and about 7 s per ad, 0 failures in 834 A4 load-test requests. The workflow falls back to deterministic rules if the model is unavailable.
  Script called: `scripts/tools/madison-ad-handoff-route-ads.py`
  Output: `logs/madison-ad-handoff-<run_id>-decisions.json`: results[{event_id, ad_id, campaign_id, company, channel, headline, cta, http_status, status, ai_status, kind, seconds, cost_usd, decision{...}, problems[], error}]

Step 3.2  Re-check every AI answer. Labor: AI.
  Action:  For each verdict: quoted evidence must appear in the ad text; character counts in the channel note must be within ±2 of the real headline length; an `auto_approve` on an ad containing placeholder text is a HARD problem; the owner must match the channel's team (unless blocked).
  Output: `problems[]` per result, in the same decisions file.

PHASE GATE 3 | Judgment type: [TO] Tool Output Review
  Good looks like: Every ad gets exactly one decision, an owner that matches its channel and a plain-English reason; quoted evidence appears in the ad; character counts are right; the batch is neither all blocked nor all approved. (Part 4, G3)
  Bad looks like:  Invented evidence, wrong character counts, placeholder text approved, broken or refused output, or more than 50% of the batch blocked. (Part 5, X3)
  Response:        Hard stop if placeholder text was approved; Flag for review for any other failed check (the human reads the flagged items before the report goes out); Log and continue for verdicts the workflow routed by fallback rules (labelled in the report).

--- LAYER 4: logs/reports/ → USER ---

Step 4.1  Produce the handoff report. Labor: AI with Human gate.
  Action:  Write a Markdown report for the marketing-ops lead from the decisions file, validation results and gate decisions.
  Script called: `scripts/tools/madison-ad-handoff-produce-report.py`
  Output:  `logs/reports/madison-ad-handoff-<run_id>.md`, sections: What this batch means · Team queues · Ready to ship · Fix before it ships · Do not publish · Sent back before review · Needs a manual check · Data used · Phase-gate decisions.
  Reader:  Agency marketing-ops lead (secondary: each channel team lead).
  Decision enabled: what ships today, what each team must fix and by when, which verdicts to check by hand, and whether to stop a broken content source upstream.

PHASE GATE 4 | Judgment type: [EI] Exception Intervention
  Good looks like: The report opens with what the batch means, shows each team's queue with the fix inside, and every number reconciles with the run log. (Part 4, G4)
  Bad looks like:  Report counts do not match the run log, an ad appears twice, or fallback-routed ads are not labelled as needing a manual check. (Part 5, X4)
  Response:        Hard stop on a count mismatch or a duplicate; Flag for review when any verdict is listed under "Needs a manual check" (the human resolves those exceptions before forwarding the report).

## Output Contract

### Agent output
File: `logs/madison-ad-handoff-<run_id>.json` (run_id = UTC `YYYYMMDD-HHMMSS`)
Fields: workflow, run_id, mode, started_at, finished_at, status, steps_completed, ingest{source: path, count, endpoints, status}, validation{source: raw, verified, rejected, tagged, reject_reasons, complete_pct, reject_rate_pct}, routing{count, mode, decisions_file}, report{path, totals}, gate_decisions[], stop_conditions.
Per-ad detail: `logs/madison-ad-handoff-<run_id>-decisions.json`. Gate records: `logs/gate-decisions/<run_id>-gate<N>.json`.

### Human report
File: `logs/reports/madison-ad-handoff-<run_id>.md`
Reader: agency marketing-ops lead
Decision enabled: what ships today, who fixes what by when, which verdicts need a manual check, whether to stop a broken upstream writer
Sections: What this batch means; Team queues (team, ads, due); Ready to ship (ad, client, channel, owner); Fix before it ships (headline, client · channel · owner · due, problems with quoted evidence, fix); Do not publish (same); Sent back before review; Needs a manual check; Data used (source, received, verified, rejected, main reason); Phase-gate decisions (gate, judgment, recipe response, decision, note).

## Stop Conditions
- Stop if the ad copy source returns 0 records: with no creative there is nothing to judge, and a report built on the other sources would mislead.
- Stop if any source has fewer than 25 verified records: the batch is too thin to trust the pairing of ads with campaigns.
- Stop if the AI approved an ad that still contains placeholder text (`[website]`, `bit.ly/…`, `TBD`): that ad would embarrass the client if published.
- Stop if the AI answered for no ad at all (service down or credentials wrong): routing every ad by fallback rules for a whole batch defeats the purpose; a human decides whether to wait or re-run.
- Stop if the report's totals do not reconcile with the routing results or an ad appears twice: a manager must never act on wrong numbers.
- Stop (Gate 0) if the run would write to HubSpot/Slack or route more than 50 ads without an explicit decision.

--- CONDUCTOR NOTE ---
The campaign dataset is synthetic: it assigns campaign types and audiences at random, so when the AI flags an "audience mismatch" on an otherwise clean ad (fashion copy for a "Tech Enthusiasts" segment), check the pairing before blaming the copy. Treat a sudden jump in the block rate as a data or prompt problem, not a sudden drop in ad quality: the first version of the routing prompt blocked 71–84% of valid ads because it read unrelated news as a mismatch. RSS feeds are published by third parties; one disappearing (or refusing old TLS versions) is normal and only removes optional context. Character-count checks are tolerant (±2) because the model sometimes counts emoji or punctuation differently. Finally, every check in this recipe is about the copy and the channel; the tool cannot know a client's legal or brand constraints, so "Ready to ship" means "passes channel rules", not "approved by the client".

--- OPEN TODOs ---
  TODO: DATA SOURCE   MarTech feed fails on macOS system Python 3.9 (TLS). Run with Python 3.11+ or accept 3 feeds. Not blocking; context only.
  TODO: DATA SOURCE   Live ads from the 6A interface are not yet stored as a batch source; today the batch is built from the verified ad library. Blocking only real-client use.
  TODO: DEFINE        "Raise priority when market context is timely": the prompt allows it, but no rule defines "timely" (topic match? recency?). Blocks a measurable check of priority bumps at Gate 3.
  TODO: DEV           Idempotency is check-then-insert, so two identical ads arriving in the same second are both processed (seen 27/27 in A4 concurrency tests). Needs a unique constraint or Redis SETNX in the action log.
  TODO: DEV           Placeholder text is caught by the AI and the Gate 3 re-check, not by the Gatekeeper (Conductor Brief X2 says it should be rejected before AI runs). Move the regex into the n8n Gatekeeper.
  TODO: APPROVE       Live mode (create real HubSpot tasks + Slack alerts) is disabled in this recipe (`mode: dry_run`). Enabling it needs explicit sign-off at Gate 0 and a rotated webhook key.
  TODO: APPROVE       Forwarding the report to channel team leads automatically (Slack digest / Gmail) after Gate 4: today the lead forwards it by hand.
  TODO: REPORT FIELD  "Due" is shown relative to the run ("within 3 days"). Decide whether channel teams need an absolute date in the agency's time zone before the report is forwarded to them.
  RESOLVED            DEFINE batch size → 20 ads per run (≤ 50 without re-approval; about $0.10 per run).
  RESOLVED            DEFINE article freshness → 90 days. RESOLVED DEFINE ad completeness → ≥ 80% with CTA.
  RESOLVED            APPROVE credentials → webhook URL and key read from env vars only; never written to files.

## Snickerdoodle

### Run Commands
Full dialogic run: `snickerdoodle run madison-ad-handoff --mode dialogic`
Sample mode (no live network calls, no writes): `snickerdoodle run madison-ad-handoff --mode dialogic --sample`
Local equivalent used for this submission: `python3 scripts/run_pipeline.py` (`--sample`, `--n 20`, `--yes`)

### Step Commands

| Step | CLI Command | Flags |
|---|---|---|
| Ingest sources (1.1–1.3) | `snickerdoodle run madison-ad-handoff --step ingest-sources` | `--sample` |
| Validate records (2.1–2.3) | `snickerdoodle run madison-ad-handoff --step validate-records` | `--sample` |
| Route ads (3.1–3.2) | `snickerdoodle run madison-ad-handoff --step route-ads` | `--sample` `--no-write` |
| Produce report (4.1) | `snickerdoodle run madison-ad-handoff --step produce-report` | `--sample` `--no-write` |

### Gate Commands

| Gate | CLI Command |
|---|---|
| Gate 0 — Run approval [PA] | `snickerdoodle gate madison-ad-handoff --gate 0 --decision approve --note "dry run, 20 ads"` |
| Gate 1 — Ingest [IJ] | `snickerdoodle gate madison-ad-handoff --gate 1 --decision approve --note "sources checked"` |
| Gate 2 — GIGO [IJ] | `snickerdoodle gate madison-ad-handoff --gate 2 --decision approve --note "verified ≥25 per source"` |
| Gate 3 — AI output [TO] | `snickerdoodle gate madison-ad-handoff --gate 3 --decision approve --note "flagged items read"` |
| Gate 4 — Report exceptions [EI] | `snickerdoodle gate madison-ad-handoff --gate 4 --decision approve --note "exceptions resolved"` |
| Pipeline failure [PF] | `snickerdoodle gate madison-ad-handoff --gate PF --decision stop --note "..."` |

### Script Locations

| Step | Script Path | Layer |
|---|---|---|
| Ingest sources | `scripts/ingest/madison-ad-handoff-ingest-sources.py` | ingest |
| Validate records | `scripts/gigo/madison-ad-handoff-validate-records.py` | gigo |
| Route ads | `scripts/tools/madison-ad-handoff-route-ads.py` | tool |
| Produce report | `scripts/tools/madison-ad-handoff-produce-report.py` | tool |
| Conductor | `scripts/run_pipeline.py` | conductor |

### Output Locations

| Output | Path | Format |
|---|---|---|
| Raw ingest | `data/raw/<source>/` | JSON |
| Rejected records | `data/raw/rejected/<source>/` | JSON |
| Verified data | `data/verified/<source>/` + `data/verified/README.md` | JSON + CSV, Markdown |
| Agent log | `logs/madison-ad-handoff-<run_id>.json` | JSON |
| Per-ad decisions | `logs/madison-ad-handoff-<run_id>-decisions.json` | JSON |
| Human report | `logs/reports/madison-ad-handoff-<run_id>.md` | Markdown |
| Gate decisions | `logs/gate-decisions/` | JSON |

## Provenance
Routing Agent: Assignment 4 n8n workflow `Assignment_4/workflow_v2.json` ("Madison Action Layer v2 – Gatekeeper → Routing → Execution"). Data sources and quality standards: Assignment 3 (`Assignment_3/madison_a3_records.csv`) and Conductor Brief Part 3 (`Assignment_5/Bhadrasen_Mayank_A5_ConductorBrief.pdf`). Config: `brand_config.json` (fields mapped one-to-one from the Conductor Brief).
