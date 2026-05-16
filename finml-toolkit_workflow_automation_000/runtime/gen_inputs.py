#!/usr/bin/env python3
"""
Generates the sandbox workspace with distractor files and the problem specification.
"""
import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ── 1. Deep distractor directory structure ──────────────────────────────────
dirs = [
    "finml_project/data/raw",
    "finml_project/data/processed",
    "finml_project/models/v1",
    "finml_project/models/v2",
    "finml_project/reports/q1",
    "finml_project/reports/q4",
    "finml_project/configs",
    "finml_project/notebooks",
    "finml_project/scripts/backtests",
    "finml_project/scripts/etl",
    "pipeline_logs/old",
    "pipeline_logs/archive",
    "compliance/2023",
    "compliance/2024",
    "audit_drafts",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "finml_project/data/raw/prices_2024_q4.csv": "date,ticker,close\n2024-10-01,AAPL,226.51\n2024-10-02,AAPL,225.77\n",
    "finml_project/data/processed/features_v3.parquet.meta": '{"rows": 50000, "cols": 42, "version": "3.1"}',
    "finml_project/models/v1/alpha_backtest.json": json.dumps({"sharpe": 1.42, "max_dd": -0.08, "strategy": "alpha-3"}),
    "finml_project/models/v2/beta_backtest.json": json.dumps({"sharpe": 1.87, "max_dd": -0.05, "strategy": "beta-7"}),
    "finml_project/reports/q4/portfolio_weights.txt": "AAPL: 0.12\nGOOGL: 0.09\nMSFT: 0.15\nSPY: 0.64\n",
    "finml_project/configs/risk_params.yaml": "risk_threshold: 0.05\nmax_leverage: 2.0\nstop_loss: 0.03\n",
    "finml_project/configs/pipeline_v2.yaml": "steps:\n  - ingest\n  - validate\n  - transform\n  - backtest\n",
    "finml_project/notebooks/EDA_sector_correlation.ipynb.stub": '{"cells": [], "metadata": {"kernel": "python3"}}',
    "finml_project/scripts/backtests/run_alpha3.sh": "#!/bin/bash\necho 'Running alpha-3 backtest'\n",
    "finml_project/scripts/etl/convert_csv_parquet.py": "import pandas as pd\ndf = pd.read_csv('input.csv')\ndf.to_parquet('output.parquet')\n",
    "pipeline_logs/old/run_2023-11-15.log": "2023-11-15 09:00|backtest strategy gamma-1\n2023-11-15 10:30|validate output\n",
    "pipeline_logs/archive/batch_2024-01.log": "2024-01-03 08:15|process Q1 earnings\n",
    "compliance/2023/audit_trail_partial.txt": "Operation log incomplete - see IT for full records\n",
    "compliance/2024/checklist.md": "- [ ] Validate portfolio weights\n- [ ] Run correlation analysis\n- [ ] Export audit trail\n",
    "audit_drafts/notes.txt": "Need to record all pipeline steps before end-of-quarter review.\nSteps: backtest alpha-3, validate portfolio, convert to parquet, analyze correlations, compare strategies.\n",
}

for rel_path, content in distractor_files.items():
    p = workspace / rel_path
    p.write_text(content)

# ── 2. The actual task specification file (business brief) ───────────────────
task_brief = """FINANCIAL ML PIPELINE - Q4 AUDIT REQUIREMENTS
================================================
Compliance team requires a complete, searchable audit trail for the Q4 pipeline run.

Pipeline steps that MUST be recorded:
1. Run: "backtest strategy alpha-3"
2. Check: "validate portfolio weights"
3. Convert: "csv to parquet format"
4. Analyze: "correlation matrix on sector data"
5. Compare: "strategy A vs strategy B returns"
6. Config: "set risk_threshold=0.05"
7. Batch: "process all Q4 earnings files"

After recording all steps:
- Perform a search for the term "portfolio" to confirm the entry is retrievable
- Export the complete audit trail in JSON format for compliance archiving
- Capture the output of the stats command to a file named: pipeline_stats.txt
- Capture the output of the search command to a file named: search_results.txt

The JSON export file must be accessible in its standard location for compliance review.
"""

(workspace / "TASK_BRIEF.txt").write_text(task_brief)

# ── 3. A red-herring "export" directory to trap naive agents ─────────────────
(workspace / "exports").mkdir(exist_ok=True)
(workspace / "exports" / "README.txt").write_text(
    "This directory is NOT where finml-toolkit exports data. Check the tool documentation.\n"
)

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in workspace.rglob('*') if _.is_file())}")