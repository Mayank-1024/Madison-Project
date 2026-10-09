// REPORT ① — reads the action log and computes the numbers a manager cares about.
const cfg = $('Report Settings').first().json;
const all = $input.all().map((i) => i.json).filter((r) => r.idempotency_key);
const since = Date.now() - (Number(cfg.lookback_hours) || 24) * 3600000;
const rows = cfg.run_id
  ? all.filter((r) => r.run_id === cfg.run_id)
  : all.filter((r) => new Date(r.createdAt).getTime() >= since);

const count = (key) => rows.reduce((m, r) => ((m[r[key]] = (m[r[key]] || 0) + 1), m), {});
const lat = rows.map((r) => Number(r.latency_ms) || 0).sort((a, b) => a - b);
const pct = (q) => (lat.length ? lat[Math.min(lat.length - 1, Math.floor(q * lat.length))] : 0);
const risks = {};
const examples = [];
for (const r of rows) {
  let det = {};
  try { det = JSON.parse(r.detail_json || '{}'); } catch (err) { det = {}; }
  for (const f of det.decision?.risk_flags || []) risks[f.type] = (risks[f.type] || 0) + 1;
  if (examples.length < 8 && r.status !== 'blocked') examples.push({ headline: r.headline, decision: r.decision, priority: r.priority,
    owner: r.owner_team, why: r.summary, fix: det.decision?.suggested_fix || '' });
}
const routed = rows.filter((r) => r.status !== 'blocked');
const MINUTES_PER_MANUAL_HANDOFF = 6; // assumption: copy into CRM + write task + notify team, per variant
const cost = rows.reduce((s, r) => s + (Number(r.cost_usd) || 0), 0);

return [{ json: {
  run_label: cfg.run_id || `last ${cfg.lookback_hours || 24} hours`,
  generated_at: new Date().toISOString(),
  total: rows.length,
  by_status: count('status'), by_decision: count('decision'), by_priority: count('priority'),
  by_team: count('owner_team'), by_ai_status: count('ai_status'),
  risk_flags: risks,
  latency_ms: { p50: pct(0.5), p95: pct(0.95), max: lat[lat.length - 1] || 0 },
  total_cost_usd: Math.round(cost * 10000) / 10000,
  cost_per_event_usd: routed.length ? Math.round((cost / routed.length) * 1e5) / 1e5 : 0,
  hours_saved: Math.round((routed.length * MINUTES_PER_MANUAL_HANDOFF) / 6) / 10,
  examples,
  rows,
} }];
