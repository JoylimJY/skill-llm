import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# Create an output/ directory to trigger the priority detection rule
(workspace / "output").mkdir(exist_ok=True)

# Create distractor project directories inside output/
(workspace / "output" / "old-project-alpha").mkdir(parents=True, exist_ok=True)
(workspace / "output" / "old-project-alpha" / "01 - Planning").mkdir(parents=True, exist_ok=True)
(workspace / "output" / "old-project-alpha" / "02 - Analysis").mkdir(parents=True, exist_ok=True)

# Distractor files in old project
(workspace / "output" / "old-project-alpha" / "01 - Planning" / "project-charter.md").write_text(
    "# Project Charter\nThis is an old project charter for alpha.\n"
)
(workspace / "output" / "old-project-alpha" / "02 - Analysis" / "market-analysis.md").write_text(
    "# Market Analysis\nOld analysis data from 2023.\n"
)
(workspace / "output" / "old-project-alpha" / "README.md").write_text(
    "# Old Project Alpha\nArchived project. Do not modify.\n"
)

# Create a second old project in output
(workspace / "output" / "legacy-food-report").mkdir(parents=True, exist_ok=True)
(workspace / "output" / "legacy-food-report" / "03 - Deep Research").mkdir(parents=True, exist_ok=True)
(workspace / "output" / "legacy-food-report" / "03 - Deep Research" / "old-research.md").write_text(
    "# Old Research\nThis is legacy content. Not related to current project.\n"
)

# Create distractor files at workspace root
(workspace / "notes.txt").write_text(
    "Random notes about farming. Not structured research.\n"
)
(workspace / "temp-ideas.md").write_text(
    "# Temp Ideas\n- hydroponics\n- vertical farms\n- city planning\n"
)
(workspace / "config.yaml").write_text(
    "project: urban-farming\nversion: 0.1\nstatus: draft\n"
)

# Create a src/ directory with distractor code
(workspace / "src").mkdir(exist_ok=True)
(workspace / "src" / "data_fetcher.py").write_text(
    "# placeholder data fetcher\ndef fetch(): pass\n"
)
(workspace / "src" / "parser.py").write_text(
    "# placeholder parser\ndef parse(data): return data\n"
)
(workspace / "src" / "utils.py").write_text(
    "# utilities\ndef clean(text): return text.strip()\n"
)

# Create a docs/ directory
(workspace / "docs").mkdir(exist_ok=True)
(workspace / "docs" / "overview.md").write_text(
    "# Project Docs\nGeneral documentation placeholder.\n"
)
(workspace / "docs" / "requirements.md").write_text(
    "# Requirements\n- Research urban farming\n- Generate reports\n"
)

# Create the main input file: a messy project brief that the agent must parse
input_brief = """# Urban Farming Futures — Research Project Brief

## Background

Our consultancy has been engaged by a municipal development agency to advise on the
feasibility of integrating urban agriculture into city planning frameworks. The client
needs evidence-based insights delivered quickly.

## Research Areas Requested

The client specifically needs us to investigate the following three areas deeply:

1. **Economics of Vertical Farming** — cost structures, ROI timelines, capital investment
   requirements, and economic viability compared to conventional agriculture at city scale.

2. **Hydroponics vs. Soil-Based Urban Growing** — comparative yield data, water usage,
   nutrient management, setup complexity, and suitability for different urban contexts.

3. **Regulatory Landscape for Urban Food Production** — zoning laws, food safety
   certification requirements, subsidy programs, and permitting challenges facing
   urban farms in major cities (focus on US and EU).

## Project Name

UrbanFarm-2025

## Deliverables

We need a structured research knowledge base with an overview document and individual
deep-dive reports per topic. The output should be immediately actionable for our
consultants presenting to city planners next month.

## Notes

- All research must be sourced and cited properly within the text
- We need specific recommendations and action items
- Avoid vague summaries — we need depth and usable conclusions
"""

(workspace / "project-brief.md").write_text(input_brief)

# Create a misleading directory at root level that should NOT be used (since output/ exists)
(workspace / "UrbanFarm-2025").mkdir(exist_ok=True)
(workspace / "UrbanFarm-2025" / "stale-notes.md").write_text(
    "# Stale Notes\nDo not use this directory for output.\n"
)

print("Workspace initialized successfully.")
print("Key file: /workspace/project-brief.md")
print("Output dir exists: /workspace/output/")