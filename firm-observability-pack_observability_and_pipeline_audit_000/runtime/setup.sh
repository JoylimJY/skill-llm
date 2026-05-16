#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${WORKSPACE:-/workspace}"
OPENCLAW_BIN="/usr/local/bin"

mkdir -p "$OPENCLAW_BIN"

# ── Mock: openclaw_observability_pipeline ────────────────────────────────────
cat > "$OPENCLAW_BIN/openclaw_observability_pipeline" << 'MOCK_OBS'
#!/usr/bin/env python3
"""
Mock implementation of openclaw_observability_pipeline
Parses: traces_path=/path/to/file.jsonl  [db_path=/path/to/output.db]
Ingests JSONL traces into SQLite, skipping malformed lines.
"""
import sys, os, json, sqlite3, re
from pathlib import Path

args = {}
for a in sys.argv[1:]:
    if "=" in a:
        k, v = a.split("=", 1)
        args[k.strip()] = v.strip()

if "traces_path" not in args:
    print("ERROR: traces_path parameter is required", file=sys.stderr)
    sys.exit(1)

traces_path = args["traces_path"]
db_path = args.get("db_path", str(Path(traces_path).parent / "traces.db"))

if not os.path.exists(traces_path):
    print(f"ERROR: traces_path not found: {traces_path}", file=sys.stderr)
    sys.exit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("""
    CREATE TABLE IF NOT EXISTS traces (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trace_id TEXT,
        span_id TEXT,
        service TEXT,
        operation TEXT,
        duration_ms REAL,
        status TEXT,
        timestamp TEXT,
        raw_json TEXT
    )
""")
cur.execute("""
    CREATE TABLE IF NOT EXISTS ingest_meta (
        key TEXT PRIMARY KEY,
        value TEXT
    )
""")
conn.commit()

