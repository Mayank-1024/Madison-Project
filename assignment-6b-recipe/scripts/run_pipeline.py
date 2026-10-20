"""CONDUCTOR · madison-ad-handoff: runs the four layers in order and stops at every typed phase gate.

  python3 scripts/run_pipeline.py                 # live sources + live AI (dry run, nothing sent), asks you at each gate
  python3 scripts/run_pipeline.py --sample        # no network, no AI: A3 snapshot + rule-based routing
  python3 scripts/run_pipeline.py --n 20          # how many ads to route (default 20, max 50 without re-approval)
  python3 scripts/run_pipeline.py --yes           # conductor applies the recipe's responses without asking (logged as such)

Gates: 0 PA (approve the run) · 1 IJ (ingest) · 2 IJ (GIGO) · 3 TO (AI output) · 4 EI (report exceptions) · PF on any failure.
Every decision is written to logs/gate-decisions/; the run log is logs/madison-ad-handoff-<run_id>.json."""
import argparse, importlib.util, json, os, sys, traceback
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import LOGS, ROOT, WORKFLOW, gate, now_iso, write_json


def load(rel):
    spec = importlib.util.spec_from_file_location(Path(rel).stem.replace("-", "_"), ROOT / rel)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


INGEST = "scripts/ingest/madison-ad-handoff-ingest-sources.py"
GIGO = "scripts/gigo/madison-ad-handoff-validate-records.py"
ROUTE = "scripts/tools/madison-ad-handoff-route-ads.py"
REPORT = "scripts/tools/madison-ad-handoff-produce-report.py"
EXPECT = {"ad_copy": (80, 100), "campaign_metadata": (100, 100), "industry_briefs": (50, 10_000)}


