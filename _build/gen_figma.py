"""Generates the Figma board assets as SVG (Figma imports SVG text as editable text layers).
Outputs: figma/exec_summary.svg, figma/architecture.svg, figma/before_after.svg, figma/scale_chart.svg"""
import pathlib, html
OUT = pathlib.Path(__file__).resolve().parent.parent / "figma"
OUT.mkdir(exist_ok=True)
e = html.escape
INK, TEXT, MUTED, LINE, TEAL, TEAL_SOFT, AMBER, BG, SOFT = "#14213d", "#2b2f38", "#6b7280", "#e3e6ec", "#0f766e", "#e6f4f2", "#d97706", "#ffffff", "#f6f7f9"
PURPLE, PURPLE_SOFT, RED, ORANGE_SOFT = "#6d28d9", "#f1ebfd", "#b42318", "#fff4e5"
FONT = "Inter, Helvetica, Arial, sans-serif"

def svg(w, h, body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="{FONT}"><rect width="{w}" height="{h}" fill="{BG}"/>{body}</svg>'

def t(x, y, s, size=16, color=TEXT, weight=400, anchor="start", ls=None):
    extra = f' letter-spacing="{ls}"' if ls else ""
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}"{extra}>{e(s)}</text>'

def lines(x, y, rows, size=15, color=TEXT, lh=1.45, weight=400):
    return "".join(t(x, y + i * size * lh, r, size, color, weight) for i, r in enumerate(rows))

