#!/usr/bin/env python3
"""
Generate a realistic fintech git repository workspace with multiple branches,
distractor files, and a mock openclaw/code-review-helper installation.
"""

import os
import subprocess
import stat
import textwrap
from pathlib import Path

WORKSPACE = Path("/workspace")
WORKSPACE.mkdir(parents=True, exist_ok=True)

# ── helper ──────────────────────────────────────────────────────────────────
def write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content))

def run(cmd, cwd=None):
    subprocess.run(cmd, shell=True, cwd=cwd or WORKSPACE, check=True)

# ════════════════════════════════════════════════════════════════════════════
# 1.  Set up the mock openclaw + code-review-helper skill
# ════════════════════════════════════════════════════════════════════════════

SKILL_DIR = WORKSPACE / ".openclaw" / "skills" / "code-review-helper"
SCRIPTS_DIR = SKILL_DIR / "scripts"
SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

# skill.json
write(SKILL_DIR / "skill.json", """\
{
  "name": "code-review-helper",
  "version": "1.0.0",
  "description": "Code review checklist generator",
  "entry": "scripts/review.sh",
  "config": {
    "check_security": true,
    "check_performance": true,
    "check_style": true,
    "check_tests": true,
    "severity_levels": ["critical", "warning", "info"],
    "output_format": "markdown"
  }
}
""")

