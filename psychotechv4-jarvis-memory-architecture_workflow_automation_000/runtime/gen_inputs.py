import os
import json
import random
from pathlib import Path
from datetime import datetime, timedelta, timezone

random.seed(42)

WORKSPACE = Path("/workspace")

# --- Create directory structure ---
dirs = [
    "memory/diary",
    "memory/dreams",
    "templates",
    "projects/alpha",
    "projects/beta",
    "logs/archive",
    "reports",
    "config",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# --- Fixed date context ---
# "Today" is 2026-07-15, "yesterday" is 2026-07-14
TODAY = "2026-07-15"
YESTERDAY = "2026-07-14"

# ============================================================
# DISTRACTOR FILES (10+ files that should NOT be touched)
# ============================================================

(WORKSPACE / "projects/alpha/analysis.py").write_text(
    "# alpha analysis\nimport pandas as pd\n\ndef run(): pass\n"
)

(WORKSPACE / "projects/beta/config.yaml").write_text(
    "model: gpt-4\ntemperature: 0.7\nmax_tokens: 512\n"
)

(WORKSPACE / "logs/archive/2026-07-10.log").write_text(
    "[INFO] Archive log from 2026-07-10. Stale data. Do not process.\n"
)

(WORKSPACE / "reports/weekly_summary.txt").write_text(
    "Week of July 6: Revenue up 3.2%. No anomalies detected.\n"
)

(WORKSPACE / "config/alerts.json").write_text(
    json.dumps({"threshold": 0.05, "email": "ops@example.com"}, indent=2)
)

(WORKSPACE / "templates/MEMORY.md").write_text(
    """# Memory

## Identity
[Who you are]

## Operator Preferences
[Key preferences]

## Infrastructure
[Key systems]

## Lessons Learned
[Hard-won lessons]

## Ongoing Projects
[Active context]
"""
)

(WORKSPACE / "templates/strategy-notes.md").write_text(
    """# Strategy Notes

## Market Scanning
- [Add learnings here]

## Platform Engagement
- [Add learnings here]
"""
)

(WORKSPACE / "templates/heartbeat-state.json").write_text(
    json.dumps({
        "lastChecks": {
            "email": None,
            "calendar": None,
            "weather": None,
            "social": None,
            "market_scanner": None
        }
    }, indent=2)
)

(WORKSPACE / "templates/cron-inbox.md").write_text(
    "# Cron Inbox\n\n*(empty)*\n"
)

(WORKSPACE / "templates/platform-posts.md").write_text(
    """# Platform Posts

## [2026-07-01 09:00] Initial test post
- **Posted:** 2026-07-01 09:00 AM EST
- **Thread/URL:** https://platform.example.com/post/001
- First test post for platform integration.
- [View ↗](https://platform.example.com/post/001)
"""
)

(WORKSPACE / "memory/dreams/2026-07-14.md").write_text(
    """# Dreams -- 2026-07-14

## 02:00 AM -- Market Maze
Wandered through endless order books. Every trade I made dissolved before execution.
"""
)

(WORKSPACE / "projects/alpha/backtest_results.csv").write_text(
    "date,strategy,pnl,sharpe\n"
    "2026-07-01,momentum,+420,1.8\n"
    "2026-07-08,mean_reversion,-130,0.4\n"
    "2026-07-14,momentum,+610,2.1\n"
)

(WORKSPACE / "reports/platform_audit.md").write_text(
    """# Platform Audit -- 2026-07

No duplicate posts detected as of 2026-07-12.
"""
)

(WORKSPACE / "config/schedule.json").write_text(
    json.dumps({
        "cron_jobs": [
            {"name": "market_scanner", "interval_minutes": 30},
            {"name": "social_checker", "interval_minutes": 60},
        ]
    }, indent=2)
)

# ============================================================
# EXISTING MEMORY.md (partially initialized, needs distillation)
# ============================================================
(WORKSPACE / "MEMORY.md").write_text(
    """# Memory

## Identity
I am an autonomous trading and analytics agent. I run cron jobs overnight to scan markets and manage platform presence.

## Operator Preferences
- Prefer conservative risk: max 2% drawdown per trade
- Report significant wins and losses immediately
- Strategy updates must be dated

## Infrastructure
- Market scanner: runs every 30 min via cron
- Platform poster: runs every 60 min via cron
- Workspace: /workspace

## Lessons Learned
- 2026-07-10: Always validate ticker symbols before placing orders. Invalid tickers caused a 45-min delay.

## Ongoing Projects
- Alpha strategy backtesting (see projects/alpha/)
- Beta config tuning (see projects/beta/)
"""
)

# ============================================================
# EXISTING DAILY LOG for YESTERDAY (with some entries)
# ============================================================
(WORKSPACE / f"memory/{YESTERDAY}.md").write_text(
    f"""# {YESTERDAY}

## 08:00 -- Session Start
Loaded memory and reviewed overnight cron results. All systems nominal.

## 11:30 -- Market Scanner Check
Scanner ran 24 cycles overnight. Detected 3 potential momentum setups in small-cap tech.

## 16:45 -- Strategy Tweak
Adjusted momentum threshold from 0.03 to 0.025 after reviewing backtest results.
"""
)

# ============================================================
# heartbeat-state.json (stale, needs updating after inbox processing)
# Last checks are from 2026-07-14 at various times
# Unix timestamps for 2026-07-14:
#   08:00 UTC = 1752480000
#   14:00 UTC = 1752501600
# ============================================================
stale_ts = {
    "email": 1752480000,       # 2026-07-14 08:00 UTC
    "calendar": 1752480000,    # 2026-07-14 08:00 UTC
    "weather": None,
    "social": 1752501600,      # 2026-07-14 14:00 UTC
    "market_scanner": 1752501600  # 2026-07-14 14:00 UTC
}
(WORKSPACE / "memory/heartbeat-state.json").write_text(
    json.dumps({"lastChecks": stale_ts}, indent=2)
)

# ============================================================
# EXISTING strategy-notes.md (sparse, needs new entry)
# ============================================================
(WORKSPACE / "memory/strategy-notes.md").write_text(
    """# Strategy Notes

## Market Scanning
- High-volume breakouts above 20-day MA are most reliable (observed 2026-07-10)
- Avoid scanning during first 30 min of market open (noise too high, learned 2026-07-11)

## Platform Engagement
- Technical analysis threads get 3x more engagement than news commentary (learned 2026-07-12)
- Post between 9-11 AM EST for maximum reach

## Risk Management
- Never exceed 2% portfolio drawdown on a single position
"""
)

# ============================================================
# memory/platform-posts.md (existing tracking file)
# ============================================================
(WORKSPACE / "memory/platform-posts.md").write_text(
    """# Platform Posts

## [2026-07-14 10:15] Momentum Breakout Alert -- NVDA
- **Posted:** 2026-07-14 10:15 AM EST
- **Thread/URL:** https://fintwit.example.com/post/9821
- Shared momentum signal for NVDA with chart analysis.
- [View ↗](https://fintwit.example.com/post/9821)

## [2026-07-14 14:30] Weekly Backtest Results Summary
- **Posted:** 2026-07-14 02:30 PM EST
- **Thread/URL:** https://fintwit.example.com/post/9834
- Posted summary of week's backtest results. Momentum strategy up 14.5% vs benchmark.
- [View ↗](https://fintwit.example.com/post/9834)
"""
)

# ============================================================
# THE CORE PROBLEM: cron-inbox.md with 4 entries
# Agent must:
# 1. Process ALL entries into today's daily log (memory/2026-07-15.md)
# 2. Identify the SIGNIFICANT entry and promote it to MEMORY.md
# 3. Update strategy-notes.md with the strategic learning
# 4. Update heartbeat-state.json: set market_scanner to a current-ish timestamp
# 5. Clear inbox (keep header only)
# ============================================================
(WORKSPACE / "memory/cron-inbox.md").write_text(
    """# Cron Inbox

## [2026-07-15 02:14] Market Scanner -- Momentum Signal: TSLA Breakout
Detected TSLA breaking above 20-day MA on 2.3x average volume at $287.40.
Signal strength: HIGH. This matches our primary momentum criteria exactly.
Position sizing recommendation: 1.5% portfolio allocation.

## [2026-07-15 03:47] Market Scanner -- Mean Reversion Failure on AAPL
AAPL mean-reversion trade triggered but reversed immediately. Loss: -0.4% portfolio.
Root cause: earnings whisper was in opposite direction. Mean reversion fails near earnings.
This is the THIRD time this pattern has caused a loss (also 2026-06-18 and 2026-05-30).

## [2026-07-15 05:30] Platform Poster -- Scheduled Post Skipped
Attempted to post overnight market recap but detected duplicate: same content posted at 14:30 yesterday.
Anti-duplicate check worked correctly. No post made.

## [2026-07-15 06:01] Market Scanner -- Daily Scan Cycle Complete
Completed 4 overnight scan cycles (02:00, 03:00, 04:00, 05:00).
No additional signals beyond TSLA breakout. All systems nominal. Scanner healthy.
"""
)

print("Workspace initialized successfully.")
print(f"Today: {TODAY}, Yesterday: {YESTERDAY}")
print("Files created:")
for f in sorted(WORKSPACE.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(WORKSPACE)}")