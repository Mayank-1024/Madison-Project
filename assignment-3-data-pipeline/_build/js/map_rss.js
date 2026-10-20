// Source 3 – four marketing RSS feeds → unified schema.
// Each feed is checked on its own, so one broken feed does not stop the others.
const FEEDS = [
  { node: 'RSS: MarTech', name: 'RSS: MarTech (martech.org)', prefix: 'MT' },
  { node: 'RSS: Marketing Dive', name: 'RSS: Marketing Dive', prefix: 'MD' },
  { node: 'RSS: HubSpot Marketing Blog', name: 'RSS: HubSpot Marketing Blog', prefix: 'HS' },
  { node: 'RSS: Social Media Examiner', name: 'RSS: Social Media Examiner', prefix: 'SME' },
];
const collectedAt = new Date().toISOString();
// Turn HTML (even escaped HTML like &lt;div&gt;) into plain readable text
const decode = (s) => s
  .replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#0?39;|&apos;/g, "'")
  .replace(/&[lr]dquo;/g, '"').replace(/&[lr]squo;/g, "'").replace(/&mdash;/g, '—').replace(/&ndash;/g, '–').replace(/&hellip;/g, '…')
  .replace(/&nbsp;|&#160;/g, ' ').replace(/&#(\d+);/g, (_, n) => String.fromCharCode(Number(n))).replace(/&amp;/g, '&');
const stripHtml = (s) => decode(decode(String(s ?? '')).replace(/<[^>]*>/g, ' ')).replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();

const output = [];
for (const feed of FEEDS) {
  let items = [];
  try { items = $(feed.node).all().map((i) => i.json); } catch (e) { items = []; }
  const failed = items.find((i) => i.error);
  const articles = items.filter((i) => !i.error && i.title);

  if (failed || articles.length === 0) {
    const reason = failed ? (failed.error.message || String(failed.error)) : 'returned 0 records';
    console.log(`Source unavailable: ${feed.name} (${reason})`);
    output.push({ json: { _kind: 'source_status', source_name: feed.name, status: 'unavailable', message: `Source unavailable: ${feed.name} – ${reason}`, records_received: 0 } });
    continue;
  }

  output.push({ json: { _kind: 'source_status', source_name: feed.name, status: 'ok', message: `Loaded ${articles.length} articles`, records_received: articles.length } });
  articles.forEach((a, i) => {
    // Remove the WordPress footer ("The post … appeared first on …") so only the real summary remains
    const summary = stripHtml(a.contentSnippet || a.content || a.summary).replace(/\s*The post .+ appeared first on .+$/, '').trim();
    output.push({
      json: {
        _kind: 'record',
        record_id: `${feed.prefix}-${String(i + 1).padStart(4, '0')}`,
        source_name: feed.name,
        source_type: 'industry_article',
        title_or_headline: stripHtml(a.title),
        body_text: summary.length > 500 ? summary.slice(0, 497).trimEnd() + '...' : summary,
        cta: '',
        brand_or_product: '',
        channel: 'Editorial / RSS',
        campaign_type: 'Industry brief',
        audience: '',
        tags: (Array.isArray(a.categories) ? a.categories : []).map((c) => (typeof c === 'string' ? c : c?._ ?? '')).filter(Boolean).slice(0, 5).join('; '),
        published_date: a.isoDate || a.pubDate || '',
        source_url: a.link || '',
        collected_at: collectedAt,
      },
    });
  });
}
return output;
