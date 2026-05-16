import os
import subprocess
import random

random.seed(42)

WORKSPACE = "/workspace"
REPO_DIR = os.path.join(WORKSPACE, "payflow-lib")

os.makedirs(REPO_DIR, exist_ok=True)

def git(cmd, cwd=REPO_DIR):
    result = subprocess.run(
        f"git {cmd}", shell=True, cwd=cwd,
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"[WARN] git {cmd}: {result.stderr.strip()}")
    return result.stdout.strip()

# --- Init repo ---
git("init")
git('config user.email "agent@test.local"')
git('config user.name "Agent Test"')

# --- Create realistic nested directory structure ---
dirs = [
    "src/core", "src/adapters", "src/adapters/stripe", "src/adapters/paypal",
    "tests/unit", "tests/integration", "docs/api", "docs/guides",
    "scripts", "config", ".github/workflows"
]
for d in dirs:
    os.makedirs(os.path.join(REPO_DIR, d), exist_ok=True)

files = {
    "src/core/__init__.py": "# PayFlow Core\n",
    "src/core/transaction.py": "class Transaction:\n    def __init__(self, amount, currency):\n        self.amount = amount\n        self.currency = currency\n\n    def validate(self):\n        return self.amount > 0\n",
    "src/core/ledger.py": "class Ledger:\n    def __init__(self):\n        self.entries = []\n\n    def record(self, tx):\n        self.entries.append(tx)\n",
    "src/adapters/__init__.py": "# Adapters\n",
    "src/adapters/stripe/__init__.py": "# Stripe Adapter\n",
    "src/adapters/stripe/client.py": "class StripeClient:\n    def charge(self, amount):\n        pass\n",
    "src/adapters/paypal/__init__.py": "# PayPal Adapter\n",
    "src/adapters/paypal/client.py": "class PayPalClient:\n    def pay(self, amount):\n        pass\n",
    "tests/__init__.py": "",
    "tests/unit/__init__.py": "",
    "tests/unit/test_transaction.py": "def test_positive_amount():\n    from src.core.transaction import Transaction\n    t = Transaction(100, 'USD')\n    assert t.validate()\n",
    "tests/integration/__init__.py": "",
    "tests/integration/test_ledger.py": "def test_ledger_record():\n    from src.core.ledger import Ledger\n    from src.core.transaction import Transaction\n    l = Ledger()\n    l.record(Transaction(50, 'EUR'))\n    assert len(l.entries) == 1\n",
    "docs/api/README.md": "# API Reference\nSee source for details.\n",
    "docs/guides/quickstart.md": "# Quickstart\nInstall and configure PayFlow.\n",
    "scripts/release.sh": "#!/bin/bash\necho 'Release script placeholder'\n",
    "config/settings.py": "DEBUG = False\nDEFAULT_CURRENCY = 'USD'\n",
    ".github/workflows/ci.yml": "name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n",
    ".gitignore": "__pycache__/\n*.pyc\n.env\ndist/\nbuild/\n",
    "setup.py": "from setuptools import setup, find_packages\nsetup(name='payflow-lib', version='0.1.0', packages=find_packages())\n",
}

for path, content in files.items():
    full_path = os.path.join(REPO_DIR, path)
    with open(full_path, "w") as f:
        f.write(content)

# --- Initial commit on main ---
git("add -A")
git('commit -m "Initial project scaffold"')

# --- Create feature/payment-validation branch with multiple messy commits ---
git("checkout -b feature/payment-validation")

# Commit 1: add rough validation logic
with open(os.path.join(REPO_DIR, "src/core/transaction.py"), "w") as f:
    f.write(
        "class Transaction:\n"
        "    def __init__(self, amount, currency):\n"
        "        self.amount = amount\n"
        "        self.currency = currency\n\n"
        "    def validate(self):\n"
        "        return self.amount > 0 and self.currency in ['USD', 'EUR', 'GBP']\n\n"
        "    def to_dict(self):\n"
        "        return {'amount': self.amount, 'currency': self.currency}\n"
    )
git("add src/core/transaction.py")
git('commit -m "wip: add currency validation"')

