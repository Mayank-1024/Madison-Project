"""Fires Madison events at the n8n webhook and measures what really happens.

Secrets come from environment variables only (never written to disk):
  export MADISON_WEBHOOK_URL="https://<your-n8n>/webhook/madison/variant"
  export MADISON_WEBHOOK_KEY="<the value in your n8n Header Auth credential>"

Usage: python3 loadtest.py events_scale-50.jsonl --concurrency 10 [--label scale-50]
Writes results/<label>.csv (one row per request) and results/<label>.json (summary).
"""
import argparse, concurrent.futures as cf, csv, json, os, pathlib, statistics, time, urllib.error, urllib.request

def send(event, url, key, timeout):
    data = json.dumps(event).encode()
    req = urllib.request.Request(url, data=data, method="POST", headers={"Content-Type": "application/json", "X-Madison-Key": key})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            code, body = r.status, r.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        code, body = e.code, e.read().decode(errors="replace")
    except Exception as e:  # timeouts, connection resets, DNS
        code, body = 0, f"{type(e).__name__}: {e}"
    secs = time.perf_counter() - t0
    try:
        j = json.loads(body)
    except ValueError:
        j = {}
    return {"event_id": event.get("event_id"), "http_status": code, "seconds": round(secs, 3), "status": j.get("status", ""),
            "decision": j.get("decision", ""), "ai_status": j.get("ai_status", ""), "cost_usd": j.get("cost_usd", ""),
            "server_latency_ms": j.get("latency_ms", ""), "error": "" if code in (200, 422) else body[:300]}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("events")
    ap.add_argument("--concurrency", type=int, default=1)
    ap.add_argument("--timeout", type=float, default=120)
    ap.add_argument("--label")
    a = ap.parse_args()
    url, key = os.environ.get("MADISON_WEBHOOK_URL"), os.environ.get("MADISON_WEBHOOK_KEY")
    if not url or not key:
        raise SystemExit("Set MADISON_WEBHOOK_URL and MADISON_WEBHOOK_KEY first (see the docstring).")
    events = [json.loads(l) for l in open(a.events) if l.strip()]
    label = a.label or pathlib.Path(a.events).stem.replace("events_", "")

    t0 = time.perf_counter()
    with cf.ThreadPoolExecutor(max_workers=a.concurrency) as pool:
        results = list(pool.map(lambda e: send(e, url, key, a.timeout), events))
    wall = time.perf_counter() - t0

    out = pathlib.Path(__file__).parent / "results"
    out.mkdir(exist_ok=True)
    with open(out / f"{label}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader(); w.writerows(results)

    secs = sorted(r["seconds"] for r in results)
    q = lambda p: secs[min(len(secs) - 1, int(p * len(secs)))]
    count = lambda k: {v: sum(1 for r in results if r[k] == v) for v in sorted({r[k] for r in results}, key=str)}
    costs = [float(r["cost_usd"]) for r in results if r["cost_usd"] not in ("", None)]
    summary = {
        "label": label, "requests": len(results), "concurrency": a.concurrency, "wall_clock_s": round(wall, 1),
        "throughput_per_min": round(len(results) / wall * 60, 1),
        "latency_s": {"min": secs[0], "p50": q(0.5), "p95": q(0.95), "max": secs[-1], "mean": round(statistics.mean(secs), 2)},
        "http_status": count("http_status"), "status": count("status"), "ai_status": count("ai_status"),
        "failures": sum(1 for r in results if r["http_status"] not in (200, 422)),
        "ai_cost_usd": round(sum(costs), 4), "ai_cost_per_routed_event_usd": round(sum(costs) / max(1, sum(c > 0 for c in costs)), 5),
        "sample_errors": [r["error"] for r in results if r["error"]][:5],
    }
    (out / f"{label}.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
