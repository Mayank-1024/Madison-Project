"""Builds output_gallery.pdf and demo_walkthrough.pdf from screenshots/ (annotated, Chrome headless)."""
import base64, html, pathlib, subprocess
ROOT = pathlib.Path(__file__).resolve().parent.parent
SS = ROOT / "screenshots"
e = html.escape
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
img = lambda n: "data:image/png;base64," + base64.b64encode((SS / f"{n}.png").read_bytes()).decode()

CSS = """@page { size: 11in 8.5in; margin: 0.4in 0.5in; }
:root { --ink:#14213d; --muted:#6b7280; --accent:#0f766e; --hl:#f97316; --line:#e3e6ec; }
* { box-sizing:border-box; } body { margin:0; font-family:-apple-system,"Helvetica Neue",Arial,sans-serif; color:#2b2f38; font-size:9.6pt; background:#fff; }
section { break-after:page; height:7.65in; display:flex; flex-direction:column; } section:last-child { break-after:auto; }
.k { color:var(--accent); font-weight:700; font-size:8pt; letter-spacing:.12em; text-transform:uppercase; }
h1 { color:var(--ink); font-size:30pt; margin:10px 0 8px; } h2 { color:var(--ink); font-size:15pt; margin:2px 0 3px; }
.sub { color:var(--muted); margin:0 0 8px; }
.row { flex:1; min-height:0; display:flex; gap:16px; }
.frame { flex:1; min-width:0; display:flex; justify-content:center; align-items:flex-start; }
.shot { position:relative; display:inline-block; border-radius:6px; box-shadow:0 0 0 1px #d4d8e0,0 4px 14px rgba(20,33,61,.16); }
.shot img { display:block; max-width:100%; max-height:5.35in; border-radius:6px; }
.box { position:absolute; border:2.5px solid var(--hl); border-radius:5px; background:rgba(249,115,22,.07); }
.box span, .notes span { display:inline-flex; align-items:center; justify-content:center; width:20px; height:20px; border-radius:50%; background:var(--hl); color:#fff; font-weight:700; font-size:9pt; }
.box span { position:absolute; left:-11px; top:-11px; box-shadow:0 0 0 2px #fff; }
.notes { list-style:none; padding:0; margin:10px 0 0; display:grid; grid-template-columns:1fr 1fr; gap:5px 22px; }
.notes li { display:flex; gap:8px; align-items:flex-start; line-height:1.35; } .notes span { flex:none; }
.card { width:3.05in; flex:none; border:1px solid var(--line); border-left:4px solid var(--accent); border-radius:6px; padding:10px 12px; align-self:flex-start; font-size:9.2pt; line-height:1.4; }
.card b { color:var(--ink); display:block; margin-top:7px; font-size:8.4pt; text-transform:uppercase; letter-spacing:.06em; } .card b:first-child { margin-top:0; }
.ok { color:#0f766e; font-weight:600; } .warn { color:#b45309; font-weight:600; }
.cover { justify-content:center; } .idx { display:grid; grid-template-columns:1fr 1fr; gap:4px 30px; max-width:9.5in; font-size:9.6pt; margin-top:14px; }
.idx div { border-bottom:1px dotted var(--line); padding:3px 0; } .idx b { color:var(--accent); margin-right:8px; }
.meta { margin-top:22px; border-top:1px solid var(--line); padding-top:10px; display:flex; gap:36px; font-size:9.2pt; } .meta b { color:var(--ink); }
table { border-collapse:collapse; width:100%; font-size:9.4pt; } td,th { text-align:left; padding:6px 8px; border-bottom:1px solid var(--line); vertical-align:top; }
th { background:var(--ink); color:#fff; font-size:8.6pt; } .two { display:grid; grid-template-columns:1fr 1fr; gap:22px; }
.panel { border:1px solid var(--line); border-radius:6px; padding:10px 14px; } .panel h3 { margin:0 0 6px; color:var(--ink); font-size:11pt; }
.panel ol, .panel ul { margin:0; padding-left:18px; } .panel li { margin:3px 0; line-height:1.38; }"""

def page(title, sections):
    return f"<!doctype html><html><head><meta charset='utf-8'><title>{e(title)}</title><style>{CSS}</style></head><body>{''.join(sections)}</body></html>"

def shot(n, boxes=()):
    b = "".join(f'<div class="box" style="left:{x}%;top:{y}%;width:{w}%;height:{h}%"><span>{i}</span></div>' for i, (x, y, w, h) in enumerate(boxes, 1))
    return f'<div class="frame"><div class="shot"><img src="{img(n)}">{b}</div></div>'

def render(html_str, name):
    p = ROOT / "_build" / f"{name}.html"; p.write_text(html_str, encoding="utf-8")
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={ROOT / (name + '.pdf')}", p.as_uri()], check=True, capture_output=True)
    print("wrote", name + ".pdf")

