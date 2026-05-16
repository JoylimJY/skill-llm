import os
import json
import random

random.seed(42)

workspace = "/workspace"

# Create directory structure with distractor files
dirs = [
    "out",
    "reference",
    "data/teams",
    "data/historical",
    "models/archived",
    "models/v2",
    "scripts/utils",
    "scripts/legacy",
    "config",
    "logs",
    "docs/internal",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- DISTRACTOR FILES ---

# Fake old bracket picks (wrong format - uses team names not seeds)
old_bracket = {
    "picks": [
        {"round": 1, "winner": "Duke", "game": 1},
        {"round": 1, "winner": "Kansas", "game": 2},
        {"round": 1, "winner": "Gonzaga", "game": 3},
    ],
    "format": "legacy-v1",
    "note": "DO NOT USE - deprecated format"
}
with open(os.path.join(workspace, "models/archived/old_bracket_2023.json"), "w") as f:
    json.dump(old_bracket, f, indent=2)

# Fake stats CSV
teams_csv = """seed,team,elo,off_rating,def_rating,ppg,momentum
1,Houston,2187,118.4,92.1,82.3,0.87
2,Tennessee,2145,112.3,89.4,78.9,0.79
3,Iowa_State,2098,110.1,91.2,76.4,0.72
4,Duke,2076,116.2,95.3,81.1,0.68
5,Michigan_St,2034,108.9,93.1,74.8,0.61
6,Illinois,2011,107.2,94.8,73.2,0.55
7,Marquette,1989,109.4,96.2,75.6,0.51
8,Mississippi_St,1967,105.1,97.3,71.4,0.47
9,Memphis,1945,103.2,98.1,69.8,0.44
10,Nevada,1923,101.5,99.4,68.2,0.38
11,New_Mexico,1901,99.8,100.2,66.7,0.32
12,James_Madison,1879,97.6,101.5,64.3,0.28
13,Charleston,1857,95.4,103.1,62.8,0.22
14,Oakland,1835,93.2,104.8,61.2,0.18
15,Longwood,1813,91.1,106.2,59.7,0.12
16,Wagner,1791,88.9,108.1,58.1,0.08"""

with open(os.path.join(workspace, "data/teams/team_stats_2024.csv"), "w") as f:
    f.write(teams_csv)

# Fake wallet config (distractor)
wallet_config = {
    "network": "base-mainnet",
    "rpc": "https://mainnet.base.org",
    "contract": "0xBracketsBot1234567890abcdef",
    "note": "wallet config placeholder"
}
with open(os.path.join(workspace, "config/wallet.json"), "w") as f:
    json.dump(wallet_config, f, indent=2)

# Fake incomplete policy module (wrong export name - distractor)
wrong_policy = """// OLD POLICY - DO NOT USE
// This uses wrong export name
module.exports = {
  pickWinner: function(teamA, teamB) {
    // wrong function name
    return teamA.seed < teamB.seed ? teamA.seed : teamB.seed;
  }
};
"""
with open(os.path.join(workspace, "models/archived/wrong_policy_v1.js"), "w") as f:
    f.write(wrong_policy)

# Fake README fragment (incomplete, misleading)
misleading_readme = """# Bracket Tool Notes (DRAFT)

Usage: bracketsbot pick --team <name>   ← THIS IS WRONG, ignore

Old approach: manually set winners by team name string.
Submit: use bracketsbot submit --wallet <addr>   ← ALSO WRONG

Stats module should export: selectWinner()   ← WRONG EXPORT NAME
"""
with open(os.path.join(workspace, "docs/internal/DRAFT_NOTES.md"), "w") as f:
    f.write(misleading_readme)

# Fake historical results
historical = {
    "year": 2023,
    "champion": "Connecticut",
    "champion_seed": 4,
    "upsets": [
        {"seed": 15, "beat": 2, "round": 1},
        {"seed": 13, "beat": 4, "round": 1}
    ]
}
with open(os.path.join(workspace, "data/historical/ncaa_2023_results.json"), "w") as f:
    json.dump(historical, f, indent=2)

# Fake log files
with open(os.path.join(workspace, "logs/run_20240301.log"), "w") as f:
    f.write("2024-03-01 10:00:00 INFO Starting bracket generation\n")
    f.write("2024-03-01 10:00:01 ERROR walk-run-policy: module not found\n")
    f.write("2024-03-01 10:00:02 ERROR Could not load policy module\n")

# Fake config with wrong file paths
bad_config = {
    "output_dir": "./results",  # wrong dir
    "policy_file": "./policies/model.py",  # wrong extension
    "format": "csv"  # wrong format
}
with open(os.path.join(workspace, "config/bracket_config.json"), "w") as f:
    json.dump(bad_config, f, indent=2)

# Partial/broken predictions file (should NOT be used as final output)
broken_predictions = {
    "picks": [1, 2],
    "complete": False,
    "error": "incomplete run"
}
with open(os.path.join(workspace, "out/partial_run.json"), "w") as f:
    json.dump(broken_predictions, f, indent=2)

# Fake utility scripts (distractors)
with open(os.path.join(workspace, "scripts/utils/seed_lookup.js"), "w") as f:
    f.write("// Utility: looks up seed by team name\nconst seeds = {};\nmodule.exports = seeds;\n")

with open(os.path.join(workspace, "scripts/legacy/old_submit.sh"), "w") as f:
    f.write("#!/bin/bash\n# DEPRECATED\n# bracketsbot submit --picks $1\necho 'Use new workflow'\n")

# Version file
with open(os.path.join(workspace, "config/version.json"), "w") as f:
    json.dump({"bracketsbot_version": "2.4.1", "schema": "v3"}, f, indent=2)

# Fake models/v2 distractor
with open(os.path.join(workspace, "models/v2/placeholder.txt"), "w") as f:
    f.write("Model v2 directory - place JS policy modules here\n")

# A task description file (the task prompt context, not hints)
task_context = """TASK: Automated Bracket Generation

Sports Analytics Team Request:
- Build a stats-driven bracket for BracketsBot 2024 NCAA tournament
- Team stats available in data/teams/team_stats_2024.csv
- Need validation step before sharing
- Output must be shareable via frontend link for human review
- No wallet signing needed from CLI
"""
with open(os.path.join(workspace, "TASK_CONTEXT.txt"), "w") as f:
    f.write(task_context)

print("Workspace initialized successfully.")
print(f"Created {len(dirs)} directories with distractor files.")