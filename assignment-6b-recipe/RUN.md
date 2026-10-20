# Run the pipeline (about 5 minutes, ~$0.10)

1. n8n: make sure **Madison Action Layer v2** is Published.
2. Terminal:
   ```bash
   cd ~/Desktop/BrandingAI/Assignment_6B
   python3 --version            # 3.11+ includes the MarTech feed; 3.9 skips it (logged, fine)
   export MADISON_WEBHOOK_URL="https://<your-n8n-domain>/webhook/madison/variant"
   export MADISON_WEBHOOK_KEY="<your current Madison Webhook Key>"
   python3 scripts/run_pipeline.py --n 20
   ```
3. At each **PHASE GATE** read the checks, then press **Enter** to accept the recipe's response (or type `stop`). Add a short note when asked
   (for example "MarTech down, context only, continue"). These notes appear in the run log and the report.
4. When it says **Done**, open Finder at `Assignment_6B/logs/reports/` and take **one screenshot** of the folder (the report file must be visible).
5. Tell me "6B run done". I'll read the logs and build the PDF.

Do not run with `--yes` for the submission run: the grader wants to see human decisions at each gate.
