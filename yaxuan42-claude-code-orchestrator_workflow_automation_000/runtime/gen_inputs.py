import os
import json
import random
from pathlib import Path

random.seed(42)

WORKSPACE = "/workspace"

# --- Directory structure: a realistic fintech project ---
dirs = [
    "workspace/quant-risk-engine",
    "workspace/quant-risk-engine/src",
    "workspace/quant-risk-engine/src/core",
    "workspace/quant-risk-engine/src/utils",
    "workspace/quant-risk-engine/src/models",
    "workspace/quant-risk-engine/tests",
    "workspace/quant-risk-engine/tests/unit",
    "workspace/quant-risk-engine/tests/integration",
    "workspace/quant-risk-engine/config",
    "workspace/quant-risk-engine/docs",
    "workspace/quant-risk-engine/scripts",
    "workspace/logs",
    "workspace/archive",
    "workspace/tmp_scratch",
]

for d in dirs:
    Path(f"/{d}").mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "/workspace/quant-risk-engine/src/core/var_calculator.py": """\
import numpy as np

def calculate_var(returns, confidence=0.95):
    \"\"\"Calculate Value at Risk.\"\"\"
    sorted_returns = np.sort(returns)
    index = int((1 - confidence) * len(sorted_returns))
    return abs(sorted_returns[index])

def calculate_cvar(returns, confidence=0.95):
    var = calculate_var(returns, confidence)
    losses = returns[returns < -var]
    return abs(losses.mean()) if len(losses) > 0 else var
""",
    "/workspace/quant-risk-engine/src/core/portfolio.py": """\
class Portfolio:
    def __init__(self, name):
        self.name = name
        self.positions = {}
    
    def add_position(self, ticker, quantity, price):
        self.positions[ticker] = {'qty': quantity, 'price': price}
    
    def total_value(self):
        return sum(p['qty'] * p['price'] for p in self.positions.values())
""",
    "/workspace/quant-risk-engine/src/utils/data_loader.py": """\
import csv

def load_returns(filepath):
    returns = []
    with open(filepath) as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            returns.append(float(row[1]))
    return returns
""",
    "/workspace/quant-risk-engine/src/models/factor_model.py": """\
# Placeholder: Fama-French 3-factor model stub
# TODO: implement properly
def factor_exposure(returns, factors):
    raise NotImplementedError(\"Factor model not yet implemented\")
""",
    "/workspace/quant-risk-engine/tests/unit/test_var.py": """\
import pytest
import numpy as np

def test_var_basic():
    returns = np.array([-0.05, -0.03, 0.01, 0.02, 0.04, -0.08, 0.00, -0.02])
    # TODO: assert calculate_var(returns) == expected
    pass
""",
    "/workspace/quant-risk-engine/tests/integration/test_pipeline.py": """\
# Integration test: full pipeline from data load to risk report
# Status: INCOMPLETE - data fixtures missing
def test_full_pipeline():
    pass
""",
    "/workspace/quant-risk-engine/config/risk_params.json": json.dumps({
        "confidence_level": 0.99,
        "lookback_days": 252,
        "max_drawdown_threshold": 0.15,
        "position_limit_usd": 5000000,
        "currencies": ["USD", "EUR", "GBP", "JPY"]
    }, indent=2),
    "/workspace/quant-risk-engine/config/environments.yaml": """\
development:
  database: sqlite:///dev_risk.db
  log_level: DEBUG

production:
  database: postgresql://risk_db:5432/prod
  log_level: WARNING
  alert_webhook: https://alerts.internal/risk
""",
    "/workspace/quant-risk-engine/docs/architecture.md": """\
# Risk Engine Architecture

## Components
1. **Data Ingestion** - pulls market data from internal feeds
2. **VaR Calculator** - computes portfolio VaR using historical simulation
3. **Factor Model** - decomposes risk into systematic/idiosyncratic (WIP)
4. **Reporting** - generates daily risk reports for compliance

## Known Issues
- Factor model is a stub (see src/models/factor_model.py)
- Integration tests are incomplete
- No async support for real-time feeds
""",
    "/workspace/logs/risk_engine_2024-01-15.log": """\
2024-01-15 09:01:22 INFO  Starting risk engine v0.4.2
2024-01-15 09:01:23 INFO  Loaded 847 positions across 12 portfolios
2024-01-15 09:01:31 WARN  Factor model fallback: using simplified beta model
2024-01-15 09:01:45 INFO  VaR calculation complete: portfolio VaR $2.3M at 99%
2024-01-15 09:01:45 ERROR Factor model not yet implemented - skipping idiosyncratic risk
""",
    "/workspace/archive/old_risk_params_v1.json": json.dumps({
        "confidence_level": 0.95,
        "lookback_days": 60,
        "deprecated": True
    }, indent=2),
    "/workspace/tmp_scratch/notes.txt": """\
Meeting notes 2024-01-10:
- Need to refactor factor_model.py before Q1 audit
- Async support is P1 for next sprint
- Ask team about integration test fixtures
""",
}

for path, content in distractor_files.items():
    Path(path).write_text(content)

# --- The actual task inputs the agent needs ---

# 1. The workdir for the task (already created above)
workdir = "/workspace/quant-risk-engine"

# 2. A design document that serves as the prompt-file source
design_doc = """\
# Risk Engine Refactoring Specification

## Objective
Refactor the `factor_model.py` stub into a working Fama-French 3-factor implementation.

## Requirements
1. Implement `factor_exposure(returns, factors)` using OLS regression
2. Add `residual_risk(returns, factors)` helper function  
3. All functions must handle pandas Series and numpy arrays
4. Add inline docstrings following NumPy doc format
5. Existing unit test in `tests/unit/test_var.py` must not break

## Acceptance Criteria
- `factor_model.py` passes a basic smoke test with synthetic data
- Code is type-annotated
- No external dependencies beyond numpy/pandas/scipy
"""

Path("/workspace/quant-risk-engine/docs/refactor-spec.md").write_text(design_doc)

# 3. Task configuration stub (NOT a valid invocation — agent must figure out the right command)
task_stub = {
    "label": "factor-model-refactor",
    "workdir": workdir,
    "description": "Refactor the Fama-French factor model stub in src/models/factor_model.py"
}
Path("/workspace/task-config.json").write_text(json.dumps(task_stub, indent=2))

print("Workspace generated successfully.")
print(f"Workdir: {workdir}")
print(f"Task stub: /workspace/task-config.json")