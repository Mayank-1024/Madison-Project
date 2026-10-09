// Gatekeeper said no → build the log row (no AI call, no actions) and answer Madison with 422.
const g = $input.first().json;
return [{ json: {
  idempotency_key: g.idempotency_key, event_id: g.event.event_id || 'unknown', run_id: g.event.run_id, mode: g.event.mode,
  status: 'blocked', decision: 'block', priority: 'low', owner_team: 'Gatekeeper', slack_channel: 'none',
  ai_status: 'skipped', risk_count: g.gate_reasons.length, headline: g.event.headline.slice(0, 200),
  summary: `Blocked by Gatekeeper: ${g.gate_reasons.join(', ')}`, hubspot_task_id: '', slack_ok: false,
  cost_usd: 0, latency_ms: Date.now() - g.received_at_ms,
  detail_json: JSON.stringify({ gate_reasons: g.gate_reasons, event: g.event }),
} }];