ingested = 0
skipped = 0
with open(traces_path) as f:
    for lineno, line in enumerate(f, 1):
        line = line.strip()
        if not line:
            skipped += 1
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            skipped += 1
            continue
        # Validate required fields
        required = ["trace_id", "service", "operation", "status", "timestamp"]
        if not all(k in obj for k in required):
            skipped += 1
            continue
        # Coerce duration_ms — if not numeric, store as NULL
        dur = obj.get("duration_ms")
        try:
            dur = float(dur)
        except (TypeError, ValueError):
            dur = None
        cur.execute("""
            INSERT INTO traces (trace_id, span_id, service, operation, duration_ms, status, timestamp, raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            obj.get("trace_id"),
            obj.get("span_id"),
            obj.get("service"),
            obj.get("operation"),
            dur,
            obj.get("status"),
            obj.get("timestamp"),
            line,
        ))
        ingested += 1

# Store ingest metadata
cur.execute("INSERT OR REPLACE INTO ingest_meta VALUES ('ingested_count', ?)", (str(ingested),))
cur.execute("INSERT OR REPLACE INTO ingest_meta VALUES ('skipped_count', ?)", (str(skipped),))
cur.execute("INSERT OR REPLACE INTO ingest_meta VALUES ('source_file', ?)", (traces_path,))
conn.commit()
conn.close()

print(f"openclaw_observability_pipeline: ingested={ingested} skipped={skipped} db={db_path}")
MOCK_OBS
chmod +x "$OPENCLAW_BIN/openclaw_observability_pipeline"

# ── Mock: openclaw_ci_pipeline_check ─────────────────────────────────────────
cat > "$OPENCLAW_BIN/openclaw_ci_pipeline_check" << 'MOCK_CI'
#!/usr/bin/env python3
"""
Mock implementation of openclaw_ci_pipeline_check
Parses: config_path=/path/to/config.json  [report_path=/path/to/report.json]
Validates CI pipeline for security gates and test steps.
"""
import sys, os, json
from pathlib import Path

args = {}
for a in sys.argv[1:]:
    if "=" in a:
        k, v = a.split("=", 1)
        args[k.strip()] = v.strip()

if "config_path" not in args:
    print("ERROR: config_path parameter is required", file=sys.stderr)
    sys.exit(1)

config_path = args["config_path"]
report_path = args.get("report_path", str(Path(config_path).parent / "ci_validation_report.json"))

if not os.path.exists(config_path):
    print(f"ERROR: config_path not found: {config_path}", file=sys.stderr)
    sys.exit(1)

with open(config_path) as f:
    config = json.load(f)

violations = []
warnings = []
passed_checks = []

# Check 1: Must have a security scan step somewhere
all_step_types = []
for stage in config.get("stages", []):
    for step in stage.get("steps", []):
        all_step_types.append(step.get("type", ""))

security_types = {"sast_scan", "dast_scan", "security_scan", "dependency_check", "vulnerability_scan"}
has_security = any(t in security_types for t in all_step_types)
if not has_security:
    violations.append({
        "rule": "SECURITY_GATE_REQUIRED",
        "severity": "CRITICAL",
        "message": "Pipeline must include at least one security scan step (sast_scan, dast_scan, security_scan, dependency_check, or vulnerability_scan)"
    })
else:
    passed_checks.append("SECURITY_GATE_REQUIRED")

# Check 2: Must have integration tests
has_integration = any(
    step.get("type") == "test_runner" and "integration" in step.get("name", "").lower()
    for stage in config.get("stages", [])
    for step in stage.get("steps", [])
)
if not has_integration:
    violations.append({
        "rule": "INTEGRATION_TEST_REQUIRED",
        "severity": "HIGH",
        "message": "Pipeline must include an integration test step"
    })
else:
    passed_checks.append("INTEGRATION_TEST_REQUIRED")

# Check 3: Coverage threshold must be >= 80%
for stage in config.get("stages", []):
    for step in stage.get("steps", []):
        if step.get("type") == "test_runner":
            cov = step.get("coverage_threshold", 0)
            if cov < 80:
                violations.append({
                    "rule": "COVERAGE_THRESHOLD",
                    "severity": "HIGH",
                    "message": f"Test step '{step.get('name')}' has coverage_threshold={cov}, minimum is 80"
                })
            else:
                passed_checks.append("COVERAGE_THRESHOLD")

# Check 4: Deploy stage must have an approval gate before production
for stage in config.get("stages", []):
    if "deploy" in stage.get("name", "").lower():
        stage_types = [s.get("type") for s in stage.get("steps", [])]
        if "approval_gate" not in stage_types and "manual_approval" not in stage_types:
            violations.append({
                "rule": "APPROVAL_GATE_REQUIRED",
                "severity": "CRITICAL",
                "message": f"Deploy stage '{stage['name']}' must have an approval_gate or manual_approval step before production deployment"
            })
        else:
            passed_checks.append("APPROVAL_GATE_REQUIRED")

# Check 5: Notifications must be enabled on failure
notif = config.get("notifications", {})
if not notif.get("on_failure", False):
    warnings.append({
        "rule": "NOTIFICATION_ON_FAILURE",
        "severity": "MEDIUM",
        "message": "Notifications on failure should be enabled"
    })
else:
    passed_checks.append("NOTIFICATION_ON_FAILURE")

status = "FAIL" if violations else "PASS"

report = {
    "pipeline_name": config.get("pipeline_name", "unknown"),
    "validation_status": status,
    "violations": violations,
    "warnings": warnings,
    "passed_checks": passed_checks,
    "summary": {
        "total_violations": len(violations),
        "critical": sum(1 for v in violations if v["severity"] == "CRITICAL"),
        "high": sum(1 for v in violations if v["severity"] == "HIGH"),
        "warnings": len(warnings),
    }
}

with open(report_path, "w") as f:
    json.dump(report, f, indent=2)

print(f"openclaw_ci_pipeline_check: status={status} violations={len(violations)} warnings={len(warnings)} report={report_path}")
for v in violations:
    print(f"  [{v['severity']}] {v['rule']}: {v['message']}")
MOCK_CI
chmod +x "$OPENCLAW_BIN/openclaw_ci_pipeline_check"

echo "[setup] Mock tools installed at $OPENCLAW_BIN"
echo "[setup] openclaw_observability_pipeline: $(which openclaw_observability_pipeline 2>/dev/null || echo NOT IN PATH)"
echo "[setup] openclaw_ci_pipeline_check: $(which openclaw_ci_pipeline_check 2>/dev/null || echo NOT IN PATH)"

# Ensure workspace exists
mkdir -p "${WORKSPACE:-/workspace}"