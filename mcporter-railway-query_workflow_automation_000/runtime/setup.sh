#!/usr/bin/env bash
set -e

# ── 1. Create the canonical ~/.mcporter/mcporter.json config ───────────────
mkdir -p ~/.mcporter

cat > ~/.mcporter/mcporter.json << 'MPORTER_CFG'
{
  "mcpServers": {
    "12306": {
      "command": "python3",
      "args": ["/usr/local/bin/mock_12306_mcp_server.py"]
    }
  }
}
MPORTER_CFG

# ── 2. Create the mock MCP stdio server ─────────────────────────────────────
cat > /usr/local/bin/mock_12306_mcp_server.py << 'MOCK_SERVER'
#!/usr/bin/env python3
"""
Mock MCP stdio server for 12306 railway queries.
Speaks JSON-RPC 2.0 over stdin/stdout (MCP protocol).
"""
import sys
import json

STATION_CODES = {
    "上海": "SHH", "上海虹桥": "AOH", "杭州": "HZH", "无锡": "WXH",
    "江阴": "KYH", "南京南": "NKH", "北京": "BJP", "广州": "GZH",
    "深圳北": "IOQ", "成都东": "ICW", "武汉": "WHN", "苏州": "SZH",
    "南京": "NJH", "宁波": "NGH",
}

# Full train schedule for HZH->NKH on 2026-03-15
# Includes G, D, K trains across the full day to force correct filtering
ALL_TRAINS_HZH_NKH = [
    {"trainNo": "G7001", "trainType": "G", "startTime": "06:12", "arriveTime": "08:45", "durationMinutes": 153, "secondClassSeat": "有票", "firstClassSeat": "有票"},
    {"trainNo": "D3051", "trainType": "D", "startTime": "07:30", "arriveTime": "10:42", "durationMinutes": 192, "secondClassSeat": "有票", "firstClassSeat": "无票"},
    {"trainNo": "K201",  "trainType": "K", "startTime": "09:00", "arriveTime": "13:20", "durationMinutes": 260, "secondClassSeat": "有票", "firstClassSeat": "无票"},
    {"trainNo": "G7003", "trainType": "G", "startTime": "10:05", "arriveTime": "12:23", "durationMinutes": 138, "secondClassSeat": "剩余3张票", "firstClassSeat": "有票"},
    {"trainNo": "D3053", "trainType": "D", "startTime": "13:15", "arriveTime": "16:18", "durationMinutes": 183, "secondClassSeat": "有票", "firstClassSeat": "有票"},
    {"trainNo": "Z51",   "trainType": "Z", "startTime": "14:00", "arriveTime": "19:10", "durationMinutes": 310, "secondClassSeat": "有票", "firstClassSeat": "无票"},
    {"trainNo": "G7005", "trainType": "G", "startTime": "16:00", "arriveTime": "18:09", "durationMinutes": 129, "secondClassSeat": "有票", "firstClassSeat": "有票"},
    {"trainNo": "G7007", "trainType": "G", "startTime": "18:05", "arriveTime": "20:11", "durationMinutes": 126, "secondClassSeat": "剩余5张票", "firstClassSeat": "有票"},
    {"trainNo": "D3055", "trainType": "D", "startTime": "19:22", "arriveTime": "22:45", "durationMinutes": 203, "secondClassSeat": "有票", "firstClassSeat": "无票"},
    {"trainNo": "G7009", "trainType": "G", "startTime": "20:00", "arriveTime": "22:05", "durationMinutes": 125, "secondClassSeat": "有票", "firstClassSeat": "有票"},
    {"trainNo": "G7011", "trainType": "G", "startTime": "21:30", "arriveTime": "23:32", "durationMinutes": 122, "secondClassSeat": "剩余2张票", "firstClassSeat": "有票"},
    {"trainNo": "K203",  "trainType": "K", "startTime": "22:10", "arriveTime": "04:30", "durationMinutes": 380, "secondClassSeat": "有票", "firstClassSeat": "无票"},
    {"trainNo": "G7013", "trainType": "G", "startTime": "22:45", "arriveTime": "00:44", "durationMinutes": 119, "secondClassSeat": "无票", "firstClassSeat": "无票"},
]

def get_station_code_of_citys(params):
    citys_str = params.get("citys", "")
    city_list = [c.strip() for c in citys_str.split("|") if c.strip()]
    result = {}
    for city in city_list:
        result[city] = STATION_CODES.get(city, "UNKNOWN")
    return json.dumps(result, ensure_ascii=False, indent=2)

