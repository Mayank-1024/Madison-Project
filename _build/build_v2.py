"""Assembles workflow_v2.json (main) and workflow_v2_error_handler.json from the Code-node sources in js/.
No credentials or secrets are written: credential-backed nodes are bound to credentials after import."""
import json, uuid, pathlib

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE.parent
js = lambda f: (HERE / "js" / f).read_text().strip()

def builder():
    nodes, conns = [], {}
    def node(name, type_, ver, pos, params, **extra):
        n = {"parameters": params, "id": str(uuid.uuid4()), "name": name, "type": type_, "typeVersion": ver, "position": pos}
        n.update(extra); nodes.append(n); return name
    def link(a, b, out=0, idx=0):
        m = conns.setdefault(a, {"main": []})["main"]
        while len(m) <= out: m.append([])
        m[out].append({"node": b, "type": "main", "index": idx})
    return nodes, conns, node, link

RETRY = {"retryOnFail": True, "maxTries": 3, "waitBetweenTries": 5000}
TABLE = {"__rl": True, "mode": "name", "value": "madison_action_log"}

def code(node, name, f, pos, **kw):
    return node(name, "n8n-nodes-base.code", 2, pos, {"jsCode": js(f)}, **kw)

def if_true(node, name, left, pos, kind="boolean"):
    op = {"type": "boolean", "operation": "true", "singleValue": True} if kind == "boolean" else {"type": "string", "operation": "notEmpty", "singleValue": True}
    return node(name, "n8n-nodes-base.if", 2.2, pos, {"conditions": {
        "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose", "version": 2},
        "conditions": [{"id": str(uuid.uuid4()), "leftValue": left, "rightValue": "", "operator": op}],
        "combinator": "and"}, "options": {}})

def http(node, name, url, cred, body_expr, pos, timeout=30000):
    return node(name, "n8n-nodes-base.httpRequest", 4.2, pos, {
        "method": "POST", "url": url, "authentication": "predefinedCredentialType", "nodeCredentialType": cred,
        **({"sendHeaders": True, "headerParameters": {"parameters": [{"name": "anthropic-version", "value": "2023-06-01"}]}} if cred == "anthropicApi" else {}),
        "sendBody": True, "specifyBody": "json", "jsonBody": body_expr, "options": {"timeout": timeout}},
        onError="continueRegularOutput", **RETRY)

def sticky(node, text, pos, w, h, color):
    node(f"Note {uuid.uuid4().hex[:6]}", "n8n-nodes-base.stickyNote", 1, pos, {"content": text, "width": w, "height": h, "color": color})

# ---------------------------------------------------------------- main workflow
nodes, conns, node, link = builder()
sticky(node, "## ① Gatekeeper — no AI\nValidates every Madison variant, blocks Popper failures and broken payloads, and stops duplicates with the `brief_id:variant_id` idempotency key.", [-40, -260], 900, 760, 7)
sticky(node, "## ② Routing Agent — Claude Haiku 4.5\nDecides priority, owner, channel fit and risks, and writes the task + alert. Strict JSON schema · 3 retries · any bad answer → rule-based fallback.", [900, -260], 900, 760, 4)
sticky(node, "## ③ Execution Agent\nCreates the HubSpot task, posts the Slack alert (3 retries each), logs every outcome, answers Madison. `dry_run` events skip external actions (for load tests).", [1840, -260], 1160, 760, 6)
sticky(node, "## ④ Run report — Insights Agent\nDaily (or on demand): reads the action log → Claude finds patterns → HTML email + Slack digest + Google Sheet + downloadable report.", [-40, 560], 2100, 520, 5)
sticky(node, "## One-time setup\nRun once after import: creates the `madison_action_log` data table.", [2140, 560], 520, 300, 3)

node("Madison Variant In", "n8n-nodes-base.webhook", 2, [0, 120], {"httpMethod": "POST", "path": "madison/variant", "authentication": "headerAuth", "responseMode": "responseNode", "options": {}}, webhookId=str(uuid.uuid4()))
code(node, "Gatekeeper: Validate & Normalize", "gatekeeper.js", [220, 120])
if_true(node, "Passed Gatekeeper?", "={{ $json.gate_passed }}", [440, 120])
code(node, "Blocked Outcome", "blocked.js", [660, 320])
node("Check Already Processed", "n8n-nodes-base.dataTable", 1.1, [660, 40], {"resource": "row", "operation": "get", "dataTableId": TABLE, "matchType": "anyCondition",
     "filters": {"conditions": [{"keyName": "idempotency_key", "condition": "eq", "keyValue": "={{ $json.idempotency_key }}"}]}, "limit": 1}, alwaysOutputData=True, onError="continueRegularOutput")
