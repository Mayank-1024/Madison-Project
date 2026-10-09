// Collects what actually happened (task created? alert posted?) into one log row.
// Every column here matches the madison_action_log data table.
const p = $('Plan Actions').first().json;
const g = $('Gatekeeper: Validate & Normalize').first().json;
const d = p.decision;
const tryGet = (name) => { try { return $(name).first().json; } catch (err) { return null; } };
const hub = p.live ? tryGet('Create HubSpot Task') : null;
const slk = p.live ? tryGet('Post Slack Alert') : null;

const taskId = hub && hub.id ? String(hub.id) : '';
const slackOk = Boolean(slk && slk.ok === true);
const failures = [];
if (p.live && !taskId) failures.push(`hubspot: ${(hub && (hub.error?.message || hub.message)) || 'no task id'}`);
if (p.live && !slackOk) failures.push(`slack: ${(slk && (slk.error?.message || slk.error)) || 'not posted'}`);

return [{ json: {
  idempotency_key: g.idempotency_key, event_id: g.event.event_id, run_id: g.event.run_id, mode: g.event.mode,
  status: failures.length ? 'partial_failure' : 'completed',
  decision: d.decision, priority: d.priority, owner_team: d.owner_team, slack_channel: d.slack_channel,
  ai_status: p.ai_ok ? 'ai' : 'fallback', risk_count: d.risk_flags.length,
  headline: g.event.headline.slice(0, 200), summary: d.rationale.slice(0, 500),
  hubspot_task_id: taskId, slack_ok: slackOk, cost_usd: p.cost_usd, latency_ms: Date.now() - g.received_at_ms,
  detail_json: JSON.stringify({ decision: d, ai_problem: p.ai_problem, ai_latency_ms: p.ai_latency_ms, input_tokens: p.input_tokens,
    output_tokens: p.output_tokens, failures, campaign: g.event.campaign, brief: g.event.brief.title, cta: g.event.cta }),
} }];
