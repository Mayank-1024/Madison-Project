"""LAYER 1 · External sources → data/raw/   (never trusted; saved exactly as received, plus a fetch envelope)
Live: HuggingFace datasets-server rows API (2 datasets) + 4 marketing RSS feeds.
--sample: no network; reads the Assignment 3 snapshot in fixtures/ instead.
Output: data/raw/<source>/<source>-<run_id>.json  {source, mode, fetched_at, endpoints[], status, records[]}"""
import csv, html, json, re, sys, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import RAW, ROOT, now_iso, write_json

HF = "https://datasets-server.huggingface.co/rows?dataset={ds}&config=default&split=train&offset=0&length=100"
DATASETS = {"ad_copy": "jaykin01/advertisement-copy", "campaign_metadata": "federicomoreno/marketing-campaign-performance-200k"}
FEEDS = {"HubSpot Marketing Blog": "https://blog.hubspot.com/marketing/rss.xml", "Social Media Examiner": "https://www.socialmediaexaminer.com/feed/",
         "Marketing Dive": "https://www.marketingdive.com/feeds/news/", "MarTech": "https://martech.org/feed/"}
UA = {"User-Agent": "Mozilla/5.0 (madison-ad-handoff pipeline; coursework)"}


def get(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


def fetch_hf(source):
    url = HF.format(ds=DATASETS[source])
    try:
        status, body = get(url)
        rows = [r["row"] | {"_row_idx": r["row_idx"]} for r in json.loads(body).get("rows", [])]
        return {"endpoint": url, "http_status": status, "ok": bool(rows), "error": None if rows else "0 rows"}, rows
    except Exception as e:  # network error, HTTP error, bad JSON: logged, never raised
        return {"endpoint": url, "http_status": getattr(e, "code", None), "ok": False, "error": f"{type(e).__name__}: {e}"}, []


def text(el, tag):
    x = el.find(tag)
    return (x.text or "").strip() if x is not None and x.text else ""


def fetch_rss():
    endpoints, records = [], []
    for name, url in FEEDS.items():
        try:
            status, body = get(url)
            root = ET.fromstring(body)
            items = root.findall(".//item")
            for it in items:
                records.append({"feed": name, "title": text(it, "title"), "link": text(it, "link"), "pubDate": text(it, "pubDate"),
                                "description": text(it, "description"),
                                "categories": [c.text for c in it.findall("category") if c.text]})
            endpoints.append({"endpoint": url, "feed": name, "http_status": status, "ok": bool(items), "items": len(items), "error": None if items else "0 items"})
        except Exception as e:
            endpoints.append({"endpoint": url, "feed": name, "http_status": getattr(e, "code", None), "ok": False, "items": 0, "error": f"{type(e).__name__}: {e}"})
    return endpoints, records


def sample_records():
    """Rebuild source-shaped raw records from the A3 snapshot (offline mode)."""
    rows = list(csv.DictReader(open(ROOT / "fixtures/a3_snapshot.csv", encoding="utf-8-sig")))
    ads = [{"product": r["brand_or_product"], "description": "", "ad": " ".join(x for x in [r["title_or_headline"], r["body_text"], r["cta"]] if x),
            "_row_idx": i} for i, r in enumerate(rows) if r["source_type"] == "ad_copy"]
    cmps = []
    for r in rows:
        if r["source_type"] != "campaign_metadata":
            continue
        b = r["body_text"]
        g = lambda p: (m.group(1) if (m := re.search(p, b)) else None)
        aud = r["audience"].split(" · ")
        cmps.append({"Campaign_ID": int(r["record_id"].split("-")[1]), "Company": r["brand_or_product"], "Campaign_Type": r["campaign_type"],
                     "Target_Audience": aud[0], "Customer_Segment": aud[1] if len(aud) > 1 else "", "Channel_Used": r["channel"],
                     "Conversion_Rate": float(g(r"Conversion rate (\d+)%") or 0) / 100, "ROI": float(g(r"ROI ([\d.]+)") or 0),
                     "Engagement_Score": int(g(r"engagement score (\d+)/10") or 0), "Date": r["published_date"]})
    arts = [{"feed": r["source_name"].replace("RSS: ", ""), "title": r["title_or_headline"], "link": r["source_url"], "pubDate": r["published_date"],
             "description": r["body_text"], "categories": [c for c in r["tags"].split("; ") if c]} for r in rows if r["source_type"] == "industry_article"]
    return ads, cmps, arts


def run(run_id, sample=False):
    out, fetched = {}, now_iso()
    if sample:
        ads, cmps, arts = sample_records()
        payload = {"ad_copy": ([{"endpoint": "fixtures/a3_snapshot.csv", "ok": True}], ads),
                   "campaign_metadata": ([{"endpoint": "fixtures/a3_snapshot.csv", "ok": True}], cmps),
                   "industry_briefs": ([{"endpoint": "fixtures/a3_snapshot.csv", "ok": True}], arts)}
    else:
        payload = {s: (lambda r: ([r[0]], r[1]))(fetch_hf(s)) for s in DATASETS}
        payload["industry_briefs"] = fetch_rss()
    for source, (endpoints, records) in payload.items():
        env = {"source": source, "mode": "sample" if sample else "live", "fetched_at": fetched, "endpoints": endpoints,
               "status": "ok" if records else "unavailable", "record_count": len(records), "records": records}
        out[source] = {"path": str(write_json(RAW / source / f"{source}-{run_id}.json", env).relative_to(ROOT)), "count": len(records),
                       "endpoints": endpoints, "status": env["status"]}
    return out


if __name__ == "__main__":
    print(json.dumps(run(sys.argv[1] if len(sys.argv) > 1 else "manual", "--sample" in sys.argv), indent=1))
