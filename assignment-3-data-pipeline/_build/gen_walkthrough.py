"""Builds Bhadrasen_Mayank_A3_Demo_Walkthrough.pdf: annotated n8n screenshots.
Boxes are [left%, top%, width%, height%] of each screenshot. Run from Assignment_3/."""
import pathlib, subprocess, html, base64

ROOT = pathlib.Path(__file__).resolve().parent.parent
SS = ROOT / "screenshots"
e = html.escape

SLIDES = [
    ("Screenshot 2026-10-02 at 2.26.14 PM.png", "Full workflow overview: a successful run",
     "The whole pipeline after the final run. Every node has a green check, and the item counts on each connection show the data flowing through.",
     [([11.6, 4.6, 85.4, 7.6], "Four labelled sections: Collect → Normalize → Quality checks → Save. Each sticky note says what its section does."),
      ([15.6, 13.5, 6.0, 85.0], "Six fetch nodes run in parallel from one trigger: 2 HuggingFace datasets + 4 RSS feeds."),
      ([44.2, 39.0, 15.4, 10.6], "Merge All Sources combines 301 items (records + one status item per source) into the quality step."),
      ([72.0, 29.2, 21.0, 10.4], "285 clean records leave the quality step and are written to CSV; the quality report runs on the branch below.")]),
    ("Screenshot 2026-10-02 at 2.19.30 PM.png", "Key configuration ①: fetching a dataset with no API key",
     "Fetch Ad Copy (HuggingFace) calls the free HuggingFace datasets-server rows API. The query parameters choose the dataset and how many rows to fetch.",
     [([35.6, 14.6, 28.0, 10.4], "Public endpoint with Authentication: None. No credentials are stored in the workflow."),
      ([36.8, 44.8, 27.0, 3.6], "dataset: which HuggingFace dataset to read (the campaign node uses the same pattern)."),
      ([36.8, 95.8, 27.0, 3.6], "length = 100 rows from offset 0, so every run gets the same rows."),
      ([65.0, 8.6, 33.4, 7.8], "n8n confirms the safety settings: always output, auto-retry, and continue on failure."),
      ([65.0, 79.2, 33.8, 18.0], "Live response: each row has product, description and the full ad text.")]),
    ("Screenshot 2026-10-02 at 2.20.52 PM.png", "Key configuration ②: built so a slow source can't crash the run",
     "The Settings tab of the same node. All six fetch nodes use exactly these settings.",
     [([34.4, 18.2, 24.4, 5.6], "Always Output Data: an empty response still produces an item, so the next node can detect it and log it."),
      ([34.4, 33.0, 24.4, 21.4], "Retry On Fail: up to 3 tries, 2 seconds apart, for slow or flaky sources."),
      ([34.4, 55.4, 24.4, 6.4], "On Error → Continue: if all retries fail, the workflow moves on instead of stopping.")]),
    ("Screenshot 2026-10-02 at 2.13.04 PM.png", "Workflow running: a real source outage, handled",
     "A test run on Oct 2 when MarTech's Cloudflare rate-limited the server (HTTP 429). Instead of crashing, the workflow logged it and finished with the other five sources.",
     [([56.4, 25.4, 13.0, 4.4, "r"], "6 sources attempted, 5 available on this run."),
      ([56.4, 30.0, 36.4, 6.6], "The built-in check logs “Source unavailable: RSS: MarTech (martech.org) – Status code 429”."),
      ([56.4, 37.4, 16.0, 16.2], "The run still completed: 285 records collected, 10 duplicates removed, 0 bad dates or empty records."),
      ([56.4, 54.6, 15.0, 6.0], "275 clean records, 94.2% complete, without MarTech. On the final run (next screenshots) all 6 sources were available.")]),
    ("Screenshot 2026-10-02 at 2.23.58 PM.png", "Key configuration ③: the quality step",
     "Quality Checks & Cleaning runs on every record from every source: trims text, converts dates to YYYY-MM-DD, drops records missing title/date/source, removes duplicates and flags incomplete fields.",
     [([28.2, 33.0, 24.4, 19.4], "Required fields per source type decide is_complete. Missing ones are named in quality_flags, never filled in silently."),
      ([28.2, 52.4, 24.4, 13.6], "One fixed 16-column order, so the CSV is identical from row 1 to the last row."),
      ([0.4, 58.6, 27.4, 39.6], "Item counts from every upstream node, so you can trace each source's records through the run."),
      ([53.6, 11.6, 45.4, 57.0], "Output: clean, consistently shaped records ready for the CSV.")]),
    ("Screenshot 2026-10-02 at 2.27.35 PM.png", "Sample output ①: the quality report from the final run",
     "Build Quality Report recalculates every number used in the documentation on each run. Per-source status, counts, completeness and date ranges.",
     [([57.4, 11.8, 24.0, 17.2], "Ad copy: 100 received → 90 kept (the dataset repeats 10 ads with shuffled sentences) → 74 complete (82.2%)."),
      ([57.4, 32.0, 32.0, 17.2], "Campaign metadata: 100/100 complete, dated 2021-01-01 to 2021-04-10."),
      ([57.4, 52.4, 22.0, 17.2], "MarTech recovered on the final run: status ok, 10 articles."),
      ([57.4, 72.6, 22.0, 17.2], "Marketing Dive, like every RSS feed, is reported separately with its own status and date range.")]),
    ("Screenshot 2026-10-02 at 2.30.29 PM.png", "Sample output ②: the final data file",
     "madison_a3_records.csv opened in Numbers: 285 records + header, 16 columns, one consistent schema across all sources.",
     [([2.4, 13.4, 76.4, 2.2, "r"], "Clear, self-explanatory column names. Each one is defined in the Data Dictionary (documentation, section 5)."),
      ([2.4, 15.6, 4.2, 81.4], "Unique record_id; the prefix shows the source (CMP, AD, MT, MD, HS, SME)."),
      ([33.8, 15.6, 17.8, 81.4], "Readable titles built from the raw fields, e.g. “Display campaign by TechCorp on Facebook”."),
      ([79.8, 51.0, 19.6, 6.0], "286 rows (285 records + header) × 16 columns.")]),
]

