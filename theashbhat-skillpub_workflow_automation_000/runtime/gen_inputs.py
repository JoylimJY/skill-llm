import os
import stat
import random
import textwrap
from pathlib import Path

random.seed(42)

WORKSPACE = os.environ.get("WORKSPACE", "/workspace")

# ── Helper ─────────────────────────────────────────────────────────────────────
def mkdir(p):
    Path(p).mkdir(parents=True, exist_ok=True)

def write(p, content):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(textwrap.dedent(content))

# ── 1.  Skill-publisher toolchain (the "baseDir") ──────────────────────────────
base = f"{WORKSPACE}/skill-publisher"
mkdir(f"{base}/scripts")

# scaffold.sh  ─ creates skill folder + SKILL.md template + scripts/ dir
write(f"{base}/scripts/scaffold.sh", """\
#!/usr/bin/env bash
set -euo pipefail
SKILL_NAME="${1:?Usage: scaffold.sh <skill-name> [--dir <output-dir>]}"
OUTPUT_DIR="./skills"
shift
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dir) OUTPUT_DIR="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done
DEST="${OUTPUT_DIR}/${SKILL_NAME}"
if [[ -d "$DEST" ]]; then
  echo "ERROR: Directory '$DEST' already exists." >&2
  exit 1
fi
mkdir -p "${DEST}/scripts"
cat > "${DEST}/SKILL.md" <<'TMPL'
---
name: SKILL_NAME_PLACEHOLDER
description: >
  DESCRIPTION_PLACEHOLDER
---

# SKILL_NAME_PLACEHOLDER

Write your skill instructions here.
TMPL
sed -i "s/SKILL_NAME_PLACEHOLDER/${SKILL_NAME}/g" "${DEST}/SKILL.md"
echo "Scaffolded skill at ${DEST}"
""")

# validate.sh  ─ checks naming, required files, frontmatter, forbidden files
write(f"{base}/scripts/validate.sh", """\
#!/usr/bin/env bash
set -euo pipefail
SKILL_FOLDER="${1:?Usage: validate.sh <skill-folder>}"
ERRORS=0

# 1. Required files
if [[ ! -f "${SKILL_FOLDER}/SKILL.md" ]]; then
  echo "FAIL: SKILL.md is missing" >&2
  ERRORS=$((ERRORS+1))
fi

# 2. Naming convention: basename must be lowercase letters and hyphens only
BASENAME=$(basename "$SKILL_FOLDER")
if ! echo "$BASENAME" | grep -qE '^[a-z][a-z0-9-]*$'; then
  echo "FAIL: Skill folder name '${BASENAME}' violates naming convention (lowercase, hyphens only)" >&2
  ERRORS=$((ERRORS+1))
fi

# 3. Frontmatter: must contain 'name' and 'description'
if ! grep -q '^name:' "${SKILL_FOLDER}/SKILL.md"; then
  echo "FAIL: SKILL.md frontmatter missing 'name'" >&2
  ERRORS=$((ERRORS+1))
fi
if ! grep -q '^description:' "${SKILL_FOLDER}/SKILL.md"; then
  echo "FAIL: SKILL.md frontmatter missing 'description'" >&2
  ERRORS=$((ERRORS+1))
fi

# 4. Forbidden files
FORBIDDEN=(README.md CHANGELOG.md LICENCE LICENSE CONTRIBUTING.md TODO.md)
for f in "${FORBIDDEN[@]}"; do
  if find "$SKILL_FOLDER" -maxdepth 2 -name "$f" | grep -q .; then
    echo "FAIL: Forbidden file '${f}' found in skill folder" >&2
    ERRORS=$((ERRORS+1))
  fi
done

# 5. Description must not be the placeholder
if grep -q 'DESCRIPTION_PLACEHOLDER' "${SKILL_FOLDER}/SKILL.md"; then
  echo "FAIL: SKILL.md description is still the scaffold placeholder" >&2
  ERRORS=$((ERRORS+1))
fi

if [[ $ERRORS -eq 0 ]]; then
  echo "OK: Validation passed for ${SKILL_FOLDER}"
  exit 0
else
  echo "FAIL: ${ERRORS} validation error(s) found" >&2
  exit 1
fi
""")

