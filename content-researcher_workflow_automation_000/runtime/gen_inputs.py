import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# Create realistic deeply-nested directory structure with distractor files
dirs = [
    "projects/edtech-research/2024/q1",
    "projects/edtech-research/2024/q2",
    "projects/edtech-research/2024/q3",
    "projects/edtech-research/2025/q1",
    "projects/edtech-research/competitors",
    "projects/edtech-research/raw_data",
    "reports/monthly",
    "reports/weekly",
    "reports/ad_hoc",
    "scripts/automation",
    "scripts/data_processing",
    "content/drafts",
    "content/published",
    "config",
    "logs",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files mimicking a real content team workspace
distractor_files = {
    "projects/edtech-research/2024/q1/market_overview.md": "# Q1 2024 Market Overview\n\nPreliminary notes on online learning landscape.\n\n- Coursera revenue up 12%\n- Udemy user base growing\n- Khan Academy free model pressure",
    "projects/edtech-research/2024/q2/competitor_notes.txt": "Competitor notes - Q2 2024\nDuolingo: aggressive push into corporate training\nMasterclass: celebrity-driven content model\nSkillshare: subscription fatigue reported",
    "projects/edtech-research/2024/q3/trends.csv": "keyword,volume,trend\nonline learning,45000,up\ne-learning platforms,23000,stable\nmicrolearning,12000,up\nbootcamp,8900,down",
    "projects/edtech-research/2025/q1/brainstorm.md": "# 2025 Research Ideas\n\n- Focus on AI tutoring tools\n- Corporate upskilling demand post-layoffs\n- Certification credibility studies",
    "projects/edtech-research/competitors/coursera_profile.json": json.dumps({"name": "Coursera", "founded": 2012, "courses": 7000, "users_millions": 148}),
    "projects/edtech-research/competitors/udemy_profile.json": json.dumps({"name": "Udemy", "founded": 2010, "courses": 213000, "users_millions": 65}),
    "projects/edtech-research/raw_data/search_dump_old.txt": "Raw dump from old search tool - 2023-11-01\nquery: online course platforms\nresults: 45\n[truncated - legacy format]",
    "reports/monthly/2025-03-report.md": "# March 2025 Monthly Report\n\nContent team output: 12 articles, 3 videos\nTop performing keyword: 'AI learning tools'",
    "reports/weekly/week14.md": "# Week 14 Summary\n\nResearch tasks pending: competitor analysis for EdTech sector\nBlocking: no structured data pipeline yet",
    "reports/ad_hoc/pivot_analysis.txt": "Ad hoc note: team requested automated research for 3 keywords:\n1. online learning platforms\n2. e-learning trends\n3. EdTech startups\nNote: output must feed into our JSON ingestion pipeline",
    "scripts/automation/run_research.sh.bak": "#!/bin/bash\n# OLD SCRIPT - deprecated\n# content-researcher --keywords 'AI' --output old_report.md\necho 'This script is outdated'",
    "scripts/data_processing/parse_json.py": "import json\nimport sys\n\ndef parse_research(filepath):\n    with open(filepath) as f:\n        data = json.load(f)\n    print(f\"Found {len(data.get('results', []))} results\")\n    return data\n\nif __name__ == '__main__':\n    parse_research(sys.argv[1])",
    "content/drafts/edtech_article_draft.md": "# The Future of Online Learning\n\n[DRAFT - needs research backing]\n\nThe e-learning industry is projected to reach $400B by 2026...\n\n[TODO: insert sourced statistics and recent news]",
    "content/published/intro_to_edtech.md": "# Introduction to EdTech\n\nPublished: 2025-01-10\n\nEducational technology has transformed how we learn...",
    "config/team_settings.yaml": "team: content-research\ndefault_output_dir: reports/ad_hoc\npreferred_format: json\nai_budget_tier: economy\nmax_api_calls_per_run: 50",
    "logs/last_run.log": "2025-03-28 14:22:01 INFO Starting content research pipeline\n2025-03-28 14:22:05 ERROR summarize: model timeout\n2025-03-28 14:22:05 WARN Falling back to no-summary mode\n2025-03-28 14:22:10 INFO Completed with 0 summaries",
}

for filepath, content in distractor_files.items():
    full_path = workspace / filepath
    full_path.write_text(content, encoding="utf-8")

# Create the mock `claw` binary that simulates web_search tool
claw_mock = r"""#!/usr/bin/env python3
import sys
import json
import hashlib

# Parse: claw tools web_search --query "..." --count N
args = sys.argv[1:]

# Find query and count from args
query = ""
count = 5
i = 0
while i < len(args):
    if args[i] == '--query' and i+1 < len(args):
        query = args[i+1]
        i += 2
    elif args[i] == '--count' and i+1 < len(args):
        count = int(args[i+1])
        i += 2
    else:
        i += 1

# Deterministic fake results based on query hash
seed = int(hashlib.md5(query.encode()).hexdigest()[:8], 16)

FAKE_SOURCES = [
    "techcrunch.com", "edweek.org", "elearningindustry.com", "forbes.com",
    "venturebeat.com", "wired.com", "theverge.com", "medium.com",
    "bloomberg.com", "reuters.com", "businessinsider.com", "cnbc.com"
]

FAKE_TITLES_TEMPLATES = [
    "{q}: New Study Reveals Key Trends",
    "How {q} Is Reshaping the Industry in 2025",
    "Top 10 Insights on {q} You Need to Know",
    "{q} Market Report: Growth Projections",
    "Experts Weigh In on the Future of {q}",
    "{q}: Breaking News and Analysis",
    "The Complete Guide to {q}",
    "{q} vs Traditional Approaches: A Comparison",
]

results = []
for i in range(count):
    idx = (seed + i * 7) % len(FAKE_SOURCES)
    title_idx = (seed + i * 3) % len(FAKE_TITLES_TEMPLATES)
    source = FAKE_SOURCES[idx]
    title = FAKE_TITLES_TEMPLATES[title_idx].format(q=query[:30])
    url_slug = title.lower().replace(" ", "-").replace(":", "").replace("'", "")[:40]
    url = f"https://{source}/articles/{url_slug}-{seed+i}"
    snippet = f"This article discusses {query} with focus on market dynamics, emerging players, and technological innovations shaping the landscape in 2025."
    results.append({
        "title": title,
        "url": url,
        "source": source,
        "snippet": snippet
    })

output = {"query": query, "results": results}
print(json.dumps(output))
"""

claw_path = Path("/usr/local/bin/claw")
claw_path.write_text(claw_mock, encoding="utf-8")
claw_path.chmod(0o755)

# Create the mock `summarize` binary
summarize_mock = r"""#!/usr/bin/env python3
import sys
import hashlib

# Read from stdin or --text argument
text = ""
model = "google/gemini-3-flash-preview"

args = sys.argv[1:]
i = 0
while i < len(args):
    if args[i] == '--model' and i+1 < len(args):
        model = args[i+1]
        i += 2
    elif args[i] == '--text' and i+1 < len(args):
        text = args[i+1]
        i += 2
    else:
        i += 1

if not text:
    import sys as _sys
    text = _sys.stdin.read()

# Generate deterministic fake summary
h = hashlib.md5(text.encode()).hexdigest()[:6]
summary = f"[Summary-{h} via {model}] This content covers key developments in the topic area, highlighting market trends, stakeholder perspectives, and future implications for practitioners and investors alike."
print(summary)
"""

summarize_path = Path("/usr/local/bin/summarize")
summarize_path.write_text(summarize_mock, encoding="utf-8")
summarize_path.chmod(0o755)

# Create the content-researcher script (the skill being tested)
content_researcher_script = r"""#!/usr/bin/env python3
"""
# The actual content-researcher script will be created in setup_script
# Here we just create a placeholder marker so the workspace is realistic

marker_path = workspace / "config" / "installed_skills.txt"
marker_path.write_text(
    "Installed OpenClaw Skills:\n- content-researcher v1.2.0\n- summarize v0.9.1\n- web_search v1.0.0\n",
    encoding="utf-8"
)

print("Workspace initialized successfully.")
print(f"Created {len(distractor_files)} distractor files across {len(dirs)} directories.")