// REPORT ④ — one tidy row per decision for the shared Google Sheet (a single batched append per report).
return $('Aggregate Run Stats').first().json.rows.map((r) => ({ json: {
  logged_at: String(r.createdAt || '').replace('T', ' ').slice(0, 19), run_id: r.run_id, event_id: r.event_id,
  headline: r.headline, decision: r.decision, priority: r.priority, owner_team: r.owner_team, status: r.status,
  routed_by: r.ai_status, risk_count: r.risk_count, why: r.summary, hubspot_task_id: r.hubspot_task_id,
  slack_posted: r.slack_ok ? 'yes' : 'no', latency_s: Math.round((Number(r.latency_ms) || 0) / 100) / 10, cost_usd: r.cost_usd,
} }));
