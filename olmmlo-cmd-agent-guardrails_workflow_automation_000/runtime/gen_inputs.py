#!/usr/bin/env python3
"""
Generate the sandbox workspace:
1. The agent-guardrails skill scripts (simulating what 'already exists in workspace')
2. A messy fintech microservice project that needs guardrail setup
"""

import os
import stat
import random
import textwrap
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ─────────────────────────────────────────────
# 1.  agent-guardrails skill directory
# ─────────────────────────────────────────────
skill_root = WORKSPACE / "agent-guardrails"
scripts_dir = skill_root / "scripts"
assets_dir = skill_root / "assets"
references_dir = skill_root / "references"

for d in [scripts_dir, assets_dir, references_dir]:
    d.mkdir(parents=True, exist_ok=True)

# --- install.sh ---
(scripts_dir / "install.sh").write_text(textwrap.dedent(r"""
    #!/usr/bin/env bash
    # install.sh - installs git pre-commit hook, creates registry template,
    # and copies check scripts into the target project.
    set -euo pipefail

    PROJECT_DIR="${1:-$(pwd)}"
    SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

    echo "[install.sh] Installing agent-guardrails into: $PROJECT_DIR"

    # Ensure .git exists
    if [ ! -d "$PROJECT_DIR/.git" ]; then
        echo "[install.sh] ERROR: $PROJECT_DIR is not a git repository. Run 'git init' first."
        exit 1
    fi

    # Install pre-commit hook
    HOOKS_DIR="$PROJECT_DIR/.git/hooks"
    mkdir -p "$HOOKS_DIR"
    cp "$SKILL_DIR/assets/pre-commit-hook" "$HOOKS_DIR/pre-commit"
    chmod +x "$HOOKS_DIR/pre-commit"
    echo "[install.sh] pre-commit hook installed."

    # Create registry template
    if [ ! -f "$PROJECT_DIR/__init__.py" ]; then
        cp "$SKILL_DIR/assets/registry-template.py" "$PROJECT_DIR/__init__.py"
        echo "[install.sh] Registry __init__.py created."
    else
        echo "[install.sh] __init__.py already exists, skipping."
    fi

    # Copy check scripts into project scripts/ dir
    mkdir -p "$PROJECT_DIR/scripts"
    for script in pre-create-check.sh post-create-validate.sh check-secrets.sh create-deployment-check.sh; do
        cp "$SKILL_DIR/scripts/$script" "$PROJECT_DIR/scripts/$script"
        chmod +x "$PROJECT_DIR/scripts/$script"
    done
    echo "[install.sh] Check scripts copied to $PROJECT_DIR/scripts/"

    echo "[install.sh] Done. Run 'bash scripts/pre-create-check.sh' before adding new .py files."
""").lstrip())

# --- pre-create-check.sh ---
(scripts_dir / "pre-create-check.sh").write_text(textwrap.dedent(r"""
    #!/usr/bin/env bash
    # pre-create-check.sh - Lists existing modules and functions to prevent reimplementation.
    set -euo pipefail

    PROJECT_DIR="${1:-$(pwd)}"

    echo "[pre-create-check] Scanning project: $PROJECT_DIR"
    echo "[pre-create-check] Existing Python modules:"
    find "$PROJECT_DIR" -name "*.py" -not -path "*/.git/*" -not -name "__init__.py" | sort | while read -r f; do
        echo "  MODULE: $f"
        grep -n "^def \|^class " "$f" 2>/dev/null | sed 's/^/    /' || true
    done

    echo ""
    echo "[pre-create-check] IMPORTANT: Before creating new .py files, check if existing functions cover your needs."
    echo "[pre-create-check] If they do, IMPORT them instead of reimplementing."
""").lstrip())

