"""Madison Automation Agent: public interface (Assignment 6A).

A marketing-ops lead pastes one ad, picks the channel it will run on, and gets a plain-English verdict:
ship / fix first / do not publish, who owns it, what breaks the channel's rules (quoted), and a rewrite.
The judging runs in the existing n8n workflow (A4); this app only collects input, checks it, and presents the result.

Secrets (set in Streamlit Community Cloud → app → Settings → Secrets, never in code):
  MADISON_WEBHOOK_URL   production URL of the n8n webhook (…/webhook/madison/variant)
  MADISON_WEBHOOK_KEY   value of the n8n Header Auth credential (sent as X-Madison-Key)
"""
import html, json, os, re, time, uuid
from collections import defaultdict, deque
from datetime import datetime, timezone

import requests
import streamlit as st

st.set_page_config(page_title="Madison Automation Agent: ad check", page_icon="🗂️", layout="wide")


def secret(name: str) -> str:
    try:
        return st.secrets.get(name, "") or os.environ.get(name, "")
    except Exception:  # no secrets file at all (local run)
        return os.environ.get(name, "")


WEBHOOK_URL = secret("MADISON_WEBHOOK_URL")
WEBHOOK_KEY = secret("MADISON_WEBHOOK_KEY")
TIMEOUT_S = 75
PER_VISITOR_PER_HOUR = 15
PER_DAY_TOTAL = 300

CHANNELS = {
    # channel: (campaign type sent to the checker, the rule shown to the user, headline limit or None)
    "Google Ads": ("Search", "Headline up to 30 characters, description up to 90. No emoji or hashtags.", 30),
    "Facebook": ("Social Media", "Hook in the first ~40 characters; text should still read well cut at ~125.", None),
    "Instagram": ("Social Media", "Hook in the first ~40 characters; hashtags are fine here.", None),
    "YouTube": ("Video", "Needs a spoken-style hook and a clear call-to-action.", None),
    "Email": ("Email", "The headline is the subject line: keep it under 60 characters. No hashtags.", 60),
    "Website": ("Display", "Clarity over hype.", None),
}

GATE_REASONS = {
    "missing_headline": "the headline is empty",
    "missing_body": "the body text is empty",
    "missing_cta": "the call-to-action is empty",
    "headline_too_long": "the headline is over 300 characters",
    "invalid_created_at": "the ad's creation date could not be read",
    "popper_quality_gate_failed": "the content writer's own quality check failed",
}


# ------------------------------------------------------------------ rate limiting (protects the AI budget; shared by all visitors)
@st.cache_resource
def _limits():
    return {"visits": defaultdict(deque), "day": {"date": None, "count": 0}}


