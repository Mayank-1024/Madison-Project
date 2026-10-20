"""LAYER 2 · data/raw/ → data/verified/   (the GIGO gate: Conductor Brief Part 3 quality standards, record by record)
Verified: data/verified/<source>/<source>.json  (+ .csv)  ·  Rejects: data/raw/rejected/<source>/rejects-<run_id>.json (one reason each)
Also writes data/verified/README.md (counts, update date, gate applied, rejects by reason)."""
import csv, html, json, re, sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import RAW, REJECTED, ROOT, VERIFIED, now_iso, read_json, write_json

CHANNELS = {"Google Ads": "Search", "YouTube": "Video", "Facebook": "Social Media", "Instagram": "Social Media", "Email": "Email", "Website": "Display"}
CTA_WORDS = re.compile(r"\b(shop|buy|order|get|grab|try|book|sign up|join|visit|call|discover|explore|learn|start|claim|save|upgrade|treat|elevate|"
                       r"experience|download|subscribe|reserve|enjoy|find|unlock|step|embrace|transform)\b", re.I)
PLACEHOLDER = re.compile(r"\[[^\]]*\]|bit\.ly/\S+|\bTBD\b", re.I)
TODAY = datetime.now(timezone.utc)


def words(s): return len(str(s or "").split())


def clean(s):
    s = html.unescape(html.unescape(str(s or "")))
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s*The post .+ appeared first on .+$", "", s)
    return re.sub(r"\s+", " ", s).strip()


def iso_date(v):
    try:
        d = datetime.fromisoformat(str(v)) if re.match(r"^\d{4}-\d{2}-\d{2}", str(v)) else parsedate_to_datetime(str(v))
        d = d if d.tzinfo else d.replace(tzinfo=timezone.utc)
        return d
    except Exception:
        return None


# ---------------------------------------------------------------- per-source validators: return (record | None, reason | None)
def ad(r, seen):
    text = clean(r.get("ad"))
    tags = " ".join(re.findall(r"#\w+", text))
    text = re.sub(r"#\w+", "", text).strip().strip('"')
    s = [x for x in re.split(r"(?<=[.!?])\s+", text) if x]
    head, body, cta = (s[0] if s else ""), s[1:], ""
    if len(s) > 1 and CTA_WORDS.search(s[-1]):
        cta, body = s[-1], s[1:-1]
    body = " ".join(body) or clean(r.get("description"))
    product = clean(r.get("product"))
    key = re.sub(r"[^a-z0-9]", "", product.lower())
    if words(head) < 3: return None, "headline under 3 words"
    if not product: return None, "no product name"
    if words(body) < 8: return None, "body under 8 words"
    if key in seen: return None, "duplicate product (shuffled repeat)"
    seen.add(key)
    flags = (["missing_cta"] if not cta else []) + (["placeholder_text"] if PLACEHOLDER.search(text) else [])
    return {"record_id": f"AD-{r['_row_idx'] + 1:04d}", "product": product, "headline": head, "body": body, "cta": cta, "hashtags": tags,
            "flags": flags, "source": "huggingface:jaykin01/advertisement-copy", "dataset_date": "2023-09-25"}, None


def campaign(r, seen):
    ch = clean(r.get("Channel_Used"))
    d = iso_date(r.get("Date"))
    cid = r.get("Campaign_ID")
    if not clean(r.get("Company")): return None, "no company"
    if ch not in CHANNELS: return None, f"unknown channel '{ch}'"
    if not clean(r.get("Target_Audience")): return None, "no audience"
    if not isinstance(r.get("Conversion_Rate"), (int, float)) or not isinstance(r.get("ROI"), (int, float)): return None, "conversion rate or ROI not numeric"
    if not d or d > TODAY: return None, "missing, invalid or future date"
    if cid in seen: return None, "duplicate campaign ID"
    seen.add(cid)
    return {"record_id": f"CMP-{int(cid):04d}", "company": clean(r["Company"]), "channel": ch, "campaign_type": CHANNELS[ch],
            "audience": " · ".join(x for x in [clean(r.get("Target_Audience")), clean(r.get("Customer_Segment"))] if x),
            "conversion_rate": r["Conversion_Rate"], "roi": r["ROI"], "engagement_score": r.get("Engagement_Score"), "date": d.date().isoformat(),
            "source_campaign_type": clean(r.get("Campaign_Type"))}, None