# ── review.sh  (the mock core script) ───────────────────────────────────────
# This script faithfully implements the CLI surface described in SKILL.md.
# It produces deterministic outputs so the eval can check content.
review_sh = r"""#!/usr/bin/env bash
# code-review-helper/scripts/review.sh  -- mock implementation

set -euo pipefail

BASE="main"
HEAD="HEAD"
PR=""
FILES=""
SECURITY=false
PERFORMANCE=false
STYLE=false
TESTS=false
ALL=true
SEVERITY="info"
OUTPUT_FMT="markdown"
OUTPUT_FILE=""
TEMPLATE=false
TEMPLATE_STYLE="standard"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base)           BASE="$2";         shift 2 ;;
    --head)           HEAD="$2";         shift 2 ;;
    --pr)             PR="$2";           shift 2 ;;
    --files)          FILES="$2";        shift 2 ;;
    --security)       SECURITY=true; ALL=false; shift ;;
    --performance)    PERFORMANCE=true; ALL=false; shift ;;
    --style)          STYLE=true; ALL=false; shift ;;
    --tests)          TESTS=true; ALL=false; shift ;;
    --all)            ALL=true;          shift ;;
    --severity)       SEVERITY="$2";     shift 2 ;;
    --output)         OUTPUT_FMT="$2";   shift 2 ;;
    --output-file)    OUTPUT_FILE="$2";  shift 2 ;;
    --template)       TEMPLATE=true;     shift ;;
    --template-style) TEMPLATE_STYLE="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

# ── Template generation ──────────────────────────────────────────────────────
if [[ "$TEMPLATE" == "true" ]]; then
  case "$TEMPLATE_STYLE" in
    minimal)
      CONTENT="## Review\n\n- [ ] Changes look correct\n- [ ] No obvious security issues\n- [ ] Tests pass"
      ;;
    standard)
      CONTENT="## Review Summary\n\n**Reviewer**: ___\n**Date**: ___\n\n### Correctness\n- [ ] Logic is correct and handles edge cases\n- [ ] Error handling is appropriate\n\n### Security\n- [ ] No hardcoded secrets\n- [ ] Input is validated and sanitized\n\n### Performance\n- [ ] No obvious performance regressions\n- [ ] Database queries are optimized\n\n### Tests\n- [ ] New code has test coverage\n- [ ] Existing tests still pass\n\n### Notes\n_Additional comments here_"
      ;;
    thorough)
      CONTENT="## Review Summary\n\n**Reviewer**: ___\n**Date**: ___\n**PR**: ___\n\n### Correctness\n- [ ] Logic is correct and handles edge cases\n- [ ] Error handling is appropriate\n- [ ] No regressions introduced\n\n### Security\n- [ ] No hardcoded secrets\n- [ ] Input is validated and sanitized\n- [ ] Authentication and authorization checks in place\n- [ ] No injection vulnerabilities\n\n### Performance\n- [ ] No obvious performance regressions\n- [ ] Database queries are optimized\n- [ ] Caching strategy reviewed\n- [ ] Pagination implemented where needed\n\n### Tests\n- [ ] New code has test coverage\n- [ ] Existing tests still pass\n- [ ] Edge cases covered\n- [ ] Integration tests present\n\n### Architecture\n- [ ] Design is consistent with existing patterns\n- [ ] No unnecessary coupling introduced\n\n### Documentation\n- [ ] Public APIs are documented\n- [ ] Changelog updated if needed\n\n### Deployment\n- [ ] Migration scripts reviewed\n- [ ] Feature flags considered\n\n### Rollback\n- [ ] Rollback plan documented\n- [ ] No irreversible data changes without safeguards\n\n### Notes\n_Additional comments here_"
      ;;
    *)
      echo "Unknown template style: $TEMPLATE_STYLE" >&2
      exit 1
      ;;
  esac
  OUTPUT="$(printf '%b' "$CONTENT")"
  if [[ -n "$OUTPUT_FILE" ]]; then
    printf '%b\n' "$CONTENT" > "$OUTPUT_FILE"
  else
    printf '%b\n' "$CONTENT"
  fi
  exit 0
fi

# ── Determine which checks to run ────────────────────────────────────────────
if [[ "$ALL" == "true" ]]; then
  SECURITY=true; PERFORMANCE=true; STYLE=true; TESTS=true
fi

# ── Severity filter helper ────────────────────────────────────────────────────
# Returns 0 (include) or 1 (exclude) based on SEVERITY threshold
sev_ok() {
  local item_sev="$1"
  case "$SEVERITY" in
    critical)
      [[ "$item_sev" == "critical" ]]
      ;;
    warning)
      [[ "$item_sev" == "critical" || "$item_sev" == "warning" ]]
      ;;
    info|*)
      true
      ;;
  esac
}

# ── Collect findings ──────────────────────────────────────────────────────────
declare -a FINDINGS=()

if [[ "$SECURITY" == "true" ]]; then
  if sev_ok "critical"; then
    FINDINGS+=('{"id":"SEC-001","category":"security","severity":"critical","check":"Hardcoded secrets/tokens","file":"src/payment/processor.py","line":42,"detail":"Possible hardcoded API key detected"}')
    FINDINGS+=('{"id":"SEC-002","category":"security","severity":"critical","check":"SQL injection patterns","file":"src/payment/queries.py","line":17,"detail":"String formatting used in SQL query construction"}')
    FINDINGS+=('{"id":"SEC-003","category":"security","severity":"critical","check":"Command injection","file":"src/auth/utils.py","line":88,"detail":"os.system call with unsanitized input"}')
  fi
  if sev_ok "warning"; then
    FINDINGS+=('{"id":"SEC-004","category":"security","severity":"warning","check":"Missing input validation","file":"src/api/endpoints.py","line":55,"detail":"Request parameters used without validation"}')
    FINDINGS+=('{"id":"SEC-005","category":"security","severity":"warning","check":"HTTP instead of HTTPS","file":"src/services/webhook.py","line":23,"detail":"Insecure HTTP URL in webhook callback"}')
    FINDINGS+=('{"id":"SEC-006","category":"security","severity":"warning","check":"Eval/exec usage","file":"src/utils/helpers.py","line":101,"detail":"eval() call detected"}')
  fi
  if sev_ok "info"; then
    FINDINGS+=('{"id":"SEC-007","category":"security","severity":"info","check":"Missing CSRF protection","file":"src/api/endpoints.py","line":78,"detail":"CSRF middleware not confirmed for this endpoint"}')
    FINDINGS+=('{"id":"SEC-008","category":"security","severity":"info","check":"Verbose error messages","file":"src/api/endpoints.py","line":92,"detail":"Full stack trace returned in API error response"}')
  fi
fi

if [[ "$PERFORMANCE" == "true" ]]; then
  if sev_ok "critical"; then
    FINDINGS+=('{"id":"PERF-001","category":"performance","severity":"critical","check":"N+1 query patterns","file":"src/payment/processor.py","line":67,"detail":"Loop contains ORM query call"}')
  fi
  if sev_ok "warning"; then
    FINDINGS+=('{"id":"PERF-002","category":"performance","severity":"warning","check":"Missing database indexes","file":"migrations/0042_payment_index.sql","line":5,"detail":"No index on payment_status column"}')
    FINDINGS+=('{"id":"PERF-003","category":"performance","severity":"warning","check":"Missing pagination","file":"src/api/endpoints.py","line":110,"detail":"Endpoint returns unbounded result set"}')
  fi
  if sev_ok "info"; then
    FINDINGS+=('{"id":"PERF-004","category":"performance","severity":"info","check":"Unoptimized imports","file":"src/payment/processor.py","line":1,"detail":"Entire module imported when only one function used"}')
  fi
fi

if [[ "$STYLE" == "true" ]]; then
  if sev_ok "warning"; then
    FINDINGS+=('{"id":"STY-001","category":"style","severity":"warning","check":"Inconsistent naming","file":"src/auth/utils.py","line":34,"detail":"camelCase used alongside snake_case in same file"}')
    FINDINGS+=('{"id":"STY-002","category":"style","severity":"warning","check":"Mixed tabs and spaces","file":"src/payment/queries.py","line":29,"detail":"Tab character found in space-indented file"}')
  fi
  if sev_ok "info"; then
    FINDINGS+=('{"id":"STY-003","category":"style","severity":"info","check":"Import ordering","file":"src/payment/processor.py","line":3,"detail":"Standard library imports should precede third-party"}')
    FINDINGS+=('{"id":"STY-004","category":"style","severity":"info","check":"Missing docstrings","file":"src/auth/utils.py","line":45,"detail":"Public function missing docstring"}')
    FINDINGS+=('{"id":"STY-005","category":"style","severity":"info","check":"TODO/FIXME/HACK comments","file":"src/services/webhook.py","line":61,"detail":"TODO comment found: remove before merge"}')
  fi
fi

if [[ "$TESTS" == "true" ]]; then
  if sev_ok "warning"; then
    FINDINGS+=('{"id":"TST-001","category":"tests","severity":"warning","check":"No tests for new functions","file":"src/payment/processor.py","line":0,"detail":"process_refund() has no corresponding test"}')
    FINDINGS+=('{"id":"TST-002","category":"tests","severity":"warning","check":"Missing edge case tests","file":"tests/test_processor.py","line":0,"detail":"No test for zero-amount payment edge case"}')
  fi
  if sev_ok "info"; then
    FINDINGS+=('{"id":"TST-003","category":"tests","severity":"info","check":"Mocking external services","file":"tests/test_webhook.py","line":0,"detail":"External payment gateway not mocked in unit test"}')
    FINDINGS+=('{"id":"TST-004","category":"tests","severity":"info","check":"Test naming conventions","file":"tests/test_processor.py","line":0,"detail":"Test methods should follow test_<action>_<condition> pattern"}')
  fi
fi

# ── Apply file filter ─────────────────────────────────────────────────────────
if [[ -n "$FILES" ]]; then
  # Simple prefix/glob matching on file field
  FILTERED=()
  for f in "${FINDINGS[@]}"; do
    file_val="$(echo "$f" | grep -o '"file":"[^"]*"' | cut -d'"' -f4)"
    # Convert glob pattern to a simple prefix check (src/auth/**/*.py -> src/auth/)
    prefix="$(echo "$FILES" | sed 's/\*\*\/\*.*//' | sed 's/\*\/.*//')"
    if [[ "$file_val" == $prefix* ]]; then
      FILTERED+=("$f")
    fi
  done
  FINDINGS=("${FILTERED[@]+"${FILTERED[@]}"}")
fi

# ── Format output ─────────────────────────────────────────────────────────────
HAS_CRITICAL=false
for f in "${FINDINGS[@]}"; do
  sev="$(echo "$f" | grep -o '"severity":"[^"]*"' | cut -d'"' -f4)"
  [[ "$sev" == "critical" ]] && HAS_CRITICAL=true
done

generate_markdown() {
  echo "# Code Review Report"
  echo ""
  echo "**Base**: $BASE  **Head**: $HEAD"
  echo ""
  echo "## Summary"
  echo ""
  echo "| Severity | Count |"
  echo "|----------|-------|"
  local crit=0 warn=0 info=0
  for f in "${FINDINGS[@]}"; do
    sev="$(echo "$f" | grep -o '"severity":"[^"]*"' | cut -d'"' -f4)"
    case "$sev" in
      critical) ((crit++)) ;;
      warning)  ((warn++)) ;;
      info)     ((info++)) ;;
    esac
  done
  echo "| Critical | $crit |"
  echo "| Warning  | $warn |"
  echo "| Info     | $info |"
  echo ""
  echo "## Findings"
  echo ""
  for f in "${FINDINGS[@]}"; do
    id="$(echo "$f"    | grep -o '"id":"[^"]*"'       | cut -d'"' -f4)"
    sev="$(echo "$f"   | grep -o '"severity":"[^"]*"' | cut -d'"' -f4)"
    check="$(echo "$f" | grep -o '"check":"[^"]*"'    | cut -d'"' -f4)"
    file="$(echo "$f"  | grep -o '"file":"[^"]*"'     | cut -d'"' -f4)"
    line="$(echo "$f"  | grep -o '"line":[0-9]*'      | cut -d':' -f2)"
    detail="$(echo "$f"| grep -o '"detail":"[^"]*"'   | cut -d'"' -f4)"
    echo "### [$id] $check"
    echo "- **Severity**: $sev"
    echo "- **File**: \`$file\` (line $line)"
    echo "- **Detail**: $detail"
    echo ""
  done
}

generate_json() {
  echo "{"
  echo '  "base": "'"$BASE"'",'
  echo '  "head": "'"$HEAD"'",'
  echo '  "findings": ['
  local count=${#FINDINGS[@]}
  local i=0
  for f in "${FINDINGS[@]}"; do
    i=$((i+1))
    if [[ $i -lt $count ]]; then
      echo "    $f,"
    else
      echo "    $f"
    fi
  done
  echo "  ]"
  echo "}"
}

generate_text() {
  echo "Code Review Report -- Base: $BASE  Head: $HEAD"
  echo "======================================================"
  for f in "${FINDINGS[@]}"; do
    id="$(echo "$f"    | grep -o '"id":"[^"]*"'       | cut -d'"' -f4)"
    sev="$(echo "$f"   | grep -o '"severity":"[^"]*"' | cut -d'"' -f4)"
    check="$(echo "$f" | grep -o '"check":"[^"]*"'    | cut -d'"' -f4)"
    file="$(echo "$f"  | grep -o '"file":"[^"]*"'     | cut -d'"' -f4)"
    detail="$(echo "$f"| grep -o '"detail":"[^"]*"'   | cut -d'"' -f4)"
    echo "[$sev] $id: $check -- $file -- $detail"
  done
}

case "$OUTPUT_FMT" in
  json)     RESULT="$(generate_json)"  ;;
  text)     RESULT="$(generate_text)"  ;;
  markdown) RESULT="$(generate_markdown)" ;;
  *)        echo "Unknown format: $OUTPUT_FMT" >&2; exit 1 ;;
esac

if [[ -n "$OUTPUT_FILE" ]]; then
  echo "$RESULT" > "$OUTPUT_FILE"
else
  echo "$RESULT"
fi

# Exit 1 if critical findings found (CI/CD contract from SKILL.md)
if [[ "$HAS_CRITICAL" == "true" ]]; then
  exit 1
fi
exit 0
"""

