import http.server, json, time
class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        b = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        if self.headers.get('X-Madison-Key') != 'k': return self._send(403, {"message": "Authorization data is wrong!"})
        time.sleep(1.2)
        gate = [r for r, ok in [("missing_headline", b.get("headline")), ("missing_cta", b.get("cta"))] if not ok]
        if gate: return self._send(422, {"status": "blocked", "decision": "block", "detail_json": json.dumps({"gate_reasons": gate})})
        ph = "[" in b["cta"]
        d = {"decision": "block" if ph else "needs_review", "priority": "high" if ph else "normal", "owner_team": "Brand & Legal Review" if ph else "Paid Media",
             "slack_channel": "campaign-review", "channel_fit": {"score": 2, "note": "Headline is 53 characters (limit 30)."},
             "risk_flags": [{"type": "placeholder_text", "severity": "high", "evidence": "[website link]"}] if ph else [{"type": "unverifiable_claim", "severity": "medium", "evidence": "Unbeatable comfort"}],
             "rationale": "Strong copy but the headline breaks the Google Ads limit.", "suggested_fix": "Headline: 'Chunky Knit Sweater, Cozy & Warm' (30 chars). CTA: 'Shop now'.",
             "hubspot_task": {"title": "Trim Google Ads headline for Innovate Industries", "body": "Shorten headline to 30 chars.\nRemove 'unbeatable'.", "due_in_days": 3},
             "slack_message": "Needs a trim.", "confidence": 0.74}
        self._send(200, {"status": "completed", "decision": d["decision"], "ai_status": "ai", "hubspot_task_id": "405887" if b["mode"] == "live" else "",
                         "detail_json": json.dumps({"decision": d}), "cost_usd": 0.0045, "latency_ms": 1200})
    def _send(self, code, obj):
        self.send_response(code); self.send_header('Content-Type', 'application/json'); self.end_headers(); self.wfile.write(json.dumps(obj).encode())
    def log_message(self, *a): pass
http.server.ThreadingHTTPServer(('127.0.0.1', 8766), H).serve_forever()
