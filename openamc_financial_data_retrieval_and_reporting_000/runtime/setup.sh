#!/usr/bin/env bash
set -e

echo "=== Setting up OpenAMC Mock MCP Server ==="

# Write the mock MCP server (Flask app)
cat > /usr/local/bin/mock_openamc_server.py << 'PYEOF'
#!/usr/bin/env python3
"""
Mock OpenAMC MCP Server - simulates the real openamc MCP server responses.
Validates that callers use correct providers, symbols, and tool names.
"""
from flask import Flask, request, jsonify
import json
import datetime

app = Flask(__name__)

VALID_RESPONSES = {}

def make_astock_response(symbol, provider):
    if provider != "akshare":
        return {"error": f"Provider '{provider}' is not supported for A-share symbol '{symbol}'. Use provider='akshare'.", "data": None}
    if not symbol.isdigit() or len(symbol) != 6:
        return {"error": f"Invalid A-share symbol format: '{symbol}'. Expected 6-digit numeric string.", "data": None}
    rows = []
    base = 35.0
    import random
    random.seed(int(symbol))
    for i in range(30):
        dt = (datetime.date(2025, 5, 1) + datetime.timedelta(days=i)).isoformat()
        base += random.uniform(-0.8, 1.2)
        rows.append({"date": dt, "open": round(base - 0.1, 2), "high": round(base + 0.5, 2), "low": round(base - 0.5, 2), "close": round(base, 2), "volume": random.randint(1000000, 5000000)})
    return {"symbol": symbol, "provider": provider, "market": "SSE", "data": rows, "record_count": len(rows)}

def make_fred_series_response(symbol, provider, start_date=None):
    if provider != "fred":
        return {"error": f"Provider '{provider}' is not valid for FRED series. Use provider='fred'.", "data": None}
    known_series = {
        "DFEDTARU": [
            {"date": "2025-01-22", "value": 4.5},
            {"date": "2025-03-19", "value": 4.5},
            {"date": "2025-05-07", "value": 4.5},
        ],
        "FEDFUNDS": [
            {"date": "2025-01-01", "value": 4.33},
            {"date": "2025-02-01", "value": 4.33},
            {"date": "2025-03-01", "value": 4.33},
        ],
        "GDP": [
            {"date": "2024-10-01", "value": 29350.0},
            {"date": "2025-01-01", "value": 29710.0},
        ]
    }
    if symbol not in known_series:
        return {"error": f"Unknown FRED series symbol: '{symbol}'", "data": None}
    data = known_series[symbol]
    if start_date:
        data = [d for d in data if d["date"] >= start_date]
    return {"symbol": symbol, "provider": provider, "series_name": f"FRED:{symbol}", "data": data, "record_count": len(data)}

def make_forex_response(symbol, provider, start_date=None, interval=None):
    if provider != "yfinance":
        return {"error": f"Provider '{provider}' is not valid for forex. Use provider='yfinance'.", "data": None}
    # Must end with =X
    if not symbol.endswith("=X"):
        return {"error": f"Invalid forex symbol format: '{symbol}'. Forex symbols must end with '=X' (e.g., 'EURUSD=X').", "data": None}
    import random
    random.seed(hash(symbol) % 1000)
    rows = []
    base = 1.085
    sd = datetime.date(2025, 3, 1)
    if start_date:
        try:
            sd = datetime.date.fromisoformat(start_date)
        except:
            pass
    for i in range(60):
        dt = (sd + datetime.timedelta(days=i)).isoformat()
        base += random.uniform(-0.003, 0.003)
        rows.append({"date": dt, "open": round(base - 0.001, 5), "high": round(base + 0.002, 5), "low": round(base - 0.002, 5), "close": round(base, 5)})
    return {"symbol": symbol, "provider": provider, "market": "FOREX", "interval": interval or "1d", "data": rows, "record_count": len(rows)}

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "server": "mock-openamc", "tools": 193})

