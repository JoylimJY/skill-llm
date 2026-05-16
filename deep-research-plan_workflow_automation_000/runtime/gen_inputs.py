import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# Create directory structure
dirs = [
    "plans",
    "reports",
    "reports/drafts",
    "reports/final",
    "data/raw",
    "data/processed",
    "data/cache",
    "logs",
    "config",
    "templates",
    "archive/2023",
    "archive/2024",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Create distractor files to simulate a real workspace

# 1. Old/malformed plan files in archive (distractors - wrong format)
old_plan_bad = {
    "title": "Quantum Computing Research",
    "questions": ["What is quantum computing?"],
    "output": "report.pdf"
    # Missing required fields: topic, research_questions, report_requirements
}
with open(workspace / "archive/2023/research-plan-old.json", "w") as f:
    json.dump(old_plan_bad, f, indent=2)

# 2. Another malformed plan missing report_requirements
old_plan_bad2 = {
    "topic": "AI in Finance",
    "research_questions": ["How is AI used in trading?"],
    # Missing report_requirements
}
with open(workspace / "archive/2024/research-plan-incomplete.json", "w") as f:
    json.dump(old_plan_bad2, f, indent=2)

# 3. A plan saved in wrong location (root instead of plans/)
wrong_location_plan = {
    "topic": "Blockchain",
    "research_questions": ["What is DeFi?"],
    "report_requirements": {"sections": ["summary"], "depth": "shallow"}
}
with open(workspace / "research-plan-2024.json", "w") as f:
    json.dump(wrong_location_plan, f, indent=2)

# 4. Config files
config_data = {
    "default_depth": "comprehensive",
    "default_min_sources": 8,
    "default_max_sources": 20,
    "output_dir": "reports/final"
}
with open(workspace / "config/research-defaults.json", "w") as f:
    json.dump(config_data, f, indent=2)

# 5. Template file (distractor - not a real plan)
template = {
    "topic": "PLACEHOLDER",
    "research_questions": ["QUESTION_1", "QUESTION_2"],
    "scope": {"include": [], "exclude": []},
    "report_requirements": {
        "sections": ["executive_summary", "findings", "conclusion", "references"],
        "depth": "comprehensive",
        "min_sources": 8
    }
}
with open(workspace / "templates/plan-template.json", "w") as f:
    json.dump(template, f, indent=2)

# 6. Log files
with open(workspace / "logs/session.log", "w") as f:
    f.write("2024-01-15 10:23:41 [INFO] Session started\n")
    f.write("2024-01-15 10:23:42 [INFO] Loading configuration\n")
    f.write("2024-01-15 10:24:01 [WARN] No active research plan found\n")
    f.write("2024-01-15 10:24:01 [INFO] Awaiting user input\n")

# 7. Previous report draft (distractor)
with open(workspace / "reports/drafts/quantum-draft.md", "w") as f:
    f.write("# Quantum Computing Report (DRAFT)\n\n")
    f.write("## Executive Summary\nThis draft explores quantum computing...\n\n")
    f.write("## Findings\nTBD\n\n## References\nTBD\n")

# 8. Data files
raw_data = [
    {"source": "pubmed", "id": "PMC123456", "title": "CRISPR advances 2023", "relevance": 0.92},
    {"source": "arxiv", "id": "2312.00001", "title": "Gene editing review", "relevance": 0.87},
]
with open(workspace / "data/raw/sample-sources.json", "w") as f:
    json.dump(raw_data, f, indent=2)

# 9. Processed data cache
with open(workspace / "data/cache/query-cache.json", "w") as f:
    json.dump({"last_query": "CRISPR therapeutics 2023", "results": 0, "cached_at": "2024-01-10"}, f, indent=2)

# 10. A misleading file named like a plan but in wrong subdir
misleading = {
    "topic": "CRISPR in oncology",
    "research_questions": ["What cancers are targeted by CRISPR?"],
    "report_requirements": {"sections": ["findings"], "depth": "brief", "min_sources": 3},
    "keywords": ["CRISPR", "cancer", "gene therapy"],  # This is wrong — plans shouldn't have HOW-to-search
    "search_engines": ["pubmed", "google_scholar"]  # Wrong — violates the "no HOW" principle
}
with open(workspace / "data/processed/crispr-plan-attempt.json", "w") as f:
    json.dump(misleading, f, indent=2)

# 11. A readme-like notes file (not a hint, just context noise)
with open(workspace / "config/notes.txt", "w") as f:
    f.write("Workspace initialized for biotech research operations.\n")
    f.write("Contact: research-team@biotech-internal.local\n")
    f.write("Last updated: 2024-01-15\n")

# 12. Archive metadata
with open(workspace / "archive/index.json", "w") as f:
    json.dump({"archived_plans": 2, "archived_reports": 0, "last_archive": "2024-01-01"}, f, indent=2)

print("Workspace scaffold generated successfully.")
print(f"Directories created: {len(dirs)}")
print(f"Distractor files created: 12")