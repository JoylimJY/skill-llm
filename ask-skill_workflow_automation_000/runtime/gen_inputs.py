import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create a realistic deeply nested distractor structure simulating an investment research firm workspace
dirs = [
    "research/macro/2024/Q1",
    "research/macro/2024/Q2",
    "research/equities/tech",
    "research/equities/energy",
    "research/fixed_income",
    "templates/old_versions",
    "templates/v4_deprecated",
    "data/bloomberg/raw",
    "data/fred/cleaned",
    "reports/published",
    "reports/drafts",
    "config/agents",
    "config/prompts",
    "logs/sessions",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractors = {
    "research/macro/2024/Q1/fed_meeting_notes.txt": """March FOMC meeting summary.
Rate held at 5.25-5.50%.
Dot plot suggests 3 cuts in 2024.
Powell: 'inflation still elevated'
""",
    "research/macro/2024/Q2/gold_price_data.csv": """date,price_usd,volume
2024-01-02,2063.40,142300
2024-01-03,2044.20,98500
2024-01-04,2030.10,110200
2024-04-01,2257.80,201000
2024-04-12,2343.50,320000
""",
    "research/equities/tech/nvda_analysis.txt": """NVDA Q1 2024 revenue: $22.1B
Data center segment: $18.4B (+427% YoY)
AI infrastructure demand remains strong.
Target price range: $800-1000
""",
    "research/equities/energy/oil_macro.txt": """Brent crude: $87/bbl
OPEC+ production cuts extended through Q3 2024
Geopolitical risk premium: ~$5-8/bbl
""",
    "research/fixed_income/us_treasury_yields.txt": """10Y UST: 4.35%
2Y UST: 4.72%
Spread (2s10s): -37bps (inverted)
Real yield (10Y TIPS): 2.15%
""",
    "templates/old_versions/ask_v3_template.md": """# ask v3.0 DEPRECATED
DO NOT USE - superseded by v4.0 and v5.0

Old format:
- Section A: Overview
- Section B: Bull Case
- Section C: Bear Case
- Section D: Recommendation

Note: No convergence scoring in v3
""",
    "templates/v4_deprecated/ask_v4_template.md": """# ask v4.0 DEPRECATED
Uses sub-agent spawning - too complex for single sessions.
Replaced by v5.0 single-agent version.

v4.0 required:
- sub_agent_spawn(critic_mode=True)
- async callback handling
- External state management

DO NOT USE in production.
""",
    "data/bloomberg/raw/gold_fundamentals_2024.txt": """Gold Fundamentals Report - Bloomberg Raw Feed
Central bank purchases 2023: 1037 tonnes (record)
India/China demand YoY: +18%
ETF flows 2024 YTD: -45 tonnes (outflows)
Mining supply growth: +1.2% YoY
Real interest rate sensitivity: -0.85 correlation with gold
USD Index (DXY) correlation: -0.72
""",
    "data/fred/cleaned/inflation_expectations.txt": """5Y5Y Forward inflation breakeven: 2.28%
Michigan 1Y inflation expectations: 3.1%
Cleveland Fed median CPI: 3.6%
PCE (Fed preferred): 2.7%
Core PCE: 2.8%
""",
    "config/agents/analyst_config.json": """{
  "agent_name": "investment_analyst",
  "version": "5.0",
  "frameworks": ["ask", "dcf", "macro_overlay"],
  "output_format": "markdown",
  "session_mode": "single_agent"
}
""",
    "config/prompts/system_prompt.txt": """You are a senior investment research analyst.
Your frameworks include: ask v5.0, standard DCF, macro overlay analysis.
Always cite sources with confidence levels.
Output must be in structured markdown.
""",
    "logs/sessions/session_2024_04_15.log": """[09:32:11] ask framework triggered
[09:32:11] topic: US dollar outlook
[09:32:45] analysis complete - 5 sections generated
[09:32:45] convergence score: 11/16 - medium confidence
[09:32:45] session closed
""",
    "reports/published/gold_q1_2024_brief.txt": """PUBLISHED - Q1 2024 Gold Market Brief
Executive Summary: Gold outperformed in Q1 2024 (+8.1%)
Key drivers: Central bank demand, geopolitical risk, rate cut expectations
Price range Q1: $2000-$2343
Next review: Q2 2024
""",
    "reports/drafts/fed_pivot_impact.txt": """DRAFT - Impact of Fed Pivot on Asset Classes
Status: Incomplete - needs structured analysis
Question: How will the first Fed rate cut affect gold?
Author notes: Need to use ask framework for full treatment
TODO: Run through v5.0 template
""",
}

for filepath, content in distractors.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# Create the task instruction file — just the business request, no hints about the format
task_brief = """RESEARCH REQUEST
================
From: Portfolio Strategy Team
To: Research Analyst
Date: 2024-04-15

Question for structured analysis:

"美联储首次降息对黄金价格的影响：看多还是看空？"

Please produce a complete structured research analysis on this question and save it as:
    analysis_output.md

Reference the analytical framework documented in SKILL.md.
"""

with open(os.path.join(workspace, "TASK_BRIEF.txt"), "w", encoding="utf-8") as f:
    f.write(task_brief)

print("Workspace generated successfully.")
print(f"Files created: {len(distractors)} distractor files + 1 task brief")