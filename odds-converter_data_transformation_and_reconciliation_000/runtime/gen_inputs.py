import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Deep distractor directory structure ---
dirs = [
    "workspace/feeds/raw/nfl",
    "workspace/feeds/raw/nba",
    "workspace/feeds/processed",
    "workspace/analytics/models",
    "workspace/analytics/reports",
    "workspace/platform/config",
    "workspace/platform/integrations",
    "workspace/archive/2023",
    "workspace/archive/2024",
    "workspace/scripts",
]
for d in dirs:
    os.makedirs(f"/{d}", exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "/workspace/feeds/raw/nfl/week12_lines.csv": "team,spread,moneyline\nKC Chiefs,-6.5,-260\nBuffalo Bills,+6.5,+215\n",
    "/workspace/feeds/raw/nfl/week12_totals.csv": "game,total,over_price,under_price\nKC_BUF,52.5,-110,-110\n",
    "/workspace/feeds/raw/nba/games_nov.csv": "home,away,line\nLAL,GSW,-3.5\nBOS,MIA,+2\n",
    "/workspace/feeds/processed/last_run.log": "2024-11-14 02:31:00 - Processed 142 lines OK\n",
    "/workspace/analytics/models/elo_ratings.json": '{"KC":1742,"BUF":1688,"LAL":1601}\n',
    "/workspace/analytics/reports/weekly_summary.txt": "Week 12 summary: 14 markets processed, avg margin 4.2%\n",
    "/workspace/platform/config/endpoints.yaml": "sportsbook_api: https://internal.example.com/v2\nkalshi_api: https://trading-api.kalshi.com/trade-api/v2\n",
    "/workspace/platform/integrations/push_results.py": "# stub: pushes odds reconciliation results to dashboard\ndef push(data): pass\n",
    "/workspace/archive/2023/odds_snapshot.csv": "event,american_odds\nSuperbowl LVII,-130\nNBA Finals 2023,+140\n",
    "/workspace/archive/2024/reconciliation_log.txt": "Reconciliation completed 2024-03-01. 0 mismatches.\n",
    "/workspace/scripts/fetch_feeds.sh": "#!/bin/bash\n# placeholder fetch script\necho 'Fetching feeds...'\n",
}

for path, content in distractor_files.items():
    with open(path, "w") as f:
        f.write(content)

# --- THE ACTUAL PROBLEM INPUTS ---

# 1. A batch of American odds that need full conversion (the main batch job)
batch_odds_file = "/workspace/feeds/raw/batch_american_odds.txt"
with open(batch_odds_file, "w") as f:
    f.write("""# Incoming American odds from sportsbook feed - needs full format reconciliation
# These values must be batch-converted to all formats for the prediction market integration
-150
+200
-110
+350
-275
""")

# 2. A fractional odds feed (European format from partner exchange)
fractional_odds_file = "/workspace/feeds/raw/fractional_feed.txt"
with open(fractional_odds_file, "w") as f:
    f.write("""# European fractional odds - needs conversion for US platform
# Format: numerator/denominator
5/2
1/4
7/5
""")

# 3. Implied probability data (analyst estimates, some are raw percentages mistakenly not divided by 100)
implied_prob_file = "/workspace/feeds/raw/implied_probs.txt"
with open(implied_prob_file, "w") as f:
    f.write("""# Analyst implied probabilities - CAUTION: some entries may be in % form (e.g., 65 instead of 0.65)
# Each line: event_label, value
championship_game_home, 0.62
playoff_clincher_away, 65
big_rivalry_draw, 0.45
""")

# 4. A decimal odds entry that is INVALID (≤ 1.0) mixed with valid ones
decimal_odds_file = "/workspace/feeds/raw/decimal_feed.txt"
with open(decimal_odds_file, "w") as f:
    f.write("""# Decimal odds from Asian exchange
# Note: one entry may be malformed
2.80
0.75
1.65
""")

# 5. Instructions file (business context only, no technical hints)
instructions_file = "/workspace/TASK.md"
with open(instructions_file, "w") as f:
    f.write("""# Odds Reconciliation Task

Our platform receives odds from four different data feeds in different formats.
We need to consolidate them into a single unified reference document.

## Inputs

- `feeds/raw/batch_american_odds.txt` — American odds values (one per line, ignore comment lines)
- `feeds/raw/fractional_feed.txt` — Fractional odds from a European exchange
- `feeds/raw/implied_probs.txt` — Analyst probability estimates (watch out for bad entries)
- `feeds/raw/decimal_feed.txt` — Decimal odds from an Asian exchange (watch out for bad entries)

## Output

Produce a file called `odds_reconciliation_report.txt` in the workspace root.

The report must contain four sections, each clearly labeled:

1. BATCH CONVERSION (American odds table)
2. FRACTIONAL CONVERSIONS (each fractional value converted to all formats)
3. IMPLIED PROBABILITY CONVERSIONS (handle malformed entries per standard practice)
4. DECIMAL CONVERSIONS (flag any invalid decimal odds per standard practice, convert valid ones)
""")

print("Workspace generated successfully.")
print("Files created:")
for path in list(distractor_files.keys()) + [batch_odds_file, fractional_odds_file, implied_prob_file, decimal_odds_file, instructions_file]:
    print(f"  {path}")