write(SCRIPTS_DIR / "review.sh", review_sh)
(SCRIPTS_DIR / "review.sh").chmod(0o755)

# ── openclaw wrapper ──────────────────────────────────────────────────────────
openclaw_bin = WORKSPACE / ".openclaw" / "bin" / "openclaw"
openclaw_bin.parent.mkdir(parents=True, exist_ok=True)

openclaw_sh = r"""#!/usr/bin/env bash
# openclaw CLI wrapper

SKILLS_DIR="$(dirname "$(dirname "$(realpath "$0")")")/skills"

CMD="${1:-}"
shift || true

case "$CMD" in
  install)
    echo "Installing skill: $1"
    ;;
  list)
    if [[ "${1:-}" == "--installed" ]]; then
      ls "$SKILLS_DIR/"
    fi
    ;;
  run)
    SKILL="$1"; shift
    SCRIPT="$SKILLS_DIR/$SKILL/scripts/review.sh"
    if [[ ! -f "$SCRIPT" ]]; then
      echo "Skill not found: $SKILL" >&2; exit 1
    fi
    exec bash "$SCRIPT" "$@"
    ;;
  *)
    echo "Usage: openclaw <install|list|run> [args]" >&2
    exit 1
    ;;
esac
"""

write(openclaw_bin, openclaw_sh)
openclaw_bin.chmod(0o755)

