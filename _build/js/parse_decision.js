// ② ROUTING AGENT — answer checker. Never trusts the AI blindly:
// API errors (rate limit / timeout / 5xx after 3 retries), refusals, truncated or malformed JSON and
// out-of-range values all mark the decision invalid, so the rule-based fallback takes over.
const res = $input.first().json;
const started = $('Build Claude Request').first().json.ai_started_at_ms;
const PRICE_IN = 1.0 / 1e6, PRICE_OUT = 5.0 / 1e6; // Claude Haiku 4.5: $1 / $5 per million tokens

const ENUMS = {
  decision: ['auto_approve', 'needs_review', 'block'],
  priority: ['urgent', 'high', 'normal', 'low'],
  owner_team: ['Paid Media', 'Lifecycle & Email', 'Social & Influencer', 'Content & SEO', 'Brand & Legal Review'],
  slack_channel: ['campaign-urgent', 'campaign-review', 'campaign-digest'],
};

let problem = null;
let decision = null;
if (res.error) {
  const msg = typeof res.error === 'string' ? res.error : (res.error.message || JSON.stringify(res.error));
  problem = `api_error: ${String(msg).slice(0, 180)}`;
} else if (res.stop_reason === 'refusal') {
  problem = 'model_refused';
} else if (res.stop_reason === 'max_tokens') {
  problem = 'response_truncated';
} else {
  const text = (res.content || []).find((b) => b.type === 'text')?.text;
  try {
    decision = JSON.parse(text);
  } catch (err) {
    problem = 'malformed_json';
  }
  if (decision) {
    for (const [field, allowed] of Object.entries(ENUMS)) {
      if (!allowed.includes(decision[field])) problem = `invalid_${field}`;
    }
    if (!decision.hubspot_task?.title || !decision.slack_message) problem = 'missing_output_text';
    if (typeof decision.confidence !== 'number') problem = 'missing_confidence';
  }
}

const usage = res.usage || {};
const inTok = usage.input_tokens || 0, outTok = usage.output_tokens || 0;
return [{ json: {
  ai_ok: problem === null,
  ai_problem: problem,
  decision: problem === null ? decision : null,
  ai_model: res.model || 'claude-haiku-4-5',
  ai_latency_ms: Date.now() - started,
  input_tokens: inTok,
  output_tokens: outTok,
  cost_usd: Math.round((inTok * PRICE_IN + outTok * PRICE_OUT) * 1e6) / 1e6,
} }];
