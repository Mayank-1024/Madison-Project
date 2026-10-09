// ERROR WORKFLOW — runs when the main workflow crashes (anything not already handled by its own branches).
// Posts a plain-language alert so a human knows within seconds.
const e = $input.first().json;
const wf = e.workflow?.name || 'Madison Action Layer v2';
const node = e.execution?.lastNodeExecuted || 'unknown node';
const msg = (e.execution?.error?.message || e.trigger?.error?.message || 'Unknown error').slice(0, 400);
const url = e.execution?.url || '';
return [{ json: { slack_payload: { channel: 'campaign-urgent', text: `🚨 ${wf} failed at "${node}": ${msg}`, blocks: [
  { type: 'section', text: { type: 'mrkdwn', text: `🚨 *Workflow failure — ${wf}*\n*Node:* ${node}\n*Error:* ${msg}` } },
  { type: 'context', elements: [{ type: 'mrkdwn', text: `${url ? `<${url}|Open execution>` : 'No execution link'} · ${new Date().toISOString()}` }] },
] } } }];