def get_tickets(params):
    date        = params.get("date", "")
    from_st     = params.get("fromStation", "")
    to_st       = params.get("toStation", "")
    filter_flags = params.get("trainFilterFlags", "")
    earliest    = int(params.get("earliestStartTime", 0))
    latest      = int(params.get("latestStartTime", 24))
    sort_flag   = params.get("sortFlag", "")
    sort_rev    = str(params.get("sortReverse", "false")).lower() in ("true", "1")
    limit       = int(params.get("limitedNum", 0))
    fmt         = params.get("format", "text")

    # Only serve HZH->NKH for this mock
    if from_st != "HZH" or to_st != "NKH":
        if fmt == "json":
            return json.dumps({"trains": [], "message": f"No data for {from_st}->{to_st}"}, ensure_ascii=False)
        return f"未找到 {from_st} 到 {to_st} 的车次"

    trains = list(ALL_TRAINS_HZH_NKH)

    # Filter by train type
    if filter_flags:
        allowed_types = set(filter_flags.upper())
        trains = [t for t in trains if t["trainType"] in allowed_types]

    # Filter by time window
    def hour_of(t_str):
        h, m = t_str.split(":")
        return int(h) + int(m) / 60.0

    trains = [t for t in trains if earliest <= hour_of(t["startTime"]) < latest]

    # Sort
    sort_key_map = {
        "startTime":   lambda t: hour_of(t["startTime"]),
        "arriveTime":  lambda t: hour_of(t["arriveTime"]),
        "duration":    lambda t: t["durationMinutes"],
    }
    if sort_flag in sort_key_map:
        trains = sorted(trains, key=sort_key_map[sort_flag], reverse=sort_rev)

    # Limit
    if limit > 0:
        trains = trains[:limit]

    if fmt == "json":
        return json.dumps({"date": date, "from": from_st, "to": to_st, "trains": trains}, ensure_ascii=False, indent=2)

    # text format
    if not trains:
        return "无结果"
    lines = [f"日期: {date}  {from_st} → {to_st}", "-" * 50]
    for t in trains:
        lines.append(
            f"{t['trainNo']}  {t['trainType']}  {t['startTime']}-{t['arriveTime']}  "
            f"{t['durationMinutes']}分钟  二等:{t['secondClassSeat']}  一等:{t['firstClassSeat']}"
        )
    return "\n".join(lines)

TOOLS = {
    "get-station-code-of-citys": {
        "name": "12306.get-station-code-of-citys",
        "description": "获取城市的铁路站代码",
        "inputSchema": {
            "type": "object",
            "properties": {"citys": {"type": "string", "description": "城市名称，用|分隔"}},
            "required": ["citys"]
        }
    },
    "get-tickets": {
        "name": "12306.get-tickets",
        "description": "查询中国铁路车票",
        "inputSchema": {
            "type": "object",
            "properties": {
                "date": {"type": "string"},
                "fromStation": {"type": "string"},
                "toStation": {"type": "string"},
                "trainFilterFlags": {"type": "string"},
                "earliestStartTime": {"type": "number"},
                "latestStartTime": {"type": "number"},
                "sortFlag": {"type": "string"},
                "sortReverse": {"type": "boolean"},
                "limitedNum": {"type": "number"},
                "format": {"type": "string"}
            },
            "required": ["date", "fromStation", "toStation"]
        }
    }
}

def handle(req):
    method = req.get("method", "")
    req_id = req.get("id")
    params = req.get("params", {})

    def ok(result):
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    if method == "initialize":
        return ok({
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "mock-12306", "version": "1.0.0"}
        })

    if method == "notifications/initialized":
        return None  # notification, no response

    if method == "tools/list":
        return ok({"tools": list(TOOLS.values())})

    if method == "tools/call":
        tool_name_full = params.get("name", "")
        tool_name = tool_name_full.split(".")[-1] if "." in tool_name_full else tool_name_full
        tool_params = params.get("arguments", {})

        if tool_name == "get-station-code-of-citys":
            content = get_station_code_of_citys(tool_params)
        elif tool_name == "get-tickets":
            content = get_tickets(tool_params)
        else:
            content = f"Unknown tool: {tool_name}"

        return ok({"content": [{"type": "text", "text": content}], "isError": False})

    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}