# security-scan.sh  ─ checks for RCE/exfiltration/env-harvesting/prompt-injection
write(f"{base}/scripts/security-scan.sh", """\
#!/usr/bin/env bash
set -euo pipefail
SKILL_FOLDER="${1:?Usage: security-scan.sh <skill-folder>}"
ISSUES=0

echo "Running security scan on ${SKILL_FOLDER}..."

# Pattern: eval / exec with dynamic input
if grep -rE '\\beval\\b.*\\$|exec\\(.*input' "${SKILL_FOLDER}" 2>/dev/null | grep -v '.md:' | grep -q .; then
  echo "WARN: Potential remote code execution pattern detected" >&2
  ISSUES=$((ISSUES+1))
fi

# Pattern: curl to non-localhost
if grep -rE 'curl[[:space:]].*https?://(?!localhost|127)' "${SKILL_FOLDER}" 2>/dev/null | grep -q .; then
  echo "WARN: Potential data exfiltration via curl" >&2
  ISSUES=$((ISSUES+1))
fi

# Pattern: env variable harvesting
if grep -rE 'printenv|env\\b.*>|\\$\\(env\\)' "${SKILL_FOLDER}" 2>/dev/null | grep -v 'security-scan' | grep -q .; then
  echo "WARN: Environment variable harvesting detected" >&2
  ISSUES=$((ISSUES+1))
fi

# Pattern: prompt injection markers in markdown
if grep -rE 'IGNORE PREVIOUS INSTRUCTIONS|ignore all prior' "${SKILL_FOLDER}" 2>/dev/null | grep -iq .; then
  echo "WARN: Prompt injection marker detected in markdown" >&2
  ISSUES=$((ISSUES+1))
fi

# Suspicious file permissions: world-writable scripts
while IFS= read -r -d '' file; do
  PERMS=$(stat -c "%a" "$file")
  if [[ "${PERMS: -1}" -ge 2 ]]; then
    echo "WARN: World-writable file detected: ${file}" >&2
    ISSUES=$((ISSUES+1))
  fi
done < <(find "${SKILL_FOLDER}" -type f -print0)

if [[ $ISSUES -eq 0 ]]; then
  echo "OK: Security scan passed for ${SKILL_FOLDER}"
  exit 0
else
  echo "WARN: ${ISSUES} security issue(s) found — review before publishing" >&2
  exit 2
fi
""")

# publish.sh  ─ requires --slug and --version; calls clawhub CLI
write(f"{base}/scripts/publish.sh", """\
#!/usr/bin/env bash
set -euo pipefail
SKILL_FOLDER="${1:?Usage: publish.sh <skill-folder> --slug <name> --version <x.y.z>}"
SLUG=""
VERSION=""
shift
while [[ $# -gt 0 ]]; do
  case "$1" in
    --slug)    SLUG="$2";    shift 2 ;;
    --version) VERSION="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done
if [[ -z "$SLUG" || -z "$VERSION" ]]; then
  echo "ERROR: --slug and --version are both required" >&2
  exit 1
fi
if ! echo "$VERSION" | grep -qE '^[0-9]+\\.[0-9]+\\.[0-9]+$'; then
  echo "ERROR: version must follow semver x.y.z" >&2
  exit 1
fi

# Check login token
TOKEN_FILE="${HOME}/.clawhub/token"
if [[ ! -f "$TOKEN_FILE" ]]; then
  echo "ERROR: Not logged in. Run 'clawhub login' first." >&2
  exit 1
fi
TOKEN=$(cat "$TOKEN_FILE")

CLAWHUB_URL="${CLAWHUB_URL:-http://localhost:7474}"
TMPARCHIVE=$(mktemp /tmp/skill-XXXXXX.tar.gz)
tar -czf "$TMPARCHIVE" -C "$(dirname "$SKILL_FOLDER")" "$(basename "$SKILL_FOLDER")"

RESPONSE=$(curl -sf -X POST "${CLAWHUB_URL}/api/publish" \\
  -H "Authorization: Bearer ${TOKEN}" \\
  -F "slug=${SLUG}" \\
  -F "version=${VERSION}" \\
  -F "archive=@${TMPARCHIVE}" 2>&1) || {
    echo "ERROR: Publish request failed: $RESPONSE" >&2
    rm -f "$TMPARCHIVE"
    exit 1
  }
rm -f "$TMPARCHIVE"
echo "Published: $RESPONSE"
""")

# clawhub CLI (login command)
write(f"{base}/scripts/clawhub", """\
#!/usr/bin/env bash
set -euo pipefail
COMMAND="${1:-}"
CLAWHUB_URL="${CLAWHUB_URL:-http://localhost:7474}"
case "$COMMAND" in
  login)
    RESPONSE=$(curl -sf -X POST "${CLAWHUB_URL}/api/login" -H "Content-Type: application/json" -d '{"user":"ci-agent","pass":"benchmark"}')
    TOKEN=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
    mkdir -p "${HOME}/.clawhub"
    echo "$TOKEN" > "${HOME}/.clawhub/token"
    echo "Logged in to ClawHub."
    ;;
  *)
    echo "Unknown clawhub command: $COMMAND" >&2
    exit 1
    ;;
esac
""")

# ── 2. Distractor files: a messy fintech project ───────────────────────────────
dirs = [
    "fintech-platform/src/normalizer",
    "fintech-platform/src/ingestion",
    "fintech-platform/src/reporting",
    "fintech-platform/tests/unit",
    "fintech-platform/tests/integration",
    "fintech-platform/config",
    "fintech-platform/deploy/k8s",
    "fintech-platform/deploy/helm",
    "fintech-platform/docs/internal",
    "fintech-platform/scripts",
]
for d in dirs:
    mkdir(f"{WORKSPACE}/{d}")

