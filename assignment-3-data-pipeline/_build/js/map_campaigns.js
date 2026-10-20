// Source 2 – HuggingFace campaign performance dataset → unified schema.
// Gives campaign context: type, channel, audience, date and results.
const SOURCE = 'HuggingFace: federicomoreno/marketing-campaign-performance-200k';
const SOURCE_URL = 'https://huggingface.co/datasets/federicomoreno/marketing-campaign-performance-200k';
const collectedAt = new Date().toISOString();

const response = $input.first()?.json ?? {};
const rows = Array.isArray(response.rows) ? response.rows : [];

// Built-in check: failed or empty source → log it and keep the workflow going
if (response.error || rows.length === 0) {
  const reason = response.error ? (response.error.message || String(response.error)) : 'returned 0 records';
  console.log(`Source unavailable: ${SOURCE} (${reason})`);
  return [{ json: { _kind: 'source_status', source_name: SOURCE, status: 'unavailable', message: `Source unavailable: ${SOURCE} – ${reason}`, records_received: 0 } }];
}

const records = rows.map(({ row }) => {
  const pct = (v) => (typeof v === 'number' ? `${Math.round(v * 100)}%` : 'n/a');
  const summary =
    `Targets ${row.Target_Audience} in ${row.Location} (${row.Language}) for ${row.Duration}. ` +
    `Conversion rate ${pct(row.Conversion_Rate)}, ROI ${row.ROI}, acquisition cost ${row.Acquisition_Cost}, ` +
    `${row.Clicks} clicks from ${row.Impressions} impressions, engagement score ${row.Engagement_Score}/10.`;

  return {
    json: {
      _kind: 'record',
      record_id: `CMP-${String(row.Campaign_ID).padStart(4, '0')}`,
      source_name: SOURCE,
      source_type: 'campaign_metadata',
      title_or_headline: `${row.Campaign_Type} campaign by ${row.Company} on ${row.Channel_Used}`,
      body_text: summary,
      cta: '',
      brand_or_product: String(row.Company ?? '').trim(),
      channel: String(row.Channel_Used ?? '').trim(),
      campaign_type: String(row.Campaign_Type ?? '').trim(),
      audience: `${row.Target_Audience ?? ''} · ${row.Customer_Segment ?? ''}`.trim(),
      tags: '',
      published_date: row.Date,
      source_url: SOURCE_URL,
      collected_at: collectedAt,
    },
  };
});

return [
  { json: { _kind: 'source_status', source_name: SOURCE, status: 'ok', message: `Loaded ${records.length} rows`, records_received: records.length } },
  ...records,
];
