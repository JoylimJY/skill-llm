---
name: math-expression
description: Evaluate complex Wolfram Language math expressions with exact results, high-precision numerics, and consistency verification. Use when users ask for reliable symbolic/numeric math results.
metadata:
  openclaw:
    os:
      - linux
      - darwin
      - win32
    requires:
      bins:
        - python3
        - WolframKernel
      python:
        - wolframclient
---

# Math Expression (Wolfram Engine)

## Overview

Use this skill to compute complex Wolfram Language expressions with reliable output:

1. Exact/symbolic result
2. High-precision numeric result
3. Consistency verification between exact and numeric forms

## Quick start

```bash
python3 -m pip install --user wolframclient
python {baseDir}/scripts/eval_expression.py --expr "Integrate[Sin[x]^2, {x, 0, Pi}]"
python {baseDir}/scripts/eval_expression.py --expr "Solve[x^5 - x - 1 == 0, x]" --precision 80
python {baseDir}/scripts/eval_expression.py --expr "N[Pi, 80]" --precision 80 --json
```

## Safety boundary

- Use this skill for symbolic/numeric math only.
- By default, the script blocks expressions containing high-risk Wolfram symbols related to filesystem, network, or process execution (for example: `Import`, `URLRead`, `Run`, `RunProcess`, `Get`, `Put`, `OpenRead`, `OpenWrite`).
- Do not disable this guard unless the runtime is isolated (sandbox/container/VM).
- If you intentionally need unrestricted evaluation, pass `--allow-unsafe` and explicitly explain the risk.

## Workflow

1. Translate the user's math request into a Wolfram Language expression.
2. Ensure the expression is math-only (no filesystem/network/process operations).
3. Run `eval_expression.py` with `--expr`.
4. Return the script output as:
   - `Exact`
   - `Numeric`
   - `Verified`
   - `Version`
5. If `Verified` is `null`/not available, explain that the expression is non-numeric or not directly comparable.

## Inputs

- Required:
  - `--expr "<Wolfram Language expression>"`
- Optional:
  - `--precision <int>` default `50`
  - `--timeout <seconds>` default `30`
  - `--json` for machine-readable output
  - `--no-verify` to skip consistency verification
  - `--allow-unsafe` to bypass safety guard (use only in isolated environments)

## Output schema (`--json`)

- `expr`: original expression
- `exact`: exact/symbolic result (string)
- `numeric`: high-precision numeric result (string)
- `verified`: `true` / `false` / `null`
- `precision`: precision used
- `version`: Wolfram version string
- `warnings`: warning list

## Exit codes

- `0`: success
- `2`: invalid arguments (including empty expression)
- `3`: missing runtime dependency (`WolframKernel` or `wolframclient`)
- `4`: evaluation failure or timeout

## Examples

- Definite integral:
  - `Integrate[Sin[x]^2, {x, 0, Pi}]`
- Polynomial root solving:
  - `Solve[x^5 - x - 1 == 0, x]`
- Limit:
  - `Limit[(Sin[x] - x)/x^3, x -> 0]`
- High precision constant:
  - `N[Pi, 120]`

## Notes

- Input is Wolfram Language only.
- This v1 is single-expression, single-run (no REPL session reuse).
- Runtime dependency: Python package `wolframclient` is required.