# Core normalizer source (this is the logic the skill should wrap)
write(f"{WORKSPACE}/fintech-platform/src/normalizer/csv_normalizer.py", """\
\"\"\"Normalize raw transaction CSV files to a canonical schema.\"\"\"
import csv, sys, re
from datetime import datetime

CANONICAL_HEADERS = ["txn_id", "amount_usd", "currency", "timestamp_utc", "merchant"]

def normalize_row(row):
    # Strip whitespace from all values
    row = {k.strip(): v.strip() for k, v in row.items()}
    # Convert amount to float with 2 decimals
    amount_raw = row.get("amount") or row.get("amount_usd") or "0"
    amount_raw = re.sub(r"[^0-9.]", "", amount_raw)
    row["amount_usd"] = f"{float(amount_raw):.2f}"
    # Normalize timestamp
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%m/%d/%Y %H:%M", "%Y-%m-%d"):
        try:
            row["timestamp_utc"] = datetime.strptime(row.get("timestamp",""), fmt).strftime("%Y-%m-%dT%H:%M:%SZ")
            break
        except ValueError:
            pass
    return row

if __name__ == "__main__":
    reader = csv.DictReader(sys.stdin)
    writer = csv.DictWriter(sys.stdout, fieldnames=CANONICAL_HEADERS, extrasaction="ignore")
    writer.writeheader()
    for r in reader:
        writer.writerow(normalize_row(r))
""")

write(f"{WORKSPACE}/fintech-platform/src/normalizer/__init__.py", "")

write(f"{WORKSPACE}/fintech-platform/config/pipeline.yaml", """\
ingestion:
  source: s3://fintech-raw/transactions/
  format: csv
normalization:
  script: src/normalizer/csv_normalizer.py
output:
  sink: postgresql://warehouse/canonical_txns
""")

write(f"{WORKSPACE}/fintech-platform/deploy/k8s/normalizer-job.yaml", """\
apiVersion: batch/v1
kind: Job
metadata:
  name: csv-normalizer
spec:
  template:
    spec:
      containers:
        - name: normalizer
          image: fintech/csv-normalizer:latest
          command: ["python3", "src/normalizer/csv_normalizer.py"]
""")

write(f"{WORKSPACE}/fintech-platform/tests/unit/test_normalizer.py", """\
import pytest
from src.normalizer.csv_normalizer import normalize_row

def test_amount_stripped():
    row = {"amount": "$1,234.56", "timestamp": "2024-01-15T10:00:00Z", "merchant": "ACME"}
    result = normalize_row(row)
    assert result["amount_usd"] == "1234.56"
""")

write(f"{WORKSPACE}/fintech-platform/docs/internal/data-dictionary.md", """\
# Data Dictionary
## Canonical Transaction Schema
| Field         | Type    | Description                        |
|---------------|---------|------------------------------------|
| txn_id        | string  | Unique transaction identifier      |
| amount_usd    | decimal | Normalized amount in USD           |
| currency      | string  | ISO 4217 currency code             |
| timestamp_utc | string  | ISO 8601 UTC timestamp             |
| merchant      | string  | Merchant name (normalized)         |
""")

# Some red-herring config files
write(f"{WORKSPACE}/fintech-platform/config/legacy_mapping.json", """\
{
  "field_map": {
    "Amt": "amount",
    "Ccy": "currency",
    "TxnDt": "timestamp"
  }
}
""")

write(f"{WORKSPACE}/fintech-platform/deploy/helm/values.yaml", """\
replicaCount: 2
image:
  repository: fintech/csv-normalizer
  tag: "2.1.0"
""")

write(f"{WORKSPACE}/fintech-platform/scripts/run_local.sh", """\
#!/usr/bin/env bash
python3 src/normalizer/csv_normalizer.py < sample.csv
""")

# ── 3. A brief from the product team (describes the goal, not the tooling) ─────
write(f"{WORKSPACE}/product-brief.txt", """\
PRODUCT BRIEF — Fintech Platform Team
======================================
We want our CSV normalization logic packaged as a distributable agent skill
so other teams can trigger it automatically. The skill should be called
"csv-normalizer" and must describe itself well enough for an AI agent to
know when to use it (think: transaction data cleaning, CSV ingestion normalization,
canonical schema transformation).

The skill should wrap the logic found in fintech-platform/src/normalizer/
and be published to our internal marketplace under the same slug "csv-normalizer"
at version 1.0.0.

Please handle the entire packaging and release process.
""")

print("Workspace generated successfully.")
print(f"  skill-publisher base: {base}")
print(f"  distractor files: fintech-platform/ tree")
print(f"  brief: product-brief.txt")