# ════════════════════════════════════════════════════════════════════════════
# 2.  Build the fintech git repository
# ════════════════════════════════════════════════════════════════════════════

REPO = WORKSPACE / "fintech-platform"
REPO.mkdir(parents=True, exist_ok=True)

run("git init", cwd=REPO)
run("git checkout -b develop", cwd=REPO)

# ── base files on develop ────────────────────────────────────────────────────
write(REPO / "README.md", """\
# FinTech Platform
Core payment processing platform.
""")

write(REPO / "src/__init__.py", "")
write(REPO / "src/payment/__init__.py", "")
write(REPO / "src/auth/__init__.py", "")
write(REPO / "src/api/__init__.py", "")
write(REPO / "src/services/__init__.py", "")
write(REPO / "src/utils/__init__.py", "")

write(REPO / "src/payment/processor.py", """\
\"\"\"Payment processor module.\"\"\"
import requests

def process_payment(amount, card_token):
    return {"status": "ok"}
""")

write(REPO / "src/auth/utils.py", """\
\"\"\"Auth utilities.\"\"\"

def verify_token(token):
    return True
""")

write(REPO / "src/api/endpoints.py", """\
\"\"\"API endpoints.\"\"\"

def get_payments():
    return []
""")

write(REPO / "migrations/0041_baseline.sql", """\
-- baseline migration
CREATE TABLE payments (id SERIAL PRIMARY KEY, amount DECIMAL);
""")