def main():
    for raw_line in sys.stdin:
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        try:
            req = json.loads(raw_line)
        except json.JSONDecodeError:
            continue

        resp = handle(req)
        if resp is not None:
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
MOCK_SERVER

chmod +x /usr/local/bin/mock_12306_mcp_server.py

# ── 3. Create the mock mcporter CLI ─────────────────────────────────────────
cat > /usr/local/bin/mcporter << 'MCPORTER_CLI'
#!/usr/bin/env python3
"""
Mock mcporter CLI.
Supports: mcporter call <server>.<tool> [key=value ...] [--config <path>]
"""
import sys
import os
import json
import subprocess
import shlex

def parse_args(argv):
    """Parse: call <tool_fullname> [k=v ...] [--config <path>]"""
    if len(argv) < 3 or argv[1] != "call":
        print("Usage: mcporter call <tool> [params...] [--config <path>]", file=sys.stderr)
        sys.exit(1)

    tool_full = argv[2]
    remaining = argv[3:]

    config_path = None
    kv_args = []
    i = 0
    while i < len(remaining):
        tok = remaining[i]
        if tok == "--config":
            if i + 1 < len(remaining):
                config_path = remaining[i + 1]
                i += 2
            else:
                print("--config requires a path", file=sys.stderr)
                sys.exit(1)
        elif "=" in tok:
            kv_args.append(tok)
            i += 1
        else:
            i += 1

    return tool_full, kv_args, config_path

def parse_kv(kv_args):
    params = {}
    for kv in kv_args:
        idx = kv.index("=")
        key = kv[:idx]
        val = kv[idx+1:].strip('"').strip("'")
        # Type coercion
        if val.lower() == "true":
            val = True
        elif val.lower() == "false":
            val = False
        else:
            try:
                val = int(val)
            except ValueError:
                try:
                    val = float(val)
                except ValueError:
                    pass
        params[key] = val
    return params

def load_config(config_path):
    if config_path is None:
        default = os.path.expanduser("~/.mcporter/mcporter.json")
        config_path = default
    with open(config_path) as f:
        return json.load(f)

def main():
    tool_full, kv_args, config_path = parse_args(sys.argv)
    params = parse_kv(kv_args)

    try:
        config = load_config(config_path)
    except FileNotFoundError:
        print(f"Config not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    # Determine server name from tool (e.g., "12306.get-tickets" -> server "12306")
    if "." in tool_full:
        server_name, tool_name = tool_full.split(".", 1)
    else:
        print(f"Tool must be in format <server>.<tool>: {tool_full}", file=sys.stderr)
        sys.exit(1)

    servers = config.get("mcpServers", {})
    if server_name not in servers:
        print(f"Server not found in config: {server_name}", file=sys.stderr)
        sys.exit(1)

    server_cfg = servers[server_name]
    command = server_cfg["command"]
    args = server_cfg.get("args", [])
    env_extra = server_cfg.get("env", {})

    env = os.environ.copy()
    env.update(env_extra)

    cmd = [command] + args
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True
    )

    def send(obj):
        line = json.dumps(obj) + "\n"
        proc.stdin.write(line)
        proc.stdin.flush()

    def recv():
        while True:
            line = proc.stdout.readline()
            if not line:
                return None
            line = line.strip()
            if line:
                return json.loads(line)

    # 1. Initialize
    send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
          "params": {"protocolVersion": "2024-11-05",
                     "capabilities": {},
                     "clientInfo": {"name": "mcporter", "version": "1.0.6"}}})
    resp = recv()

    # 2. Initialized notification
    send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    # 3. Call tool
    send({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
          "params": {"name": tool_full, "arguments": params}})
    resp = recv()

    proc.stdin.close()
    proc.wait()

    if resp is None:
        print("No response from MCP server", file=sys.stderr)
        sys.exit(1)

    if "error" in resp:
        print(f"Error: {resp['error']}", file=sys.stderr)
        sys.exit(1)

    result = resp.get("result", {})
    content = result.get("content", [])
    for item in content:
        if item.get("type") == "text":
            print(item["text"])

if __name__ == "__main__":
    main()
MCPORTER_CLI

chmod +x /usr/local/bin/mcporter

echo "Setup complete. mcporter CLI and mock 12306 MCP server installed."
echo "Testing mock server..."
mcporter call 12306.get-station-code-of-citys citys="杭州|南京南" --config ~/.mcporter/mcporter.json && echo "Mock server OK."