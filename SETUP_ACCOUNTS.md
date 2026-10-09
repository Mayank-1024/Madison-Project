# Account & credential setup (do these once, ~45 min total)

Rule: every key/token goes **only** into n8n → *Credentials* (Overview → Credentials → Create). Never paste a key into a node field, a chat, or a file. Use the exact credential names below so the imported workflow finds them.

## 1. Anthropic (Claude) — you already have a key
Just add it in n8n → Credentials → **Anthropic** (name `Anthropic – Madison`) and note your rate-limit tier (Console → Limits).

<details><summary>New-account steps (not needed)</summary>

1. Go to console.anthropic.com → sign up → **Billing** → add $10 credits (testing needs ~$5–6).
2. **API Keys** → *Create Key* → name it `n8n-madison`.
3. n8n → Credentials → **Anthropic** → paste key → Save. Name: `Anthropic – Madison`.
4. Note your **rate-limit tier** (Console → Limits) — we'll cite it in the scale test.
</details>

## 2. Slack — ~10 min
1. Use your existing Slack login, but create a **new free workspace** you own (e.g. `madison-action-layer`) — you must be admin to install a bot; school/work workspaces usually block custom apps.
2. Create 3 public channels: `#campaign-urgent`, `#campaign-review`, `#campaign-digest`.
3. api.slack.com/apps → *Create New App* → *From scratch* → pick the workspace.
4. **OAuth & Permissions** → *Bot Token Scopes*: `chat:write`, `chat:write.public`, `channels:read`.
5. *Install to Workspace* → copy the **Bot User OAuth Token** (`xoxb-…`).
6. n8n → Credentials → **Slack API** → Access Token = that token → Save. Name: `Slack – Madison Bot`.

## 3. HubSpot — ~10 min
1. hubspot.com → free CRM account.
2. Settings (gear) → **Integrations → Private Apps** (in newer accounts: *Development → Legacy apps → Private*) → *Create*.
3. Scopes: tasks read + write if listed (`crm.objects.tasks…`); otherwise `crm.objects.contacts.read` + `crm.objects.contacts.write`.
4. Create → copy the access token.
5. n8n → Credentials → **HubSpot App Token** → paste → Save. Name: `HubSpot – Madison`. (The credential test tells you if a scope is missing.)

## 4. Google (Sheets + Gmail) — ~15–20 min
Your **personal Google account** is all you need (no new account, no billing). Don't use @northeastern.edu — university admins often block custom OAuth apps. Self-hosted n8n just needs its own OAuth client:
1. console.cloud.google.com → new project `madison-n8n`.
2. **APIs & Services → Library** → enable *Google Sheets API*, *Google Drive API*, *Gmail API*.
3. **OAuth consent screen** → External → app name `Madison n8n` → add **your Gmail as a Test user**.
4. **Credentials → Create credentials → OAuth client ID** → *Web application* → Authorized redirect URI = the "OAuth Redirect URL" shown in the n8n Google credential form (looks like `https://<your-n8n-domain>/rest/oauth2-credential/callback`).
5. n8n → Credentials → **Google Sheets OAuth2 API** → paste Client ID/Secret → *Sign in with Google* → Save. Name: `Google Sheets – Madison`.
6. Same client for **Gmail OAuth2** → Name: `Gmail – Madison`.
7. Create an empty Google Sheet named **Madison Action Log** — send me nothing; you'll pick it from a dropdown after import.

## When done, tell me
- ✅/❌ for each of the 4 credentials (and any error text).
- Your Anthropic rate-limit tier.
- The email address the run report should go to.
