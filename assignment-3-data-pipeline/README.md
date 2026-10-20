# Assignment 3: Data pipeline

An n8n workflow that collects the inputs the Action Layer needs, from three free sources with no API keys:
HuggingFace ad copy (creative), a HuggingFace campaign dataset (context), and four marketing RSS feeds (current briefs).
It maps everything into one 16-column schema, removes duplicates, standardises dates to YYYY-MM-DD and flags incomplete fields.
If a source is slow or down it logs `Source unavailable` and keeps going.

**Result:** 295 records collected → **285 clean**, 94.4% complete, 100% with title, date and source.

| File | What it is |
|---|---|
| `Bhadrasen_Mayank_A3_Workflow.json` | n8n workflow (import into n8n 2.x; no credentials needed) |
| `madison_a3_records.csv` | The dataset (285 rows × 16 columns) |
| `madison_a3_quality_report.json` | Per-source counts, completeness, rejects, flags |
| `Bhadrasen_Mayank_A3_Documentation.pdf` | Data inventory, setup guide, quality checks |
| `Bhadrasen_Mayank_A3_Demo_Walkthrough.pdf` | Annotated screenshot walkthrough |
| `_build/` | Generators for the workflow JSON (`build.py` + `js/`) and the PDFs |
