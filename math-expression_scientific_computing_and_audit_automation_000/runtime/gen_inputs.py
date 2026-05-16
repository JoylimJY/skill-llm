import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create a realistic deeply nested directory structure with distractor files
dirs = [
    "workspace/audit_pipeline/input_batches",
    "workspace/audit_pipeline/output_reports",
    "workspace/audit_pipeline/logs",
    "workspace/audit_pipeline/configs",
    "workspace/audit_pipeline/archive/2023/q3",
    "workspace/audit_pipeline/archive/2023/q4",
    "workspace/audit_pipeline/archive/2024/q1",
    "workspace/numerical_lib/src/core",
    "workspace/numerical_lib/src/utils",
    "workspace/numerical_lib/tests",
    "workspace/numerical_lib/docs",
    "workspace/compliance/reports/pending",
    "workspace/compliance/reports/approved",
    "workspace/compliance/schemas",
    "workspace/scripts",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# Distractor files
distractor_files = {
    "workspace/audit_pipeline/configs/pipeline_config.yaml": """
pipeline_version: 2.1.0
batch_size: 10
retry_limit: 3
output_format: json
precision_default: 50
""",
    "workspace/audit_pipeline/logs/pipeline_run_20240312.log": """
[2024-03-12 09:14:22] INFO  Pipeline started
[2024-03-12 09:14:23] INFO  Loading batch: batch_007.json
[2024-03-12 09:14:45] ERROR Timeout on expression index 3
[2024-03-12 09:14:46] INFO  Retrying...
[2024-03-12 09:15:01] INFO  Batch complete. 9/10 passed.
""",
    "workspace/audit_pipeline/archive/2023/q4/batch_summary_q4.json": json.dumps({
        "quarter": "2023-Q4",
        "total_expressions": 42,
        "verified_ok": 38,
        "verified_null": 4,
        "failed": 0
    }, indent=2),
    "workspace/numerical_lib/src/core/integration.py": """
# Numerical integration utilities
import math

def trapezoidal(f, a, b, n=1000):
    h = (b - a) / n
    return h * (f(a)/2 + sum(f(a + i*h) for i in range(1, n)) + f(b)/2)
""",
    "workspace/numerical_lib/src/utils/precision.py": """
# Precision management
DEFAULT_PRECISION = 50
HIGH_PRECISION = 120

def get_precision_digits(level='default'):
    return DEFAULT_PRECISION if level == 'default' else HIGH_PRECISION
""",
    "workspace/numerical_lib/tests/test_integration.py": """
import pytest
from src.core.integration import trapezoidal
import math

def test_sin_squared():
    result = trapezoidal(lambda x: math.sin(x)**2, 0, math.pi)
    assert abs(result - math.pi/2) < 1e-4
""",
    "workspace/numerical_lib/docs/formulas.md": """
# Key Formulas

## Definite Integrals
- integral of sin^2(x) from 0 to pi = pi/2

## Polynomial Roots
- x^5 - x - 1 = 0 has one real root near x ≈ 1.1673

## Limits
- lim_{x->0} (sin(x) - x) / x^3 = -1/6

## Constants
- Pi to 120 digits needed for high-precision calibration
""",
    "workspace/compliance/schemas/audit_report_schema.json": json.dumps({
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["audit_id", "expressions", "summary"],
        "properties": {
            "audit_id": {"type": "string"},
            "expressions": {"type": "array"},
            "summary": {"type": "object"}
        }
    }, indent=2),
    "workspace/compliance/reports/pending/batch_009_stub.json": json.dumps({
        "audit_id": "AUDIT-2024-009",
        "status": "pending",
        "note": "Awaiting computation results"
    }, indent=2),
    "workspace/audit_pipeline/archive/2024/q1/run_metadata.json": json.dumps({
        "run_id": "run-20240101-001",
        "expressions_evaluated": 15,
        "engine": "WolframKernel",
        "precision": 80
    }, indent=2),
    "workspace/scripts/legacy_eval.sh": """#!/bin/bash
# DEPRECATED: use eval_expression.py instead
echo "This script is no longer maintained"
exit 1
""",
}

for path, content in distractor_files.items():
    with open(path, "w") as f:
        f.write(content)

# THE ACTUAL PROBLEM: A batch of math expressions to evaluate
# The agent must process these and produce a consolidated audit report

batch_input = {
    "audit_id": "AUDIT-2024-042",
    "requested_by": "Dr. Chen, Numerical Analysis Division",
    "description": "Regulatory compliance audit for numerical library v3.2. Verify the following mathematical identities used as calibration benchmarks.",
    "expressions": [
        {
            "id": "expr-001",
            "label": "Definite integral: sin^2 over [0, pi]",
            "wolfram_expr": "Integrate[Sin[x]^2, {x, 0, Pi}]",
            "required_precision": 50,
            "notes": "Standard calibration integral. Must verify exact vs numeric consistency."
        },
        {
            "id": "expr-002",
            "label": "Limit: (sin(x) - x) / x^3 as x -> 0",
            "wolfram_expr": "Limit[(Sin[x] - x)/x^3, x -> 0]",
            "required_precision": 50,
            "notes": "Symbolic limit result. Consistency verification may not apply."
        },
        {
            "id": "expr-003",
            "label": "High-precision Pi (120 digits)",
            "wolfram_expr": "N[Pi, 120]",
            "required_precision": 120,
            "notes": "High-precision constant for calibration. Use 120-digit precision."
        },
        {
            "id": "expr-004",
            "label": "Polynomial root: x^5 - x - 1 = 0",
            "wolfram_expr": "Solve[x^5 - x - 1 == 0, x]",
            "required_precision": 80,
            "notes": "Root-finding. Returns symbolic list; numeric consistency verification likely null."
        }
    ]
}

with open("workspace/audit_pipeline/input_batches/batch_042.json", "w") as f:
    json.dump(batch_input, f, indent=2)

# Also create a partial results file from a previous failed run (distractor/context)
partial_results = {
    "audit_id": "AUDIT-2024-042",
    "status": "INCOMPLETE - run aborted",
    "partial_results": [
        {
            "id": "expr-001",
            "error": "timeout",
            "result": None
        }
    ]
}
with open("workspace/audit_pipeline/output_reports/batch_042_partial_FAILED.json", "w") as f:
    json.dump(partial_results, f, indent=2)

print("Workspace generated successfully.")
print(f"Input batch: workspace/audit_pipeline/input_batches/batch_042.json")