def _allowed(visitor: str) -> str | None:
    lim = _limits()
    now = time.time()
    q = lim["visits"][visitor]
    while q and now - q[0] > 3600:
        q.popleft()
    today = datetime.now(timezone.utc).date()
    if lim["day"]["date"] != today:
        lim["day"].update(date=today, count=0)
    if len(q) >= PER_VISITOR_PER_HOUR:
        wait = int((3600 - (now - q[0])) // 60) + 1
        return f"You've checked {PER_VISITOR_PER_HOUR} ads in the last hour, which is this demo's limit. Please try again in about {wait} minutes."
    if lim["day"]["count"] >= PER_DAY_TOTAL:
        return "The demo has reached today's limit of checks. Please come back tomorrow."
    q.append(now)
    lim["day"]["count"] += 1
    return None


# ------------------------------------------------------------------ presentation helpers
e = html.escape


def card(kind: str, title: str, body_html: str) -> str:
    return f'<div class="m-card m-{kind}"><div class="m-title">{e(title)}</div>{body_html}</div>'


def problem(title: str, what: str, todo: str) -> str:
    return card("error", title, f"<p>{e(what)}</p><p class='m-todo'><b>What to do:</b> {e(todo)}</p>")


def headline_hint(headline: str, channel: str) -> str:
    n = len(headline or "")
    limit = CHANNELS[channel][2] if channel else None
    if not channel:
        return f"<span class='m-hint'>{n} characters. Pick a channel to see its limit.</span>"
    if limit and n > limit:
        return f"<span class='m-hint m-over'>{n} / {limit} characters: too long for {e(channel)}.</span>"
    if limit:
        return f"<span class='m-hint'>{n} / {limit} characters for {e(channel)}.</span>"
    return f"<span class='m-hint'>{n} characters. {e(CHANNELS[channel][1])}</span>"


VERDICT = {
    "auto_approve": ("ship", "Good to ship", "No serious problems found. Hand it off to the owning team when you're ready."),
    "needs_review": ("review", "Fix before it ships", "A person should look at this first. The problems and a fix are below."),
    "block": ("block", "Do not publish", "This ad has a serious problem (for example unfinished text) and must be fixed."),
}
PRIORITY = {"urgent": "Today", "high": "Within 1 day", "normal": "Within 3 days", "low": "This week"}
HANDOFF_VERB = {"auto_approve": "to publish", "needs_review": "to fix", "block": "to fix before anyone publishes it"}
# optional links shown after a hand-off (set as secrets; e.g. https://app.hubspot.com/tasks/<portal>/view/all/task/{id})
TASK_URL = secret("MADISON_HUBSPOT_TASK_URL")
SLACK_URL = secret("MADISON_SLACK_CHANNEL_URL")
SUGGESTED_HEADLINE = re.compile(r"Headline[^:]{0,24}:\s*(['\"“‘])(.+?)(?:\1|[”’])(?=[\s.,;()]|$)")


def own_counts(fix: str, channel: str) -> str:
    """The AI's character counts are not reliable, so count every suggested headline here (tester feedback, session 1)."""
    limit = CHANNELS.get(channel, ("", "", None))[2]
    if not limit:
        return ""
    notes = []
    for m in SUGGESTED_HEADLINE.finditer(fix or ""):
        n = len(m.group(2))
        verdict = f"fits the {limit}-character limit" if n <= limit else f"<b>still over</b> the {limit}-character limit"
        notes.append(f"“{e(m.group(2))}” is {n} characters: {verdict}.")
    return "<div class='m-count'><b>Counted by this app:</b> " + " ".join(notes) + "</div>" if notes else ""


def link(text: str, url: str) -> str:
    return f"<a href='{e(url)}' target='_blank'>{text}</a>" if url else text


def render_result(resp: dict, sent: bool, seconds: float, ad: dict) -> str:
    status = resp.get("status", "")
    if status == "duplicate":
        return card("info", "Already checked", "<p>This exact ad was already checked, so nothing new was created. Edit the ad or press <b>Clear</b> to check another one.</p>")
    try:
        detail = json.loads(resp.get("detail_json") or "{}")
    except ValueError:
        detail = {}
    if status == "blocked":
        reasons = [GATE_REASONS.get(r, r.replace("_", " ")) for r in detail.get("gate_reasons", [])]
        return problem("The ad was not checked", "It was stopped before review because " + ", ".join(reasons) + ".",
                       "Fill in the missing part and press Check this ad again.")
    d = detail.get("decision") or {}
    if not d:
        return problem("Something went wrong on our side", "The checker answered, but without a verdict.", "Please try again. If it keeps happening, the tool may be updating.")

    kind, title, sub = VERDICT.get(d.get("decision"), ("review", "Needs a look", ""))
    fallback = resp.get("ai_status") == "fallback"
    banner = ("<div class='m-banner'>The AI reviewer was unavailable, so simple rules were used instead. "
              "Treat this as a reminder to check the ad by hand.</div>") if fallback else ""
    risks = d.get("risk_flags") or []
    risk_html = "".join(
        f"<li><span class='m-sev m-{e(r.get('severity', 'low'))}'>{e(r.get('severity', '').capitalize())}</span> "
        f"<b>{e(r.get('type', '').replace('_', ' ').capitalize())}:</b> “{e(r.get('evidence', ''))}”</li>" for r in risks
    ) or "<li>None found.</li>"
    fit = d.get("channel_fit") or {}
    task = d.get("hubspot_task") or {}
    sent_box = ""
    if sent and resp.get("status") == "completed":
        task_id = str(resp.get("hubspot_task_id") or "")
        task_txt = link(f"HubSpot task #{e(task_id)}", TASK_URL.replace("{id}", task_id) if TASK_URL and task_id else "") if task_id else "a HubSpot task"
        slack_txt = link(f"Slack #{e(d.get('slack_channel', ''))}", SLACK_URL)
        sent_box = (f"<div class='m-sent'>✓ Sent to {e(d.get('owner_team', 'the team'))}: {task_txt} and an alert in {slack_txt}.<br>"
                    "<span>This is the verdict your team received.</span></div>")
        where = "Handed off. To send another ad, edit it or press <b>Clear</b>, then check it again."
    elif sent:
        where = "We tried to create the task and alert, but one of them failed. The verdict below is still valid. In a minute, press Check this ad again and hand it off once more."
    else:
        where = "Preview only: nothing has been sent to anyone yet."
    channel_count = (f" <span class='m-count-inline'>(Counted by this app: the headline is {len(ad['headline'])} characters"
                     + (f", limit {CHANNELS[ad['channel']][2]}" if CHANNELS[ad['channel']][2] else "") + ".)</span>")
    # no blank lines or leading indentation: Streamlit's markdown would turn them into code blocks
    return "".join(f"""
<div class="m-card m-{kind}">{sent_box}{banner}
<div class="m-verdict">{e(title)}</div>
<div class="m-sub">{e(sub)}</div>
<div class="m-grid">
<div><span>Owner</span>{e(d.get('owner_team', ''))}</div>
<div><span>Needed by</span>{e(PRIORITY.get(d.get('priority', ''), d.get('priority', '')))}</div>
<div><span>Channel fit</span>{e(str(fit.get('score', '?')))} / 5</div>
</div>
<p class="m-why"><b>Why:</b> {e(d.get('rationale', ''))}</p>
<p class="m-why"><b>Channel check:</b> {e(fit.get('note', ''))}{channel_count}</p>
<div class="m-h">What to fix</div><ul class="m-risks">{risk_html}</ul>
<div class="m-h">Suggested fix</div><div class="m-fix">{e(d.get('suggested_fix', ''))}{own_counts(d.get('suggested_fix', ''), ad['channel'])}</div>
<div class="m-h">Task for the team</div>
<div class="m-task"><b>{e(task.get('title', ''))}</b><br>{e(task.get('body', '')).replace(chr(10), '<br>')}</div>
<div class="m-foot">{where} · Checked in {seconds:.1f} s · confidence {e(str(d.get('confidence', '')))}</div>
</div>""".splitlines())


# ------------------------------------------------------------------ main action
def check_ad(channel, client, product, headline, body, cta, audience, conv, roi, send, visitor, info: dict) -> str:
    """Returns the HTML to show; fills `info` (team, decision, status) when the checker gave a verdict."""
    headline, body, cta, client = (headline or "").strip(), (body or "").strip(), (cta or "").strip(), (client or "").strip()[:80]
    missing = [n for n, v in [("the channel", channel), ("the client or brand", client), ("a headline", headline), ("the body text", body), ("a call-to-action", cta)] if not v]
    if missing:
        return problem("A few details are missing", "Please add " + ", ".join(missing[:-1]) + (" and " if len(missing) > 1 else "") + missing[-1] + ".",
                       "Fill in those fields, or click one of the examples under the form to see how it works.")
    if len(headline) > 300 or len(body) > 1500 or len(cta) > 200:
        return problem("That's longer than one ad", "Headlines over 300 characters, body text over 1,500 or a call-to-action over 200 are usually several ads pasted together.",
                       "Paste one ad at a time: one headline, one body, one call-to-action.")
    for label, val in [("Conversion rate", conv), ("ROI", roi)]:
        if val is not None and (val < 0 or val > (100 if label == "Conversion rate" else 50)):
            return problem(f"{label} looks off", f"{label} should be a number like 4.5 (conversion %) or 3.2 (ROI). You entered {val:g}.",
                           "Fix the number or leave it empty; it only affects how urgent the task is.")
    if not WEBHOOK_URL or not WEBHOOK_KEY:
        return problem("The checker isn't connected", "This copy of the app has no connection to the review workflow.", "If you are the owner, add the two secrets in the app settings.")
    limited = _allowed(visitor)
    if limited:
        return problem("Please slow down a little", limited, "Wait a bit, then try again.")

    now = datetime.now(timezone.utc).replace(microsecond=0)
    run = "ui-" + now.strftime("%Y%m%d")
    vid = "UI-" + uuid.uuid4().hex[:8]
    event = {
        "event_id": f"evt_{run}_{vid}", "run_id": run, "mode": "live" if send else "dry_run",
        "source_agent": "madison.ui", "brief_id": "UI", "variant_id": vid,
        "product": (product or "").strip()[:80] or client, "headline": headline, "body": body, "cta": cta,
        "popper_pass": True, "quality_score": None, "campaign_owner": "", "created_at": now.isoformat().replace("+00:00", "Z"),
        "campaign": {"company": client, "channel": channel, "campaign_type": CHANNELS[channel][0], "audience": (audience or "").strip()[:80] or "General audience",
                     "conversion_rate": (conv / 100) if conv else None, "roi": roi or None, "engagement_score": None},
        "brief": {"title": "", "summary": "", "source": "", "url": "", "published_date": ""},
    }
    t0 = time.time()
    try:
        r = requests.post(WEBHOOK_URL, json=event, headers={"X-Madison-Key": WEBHOOK_KEY}, timeout=TIMEOUT_S)
    except requests.Timeout:
        return problem("The check took too long", f"No answer after {TIMEOUT_S} seconds. Nothing was sent to your team.", "Try again in a minute. Busy moments usually clear quickly.")
    except requests.RequestException:
        return problem("We couldn't reach the checker", "The review service didn't respond. Nothing was sent to your team.", "Check your connection and try again in a minute.")
    secs = time.time() - t0
    if r.status_code in (401, 403):
        return problem("The checker refused the connection", "The app's access key was not accepted.", "If you are the owner, check the MADISON_WEBHOOK_KEY secret.")
    if r.status_code == 404:
        return problem("The checker is switched off", "The review workflow is not published right now.", "If you are the owner, publish the workflow in n8n.")
    try:
        data = r.json()
    except ValueError:
        return problem("Something went wrong on our side", f"The checker answered with an unreadable response (code {r.status_code}).", "Please try again in a minute.")
    if isinstance(data, list):
        data = data[0] if data else {}
    if r.status_code not in (200, 422):
        return problem("Something went wrong on our side", f"The checker returned an error (code {r.status_code}).", "Please try again in a minute.")
    try:
        d = json.loads(data.get("detail_json") or "{}").get("decision") or {}
    except ValueError:
        d = {}
    if d and data.get("status") in ("completed", "partial_failure", "failed"):
        info.update(team=d.get("owner_team", "the owning team"), decision=d.get("decision"), status=data.get("status"))
    return render_result(data, bool(send), secs, {"headline": headline, "channel": channel})


EMPTY_STATE = card("empty", "Your verdict will appear here",
                   "<ol><li>Choose where the ad will run.</li><li>Paste the headline, body and call-to-action.</li>"
                   "<li>Press <b>Check this ad</b>. In about 10 seconds you'll see whether it can ship, who owns it, what breaks the channel's rules, and a fix.</li>"
                   "<li>Happy with the verdict? Press <b>Hand off</b> to send it to the owning team as a HubSpot task and Slack alert. Nothing is sent before that.</li></ol>"
                   "<p class='m-small'>Not sure what to paste? Click one of the examples under the form.</p>")

FIELDS = ["channel", "client", "product", "headline", "body", "cta", "audience", "conv", "roi"]
EXAMPLES = {
    "Google Ads: knit sweater": ["Google Ads", "Innovate Industries", "Chunky knit sweater", "Stay warm this season with our Chunky Knit Sweater!",
                                 "Thick, textured & perfect for cozy layering. Unbeatable comfort & style wrapped into one.", "Shop now & snuggle up!", "Men 18-24", 4.0, 3.2],
    "Instagram: leopard-print blouse": ["Instagram", "TechCorp", "Leopard-print blouse", "Unleash your inner wild side with our Leopard-print blouse!",
                                        "This chic animal print adds sophistication to any outfit. A must-have addition to your wardrobe.", "Shop now and make a statement!", "Women 25-34", 13.0, 7.4],
    "Facebook: ankle boots": ["Facebook", "Alpha Innovations", "Ankle boots", "Step into style with our versatile Ankle Boots!",
                              "Perfect with jeans, skirts, or dresses. Elevate your look & walk confidently.", "Shop now: [website link]", "All ages", 7.0, 6.3],
}


def fill(values):
    st.session_state.update(dict(zip(FIELDS, values)))
    st.session_state.out = EMPTY_STATE
    st.session_state.checked = None


def clear():
    fill([None, "", "", "", "", "", "", None, None])


CSS = """
<style>
:root { --m-paper:#fbf8f3; --m-ink:#1f1b16; --m-text:#3a342c; --m-muted:#776d61; --m-line:#e6ddd0; --m-accent:#a8472a; --m-good:#5c6b45; --m-bad:#9b2c1f; --m-warn:#8a6418; }
.block-container { max-width: 1180px; padding-top: 2.2rem; }
h1 { font-family: "Iowan Old Style", Georgia, serif !important; color: var(--m-ink) !important; }
.m-lede { color: var(--m-muted); margin-top: -8px; }
.m-card { border: 1px solid var(--m-line); border-radius: 10px; padding: 16px 18px; background: #fff; color: var(--m-text) !important; line-height: 1.5; }
.m-card * { color: inherit; } .m-card b { color: var(--m-ink); } .m-card p { margin: 6px 0; }
.m-title { font-family: "Iowan Old Style", Georgia, serif; font-size: 1.25rem; font-weight: 700; color: var(--m-ink); margin-bottom: 6px; }
.m-empty { background: var(--m-paper); } .m-empty ol { padding-left: 20px; } .m-small { color: var(--m-muted); font-size: .9rem; }
.m-error { border-left: 5px solid var(--m-bad); background: #fdf3ef; } .m-error .m-title { color: var(--m-bad); } .m-todo { margin-top: 8px; }
.m-info { border-left: 5px solid var(--m-warn); background: #faf3e3; }
.m-ship { border-top: 6px solid var(--m-good); } .m-review { border-top: 6px solid var(--m-warn); } .m-block { border-top: 6px solid var(--m-bad); }
.m-verdict { font-family: "Iowan Old Style", Georgia, serif; font-size: 1.7rem; font-weight: 700; color: var(--m-ink); }
.m-ship .m-verdict { color: var(--m-good); } .m-review .m-verdict { color: var(--m-warn); } .m-block .m-verdict { color: var(--m-bad); }
.m-sub { color: var(--m-muted); margin-bottom: 12px; }
.m-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin: 8px 0 12px; }
.m-grid div { background: var(--m-paper); border: 1px solid var(--m-line); border-radius: 8px; padding: 8px 10px; font-weight: 600; color: var(--m-ink); }
.m-grid span { display: block; font-size: .75rem; letter-spacing: .06em; text-transform: uppercase; color: var(--m-muted); font-weight: 600; }
.m-h { margin-top: 12px; font-size: .78rem; letter-spacing: .08em; text-transform: uppercase; color: var(--m-accent); font-weight: 700; }
.m-risks { margin: 4px 0 0; padding-left: 18px; } .m-risks li { margin: 3px 0; }
.m-sev { display: inline-block; font-size: .72rem; font-weight: 700; padding: 1px 7px; border-radius: 10px; margin-right: 4px; }
.m-high { background: #f7dcd4; color: var(--m-bad) !important; } .m-medium { background: #f6ecd2; color: var(--m-warn) !important; } .m-low { background: #e8ecdf; color: var(--m-good) !important; }
.m-fix { background: #f3f5ee; border: 1px solid #dfe4d3; border-radius: 8px; padding: 9px 11px; margin-top: 4px; }
.m-task { background: var(--m-paper); border: 1px dashed var(--m-line); border-radius: 8px; padding: 9px 11px; margin-top: 4px; font-size: .93rem; }
.m-foot { margin-top: 12px; font-size: .82rem; color: var(--m-muted); border-top: 1px solid var(--m-line); padding-top: 8px; }
.m-banner { background: #faf3e3; border: 1px solid #e8d7a8; color: var(--m-warn); border-radius: 8px; padding: 8px 10px; margin-bottom: 10px; font-weight: 600; }
.m-hint { font-size: .85rem; color: var(--m-muted); } .m-over { color: var(--m-bad); font-weight: 700; }
.m-sent { background: #eef2e6; border: 1px solid #cdd8b8; color: var(--m-good) !important; border-radius: 8px; padding: 9px 11px; margin-bottom: 12px; font-weight: 700; }
.m-sent span { font-weight: 500; color: var(--m-text); } .m-sent a { text-decoration: underline; }
.m-count { margin-top: 6px; padding-top: 6px; border-top: 1px dashed #dfe4d3; font-size: .88rem; } .m-count-inline { color: var(--m-muted); }
.m-rule { font-size: .88rem; background: var(--m-paper); border: 1px solid var(--m-line); border-radius: 8px; padding: 7px 10px; color: var(--m-text); margin: -6px 0 10px; }
@media (max-width: 640px) { .m-grid { grid-template-columns: 1fr; } }
</style>
"""

# ------------------------------------------------------------------ page
st.session_state.setdefault("out", EMPTY_STATE)
st.markdown(CSS, unsafe_allow_html=True)
st.title("Madison Automation Agent")
st.markdown("<p class='m-lede'>Check a new ad against its channel's rules, see who should own it, and get a ready-to-use fix. "
            "Built for agency marketing-ops teams.</p>", unsafe_allow_html=True)

left, right = st.columns([5, 6], gap="large")
with left:
    channel = st.selectbox("1. Where will this ad run?", list(CHANNELS), index=None, key="channel", placeholder="Choose a channel",
                           help="Each channel has different rules, e.g. Google Ads headlines can be 30 characters at most.")
    if channel:
        st.markdown(f"<div class='m-rule'><b>{e(channel)} rule:</b> {e(CHANNELS[channel][1])}</div>", unsafe_allow_html=True)
    client = st.text_input("2. Client or brand", key="client", placeholder="e.g. TechCorp")
    product = st.text_input("Product (optional)", key="product", placeholder="e.g. Ankle boots")
    headline = st.text_input("3. Headline", key="headline", placeholder="The first line people see")
    st.markdown(headline_hint(headline, channel), unsafe_allow_html=True)
    body = st.text_area("4. Body text", key="body", placeholder="The main ad text", height=100)
    cta = st.text_input("5. Call-to-action", key="cta", placeholder="e.g. Shop now")
    with st.expander("Optional: audience and campaign results (helps decide how urgent it is)"):
        audience = st.text_input("Audience", key="audience", placeholder="e.g. Women 25-34")
        c1, c2 = st.columns(2)
        conv = c1.number_input("Conversion rate (%)", key="conv", value=None, min_value=0.0, step=0.5)
        roi = c2.number_input("ROI (x)", key="roi", value=None, min_value=0.0, step=0.5)
    b1, b2, _ = st.columns([2, 1, 2])
    go = b1.button("Check this ad", type="primary", width="stretch")
    b2.button("Clear", on_click=clear, width="stretch")
    st.caption("Try a real ad from our test set (click to fill the form)")
    with st.container(horizontal=True):
        for label, values in EXAMPLES.items():
            st.button(label, on_click=fill, args=(values,), width="content")

inputs = (channel, client, product, headline, body, cta, audience, conv, roi)


def run(send: bool):
    info = {}
    try:
        st.session_state.out = check_ad(*inputs, send, st.context.ip_address or "anon", info)
    except Exception:  # never show a stack trace to the user
        info = {}
        st.session_state.out = problem("Something went wrong on our side", "The app hit an unexpected problem. Nothing was sent to your team.",
                                       "Please try again in a minute.")
    st.session_state.checked = dict(info, sig=inputs, sent=send) if info else None


with right:
    if go:
        with st.spinner("Checking your ad. This takes about 10 seconds…"):
            run(send=False)
    # The hand-off comes after the verdict (user tests: all three testers looked for it there, not on the form).
    chk = st.session_state.get("checked")
    slot = st.empty()
    if chk and not chk["sent"]:
        if chk["sig"] == inputs:
            with slot.container():
                label = f"Hand off to {chk['team']} {HANDOFF_VERB.get(chk['decision'], '')}".strip()
                handoff = st.button(label, type="primary", key="handoff", width="stretch")
                st.caption("Creates a task in HubSpot and posts an alert in Slack #campaign-review. Nothing is sent until you press it.")
            if handoff:
                slot.empty()
                with st.spinner(f"Handing off to {chk['team']}…"):
                    run(send=True)
        else:
            slot.caption("You changed the ad after checking it. Press **Check this ad** again before handing it off.")
    st.markdown(st.session_state.out, unsafe_allow_html=True)
