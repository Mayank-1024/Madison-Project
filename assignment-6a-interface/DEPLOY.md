# Deploy to Hugging Face Spaces (about 10 minutes)

1. **Account:** huggingface.co → Sign up (free). Confirm your email.
2. **New Space:** your avatar → **New Space**
   - Space name: `madison-ad-check` · License: MIT · SDK: **Gradio** · Template: Blank · Hardware: **CPU basic (free)** · Visibility: **Public**
   - Create Space.
3. **Upload files:** in the Space, **Files → Add file → Upload files**, drag in the 3 files from `Assignment_6A/app/`: `app.py`, `requirements.txt`, `README.md` (replace the existing README). Commit.
4. **Secrets:** **Settings → Variables and secrets → New secret** (twice):
   - `MADISON_WEBHOOK_URL` = your n8n Production URL `https://<your-n8n-domain>/webhook/madison/variant`
   - `MADISON_WEBHOOK_KEY` = the value of your **Madison Webhook Key** credential in n8n
   (Rotate the key first, since the old one was pasted in chat: `openssl rand -hex 24` → update the n8n credential → use the new value here.)
5. The Space rebuilds (about 2 min). Open the **App** tab. Your public URL is `https://huggingface.co/spaces/<your-username>/madison-ad-check`.
6. **Smoke test:** click the *Google Ads: knit sweater* example → **Check this ad** → a verdict card appears in about 10 s.
   Then tick **Send to my team** once and confirm a HubSpot task and Slack alert appear.
7. In n8n make sure **Madison Action Layer v2** is **Published** (the webhook must be live for the URL to work at grading time).

**Cost guard:** each check is about $0.005. The app caps 15 checks per visitor per hour and 300 per day. Optionally set a monthly spend limit in console.anthropic.com → Limits.

If the build fails, open the Space's **Logs** tab and send me the last 20 lines.
