import os
import random

random.seed(42)

base = "/workspace/trade_analytics"
os.makedirs(base, exist_ok=True)

# Create directory structure
dirs = [
    "src/ingestion",
    "src/processing",
    "src/reporting",
    "src/models",
    "tests/unit",
    "tests/integration",
    "scripts",
    "docs",
    "config",
    "logs",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# ---- Distractor files (valid, unrelated) ----

with open(os.path.join(base, "scripts/backfill.py"), "w") as f:
    f.write("""\
#!/usr/bin/env python3
\"\"\"Historical backfill script.\"\"\"
import datetime

def backfill(start: str, end: str) -> None:
    s = datetime.date.fromisoformat(start)
    e = datetime.date.fromisoformat(end)
    print(f"Backfilling from {s} to {e}")

if __name__ == "__main__":
    backfill("2023-01-01", "2023-12-31")
""")

with open(os.path.join(base, "docs/architecture.md"), "w") as f:
    f.write("# Architecture\n\nThis document describes the trade analytics pipeline.\n")

with open(os.path.join(base, "config/settings.ini"), "w") as f:
    f.write("[database]\nhost=localhost\nport=5432\nname=trades\n")

with open(os.path.join(base, "logs/.gitkeep"), "w") as f:
    f.write("")

with open(os.path.join(base, "tests/unit/test_placeholder.py"), "w") as f:
    f.write("# placeholder\n")

with open(os.path.join(base, "tests/integration/test_pipeline.py"), "w") as f:
    f.write("# integration tests placeholder\n")

with open(os.path.join(base, ".gitignore"), "w") as f:
    f.write("__pycache__/\n*.pyc\nlogs/\n")

with open(os.path.join(base, "scripts/deploy.sh"), "w") as f:
    f.write("#!/bin/bash\necho 'Deploying trade analytics service'\n")

with open(os.path.join(base, "config/logging.yaml"), "w") as f:
    f.write("version: 1\nformatters:\n  simple:\n    format: '%(levelname)s %(message)s'\n")

# ---- BROKEN source files with type errors ----

# src/models/trade.py - has type errors
with open(os.path.join(base, "src/models/trade.py"), "w") as f:
    f.write('''\
"""Trade data models."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Trade:
    trade_id: str
    symbol: str
    quantity: int
    price: float
    side: str  # "buy" or "sell"
    counterparty: Optional[str]


def compute_notional(trade: Trade) -> float:
    # BUG: quantity is int, price is float -> result should be float, but we return str
    result: str = trade.quantity * trade.price
    return result


def get_trade_summary(trades: list) -> dict:
    # BUG: no type annotations, return type mismatch
    total: int = 0.0
    for t in trades:
        total += t.quantity
    return total
''')

# src/ingestion/parser.py - has type errors
with open(os.path.join(base, "src/ingestion/parser.py"), "w") as f:
    f.write('''\
"""Raw trade data parser."""
from typing import List, Dict, Any
from src.models.trade import Trade


def parse_csv_row(row: Dict[str, str]) -> Trade:
    """Parse a CSV row into a Trade object."""
    trade = Trade(
        trade_id=row["trade_id"],
        symbol=row["symbol"],
        quantity=row["quantity"],  # BUG: str assigned to int field
        price=float(row["price"]),
        side=row["side"],
        counterparty=row.get("counterparty"),
    )
    return trade


def parse_all(rows: List[Dict[str, str]]) -> List[Trade]:
    return [parse_csv_row(r) for r in rows]
''')

# src/processing/aggregator.py - has type errors
with open(os.path.join(base, "src/processing/aggregator.py"), "w") as f:
    f.write('''\
"""Aggregation logic for trade data."""
from typing import List, Dict
from src.models.trade import Trade


def group_by_symbol(trades: List[Trade]) -> Dict[str, List[Trade]]:
    result: Dict[str, List[Trade]] = {}
    for trade in trades:
        key: int = trade.symbol   # BUG: symbol is str, assigned to int-annotated key
        if key not in result:
            result[key] = []
        result[key].append(trade)
    return result


def total_volume(trades: List[Trade]) -> float:
    # BUG: returns int sum when return type is float (minor, but wrong accumulator type annotation)
    volume: str = 0
    for t in trades:
        volume += t.quantity
    return volume
''')

# src/reporting/report.py - has type errors
with open(os.path.join(base, "src/reporting/report.py"), "w") as f:
    f.write('''\
"""Report generation."""
from typing import List, Optional
from src.models.trade import Trade


def format_trade(trade: Trade) -> str:
    return f"{trade.trade_id}: {trade.symbol} {trade.side} {trade.quantity}@{trade.price}"


def generate_report(trades: List[Trade], title: Optional[str]) -> str:
    lines: List[str] = []
    # BUG: title used without None check in arithmetic context
    header: int = title + " Report"
    lines.append(header)
    for t in trades:
        lines.append(format_trade(t))
    return "\\n".join(lines)


def save_report(content: str, path: str) -> None:
    # BUG: wrong type for file handle
    fh: int = open(path, "w")
    fh.write(content)
    fh.close()
''')

# src/__init__.py
with open(os.path.join(base, "src/__init__.py"), "w") as f:
    f.write("")

with open(os.path.join(base, "src/ingestion/__init__.py"), "w") as f:
    f.write("")

with open(os.path.join(base, "src/processing/__init__.py"), "w") as f:
    f.write("")

with open(os.path.join(base, "src/reporting/__init__.py"), "w") as f:
    f.write("")

with open(os.path.join(base, "src/models/__init__.py"), "w") as f:
    f.write("")

print("Workspace generated successfully at", base)
print("Files with intentional type errors:")
print("  src/models/trade.py")
print("  src/ingestion/parser.py")
print("  src/processing/aggregator.py")
print("  src/reporting/report.py")