def slide(i, fn, title, caption, notes):
    # macOS screenshot names contain a narrow no-break space before "PM": match on the timestamp instead
    stamp = fn.split(" at ")[1].split(" ")[0]
    path = next(p for p in SS.glob("*.png") if stamp in p.name)
    img = "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()
    boxes = "".join(
        f'<div class="box{" r" if len(b) > 4 else ""}" style="left:{b[0]}%;top:{b[1]}%;width:{b[2]}%;height:{b[3]}%"><span>{n}</span></div>'
        for n, (b, _) in enumerate(notes, 1))
    items = "".join(f"<li><span>{n}</span>{e(t)}</li>" for n, (_, t) in enumerate(notes, 1))
    return f"""<section><div class="head"><div class="step">Screenshot {i} of {len(SLIDES)}</div><h2>{e(title)}</h2><p>{e(caption)}</p></div>
<div class="frame"><div class="shot"><img src="{img}">{boxes}</div></div><ol class="notes">{items}</ol></section>"""

page = f"""<!doctype html><html><head><meta charset="utf-8"><title>Bhadrasen_Mayank_A3_Demo_Walkthrough</title><style>
@page {{ size: 11in 8.5in; margin: 0.4in 0.5in; }}
:root {{ --ink:#14213d; --muted:#6b7280; --accent:#0f766e; --hl:#f97316; --line:#e3e6ec; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:-apple-system,"SF Pro Text","Helvetica Neue",Arial,sans-serif; color:#2b2f38; font-size:9.4pt; background:#fff; }}
section {{ break-after:page; height:7.65in; display:flex; flex-direction:column; }}
section:last-child {{ break-after:auto; }}
.head h2 {{ margin:2px 0 3px; color:var(--ink); font-size:15pt; }}
.head p {{ margin:0 0 8px; color:var(--muted); }}
.step {{ color:var(--accent); font-weight:700; font-size:8pt; letter-spacing:.12em; text-transform:uppercase; }}
.frame {{ flex:1; min-height:0; display:flex; justify-content:center; align-items:flex-start; }}
.shot {{ position:relative; display:inline-block; border-radius:6px; box-shadow:0 0 0 1px #d4d8e0, 0 4px 14px rgba(20,33,61,.18); }}
.shot img {{ display:block; max-width:10in; max-height:5.05in; border-radius:6px; }}
.box {{ position:absolute; border:2.5px solid var(--hl); border-radius:5px; background:rgba(249,115,22,.08); }}
.box span, .notes span {{ display:inline-flex; align-items:center; justify-content:center; width:20px; height:20px; border-radius:50%; background:var(--hl); color:#fff; font-weight:700; font-size:9pt; }}
.box span {{ position:absolute; left:-11px; top:-11px; box-shadow:0 0 0 2px #fff; }}
.box.r span {{ left:auto; right:-11px; }}
.notes {{ list-style:none; padding:0; margin:10px 0 0; display:grid; grid-template-columns:1fr 1fr; gap:5px 22px; }}
.notes li {{ display:flex; gap:8px; align-items:flex-start; line-height:1.35; }}
.notes li span {{ flex:none; margin-top:-1px; }}
.cover {{ justify-content:center; }}
.cover .k {{ color:var(--accent); font-weight:700; letter-spacing:.14em; font-size:9pt; text-transform:uppercase; }}
.cover h1 {{ color:var(--ink); font-size:30pt; margin:10px 0 8px; }}
.cover p.sub {{ color:var(--muted); font-size:12pt; margin:0 0 26px; max-width:7.5in; }}
.idx {{ display:grid; grid-template-columns:1fr 1fr; gap:6px 30px; max-width:9in; font-size:10pt; }}
.idx div {{ border-bottom:1px dotted var(--line); padding:4px 0; }} .idx b {{ color:var(--accent); margin-right:8px; }}
.legend {{ margin-top:24px; color:var(--muted); font-size:9pt; display:flex; gap:10px; align-items:center; }}
.legend i {{ display:inline-block; width:26px; height:14px; border:2.5px solid var(--hl); border-radius:4px; background:rgba(249,115,22,.08); }}
.meta {{ margin-top:30px; border-top:1px solid var(--line); padding-top:12px; font-size:9.4pt; display:flex; gap:40px; }}
.meta b {{ color:var(--ink); }}
</style></head><body>
<section class="cover"><div class="k">INFO7375 Branding &amp; AI · Assignment 3 · Demo</div>
<h1>Screenshot Walkthrough</h1>
<p class="sub">Madison Automation Agent Data Pipeline: how the n8n workflow is built, how it runs, how it handles a failing source, and what it produces.</p>
<div class="idx">{''.join(f'<div><b>{i}</b>{e(t)}</div>' for i, (_, t, _, _) in enumerate(SLIDES, 1))}</div>
<div class="legend"><i></i> Orange boxes mark key areas; numbers match the notes under each screenshot.</div>
<div class="meta"><div><b>Author</b> Mayank Bhadrasen</div><div><b>Workflow</b> Bhadrasen_Mayank_A3_Workflow.json</div><div><b>n8n</b> 2.12.3 (self-hosted)</div><div><b>Final run</b> 2026-10-02</div></div>
</section>
{''.join(slide(i, *s) for i, s in enumerate(SLIDES, 1))}
</body></html>"""

html_path = ROOT / "_build" / "walkthrough.html"
html_path.write_text(page, encoding="utf-8")
pdf = ROOT / "Bhadrasen_Mayank_A3_Demo_Walkthrough.pdf"
subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--headless", "--disable-gpu",
                "--no-pdf-header-footer", "--allow-file-access-from-files", f"--print-to-pdf={pdf}", html_path.as_uri()],
               check=True, capture_output=True)
print("wrote", pdf)
