"""Turns Assignment 3 records into Madison-style variant events (the A2 PRD input schema).
Each event = one ad (creative) + one campaign (context) + one RSS brief, paired deterministically.
About 10% are deliberately broken (Popper failure, missing field, bad date) to exercise the Gatekeeper,
and a few are exact repeats to exercise idempotency.

Usage: python3 make_events.py --n 50 --run-id scale-50 [--dry-run] [--out events_scale-50.jsonl]
"""
import argparse, csv, json, pathlib, datetime as dt

A3 = pathlib.Path(__file__).resolve().parents[2] / "Assignment_3" / "madison_a3_records.csv"

def load():
    rows = list(csv.DictReader(open(A3, encoding="utf-8-sig")))
    ads = [r for r in rows if r["source_type"] == "ad_copy"]
    cmps = [r for r in rows if r["source_type"] == "campaign_metadata"]
    briefs = [r for r in rows if r["source_type"] == "industry_article"]
    return ads, cmps, briefs

def parse_campaign(c):
    """Pull the numbers back out of the A3 campaign summary text."""
    import re
    b = c["body_text"]
    num = lambda pat: (float(m.group(1).replace(",", "")) if (m := re.search(pat, b)) else None)
    conv = num(r"Conversion rate (\d+)%")
    # The A3 campaign dataset is synthetic and assigns campaign_type at random (e.g. "Email" on Instagram),
    # so the type is derived from the channel to keep each test event internally consistent.
    TYPE_BY_CHANNEL = {"Google Ads": "Search", "YouTube": "Video", "Facebook": "Social Media", "Instagram": "Social Media",
                       "Email": "Email", "Website": "Display"}
    return {"company": c["brand_or_product"], "channel": c["channel"], "campaign_type": TYPE_BY_CHANNEL.get(c["channel"], c["campaign_type"]), "audience": c["audience"],
            "conversion_rate": conv / 100 if conv is not None else None, "roi": num(r"ROI ([\d.]+)"),
            "engagement_score": num(r"engagement score (\d+)/10")}

def build(n, run_id, dry_run, broken_every=10, repeat_every=25):
    ads, cmps, briefs = load()
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    events = []
    for i in range(n):
        ad, c, b = ads[(i * 7) % len(ads)], cmps[(i * 3) % len(cmps)], briefs[i % len(briefs)]
        e = {
            "event_id": f"evt_{run_id}_{i + 1:04d}", "run_id": run_id, "mode": "dry_run" if dry_run else "live",
            "source_agent": "madison.content_agent", "brief_id": b["record_id"], "variant_id": f"{ad['record_id']}-{run_id}-{i + 1:04d}",
            "product": ad["brand_or_product"], "headline": ad["title_or_headline"], "body": ad["body_text"], "cta": ad["cta"],
            "popper_pass": ad["is_complete"].upper() == "TRUE", "quality_score": 100 + (len(ad["body_text"]) % 60),
            "campaign_owner": f"owner+{c['brand_or_product'].lower().replace(' ', '')}@example.com", "created_at": now,
            "campaign": parse_campaign(c),
            "brief": {"title": b["title_or_headline"], "summary": b["body_text"], "source": b["source_name"].replace("RSS: ", ""),
                      "url": b["source_url"], "published_date": b["published_date"]},
        }
        k = i % broken_every
        if i and k == 3: e["headline"] = ""                       # Gatekeeper: missing field
        if i and k == 6: e["created_at"] = "not-a-date"           # Gatekeeper: invalid date
        events.append(e)
        if i and i % repeat_every == 0: events.append(dict(e))    # idempotency: exact repeat
    return events[:n]

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args()
    ev = build(a.n, a.run_id, a.dry_run)
    out = pathlib.Path(a.out or pathlib.Path(__file__).parent / f"events_{a.run_id}.jsonl")
    out.write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in ev) + "\n")
    print(f"{len(ev)} events → {out}  (popper fails: {sum(not e['popper_pass'] for e in ev)}, "
          f"broken: {sum(e['headline'] == '' or e['created_at'] == 'not-a-date' for e in ev)}, "
          f"repeats: {len(ev) - len({e['variant_id'] for e in ev})})")
