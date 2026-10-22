# Madison Automation Agent: ad check (Streamlit)

Paste one ad, pick the channel it will run on, and get a plain-English verdict: ship, fix first, or do not publish; who owns it; what breaks the channel's rules (quoted); and a ready-to-use fix.
Optionally send it to the team as a HubSpot task and Slack alert.

The judging runs in an n8n workflow with Claude Haiku 4.5 (INFO7375 Assignment 4). This app only collects input, validates it and presents the result.

- Entry point: `streamlit_app.py` · dependencies: `requirements.txt` · theme: `.streamlit/config.toml`
- **Secrets required** (Streamlit Community Cloud → app → Settings → Secrets): `MADISON_WEBHOOK_URL`, `MADISON_WEBHOOK_KEY`.
- Run locally: `MADISON_WEBHOOK_URL=... MADISON_WEBHOOK_KEY=... streamlit run streamlit_app.py`

The first version was a Gradio app for Hugging Face Spaces; Gradio Spaces became a paid (PRO) feature, so the interface was moved to Streamlit Community Cloud (free). The Gradio version is kept for reference.