# ------------------------------------------------------------------ output gallery
G = [
 (1, "Urgent alert: auto-approved, ship today", "Slack · #campaign-urgent (Madison Project workspace)", "Bolero Jacket + Choker necklace variants, both auto-approved; HubSpot task IDs, confidence and event IDs in the footer.", "ok", "Works. Message shows the decision, owner, channel-fit score, risks and fix in one glance. Note: these show 🔶 HIGH in #campaign-urgent — the prompt routed by 'strong performance'; the channel rule and priority label can disagree by one level."),
 (2, "Review alert with evidence + rewrite", "Slack · #campaign-review", "Chunky Knit Sweater for Google Ads: headline 53/30 chars, 'unbeatable' flagged with the exact words, rewritten headline that fits.", "ok", "Works — the most useful output: a reviewer sees why and the suggested fix without opening any tool."),
 (3, "Normal-priority approvals", "Slack · #campaign-digest", "Wide-Leg Trousers (Facebook) and Racerback Tank (email) — no risks, optional polish suggested.", "ok", "Works. Low-noise channel for routine approvals, so #urgent stays meaningful."),
 (4, "Run-report digest", "Slack · #campaign-digest (posted by Madison Bot)", "Batch v2-50 summary: 50 processed, 16 auto-approved, 34 to humans, AI cost $0.1556, top risks, busiest teams, top recommendation from the Insights Agent.", "ok", "Works. One message a manager can read in 10 seconds."),
 (5, "HubSpot tasks created by the agent", "HubSpot CRM · Tasks (free account)", "Dozens of tasks with imperative titles ('Publish Instagram variant…', 'Block & investigate…'), due dates set from priority.", "warn", "Works. Older tasks from the v1 prompt ('Block…') are still listed; the v2 batch is the 'Publish…' group. Tasks are not yet assigned to owners (no HubSpot users in a free test account)."),
 (6, "One HubSpot task, opened", "HubSpot · task preview", "Priority High, due date, and notes containing what to do, why, the suggested fix and the Madison event ID for traceability.", "warn", "Works. This example is from the first (v1) smoke test — it shows the brief-mismatch block that the v2 prompt fixed."),
 (7, "Run report email — headline + KPIs", "Gmail (Email Report node, HTML)", "Subject 'Madison run report — v2-50: 50 variants, 16 auto-approved', KPI boxes and the AI headline.", "warn", "Works when re-run; this capture shows the email node's input. The To field shows 'undefined' in a single-step test because Report Settings wasn't executed in that run — runs fine from the trigger."),
 (8, "Run report — AI patterns & recommendations", "Gmail / Insights Agent output", "3 number-backed patterns, 3 prompt/process recommendations (e.g. CTA rubric, platform format rules) and a 3-item watchlist.", "ok", "Works. This is the 'analysing patterns → recommendations' intelligence, grounded in the batch numbers."),
 (9, "Shared decision log", "Google Sheets · 'Madison Action Log'", "49 rows for run v2-50: decision, priority, owner, routed_by, risk count, reason, HubSpot task ID, Slack posted, latency, cost.", "warn", "Works. A non-technical person can filter it. Visible flaw: evt_v2-50_0026 appears twice — the concurrent-duplicate race documented in scale_test_results.md."),
 (10, "System of record: n8n Data Table", "n8n · Data tables · madison_action_log", "Every outcome with its idempotency key, mode, status, decision, owner, Slack channel, AI status.", "ok", "Works. Source for the reports and the duplicate check."),
 (11, "Duplicate blocked (idempotency)", "Terminal · loadtest.py → production webhook", "Re-sending an already-processed event returns status 'duplicate' in 0.19 s with $0 AI cost and no new task/alert.", "ok", "Works for sequential repeats; concurrent repeats are the known gap."),
 (12, "Load test: 400 requests, 100 concurrent", "Terminal · results/v2-400.json", "400 requests in 71.8 s (334/min), 0 failures, 140 blocked by Gatekeeper, 260 routed by Claude, $1.17 total.", "ok", "Works. Latency rose to p50 16.3 s — the saturation point of the 1-vCPU VPS."),
 (13, "Executions burst + full canvas", "n8n · Executions", "The run history during a load test (each event = one execution, 1–10 s) and the workflow's four sections.", "ok", "Works. Every execution 'Succeeded'."),
 (17, "AI outage handled: fallback alert", "Slack · #campaign-review (live failure test fallback-1)", "With Claude deliberately unreachable (invalid model ID), the fallback router still routed the variant: ⚠️ AI router unavailable, rule-based risk flag, owner, HubSpot task — marked 'Routed by fallback rules · confidence 0'.", "ok", "Works. Live proof of error handling: no crash, no lost event, HTTP 200 in 11.8 s, $0 AI cost."),
]
secs = [f"""<section class="cover"><div class="k">INFO7375 · Assignment 4 · Output gallery</div><h1>14 real outputs</h1>
<p class="sub" style="font-size:12pt;max-width:8in">Everything below was produced by the Madison Action Layer v2 workflow (n8n + Claude Haiku 4.5) on 2026-10-09 — real Slack messages, HubSpot tasks, a Google Sheet, an emailed report and load-test evidence. No mock-ups.</p>
<div class="idx">{''.join(f'<div><b>{i}</b>{e(t_)}</div>' for i, (_, t_, *_r) in enumerate(G, 1))}</div>
<div class="meta"><div><b>Author</b> Mayank Bhadrasen</div><div><b>Workflow</b> workflow_v2.json</div><div><b>Files</b> outputs/ (HTML + PDF report, Sheet CSV)</div></div></section>"""]
for i, (n, title, where, what, q, check) in enumerate(G, 1):
    secs.append(f"""<section><div class="k">Example {i} of {len(G)}</div><h2>{e(title)}</h2><div class="row">{shot(n)}
<div class="card"><b>What was produced</b>{e(what)}<b>Where it went</b>{e(where)}<b>Screenshot / file</b>screenshots/{n}.png<b>Quality check</b><span class="{q}">{'✓' if q == 'ok' else '⚠'}</span> {e(check)}</div></div></section>""")
render(page("Bhadrasen_Mayank_A4_Output_Gallery", secs), "output_gallery")

