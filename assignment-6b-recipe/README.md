# Assignment 6B: The Recipe (Path B)

The Action Layer rebuilt as a conductor-run pipeline with four layers, typed phase gates and a recipe a conductor can follow.

```
external sources ──► data/raw/ ──► data/verified/ ──► Routing Agent (Claude Haiku 4.5) ──► logs/reports/
      Gate 0 PA      Gate 1 IJ      Gate 2 IJ             Gate 3 TO                      Gate 4 EI     (PF on any failure)
```

| File | What it is |
|---|---|
| `recipe_Bhadrasen.md` | The recipe: assignment template + Madison `cowork_recipe_standardize.md` format, typed TODOs, conductor note |
| `brand_config.json` | Conductor Brief as machine-readable config (every gate has a judgment type) |
| `scripts/run_pipeline.py` | The conductor; stops at every gate for a human decision |
| `scripts/{ingest,gigo,tools}/` | One script per layer (Python standard library only) |
| `fixtures/a3_snapshot.csv` | Offline data for `--sample` mode |
| `RUN.md` | How to run it |

```bash
python3 scripts/run_pipeline.py --sample      # offline, no AI
python3 scripts/run_pipeline.py --n 20        # live sources + live AI (dry run: nothing sent to HubSpot/Slack)
```
*Status (2026-10-20): built and tested in sample mode and with live ingest; the graded live run is pending.*