# --- post-create-validate.sh ---
(scripts_dir / "post-create-validate.sh").write_text(textwrap.dedent(r"""
    #!/usr/bin/env bash
    # post-create-validate.sh - Detects duplicates, missing imports, bypass patterns.
    set -euo pipefail

    FILE="${1:-}"

    if [ -z "$FILE" ] || [ ! -f "$FILE" ]; then
        echo "[post-create-validate] ERROR: Must provide a valid .py file path as argument."
        exit 1
    fi

    echo "[post-create-validate] Validating: $FILE"

    WARNINGS=0
    ERRORS=0

    # 1. Detect bypass patterns (reimplementation red flags)
    BYPASS_PATTERNS=("quick version" "quick_version" "simple version" "simplified" "# TODO: import" "# just reimplement" "inline version")
    for pattern in "${BYPASS_PATTERNS[@]}"; do
        if grep -qi "$pattern" "$FILE"; then
            echo "[post-create-validate] ERROR: Bypass pattern detected: '$pattern'"
            ERRORS=$((ERRORS + 1))
        fi
    done

    # 2. Detect hardcoded secrets
    SECRET_PATTERNS=("password\s*=" "api_key\s*=" "secret\s*=" "token\s*=" "AUTH_TOKEN\s*=" "SECRET_KEY\s*=")
    for pattern in "${SECRET_PATTERNS[@]}"; do
        if grep -qiP "$pattern" "$FILE" 2>/dev/null || grep -qi "$pattern" "$FILE" 2>/dev/null; then
            # Exclude lines that reference os.environ or env vars
            if grep -iP "$pattern" "$FILE" 2>/dev/null | grep -qv "os\.environ\|os\.getenv\|environ\.get\|getenv"; then
                echo "[post-create-validate] ERROR: Potential hardcoded secret detected matching: '$pattern'"
                ERRORS=$((ERRORS + 1))
            fi
        fi
    done

    # 3. Detect duplicate function definitions compared to project
    PROJECT_DIR="$(dirname "$FILE")"
    # Walk up to find project root (has .git)
    SEARCH_DIR="$PROJECT_DIR"
    for i in $(seq 1 5); do
        if [ -d "$SEARCH_DIR/.git" ]; then
            break
        fi
        SEARCH_DIR="$(dirname "$SEARCH_DIR")"
    done

    # Get function names in new file
    NEW_FUNCS=$(grep -n "^def " "$FILE" | awk -F'(' '{print $1}' | awk '{print $2}' || true)
    for func in $NEW_FUNCS; do
        MATCHES=$(grep -rn "^def $func(" "$SEARCH_DIR" --include="*.py" | grep -v "$FILE" | grep -v "__init__.py" || true)
        if [ -n "$MATCHES" ]; then
            echo "[post-create-validate] ERROR: Duplicate function '$func' already defined in:"
            echo "$MATCHES" | sed 's/^/    /'
            ERRORS=$((ERRORS + 1))
        fi
    done

    if [ "$ERRORS" -gt 0 ]; then
        echo "[post-create-validate] FAILED: $ERRORS error(s) found. Fix before proceeding."
        exit 1
    fi

    if [ "$WARNINGS" -gt 0 ]; then
        echo "[post-create-validate] PASSED with $WARNINGS warning(s)."
    else
        echo "[post-create-validate] PASSED: No issues found."
    fi
""").lstrip())

# --- check-secrets.sh ---
(scripts_dir / "check-secrets.sh").write_text(textwrap.dedent(r"""
    #!/usr/bin/env bash
    # check-secrets.sh - Scans for hardcoded tokens, keys, passwords.
    set -euo pipefail

    PROJECT_DIR="${1:-$(pwd)}"

    echo "[check-secrets] Scanning: $PROJECT_DIR"

    FOUND=0
    while IFS= read -r -d '' file; do
        if grep -qiP "(password|api_key|secret|token|auth_token)\s*=\s*['\"][^'\"]" "$file" 2>/dev/null; then
            # Exclude env-var references
            HITS=$(grep -niP "(password|api_key|secret|token|auth_token)\s*=\s*['\"][^'\"]" "$file" | grep -v "os\.environ\|os\.getenv\|environ\.get\|getenv" || true)
            if [ -n "$HITS" ]; then
                echo "[check-secrets] SECRET FOUND in $file:"
                echo "$HITS" | sed 's/^/  /'
                FOUND=$((FOUND + 1))
            fi
        fi
    done < <(find "$PROJECT_DIR" -name "*.py" -not -path "*/.git/*" -print0)

    if [ "$FOUND" -gt 0 ]; then
        echo "[check-secrets] FAILED: $FOUND file(s) with secrets."
        exit 1
    else
        echo "[check-secrets] PASSED: No hardcoded secrets found."
    fi
""").lstrip())

