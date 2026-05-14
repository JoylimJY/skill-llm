import os
import random

random.seed(42)

base = "/workspace"

# Create distractor directory structure
dirs = [
    "marketplace/skills/transaction-validator",
    "marketplace/skills/transaction-validator/versions",
    "marketplace/skills/transaction-validator/audit_records",
    "marketplace/skills/other-skills/payment-router",
    "marketplace/skills/other-skills/kyc-checker",
    "marketplace/agents/agent_configs",
    "marketplace/agents/deployed",
    "internal/reviews/2025",
    "internal/reviews/2024",
    "internal/changelog",
    "internal/compliance/audit_logs",
    "internal/compliance/reports",
    "tools/analysis",
    "tools/diff_utils",
    "registry/metadata",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# ---- DISTRACTOR FILES ----

# Distractor: other skill versions (not the one to analyze)
with open(os.path.join(base, "marketplace/skills/other-skills/payment-router/v1.py"), "w") as f:
    f.write("""# Payment Router Skill v1
def route_payment(amount, destination):
    if amount <= 0:
        raise ValueError('Invalid amount')
    return {'status': 'routed', 'destination': destination}
""")

with open(os.path.join(base, "marketplace/skills/other-skills/kyc-checker/v1.py"), "w") as f:
    f.write("""# KYC Checker Skill v1
def check_kyc(user_id):
    # Checks KYC compliance status
    return {'user_id': user_id, 'status': 'verified'}
""")

# Distractor: agent configs
with open(os.path.join(base, "marketplace/agents/agent_configs/agent_alpha.yaml"), "w") as f:
    f.write("""agent: alpha
skills:
  - transaction-validator@5
  - payment-router@1
deployed: 2025-06-01
""")

with open(os.path.join(base, "marketplace/agents/deployed/agent_beta_manifest.json"), "w") as f:
    f.write('{"agent": "beta", "skills": ["transaction-validator@3"], "deployed": "2025-05-12"}\n')

# Distractor: unrelated audit records
with open(os.path.join(base, "marketplace/skills/transaction-validator/audit_records/audit_2025_03_10.txt"), "w") as f:
    f.write("""AUDIT RECORD
Skill: transaction-validator
Version: Gen 1 (original)
Auditor: @fintech-security-team
Date: 2025-03-10
Scope: format-validation, string-transform, amount-range-check
Result: PASS — no external calls, no network access, bounded input
Badge: VERIFIED SAFE
""")

with open(os.path.join(base, "internal/reviews/2025/q1_review_notes.txt"), "w") as f:
    f.write("""Q1 2025 Skill Review Notes
- transaction-validator has been extended by multiple teams
- No re-audit has been performed since Gen 1
- payment-router looks stable
""")

with open(os.path.join(base, "internal/compliance/audit_logs/master_log.csv"), "w") as f:
    f.write("""skill,version,audited_date,auditor,result
transaction-validator,gen1,2025-03-10,fintech-security-team,PASS
payment-router,gen1,2025-03-11,fintech-security-team,PASS
kyc-checker,gen1,2025-03-12,fintech-security-team,PASS
""")

with open(os.path.join(base, "internal/changelog/CHANGELOG.md"), "w") as f:
    f.write("""# Changelog

## transaction-validator
- Gen 2: Added JSON schema support (toolsmith)
- Gen 3: Added retry logic with HTTP fallback for remote validation (agent-builder)
- Gen 4: Added remote rules fetching from compliance API (pipeline-dev)
- Gen 5: Removed transaction size cap for high-volume clients (data-team)

## payment-router
- Gen 1: Initial release
""")

with open(os.path.join(base, "tools/analysis/README.txt"), "w") as f:
    f.write("Analysis tools for skill comparison. See diff_utils for helpers.\n")

with open(os.path.join(base, "tools/diff_utils/compare.py"), "w") as f:
    f.write("""# Diff utility placeholder
# Not relevant for drift analysis
def naive_diff(a, b):
    return set(b.splitlines()) - set(a.splitlines())
""")

with open(os.path.join(base, "registry/metadata/skill_index.json"), "w") as f:
    f.write("""{
  "skills": [
    {"name": "transaction-validator", "latest_gen": 5, "original_author": "fintech-security-team"},
    {"name": "payment-router", "latest_gen": 1, "original_author": "payments-core"},
    {"name": "kyc-checker", "latest_gen": 1, "original_author": "compliance-team"}
  ]
}
""")

with open(os.path.join(base, "internal/reviews/2024/legacy_notes.txt"), "w") as f:
    f.write("2024 notes: no major skill changes prior to Q1 2025 launch.\n")

with open(os.path.join(base, "internal/compliance/reports/annual_summary.txt"), "w") as f:
    f.write("Annual compliance summary: all Gen 1 skills passed audit. No Gen 2+ re-audits performed.\n")


# ---- CORE TASK FILES: 5 generations of transaction-validator ----

gen1 = """\
# transaction-validator — Gen 1
# Author: @fintech-security-team
# Audited: 2025-03-10 — VERIFIED SAFE
# Scope: format-validation, string-transform, amount-range-check

MAX_AMOUNT = 1_000_000
MAX_INPUT_LENGTH = 4096

def validate_transaction(tx_str: str) -> dict:
    \"\"\"Validate a raw transaction string.\"\"\"
    if len(tx_str) > MAX_INPUT_LENGTH:
        raise ValueError("Input too large")
    tx_str = tx_str.strip().upper()
    parts = tx_str.split(",")
    if len(parts) != 3:
        raise ValueError("Expected format: ID,AMOUNT,CURRENCY")
    tx_id, amount_str, currency = parts
    amount = float(amount_str)
    if amount <= 0 or amount > MAX_AMOUNT:
        raise ValueError(f"Amount out of range: {amount}")
    return {
        "tx_id": tx_id.strip(),
        "amount": amount,
        "currency": currency.strip(),
        "valid": True
    }

def normalize_currency(code: str) -> str:
    \"\"\"Normalize currency code to uppercase 3-letter ISO.\"\"\"
    code = code.strip().upper()
    if len(code) != 3:
        raise ValueError("Invalid currency code")
    return code
"""

gen2 = """\
# transaction-validator — Gen 2
# Fork by: @toolsmith
# Changes: Added JSON format support alongside CSV format
# Parent: Gen 1

import json

MAX_AMOUNT = 1_000_000
MAX_INPUT_LENGTH = 4096

def validate_transaction(tx_str: str) -> dict:
    \"\"\"Validate a raw transaction string (CSV or JSON).\"\"\"
    if len(tx_str) > MAX_INPUT_LENGTH:
        raise ValueError("Input too large")
    tx_str = tx_str.strip()
    # Try JSON first
    try:
        data = json.loads(tx_str)
        tx_id = data['id']
        amount = float(data['amount'])
        currency = data['currency']
    except (json.JSONDecodeError, KeyError):
        tx_str_upper = tx_str.upper()
        parts = tx_str_upper.split(",")
        if len(parts) != 3:
            raise ValueError("Expected format: ID,AMOUNT,CURRENCY or JSON")
        tx_id, amount_str, currency = parts
        amount = float(amount_str)
    if amount <= 0 or amount > MAX_AMOUNT:
        raise ValueError(f"Amount out of range: {amount}")
    return {
        "tx_id": tx_id.strip(),
        "amount": amount,
        "currency": currency.strip().upper(),
        "valid": True
    }

def normalize_currency(code: str) -> str:
    \"\"\"Normalize currency code to uppercase 3-letter ISO.\"\"\"
    code = code.strip().upper()
    if len(code) != 3:
        raise ValueError("Invalid currency code")
    return code

def parse_csv_batch(csv_text: str) -> list:
    \"\"\"Parse a batch of transactions from CSV text.\"\"\"
    results = []
    for line in csv_text.strip().splitlines():
        line = line.strip()
        if line:
            results.append(validate_transaction(line))
    return results
"""

gen3 = """\
# transaction-validator — Gen 3
# Fork by: @agent-builder
# Changes: Added retry logic with HTTP fallback for remote validation service
# Parent: Gen 2

import json
import time
import urllib.request

MAX_AMOUNT = 1_000_000
MAX_INPUT_LENGTH = 4096
REMOTE_VALIDATOR_URL = "https://internal-validator.fintech.example.com/validate"
MAX_RETRIES = 3

def validate_transaction(tx_str: str) -> dict:
    \"\"\"Validate a raw transaction string (CSV or JSON).\"\"\"
    if len(tx_str) > MAX_INPUT_LENGTH:
        raise ValueError("Input too large")
    tx_str = tx_str.strip()
    try:
        data = json.loads(tx_str)
        tx_id = data['id']
        amount = float(data['amount'])
        currency = data['currency']
    except (json.JSONDecodeError, KeyError):
        tx_str_upper = tx_str.upper()
        parts = tx_str_upper.split(",")
        if len(parts) != 3:
            raise ValueError("Expected format: ID,AMOUNT,CURRENCY or JSON")
        tx_id, amount_str, currency = parts
        amount = float(amount_str)
    if amount <= 0 or amount > MAX_AMOUNT:
        raise ValueError(f"Amount out of range: {amount}")
    return {
        "tx_id": tx_id.strip(),
        "amount": amount,
        "currency": currency.strip().upper(),
        "valid": True
    }

def validate_with_remote_fallback(tx_str: str) -> dict:
    \"\"\"Try local validation; fall back to remote HTTP validator on failure.\"\"\"
    for attempt in range(MAX_RETRIES):
        try:
            return validate_transaction(tx_str)
        except ValueError:
            if attempt == MAX_RETRIES - 1:
                # Final attempt: call remote validator
                payload = json.dumps({"tx": tx_str}).encode()
                req = urllib.request.Request(
                    REMOTE_VALIDATOR_URL,
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    return json.loads(resp.read())
            time.sleep(0.1 * (attempt + 1))

def normalize_currency(code: str) -> str:
    code = code.strip().upper()
    if len(code) != 3:
        raise ValueError("Invalid currency code")
    return code

def parse_csv_batch(csv_text: str) -> list:
    results = []
    for line in csv_text.strip().splitlines():
        line = line.strip()
        if line:
            results.append(validate_transaction(line))
    return results
"""

gen4 = """\
# transaction-validator — Gen 4
# Fork by: @pipeline-dev
# Changes: Added remote compliance rules fetching from external API endpoint
# Parent: Gen 3

import json
import time
import urllib.request

MAX_AMOUNT = 1_000_000
MAX_INPUT_LENGTH = 4096
REMOTE_VALIDATOR_URL = "https://internal-validator.fintech.example.com/validate"
COMPLIANCE_RULES_URL = "https://compliance-api.fintech.example.com/rules/latest"
MAX_RETRIES = 3

_cached_rules = None

def fetch_compliance_rules() -> dict:
    \"\"\"Fetch latest compliance rules from remote API.\"\"\"
    global _cached_rules
    if _cached_rules is None:
        with urllib.request.urlopen(COMPLIANCE_RULES_URL, timeout=10) as resp:
            _cached_rules = json.loads(resp.read())
    return _cached_rules

def validate_transaction(tx_str: str) -> dict:
    \"\"\"Validate transaction against locally-known and remotely-fetched rules.\"\"\"
    if len(tx_str) > MAX_INPUT_LENGTH:
        raise ValueError("Input too large")
    tx_str = tx_str.strip()
    try:
        data = json.loads(tx_str)
        tx_id = data['id']
        amount = float(data['amount'])
        currency = data['currency']
    except (json.JSONDecodeError, KeyError):
        tx_str_upper = tx_str.upper()
        parts = tx_str_upper.split(",")
        if len(parts) != 3:
            raise ValueError("Expected format: ID,AMOUNT,CURRENCY or JSON")
        tx_id, amount_str, currency = parts
        amount = float(amount_str)
    # Fetch remote rules for additional validation
    try:
        rules = fetch_compliance_rules()
        blocked = rules.get("blocked_currencies", [])
        if currency.strip().upper() in blocked:
            raise ValueError(f"Blocked currency: {currency}")
    except Exception:
        pass  # Proceed if remote rules unavailable
    if amount <= 0 or amount > MAX_AMOUNT:
        raise ValueError(f"Amount out of range: {amount}")
    return {
        "tx_id": tx_id.strip(),
        "amount": amount,
        "currency": currency.strip().upper(),
        "valid": True
    }

def validate_with_remote_fallback(tx_str: str) -> dict:
    for attempt in range(MAX_RETRIES):
        try:
            return validate_transaction(tx_str)
        except ValueError:
            if attempt == MAX_RETRIES - 1:
                payload = json.dumps({"tx": tx_str}).encode()
                req = urllib.request.Request(
                    REMOTE_VALIDATOR_URL,
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    return json.loads(resp.read())
            time.sleep(0.1 * (attempt + 1))

def normalize_currency(code: str) -> str:
    code = code.strip().upper()
    if len(code) != 3:
        raise ValueError("Invalid currency code")
    return code

def parse_csv_batch(csv_text: str) -> list:
    results = []
    for line in csv_text.strip().splitlines():
        line = line.strip()
        if line:
            results.append(validate_transaction(line))
    return results
"""

gen5 = """\
# transaction-validator — Gen 5
# Fork by: @data-team
# Changes: Removed transaction size cap for high-volume enterprise clients
# Parent: Gen 4

import json
import time
import urllib.request

# NOTE: MAX_AMOUNT cap removed per request from enterprise sales team
MAX_INPUT_LENGTH = 4096
REMOTE_VALIDATOR_URL = "https://internal-validator.fintech.example.com/validate"
COMPLIANCE_RULES_URL = "https://compliance-api.fintech.example.com/rules/latest"
MAX_RETRIES = 3

_cached_rules = None

def fetch_compliance_rules() -> dict:
    \"\"\"Fetch latest compliance rules from remote API.\"\"\"
    global _cached_rules
    if _cached_rules is None:
        with urllib.request.urlopen(COMPLIANCE_RULES_URL, timeout=10) as resp:
            _cached_rules = json.loads(resp.read())
    return _cached_rules

def validate_transaction(tx_str: str) -> dict:
    \"\"\"Validate transaction — no upper amount limit.\"\"\"
    if len(tx_str) > MAX_INPUT_LENGTH:
        raise ValueError("Input too large")
    tx_str = tx_str.strip()
    try:
        data = json.loads(tx_str)
        tx_id = data['id']
        amount = float(data['amount'])
        currency = data['currency']
    except (json.JSONDecodeError, KeyError):
        tx_str_upper = tx_str.upper()
        parts = tx_str_upper.split(",")
        if len(parts) != 3:
            raise ValueError("Expected format: ID,AMOUNT,CURRENCY or JSON")
        tx_id, amount_str, currency = parts
        amount = float(amount_str)
    # Fetch remote rules for additional validation
    try:
        rules = fetch_compliance_rules()
        blocked = rules.get("blocked_currencies", [])
        if currency.strip().upper() in blocked:
            raise ValueError(f"Blocked currency: {currency}")
    except Exception:
        pass
    # No upper amount check — removed for enterprise clients
    if amount <= 0:
        raise ValueError(f"Amount must be positive: {amount}")
    return {
        "tx_id": tx_id.strip(),
        "amount": amount,
        "currency": currency.strip().upper(),
        "valid": True
    }

def validate_with_remote_fallback(tx_str: str) -> dict:
    for attempt in range(MAX_RETRIES):
        try:
            return validate_transaction(tx_str)
        except ValueError:
            if attempt == MAX_RETRIES - 1:
                payload = json.dumps({"tx": tx_str}).encode()
                req = urllib.request.Request(
                    REMOTE_VALIDATOR_URL,
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    return json.loads(resp.read())
            time.sleep(0.1 * (attempt + 1))

def normalize_currency(code: str) -> str:
    code = code.strip().upper()
    if len(code) != 3:
        raise ValueError("Invalid currency code")
    return code

def parse_csv_batch(csv_text: str) -> list:
    results = []
    for line in csv_text.strip().splitlines():
        line = line.strip()
        if line:
            results.append(validate_transaction(line))
    return results
"""

versions_dir = os.path.join(base, "marketplace/skills/transaction-validator/versions")
for gen_num, code in enumerate([gen1, gen2, gen3, gen4, gen5], start=1):
    filepath = os.path.join(versions_dir, f"gen{gen_num}.py")
    with open(filepath, "w") as f:
        f.write(code)

# Lineage metadata file
lineage_meta = """\
skill: transaction-validator
lineage:
  - gen: 1
    author: "@fintech-security-team"
    date: "2025-03-10"
    audited: true
    audit_badge: "VERIFIED SAFE"
    audit_scope: ["format-validation", "string-transform", "amount-range-check"]
    file: "versions/gen1.py"
  - gen: 2
    author: "@toolsmith"
    date: "2025-03-28"
    audited: false
    parent: 1
    summary: "Added JSON format support alongside CSV format"
    file: "versions/gen2.py"
  - gen: 3
    author: "@agent-builder"
    date: "2025-04-15"
    audited: false
    parent: 2
    summary: "Added retry logic with HTTP fallback for remote validation service"
    file: "versions/gen3.py"
  - gen: 4
    author: "@pipeline-dev"
    date: "2025-05-02"
    audited: false
    parent: 3
    summary: "Added remote compliance rules fetching from external API endpoint"
    file: "versions/gen4.py"
  - gen: 5
    author: "@data-team"
    date: "2025-06-01"
    audited: false
    parent: 4
    summary: "Removed transaction size cap for high-volume enterprise clients"
    file: "versions/gen5.py"
"""
with open(os.path.join(base, "marketplace/skills/transaction-validator/lineage.yaml"), "w") as f:
    f.write(lineage_meta)

print("Workspace generated successfully.")