def article(r, seen):
    title, url, summary = clean(r.get("title")), clean(r.get("link")), clean(r.get("description"))
    d = iso_date(r.get("pubDate"))
    if not title: return None, "no title"
    if not re.match(r"^https?://", url): return None, "no working URL"
    if not d or d > TODAY + timedelta(days=1): return None, "missing or invalid date"
    if d < TODAY - timedelta(days=90): return None, "older than 90 days"
    if words(summary) < 20: return None, "summary under 20 words"
    if url.lower() in seen: return None, "duplicate URL"
    seen.add(url.lower())
    if len(summary) > 600: summary = summary[:597].rstrip() + "..."
    return {"record_id": "", "feed": r.get("feed"), "title": title, "url": url, "date": d.date().isoformat(), "summary": summary,
            "categories": "; ".join((r.get("categories") or [])[:5])}, None


VALIDATORS = {"ad_copy": ad, "campaign_metadata": campaign, "industry_briefs": article}
GATE_TEXT = {
    "ad_copy": "Headline of 3+ words, product name, body of 8+ words, not a duplicate product. Missing call-to-action or placeholder text is tagged (kept), not rejected.",
    "campaign_metadata": "Company, one of 6 known channels, audience, numeric conversion rate and ROI, valid past YYYY-MM-DD date, unique campaign ID. Campaign type derived from the channel.",
    "industry_briefs": "Title, http(s) URL seen once, publication date within the last 90 days, plain-text summary of 20+ words (HTML and WordPress footers stripped).",
}
DESC = {"ad_copy": "finished ad variants (the creative to judge)", "campaign_metadata": "client campaigns (owner + urgency context)",
        "industry_briefs": "marketing news articles (market context only)"}


def run(run_id, ingest):
    result = {}
    for source, info in ingest.items():
        env = read_json(ROOT / info["path"])
        seen, verified, rejects = set(), [], []
        for i, r in enumerate(env["records"]):
            rec, why = VALIDATORS[source](r, seen)
            if rec:
                if source == "industry_briefs":
                    rec["record_id"] = f"ART-{len(verified) + 1:04d}"
                verified.append(rec)
            else:
                rejects.append({"raw_index": i, "reason": why, "record": r})
        write_json(VERIFIED / source / f"{source}.json", {"source": source, "run_id": run_id, "verified_at": now_iso(), "count": len(verified), "records": verified})
        if verified:
            with open(VERIFIED / source / f"{source}.csv", "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(verified[0].keys())); w.writeheader()
                w.writerows({k: ("; ".join(v) if isinstance(v, list) else v) for k, v in x.items()} for x in verified)
        write_json(REJECTED / source / f"rejects-{run_id}.json", {"source": source, "run_id": run_id, "count": len(rejects), "rejects": rejects})
        flagged = sum(1 for x in verified if x.get("flags"))
        result[source] = {"raw": len(env["records"]), "verified": len(verified), "rejected": len(rejects), "tagged": flagged,
                          "reject_reasons": dict(Counter(x["reason"] for x in rejects)), "complete_pct": round(100 * (len(verified) - flagged) / max(1, len(verified)), 1),
                          "reject_rate_pct": round(100 * len(rejects) / max(1, len(env["records"])), 1), "mode": env["mode"], "status": env["status"]}
    write_readme(run_id, result)
    return result


def write_readme(run_id, res):
    today = TODAY.date().isoformat()
    lines = ["# data/verified/", "", f"Verified inputs for the **madison-ad-handoff** pipeline. Generated by `scripts/gigo/madison-ad-handoff-validate-records.py` on {today} (run `{run_id}`).",
             "Only records that passed the GIGO gate (Conductor Brief Part 3) are in these folders. Every rejected record is kept, with its reason, in `data/raw/rejected/<source>/`.", "",
             "```", "data/verified/"]
    for s, r in res.items():
        lines.append(f"  {s + '/':<20} -- {r['verified']:>3} records | {today} | {DESC[s]}")
    lines += ["  README.md", "```", "", "| Source | Raw received | Verified | Rejected | Reject rate | Tagged (kept) | Complete |", "|---|---|---|---|---|---|---|"]
    for s, r in res.items():
        lines.append(f"| `{s}` | {r['raw']} | {r['verified']} | {r['rejected']} | {r['reject_rate_pct']}% | {r['tagged']} | {r['complete_pct']}% |")
    for s, r in res.items():
        lines += ["", f"## {s}/", f"- **Records:** {r['verified']} · **Last update:** {today} · **Mode:** {r['mode']}", f"- **Quality gate applied:** {GATE_TEXT[s]}",
                  "- **Records rejected and why:** " + ("; ".join(f"{n} × {why}" for why, n in r["reject_reasons"].items()) if r["reject_reasons"] else "none"),
                  f"- **Files:** `{s}.json` (with run metadata), `{s}.csv` (same records, spreadsheet-friendly)"]
    (VERIFIED / "README.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    rid = sys.argv[1]
    ing = {s: {"path": f"data/raw/{s}/{s}-{rid}.json"} for s in ["ad_copy", "campaign_metadata", "industry_briefs"]}
    print(json.dumps(run(rid, ing), indent=1))
