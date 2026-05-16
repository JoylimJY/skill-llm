#!/bin/bash
set -e

# ─────────────────────────────────────────────────────────────────────────────
# Create a mock WolframKernel binary that simulates the real Wolfram Engine
# ─────────────────────────────────────────────────────────────────────────────
cat > /usr/local/bin/WolframKernel << 'WOLFRAM_MOCK_EOF'
#!/usr/bin/env python3
"""
Mock WolframKernel — simulates the Wolfram Engine's packet-based stdin/stdout
protocol as expected by the wolframclient Python library.
"""
import sys
import os
import re
import time

# The wolframclient library communicates with WolframKernel via a binary packet
# protocol. This mock intercepts and handles the protocol at the Python level
# by replacing the kernel process entirely. However, since wolframclient spawns
# WolframKernel as a subprocess and communicates via its stdin/stdout using
# the MathLink/WSTP protocol (binary), a true mock at that level is complex.
# 
# Instead, we mock eval_expression.py directly at the script level.
# This file exists to satisfy the `which WolframKernel` / PATH check.
# The actual mocking is done by monkey-patching eval_expression.py behavior
# via environment variables checked in the mock wolframclient session.

# If called with -h or --help, respond gracefully
if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', '-version']:
    print("Wolfram Kernel 13.3.0 for Linux x86 (64-bit)")
    print("Copyright 1988-2023 Wolfram Research, Inc.")
    sys.exit(0)

# For version check
print("Wolfram Kernel 13.3.0 for Linux x86 (64-bit)")
sys.exit(0)
WOLFRAM_MOCK_EOF
chmod +x /usr/local/bin/WolframKernel

# ─────────────────────────────────────────────────────────────────────────────
# Create the skill's main script directory and eval_expression.py
# This simulates the {baseDir}/scripts/eval_expression.py from SKILL.md
# ─────────────────────────────────────────────────────────────────────────────
mkdir -p /opt/math-expression/scripts

cat > /opt/math-expression/scripts/eval_expression.py << 'EVAL_SCRIPT_EOF'
#!/usr/bin/env python3
"""
eval_expression.py — Wolfram Language expression evaluator.
Skill: math-expression (SKILL.md)
"""

import argparse
import json
import sys
import re
import os
import subprocess
import time

VERSION = "math-expression-skill/1.0.0 (WolframKernel 13.3.0)"

# Safety guard: blocked Wolfram symbols
BLOCKED_SYMBOLS = [
    "Import", "Export", "URLRead", "URLFetch", "URLPost",
    "Run", "RunProcess", "Get", "Put", "OpenRead", "OpenWrite",
    "DeleteFile", "CopyFile", "CreateDirectory", "DeleteDirectory",
    "SystemOpen", "StartProcess", "LinkLaunch", "ReadList"
]

# ── Mock evaluation engine ────────────────────────────────────────────────────
# In a real deployment this would use wolframclient.WolframLanguageSession.
# Here we implement a deterministic lookup table for the benchmark expressions.

MOCK_RESULTS = {
    # key: (normalized_expr, precision) -> (exact, numeric, verified)
    # We match on normalized expression string
}

def normalize_expr(expr: str) -> str:
    return re.sub(r'\s+', '', expr.strip())

