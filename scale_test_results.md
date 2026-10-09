# Scale Testing Results — Madison Action Layer v2

**System under test:** n8n 2.12.3 (single main process, default execution mode) on a Hostinger **KVM 1 VPS (1 vCPU / 4 GB RAM)** · Routing Agent = **Claude Haiku 4.5** (`claude-haiku-4-5`) via the Messages API with strict JSON-schema output · Slack + HubSpot live actions · n8n Data Table action log.
**Test date:** 2026-10-09. **Load generator:** `scale_test/loadtest.py` on a MacBook Air, firing real HTTP POSTs at the production webhook (`/webhook/madison/variant`, Header-Auth protected). Every number below comes from `scale_test/results/*.json|csv` — nothing is estimated unless marked *estimate*.

**Test data:** events built by `scale_test/make_events.py` from the 285 Assignment 3 records (ad copy + campaign context + RSS brief). By design ~30% of every batch is invalid (Popper quality-gate failures from A3's `missing_cta` ads, plus deliberately missing headlines and invalid dates) and every 25th event is an exact repeat — so the Gatekeeper and idempotency paths are tested under load too. "Dry-run" events run Gatekeeper + Claude + logging but skip Slack/HubSpot (so 400 test events don't spam real tools).

## Scale Testing Results

| Run | Requests | Concurrency | Mode | Wall clock | Throughput | Latency p50 / p95 / max (client) | Failures | Claude cost |
|---|---|---|---|---|---|---|---|---|
| Single request (cold) | 1 | 1 | live | 19.4 s | — | 19.4 s | 0 | $0.0049 |
| **Single request** | 1 | 1 | live | **9.5 s** | — | 9.5 s | 0 | $0.0051 |
| **10 requests** (sequential) | 10 | 1 | live | **71.9 s** | 8 / min | 8.9 / 10.0 / 10.0 s | 0 | $0.041 |
| 10 requests (parallel) | 10 | 10 | live | 11.4 s | 53 / min | 9.5 / 11.4 / 11.4 s | 0 | $0.040 |
| **50 requests** | 50 | 10 | live | **28.3 s** | 106 / min | 6.4 / 9.2 / 10.0 s | 0 | $0.156 |
| 100 requests | 100 | 20 | dry-run | 33.5 s | 179 / min | 8.2 / 10.8 / 13.0 s | 0 | $0.331 |
| 200 requests | 200 | 50 | dry-run | 37.9 s | 317 / min | 9.6 / 13.2 / 15.7 s | 0 | $0.671 |
| **400 requests** | 400 | 100 | dry-run | **71.8 s** | **334 / min** | **16.3 / 26.8 / 31.5 s** | 0 | $1.166 |
| Duplicate re-send | 1 | 1 | live | 0.2 s | — | 0.19 s | 0 | $0 (no AI call) |

*The first single request took 19.4 s: Anthropic compiles a new JSON schema once (then caches it 24 h). Every later single request took 8–10 s.*
*The 50-request row is the final prompt (v2). An earlier 50-request run with the first prompt had identical reliability (0 failures, p50 8.9 s) — see "Intelligence tuning" below.*

**Total across all runs (incl. the smoke and demo events):** 834 requests · **0 failed requests (0 HTTP errors, 0 timeouts, 0 AI fallbacks)** · total Claude spend **$2.63**.

- **Maximum capacity: not reached as a hard failure.** At 400 requests / 100 concurrent every request still succeeded, but throughput stopped growing (317 → 334 / min) while latency doubled — that saturation point is the practical ceiling of this VPS: **≈ 330 events / minute (≈ 5.5 / second)**.

## What Breaks First

