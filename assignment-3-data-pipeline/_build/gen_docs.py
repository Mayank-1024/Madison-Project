"""Builds Bhadrasen_Mayank_A3_Documentation.pdf from the workflow's own output files.
Usage: python3 gen_docs.py <quality_report.json> <records.csv> <out_dir>"""
import csv, json, sys, subprocess, html, collections, pathlib

rep_path, csv_path, out_dir = sys.argv[1], sys.argv[2], pathlib.Path(sys.argv[3]).resolve()
rep = json.load(open(rep_path))
rep = rep[0] if isinstance(rep, list) else rep
rows = list(csv.DictReader(open(csv_path, encoding="utf-8-sig")))
e = html.escape

total = len(rows)
complete = sum(1 for r in rows if r["is_complete"].upper() == "TRUE")
rate = round(complete / total * 100, 1)
raw = rep["raw_records_collected"]
removed = rep["removed_breakdown"]
ps = {p["source_name"]: p for p in rep["per_source"]}
run_date = rep["report_generated_at"][:10]

def src(prefix):
    return [p for n, p in ps.items() if n.startswith(prefix)]

ads = ps["HuggingFace: jaykin01/advertisement-copy"]
camp = ps["HuggingFace: federicomoreno/marketing-campaign-performance-200k"]
feeds = src("RSS:")
rss_kept = sum(p["records_kept"] for p in feeds)
rss_recv = sum(p["records_received"] for p in feeds)
rss_done = sum(p["complete_records"] for p in feeds)
rss_dates = sorted(d for p in feeds if p["date_range"] for d in p["date_range"].split(" to "))
flags = rep["quality_flag_counts"]
cols = list(rows[0].keys())

def fill_pct(col):
    return round(sum(1 for r in rows if r[col].strip()) / total * 100, 1)

def status_pill(s):
    return f'<span class="pill {"ok" if s == "ok" else "bad"}">{"Available" if s == "ok" else "Unavailable"}</span>'

per_source_rows = "".join(
    f"<tr><td>{e(p['source_name'])}</td><td>{status_pill(p['status'])}</td><td class=n>{p['records_received']}</td>"
    f"<td class=n>{p['records_kept']}</td><td class=n>{p['complete_records']}</td><td class=n>{p['completeness_pct']}%</td>"
    f"<td style='white-space:nowrap;font-size:8.2pt'>{e(p['date_range'])}</td></tr>" for p in rep["per_source"])

DICT = {
    "record_id": ("Unique ID: prefix shows the source (CMP, AD, MT, MD, HS, SME)", "CMP-0001"),
    "source_name": ("Exact source the record came from", "RSS: Marketing Dive"),
    "source_type": ("campaign_metadata · ad_copy · industry_article", "ad_copy"),
    "title_or_headline": ("Campaign title, ad headline, or article title", "Discover Harem Pants!"),
    "body_text": ("Campaign summary, ad body, or article summary (plain text, ≤ 500 chars)", "Unique, stylish bohemian vibes…"),
    "cta": ("Call to action (ads only)", "Limited stock - shop now!"),
    "brand_or_product": ("Company (campaigns) or product (ads)", "Harem pants"),
    "channel": ("Delivery channel", "Google Ads"),
    "campaign_type": ("Campaign category", "Email"),
    "audience": ("Target audience · customer segment (campaigns)", "Men 18-24 · Health & Wellness"),
    "tags": ("RSS categories or ad hashtags", "B2B marketing; Video marketing"),
    "published_date": ("Date of the record, always YYYY-MM-DD", "2026-09-28"),
    "source_url": ("Link to the article or dataset page", "https://martech.org/…"),
    "collected_at": ("UTC timestamp of the workflow run", "2026-09-29T05:03:46Z"),
    "is_complete": ("TRUE when every required field for that source type is filled", "TRUE"),
    "quality_flags": ("Why a record is incomplete, or notes on how a value was derived", "missing_cta"),
}
dict_rows = "".join(
    f"<tr><td><code>{c}</code></td><td>{e(DICT[c][0])}</td><td class=muted>{e(DICT[c][1])}</td><td class=n>{fill_pct(c)}%</td></tr>"
    for c in cols)

def sample(prefix):
    r = next(r for r in rows if r["record_id"].startswith(prefix))
    keys = ["record_id", "title_or_headline", "body_text", "cta", "brand_or_product", "channel", "campaign_type", "audience", "published_date", "is_complete", "quality_flags"]
    return "".join(f"<tr><th>{k}</th><td>{e(r[k][:180]) or '<span class=muted>—</span>'}</td></tr>" for k in keys)