def mock_evaluate(expr: str, precision: int):
    """
    Returns (exact_str, numeric_str, verified) for known benchmark expressions.
    verified: True/False/None
    """
    n = normalize_expr(expr)

    # Integrate[Sin[x]^2, {x, 0, Pi}]
    if re.match(r'Integrate\[Sin\[x\]\^2,\{x,0,Pi\}\]', n, re.IGNORECASE):
        exact = "Pi/2"
        # Generate numeric with requested precision
        import decimal
        decimal.getcontext().prec = precision + 10
        pi_val = decimal.Decimal(
            "3.14159265358979323846264338327950288419716939937510"
            "58209749445923078164062862089986280348253421170679"
            "82148086513282306647093844609550582231725359408128"
            "48111745028410270193852110555964462294895493038196"
        )
        numeric_val = pi_val / 2
        numeric_str = str(numeric_val)[:precision + 2]
        # Trim trailing zeros after decimal
        return exact, numeric_str, True

    # Limit[(Sin[x] - x)/x^3, x -> 0]
    if re.match(r'Limit\[\(Sin\[x\]-x\)/x\^3,x->0\]', n, re.IGNORECASE) or \
       re.match(r'Limit\[\(Sin\[x\]-x\)/x\^3,x\->0\]', n):
        exact = "-1/6"
        numeric_str = "-0." + "1" * (precision // 10) + "6666666666666667"
        numeric_str = "-0.16666666666666666666666666666666666666666666666667"
        if precision > 50:
            numeric_str = "-0." + "6" * precision  # simplified
        return exact, numeric_str, None  # limit is symbolic; verified=null

    # N[Pi, <precision>]  — high precision pi
    if re.match(r'N\[Pi,\d+\]', n):
        m = re.match(r'N\[Pi,(\d+)\]', n)
        prec = int(m.group(1)) if m else precision
        # Return Pi to requested digits
        pi_full = (
            "3.14159265358979323846264338327950288419716939937510"
            "58209749445923078164062862089986280348253421170679"
            "82148086513282306647093844609550582231725359408128"
            "48111745028410270193852110555964462294895493038196"
            "44288109756659334461284756482337867831652712019091"
            "45648566923460348610454326648213393607260249141273"
            "72458700660631558817488152092096282925409171536436"
        )
        # exact = Pi (symbolic), numeric = digits
        digits_needed = prec + 2
        numeric_str = pi_full[:digits_needed] if digits_needed <= len(pi_full) else pi_full
        return "Pi", numeric_str, True

    # Solve[x^5 - x - 1 == 0, x]
    if re.match(r'Solve\[x\^5-x-1==0,x\]', n, re.IGNORECASE):
        # Returns a list of rules — symbolic, mixed complex roots
        exact = "{{x -> Root[-1 - #1 + #1^5 &, 1]}, {x -> Root[-1 - #1 + #1^5 &, 2]}, {x -> Root[-1 - #1 + #1^5 &, 3]}, {x -> Root[-1 - #1 + #1^5 &, 4]}, {x -> Root[-1 - #1 + #1^5 &, 5]}}"
        numeric_str = "{{x -> -0.7548776662466927 - 0.8746973440836854*I}, {x -> -0.7548776662466927 + 0.8746973440836854*I}, {x -> 0.2043506454998643 - 1.1380311843117789*I}, {x -> 0.2043506454998643 + 1.1380311843117789*I}, {x -> 1.1673039782614187}}"
        return exact, numeric_str, None  # list of roots; verified=null

    # Unknown expression
    raise ValueError(f"Unknown expression for mock evaluation: {expr}")


def check_safety(expr: str):
    """Returns list of blocked symbols found in expression."""
    found = []
    for sym in BLOCKED_SYMBOLS:
        pattern = r'\b' + re.escape(sym) + r'\s*\['
        if re.search(pattern, expr):
            found.append(sym)
    return found


def main():
    parser = argparse.ArgumentParser(description="Evaluate Wolfram Language math expressions.")
    parser.add_argument("--expr", required=True, help="Wolfram Language expression to evaluate")
    parser.add_argument("--precision", type=int, default=50, help="Numeric precision (digits), default 50")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout in seconds, default 30")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Output machine-readable JSON")
    parser.add_argument("--no-verify", action="store_true", help="Skip consistency verification")
    parser.add_argument("--allow-unsafe", action="store_true", help="Bypass safety guard (isolated env only)")

    args = parser.parse_args()

    expr = args.expr.strip()
    if not expr:
        print("ERROR: Empty expression", file=sys.stderr)
        sys.exit(2)

    warnings = []

    # Safety check
    if not args.allow_unsafe:
        blocked = check_safety(expr)
        if blocked:
            msg = f"SAFETY BLOCK: Expression contains restricted symbols: {blocked}. Use --allow-unsafe in isolated env."
            if args.json_output:
                print(json.dumps({"error": msg, "expr": expr, "exit_code": 4}))
            else:
                print(f"ERROR: {msg}", file=sys.stderr)
            sys.exit(4)

    # Check WolframKernel is available
    import shutil
    if not shutil.which("WolframKernel"):
        print("ERROR: WolframKernel not found in PATH", file=sys.stderr)
        sys.exit(3)

    # Check wolframclient
    try:
        import wolframclient
    except ImportError:
        print("ERROR: wolframclient Python package not installed", file=sys.stderr)
        sys.exit(3)

    # Evaluate
    try:
        exact, numeric, verified_raw = mock_evaluate(expr, args.precision)
    except Exception as e:
        msg = f"Evaluation failed: {e}"
        if args.json_output:
            print(json.dumps({"error": msg, "expr": expr, "exit_code": 4}))
        else:
            print(f"ERROR: {msg}", file=sys.stderr)
        sys.exit(4)

    # Handle --no-verify
    if args.no_verify:
        verified = None
        warnings.append("Consistency verification skipped (--no-verify)")
    else:
        verified = verified_raw

    result = {
        "expr": expr,
        "exact": exact,
        "numeric": numeric,
        "verified": verified,
        "precision": args.precision,
        "version": VERSION,
        "warnings": warnings
    }

    if args.json_output:
        print(json.dumps(result, indent=2))
    else:
        print(f"Exact   : {exact}")
        print(f"Numeric : {numeric}")
        print(f"Verified: {verified}")
        print(f"Version : {VERSION}")
        if warnings:
            for w in warnings:
                print(f"Warning : {w}")

    sys.exit(0)


if __name__ == "__main__":
    main()
EVAL_SCRIPT_EOF

chmod +x /opt/math-expression/scripts/eval_expression.py

# ─────────────────────────────────────────────────────────────────────────────
# Make it runnable as both:
#   python3 /opt/math-expression/scripts/eval_expression.py
#   python3 -m ... (via symlink or path)
# ─────────────────────────────────────────────────────────────────────────────
ln -sf /opt/math-expression/scripts/eval_expression.py /usr/local/bin/eval_expression.py

echo "Setup complete. WolframKernel mock and eval_expression.py are ready."
echo "Skill base dir: /opt/math-expression"
ls -la /opt/math-expression/scripts/
which WolframKernel && echo "WolframKernel: OK"
python3 -c "import wolframclient; print('wolframclient: OK')"