# ------------------------------------------------------------------ demo walkthrough
W = [
 (14, "The workflow: four agents in one n8n canvas", "One webhook in, real actions out. Each event only runs the branch it needs — blocked, duplicate and fallback branches stay grey.",
  [((16.8, 19.8, 22.5, 35.8), "① Gatekeeper (no AI): schema, date and Popper checks + idempotency lookup."),
   ((40.3, 19.8, 22.5, 35.8), "② Routing Agent: Claude Haiku 4.5 with a strict JSON schema, then a validator."),
   ((63.9, 19.8, 29.2, 35.8), "③ Execution Agent: HubSpot task → Slack alert → log → answer Madison."),
   ((16.8, 58.4, 52.6, 24.6), "④ Insights Agent: daily/on-demand batch report → email, Slack, Sheet, HTML.")]),
 (15, "Intelligence: Claude's routing decision", "The Routing Agent receives the variant, the campaign context and market context, and must answer in a fixed schema.",
  [((0.5, 21, 34.5, 9.5), "System prompt: channel limits, severity calibration, decision + priority rules."),
   ((1, 31, 34, 64), "JSON schema with enums — the answer is machine-checkable, not free text."),
   ((58, 30.2, 41.5, 33.5), "Decision: needs_review, owner, channel fit 4/5, two risk flags with evidence, a rewrite."),
   ((58, 70.5, 22, 20.5), "Real usage: 2,199 input + 474 output tokens.")]),
 (16, "Never trust the AI blindly: the validator", "Every answer is checked before anything is sent. Refusals, truncation, bad JSON or invalid values go to a rule-based fallback.",
  [((53.6, 12.6, 9, 3.4), "ai_ok: true — the answer passed every check."),
   ((26, 21, 23.5, 45), "Checks: API error, refusal, max_tokens, JSON parse, enum values, required text."),
   ((53.6, 34.3, 45.5, 21.4), "Risk flags carry the exact evidence and a severity."),
   ((53.6, 85.5, 18, 10.5), "Cost tracked per event: $0.0046, latency 6.7 s.")]),
 (18, "Failing safely: Claude unreachable, work still routed", "Live test fallback-1: model ID set to an invalid value. The path bends through the fallback router instead of stopping.",
  [((9.5, 11, 14.5, 41), "Routing Agent errors (⚠) after 3 retries — but continues."),
   ((70.5, 25, 10, 8), "Validator answers false → branch to fallback."),
   ((55, 62, 20.5, 37), "Rule-based Fallback Router: regex risks + team by channel."),
   ((85, 11, 14, 31), "Plan Actions continues: task + Slack alert still sent.")]),
 (19, "The validator rejects the failed AI answer", "Validate AI Decision receives Claude's API error instead of a decision, marks it invalid and hands the event to the fallback router.",
  [((0.5, 14.5, 34.5, 22.5), "Claude's error arrives as data (model claude-haiku-x not found) after 3 retries."),
   ((69.5, 13.5, 30, 8.5), "ai_ok: false + ai_problem: api_error, so the answer is rejected."),
   ((36.5, 31, 31.5, 46), "Allowed values for decision, priority, owner team and Slack channel are enforced."),
   ((69.5, 32.5, 18, 12.5), "No tokens used: $0 AI cost for this event.")]),
 (17,"…and the team is told the AI was skipped", "The fallback alert in #campaign-review — a human checks it; nothing is lost.",
  [((27.3, 64.2, 47.5, 3.2), "⚠️ AI router unavailable — with the real API error."),
   ((41.3, 70.6, 13.5, 4.6), "Channel fit: not assessed (AI unavailable)."),
   ((27.3, 84.4, 27.5, 2.9), "HubSpot task created · 'Routed by fallback rules' · confidence 0.")]),
 (2, "Output: an alert a busy marketer can act on", "Slack Block Kit message in #campaign-review — decision, owner, channel fit, evidence and the fix, linked to the HubSpot task.",
  [((27.5, 69, 71.5, 8), "Risk flags quote the copy ('Unbeatable comfort')."),
   ((27.5, 78.2, 71.5, 5), "Suggested fix: a headline that fits the 30-char Google Ads limit."),
   ((44.5, 56, 30, 13), "Channel fit 2/5 with the reason (53 chars vs 30)."),
   ((31, 83.4, 28, 2.6), "HubSpot task ID + 'Routed by Claude Haiku 4.5' + confidence.")]),
 (5, "Action: tasks land in the CRM", "Each routed variant becomes a HubSpot task with an imperative title, priority and due date (urgent = today).",
  [((11.3, 15.8, 9, 82), "Imperative task titles written by Claude."),
   ((20.5, 15.8, 3.6, 82), "All created via the HubSpot API — status Not Started."),
   ((73.8, 15.8, 18, 82), "Due date set from priority (today / tomorrow / 3 days).")]),
 (9, "Visibility: the shared decision log", "Google Sheet appended in one batch per report — readable without opening n8n.",
  [((26.5, 12.4, 6.1, 84.5), "Decision mix: auto_approve / needs_review / block."),
   ((51.2, 12.4, 6.2, 84.5), "Routed by Claude (ai) or skipped by the Gatekeeper."),
   ((69.6, 12.4, 6.1, 84.5), "HubSpot task ID — traceable to the CRM."),
   ((81.4, 12.4, 12.4, 84.5), "Latency and cost per decision.")]),
 (12, "Scale: 400 requests, 100 at a time", "Real HTTP load against the production webhook on a 1 vCPU VPS. Full results: scale_test_results.md.",
  [((0.5, 10.8, 45, 11.8), "400 requests · 100 concurrent · 71.8 s · 334/min."),
   ((0.5, 25.8, 40, 20), "Latency p50 16 s / p95 27 s — the saturation point (≤ 50 concurrent: ~9 s)."),
   ((0.5, 47.5, 30, 17), "0 HTTP errors: 260 routed, 140 correctly rejected (422)."),
   ((0.5, 83.2, 55, 10), "Total AI cost $1.17 → $0.0045 per routed event.")]),
 (11, "Reliability: duplicates are not re-processed", "Re-sending an already-processed event is answered from the action log — no AI call, no task, no alert.",
  [((1, 63, 30, 9), "status: duplicate"), ((1, 26.5, 30, 18.5), "0.19 s end to end"), ((1, 80, 42, 9), "AI cost $0")]),
]
secs = [f"""<section class="cover"><div class="k">INFO7375 · Assignment 4 · Demo</div><h1>Screenshot walkthrough</h1>
<p class="sub" style="font-size:12pt;max-width:8in">Madison Action Layer v2: how the AI makes decisions, what it produces, how it fails safely and how far it scales. All screenshots from real runs on 2026-10-09.</p>
<div class="idx">{''.join(f'<div><b>{i}</b>{e(t_)}</div>' for i, (_, t_, *_r) in enumerate(W, 1))}</div>
<div class="meta"><div><b>Author</b> Mayank Bhadrasen</div><div><b>Stack</b> n8n 2.12.3 (self-hosted) + Claude Haiku 4.5</div><div><b>Integrations</b> HubSpot · Slack · Google Sheets · Gmail</div></div></section>"""]
for i, (n, title, cap, notes) in enumerate(W, 1):
    items = "".join(f"<li><span>{j}</span>{e(txt)}</li>" for j, (_, txt) in enumerate(notes, 1))
    secs.append(f"""<section><div class="k">Screenshot {i} of {len(W)}</div><h2>{e(title)}</h2><p class="sub">{e(cap)}</p>
<div class="row">{shot(n, [b_ for b_, _ in notes])}</div><ol class="notes">{items}</ol></section>""")
render(page("Bhadrasen_Mayank_A4_Demo_Walkthrough", secs), "demo_walkthrough")