feed_lines = "".join(f"<li>{e(p['source_name'].replace('RSS: ', ''))}: <b>{p['records_kept']}</b> articles ({e(p['date_range'])})</li>" for p in feeds)
unavailable = rep["unavailable_sources"]
status_line = ("All sources were available on this run." if not unavailable
               else "Unavailable on this run (logged, workflow continued): " + "; ".join(e(u) for u in unavailable))

ERRORS = [
    ("RSS node returns <b>403 Forbidden</b> or <b>429 Too Many Requests</b> (most often MarTech, which sits behind Cloudflare)",
     "Nothing breaks: the node continues on error and the report lists <code>Source unavailable: RSS: MarTech…</code>. Wait 10–15 minutes and re-run. Avoid running the workflow many times in a row."),
    ("HuggingFace HTTP node times out or returns a 5xx error",
     "The node retries 3 times, 2 seconds apart. If it still fails, the source is logged as unavailable. Check <a>https://status.huggingface.co</a> and re-run later."),
    ("<b>Save CSV to Disk</b> shows <i>“The file … is not writable”</i> or <i>ENOENT</i>",
     "n8n 2.x only allows file writes inside <code>~/.n8n-files</code>, and the folder must already exist. Create it (Docker: <code>docker exec -it &lt;n8n-container&gt; mkdir -p /home/node/.n8n-files</code>) or download the file from the <b>Convert to CSV</b> node instead. The run still completes either way."),
    ("Import fails, or nodes show <i>“Install this node to use it”</i>",
     "The workflow was built for n8n <b>2.12.3</b>. Update n8n (<code>npm install -g n8n@latest</code>) and import again."),
    ("<code>n8n start</code> fails with a Node.js version error (local install)",
     "n8n 2.x requires <b>Node.js 22.16 or newer</b>. Check with <code>node -v</code> and install the current LTS from nodejs.org."),
    ("Emoji or “·” look garbled when the CSV is opened in Excel",
     "The file is UTF-8. In Excel use <b>Data → From Text/CSV → File origin: UTF-8</b>, or open it in Google Sheets / Numbers."),
    ("<b>Map RSS Articles</b> shows <i>“Referenced node doesn’t exist”</i>",
     "An RSS node was renamed. The four RSS node names must stay exactly <code>RSS: MarTech</code>, <code>RSS: Marketing Dive</code>, <code>RSS: HubSpot Marketing Blog</code>, <code>RSS: Social Media Examiner</code>."),
]
err_rows = "".join(f"<tr><td>{a}</td><td>{b}</td></tr>" for a, b in ERRORS)

CHECKS = [
    ("Source health", "Every fetch node", "Retries 3× (2 s apart), then <b>continues on error</b>. Map nodes turn a failed or empty response into a <code>Source unavailable: &lt;name&gt;</code> status, written to the quality report."),
    ("Empty-record check", "Quality Checks & Cleaning", "Drops any record with no title, no date or no source. These three fields are present in 100% of output rows."),
    ("Date validation", "Quality Checks & Cleaning", "Parses every date and rejects anything unparseable, before 2000 or in the future. Output is always <code>YYYY-MM-DD</code>."),
    ("Duplicate removal", "Quality Checks & Cleaning", "Articles: same URL. Ads: same product (the dataset repeats ads with shuffled sentences). Campaigns: same campaign ID."),
    ("Text cleaning", "Map nodes + Quality step", "Strips HTML and escaped entities, removes WordPress “The post … appeared first on …” footers, collapses whitespace, trims all fields."),
    ("Completeness flags", "Quality Checks & Cleaning", "Per-source required fields. Missing ones are named in <code>quality_flags</code> (e.g. <code>missing_cta</code>) and <code>is_complete</code> is set to FALSE. Nothing is silently filled in."),
    ("Provenance notes", "Map Ad Copy", "When a value is derived rather than read directly, the record says so: <code>date_from_dataset_release</code>, <code>body_from_product_description</code>."),
    ("Run report", "Build Quality Report", "Recalculates every number in this document on each run: per-source counts, completeness, removal breakdown, flag counts."),
]
check_rows = "".join(f"<tr><td><b>{a}</b></td><td class=muted>{b}</td><td>{c}</td></tr>" for a, b, c in CHECKS)

