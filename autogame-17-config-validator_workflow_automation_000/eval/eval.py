import sys
import json
import os
import subprocess
from pathlib import Path

workspace = sys.argv[1]

checks = []
passed_all = True

def record(name: str, passed: bool, detail: str):
    global passed_all
    checks.append({"name": name, "passed": passed, "detail": detail})
    if not passed:
        passed_all = False

# ── Run the validator and capture output ──────────────────────────────────────
try:
    result = subprocess.run(
        ["node", "skills/config-validator/index.js"],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=30
    )
    stdout = result.stdout.strip()
    exit_code = result.returncode

    try:
        report = json.loads(stdout)
        validator_ran = True
    except Exception as e:
        report = None
        validator_ran = False
        record("validator produces valid JSON output", False, f"stdout not parseable JSON: {e}\nstdout={stdout[:500]}")

except Exception as e:
    report = None
    validator_ran = False
    exit_code = -1
    record("validator runs without crash", False, str(e))

if validator_ran:
    record("validator produces valid JSON output", True, f"exit_code={exit_code}")

    # All checks must pass → exit code 0
    summary = report.get("summary", {})
    total_failed = summary.get("failed", -1)
    record(
        "validator reports zero failures (exit code 0)",
        exit_code == 0 and total_failed == 0,
        f"summary={summary}"
    )

# ── Independent file-level checks ────────────────────────────────────────────

# 1. .env file checks
env_path = Path(workspace) / ".env"
try:
    env_text = env_path.read_text()
    env_vars = {}
    for line in env_text.splitlines():
        m = __import__("re").match(r'^\s*([A-Z_][A-Z0-9_]*)\s*=\s*(.*)$', line)
        if m:
            env_vars[m.group(1)] = m.group(2).strip()

    # OPENCLAW_API_KEY must be present and non-placeholder
    val = env_vars.get("OPENCLAW_API_KEY", "")
    record(".env: OPENCLAW_API_KEY has real value",
           bool(val) and val not in ("", "PLACEHOLDER"),
           f"value='{val}'")

    # OPENCLAW_ENV must be one of the allowed values
    val = env_vars.get("OPENCLAW_ENV", "")
    record(".env: OPENCLAW_ENV is valid (development|staging|production)",
           val in ("development", "staging", "production"),
           f"value='{val}'")

    # OPENCLAW_LOG_LEVEL must be one of the allowed values
    val = env_vars.get("OPENCLAW_LOG_LEVEL", "")
    record(".env: OPENCLAW_LOG_LEVEL is valid (debug|info|warn|error)",
           val in ("debug", "info", "warn", "error"),
           f"value='{val}'")

    # OPENCLAW_DB_URI must be present and non-empty/non-placeholder
    val = env_vars.get("OPENCLAW_DB_URI", "")
    record(".env: OPENCLAW_DB_URI is present with real value",
           bool(val) and val not in ("", "PLACEHOLDER"),
           f"value='{val}'")

except Exception as e:
    record(".env: readable", False, str(e))

# 2. openclaw.json checks
oc_path = Path(workspace) / "openclaw.json"
try:
    cfg = json.loads(oc_path.read_text())

    import re
    # version must be semver string
    ver = cfg.get("version", None)
    record("openclaw.json: version is semver string",
           isinstance(ver, str) and bool(re.match(r'^\d+\.\d+\.\d+$', ver)),
           f"version={json.dumps(ver)}")

    # service.port must be an integer 1-65535
    port = cfg.get("service", {}).get("port", None)
    record("openclaw.json: service.port is valid integer",
           isinstance(port, int) and not isinstance(port, bool) and 1 <= port <= 65535,
           f"port={json.dumps(port)}")

    # service.healthEndpoint must start with /
    ep = cfg.get("service", {}).get("healthEndpoint", "")
    record("openclaw.json: service.healthEndpoint starts with /",
           isinstance(ep, str) and ep.startswith("/"),
           f"healthEndpoint={json.dumps(ep)}")

    # retryPolicy.maxRetries must be non-negative
    mr = cfg.get("retryPolicy", {}).get("maxRetries", None)
    record("openclaw.json: retryPolicy.maxRetries is non-negative",
           isinstance(mr, (int, float)) and not isinstance(mr, bool) and mr >= 0,
           f"maxRetries={json.dumps(mr)}")

    # auth.provider must be jwt|oauth2|apikey
    prov = cfg.get("auth", {}).get("provider", "")
    record("openclaw.json: auth.provider is valid (jwt|oauth2|apikey)",
           prov in ("jwt", "oauth2", "apikey"),
           f"provider={json.dumps(prov)}")

except Exception as e:
    record("openclaw.json: readable and parseable", False, str(e))

# 3. package.json dependencies are installed
pkg_path = Path(workspace) / "package.json"
nm_path = Path(workspace) / "node_modules"
try:
    pkg = json.loads(pkg_path.read_text())
    deps = list((pkg.get("dependencies") or {}).keys())
    for dep in deps:
        installed = (nm_path / dep).exists()
        record(f"package.json dep installed in node_modules: {dep}",
               installed,
               f"node_modules/{dep} exists: {installed}")
except Exception as e:
    record("package.json: deps check", False, str(e))

# ── Score ─────────────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4) if total > 0 else 0.0
final_passed = passed_count == total

print(json.dumps({
    "passed": final_passed,
    "score": score,
    "checks": checks
}, indent=2))