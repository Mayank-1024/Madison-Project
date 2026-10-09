// FALLBACK ROUTER — used only when the AI answer is unusable. Deterministic rules, so the variant is
// still routed and a human is told the AI was skipped. Nothing is lost, nothing crashes.
const p = $input.first().json;
const e = $('Gatekeeper: Validate & Normalize').first().json.event;
const text = `${e.headline} ${e.body} ${e.cta}`;
const flags = [];
const hit = (re) => (text.match(re) || [])[0];
if (hit(/\[[^\]]*\]|bit\.ly\/\S+|\bTBD\b/i)) flags.push({ type: 'placeholder_text', severity: 'high', evidence: hit(/\[[^\]]*\]|bit\.ly\/\S+|\bTBD\b/i) });
if (hit(/unbeatable|ultimate|best|#1/i)) flags.push({ type: 'unverifiable_claim', severity: 'medium', evidence: hit(/unbeatable|ultimate|best|#1/i) });
if (hit(/limited stock|last chance|don.t miss/i)) flags.push({ type: 'false_urgency', severity: 'low', evidence: hit(/limited stock|last chance|don.t miss/i) });

const ch = e.campaign.channel.toLowerCase();
const team = /google|search|display/.test(ch) ? 'Paid Media' : ch === 'email' ? 'Lifecycle & Email'
  : /facebook|instagram|youtube|influencer|social/.test(ch) ? 'Social & Influencer' : 'Content & SEO';
const blocked = flags.some((f) => f.severity === 'high');

return [{ json: { ...p, ai_ok: false, decision: {
  decision: blocked ? 'block' : 'needs_review',
  priority: blocked ? 'high' : 'normal',
  owner_team: blocked ? 'Brand & Legal Review' : team,
  slack_channel: 'campaign-review',
  channel_fit: { score: 3, note: 'Not assessed (AI unavailable).' },
  risk_flags: flags,
  rationale: `AI router unavailable (${p.ai_problem}); routed by fallback rules for human review.`,
  suggested_fix: 'None — human review required.',
  hubspot_task: { title: `Review ${e.campaign.channel} variant ${e.variant_id} (AI fallback)`.slice(0, 80),
    body: `AI routing failed: ${p.ai_problem}.\nCheck the copy manually before publishing.\nHeadline: ${e.headline}`, due_in_days: 1 },
  slack_message: `⚠️ AI router unavailable (${p.ai_problem}). "${e.headline.slice(0, 80)}" for ${e.campaign.company} needs a manual check.`,
  confidence: 0,
} } }];