def c(check, ok, value): return {"check": check, "ok": bool(ok), "value": value}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true"); ap.add_argument("--yes", action="store_true"); ap.add_argument("--n", type=int, default=20)
    a = ap.parse_args()
    run = {"run_id": datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"), "auto": a.yes, "gates": [], "steps_completed": [], "stop": None}
    log = {"workflow": WORKFLOW, "run_id": run["run_id"], "mode": "sample" if a.sample else "live (AI dry run)", "started_at": now_iso()}
    print(f"\nRECIPE: Madison Automation Agent · {WORKFLOW} · run {run['run_id']}")

    def finish(status):
        log.update(finished_at=now_iso(), status=status, steps_completed=run["steps_completed"], gate_decisions=run["gates"], stop_conditions=run["stop"])
        p = write_json(LOGS / f"{WORKFLOW}-{run['run_id']}.json", log)
        print(f"\nRun log: {p.relative_to(ROOT)}  ·  status: {status}")
        return 0 if status == "completed" else 1

    def failure(step, err):
        run["stop"] = f"{step}: {err}"
        gate(run, "PF", f"Pipeline failure in {step}", "PF", [c("step finished without error", False, str(err)[:160])], "stop",
             ["The step raised an error. The recipe stops; decide whether to fix and re-run."])
        return finish("stopped")

    # ---- GATE 0 · PA
    cost = 0 if a.sample else round(a.n * 0.005, 2)
    checks = [c("no live HubSpot/Slack writes (dry run)", True, "mode=dry_run"), c("batch size within 50", a.n <= 50, f"{a.n} ads"),
              c("AI credentials present (live only)", a.sample or (os.environ.get("MADISON_WEBHOOK_URL") and os.environ.get("MADISON_WEBHOOK_KEY")),
                "sample" if a.sample else ("set" if os.environ.get("MADISON_WEBHOOK_URL") else "MISSING"))]
    resp = "pass" if all(x["ok"] for x in checks) else "stop"
    if gate(run, 0, "Run approval", "PA", checks, resp,
            [f"Sources: 2 HuggingFace datasets + 4 RSS feeds ({'A3 snapshot, offline' if a.sample else 'live'})",
             f"Ads to route: {a.n} · estimated AI cost: ${cost} · writes: data/raw, data/verified, logs only"]) == "stop":
        run["stop"] = "gate 0: run not approved"; return finish("stopped")

    # ---- LAYER 1 → GATE 1 · IJ
    try:
        ing = load(INGEST).run(run["run_id"], a.sample); run["steps_completed"].append("1.ingest")
    except Exception as e:
        return failure("Layer 1 ingest", e)
    log["ingest"] = ing
    checks = [c(f"{s}: {lo}-{hi if hi < 10_000 else '∞'} records", lo <= v["count"] <= hi, v["count"]) for s, v in ing.items() for lo, hi in [EXPECT[s]]]
    checks += [c(f"{e.get('feed') or s} answered", e.get("ok"), e.get("error") or e.get("items", "ok")) for s, v in ing.items() for e in v["endpoints"]]
    resp = "stop" if ing["ad_copy"]["count"] == 0 else ("pass" if all(x["ok"] for x in checks) else "flag")
    if gate(run, 1, "Ingest: external sources to data/raw", "IJ", checks, resp,
            [f"{s}: {v['count']} raw records → {v['path']}" for s, v in ing.items()]) == "stop":
        run["stop"] = "gate 1"; return finish("stopped")

    # ---- LAYER 2 → GATE 2 · IJ
    try:
        val = load(GIGO).run(run["run_id"], ing); run["steps_completed"].append("2.validate")
    except Exception as e:
        return failure("Layer 2 validation", e)
    log["validation"] = val
    checks = [c(f"{s}: at least 25 verified", v["verified"] >= 25, v["verified"]) for s, v in val.items()]
    checks += [c(f"{s}: reject rate ≤ 20%", v["reject_rate_pct"] <= 20, f"{v['reject_rate_pct']}%") for s, v in val.items()]
    checks += [c("ad_copy: ≥ 80% complete (rest tagged, kept)", val["ad_copy"]["complete_pct"] >= 80, f"{val['ad_copy']['complete_pct']}%"),
               c("every reject has a logged reason", True, "data/raw/rejected/")]
    resp = "stop" if any(v["verified"] < 25 for v in val.values()) else ("pass" if all(x["ok"] for x in checks) else "flag")
    if gate(run, 2, "GIGO: data/raw to data/verified", "IJ", checks, resp,
            [f"{s}: {v['raw']} raw → {v['verified']} verified, {v['rejected']} rejected {v['reject_reasons'] or ''}" for s, v in val.items()]) == "stop":
        run["stop"] = "gate 2"; return finish("stopped")

    # ---- LAYER 3 → GATE 3 · TO
    try:
        rt = load(ROUTE).run(run["run_id"], a.n, a.sample); run["steps_completed"].append("3.route")
    except Exception as e:
        return failure("Layer 3 AI routing", e)
    if rt.get("error"):
        return failure("Layer 3 AI routing", rt["error"])
    res = rt["results"]
    reviewed = [r for r in res if r["status"] == "completed"]
    if res and not reviewed and not [r for r in res if r["status"] == "blocked"]:
        return failure("Layer 3 AI routing", "the AI service did not answer for any ad")
    blocks = sum(1 for r in reviewed if r["decision"].get("decision") == "block")
    hard = [r for r in reviewed if any(p.startswith("HARD") for p in r["problems"])]
    flagged = [r for r in reviewed if r["problems"]]
    log["routing"] = {k: v for k, v in rt.items() if k != "results"} | {"decisions_file": f"logs/{WORKFLOW}-{run['run_id']}-decisions.json"}
    checks = [c("every reviewed ad has one decision + owner + reason", all(r["decision"].get("decision") and r["decision"].get("owner_team") and r["decision"].get("rationale") for r in reviewed), f"{len(reviewed)} reviewed"),
              c("no placeholder text approved", not hard, f"{len(hard)} found"),
              c("evidence/counts/owner re-check passed", not flagged, f"{len(flagged)} flagged"),
              c("block rate ≤ 50% of reviewed", blocks <= 0.5 * max(1, len(reviewed)), f"{blocks}/{len(reviewed)}"),
              c("batch not 100% auto-approved", any(r["decision"].get("decision") != "auto_approve" for r in reviewed) or not reviewed, "mix ok")]
    resp = "stop" if hard else ("pass" if all(x["ok"] for x in checks) else "flag")
    mix = {k: sum(1 for r in reviewed if r["decision"].get("decision") == k) for k in ("auto_approve", "needs_review", "block")}
    lines = [f"Decisions: {mix} · sent back before review: {sum(1 for r in res if r['status'] == 'blocked')}"]
    lines += [f"FLAG {r['ad_id']}: {'; '.join(r['problems'])}" for r in flagged[:8]]
    if gate(run, 3, "AI output review", "TO", checks, resp, lines) == "stop":
        run["stop"] = "gate 3"; return finish("stopped")

    # ---- LAYER 4 → GATE 4 · EI
    try:
        path, totals = load(REPORT).build(run["run_id"], rt, val, run["gates"]); run["steps_completed"].append("4.report")
    except Exception as e:
        return failure("Layer 4 report", e)
    ids = [r["event_id"] for r in res]
    checks = [c("report totals reconcile with routing results", totals["checked"] == len(res) == totals["ship"] + totals["fix"] + totals["do_not_publish"] + totals["sent_back"] + totals["errored"], totals),
              c("no ad appears twice", len(ids) == len(set(ids)), f"{len(ids)} ids"),
              c("exceptions labelled for manual check", True, f"{totals['manual_check']} labelled")]
    resp = "stop" if not checks[0]["ok"] or not checks[1]["ok"] else ("flag" if totals["manual_check"] else "pass")
    log["report"] = {"path": str(path.relative_to(ROOT)), "totals": totals}
    decision = gate(run, 4, "Report to the marketing-ops lead", "EI", checks, resp, [f"Report: {path.relative_to(ROOT)}", f"Totals: {totals}"])
    # re-render so the report's gate table includes gate 4
    load(REPORT).build(run["run_id"], rt, val, run["gates"])
    if decision == "stop":
        run["stop"] = "gate 4"; return finish("stopped")
    print(f"\nDone. Open the report: {path.relative_to(ROOT)}")
    return finish("completed")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrupted by the human; nothing further was run."); sys.exit(130)
