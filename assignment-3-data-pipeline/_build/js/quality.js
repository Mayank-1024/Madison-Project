// Quality step – runs on every record from every source.
// 1) trims text  2) standardises dates to YYYY-MM-DD  3) drops records missing title/date/source
// 4) removes duplicates  5) marks each record complete / incomplete with reasons
const all = $input.all().map((i) => i.json);
const records = all.filter((r) => r._kind === 'record');

// Which fields must be filled for a record to count as "complete", per source type
const REQUIRED = {
  ad_copy: ['title_or_headline', 'body_text', 'cta', 'brand_or_product'],
  campaign_metadata: ['title_or_headline', 'body_text', 'channel', 'campaign_type', 'audience'],
  industry_article: ['title_or_headline', 'body_text', 'source_url'],
};
const COLUMNS = ['record_id', 'source_name', 'source_type', 'title_or_headline', 'body_text', 'cta', 'brand_or_product', 'channel', 'campaign_type', 'audience', 'tags', 'published_date', 'source_url', 'collected_at', 'is_complete', 'quality_flags'];

const today = new Date();
const toIsoDate = (value) => {
  if (!value) return null;
  const s = String(value).trim();
  const d = /^\d{4}-\d{2}-\d{2}$/.test(s) ? new Date(s + 'T00:00:00Z') : new Date(s);
  if (isNaN(d.getTime())) return null;
  if (d.getUTCFullYear() < 2000 || d.getTime() > today.getTime() + 86400000) return null; // not a plausible date
  return d.toISOString().slice(0, 10);
};

const seen = new Set();
const clean = [];
const dropped = { missing_essentials: 0, invalid_date: 0, duplicates: 0 };

for (const r of records) {
  const rec = {};
  for (const col of COLUMNS) rec[col] = typeof r[col] === 'string' ? r[col].replace(/\s+/g, ' ').trim() : r[col] ?? '';

  // Essentials check – title, date and source must exist in EVERY record
  if (!rec.title_or_headline || !rec.source_name || !r.published_date) { dropped.missing_essentials++; continue; }

  // Date check – must parse to a real date
  const iso = toIsoDate(r.published_date);
  if (!iso) { dropped.invalid_date++; continue; }
  rec.published_date = iso;

  // Duplicate check – articles: same URL · ads: same product (the dataset repeats ads with shuffled sentences)
  // · campaigns: same campaign ID
  const norm = (v) => String(v).toLowerCase().replace(/[^a-z0-9]/g, '');
  const key = rec.source_type === 'industry_article' ? `url:${rec.source_url.toLowerCase()}`
    : rec.source_type === 'ad_copy' ? `ad:${norm(rec.brand_or_product)}`
    : `${rec.source_type}:${rec.record_id}`;
  if (seen.has(key)) { dropped.duplicates++; continue; }
  seen.add(key);

  // Completeness check – flag every missing field instead of hiding it
  const flags = (REQUIRED[rec.source_type] || []).filter((f) => !rec[f]).map((f) => `missing_${f}`);
  if (Array.isArray(r._notes)) flags.push(...r._notes); // informational notes, not missing data
  rec.is_complete = flags.every((f) => !f.startsWith('missing_'));
  rec.quality_flags = flags.join('; ');
  clean.push(rec);
}

// Keep a stable, readable order: by source type, then newest first
const order = { campaign_metadata: 1, ad_copy: 2, industry_article: 3 };
clean.sort((a, b) => order[a.source_type] - order[b.source_type] || b.published_date.localeCompare(a.published_date) || a.record_id.localeCompare(b.record_id));

// One bundle out: the clean records (split into CSV rows next) + the counts for the quality report
return [{ json: { records: clean, raw_records: records.length, removed: dropped } }];
