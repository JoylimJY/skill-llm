import os
import random
import json
from pathlib import Path

random.seed(42)

# ── Base workspace ──────────────────────────────────────────────────────────
workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ── OpenClaw directory structure ────────────────────────────────────────────
openclaw_root = Path("/home/node/.openclaw")

# --- SOURCE AGENT: "research" ---
research_ws = openclaw_root / "workspace-research"
research_memory_dir = research_ws / "memory"
research_memory_dir.mkdir(parents=True, exist_ok=True)

# MEMORY.md for research agent
(research_ws / "MEMORY.md").write_text(
    "# Research Agent Long-Term Memory\n\n"
    "## Core Identity\n"
    "I am the Research Agent, specializing in financial market analysis and intelligence gathering.\n\n"
    "## Key Projects\n"
    "- Project Helios: Q1 2025 Emerging Markets Report\n"
    "- Project Orion: Real-time sentiment tracking pipeline\n\n"
    "## User Profile\n"
    "Primary user: Dr. Elena Vasquez, Senior Research Director\n"
    "Email: e.vasquez@finresearch.internal\n"
    "Phone: +1-555-0192\n"
    "Preferred report format: PDF with executive summary\n"
    "Personal note: Prefers morning briefings before 8 AM\n\n"
    "## Learned Preferences\n"
    "- Always cite Bloomberg data sources\n"
    "- Flag any data older than 72 hours\n"
)

# Daily memory files for research agent
daily_entries = {
    "2025-03-10.md": (
        "# March 10, 2025 - Research Briefing\n\n"
        "## Market Overview\n"
        "- S&P 500 declined 0.8% on inflation concerns\n"
        "- Tech sector led losses, down 1.2%\n\n"
        "## Key Findings\n"
        "- Fed minutes suggest two more rate hikes possible in 2025\n"
        "- European equities outperforming US counterparts\n\n"
        "## Action Items\n"
        "- Compile emerging markets exposure report\n"
        "- Review Q4 earnings surprises dataset\n"
    ),
    "2025-03-12.md": (
        "# March 12, 2025 - Research Briefing\n\n"
        "## Market Overview\n"
        "- Crude oil spiked 3.4% on supply disruption news\n"
        "- Energy sector gained 2.1%\n\n"
        "## Intelligence Notes\n"
        "- OPEC+ meeting rescheduled to March 28\n"
        "- Saudi Aramco production guidance revised upward\n\n"
        "## Data Sources\n"
        "- Bloomberg Terminal feed 06:30 UTC\n"
        "- Reuters commodities desk\n"
    ),
    "2025-03-15.md": (
        "# March 15, 2025 - Research Briefing\n\n"
        "## CRITICAL INTELLIGENCE: Q1 Rebalancing Signals\n"
        "Large institutional flows detected across fixed income:\n"
        "- 10Y Treasury yield crossed 4.75% threshold\n"
        "- Investment-grade spreads widening: +18bps week-over-week\n"
        "- High-yield spreads: +42bps, stress indicator triggered\n\n"
        "## Equity Desk Notes\n"
        "- Russell 2000 underperformance vs S&P 500: -230bps MTD\n"
        "- Financials sector rotation into defensives confirmed\n"
        "- VIX term structure inversion observed (front month > back month)\n\n"
        "## Analyst Recommendations\n"
        "- Increase duration hedge positions by 15%\n"
        "- Review leveraged loan book exposure\n"
        "- Prepare stress-test scenarios for 5%+ equity correction\n\n"
        "## Data Sources\n"
        "- Bloomberg Fixed Income Analytics: 07:00 UTC\n"
        "- ICE BofA Credit Index feed\n"
        "- CBOE volatility data\n"
    ),
    "2025-03-17.md": (
        "# March 17, 2025 - Research Briefing\n\n"
        "## Post-Rebalancing Analysis\n"
        "- Institutional flows normalized after Q1 rebalancing\n"
        "- Credit spreads retracing: -8bps from peak\n\n"
        "## Sector Watch\n"
        "- Healthcare outperforming: +1.8% YTD vs S&P flat\n"
        "- Consumer staples inflows accelerating\n\n"
        "## Notes\n"
        "- Weekly options expiry impact minimal this week\n"
    ),
    "2025-03-20.md": (
        "# March 20, 2025 - Research Briefing\n\n"
        "## FOMC Decision Day\n"
        "- Fed held rates steady at 5.25-5.50% (as expected)\n"
        "- Dot plot revised: median projection now 2 cuts in 2025\n\n"
        "## Market Reaction\n"
        "- Risk-on rally: S&P 500 +1.4%, NASDAQ +1.9%\n"
        "- 2Y yield fell 12bps, curve steepened\n\n"
        "## Forward Guidance\n"
        "- Watch PCE data release on March 28\n"
        "- Monitor bank earnings season starting April 11\n"
    ),
}