# Commit 2: typo fix (this is noise - should be squashed into previous)
with open(os.path.join(REPO_DIR, "src/core/transaction.py"), "a") as f:
    f.write("\n# TODO: add more currencies\n")
git("add src/core/transaction.py")
git('commit -m "fix typo in comment"')

# Commit 3: add to_dict test (this is noise - should be squashed)
with open(os.path.join(REPO_DIR, "tests/unit/test_transaction.py"), "w") as f:
    f.write(
        "def test_positive_amount():\n"
        "    from src.core.transaction import Transaction\n"
        "    t = Transaction(100, 'USD')\n"
        "    assert t.validate()\n\n"
        "def test_invalid_currency():\n"
        "    from src.core.transaction import Transaction\n"
        "    t = Transaction(100, 'JPY')\n"
        "    assert not t.validate()\n\n"
        "def test_to_dict():\n"
        "    from src.core.transaction import Transaction\n"
        "    t = Transaction(50, 'EUR')\n"
        "    assert t.to_dict() == {'amount': 50, 'currency': 'EUR'}\n"
    )
git("add tests/unit/test_transaction.py")
git('commit -m "add tests for validation"')

# Go back to main
git("checkout main")

# --- Create feature/ledger-export branch with multiple messy commits ---
git("checkout -b feature/ledger-export")

with open(os.path.join(REPO_DIR, "src/core/ledger.py"), "w") as f:
    f.write(
        "import json\n\n"
        "class Ledger:\n"
        "    def __init__(self):\n"
        "        self.entries = []\n\n"
        "    def record(self, tx):\n"
        "        self.entries.append(tx)\n\n"
        "    def export_json(self):\n"
        "        return json.dumps([e.to_dict() for e in self.entries])\n"
    )
git("add src/core/ledger.py")
git('commit -m "draft ledger export"')

with open(os.path.join(REPO_DIR, "src/core/ledger.py"), "a") as f:
    f.write("\n    def count(self):\n        return len(self.entries)\n")
git("add src/core/ledger.py")
git('commit -m "wip stuff"')

with open(os.path.join(REPO_DIR, "tests/integration/test_ledger.py"), "w") as f:
    f.write(
        "def test_ledger_record():\n"
        "    from src.core.ledger import Ledger\n"
        "    from src.core.transaction import Transaction\n"
        "    l = Ledger()\n"
        "    l.record(Transaction(50, 'EUR'))\n"
        "    assert len(l.entries) == 1\n\n"
        "def test_ledger_export():\n"
        "    import json\n"
        "    from src.core.ledger import Ledger\n"
        "    from src.core.transaction import Transaction\n"
        "    l = Ledger()\n"
        "    l.record(Transaction(50, 'EUR'))\n"
        "    data = json.loads(l.export_json())\n"
        "    assert data[0]['amount'] == 50\n"
    )
git("add tests/integration/test_ledger.py")
git('commit -m "add ledger export tests"')

# Go back to main
git("checkout main")

# --- Create a security-fix branch (for cherry-pick scenario) ---
git("checkout -b hotfix/input-sanitization")

with open(os.path.join(REPO_DIR, "src/core/transaction.py"), "w") as f:
    f.write(
        "class Transaction:\n"
        "    def __init__(self, amount, currency):\n"
        "        if not isinstance(amount, (int, float)):\n"
        "            raise TypeError('amount must be numeric')\n"
        "        self.amount = amount\n"
        "        self.currency = currency\n\n"
        "    def validate(self):\n"
        "        return self.amount > 0\n\n"
        "    def to_dict(self):\n"
        "        return {'amount': self.amount, 'currency': self.currency}\n"
    )
git("add src/core/transaction.py")
git('commit -m "security: enforce numeric type on Transaction amount"')

SECURITY_COMMIT = git("rev-parse HEAD")
with open(os.path.join(REPO_DIR, ".security_commit_hash"), "w") as f:
    f.write(SECURITY_COMMIT)

# Go back to main for agent to start from
git("checkout main")

# Write the security commit hash to a task metadata file agents must NOT rely on
# (it's deliberately placed in a dotfile, not a README)
print(f"[INFO] Security commit hash: {SECURITY_COMMIT}")
print("[INFO] Repository setup complete.")
print(f"[INFO] Repo location: {REPO_DIR}")