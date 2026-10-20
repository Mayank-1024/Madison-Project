// Source 1 – HuggingFace ad copy → unified schema.
// Splits each ad into headline (first sentence), body (middle) and CTA (closing call to action).
const SOURCE = 'HuggingFace: jaykin01/advertisement-copy';
const SOURCE_URL = 'https://huggingface.co/datasets/jaykin01/advertisement-copy';
const DATASET_DATE = '2023-09-25'; // dataset last-updated date on HuggingFace (rows have no own date)
const collectedAt = new Date().toISOString();

const response = $input.first()?.json ?? {};
const rows = Array.isArray(response.rows) ? response.rows : [];

// Built-in check: failed or empty source → log it and keep the workflow going
if (response.error || rows.length === 0) {
  const reason = response.error ? (response.error.message || String(response.error)) : 'returned 0 records';
  console.log(`Source unavailable: ${SOURCE} (${reason})`);
  return [{ json: { _kind: 'source_status', source_name: SOURCE, status: 'unavailable', message: `Source unavailable: ${SOURCE} – ${reason}`, records_received: 0 } }];
}

const CTA_WORDS = /\b(shop|buy|order|get|grab|try|book|sign up|join|visit|call|discover|explore|learn|start|claim|save|upgrade|treat|elevate|experience|download|subscribe|reserve|enjoy|find|unlock|step|embrace|transform)\b/i;

const records = rows.map(({ row_idx, row }) => {
  const text = String(row.ad ?? '').trim();
  const tags = (text.match(/#\w+/g) || []).join(' ');
  const clean = text.replace(/#\w+/g, '').replace(/\s+/g, ' ').replace(/^"|"$/g, '').trim();
  const sentences = clean.split(/(?<=[.!?])\s+/).filter(Boolean);

  const headline = sentences[0] ?? '';
  let cta = '';
  let bodyParts = sentences.slice(1);
  const last = sentences[sentences.length - 1];
  if (sentences.length > 1 && CTA_WORDS.test(last)) {
    cta = last;
    bodyParts = sentences.slice(1, -1);
  }

  // Short ads (headline + CTA only): use the dataset's product description as the body, and say so
  let body = bodyParts.join(' ');
  const notes = ['date_from_dataset_release'];
  if (!body && row.description) { body = String(row.description).trim(); notes.push('body_from_product_description'); }

  return {
    json: {
      _kind: 'record',
      record_id: `AD-${String(row_idx + 1).padStart(4, '0')}`,
      source_name: SOURCE,
      source_type: 'ad_copy',
      title_or_headline: headline,
      body_text: body,
      cta,
      brand_or_product: String(row.product ?? '').trim(),
      channel: '',
      campaign_type: 'Product ad',
      audience: '',
      tags,
      published_date: DATASET_DATE,
      source_url: SOURCE_URL,
      collected_at: collectedAt,
      _notes: notes,
    },
  };
});

return [
  { json: { _kind: 'source_status', source_name: SOURCE, status: 'ok', message: `Loaded ${records.length} rows`, records_received: records.length } },
  ...records,
];