| Limit | Observed | Evidence |
|---|---|---|
| **n8n intake on 1 vCPU (first to saturate)** | At 100 concurrent, requests queue **~7 s before n8n starts processing them** | Events rejected by the Gatekeeper (no AI call) normally return in **0.2 s**; at 100 concurrent they took **8.1 s** median. Server-side processing time stayed at ~9 s, so the extra wait is queueing in front of the single n8n process, not Claude. |
| **Idempotency under concurrency** | **Concurrent exact duplicates are both processed** (27 of 27 repeats sent inside concurrent batches; e.g. `evt_v2-50_0026` appears twice in the Sheet) | The check-then-insert against the Data Table is not atomic: two requests with the same key both read "not seen" before either writes. **Sequential duplicates are caught** (re-send → `duplicate`, 0.19 s, $0). |
| API rate limits (Anthropic) | **Not hit** — 0 × 429 up to 100 concurrent | 0 fallbacks; cost per event constant ($0.0044–0.0051). Account tier limits were not exceeded at ~330 req/min. |
| Slack / HubSpot rate limits | **Not hit** at 10 concurrent live (50 tasks + 50 alerts in 28 s) | 35/35 completed events have a HubSpot task ID and `slack_ok = true`. Slack's ~1 msg/s/channel limit is the next expected live limit above this. |
| Memory issues | **None observed** at 400 requests / 100 concurrent | No crashed or failed executions. (VPS RAM was not instrumented — honest gap.) |
| Timeout errors | **None** (client timeout 120 s; worst request 31.5 s) | Claude call itself: 4–10 s per event. |
| **Cost per 100 requests** | **$0.45** (100 routed events) · **$0.31** for a typical batch where ~30% are blocked before AI | Measured from Claude `usage` tokens: ~2,200 input + ~470 output tokens per event at $1 / $5 per MTok. |

## Production Readiness

**Could this run 24/7? Yes, for a single team's volume — with three changes before multi-team scale.**
- It already survives slow/failed dependencies: every external call retries 3× (5 s apart) and continues on error; malformed or refused AI answers drop to a deterministic fallback router; an n8n error workflow alerts `#campaign-urgent` on any crash; Header Auth protects the webhook.
- Before scaling further: (1) **n8n queue mode** (Redis + 2–3 workers) to remove the 1-vCPU intake bottleneck; (2) an **atomic idempotency claim** (Postgres unique constraint on `idempotency_key`, or Redis `SETNX`) to close the concurrent-duplicate race; (3) a separate Slack channel throttle (or batching into threads) above ~1 alert/second.

**Estimated monthly cost at 1,000 requests/day** (*estimate*, from measured unit costs):
- Claude Haiku 4.5: 1,000 × 30 × $0.0045 = **$135 / month** if every request is routed; **≈ $95 / month** at the observed ~30% Gatekeeper-block rate.
- Run reports: 1 Insights call/day ≈ $0.01 → ~$0.30 / month.
- n8n + VPS: the existing Hostinger KVM 1 (1,000/day = 0.7/min, ~0.2% of measured capacity). Slack, HubSpot free CRM, Google Sheets/Gmail: $0.
- **≈ $95–135 / month total**, vs. the manual handoff it replaces: at 6 min per variant (*assumption*) and $34.63/hr (DoubleVerify 2025 rate used in A2), 1,000 variants/day ≈ 100 h/day of copy-paste work.

**Required monitoring:**
1. Failed-execution rate and n8n error-workflow alerts (target 0).
2. p95 end-to-end latency (alert > 20 s → queue building up).
3. AI fallback rate (`ai_status = fallback`; rising = API trouble or prompt drift).
4. Anthropic 429s / spend per day (budget alert).
5. HubSpot/Slack `partial_failure` rows in the action log.
6. Duplicate `idempotency_key` count in the log (should stay 0 once the atomic claim is in place).
7. Decision mix drift (share of block / needs_review / auto_approve per day).

## Intelligence tuning (honest note)
The first scale runs (scale-1 … scale-200) used prompt v1. Reliability was perfect, but Claude **blocked 85% of variants** — its reasons showed why: the test generator paired fashion ads with random news briefs and the synthetic A3 campaign data assigns campaign types at random ("Email campaign on Instagram"), and Claude correctly flagged those mismatches. Fixes: campaign type derived from channel in the generator, the brief reframed as optional *market context*, and severity rules calibrated (placeholders / false factual claims = high; marketing adjectives = low). Prompt v2 results on 50 live events: **16 auto-approved · 18 needs review · 1 blocked by Claude · 15 blocked by the Gatekeeper** — a realistic mix, at lower latency (p50 6.4 s vs 8.9 s) and lower cost ($0.0044 vs $0.0050 per event). Residual quirk: Claude still occasionally raises a medium "audience mismatch" (e.g. fashion copy for a "Tech Enthusiasts" segment) — a real signal in the synthetic data, sent to human review rather than blocked.

## Raw evidence
`scale_test/results/` — one CSV (per request) and one JSON (summary) per run: `smoke-1`, `demo-1`, `scale-1`, `scale-10`, `scale-10p`, `scale-50`, `scale-100`, `scale-200`, `v2-10`, `v2-50`, `v2-400`, `dup-check`. Screenshots: Terminal summaries (dup-check, v2-400), n8n Executions list, Google Sheet with the duplicated `evt_v2-50_0026` rows.
