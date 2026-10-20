// Quality report – the numbers for the documentation, calculated fresh on every run.
const { records: clean, raw_records, removed } = $input.first().json;
const statuses = $('Merge All Sources').all().map((i) => i.json).filter((r) => r._kind === 'source_status');

const pct = (a, b) => (b ? Math.round((a / b) * 1000) / 10 : 0);
const complete = clean.filter((r) => r.is_complete === true).length;

const perSource = statuses.map((s) => {
  const rows = clean.filter((r) => r.source_name === s.source_name);
  const done = rows.filter((r) => r.is_complete === true).length;
  const dates = rows.map((r) => r.published_date).sort();
  return {
    source_name: s.source_name,
    status: s.status,
    message: s.message,
    records_received: s.records_received,
    records_kept: rows.length,
    complete_records: done,
    completeness_pct: pct(done, rows.length),
    date_range: dates.length ? `${dates[0]} to ${dates[dates.length - 1]}` : '',
  };
});

const flagCounts = {};
for (const r of clean) for (const f of String(r.quality_flags || '').split('; ').filter(Boolean)) flagCounts[f] = (flagCounts[f] || 0) + 1;

const has = (r, f) => String(r[f] ?? '').trim() !== '';
return [{
  json: {
    report_generated_at: new Date().toISOString(),
    project: 'Madison Automation Agent – Action Layer data pipeline',
    sources_attempted: statuses.length,
    sources_available: statuses.filter((s) => s.status === 'ok').length,
    unavailable_sources: statuses.filter((s) => s.status !== 'ok').map((s) => s.message),
    raw_records_collected: raw_records,
    records_removed: raw_records - clean.length,
    removed_breakdown: removed,
    clean_records: clean.length,
    complete_records: complete,
    quality_rate_pct: pct(complete, clean.length),
    essentials_check: {
      title_present_pct: pct(clean.filter((r) => has(r, 'title_or_headline')).length, clean.length),
      date_present_pct: pct(clean.filter((r) => has(r, 'published_date')).length, clean.length),
      source_present_pct: pct(clean.filter((r) => has(r, 'source_name') && has(r, 'source_url')).length, clean.length),
      dates_in_yyyy_mm_dd_pct: pct(clean.filter((r) => /^\d{4}-\d{2}-\d{2}$/.test(r.published_date)).length, clean.length),
    },
    per_source: perSource,
    quality_flag_counts: flagCounts,
  },
}];
