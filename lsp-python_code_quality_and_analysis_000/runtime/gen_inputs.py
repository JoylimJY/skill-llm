import os
import random
import stat

random.seed(42)

WORKSPACE = "/workspace"

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "fintech_etl/scripts",
    "fintech_etl/pipeline",
    "fintech_etl/pipeline/ingestion",
    "fintech_etl/pipeline/transformation",
    "fintech_etl/pipeline/output",
    "fintech_etl/utils",
    "fintech_etl/config",
    "fintech_etl/tests",
    "fintech_etl/docs",
    "fintech_etl/legacy",
    "scripts",          # <-- lsp skill scripts live here
    "references",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ── LSP skill scripts (the SKILL.md says "all scripts already exist") ────────

# lsp-service.py  – real minimal implementation wrapping pylsp diagnostics
lsp_service_py = r'''#!/usr/bin/env python3
"""Minimal lsp-service wrapper for code quality checking."""
import sys
import json
import subprocess
import tempfile
import os

SEVERITY_ICON = {1: "❌", 2: "⚠️", 3: "ℹ️", 4: "💡"}

def run_pyflakes(filepath):
    result = subprocess.run(
        [sys.executable, "-m", "pyflakes", filepath],
        capture_output=True, text=True
    )
    issues = []
    for line in (result.stdout + result.stderr).splitlines():
        line = line.strip()
        if not line:
            continue
        # format: filepath:lineno: message
        parts = line.split(":", 2)
        if len(parts) >= 3:
            try:
                lineno = int(parts[1].strip())
            except ValueError:
                lineno = 0
            msg = parts[2].strip()
        else:
            lineno = 0
            msg = line
        issues.append({"line": lineno, "source": "pyflakes", "message": msg, "severity": 2})
    return issues

def run_pycodestyle(filepath):
    result = subprocess.run(
        [sys.executable, "-m", "pycodestyle", "--max-line-length=79", filepath],
        capture_output=True, text=True
    )
    issues = []
    for line in (result.stdout + result.stderr).splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(":", 3)
        if len(parts) >= 4:
            try:
                lineno = int(parts[1].strip())
            except ValueError:
                lineno = 0
            msg = parts[3].strip()
        else:
            lineno = 0
            msg = line
        # Errors start with E, Warnings with W
        code = msg.split()[0] if msg else ""
        severity = 1 if code.startswith("E") else 2
        issues.append({"line": lineno, "source": "pycodestyle", "message": msg, "severity": severity})
    return issues

def cmd_check(filepath):
    if not os.path.isfile(filepath):
        print(f"❌ 文件不存在: {filepath}")
        return
    issues = run_pyflakes(filepath) + run_pycodestyle(filepath)
    if not issues:
        print("✅ 没有发现问题")
        return
    for issue in sorted(issues, key=lambda x: x["line"]):
        icon = SEVERITY_ICON.get(issue["severity"], "⚠️")
        print(f"{icon} 第 {issue['line']} 行 [{issue['source']}]: {issue['message']}")

def cmd_complete(filepath, line, char):
    print("补全建议:")
    print("  • (completion not available in minimal mode)")

def cmd_info(filepath, line, char):
    print("(hover info not available in minimal mode)")

def cmd_goto(filepath, line, char):
    print("(goto not available in minimal mode)")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: lsp-service.py <check|complete|info|goto> <file> [line] [char]")
        sys.exit(1)
    cmd = sys.argv[1]
    fpath = sys.argv[2]
    if cmd == "check":
        cmd_check(fpath)
    elif cmd == "complete":
        cmd_complete(fpath, int(sys.argv[3]), int(sys.argv[4]))
    elif cmd == "info":
        cmd_info(fpath, int(sys.argv[3]), int(sys.argv[4]))
    elif cmd == "goto":
        cmd_goto(fpath, int(sys.argv[3]), int(sys.argv[4]))
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
'''

