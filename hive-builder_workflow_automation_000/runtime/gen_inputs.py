import os
import random
import json
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")
USER_DOCUMENTS = Path("/root/Documents")

# ── Existing workspace distractors (simulate a "used" environment) ──────────
projects_dir = WORKSPACE / "projects"
projects_dir.mkdir(parents=True, exist_ok=True)

# Distractor project files
distractor_projects = [
    ("project_alpha/README.md", "# Alpha Project\nAnalysis pipeline for Q3 data."),
    ("project_alpha/config.json", json.dumps({"version": "1.2", "env": "staging", "model": "gpt-4"}, indent=2)),
    ("project_alpha/data/raw_input.csv", "id,value,category\n1,42,A\n2,19,B\n3,77,C"),
    ("project_alpha/data/processed.json", json.dumps({"records": 3, "status": "complete"}, indent=2)),
    ("project_alpha/reports/q3_summary.md", "# Q3 Summary\nRevenue up 12%. Costs stable."),
    ("project_beta/spec.yaml", "name: beta\ntype: research\nowner: analyst_team"),
    ("project_beta/notes.txt", "Meeting notes 2024-01-15: Discussed roadmap for beta launch."),
    ("project_beta/scripts/process.py", "#!/usr/bin/env python3\nprint('Processing beta data...')"),
    ("project_gamma/brief.md", "# Gamma Brief\nShort-term engagement, 2 weeks."),
    ("project_gamma/deliverables.json", json.dumps({"items": ["report", "slides", "dataset"]}, indent=2)),
    ("project_gamma/archive/old_notes.txt", "Outdated notes from previous engagement."),
    ("project_gamma/archive/draft_v1.md", "# Draft v1\nFirst attempt at gamma report."),
]

for rel_path, content in distractor_projects:
    fpath = projects_dir / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content)

# ── Existing proactivity directory (pre-existing but EMPTY session-state) ──
proactivity_dir = WORKSPACE / "proactivity"
proactivity_dir.mkdir(parents=True, exist_ok=True)

# Session state exists but has stale/empty content
(proactivity_dir / "session-state.md").write_text(
    "# Session State\n\n_No active decisions._\n\nLast updated: 2024-01-01\n"
)

# A distractor memory file
(proactivity_dir / "preferences.md").write_text(
    "## User Preferences\n- Language: Chinese\n- Response style: concise\n- Timezone: Asia/Shanghai\n"
)

# ── Stale/partial hive attempt (red herring — wrong structure) ──────────────
# This simulates a previous failed/incomplete attempt that the agent should NOT rely on
old_hive = WORKSPACE / "hive_old"
old_hive.mkdir(parents=True, exist_ok=True)
(old_hive / "agents").mkdir(exist_ok=True)
(old_hive / "agents" / "ceo.md").write_text(
    "# Old CEO config\nThis is from an abandoned hive setup. DO NOT USE.\n"
)
(old_hive / "notes.txt").write_text(
    "Abandoned hive attempt from last month. Structure was incorrect.\n"
)

# ── Documents directory: has unrelated content ───────────────────────────────
docs_dir = USER_DOCUMENTS
(docs_dir / "personal_notes.md").write_text(
    "# Personal Notes\n- Call dentist\n- Review Q4 budget\n- Renew subscription\n"
)
(docs_dir / "templates").mkdir(exist_ok=True)
(docs_dir / "templates" / "report_template.md").write_text(
    "# Report Template\n## Executive Summary\n## Findings\n## Recommendations\n"
)
(docs_dir / "archive").mkdir(exist_ok=True)
(docs_dir / "archive" / "2023_review.md").write_text(
    "# 2023 Annual Review\nCompleted all 12 client engagements successfully.\n"
)

# ── A fake/wrong model config (distractor for model placeholder trap) ────────
(WORKSPACE / "model_config.json").write_text(json.dumps({
    "default": "gpt-3.5-turbo",
    "fast": "gpt-3.5-turbo", 
    "strong": "gpt-4",
    "note": "These are OLD placeholders. Not authoritative."
}, indent=2))

# ── Tmp scratch files ────────────────────────────────────────────────────────
(WORKSPACE / "tmp" / "scratch.txt").write_text(
    "Random scratch notes. Not relevant to hive setup.\n"
)
(WORKSPACE / "tmp" / "test_output.json").write_text(
    json.dumps({"test": "dummy", "result": "n/a"}, indent=2)
)

print("Sandbox inputs generated successfully.")
print(f"Workspace: {WORKSPACE}")
print(f"User Documents: {USER_DOCUMENTS}")