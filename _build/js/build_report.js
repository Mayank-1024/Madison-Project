// REPORT ③ — turns stats + AI insights into things people actually read:
// an HTML email/report, a Slack digest, and rows for the shared Google Sheet.
const s = $('Aggregate Run Stats').first().json;
const res = $input.first().json;
let ins = null;
try {
  if (!res.error && res.stop_reason !== 'refusal') ins = JSON.parse((res.content || []).find((b) => b.type === 'text').text);
} catch (err) { ins = null; }
if (!ins) ins = { headline: 'AI insights unavailable for this run — statistics below are complete.', patterns: [], recommendations: [], watchlist: [] };

const esc = (t) => String(t ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const pill = (obj) => Object.entries(obj).sort((a, b) => b[1] - a[1])
  .map(([k, v]) => `<span style="display:inline-block;margin:2px 4px 2px 0;padding:3px 9px;border-radius:12px;background:#eef2f7;font-size:12px">${esc(k)} <b>${v}</b></span>`).join('') || '—';
const list = (arr) => (arr.length ? `<ul style="margin:6px 0 0;padding-left:18px">${arr.map((x) => `<li style="margin:3px 0">${esc(x)}</li>`).join('')}</ul>` : '<p style="color:#6b7280">—</p>');
const kpi = (v, l) => `<td style="padding:12px 14px;border:1px solid #e3e6ec;border-top:3px solid #0f766e;border-radius:6px"><div style="font-size:22px;font-weight:700;color:#14213d">${v}</div><div style="font-size:12px;color:#6b7280">${l}</div></td>`;
const ex = s.examples.map((x) => `<tr><td style="padding:6px 8px;border-bottom:1px solid #eee">${esc(x.headline)}</td><td style="padding:6px 8px;border-bottom:1px solid #eee">${esc(x.decision)} · ${esc(x.priority)}</td><td style="padding:6px 8px;border-bottom:1px solid #eee">${esc(x.owner)}</td><td style="padding:6px 8px;border-bottom:1px solid #eee;color:#374151">${esc(x.why)}</td></tr>`).join('');

const html = `<!doctype html><html><body style="margin:0;background:#f6f7f9;font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif;color:#2b2f38">
<div style="max-width:760px;margin:0 auto;padding:24px">
<div style="font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#0f766e;font-weight:700">Madison Action Layer · Run report</div>
<h1 style="margin:6px 0 4px;font-size:24px;color:#14213d">${esc(s.run_label)}</h1>
<div style="color:#6b7280;font-size:13px">Generated ${esc(s.generated_at.replace('T', ' ').slice(0, 16))} UTC · ${s.total} variants</div>
<div style="background:#14213d;color:#fff;border-radius:8px;padding:14px 16px;margin:16px 0;font-size:15px">💡 ${esc(ins.headline)}</div>
<table style="border-collapse:separate;border-spacing:8px;width:100%;margin:0 -8px"><tr>
${kpi(s.total, 'variants processed')}${kpi(s.by_decision.auto_approve || 0, 'auto-approved')}${kpi((s.by_decision.needs_review || 0) + (s.by_decision.block || 0), 'sent to humans')}${kpi('$' + s.total_cost_usd, 'AI cost')}${kpi(s.hours_saved + ' h', 'manual work saved*')}
</tr></table>
<h3 style="color:#14213d;margin:18px 0 4px">Patterns the AI found</h3>${list(ins.patterns)}
<h3 style="color:#14213d;margin:18px 0 4px">Recommended changes</h3>${list(ins.recommendations)}
<h3 style="color:#14213d;margin:18px 0 4px">Watchlist this week</h3>${list(ins.watchlist)}
<h3 style="color:#14213d;margin:18px 0 6px">Breakdown</h3>
<p style="margin:4px 0"><b>Decision</b> ${pill(s.by_decision)}</p><p style="margin:4px 0"><b>Priority</b> ${pill(s.by_priority)}</p>
<p style="margin:4px 0"><b>Owner team</b> ${pill(s.by_team)}</p><p style="margin:4px 0"><b>Risk flags</b> ${pill(s.risk_flags)}</p>
<p style="margin:4px 0"><b>Routing</b> ${pill(s.by_ai_status)} <b>Status</b> ${pill(s.by_status)}</p>
<p style="margin:4px 0"><b>Latency</b> p50 ${(s.latency_ms.p50 / 1000).toFixed(1)}s · p95 ${(s.latency_ms.p95 / 1000).toFixed(1)}s · cost/event $${s.cost_per_event_usd}</p>
<h3 style="color:#14213d;margin:18px 0 6px">Sample decisions</h3>
<table style="width:100%;border-collapse:collapse;font-size:12px;background:#fff"><tr style="background:#14213d;color:#fff"><th style="padding:6px 8px;text-align:left">Headline</th><th style="padding:6px 8px;text-align:left">Decision</th><th style="padding:6px 8px;text-align:left">Owner</th><th style="padding:6px 8px;text-align:left">Why</th></tr>${ex}</table>
<p style="color:#6b7280;font-size:11px;margin-top:16px">*Assumes 6 minutes of manual handoff (copy to CRM, write task, notify team) per routed variant. Built with n8n + Claude Haiku 4.5.</p>
</div></body></html>`;

const top = (obj) => Object.entries(obj).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([k, v]) => `${k} ${v}`).join(' · ') || '—';
const slack = { channel: 'campaign-digest', text: `📊 Madison run report: ${s.total} variants`, unfurl_links: false, blocks: [
  { type: 'section', text: { type: 'mrkdwn', text: `📊 *Madison run report — ${s.run_label}*\n${ins.headline}` } },
  { type: 'section', fields: [
    { type: 'mrkdwn', text: `*Processed*\n${s.total}` }, { type: 'mrkdwn', text: `*Auto-approved*\n${s.by_decision.auto_approve || 0}` },
    { type: 'mrkdwn', text: `*Needs humans*\n${(s.by_decision.needs_review || 0) + (s.by_decision.block || 0)}` }, { type: 'mrkdwn', text: `*AI cost*\n$${s.total_cost_usd}` },
  ] },
  { type: 'section', text: { type: 'mrkdwn', text: `*Top risks:* ${top(s.risk_flags)}\n*Busiest teams:* ${top(s.by_team)}\n*Top recommendation:* ${ins.recommendations[0] || '—'}` } },
] };

return [{ json: { html, subject: `Madison run report — ${s.run_label}: ${s.total} variants, ${s.by_decision.auto_approve || 0} auto-approved`, slack_payload: slack, insights: ins } }];
