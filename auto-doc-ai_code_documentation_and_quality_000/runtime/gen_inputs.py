import os
import random

random.seed(42)

workspace = "/workspace"

# Create directory structure: src/ with nested subdirs
dirs = [
    "src",
    "src/pipeline",
    "src/pipeline/transforms",
    "src/models",
    "src/utils",
    "src/validators",
    "tests",
    "tests/unit",
    "tests/integration",
    "config",
    "scripts",
    "docs",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ─── src/pipeline/__init__.py ────────────────────────────────────────────────
with open(os.path.join(workspace, "src/pipeline/__init__.py"), "w") as f:
    f.write('"""Pipeline package."""\n')

# ─── src/pipeline/ingest.py ──────────────────────────────────────────────────
# Mix: one function with NO docstring, one with a BAD/STUB docstring
with open(os.path.join(workspace, "src/pipeline/ingest.py"), "w") as f:
    f.write('''\
import csv
import json
from typing import List, Dict, Any


def load_csv(filepath: str, delimiter: str = ",") -> List[Dict[str, Any]]:
    # TODO: add docs
    rows = []
    with open(filepath, newline="") as fh:
        reader = csv.DictReader(fh, delimiter=delimiter)
        for row in reader:
            rows.append(dict(row))
    return rows


def load_json(filepath: str) -> Any:
    """Load stuff.

    Stub docstring that is not Google Style.
    """
    with open(filepath) as fh:
        return json.load(fh)


def normalize_record(record: Dict[str, Any], schema: Dict[str, str]) -> Dict[str, Any]:
    """Normalize a record based on schema types.

    Args:
        record (Dict[str, Any]): The raw record dictionary.
        schema (Dict[str, str]): Mapping of field names to expected types.

    Returns:
        Dict[str, Any]: Normalized record with type-cast values.

    Raises:
        ValueError: If a field value cannot be cast to the specified type.
    """
    result = {}
    for key, type_str in schema.items():
        val = record.get(key)
        if type_str == "int":
            result[key] = int(val)
        elif type_str == "float":
            result[key] = float(val)
        else:
            result[key] = str(val)
    return result
''')

# ─── src/pipeline/transforms/__init__.py ─────────────────────────────────────
with open(os.path.join(workspace, "src/pipeline/transforms/__init__.py"), "w") as f:
    f.write("")

# ─── src/pipeline/transforms/clean.py ────────────────────────────────────────
# All functions have NO docstrings
with open(os.path.join(workspace, "src/pipeline/transforms/clean.py"), "w") as f:
    f.write('''\
import re
from typing import Optional


def strip_whitespace(text: str) -> str:
    return text.strip()


def remove_special_chars(text: str, keep_pattern: Optional[str] = None) -> str:
    if keep_pattern:
        return re.sub(f"[^\\w{re.escape(keep_pattern)}]", "", text)
    return re.sub(r"[^\\w]", "", text)


def normalize_amount(amount_str: str, currency_symbol: str = "$") -> float:
    cleaned = amount_str.replace(currency_symbol, "").replace(",", "").strip()
    return float(cleaned)
''')

# ─── src/models/__init__.py ───────────────────────────────────────────────────
with open(os.path.join(workspace, "src/models/__init__.py"), "w") as f:
    f.write("")

# ─── src/models/transaction.py ───────────────────────────────────────────────
# Class with methods: one has a stub docstring, one has no docstring
with open(os.path.join(workspace, "src/models/transaction.py"), "w") as f:
    f.write('''\
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Transaction:
    """Represents a financial transaction."""

    transaction_id: str
    amount: float
    currency: str
    timestamp: datetime
    description: Optional[str] = None
    tags: list = field(default_factory=list)

    def is_debit(self) -> bool:
        """Check debit.

        bad docs
        """
        return self.amount < 0

    def apply_fx_rate(self, rate: float, target_currency: str) -> "Transaction":
        new_amount = self.amount * rate
        return Transaction(
            transaction_id=self.transaction_id,
            amount=new_amount,
            currency=target_currency,
            timestamp=self.timestamp,
            description=self.description,
            tags=self.tags,
        )

    def to_dict(self):
        return {
            "transaction_id": self.transaction_id,
            "amount": self.amount,
            "currency": self.currency,
            "timestamp": self.timestamp.isoformat(),
            "description": self.description,
            "tags": self.tags,
        }
''')

# ─── src/validators/__init__.py ──────────────────────────────────────────────
with open(os.path.join(workspace, "src/validators/__init__.py"), "w") as f:
    f.write("")

# ─── src/validators/schema_validator.py ──────────────────────────────────────
# Functions with NO docstrings and one with a totally wrong docstring
with open(os.path.join(workspace, "src/validators/schema_validator.py"), "w") as f:
    f.write('''\
from typing import Any, Dict, List


def validate_required_fields(record: Dict[str, Any], required: List[str]) -> bool:
    for field in required:
        if field not in record or record[field] is None:
            return False
    return True


def validate_amount_range(amount: float, min_val: float = 0.0, max_val: float = 1e9) -> bool:
    """This function validates something about amounts.

    Not documented properly at all.
    Just a placeholder.
    """
    return min_val <= amount <= max_val


def validate_currency_code(code: str) -> bool:
    return len(code) == 3 and code.isalpha() and code.isupper()
''')

# ─── src/utils/__init__.py ────────────────────────────────────────────────────
with open(os.path.join(workspace, "src/utils/__init__.py"), "w") as f:
    f.write("")

# ─── src/utils/logger.py ─────────────────────────────────────────────────────
# All functions undocumented
with open(os.path.join(workspace, "src/utils/logger.py"), "w") as f:
    f.write('''\
import logging
import sys
from typing import Optional


def setup_logger(name: str, level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    handler = logging.StreamHandler(sys.stdout)
    if log_file:
        handler = logging.FileHandler(log_file)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def log_event(logger: logging.Logger, event_type: str, payload: dict) -> None:
    logger.info(f"EVENT:{event_type} DATA:{payload}")
''')

# ─── src/__init__.py ─────────────────────────────────────────────────────────
with open(os.path.join(workspace, "src/__init__.py"), "w") as f:
    f.write('"""Fintech pipeline source package."""\n')

# ─── Distractor files (not in src/) ──────────────────────────────────────────

# tests/unit/test_ingest.py
with open(os.path.join(workspace, "tests/unit/test_ingest.py"), "w") as f:
    f.write('''\
import pytest
from src.pipeline.ingest import load_csv, normalize_record


def test_normalize_record_basic():
    record = {"amount": "42", "name": "Alice"}
    schema = {"amount": "int", "name": "str"}
    result = normalize_record(record, schema)
    assert result["amount"] == 42
    assert result["name"] == "Alice"
''')

# tests/integration/test_pipeline.py
with open(os.path.join(workspace, "tests/integration/test_pipeline.py"), "w") as f:
    f.write('''\
# Integration tests placeholder
def test_placeholder():
    pass
''')

# config/pipeline_config.yaml
with open(os.path.join(workspace, "config/pipeline_config.yaml"), "w") as f:
    f.write('''\
pipeline:
  name: fintech-etl
  version: "2.1.0"
  batch_size: 500
  currency: USD
  log_level: INFO
''')

# scripts/run_pipeline.sh
with open(os.path.join(workspace, "scripts/run_pipeline.sh"), "w") as f:
    f.write('''\
#!/bin/bash
set -e
echo "Starting fintech ETL pipeline..."
python -m src.pipeline
echo "Pipeline complete."
''')

# docs/architecture.md
with open(os.path.join(workspace, "docs/architecture.md"), "w") as f:
    f.write('''\
# Architecture

This document describes the high-level architecture of the fintech data pipeline.
''')

print("Workspace generated successfully.")
print("Files needing docstring work:")
print("  - src/pipeline/ingest.py (load_csv: no docstring; load_json: stub docstring)")
print("  - src/pipeline/transforms/clean.py (all 3 functions: no docstrings)")
print("  - src/models/transaction.py (is_debit: stub; apply_fx_rate: none; to_dict: none)")
print("  - src/validators/schema_validator.py (validate_required_fields: none; validate_amount_range: stub; validate_currency_code: none)")
print("  - src/utils/logger.py (both functions: no docstrings)")