for filename, content in daily_entries.items():
    (research_memory_dir / filename).write_text(content)

# --- TARGET AGENT: "analyst" ---
analyst_ws = openclaw_root / "workspace-analyst"
analyst_memory_dir = analyst_ws / "memory"
analyst_memory_dir.mkdir(parents=True, exist_ok=True)

# MEMORY.md for analyst agent (existing)
(analyst_ws / "MEMORY.md").write_text(
    "# Analyst Agent Long-Term Memory\n\n"
    "## Core Identity\n"
    "I am the Analyst Agent, specializing in portfolio risk assessment and trade recommendation synthesis.\n\n"
    "## Key Projects\n"
    "- Project Atlas: Risk-adjusted return optimization model\n"
    "- Project Meridian: Client portfolio stress-testing suite\n\n"
    "## Learned Behaviors\n"
    "- Always present trade recommendations with confidence intervals\n"
    "- Cross-reference at least 3 data sources before flagging alerts\n"
    "- Use basis points (bps) for spread changes, not percentages\n"
)

# Analyst already has some memory files (different dates — no conflict)
(analyst_memory_dir / "2025-03-08.md").write_text(
    "# March 8, 2025 - Analyst Notes\n\n"
    "## Portfolio Review\n"
    "- Reviewed 14 client portfolios for Q1 rebalancing readiness\n"
    "- Flagged 3 portfolios with elevated duration risk\n\n"
    "## Risk Metrics\n"
    "- Average portfolio beta: 0.94\n"
    "- Modified duration: 6.2 years (target: 5.5)\n"
)

(analyst_memory_dir / "2025-03-11.md").write_text(
    "# March 11, 2025 - Analyst Notes\n\n"
    "## Stress Test Results\n"
    "- 200bps rate shock scenario: -8.3% portfolio impact\n"
    "- Credit spread widening (100bps): -2.1% impact\n\n"
    "## Recommendations\n"
    "- Reduce investment-grade duration by 0.7 years\n"
    "- Add 5% allocation to floating-rate instruments\n"
)

# --- DISTRACTOR FILES in workspace ---
# These are project files that should NOT mislead the agent
distractor_dir = workspace / "project_files"
distractor_dir.mkdir(exist_ok=True)

(distractor_dir / "config.json").write_text(json.dumps({
    "environment": "production",
    "log_level": "info",
    "agents": ["research", "analyst", "trader"],
    "memory_retention_days": 90
}, indent=2))

(distractor_dir / "agent_registry.yaml").write_text(
    "agents:\n"
    "  research:\n"
    "    type: intelligence_gathering\n"
    "    model: gpt-4\n"
    "    workspace: workspace-research\n"
    "  analyst:\n"
    "    type: risk_assessment\n"
    "    model: gpt-4\n"
    "    workspace: workspace-analyst\n"
    "  trader:\n"
    "    type: execution\n"
    "    model: gpt-4\n"
    "    workspace: workspace-trader\n"
)

(distractor_dir / "transfer_log.txt").write_text(
    "2025-01-15 09:22:11 | TRANSFER | research -> trader | MEMORY.md | SUCCESS\n"
    "2025-02-03 14:05:44 | TRANSFER | analyst -> main | 2025-02-01.md | SUCCESS\n"
    "2025-02-28 08:11:02 | LIST | research | 7 files found\n"
)

(distractor_dir / "risk_thresholds.json").write_text(json.dumps({
    "credit_spread_alert_bps": 40,
    "duration_max_years": 7.0,
    "vix_stress_threshold": 25,
    "equity_correction_trigger_pct": 5.0
}, indent=2))

reports_dir = workspace / "reports" / "q1_2025"
reports_dir.mkdir(parents=True, exist_ok=True)

