"""LAYER 3 · Tool / AI processing   (data/verified/ → Routing Agent → logs/)
Pairs each verified ad with a client campaign (and a news article as optional context), sends it to the Assignment 4
Routing Agent (n8n workflow → Claude Haiku 4.5) in dry_run mode, then re-checks every answer before anyone trusts it:
  evidence really appears in the ad · character counts are right · no placeholder text is approved · owner matches channel.
Secrets from the environment only: MADISON_WEBHOOK_URL, MADISON_WEBHOOK_KEY.  --sample: no network, rule-based routing.
Output: logs/<workflow>-<run_id>-decisions.json"""
import json, os, re, sys, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import LOGS, VERIFIED, WORKFLOW, now_iso, read_json, write_json

TEAM = {"Google Ads": "Paid Media", "Email": "Lifecycle & Email", "Facebook": "Social & Influencer", "Instagram": "Social & Influencer",
        "YouTube": "Social & Influencer", "Website": "Content & SEO"}
LIMIT = {"Google Ads": 30, "Email": 60}
PLACEHOLDER = re.compile(r"\[[^\]]*\]|bit\.ly/\S+|\bTBD\b", re.I)


def build_events(run_id, n):
    ads = read_json(VERIFIED / "ad_copy/ad_copy.json")["records"]
    cmps = read_json(VERIFIED / "campaign_metadata/campaign_metadata.json")["records"]
    arts = read_json(VERIFIED / "industry_briefs/industry_briefs.json")["records"]
    out = []
    for i in range(min(n, len(ads))):
        a, c, b = ads[(i * 7) % len(ads)], cmps[(i * 3) % len(cmps)], arts[i % len(arts)] if arts else {}
        out.append({"event_id": f"evt_{run_id}_{i + 1:03d}", "run_id": run_id, "mode": "dry_run", "source_agent": "madison.recipe",
                    "brief_id": b.get("record_id", "NONE"), "variant_id": f"{a['record_id']}-{run_id}", "product": a["product"],
                    "headline": a["headline"], "body": a["body"], "cta": a["cta"], "popper_pass": "missing_cta" not in a["flags"],
                    "quality_score": None, "campaign_owner": "", "created_at": now_iso(),
                    "campaign": {k: c[k] for k in ["company", "channel", "campaign_type", "audience", "conversion_rate", "roi", "engagement_score"]},
                    "brief": {"title": b.get("title", ""), "summary": b.get("summary", ""), "source": b.get("feed", ""), "url": b.get("url", ""), "published_date": b.get("date", "")},
                    "_ad_flags": a["flags"], "_ad_id": a["record_id"], "_campaign_id": c["record_id"]})
    return out


def call_live(ev, url, key):
    body = json.dumps({k: v for k, v in ev.items() if not k.startswith("_")}).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type": "application/json", "X-Madison-Key": key})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            code, raw = r.status, r.read()
    except urllib.error.HTTPError as e:
        code, raw = e.code, e.read()
    except Exception as e:
        return {"http_status": 0, "error": f"{type(e).__name__}: {e}", "seconds": round(time.time() - t0, 2)}
    try:
        data = json.loads(raw)
        data = data[0] if isinstance(data, list) else data
    except ValueError:
        data = {"error": "unreadable response"}
    return {"http_status": code, "seconds": round(time.time() - t0, 2), **data}


def call_sample(ev):
    """Offline stand-in: the same deterministic rules as the n8n fallback router."""
    text = " ".join([ev["headline"], ev["body"], ev["cta"]])
    if not ev["popper_pass"]:
        return {"http_status": 422, "status": "blocked", "seconds": 0, "detail_json": json.dumps({"gate_reasons": ["popper_quality_gate_failed"]})}
    flags, ch = [], ev["campaign"]["channel"]
    if (m := PLACEHOLDER.search(text)): flags.append({"type": "placeholder_text", "severity": "high", "evidence": m.group(0)})
    if (m := re.search(r"unbeatable|ultimate|best|#1", text, re.I)): flags.append({"type": "unverifiable_claim", "severity": "medium", "evidence": m.group(0)})
    lim, n = LIMIT.get(ch), len(ev["headline"])
    blocked = any(f["severity"] == "high" for f in flags)
    dec = "block" if blocked else ("needs_review" if flags or (lim and n > lim) else "auto_approve")
    d = {"decision": dec, "priority": "high" if blocked else "normal", "owner_team": "Brand & Legal Review" if blocked else TEAM.get(ch, "Content & SEO"),
         "slack_channel": "campaign-review" if dec != "auto_approve" else "campaign-digest",
         "channel_fit": {"score": 2 if (lim and n > lim) else 4, "note": f"Headline is {n} characters" + (f" (limit {lim})." if lim else ".")},
         "risk_flags": flags, "rationale": "Sample mode: routed by deterministic rules, not the AI.", "suggested_fix": "Shorten the headline to the channel limit." if lim and n > lim else "None needed",
         "hubspot_task": {"title": f"Review {ch} ad for {ev['campaign']['company']}", "body": "Sample mode task.", "due_in_days": 3},
         "slack_message": "Sample mode.", "confidence": 0.5}
    return {"http_status": 200, "status": "completed", "ai_status": "sample", "seconds": 0, "cost_usd": 0, "detail_json": json.dumps({"decision": d})}


