#!/usr/bin/env python3
import os
import json
import random

random.seed(42)

workspace = "/workspace"

# --- Directory structure with distractor files ---
dirs = [
    "tools",
    "tools/legacy",
    "data/raw",
    "data/processed",
    "reports/old",
    "reports/drafts",
    "config",
    "config/backup",
    "scripts/deprecated",
    "scripts/utils",
    "notebooks",
    "logs",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "data/raw/sp500_tickers.txt": "\n".join(["AAPL", "MSFT", "JNJ", "UNH", "ABT", "PFE", "MRK", "TMO", "DHR", "BMY"]),
    "data/raw/sector_map.csv": "ticker,sector\nJNJ,Healthcare\nUNH,Healthcare\nABT,Healthcare\nPFE,Healthcare\nMRK,Healthcare\n",
    "data/processed/stale_prices.json": json.dumps({"AAPL": 145.0, "MSFT": 290.0, "JNJ": 165.0}, indent=2),
    "config/backup/old_screener_params.json": json.dumps({
        "sector": "Healthcare",
        "min_market_cap": 5000000000,
        "max_pe": 20,
        "dividend_pct": 2.5
    }, indent=2),
    "config/thresholds.yaml": "# Outdated threshold file\nmarket_cap_min: 5000000000\npe_max: 20\ndividend_yield_min: 2.5%\n",
    "scripts/deprecated/old_fetch.py": "# Deprecated — do not use\nimport yfinance as yf\ndef fetch(sym):\n    return yf.Ticker(sym).history(period='1mo')\n",
    "scripts/utils/helpers.py": "import json\ndef load_json(path):\n    with open(path) as f:\n        return json.load(f)\n",
    "reports/old/q1_2023_summary.txt": "Q1 2023 Healthcare Screening Report\nSymbols analyzed: JNJ, UNH, ABT\nNote: Methodology outdated, use new pipeline.\n",
    "reports/drafts/draft_template.json": json.dumps({
        "report_type": "equity_screening",
        "screener_params": {},
        "screened_stocks": [],
        "financials": {},
        "comparison": {}
    }, indent=2),
    "notebooks/exploratory_analysis.py": "# Scratch notebook\n# TODO: automate this pipeline\nsymbols = ['JNJ', 'UNH', 'ABT']\nfor s in symbols:\n    print(s)\n",
    "logs/run_20240101.log": "ERROR: Connection timeout\nINFO: Retrying...\nERROR: Data unavailable\n",
    "tools/legacy/old_tool_caller.py": "# DO NOT USE - replaced by new tool interface\ndef call_tool(name, **kwargs):\n    raise NotImplementedError('Use yf_tool.py instead')\n",
    "config/api_params_draft.json": json.dumps({
        "_comment": "DRAFT - parameters not finalized",
        "dividend_yield_format": "percentage? decimal? TBD",
        "pe_ratio_field": "trailing_PE or forward_PE?",
        "statement_types": ["income_stmt", "bs", "cf"]
    }, indent=2),
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w") as f:
        f.write(content)

# --- Mock tool server script ---
mock_server_script = '''#!/usr/bin/env python3
"""
Mock YFinance MCP Tool Server
Listens on port 8080, accepts POST /call with JSON body: {"tool": "...", "params": {...}}
Logs all calls to /workspace/logs/tool_calls.jsonl
Returns deterministic mock data based on tool name + params.
"""
import json
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import os

CALL_LOG = "/workspace/logs/tool_calls.jsonl"

# Deterministic mock responses
MOCK_DATA = {
    "tool_screen_stocks": {
        "default": {
            "count": 3,
            "stocks": [
                {"symbol": "JNJ", "name": "Johnson & Johnson", "sector": "Healthcare",
                 "market_cap": 380000000000, "pe_ratio": 14.2, "dividend_yield": 0.031,
                 "price": 152.45, "exchange": "NYQ"},
                {"symbol": "ABT", "name": "Abbott Laboratories", "sector": "Healthcare",
                 "market_cap": 175000000000, "pe_ratio": 22.1, "dividend_yield": 0.021,
                 "price": 100.12, "exchange": "NYQ"},
                {"symbol": "BMY", "name": "Bristol-Myers Squibb", "sector": "Healthcare",
                 "market_cap": 130000000000, "pe_ratio": 8.9, "dividend_yield": 0.042,
                 "price": 52.33, "exchange": "NYQ"},
            ]
        }
    },
    "tool_get_financials": {
        "JNJ": {
            "income": {"total_revenue": 85159000000, "net_income": 13446000000, "ebitda": 22000000000},
            "balance_sheet": {"total_assets": 182018000000, "total_debt": 35092000000, "cash": 22000000000},
            "cash_flow": {"operating_cashflow": 19800000000, "capex": -4500000000, "free_cashflow": 15300000000}
        },
        "ABT": {
            "income": {"total_revenue": 19986000000, "net_income": 5109000000, "ebitda": 6800000000},
            "balance_sheet": {"total_assets": 68827000000, "total_debt": 14000000000, "cash": 8200000000},
            "cash_flow": {"operating_cashflow": 6400000000, "capex": -1200000000, "free_cashflow": 5200000000}
        },
        "BMY": {
            "income": {"total_revenue": 45000000000, "net_income": 6327000000, "ebitda": 14500000000},
            "balance_sheet": {"total_assets": 95000000000, "total_debt": 35000000000, "cash": 15000000000},
            "cash_flow": {"operating_cashflow": 13200000000, "capex": -800000000, "free_cashflow": 12400000000}
        }
    },
    "tool_compare_stocks": {
        "default": {
            "comparison": [
                {"symbol": "JNJ", "price": 152.45, "market_cap": 380000000000,
                 "pe_ratio": 14.2, "dividend_yield": 0.031, "analyst_rating": "Buy",
                 "profit_margin": 0.158, "revenue_growth": 0.064},
                {"symbol": "ABT", "price": 100.12, "market_cap": 175000000000,
                 "pe_ratio": 22.1, "dividend_yield": 0.021, "analyst_rating": "Strong Buy",
                 "profit_margin": 0.256, "revenue_growth": -0.182},
                {"symbol": "BMY", "price": 52.33, "market_cap": 130000000000,
                 "pe_ratio": 8.9, "dividend_yield": 0.042, "analyst_rating": "Hold",
                 "profit_margin": 0.141, "revenue_growth": 0.021},
            ]
        }
    }
}

class ToolHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress default logging

    def do_POST(self):
        if self.path != "/call":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            payload = json.loads(body)
        except Exception as e:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b\'{"error": "bad json"}\')
            return

        tool = payload.get("tool", "")
        params = payload.get("params", {})

        # Log the call
        os.makedirs("/workspace/logs", exist_ok=True)
        with open(CALL_LOG, "a") as f:
            f.write(json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                "tool": tool,
                "params": params
            }) + "\\n")

        # Route to mock data
        result = self._get_mock_result(tool, params)
        
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())

    def _get_mock_result(self, tool, params):
        if tool == "tool_screen_stocks":
            return MOCK_DATA["tool_screen_stocks"]["default"]
        
        elif tool == "tool_get_financials":
            symbol = params.get("symbol", "")
            data = MOCK_DATA["tool_get_financials"].get(symbol, {})
            stmt_type = params.get("statement_type", "income")
            quarterly = params.get("quarterly", False)
            
            if stmt_type == "all":
                result = {k: v for k, v in data.items()}
                result["quarterly"] = quarterly
                result["symbol"] = symbol
                return result
            elif stmt_type in data:
                return {"symbol": symbol, stmt_type: data[stmt_type], "quarterly": quarterly}
            else:
                return {"symbol": symbol, "data": {}, "quarterly": quarterly}
        
        elif tool == "tool_compare_stocks":
            return MOCK_DATA["tool_compare_stocks"]["default"]
        
        else:
            return {"error": f"Unknown tool: {tool}"}

if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8080), ToolHandler)
    print("Mock YFinance MCP server running on port 8080", flush=True)
    server.serve_forever()
'''

with open(os.path.join(workspace, "tools", "mock_server.py"), "w") as f:
    f.write(mock_server_script)

# --- Tool client CLI script (what the agent should use) ---
tool_client_script = '''#!/usr/bin/env python3
"""
YFinance MCP Tool Client
Usage: python yf_tool.py <tool_name> [key=value ...]

Example:
  python yf_tool.py tool_screen_stocks sector=Healthcare min_market_cap=10000000000 max_pe_ratio=25 min_dividend_yield=0.02
  python yf_tool.py tool_get_financials symbol=JNJ statement_type=all quarterly=true
  python yf_tool.py tool_compare_stocks symbols="JNJ,ABT,BMY"

Returns JSON to stdout.
"""
import sys
import json
import requests

SERVER_URL = "http://127.0.0.1:8080/call"

def parse_value(v):
    if v.lower() == "true":
        return True
    if v.lower() == "false":
        return False
    try:
        if "." in v:
            return float(v)
        return int(v)
    except ValueError:
        return v

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: yf_tool.py <tool_name> [key=value ...]"}))
        sys.exit(1)

    tool_name = sys.argv[1]
    params = {}
    for arg in sys.argv[2:]:
        if "=" in arg:
            k, v = arg.split("=", 1)
            params[k] = parse_value(v)

    payload = {"tool": tool_name, "params": params}
    try:
        resp = requests.post(SERVER_URL, json=payload, timeout=10)
        print(resp.text)
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

with open(os.path.join(workspace, "tools", "yf_tool.py"), "w") as f:
    f.write(tool_client_script)

# --- Intentionally misleading/incomplete config files ---
bad_config = {
    "_note": "These parameters are WRONG - do not copy",
    "dividend_yield_as_percent": 2.5,
    "wrong_field_name": "dividend_pct",
    "pe_ratio_name_guess": "trailing_pe",
    "financials_type_guess": "income_statement",
}
with open(os.path.join(workspace, "config", "WRONG_params_example.json"), "w") as f:
    json.dump(bad_config, f, indent=2)

# --- Task brief (business context, no technical hints) ---
task_brief = """INTERNAL MEMO — Quantitative Research Team
Date: 2024-Q4
Subject: Automated Healthcare Value Screen

We need an automated pipeline that:
1. Screens healthcare value stocks meeting our fund criteria
2. Pulls complete financials for each qualifying name
3. Produces a side-by-side comparison of all candidates
4. Saves the consolidated output to a report file

The tool infrastructure is already set up. Refer to the skill documentation for how to use it.
Output file should be named: healthcare_value_report.json
"""
with open(os.path.join(workspace, "TASK_BRIEF.txt"), "w") as f:
    f.write(task_brief)

# Clear the call log
os.makedirs(os.path.join(workspace, "logs"), exist_ok=True)
with open(os.path.join(workspace, "logs", "tool_calls.jsonl"), "w") as f:
    pass

print("Workspace generated successfully.")