(reports_dir / "preliminary_risk_report.md").write_text(
    "# Q1 2025 Preliminary Risk Report\n\n"
    "**Status:** DRAFT — Pending analyst review\n\n"
    "## Executive Summary\n"
    "Credit markets showing elevated stress signals as of mid-March 2025.\n"
    "Recommend immediate review of fixed income positioning.\n\n"
    "## Key Metrics\n"
    "- Portfolio VaR (95%, 1-day): $2.4M\n"
    "- Sharpe Ratio (YTD): 0.73\n"
    "- Maximum Drawdown: -3.2%\n"
)

(reports_dir / "data_sources.txt").write_text(
    "Bloomberg Terminal: Primary\n"
    "Refinitiv Eikon: Secondary\n"
    "ICE Data Services: Credit indices\n"
    "CBOE: Volatility data\n"
    "Federal Reserve H.15: Interest rates\n"
)

scripts_dir = workspace / "scripts"
scripts_dir.mkdir(exist_ok=True)

(scripts_dir / "run_stress_test.sh").write_text(
    "#!/bin/bash\n"
    "# Stress test runner\n"
    "echo 'Running portfolio stress tests...'\n"
    "python3 /workspace/scripts/stress_engine.py --scenario=q1_2025\n"
)

(scripts_dir / "backup_memories.sh").write_text(
    "#!/bin/bash\n"
    "# Memory backup script\n"
    "DATE=$(date +%Y%m%d)\n"
    "tar -czf /tmp/memory_backup_${DATE}.tar.gz /home/node/.openclaw/\n"
    "echo 'Backup complete'\n"
)

(scripts_dir / "cleanup_old_memories.py").write_text(
    "#!/usr/bin/env python3\n"
    "\"\"\"Removes memory files older than retention policy.\"\"\"\n"
    "import os\n"
    "from pathlib import Path\n"
    "from datetime import datetime, timedelta\n\n"
    "RETENTION_DAYS = 90\n"
    "OPENCLAW_ROOT = Path('/home/node/.openclaw')\n\n"
    "cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)\n"
    "for mem_file in OPENCLAW_ROOT.rglob('*.md'):\n"
    "    mtime = datetime.fromtimestamp(mem_file.stat().st_mtime)\n"
    "    if mtime < cutoff:\n"
    "        print(f'Would remove: {mem_file}')\n"
)

logs_dir = workspace / "logs"
logs_dir.mkdir(exist_ok=True)

(logs_dir / "agent_activity_2025-03.log").write_text(
    "[2025-03-15 06:45:12] research | MEMORY_WRITE | 2025-03-15.md | 847 bytes\n"
    "[2025-03-15 07:01:33] research | QUERY | fixed_income_spreads | 23ms\n"
    "[2025-03-15 07:15:44] analyst | QUERY | portfolio_stress | 45ms\n"
    "[2025-03-15 08:22:01] analyst | MEMORY_WRITE | 2025-03-15.md | PENDING\n"
    "[2025-03-15 09:00:05] research | ANALYSIS | q1_rebalancing | COMPLETE\n"
)

(logs_dir / "system_health.log").write_text(
    "[2025-03-20 00:00:01] SYSTEM | CPU: 12% | MEM: 34% | DISK: 67%\n"
    "[2025-03-20 01:00:01] SYSTEM | CPU: 8% | MEM: 33% | DISK: 67%\n"
    "[2025-03-20 06:00:01] SYSTEM | CPU: 45% | MEM: 51% | DISK: 67%\n"
)

# -- A fake "transfer" approach that naive agents might try (red herring) --
(workspace / "manual_transfer_attempt.sh").write_text(
    "#!/bin/bash\n"
    "# WARNING: This manual approach does NOT use the proper tool\n"
    "# cp /home/node/.openclaw/workspace-research/memory/2025-03-15.md \\\n"
    "#    /home/node/.openclaw/workspace-analyst/memory/\n"
    "# DO NOT USE: Bypasses identity adaptation and privacy filters\n"
)

print("Workspace generation complete.")
print(f"Research agent memories: {list((Path('/home/node/.openclaw/workspace-research/memory')).iterdir())}")
print(f"Analyst agent memories: {list((Path('/home/node/.openclaw/workspace-analyst/memory')).iterdir())}")