def verify(ev, resp):
    """Phase-gate 3 checks on one AI answer. Returns a list of problems (empty = trustworthy)."""
    try:
        d = (json.loads(resp.get("detail_json") or "{}")).get("decision") or {}
    except ValueError:
        d = {}
    if resp.get("status") == "blocked":
        return d, [], "rejected_by_gatekeeper"
    if not d:
        return d, ["no decision returned"], "failed"
    problems, ad_text = [], " ".join([ev["headline"], ev["body"], ev["cta"]]).lower()
    for f in d.get("risk_flags") or []:
        quotes = re.findall(r"[“\"']([^”\"']{4,})[”\"']", f.get("evidence", "")) or [f.get("evidence", "")]
        if f.get("type") in ("placeholder_text", "unverifiable_claim", "false_urgency", "weak_or_missing_cta") and quotes and not any(
                q.lower().strip(" .!") in ad_text or ad_text.find(q.lower()[:12]) >= 0 for q in quotes):
            problems.append(f"evidence not found in ad: {quotes[0][:50]!r}")
    note, n = (d.get("channel_fit") or {}).get("note", ""), len(ev["headline"])
    counts = [int(x) for x in re.findall(r"(\d+)\s*(?:characters|chars|char)\b", note)]
    lim = LIMIT.get(ev["campaign"]["channel"])
    if counts and not any(abs(c - n) <= 2 for c in counts) and not all(c == lim for c in counts):
        problems.append(f"character count off: says {counts}, headline is {n}")
    if d.get("decision") == "auto_approve" and PLACEHOLDER.search(ad_text):
        problems.append("HARD: placeholder text approved")
    exp = TEAM.get(ev["campaign"]["channel"])
    if d.get("decision") != "block" and exp and d.get("owner_team") != exp:
        problems.append(f"owner {d.get('owner_team')!r} does not match channel (expected {exp!r})")
    return d, problems, ("fallback" if resp.get("ai_status") == "fallback" else "ok")


def run(run_id, n=20, sample=False):
    events = build_events(run_id, n)
    url, key = os.environ.get("MADISON_WEBHOOK_URL", ""), os.environ.get("MADISON_WEBHOOK_KEY", "")
    if not sample and (not url or not key):
        return {"error": "MADISON_WEBHOOK_URL / MADISON_WEBHOOK_KEY not set", "results": []}
    with ThreadPoolExecutor(max_workers=5) as pool:
        resps = list(pool.map(call_sample if sample else (lambda e: call_live(e, url, key)), events))
    results = []
    for ev, resp in zip(events, resps):
        d, problems, kind = verify(ev, resp)
        results.append({"event_id": ev["event_id"], "ad_id": ev["_ad_id"], "campaign_id": ev["_campaign_id"], "company": ev["campaign"]["company"],
                        "channel": ev["campaign"]["channel"], "headline": ev["headline"], "cta": ev["cta"], "http_status": resp.get("http_status"),
                        "status": resp.get("status", "error"), "ai_status": resp.get("ai_status", ""), "kind": kind, "seconds": resp.get("seconds"),
                        "cost_usd": float(resp.get("cost_usd") or 0), "decision": d, "problems": problems, "error": resp.get("error")})
    out = {"workflow": WORKFLOW, "run_id": run_id, "mode": "sample" if sample else "live-dry_run", "generated_at": now_iso(), "count": len(results), "results": results}
    write_json(LOGS / f"{WORKFLOW}-{run_id}-decisions.json", out)
    return out


if __name__ == "__main__":
    r = run(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 20, "--sample" in sys.argv)
    print(json.dumps({k: v for k, v in r.items() if k != "results"}, indent=1))
