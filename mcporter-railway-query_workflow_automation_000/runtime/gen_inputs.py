import os
import json
import random
import stat

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── distractor directory structure ──────────────────────────────────────────
dirs = [
    "scripts",
    "references",
    "logs",
    "data/raw",
    "data/processed",
    "config/backup",
    "reports/2025",
    "reports/2026",
    "tmp",
    "archive/old_queries",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# distractor files
distractors = {
    "logs/query_20260201.log": "2026-02-01 08:12:33 INFO Query executed: SHH->HZH\n2026-02-01 08:12:35 INFO 12 results returned\n",
    "logs/query_20260210.log": "2026-02-10 14:05:11 INFO Query executed: AOH->NKH\n2026-02-10 14:05:13 INFO 7 results returned\n",
    "data/raw/tickets_20260201.txt": "G1234 08:00 10:30 上海虹桥->杭州\nG5678 09:00 11:15 上海虹桥->杭州\n",
    "data/processed/summary_feb.csv": "date,route,count\n2026-02-01,SHH-HZH,12\n2026-02-02,SHH-HZH,9\n",
    "config/backup/old_config.json": json.dumps({"mcpServers": {"old12306": {"command": "node", "args": ["/usr/local/lib/old-12306-mcp/index.js"]}}}),
    "references/station-codes.md": """# Station Codes Reference

| 城市 | 代码 |
|------|------|
| 上海 | SHH |
| 上海虹桥 | AOH |
| 杭州 | HZH |
| 无锡 | WXH |
| 江阴 | KYH |
| 南京南 | NKH |
| 北京 | BJP |
| 广州 | GZH |
| 深圳北 | IOQ |
| 成都东 | ICW |
| 武汉 | WHN |
| 苏州 | SZH |
""",
    "references/query-examples.md": """# Query Examples

## Example 1: Basic G-train query
```
mcporter call 12306.get-tickets date="2026-03-01" fromStation="SHH" toStation="NKH" trainFilterFlags="G" --config ~/.mcporter/mcporter.json
```

## Example 2: Morning intercity trains
```
mcporter call 12306.get-tickets date="2026-03-01" fromStation="HZH" toStation="WXH" trainFilterFlags="GD" earliestStartTime=6 latestStartTime=12 sortFlag="startTime" --config ~/.mcporter/mcporter.json
```

## Example 3: Station code lookup
```
mcporter call 12306.get-station-code-of-citys citys="北京|上海|杭州" --config ~/.mcporter/mcporter.json
```
""",
    "archive/old_queries/q_20251201.sh": "#!/bin/bash\nmcporter call 12306.get-tickets date=\"2025-12-01\" fromStation=\"AOH\" toStation=\"HZH\" trainFilterFlags=\"GD\" --config ~/.mcporter/mcporter.json\n",
    "archive/old_queries/q_20251215.sh": "#!/bin/bash\nmcporter call 12306.get-tickets date=\"2025-12-15\" fromStation=\"NKH\" toStation=\"HZH\" trainFilterFlags=\"G\" earliestStartTime=7 latestStartTime=11 --config ~/.mcporter/mcporter.json\n",
    "tmp/scratch.txt": "TODO: need to check HZH -> NKH evening trains\nsomething about GD filter?\nduration sort?\n",
    "reports/2025/annual_travel.txt": "Total trips: 47\nMost used route: AOH-HZH\nAverage duration: 1h 20min\n",
    "reports/2026/q1_plan.txt": "Q1 2026 travel plan:\n- Feb 18: Shanghai -> Kunming\n- Mar 5: Hangzhou -> Nanjing\n- Mar 20: Nanjing -> Beijing\n",
}
for rel_path, content in distractors.items():
    full_path = os.path.join(workspace, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# ── scripts/ (mentioned in SKILL.md, must exist but are NOT the solution) ───
scripts = {
    "scripts/query-afternoon.sh": """#!/bin/bash
# Query afternoon trains (12:00-18:00)
# Usage: ./scripts/query-afternoon.sh <date> <fromStation> <toStation>
DATE=$1
FROM=$2
TO=$3
mcporter call 12306.get-tickets \\
  date="$DATE" \\
  fromStation="$FROM" \\
  toStation="$TO" \\
  trainFilterFlags="GD" \\
  earliestStartTime=12 \\
  latestStartTime=18 \\
  sortFlag="startTime" \\
  --config ~/.mcporter/mcporter.json
""",
    "scripts/query-tickets.sh": """#!/bin/bash
# Query all-day trains
# Usage: ./scripts/query-tickets.sh <date> <fromStation> <toStation>
DATE=$1
FROM=$2
TO=$3
mcporter call 12306.get-tickets \\
  date="$DATE" \\
  fromStation="$FROM" \\
  toStation="$TO" \\
  trainFilterFlags="GD" \\
  --config ~/.mcporter/mcporter.json
""",
    "scripts/get-station-code.sh": """#!/bin/bash
# Get station code for a city
# Usage: ./scripts/get-station-code.sh <city_name>
CITY=$1
mcporter call 12306.get-station-code-of-citys \\
  citys="$CITY" \\
  --config ~/.mcporter/mcporter.json
""",
}
for rel_path, content in scripts.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    os.chmod(full_path, 0o755)

# ── intentionally broken / misleading config ────────────────────────────────
# Place a stale/broken mcporter config in a non-standard location to mislead
broken_cfg_dir = os.path.join(workspace, "config")
os.makedirs(broken_cfg_dir, exist_ok=True)
with open(os.path.join(broken_cfg_dir, "mcporter.json"), "w") as f:
    json.dump({
        "mcpServers": {
            "12306": {
                "command": "node",
                "args": ["/usr/local/lib/WRONG-PATH/12306-mcp/index.js"],
                "env": {}
            }
        }
    }, f, indent=2)

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in os.walk(workspace) for __ in _[2])}")