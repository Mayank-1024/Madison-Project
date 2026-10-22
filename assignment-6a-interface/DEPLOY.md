# Deploy to Streamlit Community Cloud (free, about 10 minutes)

Hugging Face now charges for Gradio Spaces, so the app runs on Streamlit Community Cloud instead (named in the brief).

1. Go to **share.streamlit.io** → **Continue with GitHub** → sign in as `Mayank-1024` → authorize Streamlit.
2. **Create app** (top right) → **Deploy a public app from GitHub**.
   - Repository: `Mayank-1024/Madison-Project` · Branch: `main`
   - Main file path: `assignment-6a-interface/app/streamlit_app.py`
   - App URL: pick a name, e.g. `madison-ad-check` → `https://madison-ad-check.streamlit.app`
3. **Advanced settings** → Python version **3.12** → in **Secrets** paste (TOML, keep the quotes):
   ```
   MADISON_WEBHOOK_URL = "https://<your-n8n-domain>/webhook/madison/variant"
   MADISON_WEBHOOK_KEY = "<the new key from your n8n 'Madison Webhook Key' credential>"
   ```
   Save → **Deploy**. The first build takes 2-3 minutes.
4. **Smoke test:** click *Google Ads: knit sweater* → **Check this ad** → a verdict card appears in about 10 s.
   Then tick **Send to my team** once and confirm a HubSpot task and Slack alert appear.
5. In n8n make sure **Madison Action Layer v2** stays **Published** (the webhook must be live for the URL to work at grading time).

**Sleeping:** Community Cloud puts apps to sleep after a long stretch with no visitors. A visitor then sees "This app has gone to sleep" and clicks **Yes, get this app back up** (about 30 s). Open the URL yourself shortly before submitting and before each user test.

**Cost guard:** each check is about $0.005. The app caps 15 checks per visitor per hour and 300 per day. Optionally set a monthly spend limit in console.anthropic.com → Limits.

If the build fails, click **Manage app** (bottom right of the app) and send me the last 20 lines of the log.