if_true(node, "Already Processed?", "={{ $json.idempotency_key }}", [880, 40], kind="string")
code(node, "Duplicate Outcome", "duplicate.js", [1100, -120])
code(node, "Build Claude Request", "build_request.js", [1100, 100])
http(node, "Routing Agent (Claude Haiku 4.5)", "https://api.anthropic.com/v1/messages", "anthropicApi", "={{ JSON.stringify($json.request_body) }}", [1320, 100], timeout=60000)
code(node, "Validate AI Decision", "parse_decision.js", [1540, 100])
if_true(node, "AI Decision Valid?", "={{ $json.ai_ok }}", [1760, 100])
code(node, "Rule-based Fallback Router", "fallback.js", [1760, 320])
code(node, "Plan Actions", "plan_actions.js", [1980, 100])
if_true(node, "Live Mode?", "={{ $json.live }}", [2180, 100])
http(node, "Create HubSpot Task", "https://api.hubapi.com/crm/v3/objects/tasks", "hubspotAppToken", "={{ JSON.stringify($json.hubspot_payload) }}", [2400, 0])
http(node, "Post Slack Alert", "https://slack.com/api/chat.postMessage", "slackApi",
     "={{ JSON.stringify($('Plan Actions').first().json.slack_payload).replace('__TASK_ID__', $json.id ? '#' + $json.id : 'not created') }}", [2620, 0])
code(node, "Assemble Outcome", "assemble.js", [2620, 220])
node("Log to Action Log", "n8n-nodes-base.dataTable", 1.1, [2820, 220], {"resource": "row", "operation": "insert", "dataTableId": TABLE,
     "columns": {"mappingMode": "autoMapInputData", "value": {}, "matchingColumns": [], "schema": []}, "options": {}}, onError="continueRegularOutput")
node("Respond to Madison", "n8n-nodes-base.respondToWebhook", 1.4, [2900, -120], {"respondWith": "firstIncomingItem",
     "options": {"responseCode": "={{ $json.status === 'blocked' ? 422 : 200 }}"}})

link("Madison Variant In", "Gatekeeper: Validate & Normalize")
link("Gatekeeper: Validate & Normalize", "Passed Gatekeeper?")
link("Passed Gatekeeper?", "Check Already Processed", 0); link("Passed Gatekeeper?", "Blocked Outcome", 1)
link("Check Already Processed", "Already Processed?")
link("Already Processed?", "Duplicate Outcome", 0); link("Already Processed?", "Build Claude Request", 1)
link("Build Claude Request", "Routing Agent (Claude Haiku 4.5)")
link("Routing Agent (Claude Haiku 4.5)", "Validate AI Decision")
link("Validate AI Decision", "AI Decision Valid?")
link("AI Decision Valid?", "Plan Actions", 0); link("AI Decision Valid?", "Rule-based Fallback Router", 1)
link("Rule-based Fallback Router", "Plan Actions")
link("Plan Actions", "Live Mode?")
link("Live Mode?", "Create HubSpot Task", 0); link("Live Mode?", "Assemble Outcome", 1)
link("Create HubSpot Task", "Post Slack Alert")
link("Post Slack Alert", "Assemble Outcome")
link("Assemble Outcome", "Log to Action Log")
link("Blocked Outcome", "Log to Action Log")
link("Log to Action Log", "Respond to Madison")
link("Duplicate Outcome", "Respond to Madison")

# report flow
node("Build Run Report (manual)", "n8n-nodes-base.manualTrigger", 1, [0, 760], {})
node("Daily 6 pm Digest", "n8n-nodes-base.scheduleTrigger", 1.2, [0, 940], {"rule": {"interval": [{"field": "cronExpression", "expression": "0 18 * * *"}]}})
node("Report Settings", "n8n-nodes-base.set", 3.4, [220, 840], {"assignments": {"assignments": [
    {"id": str(uuid.uuid4()), "name": "run_id", "value": "", "type": "string"},
    {"id": str(uuid.uuid4()), "name": "lookback_hours", "value": 24, "type": "number"},
    {"id": str(uuid.uuid4()), "name": "report_email", "value": "you@example.com", "type": "string"}]}, "options": {}})