write(REPO / "tests/__init__.py", "")
write(REPO / "tests/test_processor.py", """\
def test_process_payment():
    assert True
""")

write(REPO / "requirements.txt", "requests==2.31.0\n")
write(REPO / "setup.py", "from setuptools import setup; setup(name='fintech')\n")
write(REPO / "Makefile", "test:\n\tpytest tests/\n")
write(REPO / ".gitignore", "__pycache__/\n*.pyc\n.env\n")
write(REPO / "docs/architecture.md", "# Architecture\nSee diagrams folder.\n")
write(REPO / "docs/api.md", "# API Reference\nREST endpoints documented here.\n")
write(REPO / "config/settings.py", "DEBUG = False\nDATABASE_URL = 'postgresql://localhost/fintech'\n")
write(REPO / "config/logging.yaml", "version: 1\nhandlers:\n  console:\n    class: logging.StreamHandler\n")
write(REPO / "scripts/deploy.sh", "#!/bin/bash\necho 'deploying'\n")
write(REPO / "scripts/migrate.sh", "#!/bin/bash\necho 'migrating'\n")

run("git add .", cwd=REPO)
run('git commit -m "Initial commit: base platform"', cwd=REPO)

# ── feature branch with new payment-service changes ──────────────────────────
run("git checkout -b feature/payment-service", cwd=REPO)

write(REPO / "src/payment/processor.py", """\
import os
import requests
from payment import queries

API_KEY = "sk_live_4xG9mN2pQr7vK8jL3wT0uZ"   # hardcoded secret

def process_payment(amount, card_token):
    result = queries.get_pending(card_token)
    for r in result:
        detail = queries.get_detail(r['id'])   # N+1 query
    return {"status": "ok"}

def process_refund(payment_id, amount):
    cmd = "refund_tool --id=" + payment_id
    os.system(cmd)   # command injection
    return True
""")

