---
title: Madison Automation Agent
emoji: 🗂️
colorFrom: red
colorTo: yellow
sdk: gradio
sdk_version: 6.30.0
app_file: app.py
python_version: "3.12"
pinned: false
short_description: Check an ad against its channel's rules and hand it off
---

# Madison Automation Agent: ad check

Paste one ad, pick the channel it will run on, and get a plain-English verdict: ship, fix first, or do not publish; who owns it; what breaks the channel's rules (quoted); and a ready-to-use fix.
Optionally send it to the team as a HubSpot task and Slack alert.

The judging runs in an n8n workflow with Claude Haiku 4.5 (INFO7375 Assignment 4). This Space only collects input, validates it and presents the result.

**Secrets required (Settings → Variables and secrets):** `MADISON_WEBHOOK_URL`, `MADISON_WEBHOOK_KEY`.