def box(x, y, w, h, fill=SOFT, stroke=LINE, r=10, sw=1, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>'

def badge(x, y):
    return box(x, y, 300, 40, INK, INK, 20) + t(x + 150, y + 26, "Built with n8n + Claude Haiku 4.5", 15, "#ffffff", 600, "middle")

# ------------------------------------------------------------------ executive summary (1 page)
W, H = 1440, 1024
b = []
b.append(t(64, 72, "MADISON AUTOMATION AGENT · ASSIGNMENT 4", 13, TEAL, 700, ls="2"))
b.append(t(64, 122, "The Action Layer: AI-routed handoff from content to CRM", 38, INK, 700))
b.append(t(64, 156, "Executive summary · Mayank Bhadrasen · INFO7375 Branding & AI · Oct 2026", 15, MUTED))
b.append(badge(1076, 50))
# problem
b.append(box(64, 186, 640, 150, SOFT, LINE))
b.append(t(88, 218, "PROBLEM", 12, TEAL, 700, ls="1.5"))
b.append(lines(88, 248, ["Madison's Content Agent writes quality-checked ad variants, but they", "dead-end in a CSV and a chat ping. Marketers then spend ~10 hours a", "week (26% of their time) on manual handoffs like copying content into", "CRMs and notifying teams (DoubleVerify 2025, 1,970 marketers)."], 15.5))
# solution
b.append(box(736, 186, 640, 150, SOFT, LINE))
b.append(t(760, 218, "SOLUTION APPROACH", 12, TEAL, 700, ls="1.5"))
b.append(lines(760, 248, ["① Gatekeeper — validates, blocks bad payloads, stops duplicates (no AI)",
                          "② Routing Agent (Claude) — channel fit, risk flags, decision, owner, fix",
                          "③ Execution Agent — HubSpot task + Slack alert, retried and logged",
                          "④ Insights Agent (Claude) — batch patterns → email, Slack, Sheet"], 15))
# metrics row
kpis = [("834", "requests in scale tests"), ("0", "failed requests"), ("$0.0044", "AI cost per event"), ("6.4 s", "median live handoff"), ("≈330/min", "ceiling on a 1-vCPU VPS")]
for i, (v, l) in enumerate(kpis):
    x = 64 + i * 265
    b.append(box(x, 372, 248, 108, BG, LINE))
    b.append(f'<rect x="{x}" y="372" width="248" height="4" rx="2" fill="{TEAL}"/>')
    b.append(t(x + 20, 428, v, 32, INK, 700))
    b.append(t(x + 20, 458, l, 14, MUTED))
b.append(t(64, 356, "CURRENT PERFORMANCE (measured 2026-10-09, Claude Haiku 4.5, n8n 2.12.3 on Hostinger KVM 1)", 12, TEAL, 700, ls="1.5"))
# sample outputs
b.append(t(64, 548, "SAMPLE OUTPUTS", 12, TEAL, 700, ls="1.5"))
b.append(box(64, 562, 640, 120, "#1a1d21", "#1a1d21"))
b.append(t(86, 592, "Slack · #campaign-review", 13, "#9ca3af", 600))
b.append(lines(86, 620, ["🟦 NORMAL · 👀 Needs review", "Alpha Innovations email variant needs subject line trim (87→60 chars).", "Copy is strong; fix headline length and we're good to ship."], 14.5, "#f3f4f6"))
b.append(box(64, 696, 640, 120, ORANGE_SOFT, "#f3dfb5"))
b.append(t(86, 726, "Insights Agent · run report v2-50", 13, AMBER, 700))
b.append(lines(86, 754, ["“Channel mismatch was the top risk flag (16 of 50 variants). Embed", "platform-specific format rules into the Content Agent prompt to cut", "channel_mismatch flags from 32% to under 15%.”"], 14.5, TEXT))
# results + value
b.append(t(736, 548, "RESULTS ACHIEVED (50 live variants)", 12, TEAL, 700, ls="1.5"))
res = [("16", "auto-approved → HubSpot task + Slack alert in ~6 s"), ("18", "sent to review with exact risk evidence + rewrite"), ("16", "blocked (15 by Gatekeeper, 1 placeholder by Claude)"), ("35", "HubSpot tasks + 35 Slack alerts, 0 failures")]
for i, (v, l) in enumerate(res):
    y = 562 + i * 64
    b.append(box(736, y, 640, 54, BG, LINE))
    b.append(t(760, y + 36, v, 24, INK, 700))
    b.append(t(812, y + 34, l, 15, TEXT))
b.append(t(64, 862, "BUSINESS VALUE", 12, TEAL, 700, ls="1.5"))
b.append(box(64, 876, 1312, 96, TEAL_SOFT, "#b7dfd9"))
b.append(lines(88, 910, ["50 variants routed for $0.16 of AI replaced ≈3.5 hours of manual handoff (≈$121 at $34.63/h) — a ~750× return per batch.",
                         "At 1,000 variants/day: ≈$95–135/month in Claude costs on the existing VPS; no new SaaS seats (free HubSpot, Slack, Sheets)."], 16, INK, weight=500))
b.append(t(64, 1000, "Time saved assumes 6 min manual handoff per variant (copy to CRM, write task, notify team). Costs measured from Claude usage tokens.", 12, MUTED))
(OUT / "exec_summary.svg").write_text(svg(W, H, "".join(b)))

# ------------------------------------------------------------------ architecture
W, H = 1760, 1080
b = []
b.append('<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#475569"/></marker>'
         f'<marker id="r" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{RED}"/></marker></defs>')
b.append(t(56, 64, "TECHNICAL ARCHITECTURE", 13, TEAL, 700, ls="2"))
b.append(t(56, 106, "Madison Action Layer v2 — data flow, AI components, integrations and failure paths", 30, INK, 700))
b.append(badge(1324, 44))

def node(x, y, w, h, title, sub, kind="code"):
    fill, stroke = {"code": (SOFT, "#cbd2dc"), "ai": (PURPLE_SOFT, PURPLE), "int": (ORANGE_SOFT, AMBER), "store": (TEAL_SOFT, TEAL), "src": ("#eef2ff", "#4338ca")}[kind]
    out = box(x, y, w, h, fill, stroke, 10, 1.6)
    out += t(x + 14, y + 26, title, 15, INK, 700)
    out += lines(x + 14, y + 48, sub, 12.5, TEXT, 1.35)
    if kind == "ai":
        out += box(x + w - 46, y + 10, 34, 20, PURPLE, PURPLE, 10) + t(x + w - 29, y + 24, "AI", 11, "#fff", 700, "middle")
    return out

def arrow(x1, y1, x2, y2, red=False, label=None, lx=None, ly=None):
    c = RED if red else "#475569"
    d = ' stroke-dasharray="7 5"' if red else ""
    s = f'<path d="M{x1},{y1} L{x2},{y2}" stroke="{c}" stroke-width="2" fill="none" marker-end="url(#{"r" if red else "a"})"{d}/>'
    if label:
        s += t(lx if lx is not None else (x1 + x2) / 2, ly if ly is not None else (y1 + y2) / 2 - 8, label, 12, c, 600, "middle")
    return s

def elbow(pts, red=False, label=None, lx=0, ly=0):
    c = RED if red else "#475569"
    d = ' stroke-dasharray="7 5"' if red else ""
    p = "M" + " L".join(f"{x},{y}" for x, y in pts)
    s = f'<path d="{p}" stroke="{c}" stroke-width="2" fill="none" marker-end="url(#{"r" if red else "a"})"{d}/>'
    if label: s += t(lx, ly, label, 12, c, 600, "middle")
    return s

# lane labels
b.append(t(56, 168, "PER-EVENT PATH (webhook, synchronous, ~6–9 s)", 12, MUTED, 700, ls="1.2"))
Y = 190
b.append(node(56, Y, 200, 96, "Madison Content Agent", ["Variant event (A2 schema)", "A3 data → make_events.py"], "src"))
b.append(node(300, Y, 190, 96, "Webhook", ["POST /madison/variant", "Header Auth key"], "int"))
b.append(node(534, Y, 210, 96, "① Gatekeeper", ["Schema + date checks", "Popper gate · idempotency key"], "code"))
b.append(node(788, Y, 200, 96, "Idempotency check", ["Data Table lookup", "brief_id:variant_id"], "store"))
b.append(node(1032, Y, 230, 96, "② Routing Agent", ["Claude Haiku 4.5 · JSON schema", "fit · risks · decision · fix"], "ai"))
b.append(node(1306, Y, 200, 96, "Validate AI Decision", ["enums · refusal · truncation", "tokens → cost"], "code"))
b.append(arrow(256, Y + 48, 298, Y + 48)); b.append(arrow(490, Y + 48, 532, Y + 48)); b.append(arrow(744, Y + 48, 786, Y + 48, label="valid"))
b.append(arrow(988, Y + 48, 1030, Y + 48, label="new")); b.append(arrow(1262, Y + 48, 1304, Y + 48))
Y2 = 400
b.append(node(1306, Y2, 200, 96, "③ Plan Actions", ["Task + Slack Block Kit", "live vs dry_run"], "code"))
b.append(arrow(1406, Y + 96, 1406, Y2 - 2, label="valid", lx=1440, ly=Y + 160))
b.append(node(1032, Y2, 230, 96, "HubSpot · Slack", ["Create task (CRM)", "Alert #urgent/#review/#digest"], "int"))
b.append(arrow(1306, Y2 + 48, 1264, Y2 + 48))
b.append(node(788, Y2, 200, 96, "Action Log", ["n8n Data Table · 18 cols", "every outcome + cost"], "store"))
b.append(arrow(1032, Y2 + 48, 990, Y2 + 48))
b.append(node(534, Y2, 210, 96, "Respond to Madison", ["200 decision JSON", "422 blocked · 200 duplicate"], "int"))
b.append(arrow(788, Y2 + 48, 746, Y2 + 48))
# failure paths
b.append(node(1306, 560, 200, 80, "Rule-based Fallback", ["regex risks · team by channel", "→ human review"], "code"))
b.append(elbow([(1506, Y + 72), (1560, Y + 72), (1560, 600), (1508, 600)], True, "429 · timeout · bad JSON", 1640, 420))
b.append(arrow(1406, 560, 1406, Y2 + 98, True))
b.append(elbow([(639, Y + 96), (639, 340), (560, 340), (560, Y2 - 2)], True))
b.append(t(500, 334, "blocked → 422", 12, RED, 600, "middle"))
b.append(elbow([(888, Y + 96), (888, 350), (700, 350), (700, Y2 - 2)], True))
b.append(t(800, 372, "duplicate → skip", 12, RED, 600, "middle"))
b.append(t(1290, 532, "3 retries (5 s) on every external call · failures logged, never dropped", 12, RED, 600, "end"))
# report lane
b.append(f'<line x1="56" y1="690" x2="1624" y2="690" stroke="{LINE}" stroke-width="1"/>')
b.append(t(56, 724, "BATCH PATH (daily 6 pm schedule or on demand)", 12, MUTED, 700, ls="1.2"))
Y3 = 746
b.append(node(56, Y3, 200, 90, "Schedule / Manual", ["Report Settings", "run_id · lookback"], "src"))
b.append(node(300, Y3, 190, 90, "Read Action Log", ["Data Table · all rows"], "store"))
b.append(node(534, Y3, 210, 90, "Aggregate Stats", ["mix · latency · cost", "risk counts · hours saved"], "code"))
b.append(node(788, Y3, 230, 90, "④ Insights Agent", ["Claude Haiku 4.5 · JSON", "patterns · recs · watchlist"], "ai"))
b.append(node(1062, Y3, 200, 90, "Build Report", ["HTML email · Slack digest", "Sheet rows"], "code"))
for x1, x2 in [(256, 298), (490, 532), (744, 786), (1018, 1060)]: b.append(arrow(x1, Y3 + 45, x2, Y3 + 45))
outs = [("Gmail", "HTML run report"), ("Slack #campaign-digest", "digest"), ("Google Sheets", "batched append"), ("HTML file", "download")]
for i, (a_, s_) in enumerate(outs):
    y = 706 + i * 60
    b.append(node(1340, y, 220, 52, a_, [s_], "int"))
    b.append(elbow([(1262, Y3 + 45), (1300, Y3 + 45), (1300, y + 28), (1338, y + 28)]))
# error workflow + legend
b.append(node(56, 966, 300, 80, "Error workflow (n8n)", ["Error Trigger → Slack #campaign-urgent", "any unhandled crash"], "int"))
b.append(box(400, 966, 1160, 80, BG, LINE))
leg = [(PURPLE_SOFT, PURPLE, "AI component (Claude)"), (ORANGE_SOFT, AMBER, "Integration point"), (TEAL_SOFT, TEAL, "Storage (Data Table)"), (SOFT, "#cbd2dc", "n8n Code / logic")]
for i, (f, s_, l) in enumerate(leg):
    x = 424 + i * 230
    b.append(box(x, 994, 26, 22, f, s_, 5, 1.6)); b.append(t(x + 36, 1011, l, 14, TEXT))
b.append(f'<path d="M1344,1005 L1394,1005" stroke="{RED}" stroke-width="2" stroke-dasharray="7 5"/>' + t(1404, 1011, "Failure path", 14, TEXT))
(OUT / "architecture.svg").write_text(svg(W, H, "".join(b)))

# ------------------------------------------------------------------ before / after
W, H = 1440, 900
b = []
b.append(t(64, 72, "BEFORE / AFTER", 13, TEAL, 700, ls="2"))
b.append(t(64, 116, "Assignment 3 collected the data. Assignment 4 acts on it.", 34, INK, 700))
b.append(box(64, 150, 640, 120, SOFT, LINE)); b.append(box(736, 150, 640, 120, TEAL_SOFT, "#b7dfd9"))
b.append(t(88, 186, "A3 · DATA PIPELINE", 13, MUTED, 700, ls="1.5")); b.append(t(760, 186, "A4 · ACTION LAYER", 13, TEAL, 700, ls="1.5"))
b.append(lines(88, 220, ["Collects 285 clean records from 3 sources", "into a CSV + quality report."], 18, INK, weight=600))
b.append(lines(760, 220, ["Turns each record into a decision and a real", "action in HubSpot and Slack — in ~6 seconds."], 18, INK, weight=600))
rows = [("Intelligence", "None — rules only (dedupe, date checks)", "Claude routes every variant: channel fit, risk flags with evidence, decision, owner, rewrite; a 2nd agent finds batch patterns"),
        ("Output", "CSV + JSON quality report", "Slack alerts · HubSpot tasks · Gmail report · Google Sheet · HTML report"),
        ("Trigger", "Manual run, once", "Webhook per event + daily scheduled digest"),
        ("Error handling", "Retry + continue on fetch errors", "Retries on every call · AI answer validator · fallback router · error workflow → Slack"),
        ("Duplicates", "Removed after collection", "Idempotency key blocks re-processing (0.19 s, $0)"),
        ("Scale evidence", "1 run, 295 records", "834 real requests up to 100 concurrent · 0 failures · ≈330/min ceiling"),
        ("Cost visibility", "—", "$0.0044 per event, measured from token usage"),
        ("Human time", "Still copy-paste into CRM", "≈3.5 h saved per 50 variants")]
y = 300
for k, a_, c_ in rows:
    b.append(f'<line x1="64" y1="{y}" x2="1376" y2="{y}" stroke="{LINE}"/>')
    b.append(t(64, y + 34, k, 15, MUTED, 700))
    b.append(t(240, y + 34, a_, 15, TEXT))
    # wrap A4 column at ~62 chars
    words, ln, out_ = c_.split(), "", []
    for w_ in words:
        if len(ln) + len(w_) > 64: out_.append(ln); ln = w_
        else: ln = (ln + " " + w_).strip()
    out_.append(ln)
    b.append(lines(736, y + 34, out_, 15, INK, 1.4, 600))
    y += max(56, 22 * len(out_) + 30)
b.append(t(64, y + 40, "Same 285 A3 records feed A4: ad copy = creative · campaigns = routing context · RSS = market context.", 14, MUTED))
(OUT / "before_after.svg").write_text(svg(W, H, "".join(b)))

# ------------------------------------------------------------------ scale chart: two panels, one axis each (no dual axis)
W, H = 1320, 600
conc = [1, 10, 20, 50, 100]
thr = [8.3, 78.1, 178.9, 317.0, 334.1]
p50 = [8.9, 8.9, 8.2, 9.6, 16.3]
p95 = [10.0, 10.7, 10.8, 13.2, 26.8]
b = []
b.append(t(48, 54, "Scale test · n8n on 1 vCPU + Claude Haiku 4.5", 22, INK, 700))
b.append(t(48, 82, "Runs scale-10 · scale-50 · scale-100 · scale-200 · v2-400 (real requests; 0 failures in every run)", 14, MUTED))

def panel(x0, y0, w, h, title, ymax, yticks, series, unit):
    s = t(x0, y0 - 18, title, 16, INK, 700)
    xs = lambda i: x0 + 50 + i * (w - 80) / (len(conc) - 1)
    ys = lambda v: y0 + h - 40 - v / ymax * (h - 70)
    for v in yticks:
        s += f'<line x1="{x0 + 50}" y1="{ys(v)}" x2="{x0 + w - 30}" y2="{ys(v)}" stroke="#eceef2"/>' + t(x0 + 40, ys(v) + 4, f"{v}", 12, MUTED, anchor="end")
    s += f'<line x1="{x0 + 50}" y1="{ys(0)}" x2="{x0 + w - 30}" y2="{ys(0)}" stroke="#9aa1ad"/>'
    for i, c in enumerate(conc):
        s += t(xs(i), ys(0) + 22, str(c), 12, MUTED, anchor="middle")
    s += t(x0 + 50 + (w - 80) / 2, ys(0) + 44, "concurrent requests (steps, not to scale)", 12, MUTED, anchor="middle")
    s += t(x0 + 10, y0 + 10, unit, 12, MUTED)
    for name, vals, col in series:
        pts = " ".join(f"{xs(i)},{ys(v)}" for i, v in enumerate(vals))
        s += f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2" stroke-linejoin="round"/>'
        for i, v in enumerate(vals):
            s += f'<circle cx="{xs(i)}" cy="{ys(v)}" r="5" fill="{col}" stroke="#fff" stroke-width="2"/>'
        lv = vals[-1]
        s += t(xs(len(vals) - 1) - 10, ys(lv) - 12, f"{name} {lv:g}", 13, TEXT, 600, "end")
    return s

b.append(panel(48, 140, 600, 400, "Throughput (events / minute)", 350, [0, 100, 200, 300], [("", thr, "#0d9488")], "events/min"))
b.append(t(440, 196, "plateau ≈ 330/min →", 13, TEXT, 600, "end"))
b.append(panel(700, 140, 600, 400, "End-to-end latency (seconds)", 30, [0, 10, 20, 30], [("p95", p95, "#d97706"), ("p50", p50, "#0d9488")], "seconds"))
# legend for latency (2 series)
b.append(f'<circle cx="1110" cy="118" r="5" fill="#0d9488"/>' + t(1122, 123, "p50 (median)", 13, TEXT))
b.append(f'<circle cx="1230" cy="118" r="5" fill="#d97706"/>' + t(1242, 123, "p95", 13, TEXT))
b.append(t(48, 586, "Above 50 concurrent, throughput stops rising and latency doubles: requests queue in front of the single n8n process (Gatekeeper-only events: 0.2 s → 8.1 s).", 13, MUTED))
(OUT / "scale_chart.svg").write_text(svg(W, H, "".join(b)))
print("wrote", [p.name for p in OUT.glob("*.svg")])
