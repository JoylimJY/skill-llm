FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:/root/.local/bin:$PATH"

# Install Python dependencies
RUN pip install requests flask -i https://pypi.tuna.tsinghua.edu.cn/simple

# Create the skill directory structure
RUN mkdir -p /opt/a-stock-analysis/scripts

# Create analyze.py script
RUN cat > /opt/a-stock-analysis/scripts/analyze.py << 'ANALYZE_EOF'
#!/usr/bin/env python3
"""A-Stock analysis tool using Sina Finance API."""
import argparse
import json
import os
import sys
import requests

BASE_URL = os.environ.get("MOCK_SERVER_BASE", "http://localhost:8766")

def get_quote(code):
    resp = requests.get(f"{BASE_URL}/hq", params={"codes": code}, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data.get(code, {})

def get_minute(code):
    resp = requests.get(f"{BASE_URL}/minute", params={"code": code}, timeout=10)
    resp.raise_for_status()
    return resp.json()

def main():
    parser = argparse.ArgumentParser(description="Analyze A-stock")
    parser.add_argument("code", help="Stock code e.g. 600789")
    parser.add_argument("--minute", action="store_true", help="Include minute data")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Output as JSON")
    args = parser.parse_args()

    quote = get_quote(args.code)
    result = {"code": args.code, "quote": quote}

    if args.minute:
        result["minute"] = get_minute(args.code)

    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Code: {args.code}")
        print(f"Name: {quote.get('name', 'N/A')}")
        print(f"Price: {quote.get('price', 'N/A')}")
        print(f"Change: {quote.get('change_pct', 'N/A')}%")
        print(f"Volume: {quote.get('volume', 'N/A')}")

if __name__ == "__main__":
    main()
ANALYZE_EOF

# Create portfolio.py script
RUN cat > /opt/a-stock-analysis/scripts/portfolio.py << 'PORTFOLIO_EOF'
#!/usr/bin/env python3
"""Portfolio management tool."""
import argparse
import json
import os
import sys

PORTFOLIO_FILE = os.environ.get("PORTFOLIO_FILE", "/tmp/portfolio.json")

def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE) as f:
            return json.load(f)
    return {}

def save_portfolio(portfolio):
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f, ensure_ascii=False, indent=2)

def cmd_add(args):
    portfolio = load_portfolio()
    portfolio[args.code] = {
        "code": args.code,
        "cost": float(args.cost),
        "quantity": int(args.quantity),
    }
    save_portfolio(portfolio)
    print(f"Added {args.code}: cost={args.cost}, qty={args.quantity}")

def cmd_remove(args):
    portfolio = load_portfolio()
    if args.code in portfolio:
        del portfolio[args.code]
        save_portfolio(portfolio)
        print(f"Removed {args.code}")
    else:
        print(f"{args.code} not found in portfolio")

def cmd_update(args):
    portfolio = load_portfolio()
    if args.code not in portfolio:
        print(f"{args.code} not found in portfolio")
        sys.exit(1)
    if args.cost is not None:
        portfolio[args.code]["cost"] = float(args.cost)
    if args.quantity is not None:
        portfolio[args.code]["quantity"] = int(args.quantity)
    save_portfolio(portfolio)
    print(f"Updated {args.code}")

def cmd_list(args):
    portfolio = load_portfolio()
    print(json.dumps(portfolio, ensure_ascii=False, indent=2))

def main():
    parser = argparse.ArgumentParser(description="Portfolio manager")
    subparsers = parser.add_subparsers(dest="command")

    p_add = subparsers.add_parser("add")
    p_add.add_argument("code")
    p_add.add_argument("--cost", required=True)
    p_add.add_argument("--quantity", required=True)
    p_add.set_defaults(func=cmd_add)

    p_remove = subparsers.add_parser("remove")
    p_remove.add_argument("code")
    p_remove.set_defaults(func=cmd_remove)

    p_update = subparsers.add_parser("update")
    p_update.add_argument("code")
    p_update.add_argument("--cost", default=None)
    p_update.add_argument("--quantity", default=None)
    p_update.set_defaults(func=cmd_update)

    p_list = subparsers.add_parser("list")
    p_list.set_defaults(func=cmd_list)

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    args.func(args)

if __name__ == "__main__":
    main()
PORTFOLIO_EOF

RUN chmod +x /opt/a-stock-analysis/scripts/analyze.py /opt/a-stock-analysis/scripts/portfolio.py

# Create a uv project
RUN mkdir -p /opt/a-stock-analysis
RUN printf '[project]\nname = "a-stock-analysis"\nversion = "0.1.0"\nrequires-python = ">=3.11"\ndependencies = ["requests"]\n' > /opt/a-stock-analysis/pyproject.toml

RUN mkdir -p /workspace
WORKDIR /workspace