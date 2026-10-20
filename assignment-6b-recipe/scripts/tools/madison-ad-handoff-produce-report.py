"""LAYER 4 · logs/reports/ → USER   (the human report a marketing-ops lead reads; not a JSON dump)
Reader: agency marketing-ops lead. Decision enabled: what ships today, what each team must fix, what to stop.
Output: logs/reports/madison-ad-handoff-<run_id>.md"""
import json, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import REPORTS, WORKFLOW, now_iso

LABEL = {"auto_approve": "Ready to ship", "needs_review": "Fix before it ships", "block": "Do not publish"}
DUE = {"urgent": "today", "high": "within 1 day", "normal": "within 3 days", "low": "this week"}


def esc(s): return str(s or "").replace("|", "/").replace("\n", " ")


def build(run_id, routing, validation, gates):
    res = routing["results"]
    reviewed = [r for r in res if r["status"] == "completed"]
    gated = [r for r in res if r["status"] == "blocked"]
    errored = [r for r in res if r["status"] not in ("completed", "blocked")]
    by = {k: [r for r in reviewed if r["decision"].get("decision") == k] for k in LABEL}
    manual = [r for r in reviewed if r["kind"] in ("fallback", "sample") or r["problems"]]
    teams = Counter(r["decision"].get("owner_team", "?") for r in reviewed)
    risks = Counter(f.get("type", "?") for r in reviewed for f in r["decision"].get("risk_flags") or [])
    cost = sum(r["cost_usd"] for r in res)
    top_risk = risks.most_common(1)[0] if risks else None
    L = [f"# Ad handoff report · run `{run_id}`", f"*For the agency marketing-ops lead · generated {now_iso().replace('T', ' ')[:16]} UTC · mode: {routing['mode']}*", "",
         "## What this batch means", "",
         f"**{len(res)} new ads checked.** {len(by['auto_approve'])} can ship now, {len(by['needs_review'])} need a fix first, "
         f"{len(by['block'])} must not be published, and {len(gated)} were sent back before review because they were incomplete."
         + (f" The most common problem was **{top_risk[0].replace('_', ' ')}** ({top_risk[1]} ads)." if top_risk else "")
         + (f" **{len(manual)} verdicts need a manual check** (see the last section)." if manual else ""), ""]
    L += ["## Team queues", "", "| Team | Ads | Due |", "|---|---|---|"]
    for t, n in teams.most_common():
        dues = sorted({DUE.get(r["decision"].get("priority"), "?") for r in reviewed if r["decision"].get("owner_team") == t})
        L.append(f"| {esc(t)} | {n} | {', '.join(dues)} |")
    L += ["", f"## Ready to ship ({len(by['auto_approve'])})", "", "| Ad | Client | Channel | Owner |", "|---|---|---|---|"]
    L += [f"| {esc(r['headline'])} | {esc(r['company'])} | {esc(r['channel'])} | {esc(r['decision'].get('owner_team'))} |" for r in by["auto_approve"]] or ["| none | | | |"]
    for key in ("needs_review", "block"):
        L += ["", f"## {LABEL[key]} ({len(by[key])})", ""]
        for r in by[key]:
            d = r["decision"]
            L += [f"**{esc(r['headline'])}**  ", f"{esc(r['company'])} · {esc(r['channel'])} · owner **{esc(d.get('owner_team'))}** · due {DUE.get(d.get('priority'), '?')}  ",
                  "Problems: " + ("; ".join(f"{f.get('type', '').replace('_', ' ')} ({f.get('severity')}): “{esc(f.get('evidence'))[:90]}”" for f in d.get("risk_flags") or []) or "channel fit only") + "  ",
                  f"Fix: {esc(d.get('suggested_fix'))}", ""]
        if not by[key]:
            L.append("None.")
    L += ["", f"## Sent back before review ({len(gated)})", "", "These ads were incomplete when they arrived (for example no call-to-action), so the AI never saw them. Ask the content writer to finish them.", ""]
    L += [f"- {esc(r['headline'])} ({esc(r['company'])}, {esc(r['channel'])})" for r in gated] or ["- none"]
    L += ["", f"## Needs a manual check ({len(manual) + len(errored)})", ""]
    for r in manual:
        why = r["problems"] or [("routed by fallback rules, AI was unavailable" if r["kind"] == "fallback" else "sample mode, rules not AI")]
        L.append(f"- **{esc(r['headline'])}**: " + "; ".join(why))
    L += [f"- **{esc(r['headline'])}**: the checker did not answer ({esc(r.get('error'))})" for r in errored]
    if not manual and not errored:
        L.append("- none: every verdict passed the automatic checks.")
    L += ["", "## Data used", "", "| Source | Received | Verified | Rejected | Main rejection reason |", "|---|---|---|---|---|"]
    for s, v in validation.items():
        top = max(v["reject_reasons"].items(), key=lambda x: x[1])[0] if v["reject_reasons"] else "none"
        L.append(f"| {s} | {v['raw']} | {v['verified']} | {v['rejected']} | {esc(top)} |")
    L += ["", "## Phase-gate decisions", "", "| Gate | Judgment | Recipe response | Decision | Note |", "|---|---|---|---|---|"]
    L += [f"| {g['gate']}. {esc(g['name'])} | {g['judgment_type']} | {g['recipe_response']} | {g['decision']} | {esc(g['note'])} |" for g in gates]
    secs = [r["seconds"] for r in res if r.get("seconds")]
    L += ["", f"*AI cost for this batch: ${cost:.4f} · median time per ad: {sorted(secs)[len(secs) // 2] if secs else 0:.1f} s · nothing was sent to HubSpot or Slack (dry run).*", ""]
    path = REPORTS / f"{WORKFLOW}-{run_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(L))
    totals = {"checked": len(res), "ship": len(by["auto_approve"]), "fix": len(by["needs_review"]), "do_not_publish": len(by["block"]),
              "sent_back": len(gated), "errored": len(errored), "manual_check": len(manual) + len(errored), "cost_usd": round(cost, 4)}
    return path, totals
