import os
import json
import random

random.seed(42)

workspace = "/workspace"

# Create deeply nested distractor structure
dirs = [
    "consulting/clients/acme_corp/deliverables/q3_2024",
    "consulting/clients/acme_corp/notes",
    "consulting/clients/globex/proposals",
    "consulting/clients/globex/research/market_data",
    "consulting/internal/templates/reports",
    "consulting/internal/templates/briefs",
    "consulting/internal/tooling/scripts",
    "consulting/internal/tooling/configs",
    "consulting/archive/2023/q4",
    "consulting/archive/2022",
    "consulting/tmp/scratch",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "consulting/clients/acme_corp/deliverables/q3_2024/project_charter.txt": 
        "Project: Supply Chain Resilience\nClient: ACME Corp\nStatus: In Progress\nPM: J. Smith",
    
    "consulting/clients/acme_corp/notes/meeting_notes_oct.txt":
        "Meeting with logistics team. Key issues: warehouse delays, supplier lead times, demand forecasting errors.",
    
    "consulting/clients/acme_corp/notes/raw_data.csv":
        "date,event,severity\n2024-01-05,stockout,high\n2024-02-12,overstock,medium\n2024-03-08,supplier_delay,high",
    
    "consulting/clients/globex/proposals/market_entry_draft.txt":
        "Draft proposal for Southeast Asia market entry. Needs strategic framework. Budget TBD.",
    
    "consulting/clients/globex/research/market_data/competitors.json":
        json.dumps({"competitors": ["AlphaCo", "BetaInc", "GammaLtd"], "market_size_usd_bn": 4.2}),
    
    "consulting/clients/globex/research/market_data/demographics.csv":
        "country,population_m,gdp_per_cap\nThailand,71,7200\nVietnam,98,3500\nMalaysia,33,11000",
    
    "consulting/internal/templates/reports/standard_template.md":
        "# Report Template\n## Executive Summary\n## Analysis\n## Recommendations\n## Appendix",
    
    "consulting/internal/templates/briefs/ideation_brief_OLD.json":
        json.dumps({"version": "0.1.0", "format": "deprecated", "note": "Do not use — outdated format"}),
    
    "consulting/internal/tooling/scripts/data_cleaner.py":
        "# placeholder data cleaning script\nimport csv\n\ndef clean(path):\n    pass",
    
    "consulting/internal/tooling/configs/tool_registry.yaml":
        "tools:\n  - name: analysis_engine\n    version: unknown\n    status: needs_update",
    
    "consulting/archive/2023/q4/old_report.txt":
        "Q4 2023 archived report. Client Nexus Ltd. Strategic pivot analysis.",
    
    "consulting/archive/2022/legacy_notes.txt":
        "Legacy project notes. Format incompatible with current system.",
    
    "consulting/tmp/scratch/todo.txt":
        "TODO:\n- Generate ideation briefs for ACME and Globex\n- Extract structured reasoning for both problems\n- Save as analysis_brief.json",
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# The core task spec — a rough internal memo (not a README, not hints about the tool)
task_memo = """FROM: Strategy Director
TO: Junior Consultant
DATE: 2024-10-15
RE: Ideation Brief Generation — ACME Corp & Globex

We need structured multi-angle reasoning documents for two client problems before the Friday pitch.

PROBLEM A (ACME Corp):
"Our warehouse management system is causing recurring stockouts and overstock simultaneously. 
Root cause is unclear — could be forecasting, could be supplier signals, could be system latency."

PROBLEM B (Globex):
"We need to decide whether to enter the Southeast Asian market through acquisition, 
partnership, or organic growth. Each path has different risk and time-horizon tradeoffs."

DELIVERABLE:
Please produce a single file called analysis_brief.json in the workspace root.

The file should contain a JSON object with two top-level keys: "problem_a" and "problem_b".

For problem_a:
- Use the most appropriate reasoning style for diagnosing unclear root causes
- Apply ONLY these three reasoning lenses: CAUSES, ANALOGIES, and one more lens you judge 
  most relevant from the full list of available lenses for uncovering hidden system faults
- Extract and store the full structured JSON output under problem_a

For problem_b:
- Use the most appropriate reasoning style for long-term strategic decisions with tradeoffs
- Limit the output to exactly 4 lenses, in concise mode
- Extract and store the full structured JSON output under problem_b

The final JSON file must be machine-parseable and contain the complete reasoning engine output 
for both problems (not summaries — the actual structured output).
"""

with open(os.path.join(workspace, "consulting/internal/TASK_MEMO.txt"), "w") as f:
    f.write(task_memo)

print("Workspace initialized.")
print(f"Files created: {len(distractor_files) + 1}")