node("Read Action Log", "n8n-nodes-base.dataTable", 1.1, [440, 840], {"resource": "row", "operation": "get", "dataTableId": TABLE, "returnAll": True}, alwaysOutputData=True)
code(node, "Aggregate Run Stats", "aggregate.js", [660, 840])
code(node, "Build Insights Request", "insights_request.js", [880, 840])
http(node, "Insights Agent (Claude Haiku 4.5)", "https://api.anthropic.com/v1/messages", "anthropicApi", "={{ JSON.stringify($json.request_body) }}", [1100, 840], timeout=60000)
code(node, "Build Report", "build_report.js", [1320, 840])
node("Email Report (Gmail)", "n8n-nodes-base.gmail", 2.1, [1560, 660], {"operation": "send", "sendTo": "={{ $('Report Settings').first().json.report_email }}",
     "subject": "={{ $json.subject }}", "emailType": "html", "message": "={{ $json.html }}", "options": {"appendAttribution": False}}, onError="continueRegularOutput", **RETRY)
http(node, "Post Slack Digest", "https://slack.com/api/chat.postMessage", "slackApi", "={{ JSON.stringify($json.slack_payload) }}", [1560, 800])
node("Save Report as HTML", "n8n-nodes-base.convertToFile", 1.1, [1560, 940], {"operation": "toText", "sourceProperty": "html", "options": {"fileName": "madison_run_report.html"}})
code(node, "Rows for Sheet", "sheet_rows.js", [1780, 1000])
node("Append to Google Sheet", "n8n-nodes-base.googleSheets", 4.7, [1980, 1000], {"operation": "append",
     "documentId": {"__rl": True, "mode": "list", "value": ""}, "sheetName": {"__rl": True, "mode": "list", "value": ""},
     "columns": {"mappingMode": "autoMapInputData", "value": {}, "matchingColumns": [], "schema": []}, "options": {}}, onError="continueRegularOutput", **RETRY)
for t in ["Build Run Report (manual)", "Daily 6 pm Digest"]: link(t, "Report Settings")
link("Report Settings", "Read Action Log"); link("Read Action Log", "Aggregate Run Stats")
link("Aggregate Run Stats", "Build Insights Request"); link("Build Insights Request", "Insights Agent (Claude Haiku 4.5)")
link("Insights Agent (Claude Haiku 4.5)", "Build Report")
for t in ["Email Report (Gmail)", "Post Slack Digest", "Save Report as HTML", "Rows for Sheet"]: link("Build Report", t)
link("Rows for Sheet", "Append to Google Sheet")

# one-time setup
COLS = [("idempotency_key", "string"), ("event_id", "string"), ("run_id", "string"), ("mode", "string"), ("status", "string"),
        ("decision", "string"), ("priority", "string"), ("owner_team", "string"), ("slack_channel", "string"), ("ai_status", "string"),
        ("risk_count", "number"), ("headline", "string"), ("summary", "string"), ("hubspot_task_id", "string"), ("slack_ok", "boolean"),
        ("cost_usd", "number"), ("latency_ms", "number"), ("detail_json", "string")]
node("Run Once: Setup", "n8n-nodes-base.manualTrigger", 1, [2200, 700], {})
node("Create Action Log Table", "n8n-nodes-base.dataTable", 1.1, [2420, 700], {"resource": "table", "operation": "create", "tableName": "madison_action_log",
     "columns": {"column": [{"name": n, "type": t} for n, t in COLS]}, "options": {"createIfNotExists": True}})
link("Run Once: Setup", "Create Action Log Table")

main = {"name": "Madison Action Layer v2 – Gatekeeper → Routing → Execution", "nodes": nodes, "connections": conns, "pinData": {},
        "settings": {"executionOrder": "v1"}, "active": False, "meta": {"templateCredsSetupCompleted": False}, "tags": []}
(OUT / "workflow_v2.json").write_text(json.dumps(main, indent=2, ensure_ascii=False))

# ---------------------------------------------------------------- error workflow
nodes, conns, node, link = builder()
node("On Workflow Error", "n8n-nodes-base.errorTrigger", 1, [0, 0], {})
code(node, "Format Failure Alert", "error_format.js", [220, 0])
http(node, "Alert #campaign-urgent", "https://slack.com/api/chat.postMessage", "slackApi", "={{ JSON.stringify($json.slack_payload) }}", [440, 0])
link("On Workflow Error", "Format Failure Alert"); link("Format Failure Alert", "Alert #campaign-urgent")
err = {"name": "Madison Action Layer v2 – Error Handler", "nodes": nodes, "connections": conns, "pinData": {}, "settings": {"executionOrder": "v1"}, "active": False, "tags": []}
(OUT / "workflow_v2_error_handler.json").write_text(json.dumps(err, indent=2, ensure_ascii=False))
print("main:", len(main["nodes"]), "nodes · error handler:", len(err["nodes"]), "nodes")
