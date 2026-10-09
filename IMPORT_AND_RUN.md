# Import & run — Madison Action Layer v2

## A. Credentials (n8n → Overview → Credentials → Create)
| Credential type | Used by | Notes |
|---|---|---|
| **Anthropic** | Routing Agent, Insights Agent | your existing key |
| **Slack API** | Post Slack Alert, Post Slack Digest, error handler | bot token `xoxb-…` from a workspace you admin (see SETUP_ACCOUNTS.md §2) |
| **HubSpot App Token** | Create HubSpot Task | private app token |
| **Google Sheets OAuth2 API** / **Gmail OAuth2** | Append to Google Sheet / Email Report | personal Gmail account |
| **Header Auth** | Madison Variant In (webhook) | Name: `X-Madison-Key` · Value: run `openssl rand -hex 24` in Terminal and paste the output. Keep that value — the load test needs it. |

## B. Import (≈5 min)
1. Workflows → **Import from File** → `workflow_v2_error_handler.json` → open **Alert #campaign-urgent** → pick the Slack credential → Save.
2. Import `workflow_v2.json`. Open each node with a ⚠️ and pick its credential:
   Madison Variant In (Header Auth) · Routing Agent + Insights Agent (Anthropic) · Create HubSpot Task (HubSpot) · Post Slack Alert + Post Slack Digest (Slack) · Email Report (Gmail) · Append to Google Sheet (Google Sheets → choose your **Madison Action Log** sheet + its first tab).
   ⚠️ Picking the document resets **Mapping Column Mode** to *Map Each Column Manually* — set it back to **Map Automatically** (otherwise: "At least one value has to be added under 'Values to Send'").
3. **Report Settings** node → set `report_email` to your address.
4. Workflow ⋯ → **Settings → Error workflow** → choose *Madison Action Layer v2 – Error Handler* → Save.
5. In Slack, invite the bot to the 3 channels: in each channel type `/invite @<bot name>` (needed for private channels; harmless for public).

## C. First run
1. Click **Run Once: Setup** → execute (creates the `madison_action_log` data table; safe to re-run).
2. **Publish** the workflow (top right) so the production webhook is live. Copy the **Production URL** from *Madison Variant In*.
3. In Terminal (from `Assignment_4/scale_test/`):
   ```bash
   export MADISON_WEBHOOK_URL="<production URL>"
   export MADISON_WEBHOOK_KEY="<the Header Auth value>"
   python3 make_events.py --n 1 --run-id smoke-1
   python3 loadtest.py events_smoke-1.jsonl --concurrency 1
   ```
   Expect `"status": {"completed": 1}`, a Slack message, a HubSpot task, and a row in the data table.
4. Send me the printed summary (and a screenshot of any red node). Then we run the scale tests.

## D. Scale-test plan (run in this order, ~$1–2 of Claude credits total)
| Step | Command | What it measures |
|---|---|---|
| 1 | `--n 1 --run-id scale-1` · concurrency 1 | single-request latency |
| 2 | `--n 10 --run-id scale-10` · concurrency 1 | sequential baseline |
| 3 | `--n 10 --run-id scale-10p` · concurrency 10 | parallel burst |
| 4 | `--n 50 --run-id scale-50` · concurrency 10 | live Slack + HubSpot under load |
| 5 | `--n 100 --run-id scale-100 --dry-run` · concurrency 20 | AI + gatekeeper throughput (no Slack/HubSpot spam) |
| 6 | `--n 200 --run-id scale-200 --dry-run` · concurrency 50 | find the breaking point on the 1 vCPU VPS |

After each step: run **Build Run Report (manual)** with `run_id` = that step's id to produce the email, Slack digest, Sheet rows and HTML report (that's your output gallery).