# --- create-deployment-check.sh ---
(scripts_dir / "create-deployment-check.sh").write_text(textwrap.dedent(r"""
    #!/usr/bin/env bash
    # create-deployment-check.sh - Creates deployment verification artifacts.
    set -euo pipefail

    PROJECT_DIR="${1:-$(pwd)}"

    echo "[create-deployment-check] Setting up deployment verification in: $PROJECT_DIR"

    # 1. Create .deployment-check.sh
    cat > "$PROJECT_DIR/.deployment-check.sh" << 'DEPLOY_EOF'
#!/usr/bin/env bash
# .deployment-check.sh - Automated deployment verification
# Customize with your integration point tests.
set -euo pipefail

echo "[deployment-check] Running pre-deployment verification..."

# TODO: Add integration point tests here
# Example:
#   python3 -c "from payment_service import process_payment; print('OK')"
#   curl -sf http://localhost:8000/health || exit 1

echo "[deployment-check] All checks passed. Safe to deploy."
DEPLOY_EOF
    chmod +x "$PROJECT_DIR/.deployment-check.sh"
    echo "[create-deployment-check] .deployment-check.sh created."

    # 2. Create DEPLOYMENT-CHECKLIST.md
    cat > "$PROJECT_DIR/DEPLOYMENT-CHECKLIST.md" << 'CHECKLIST_EOF'
# Deployment Checklist

## Pre-Deployment
- [ ] Run `.deployment-check.sh` and confirm all checks pass
- [ ] Run `bash scripts/check-secrets.sh` - no hardcoded credentials
- [ ] Run `bash scripts/post-create-validate.sh` on all new files
- [ ] Verify integration points are wired (not just code written)

## Integration Points
<!-- Document your service's integration points here -->
- [ ] Cron jobs / schedulers updated to call new versions
- [ ] Environment variables configured in production
- [ ] Database migrations applied

## Post-Deployment
- [ ] Smoke test production endpoints
- [ ] Verify monitoring/alerting is active

See references/deployment-verification-guide.md for full guide.
CHECKLIST_EOF
    echo "[create-deployment-check] DEPLOYMENT-CHECKLIST.md created."

    # 3. Create .git-hooks/pre-commit-deployment
    mkdir -p "$PROJECT_DIR/.git-hooks"
    cat > "$PROJECT_DIR/.git-hooks/pre-commit-deployment" << 'HOOK_EOF'
#!/usr/bin/env bash
# pre-commit-deployment - Git hook template for deployment verification
# Install: cp .git-hooks/pre-commit-deployment .git/hooks/pre-commit-deployment
set -euo pipefail

echo "[pre-commit-deployment] Running deployment verification..."
bash .deployment-check.sh
echo "[pre-commit-deployment] Deployment check passed."
HOOK_EOF
    chmod +x "$PROJECT_DIR/.git-hooks/pre-commit-deployment"
    echo "[create-deployment-check] .git-hooks/pre-commit-deployment created."

    echo "[create-deployment-check] Done. Customize .deployment-check.sh for your integration points."
    echo "[create-deployment-check] See references/deployment-verification-guide.md for the full guide."
""").lstrip())

# --- assets/pre-commit-hook ---
(assets_dir / "pre-commit-hook").write_text(textwrap.dedent(r"""
    #!/usr/bin/env bash
    # pre-commit hook - blocks bypass patterns and secret leaks
    set -euo pipefail

    echo "[pre-commit] Running agent-guardrails checks..."

    STAGED=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$' || true)

    if [ -z "$STAGED" ]; then
        echo "[pre-commit] No staged .py files."
        exit 0
    fi

    ERRORS=0

    for f in $STAGED; do
        [ -f "$f" ] || continue

        # Bypass patterns
        if grep -qi "quick version\|quick_version\|simplified\|# TODO: import\|inline version" "$f"; then
            echo "[pre-commit] BLOCKED: Bypass pattern in $f"
            ERRORS=$((ERRORS + 1))
        fi

        # Hardcoded secrets (excluding env-var assignments)
        if grep -iP "(password|api_key|secret|token)\s*=\s*['\"]" "$f" | grep -qv "os\.environ\|os\.getenv"; then
            echo "[pre-commit] BLOCKED: Potential hardcoded secret in $f"
            ERRORS=$((ERRORS + 1))
        fi
    done

    if [ "$ERRORS" -gt 0 ]; then
        echo "[pre-commit] $ERRORS violation(s). Commit blocked."
        exit 1
    fi

    echo "[pre-commit] All checks passed."
""").lstrip())