@app.route("/call", methods=["POST"])
def call_tool():
    body = request.get_json(force=True)
    tool = body.get("tool", "")
    args = body.get("args", {})
    
    if tool == "available_categories":
        return jsonify({"categories": ["equity", "economy", "currency", "commodity", "crypto", "derivatives", "fixedincome", "congress", "akshare"]})
    
    if tool == "available_tools":
        category = args.get("category", "")
        tools_map = {
            "equity": ["equity_price_historical", "equity_price_quote"],
            "economy": ["economy_unemployment", "economy_indicators", "economy_fred_series"],
            "currency": ["currency_price_historical"],
            "akshare": ["akshare_business_analysis", "akshare_etf_holdings", "news_company"],
        }
        return jsonify({"category": category, "tools": tools_map.get(category, [])})
    
    if tool == "equity_price_historical":
        symbol = args.get("symbol", "")
        provider = args.get("provider", "yfinance")
        return jsonify(make_astock_response(symbol, provider))
    
    if tool == "economy_fred_series":
        symbol = args.get("symbol", "")
        provider = args.get("provider", "fred")
        start_date = args.get("start_date", None)
        return jsonify(make_fred_series_response(symbol, provider, start_date))
    
    if tool == "economy_indicators":
        # This is a trap - should use economy_fred_series for FRED series
        symbol = args.get("symbol", "")
        provider = args.get("provider", "fred")
        if symbol in ["DFEDTARU", "FEDFUNDS"]:
            return jsonify({"error": "For FRED series data, use 'economy_fred_series' tool, not 'economy_indicators'.", "data": None})
        return jsonify({"symbol": symbol, "provider": provider, "data": []})
    
    if tool == "currency_price_historical":
        symbol = args.get("symbol", "")
        provider = args.get("provider", "yfinance")
        start_date = args.get("start_date", None)
        interval = args.get("interval", "1d")
        return jsonify(make_forex_response(symbol, provider, start_date, interval))
    
    # Catch-all for other valid tools
    return jsonify({"tool": tool, "args": args, "data": [], "note": "mock response"})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8001, debug=False)
PYEOF

chmod +x /usr/local/bin/mock_openamc_server.py

# Start the mock server in background
python3 /usr/local/bin/mock_openamc_server.py &
SERVER_PID=$!
echo $SERVER_PID > /tmp/mock_server.pid
echo "Mock server started with PID $SERVER_PID"

# Wait for server to be ready
sleep 2
echo "Server health check:"
curl -s http://127.0.0.1:8001/health || echo "WARNING: Server not responding"

# Write the `mcp` CLI wrapper that the agent will use
cat > /usr/local/bin/mcp << 'MCPEOF'
#!/usr/bin/env python3
"""
mcporter CLI wrapper - mcp command
Usage: mcp call <server> <tool> [--args '<json>'] [--timeout <ms>]
"""
import sys
import json
import urllib.request
import urllib.error

def main():
    args = sys.argv[1:]
    
    if len(args) < 1:
        print("Usage: mcp call <server> <tool> [--args '<json>'] [--timeout <ms>]")
        sys.exit(1)
    
    if args[0] != "call":
        print(f"Unknown subcommand: {args[0]}")
        sys.exit(1)
    
    if len(args) < 3:
        print("Usage: mcp call <server> <tool> [--args '<json>']")
        sys.exit(1)
    
    server_name = args[1]   # e.g. openamc
    tool_name = args[2]      # e.g. equity_price_historical
    tool_args = {}
    
    i = 3
    while i < len(args):
        if args[i] == "--args" and i + 1 < len(args):
            try:
                tool_args = json.loads(args[i+1])
            except json.JSONDecodeError as e:
                print(f"Error parsing --args JSON: {e}")
                sys.exit(1)
            i += 2
        elif args[i] == "--timeout" and i + 1 < len(args):
            i += 2  # ignore timeout for mock
        else:
            i += 1
    
    payload = json.dumps({"server": server_name, "tool": tool_name, "args": tool_args}).encode()
    
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:8001/call",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            print(json.dumps(result, indent=2, ensure_ascii=False))
    except urllib.error.URLError as e:
        print(f"Error: Cannot connect to MCP server at http://127.0.0.1:8001 - {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
MCPEOF

chmod +x /usr/local/bin/mcp

echo "=== Setup complete ==="
echo "mcp command available at: $(which mcp)"
echo "Mock OpenAMC server running on http://127.0.0.1:8001"