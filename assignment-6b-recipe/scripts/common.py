"""Shared paths, config and gate recording for the madison-ad-handoff pipeline (stdlib only)."""
import json, os, pathlib, sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORKFLOW = "madison-ad-handoff"
SOURCES = ["ad_copy", "campaign_metadata", "industry_briefs"]
RAW, VERIFIED, REJECTED = ROOT / "data/raw", ROOT / "data/verified", ROOT / "data/raw/rejected"
LOGS, REPORTS, GATES = ROOT / "logs", ROOT / "logs/reports", ROOT / "logs/gate-decisions"
CONFIG = json.loads((ROOT / "brand_config.json").read_text())


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_json(path, obj):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False))
    return path


def read_json(path):
    return json.loads(pathlib.Path(path).read_text())


def gate(run, n, name, judgment, checks, auto_response, summary_lines):
    """Show the gate evidence, ask the human for the typed judgment, record the decision.
    auto_response: 'pass' | 'flag' | 'stop' computed from the checks; the human can override (and that is logged)."""
    bar = "=" * 72
    print(f"\n{bar}\nPHASE GATE {n} | {name} | Judgment type: {judgment} ({JUDGMENT[judgment]})\n{bar}")
    for line in summary_lines:
        print("  " + line)
    print("\n  Checks:")
    for c in checks:
        print(f"   [{'PASS' if c['ok'] else 'FAIL'}] {c['check']}  ({c['value']})")
    print(f"\n  Recipe response: {auto_response.upper()}")
    if run["auto"]:
        decision = "approve" if auto_response == "pass" else ("stop" if auto_response == "stop" else "approve")
        note = f"--yes mode: conductor applied recipe response '{auto_response}'"
    else:
        default = "stop" if auto_response == "stop" else "approve"
        ans = input(f"  Your decision [approve / stop] (Enter = {default}): ").strip().lower() or default
        decision = "stop" if ans.startswith("s") else "approve"
        note = input("  Note for the log (optional): ").strip()
    rec = {"workflow": WORKFLOW, "run_id": run["run_id"], "gate": n, "name": name, "judgment_type": judgment,
           "recipe_response": auto_response, "decision": decision, "note": note, "checks": checks, "decided_at": now_iso(),
           "decided_by": "conductor (--yes)" if run["auto"] else "human"}
    write_json(GATES / f"{run['run_id']}-gate{n}.json", rec)
    run["gates"].append(rec)
    if decision == "stop":
        print(f"\n  STOPPED at gate {n}. Decision recorded in logs/gate-decisions/.")
    return decision


JUDGMENT = {"PA": "Pipeline Approval", "PF": "Pipeline Failure", "TO": "Tool Output Review",
            "IJ": "Ingest Judgment", "EI": "Exception Intervention"}
