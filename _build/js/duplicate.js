// Same brief_id:variant_id was already processed → do nothing (idempotency), tell Madison politely.
const g = $('Gatekeeper: Validate & Normalize').first().json;
return [{ json: { status: 'duplicate', idempotency_key: g.idempotency_key, event_id: g.event.event_id,
  summary: 'Already processed — no new task or alert created.' } }];
