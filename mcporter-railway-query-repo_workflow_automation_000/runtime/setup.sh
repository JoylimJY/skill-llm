#!/bin/bash
set -e

# ── Install mock mcporter CLI ─────────────────────────────────────────────────
cat > /usr/local/bin/mcporter << 'MCPORTER_EOF'
#!/usr/bin/env python3
"""
Mock mcporter CLI for evaluation purposes.
Intercepts calls and returns deterministic fake data based on parameters.
Logs all invocations for eval inspection.
"""
import sys
import json
import os
import re
from datetime import datetime

LOG_FILE = "/tmp/mcporter_calls.log"
CALL_RECORD = "/tmp/mcporter_call_record.json"

def parse_args(argv):
    """Parse mcporter call arguments into a dict."""
    args = {}
    tool = None
    i = 0
    while i < len(argv):
        token = argv[i]
        if token == "call" and i + 1 < len(argv):
            tool = argv[i + 1]
            i += 2
            continue
        if token == "--config":
            args["__config"] = argv[i + 1] if i + 1 < len(argv) else ""
            i += 2
            continue
        if "=" in token:
            k, v = token.split("=", 1)
            # strip quotes
            v = v.strip('"').strip("'")
            args[k] = v
        i += 1
    return tool, args

def log_call(tool, args):
    record = {"tool": tool, "args": args, "timestamp": datetime.now().isoformat()}
    # Append to log
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")
    # Maintain list of all calls
    calls = []
    if os.path.exists(CALL_RECORD):
        try:
            with open(CALL_RECORD) as f:
                calls = json.load(f)
        except Exception:
            calls = []
    calls.append(record)
    with open(CALL_RECORD, "w") as f:
        json.dump(calls, f, indent=2, ensure_ascii=False)

def handle_get_station_code(args):
    citys = args.get("citys", "")
    # Must be pipe-separated
    city_list = citys.split("|")
    result = {}
    mapping = {
        "成都东": "CDW",
        "西安北": "ENH",
        "上海": "SHH",
        "上海虹桥": "AOH",
        "杭州": "HZH",
        "无锡": "WXH",
        "江阴": "KYH",
        "南京南": "NKH",
        "北京": "BJP",
        "广州南": "GGQ",
    }
    lines = []
    for city in city_list:
        city = city.strip()
        code = mapping.get(city, "UNKNOWN")
        result[city] = code
        lines.append(f"{city}: {code}")
    return "\n".join(lines)

# Deterministic fake train data for CDW->ENH on 2026-03-15
TRAINS_CDW_ENH = [
    {"train_no": "G2195", "from_station": "CDW", "to_station": "ENH",
     "depart": "08:02", "arrive": "11:36", "duration": "3h34m", "duration_minutes": 214,
     "seats": {"二等座": "有票", "一等座": "有票", "商务座": "无票"}},
    {"train_no": "G87",   "from_station": "CDW", "to_station": "ENH",
     "depart": "08:48", "arrive": "12:08", "duration": "3h20m", "duration_minutes": 200,
     "seats": {"二等座": "有票", "一等座": "剩余3张票", "商务座": "有票"}},
    {"train_no": "G307",  "from_station": "CDW", "to_station": "ENH",
     "depart": "09:30", "arrive": "13:01", "duration": "3h31m", "duration_minutes": 211,
     "seats": {"二等座": "剩余12张票", "一等座": "有票", "商务座": "有票"}},
    {"train_no": "G89",   "from_station": "CDW", "to_station": "ENH",
     "depart": "10:15", "arrive": "13:28", "duration": "3h13m", "duration_minutes": 193,
     "seats": {"二等座": "有票", "一等座": "有票", "商务座": "剩余2张票"}},
    {"train_no": "G2197", "from_station": "CDW", "to_station": "ENH",
     "depart": "11:40", "arrive": "15:12", "duration": "3h32m", "duration_minutes": 212,
     "seats": {"二等座": "无票", "一等座": "剩余5张票", "商务座": "有票"}},
    {"train_no": "G91",   "from_station": "CDW", "to_station": "ENH",
     "depart": "12:05", "arrive": "15:14", "duration": "3h09m", "duration_minutes": 189,
     "seats": {"二等座": "有票", "一等座": "有票", "商务座": "有票"}},
    {"train_no": "D308",  "from_station": "CDW", "to_station": "ENH",
     "depart": "13:22", "arrive": "17:50", "duration": "4h28m", "duration_minutes": 268,
     "seats": {"二等座": "有票", "一等座": "有票", "商务座": "无票"}},
    {"train_no": "G2199", "from_station": "CDW", "to_station": "ENH",
     "depart": "13:55", "arrive": "17:24", "duration": "3h29m", "duration_minutes": 209,
     "seats": {"二等座": "剩余8张票", "一等座": "有票", "商务座": "有票"}},
    {"train_no": "G93",   "from_station": "CDW", "to_station": "ENH",
     "depart": "14:30", "arrive": "17:38", "duration": "3h08m", "duration_minutes": 188,
     "seats": {"二等座": "有票", "一等座": "剩余1张票", "商务座": "有票"}},
    {"train_no": "G2201", "from_station": "CDW", "to_station": "ENH",
     "depart": "15:00", "arrive": "18:35", "duration": "3h35m", "duration_minutes": 215,
     "seats": {"二等座": "有票", "一等座": "有票", "商务座": "有票"}},
]

