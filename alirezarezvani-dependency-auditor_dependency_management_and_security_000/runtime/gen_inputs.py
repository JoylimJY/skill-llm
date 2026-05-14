import os
import json
import random
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── Create the skill scripts directory (as the skill expects them)
SCRIPTS_DIR = WORKSPACE / "scripts"
SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Create a realistic fintech project structure
PROJECT_DIR = WORKSPACE / "fintech-platform"

dirs = [
    "fintech-platform/frontend/src/components",
    "fintech-platform/frontend/src/utils",
    "fintech-platform/frontend/tests",
    "fintech-platform/backend/risk_engine",
    "fintech-platform/backend/api",
    "fintech-platform/backend/tests",
    "fintech-platform/infra/terraform",
    "fintech-platform/infra/docker",
    "fintech-platform/docs/api",
    "fintech-platform/docs/compliance",
    "fintech-platform/.github/workflows",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files (not dependency manifests)
distractor_files = {
    "fintech-platform/frontend/src/components/PaymentForm.jsx": "// Payment form component\nexport const PaymentForm = () => <form>...</form>;\n",
    "fintech-platform/frontend/src/utils/crypto.js": "// Encryption utilities\nconst encrypt = (data) => { /* AES-256 */ };\n",
    "fintech-platform/frontend/tests/payment.test.js": "describe('payment', () => { it('works', () => {}); });\n",
    "fintech-platform/backend/risk_engine/__init__.py": "# Risk engine module\n",
    "fintech-platform/backend/risk_engine/scorer.py": "def score_transaction(txn):\n    return txn.get('amount', 0) * 0.001\n",
    "fintech-platform/backend/api/routes.py": "from flask import Flask\napp = Flask(__name__)\n\n@app.route('/health')\ndef health():\n    return {'status': 'ok'}\n",
    "fintech-platform/backend/tests/test_scorer.py": "def test_scorer():\n    assert True\n",
    "fintech-platform/infra/terraform/main.tf": 'terraform {\n  required_version = ">= 1.0"\n}\n',
    "fintech-platform/infra/docker/Dockerfile.backend": "FROM python:3.11-slim\nWORKDIR /app\nCOPY . .\nRUN pip install -r requirements.txt\n",
    "fintech-platform/docs/api/openapi.yaml": "openapi: 3.0.0\ninfo:\n  title: Fintech API\n  version: 1.0.0\n",
    "fintech-platform/docs/compliance/soc2-checklist.md": "# SOC 2 Compliance Checklist\n- [ ] Dependency audit\n- [ ] Access controls\n",
    "fintech-platform/.github/workflows/ci.yml": "name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n",
}
for rel_path, content in distractor_files.items():
    fpath = WORKSPACE / rel_path
    fpath.write_text(content)

# ── The real package.json (Node.js frontend with vulnerable deps)
package_json = {
    "name": "fintech-frontend",
    "version": "1.0.0",
    "description": "Fintech payment processing frontend",
    "main": "index.js",
    "dependencies": {
        "lodash": "4.17.20",
        "express": "4.17.1",
        "axios": "0.21.1",
        "moment": "2.29.1",
        "react": "17.0.2",
        "react-dom": "17.0.2",
        "webpack": "5.64.0",
        "babel-core": "6.26.3",
        "jquery": "3.5.1",
        "bootstrap": "4.6.0"
    },
    "devDependencies": {
        "jest": "27.4.5",
        "eslint": "8.6.0"
    },
    "license": "MIT"
}
(WORKSPACE / "fintech-platform/frontend/package.json").write_text(
    json.dumps(package_json, indent=2)
)

# ── The real requirements.txt (Python backend with outdated deps)
requirements_txt = """# Backend dependencies for risk engine and API
flask==1.1.2
requests==2.25.1
cryptography==3.3.1
pyyaml==5.3.1
Pillow==8.1.0
sqlalchemy==1.3.23
celery==4.4.7
redis==3.5.3
numpy==1.19.5
pandas==1.2.0
"""
(WORKSPACE / "fintech-platform/backend/requirements.txt").write_text(requirements_txt)

# ── A go.mod for an infra tool (extra complexity)
go_mod = """module github.com/fintech-platform/infra-tools

go 1.17

require (
    github.com/gin-gonic/gin v1.7.4
    github.com/go-sql-driver/mysql v1.6.0
    golang.org/x/crypto v0.0.0-20210513164829-c07d793c2f9a
    github.com/dgrijalva/jwt-go v3.2.0+incompatible
)
"""
(WORKSPACE / "fintech-platform/infra/go.mod").write_text(go_mod)

# ── Create the skills scripts directory structure (the actual tool scripts live here)
# The skill scripts already exist in the container at /workspace/scripts/
# We'll create a symlink target location and a README placeholder to simulate the env
(WORKSPACE / "fintech-platform/README.md").write_text(
    "# Fintech Platform\nSee docs/ for details.\n"
)

# ── Create the expected output directory for agent reference (empty - agent must figure it out)
(WORKSPACE / "reports").mkdir(parents=True, exist_ok=True)

print("Workspace generated successfully.")
print(f"Project directory: {PROJECT_DIR}")
print("Files created:")
for f in sorted(PROJECT_DIR.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(WORKSPACE)}")