# check_python.py – batch checker with --auto-fix
check_python_py = r'''#!/usr/bin/env python3
"""Batch Python code quality checker with optional auto-fix."""
import sys
import os
import subprocess
import argparse

SEVERITY_ICON = {1: "❌", 2: "⚠️", 3: "ℹ️", 4: "💡"}

def find_python_files(path):
    if os.path.isfile(path):
        return [path] if path.endswith(".py") else []
    result = []
    for root, dirs, files in os.walk(path):
        # skip hidden and __pycache__
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
        for f in files:
            if f.endswith(".py"):
                result.append(os.path.join(root, f))
    return sorted(result)

def check_file(filepath):
    issues = []
    # pyflakes
    r = subprocess.run(
        [sys.executable, "-m", "pyflakes", filepath],
        capture_output=True, text=True
    )
    for line in (r.stdout + r.stderr).splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(":", 2)
        if len(parts) >= 3:
            try:
                lineno = int(parts[1].strip())
            except ValueError:
                lineno = 0
            msg = parts[2].strip()
        else:
            lineno = 0
            msg = line
        issues.append({"line": lineno, "source": "pyflakes", "message": msg, "severity": 2})
    # pycodestyle
    r2 = subprocess.run(
        [sys.executable, "-m", "pycodestyle", "--max-line-length=79", filepath],
        capture_output=True, text=True
    )
    for line in (r2.stdout + r2.stderr).splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(":", 3)
        if len(parts) >= 4:
            try:
                lineno = int(parts[1].strip())
            except ValueError:
                lineno = 0
            msg = parts[3].strip()
        else:
            lineno = 0
            msg = line
        code = msg.split()[0] if msg else ""
        severity = 1 if code.startswith("E") else 2
        issues.append({"line": lineno, "source": "pycodestyle", "message": msg, "severity": severity})
    return issues

def auto_fix(path):
    # Remove unused imports
    subprocess.run(
        [sys.executable, "-m", "autoflake",
         "--remove-all-unused-imports", "--in-place", "--recursive", path],
        capture_output=True
    )
    # Format with black
    subprocess.run(
        [sys.executable, "-m", "black", path],
        capture_output=True
    )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="File or directory to check")
    parser.add_argument("--auto-fix", action="store_true", help="Auto-fix issues")
    args = parser.parse_args()

    if args.auto_fix:
        print(f"🔧 自动修复: {args.path}")
        auto_fix(args.path)
        print("✅ 修复完成")

    files = find_python_files(args.path)
    total_issues = 0
    for fpath in files:
        issues = check_file(fpath)
        if issues:
            print(f"\n=== {fpath} ===")
            for issue in sorted(issues, key=lambda x: x["line"]):
                icon = SEVERITY_ICON.get(issue["severity"], "⚠️")
                print(f"{icon} 第 {issue['line']} 行 [{issue['source']}]: {issue['message']}")
            total_issues += len(issues)
        else:
            print(f"✅ {fpath}: 没有发现问题")

    print(f"\n总计: {len(files)} 个文件, {total_issues} 个问题")

if __name__ == "__main__":
    main()
'''

with open(os.path.join(WORKSPACE, "scripts", "lsp-service.py"), "w") as f:
    f.write(lsp_service_py)

with open(os.path.join(WORKSPACE, "scripts", "check_python.py"), "w") as f:
    f.write(check_python_py)

# ── Distractor/config files (non-Python, just noise) ────────────────────────
distractor_files = {
    "fintech_etl/config/db_config.yaml": "host: localhost\nport: 5432\ndbname: fintech\n",
    "fintech_etl/config/pipeline.toml": "[pipeline]\nmax_retries = 3\ntimeout = 30\n",
    "fintech_etl/docs/architecture.md": "# Architecture\nSee confluence for details.\n",
    "fintech_etl/docs/changelog.txt": "v1.0.0 - initial release\nv1.1.0 - added retry logic\n",
    "fintech_etl/.gitignore": "__pycache__/\n*.pyc\n.env\n",
    "fintech_etl/requirements.txt": "pandas==1.5.0\nnumpy==1.24.0\nrequests==2.28.0\n",
    "fintech_etl/tests/conftest.py": "# conftest placeholder\nimport pytest\n",
    "fintech_etl/legacy/README.txt": "Legacy code - do not modify without approval.\n",
}
for path, content in distractor_files.items():
    full = os.path.join(WORKSPACE, path)
    with open(full, "w") as f:
        f.write(content)

# ── Messy Python source files WITH deliberate issues ────────────────────────