flag_desc = {
    "date_from_dataset_release": "Ad dataset has no per-row date; the HuggingFace dataset's last-updated date (2023-09-25) is used. Informational, does not make a record incomplete.",
    "missing_cta": "Ad has no recognisable closing call to action. Counted as incomplete.",
    "body_from_product_description": "Ad was only headline + CTA; the dataset's product description is used as the body. Informational.",
}
flag_rows = "".join(f"<tr><td><code>{k}</code></td><td class=n>{v}</td><td>{e(flag_desc.get(k, ''))}</td></tr>" for k, v in flags.items())

page = f"""<!doctype html><html><head><meta charset="utf-8"><title>Bhadrasen_Mayank_A3_Documentation</title>
<style>
@page {{ size: Letter; margin: 0.7in 0.75in; }}
:root {{ --ink:#14213d; --text:#2b2f38; --muted:#6b7280; --line:#e3e6ec; --accent:#0f766e; --accent-soft:#e6f4f2; --warn:#b45309; --bg-soft:#f6f7f9; }}
* {{ box-sizing:border-box; }}
body {{ font-family:-apple-system,"SF Pro Text","Helvetica Neue",Arial,sans-serif; color:var(--text); font-size:9.6pt; line-height:1.45; margin:0; background:#fff; }}
h1,h2,h3 {{ color:var(--ink); line-height:1.2; margin:0; }}
h2 {{ font-size:17pt; margin-bottom:4px; }}
h2 .num {{ color:var(--accent); margin-right:8px; }}
.lead {{ color:var(--muted); margin:0 0 16px; }}
h3 {{ font-size:11pt; margin:14px 0 5px; break-after:avoid; }}
section {{ break-before:page; }}
p {{ margin:6px 0; }}
code {{ font-family:"SF Mono",Menlo,monospace; font-size:8.6pt; background:var(--bg-soft); padding:1px 4px; border-radius:3px; color:#334155; }}
table {{ width:100%; border-collapse:collapse; margin:8px 0 4px; font-size:9pt; break-inside:auto; }}
th,td {{ text-align:left; vertical-align:top; padding:4px 7px; border-bottom:1px solid var(--line); }}
thead th {{ background:var(--ink); color:#fff; font-weight:600; font-size:8.6pt; letter-spacing:.02em; }}
tr {{ break-inside:avoid; }}
td.n, th.n {{ text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }}
.muted {{ color:var(--muted); }}
.pill {{ display:inline-block; padding:1px 8px; border-radius:10px; font-size:8pt; font-weight:600; }}
.pill.ok {{ background:var(--accent-soft); color:var(--accent); }} .pill.bad {{ background:#fdecea; color:#b42318; }}
.cover {{ height:9.4in; display:flex; flex-direction:column; justify-content:space-between; }}
.cover .kicker {{ color:var(--accent); font-weight:700; letter-spacing:.14em; font-size:9pt; text-transform:uppercase; }}
.cover h1 {{ font-size:32pt; margin:14px 0 10px; letter-spacing:-.01em; }}
.cover .sub {{ font-size:13pt; color:var(--muted); max-width:5.6in; }}
.kpis {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-top:34px; }}
.kpi {{ border:1px solid var(--line); border-top:3px solid var(--accent); border-radius:6px; padding:12px 14px; }}
.kpi b {{ display:block; font-size:22pt; color:var(--ink); font-variant-numeric:tabular-nums; }}
.kpi span {{ color:var(--muted); font-size:8.6pt; }}
.meta {{ border-top:1px solid var(--line); padding-top:14px; display:grid; grid-template-columns:1fr 1fr; gap:4px 24px; font-size:9.4pt; }}
.meta b {{ color:var(--ink); }}
.toc {{ margin-top:30px; font-size:9.6pt; columns:2; }}
.toc div {{ padding:3px 0; border-bottom:1px dotted var(--line); }}
.toc span {{ color:var(--accent); font-weight:700; margin-right:6px; }}
.flow {{ display:flex; align-items:stretch; gap:6px; margin:14px 0 6px; }}
.flow .box {{ flex:1; border:1px solid var(--line); border-radius:6px; padding:8px 10px; font-size:8.5pt; background:var(--bg-soft); }}
.flow .box b {{ display:block; color:var(--ink); font-size:9pt; margin-bottom:2px; }}
.flow .box.hl {{ background:var(--accent-soft); border-color:#b7dfd9; }}
.flow .arrow {{ align-self:center; color:var(--accent); font-weight:700; }}
.inv {{ border:1px solid var(--line); border-left:4px solid var(--accent); border-radius:6px; padding:7px 12px; margin:7px 0; font-size:9pt; line-height:1.38; break-inside:avoid; }}
.inv h4 {{ margin:0 0 4px; color:var(--ink); font-size:10.6pt; }}
.inv ul {{ margin:2px 0 0; padding-left:16px; }} .inv li {{ margin:1px 0; }}
.stats {{ background:var(--ink); color:#fff; border-radius:6px; padding:12px 16px; break-inside:avoid; }}
.stats h4 {{ margin:0 0 4px; color:#fff; }} .stats ul {{ margin:0; padding-left:16px; }} .stats b {{ color:#7ee0d3; }}
.callout {{ background:#fff8eb; border:1px solid #f3dfb5; border-radius:6px; padding:9px 12px; font-size:9pt; margin:10px 0; break-inside:avoid; }}
.callout b {{ color:var(--warn); }}
ol.steps {{ padding-left:0; list-style:none; counter-reset:s; margin:6px 0; }}
ol.steps li {{ counter-increment:s; position:relative; padding:4px 0 4px 34px; border-bottom:1px solid var(--line); break-inside:avoid; }}
ol.steps li::before {{ content:counter(s); position:absolute; left:0; top:4px; width:22px; height:22px; border-radius:50%; background:var(--accent); color:#fff; font-weight:700; font-size:8.6pt; display:flex; align-items:center; justify-content:center; }}
.two {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; }}
.sample th {{ width:1.45in; color:var(--muted); font-weight:500; background:var(--bg-soft); font-size:8.4pt; }}
pre {{ background:#0f172a; color:#e2e8f0; border-radius:6px; padding:10px 12px; font-size:8.2pt; line-height:1.45; white-space:pre-wrap; break-inside:avoid; }}
a {{ color:var(--accent); text-decoration:none; }}
</style></head><body>

<div class="cover">
  <div>
    <div class="kicker">INFO7375 Branding &amp; AI · Assignment 3</div>
    <h1>Madison Automation Agent<br>Data Pipeline</h1>
    <div class="sub">An n8n workflow that collects the marketing campaign, ad-copy and industry-brief data the Madison Action Layer needs, then cleans and checks it.</div>
    <div class="kpis">
      <div class="kpi"><b>{total}</b><span>clean records</span></div>
      <div class="kpi"><b>{rate}%</b><span>complete records</span></div>
      <div class="kpi"><b>3</b><span>sources · {len(rep['per_source'])} feeds/datasets</span></div>
      <div class="kpi"><b>100%</b><span>title, date &amp; source present</span></div>
    </div>
    <div class="toc">
      <div><span>1</span>Project &amp; pipeline overview</div><div><span>2</span>Data Inventory</div>
      <div><span>3</span>Quality numbers</div><div><span>4</span>Data quality checks built in</div>
      <div><span>5</span>Data dictionary</div><div><span>6</span>Setup Guide</div>
      <div><span>7</span>Common errors &amp; fixes</div><div><span>8</span>How this feeds Assignment 4</div>
    </div>
  </div>
  <div class="meta">
    <div><b>Author</b> Mayank Bhadrasen · MS Information Systems</div><div><b>Instructor</b> Professor Nina Harris</div>
    <div><b>Workflow</b> Bhadrasen_Mayank_A3_Workflow.json</div><div><b>Data file</b> madison_a3_records.csv</div>
    <div><b>Data collected</b> {run_date} (n8n 2.12.3, self-hosted)</div><div><b>Submitted</b> October 2, 2026</div>
  </div>
</div>

<section>
<h2><span class="num">1</span>Project &amp; pipeline overview</h2>
<p class="lead">The problem from Assignment 2, and how this data helps solve it.</p>
<p><b>Problem.</b> Madison's Content Agent generates and quality-scores ad variants, but its output ends in a CSV file and a Discord message. Nothing reaches a CRM or task tool, so people copy approved content into HubSpot and alert their team by hand. Marketers spend about 10 hours a week (26% of their time) on routine manual work like this (DoubleVerify 2025 Global Insights, 1,970 marketers surveyed).</p>
<p><b>Solution being built.</b> The <b>Madison Automation Agent</b> is an Action Layer with three agents: a <b>Gatekeeper</b> that validates and dedupes Madison's variants, a <b>Routing Agent</b> (Claude) that decides what action to take, and an <b>Execution Agent</b> that creates HubSpot tasks and Slack alerts.</p>
<p><b>What this assignment collects.</b> To test those agents, we need realistic inputs shaped like Madison's output. Each of the three sources supplies one part of that input:</p>
<div class="flow">
  <div class="box"><b>① Ad copy</b>HuggingFace ad dataset. Gives the <i>creative</i>: headline · body · CTA, matching Madison's variant fields.</div>
  <div class="box"><b>② Campaign metadata</b>HuggingFace campaign dataset. Gives the <i>context</i>: channel · campaign type · audience · results.</div>
  <div class="box"><b>③ Industry briefs</b>4 marketing RSS feeds. Give <i>real, dated topics</i> to use as campaign briefs.</div>
  <div class="arrow">→</div>
  <div class="box hl"><b>n8n pipeline</b>Map to one 16-column schema → quality checks → CSV + quality report.</div>
  <div class="arrow">→</div>
  <div class="box hl"><b>Assignment 4</b>Combined into Madison-style payloads to test Gatekeeper → Routing → Execution.</div>
</div>
<h3>Workflow at a glance (19 nodes in 4 labelled sections)</h3>
<table><thead><tr><th style="width:22%">Section</th><th style="width:36%">Nodes</th><th>What it does</th></tr></thead><tbody>
<tr><td><b>① Collect</b></td><td>Start Collection → 2 HTTP Request (HuggingFace) + 4 RSS Read</td><td>Fetches all sources in parallel. Each fetch retries 3× and continues on error.</td></tr>
<tr><td><b>② Normalize</b></td><td>Map Ad Copy · Map Campaigns · Merge RSS Feeds → Map RSS Articles</td><td>Maps each source into the shared schema and records a status for each source (available / unavailable).</td></tr>
<tr><td><b>③ Quality</b></td><td>Merge All Sources → Quality Checks &amp; Cleaning</td><td>Validates, de-duplicates, standardises dates and flags incomplete fields.</td></tr>
<tr><td><b>④ Save</b></td><td>Records to Rows → Convert to CSV → Save CSV · Build Quality Report → Convert to JSON → Save Report</td><td>Writes the clean data file and the quality report.</td></tr>
</tbody></table>
<div class="callout"><b>Collect once, reuse forever.</b> The workflow was run once on {run_date}. The saved CSV is the dataset of record for Assignment 4. Re-running is safe and repeatable (fixed dataset offsets, same schema), but RSS feeds will return newer articles.</div>
</section>

<section>
<h2><span class="num">2</span>Data Inventory</h2>
<p class="lead">In the required template format.</p>
<p><b>## Project:</b> Madison Automation Agent: Action Layer for Madison's Content Agent<br>
<b>## Problem:</b> AI-generated marketing content never reaches the systems where work happens (CRM, task tools, team chat). This data supplies realistic ad variants, campaign context and briefs to build and test an automated handoff.</p>
<h3>### Data Collected</h3>
<div class="inv"><h4>Source 1: HuggingFace: <code>jaykin01/advertisement-copy</code></h4><ul>
<li><b>Type:</b> Product ad copy (product, description, full ad text), split by the workflow into headline · body · CTA</li>
<li><b>Amount:</b> {ads['records_kept']} records ({ads['records_received']} fetched, {ads['records_received'] - ads['records_kept']} duplicates removed)</li>
<li><b>Purpose:</b> Supplies the <i>creative</i> fields Madison produces (<code>headline</code>, <code>body</code>, <code>cta</code>), so Assignment 4 can build realistic variant payloads</li>
<li><b>Collection method:</b> n8n HTTP Request → HuggingFace datasets-server rows API (no key), rows 0–99</li>
<li><b>Quality:</b> {ads['complete_records']}/{ads['records_kept']} complete records ({ads['completeness_pct']}%). Incomplete records have no recognisable CTA and are flagged <code>missing_cta</code></li></ul></div>
<div class="inv"><h4>Source 2: HuggingFace: <code>federicomoreno/marketing-campaign-performance-200k</code></h4><ul>
<li><b>Type:</b> Structured campaign records: company, campaign type, channel, audience, segment, date, conversion rate, ROI, clicks, impressions</li>
<li><b>Amount:</b> {camp['records_kept']} records ({camp['date_range']})</li>
<li><b>Purpose:</b> Supplies the <i>campaign context</i> the Routing Agent uses to decide actions and owners (channel, type, audience)</li>
<li><b>Collection method:</b> n8n HTTP Request → HuggingFace datasets-server rows API (no key), rows 0–99 (mirror of a public Kaggle campaign dataset)</li>
<li><b>Quality:</b> {camp['complete_records']}/{camp['records_kept']} complete records ({camp['completeness_pct']}%)</li></ul></div>
<div class="inv"><h4>Source 3: Marketing industry RSS feeds (4 feeds)</h4><ul>
<li><b>Type:</b> Current marketing and martech news articles: title, summary, categories, date, URL</li>
<li><b>Amount:</b> {rss_kept} records ({rss_dates[0] if rss_dates else ''} to {rss_dates[-1] if rss_dates else ''})<ul>{feed_lines}</ul></li>
<li><b>Purpose:</b> Real, dated marketing topics used as campaign briefs and as context for routing decisions</li>
<li><b>Collection method:</b> n8n RSS Read node, one per feed, merged, then mapped</li>
<li><b>Quality:</b> {rss_done}/{rss_kept} complete records ({round(rss_done / rss_kept * 100, 1) if rss_kept else 0}%)</li></ul></div>
<div class="stats"><h4>### Statistics</h4><ul>
<li><b>Total records:</b> {total} (from {raw} collected; {raw - total} removed: {removed['duplicates']} duplicates, {removed['missing_essentials']} missing essentials, {removed['invalid_date']} invalid dates)</li>
<li><b>Clean records:</b> {complete} fully complete ({rate}% quality rate)</li>
<li><b>Sources:</b> 3 (2 HuggingFace datasets + 4 RSS feeds); {rep['sources_available']}/{rep['sources_attempted']} feeds/datasets available on the collection run</li>
<li><b>Ready for:</b> Assignment 4: combining ad copy + campaign context + briefs into Madison-style payloads to test the Gatekeeper → Routing → Execution agents (see Section 8)</li></ul></div>
</section>

<section>
<h2><span class="num">3</span>Quality numbers</h2>
<p class="lead">Every number below comes from <code>madison_a3_quality_report.json</code>, which the workflow generates on each run.</p>
<table><thead><tr><th>Source</th><th>Status</th><th class=n>Received</th><th class=n>Kept</th><th class=n>Complete</th><th class=n>Complete %</th><th>Date range</th></tr></thead>
<tbody>{per_source_rows}<tr><td><b>Total</b></td><td></td><td class=n><b>{raw}</b></td><td class=n><b>{total}</b></td><td class=n><b>{complete}</b></td><td class=n><b>{rate}%</b></td><td></td></tr></tbody></table>
<p class="muted" style="font-size:8.6pt">{status_line}</p>
<div class="two">
<div><h3>Quality checklist results</h3>
<table><tbody>
<tr><td>Records complete (target ≥ 80%)</td><td class=n><b>{rate}%</b></td></tr>
<tr><td>Title present</td><td class=n>{rep['essentials_check']['title_present_pct']}%</td></tr>
<tr><td>Date present</td><td class=n>{rep['essentials_check']['date_present_pct']}%</td></tr>
<tr><td>Source name + URL present</td><td class=n>{rep['essentials_check']['source_present_pct']}%</td></tr>
<tr><td>Dates in YYYY-MM-DD</td><td class=n>{rep['essentials_check']['dates_in_yyyy_mm_dd_pct']}%</td></tr>
<tr><td>Duplicates remaining</td><td class=n>0</td></tr></tbody></table></div>
<div><h3>Records removed</h3>
<table><tbody>
<tr><td>Duplicates</td><td class=n>{removed['duplicates']}</td></tr>
<tr><td>Missing title / date / source</td><td class=n>{removed['missing_essentials']}</td></tr>
<tr><td>Invalid or implausible date</td><td class=n>{removed['invalid_date']}</td></tr>
<tr><td><b>Total removed</b></td><td class=n><b>{raw - total}</b></td></tr></tbody></table></div>
</div>
<h3>Quality flags on kept records</h3>
<table><thead><tr><th style="width:30%">Flag</th><th class=n style="width:10%">Records</th><th>Meaning</th></tr></thead><tbody>{flag_rows}</tbody></table>
<h3>Known limitations (stated openly)</h3>
<ul>
<li><b>Ad dates:</b> the ad dataset has no per-row date, so all ads use the dataset's release date and are flagged.</li>
<li><b>Campaign data is synthetic</b> (a public practice dataset), which suits testing routing logic but not drawing market conclusions. Neither HuggingFace dataset states a license; both are used for coursework only.</li>
<li><b>RSS summaries</b> come from publishers' feed excerpts, and some end in “[…]” where the publisher truncates them.</li>
</ul>
</section>

<section>
<h2><span class="num">4</span>Data quality checks built in</h2>
<p class="lead">These checks run inside the workflow on every run, not by hand afterwards.</p>
<table><thead><tr><th style="width:20%">Check</th><th style="width:22%">Where</th><th>How it works</th></tr></thead><tbody>{check_rows}</tbody></table>
<h3>Handling a slow or empty source</h3>
<p>Every fetch node is set to <b>Retry on Fail (3 tries, 2 s wait)</b>, <b>On Error → Continue</b> and <b>Always Output Data</b>. If a source still fails or returns nothing, its Map node outputs a status item instead of records, for example:</p>
<pre>{{ "source_name": "RSS: MarTech (martech.org)", "status": "unavailable",
  "message": "Source unavailable: RSS: MarTech (martech.org) – 403 Forbidden", "records_received": 0 }}</pre>
<p>The other sources keep running, and the message appears in <code>unavailable_sources</code> in the quality report. This was tested by simulating a timeout (HuggingFace ads), an empty response (campaigns) and a 403 error (Marketing Dive) in the same run. All three were logged and the run still finished with the remaining data. It also happened for real: during a test run on 2026-10-02, MarTech's Cloudflare returned <b>429 Too Many Requests</b>. The workflow logged <code>Source unavailable: RSS: MarTech (martech.org) – Status code 429</code> and finished with 275 clean records from the other five feeds (Demo walkthrough, screenshot 4).</p>
</section>

<section>
<h2><span class="num">5</span>Data dictionary</h2>
<p class="lead"><code>madison_a3_records.csv</code>: {total} rows × {len(cols)} columns, UTF-8, one row per record. Rows are ordered by source type, newest first. “Filled” is the share of rows with a value; empty values are expected where a field doesn't apply to that source (e.g. CTA for articles).</p>
<table><thead><tr><th style="width:19%">Column</th><th>Meaning</th><th style="width:25%">Example</th><th class=n style="width:9%">Filled</th></tr></thead><tbody>{dict_rows}</tbody></table>
<h3>Required fields per source type (used for <code>is_complete</code>)</h3>
<table><tbody>
<tr><td style="width:24%"><code>ad_copy</code></td><td>title_or_headline, body_text, cta, brand_or_product</td></tr>
<tr><td><code>campaign_metadata</code></td><td>title_or_headline, body_text, channel, campaign_type, audience</td></tr>
<tr><td><code>industry_article</code></td><td>title_or_headline, body_text, source_url</td></tr>
<tr><td><b>All records</b></td><td>source_name, published_date (valid), title_or_headline. Records missing these are removed, not just flagged.</td></tr></tbody></table>
</section>

<section>
<h2><span class="num">6</span>Setup Guide</h2>
<p class="lead">Written so a classmate can reproduce the dataset from scratch, in about 10 minutes.</p>
<h3>What you need first</h3>
<table><tbody>
<tr><td style="width:28%"><b>n8n 2.x</b></td><td>Either self-hosted (this project runs on a Hostinger VPS, n8n 2.12.3) or local: <code>npm install -g n8n</code> (needs <b>Node.js 22.16+</b>)</td></tr>
<tr><td><b>Credentials / API keys</b></td><td><b>None.</b> All sources are public and need no login: the HuggingFace datasets-server API and RSS feeds. The workflow contains no secrets, tokens or webhook URLs.</td></tr>
<tr><td><b>Files</b></td><td><code>Bhadrasen_Mayank_A3_Workflow.json</code></td></tr>
<tr><td><b>Internet access</b></td><td>To <code>datasets-server.huggingface.co</code>, <code>martech.org</code>, <code>marketingdive.com</code>, <code>blog.hubspot.com</code>, <code>socialmediaexaminer.com</code></td></tr>
</tbody></table>
<h3>Run it</h3>
<ol class="steps">
<li><b>Start n8n.</b> Local: run <code>n8n start</code> in a terminal, then open your browser to <code>http://localhost:5678</code>. Self-hosted: open your n8n URL. Create the owner account on first launch.</li>
<li><b>Import the workflow.</b> <i>Overview → Create workflow</i>, then the <b>⋯</b> menu (top right) → <b>Import from File…</b> → choose <code>Bhadrasen_Mayank_A3_Workflow.json</code>. You'll see 19 nodes in four coloured sections.</li>
<li><b>(Optional) enable disk copies.</b> n8n 2.x only writes files inside <code>~/.n8n-files</code>. Create it once: local <code>mkdir -p ~/.n8n-files</code>. Docker/Hostinger: <code>docker exec -it &lt;container&gt; mkdir -p /home/node/.n8n-files</code>. Then change the path in both <b>Save … to Disk</b> nodes to match (local: <code>/Users/&lt;you&gt;/.n8n-files/…</code>). You can skip this step; step 5 works without it.</li>
<li><b>Run.</b> Click <b>Execute workflow</b>. It finishes in about 10–20 seconds and every node turns green. Item counts appear on each connection.</li>
<li><b>Download the outputs.</b> Open <b>Convert to CSV</b> → output panel → <b>Download</b> (<code>madison_a3_records.csv</code>). Do the same on <b>Convert Report to JSON</b> (<code>madison_a3_quality_report.json</code>).</li>
<li><b>Check the run.</b> Open the report and confirm <code>unavailable_sources</code> is empty. If a feed is listed there, see Section 7 and re-run later. The rest of the data is still valid.</li>
</ol>
<h3>Changing what is collected</h3>
<p>Volume: change <code>length</code> (max 100) or <code>offset</code> in the two HuggingFace HTTP nodes' query parameters. Feeds: replace the URL in an RSS node, but keep the node name, or update the <code>FEEDS</code> list at the top of <b>Map RSS Articles</b> to match.</p>
</section>

<section>
<h2><span class="num">7</span>Common errors &amp; fixes</h2>
<p class="lead">Problems seen while building and testing this workflow, and how to resolve them.</p>
<table><thead><tr><th style="width:40%">Symptom</th><th>Fix</th></tr></thead><tbody>{err_rows}</tbody></table>

<h2 style="margin-top:28px"><span class="num">8</span>How this feeds Assignment 4</h2>
<p class="lead">From collected records to test payloads for the Action Layer.</p>
<p>Assignment 4 combines one record from each source into a Madison-style variant event, the exact input schema defined in the Assignment 2 PRD:</p>
<pre>{{ "event_id": "evt_A4_001",            "source_agent": "madison.content_agent",
  "brief_id": "MT-0003",                 // ③ industry brief (RSS record_id)
  "variant_id": "AD-0013",               // ① ad copy
  "headline": "Upgrade your denim game!", "body": "Introducing Zipper-detail Jeans…",
  "cta": "Get yours today, stand out in the crowd.",
  // ② campaign context
  "channel": "Google Ads", "campaign_type": "Email", "audience": "Men 18-24 · Foodies",
  "popper_pass": true, "created_at": "2026-09-28" }}</pre>
<ul>
<li><b>Gatekeeper tests:</b> the {flags.get('missing_cta', 0)} ads flagged <code>missing_cta</code> are natural failing inputs for the PRD metric “0 quality-gate violations in 10 deliberately failing inputs”.</li>
<li><b>Routing tests:</b> channel, campaign type and audience give the Routing Agent (Claude) varied cases for choosing HubSpot task owners and Slack alerts.</li>
<li><b>Field-mapping tests:</b> the consistent 16-column schema supports the PRD metric “0 field-mapping errors in 50 test runs”.</li>
</ul>
<h3>Sample records</h3>
<div class="two"><table class="sample"><tbody>{sample('AD-')}</tbody></table><table class="sample"><tbody>{sample('CMP-')}</tbody></table></div>
</section>
</body></html>"""

out_dir.mkdir(parents=True, exist_ok=True)
html_path = out_dir / "Bhadrasen_Mayank_A3_Documentation.html"
html_path.write_text(page, encoding="utf-8")
pdf_path = out_dir / "Bhadrasen_Mayank_A3_Documentation.pdf"
subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--headless", "--disable-gpu",
                "--no-pdf-header-footer", f"--print-to-pdf={pdf_path}", html_path.as_uri()],
               check=True, capture_output=True)
print("wrote", pdf_path, f"| {total} records, {rate}% complete")