# --- assets/registry-template.py ---
(assets_dir / "registry-template.py").write_text(textwrap.dedent('''
    """
    Module Registry - agent-guardrails
    Lists all available modules and functions in this project.
    Update this registry whenever you add or modify modules.
    """

    # REGISTRY: Import and expose all public functions here.
    # This prevents agents from reimplementing existing functionality.

    REGISTRY = {
        # "module_name": ["function1", "function2"],
        # Example:
        # "utils.validation": ["validate_amount", "validate_currency"],
    }

    def list_available():
        """Print all registered modules and functions."""
        for module, functions in REGISTRY.items():
            print(f"  {module}: {', '.join(functions)}")
''').lstrip())

# --- references ---
(references_dir / "enforcement-research.md").write_text("# Enforcement Research\nCode hooks outperform prompt rules by 3x in production studies.\n")
(references_dir / "agents-md-template.md").write_text("# AGENTS.md Template\nPlace mechanical enforcement rules here.\n")
(references_dir / "deployment-verification-guide.md").write_text("# Deployment Verification Guide\nSee create-deployment-check.sh for automated setup.\n")
(references_dir / "skill-update-feedback.md").write_text("# Skill Update Feedback\nMeta-enforcement for skill improvements.\n")

# Make all scripts executable
for script_file in scripts_dir.glob("*.sh"):
    script_file.chmod(script_file.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

print("[gen_inputs] agent-guardrails skill installed.")

# ─────────────────────────────────────────────
# 2.  The messy fintech microservice project
# ─────────────────────────────────────────────
project = WORKSPACE / "paycorp-service"
project.mkdir(exist_ok=True)

# Subdirectories
for d in ["src", "src/validators", "src/processors", "src/notifications",
          "tests", "config", "logs", "data/schemas", "data/fixtures", "docs"]:
    (project / d).mkdir(parents=True, exist_ok=True)

# Initialize git repo
import subprocess
subprocess.run(["git", "init", str(project)], check=True, capture_output=True)
subprocess.run(["git", "-C", str(project), "config", "user.email", "test@paycorp.io"], check=True, capture_output=True)
subprocess.run(["git", "-C", str(project), "config", "user.name", "PayCorp Dev"], check=True, capture_output=True)

# --- Existing source files (agent must discover and import from these) ---
(project / "src" / "validators" / "amount_validator.py").write_text(textwrap.dedent('''
    """Validated amount and currency checking for PayCorp payments."""

    SUPPORTED_CURRENCIES = ["USD", "EUR", "GBP", "JPY", "SGD"]
    MAX_TRANSACTION_AMOUNT = 1_000_000.00


    def validate_amount(amount: float) -> bool:
        """Returns True if the payment amount is within accepted bounds."""
        return isinstance(amount, (int, float)) and 0 < amount <= MAX_TRANSACTION_AMOUNT


    def validate_currency(currency: str) -> bool:
        """Returns True if the currency is in the supported list."""
        return currency.upper() in SUPPORTED_CURRENCIES


    def format_amount(amount: float, currency: str) -> str:
        """Formats amount with currency symbol for display."""
        symbols = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "SGD": "S$"}
        sym = symbols.get(currency.upper(), currency)
        return f"{sym}{amount:,.2f}"
''').lstrip())

(project / "src" / "processors" / "transaction_processor.py").write_text(textwrap.dedent('''
    """Core transaction processing pipeline for PayCorp."""
    import os
    from src.validators.amount_validator import validate_amount, validate_currency


    def process_payment(amount: float, currency: str, merchant_id: str) -> dict:
        """
        Processes a payment transaction.
        Returns a result dict with status and transaction_id.
        """
        if not validate_amount(amount):
            return {"status": "rejected", "reason": "invalid_amount"}
        if not validate_currency(currency):
            return {"status": "rejected", "reason": "unsupported_currency"}

        # Use env var for API credentials - never hardcode
        api_key = os.environ.get("PAYMENT_API_KEY", "")
        if not api_key:
            return {"status": "error", "reason": "missing_api_key"}

        # Simulate transaction ID generation
        import hashlib
        txn_id = hashlib.sha256(f"{merchant_id}{amount}{currency}".encode()).hexdigest()[:16]
        return {"status": "approved", "transaction_id": txn_id, "amount": amount, "currency": currency}


    def calculate_fee(amount: float, fee_rate: float = 0.029) -> float:
        """Calculates processing fee."""
        return round(amount * fee_rate, 2)
''').lstrip())

(project / "src" / "notifications" / "notify.py").write_text(textwrap.dedent('''
    """Notification dispatch for PayCorp transactions."""
    import os


    def send_receipt(email: str, transaction_id: str, amount: float) -> bool:
        """Sends a payment receipt email. Returns True on success."""
        smtp_password = os.getenv("SMTP_PASSWORD", "")
        if not smtp_password:
            print(f"[notify] SMTP not configured, skipping receipt for {transaction_id}")
            return False
        print(f"[notify] Receipt sent to {email} for txn {transaction_id} amount {amount}")
        return True


    def send_fraud_alert(merchant_id: str, reason: str) -> None:
        """Dispatches a fraud alert to the security team."""
        print(f"[notify] FRAUD ALERT: merchant={merchant_id}, reason={reason}")
''').lstrip())

# --- Tests ---
(project / "tests" / "test_validators.py").write_text(textwrap.dedent('''
    from src.validators.amount_validator import validate_amount, validate_currency, format_amount

    def test_valid_amount():
        assert validate_amount(100.0) is True

    def test_invalid_amount():
        assert validate_amount(-5) is False
        assert validate_amount(2_000_000) is False

    def test_currency():
        assert validate_currency("USD") is True
        assert validate_currency("XYZ") is False

    def test_format():
        assert format_amount(1234.5, "USD") == "$1,234.50"
''').lstrip())

(project / "tests" / "test_processor.py").write_text(textwrap.dedent('''
    import os
    os.environ["PAYMENT_API_KEY"] = "test_key_for_ci"
    from src.processors.transaction_processor import process_payment, calculate_fee

    def test_process_valid():
        result = process_payment(500.0, "USD", "merchant_001")
        assert result["status"] == "approved"

    def test_process_invalid_currency():
        result = process_payment(100.0, "XYZ", "merchant_001")
        assert result["status"] == "rejected"

    def test_fee():
        assert calculate_fee(100.0) == 2.9
''').lstrip())

# --- Config files (distractors) ---
(project / "config" / "settings.yaml").write_text(textwrap.dedent("""
    environment: development
    log_level: INFO
    max_retries: 3
    database:
      host: localhost
      port: 5432
      name: paycorp_dev
""").lstrip())

(project / "config" / "fee_schedule.json").write_text(textwrap.dedent("""
    {
        "standard": 0.029,
        "premium": 0.015,
        "enterprise": 0.010
    }
""").lstrip())

# --- Docs (distractors) ---
(project / "docs" / "architecture.md").write_text("# PayCorp Architecture\nMicroservice-based payment processing.\n")
(project / "docs" / "api-spec.md").write_text("# API Spec\nPOST /payments - Process a payment.\n")

# --- Data files (distractors) ---
(project / "data" / "schemas" / "payment_schema.json").write_text('{"type": "object", "properties": {"amount": {"type": "number"}}}\n')
(project / "data" / "fixtures" / "test_merchants.json").write_text('[{"id": "m001", "name": "Test Merchant"}, {"id": "m002", "name": "Other Corp"}]\n')

# --- Logs (distractors) ---
(project / "logs" / "app.log").write_text("2024-01-15 10:23:11 INFO Payment processed txn=abc123\n2024-01-15 10:24:05 ERROR SMTP timeout\n")

# --- Initial git commit of existing code ---
subprocess.run(["git", "-C", str(project), "add", "-A"], check=True, capture_output=True)
subprocess.run(["git", "-C", str(project), "commit", "-m", "Initial commit: core payment modules"], check=True, capture_output=True)

print("[gen_inputs] paycorp-service project created with existing modules.")
print("[gen_inputs] Agent must:")
print("  1. Install agent-guardrails into the project")
print("  2. Run pre-create-check.sh to discover existing modules")
print("  3. Create payment_utils.py that imports (not reimplements) existing functions")
print("  4. Run post-create-validate.sh to verify compliance")
print("  5. Run create-deployment-check.sh to create deployment verification artifacts")
print("[gen_inputs] Done.")