write(REPO / "src/payment/queries.py", """\
import psycopg2

def get_pending(card_token):
    conn = psycopg2.connect("dbname=fintech")
    cur = conn.cursor()
    cur.execute("SELECT * FROM payments WHERE token = '%s'" % card_token)  # SQL injection
    return cur.fetchall()

def get_detail(payment_id):
    conn = psycopg2.connect("dbname=fintech")
    cur = conn.cursor()
    cur.execute("SELECT * FROM payments WHERE id = %d" % payment_id)
    return cur.fetchone()
""")

write(REPO / "src/auth/utils.py", """\
import os
import hashlib

secretKey = "hardcoded_jwt_secret_1234"   # another hardcoded secret
camelCaseVar = "bad naming"

def verify_token(token):
    return True

def execute_command(user_input):
    os.system(user_input)   # command injection

def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()   # weak crypto
""")

write(REPO / "src/api/endpoints.py", """\
from flask import request, jsonify

def get_payments():
    user_id = request.args.get('user_id')   # no validation
    # TODO: add rate limiting
    payments = db.query("SELECT * FROM payments WHERE user_id=" + user_id)
    return jsonify(payments)   # unbounded result set
""")

write(REPO / "src/services/webhook.py", """\
import requests

CALLBACK_URL = "http://external-payment-gateway.com/webhook"   # HTTP not HTTPS

def send_webhook(payload):
    # TODO: add retry logic
    resp = requests.post(CALLBACK_URL, json=payload)
    return resp.status_code
""")

write(REPO / "src/utils/helpers.py", """\
def dynamic_eval(expr):
    return eval(expr)   # dangerous eval

def compute(data):
    result = ""
    for item in data:
        result = result + str(item)   # string concat in loop
    return result
""")

write(REPO / "migrations/0042_payment_index.sql", """\
-- Add payment service tables
CREATE TABLE payment_methods (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    payment_status VARCHAR(50)
);
-- Missing index on payment_status
""")

write(REPO / "tests/test_processor.py", """\
def test_process_payment():
    assert True

# process_refund is not tested
""")

write(REPO / "tests/test_webhook.py", """\
import requests

def test_send_webhook():
    # calls real external service, not mocked
    result = send_webhook({"amount": 100})
    assert result == 200
""")

run("git add .", cwd=REPO)
run('git commit -m "feat: add payment service with refund, webhook, auth improvements"', cwd=REPO)

# ════════════════════════════════════════════════════════════════════════════
# 3.  Distractor files and directories
# ════════════════════════════════════════════════════════════════════════════

write(WORKSPACE / "old-reviews" / "review_2024_q1.txt", "Old review notes from Q1 2024.\n")
write(WORKSPACE / "old-reviews" / "review_2024_q2.md", "## Q2 Review\nSome notes.\n")
write(WORKSPACE / "ci-configs" / "github-actions.yml", "name: CI\non: push\njobs:\n  test:\n    runs-on: ubuntu-latest\n")
write(WORKSPACE / "ci-configs" / "jenkins.groovy", "pipeline { agent any; stages { stage('test') { steps { sh 'pytest' } } } }\n")
write(WORKSPACE / "templates" / "pr_old_template.md", "## Old Template\n- [ ] Reviewed\n")
write(WORKSPACE / "notes" / "team_process.txt", "Our review process requires security + performance checks.\n")
write(WORKSPACE / "notes" / "onboarding.md", "# Onboarding\nWelcome to the team.\n")
write(WORKSPACE / "scratch" / "experiment.py", "# scratch file\nprint('hello')\n")
write(WORKSPACE / "scratch" / "test_ideas.txt", "Ideas for future tests.\n")
write(WORKSPACE / "archive" / "legacy_review.json", '{"legacy": true, "findings": []}\n')

print("Workspace generation complete.")
print(f"Repository: {REPO}")
print(f"Openclaw: {openclaw_bin}")