def handle_get_tickets(args):
    date        = args.get("date", "")
    from_st     = args.get("fromStation", "")
    to_st       = args.get("toStation", "")
    flags       = args.get("trainFilterFlags", "")
    earliest    = int(args.get("earliestStartTime", 0))
    latest      = int(args.get("latestStartTime", 24))
    sort_flag   = args.get("sortFlag", "")
    sort_rev    = args.get("sortReverse", "false").lower() == "true"
    limit       = int(args.get("limitedNum", 0))
    fmt         = args.get("format", "text")

    # Only serve CDW->ENH on 2026-03-15 with any reasonable params
    if from_st.upper() not in ("CDW",) or to_st.upper() not in ("ENH",) or date != "2026-03-15":
        if fmt == "json":
            print(json.dumps([], ensure_ascii=False))
        else:
            print("无结果：请检查车站代码和日期")
        return

    trains = list(TRAINS_CDW_ENH)

    # Filter by train type
    if flags:
        allowed = set()
        if "G" in flags.upper():
            allowed.add("G")
        if "D" in flags.upper():
            allowed.add("D")
        if "C" in flags.upper():
            allowed.add("C")
        if allowed:
            trains = [t for t in trains if t["train_no"][0] in allowed]

    # Filter by time window
    def depart_hour(t):
        h, m = t["depart"].split(":")
        return int(h) + int(m)/60.0

    trains = [t for t in trains if earliest <= depart_hour(t) <= latest]

    # Sort
    if sort_flag == "duration":
        trains.sort(key=lambda t: t["duration_minutes"], reverse=sort_rev)
    elif sort_flag == "startTime":
        trains.sort(key=lambda t: t["depart"], reverse=sort_rev)
    elif sort_flag == "arriveTime":
        trains.sort(key=lambda t: t["arrive"], reverse=sort_rev)

    # Limit
    if limit > 0:
        trains = trains[:limit]

    # Format output
    if fmt == "json":
        # Return clean JSON without internal field
        output = []
        for t in trains:
            row = {k: v for k, v in t.items() if k != "duration_minutes"}
            output.append(row)
        print(json.dumps(output, ensure_ascii=False, indent=2))
    elif fmt == "csv":
        print("train_no,from_station,to_station,depart,arrive,duration")
        for t in trains:
            print(f"{t['train_no']},{t['from_station']},{t['to_station']},{t['depart']},{t['arrive']},{t['duration']}")
    else:
        # text
        if not trains:
            print("无票")
            return
        for t in trains:
            seats_str = ", ".join(f"{k}: {v}" for k, v in t["seats"].items())
            print(f"{t['train_no']}  {t['from_station']}→{t['to_station']}  {t['depart']}-{t['arrive']}  {t['duration']}  [{seats_str}]")

def main():
    argv = sys.argv[1:]
    if not argv or argv[0] != "call":
        print("Usage: mcporter call <tool> [key=value ...] [--config <path>]")
        sys.exit(0)

    tool, args = parse_args(argv)
    log_call(tool, args)

    if tool == "12306.get-station-code-of-citys":
        print(handle_get_station_code(args))
    elif tool == "12306.get-tickets":
        handle_get_tickets(args)
    else:
        print(f"Unknown tool: {tool}")
        sys.exit(1)

if __name__ == "__main__":
    main()
MCPORTER_EOF

chmod +x /usr/local/bin/mcporter

# ── Install the workspace scripts (as referenced in SKILL.md) ─────────────────
mkdir -p /workspace/scripts

cat > /workspace/scripts/query-tickets.sh << 'EOF'
#!/bin/bash
DATE=$1
FROM=$2
TO=$3
mcporter call 12306.get-tickets \
  date="$DATE" \
  fromStation="$FROM" \
  toStation="$TO" \
  trainFilterFlags="GD" \
  --config ~/.mcporter/mcporter.json
EOF

cat > /workspace/scripts/query-afternoon.sh << 'EOF'
#!/bin/bash
DATE=$1
FROM=$2
TO=$3
mcporter call 12306.get-tickets \
  date="$DATE" \
  fromStation="$FROM" \
  toStation="$TO" \
  trainFilterFlags="GD" \
  earliestStartTime=12 \
  latestStartTime=18 \
  sortFlag="startTime" \
  --config ~/.mcporter/mcporter.json
EOF

cat > /workspace/scripts/get-station-code.sh << 'EOF'
#!/bin/bash
CITY=$1
mcporter call 12306.get-station-code-of-citys \
  citys="$CITY" \
  --config ~/.mcporter/mcporter.json
EOF

chmod +x /workspace/scripts/query-tickets.sh
chmod +x /workspace/scripts/query-afternoon.sh
chmod +x /workspace/scripts/get-station-code.sh

# ── Verify mock works ─────────────────────────────────────────────────────────
echo "=== Mock mcporter sanity check ==="
mcporter call 12306.get-station-code-of-citys citys="成都东|西安北" --config ~/.mcporter/mcporter.json
echo "=== Setup complete ==="