# File 1: ingestion/fetch_trades.py
# Issues: unused import (os, datetime), E302 (missing 2 blank lines before function)
fetch_trades = '''\
import os
import sys
import datetime
import json


def fetch_raw_trades(source_url, api_key):
    """Fetch raw trade data from external source."""
    print(f"Fetching from {source_url}")
    return []
def parse_trade_record(record):
    """Parse a single trade record dict."""
    return {
        "id": record.get("trade_id"),
        "amount": record.get("amount", 0.0),
        "currency": record.get("currency", "USD"),
    }
'''

# File 2: transformation/normalize.py
# Issues: unused import (re), W293 (whitespace on blank line), E501 (line too long)
normalize = '''\
import re
import json
from decimal import Decimal


def normalize_amount(raw_amount, currency="USD"):
    """Convert raw string amount to Decimal with currency normalization."""
    cleaned = str(raw_amount).replace(",", "").strip()
    return Decimal(cleaned)


def normalize_currency_code(code):
    # Map legacy codes to ISO 4217
    mapping = {"US": "USD", "EU": "EUR", "GB": "GBP", "JP": "JPY", "CN": "CNY", "AU": "AUD", "CA": "CAD"}
    return mapping.get(code.upper(), code.upper())
   
def build_normalized_record(raw):
    """Build a fully normalized trade record from raw input dict, applying all transformation rules defined in the fintech compliance spec v2.3."""
    return {
        "trade_id": raw["id"],
        "amount": float(normalize_amount(raw.get("amount", "0"))),
        "currency": normalize_currency_code(raw.get("currency", "USD")),
    }
'''

# File 3: output/write_report.py
# Issues: E402 (import not at top), unused import (pathlib.Path)
write_report = '''\
import json
import sys

# Some runtime setup
DEBUG = False

import os
from pathlib import Path


def write_json_report(data, output_path):
    """Write processed trade data to JSON report file."""
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    print(f"Report written to {output_path}")


def write_csv_report(data, output_path):
    """Write processed trade data to CSV."""
    import csv
    if not data:
        return
    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
'''

# File 4: utils/validators.py
# Issues: unused imports (typing.List, typing.Optional), E711 (comparison to None with ==)
validators = '''\
import re
from typing import List, Optional, Dict


def is_valid_trade_id(trade_id):
    """Validate that trade_id matches expected format TRD-XXXXXXXX."""
    pattern = r"^TRD-[A-Z0-9]{8}$"
    return bool(re.match(pattern, str(trade_id)))


def is_valid_amount(amount):
    """Check amount is positive numeric."""
    try:
        val = float(amount)
        return val > 0
    except (ValueError, TypeError):
        return False


def validate_record(record):
    """Validate a full trade record dict."""
    errors = []
    if record.get("trade_id") == None:
        errors.append("Missing trade_id")
    if not is_valid_amount(record.get("amount", -1)):
        errors.append("Invalid amount")
    return errors
'''

# File 5: pipeline/__init__.py  – clean file (should have 0 issues after fix)
pipeline_init = '''\
"""Fintech ETL pipeline package."""

__version__ = "1.2.0"
__author__ = "FinTech Engineering"
'''

# File 6: legacy/old_loader.py
# Issues: multiple unused imports, W293, E302
old_loader = '''\
import os
import sys
import time
import threading
import logging
import hashlib


def load_legacy_file(filepath):
    print(f"Loading {filepath}")
    data = []
    with open(filepath, "r") as f:
        for line in f:
            data.append(line.strip())
    return data
def process_legacy_record(record):
    """Process a legacy format record."""
    parts = record.split("|")
    if len(parts) < 3:
        return None
    return {"id": parts[0], "amount": parts[1], "currency": parts[2]}
'''

files_to_write = {
    "fintech_etl/pipeline/ingestion/fetch_trades.py": fetch_trades,
    "fintech_etl/pipeline/transformation/normalize.py": normalize,
    "fintech_etl/pipeline/output/write_report.py": write_report,
    "fintech_etl/utils/validators.py": validators,
    "fintech_etl/pipeline/__init__.py": pipeline_init,
    "fintech_etl/legacy/old_loader.py": old_loader,
}

for rel_path, content in files_to_write.items():
    full_path = os.path.join(WORKSPACE, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

print("Workspace generated successfully.")
print("Python files with intentional issues created in fintech_etl/")