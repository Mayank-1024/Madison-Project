# Assignment 6A: Interface (Path A)

A Gradio web app that wraps the Action Layer for a non-technical user: paste one ad, pick its channel, and get a plain-English verdict
(*Good to ship* / *Fix before it ships* / *Do not publish*), the owning team, quoted problems, a rewrite, and the task text.
**Send to my team** is off by default (preview only); ticking it creates the real HubSpot task and Slack alert.

- Calls the n8n webhook from Assignment 4; the Claude key stays inside n8n. Secrets: `MADISON_WEBHOOK_URL`, `MADISON_WEBHOOK_KEY`.
- Plain-English errors for missing fields, oversized text, bad numbers, timeouts, auth and gatekeeper rejections; 15 checks per visitor per hour.
- Deploy: see `DEPLOY.md` (Hugging Face Spaces). User testing kit: `testing/USER_TEST_KIT.md`. Local test double: `_build/mock_webhook.py`.

*Status (2026-10-20): built and tested locally; public deployment and user testing in progress.*
