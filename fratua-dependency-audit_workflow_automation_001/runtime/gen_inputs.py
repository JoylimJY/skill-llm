import os
import json
import random

random.seed(42)

BASE = "/workspace"

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "api-gateway/src/routes",
    "api-gateway/src/middleware",
    "api-gateway/src/utils",
    "api-gateway/tests",
    "risk-scorer/src",
    "risk-scorer/tests",
    "risk-scorer/models",
    "infra/docker",
    "infra/k8s",
    "docs",
    "scripts",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# ── package.json (Node.js API gateway) ──────────────────────────────────────
# lodash 4.17.19 has known vuln (CVE-2021-23337); fixed in 4.17.21
# express 4.18.2 → latest 5.0.1 (major/breaking)
# axios 1.3.4 → latest 1.7.2 (minor)
# moment is listed but NEVER imported → unused
# helmet is used
package_json = {
    "name": "fintech-api-gateway",
    "version": "1.0.0",
    "description": "Fintech API Gateway service",
    "main": "src/index.js",
    "scripts": {
        "start": "node src/index.js",
        "test": "jest"
    },
    "dependencies": {
        "express": "4.18.2",
        "lodash": "4.17.19",
        "axios": "1.3.4",
        "helmet": "7.0.0",
        "moment": "2.29.4",
        "jsonwebtoken": "8.5.1"
    },
    "devDependencies": {
        "jest": "29.5.0",
        "eslint": "8.40.0"
    }
}

with open(os.path.join(BASE, "api-gateway", "package.json"), "w") as f:
    json.dump(package_json, f, indent=2)

# package-lock.json stub (so npm doesn't complain)
package_lock = {
    "name": "fintech-api-gateway",
    "version": "1.0.0",
    "lockfileVersion": 3,
    "requires": True,
    "packages": {
        "": {
            "name": "fintech-api-gateway",
            "version": "1.0.0",
            "dependencies": {
                "express": "4.18.2",
                "lodash": "4.17.19",
                "axios": "1.3.4",
                "helmet": "7.0.0",
                "moment": "2.29.4",
                "jsonwebtoken": "8.5.1"
            }
        }
    }
}
with open(os.path.join(BASE, "api-gateway", "package-lock.json"), "w") as f:
    json.dump(package_lock, f, indent=2)

# ── Node.js source files (api-gateway) ──────────────────────────────────────
index_js = """\
const express = require('express');
const helmet = require('helmet');
const { verifyToken } = require('./middleware/auth');
const routes = require('./routes/transactions');

const app = express();
app.use(helmet());
app.use(express.json());
app.use('/api', verifyToken, routes);

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Gateway running on ${PORT}`));
"""
with open(os.path.join(BASE, "api-gateway", "src", "index.js"), "w") as f:
    f.write(index_js)

auth_js = """\
const jwt = require('jsonwebtoken');

function verifyToken(req, res, next) {
  const token = req.headers['authorization'];
  if (!token) return res.status(401).json({ error: 'No token' });
  try {
    req.user = jwt.verify(token, process.env.JWT_SECRET || 'dev-secret');
    next();
  } catch (e) {
    res.status(403).json({ error: 'Invalid token' });
  }
}

module.exports = { verifyToken };
"""
with open(os.path.join(BASE, "api-gateway", "src", "middleware", "auth.js"), "w") as f:
    f.write(auth_js)

transactions_js = """\
const express = require('express');
const _ = require('lodash');
const axios = require('axios');

const router = express.Router();

router.get('/transactions', async (req, res) => {
  const sorted = _.sortBy(req.body.transactions, 'amount');
  const riskResp = await axios.post('http://risk-scorer:5000/score', { transactions: sorted });
  res.json(riskResp.data);
});

module.exports = router;
"""
with open(os.path.join(BASE, "api-gateway", "src", "routes", "transactions.js"), "w") as f:
    f.write(transactions_js)

utils_js = """\
// Utility helpers
function formatCurrency(amount, currency = 'USD') {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(amount);
}

module.exports = { formatCurrency };
// NOTE: moment is not imported here or anywhere — it was added speculatively but never used
"""
with open(os.path.join(BASE, "api-gateway", "src", "utils", "helpers.js"), "w") as f:
    f.write(utils_js)

test_gateway_js = """\
const { formatCurrency } = require('../src/utils/helpers');

test('formatCurrency works', () => {
  expect(formatCurrency(100)).toBe('$100.00');
});
"""
with open(os.path.join(BASE, "api-gateway", "tests", "gateway.test.js"), "w") as f:
    f.write(test_gateway_js)

# ── requirements.txt (Python risk scorer) ───────────────────────────────────
# numpy 1.23.0 → latest 1.26.4 (minor/patch)
# scikit-learn 1.0.2 → latest 1.4.2 (minor)
# flask 2.2.2 → latest 3.0.3 (major/breaking)
# cryptography 38.0.1 has known vulns; fixed in 41.0.0+
# pandas is listed but NOT imported in any .py file → unused
requirements_txt = """\
numpy==1.23.0
scikit-learn==1.0.2
flask==2.2.2
cryptography==38.0.1
pandas==1.5.3
requests==2.28.1
"""
with open(os.path.join(BASE, "risk-scorer", "requirements.txt"), "w") as f:
    f.write(requirements_txt)

# ── Python source files (risk-scorer) ───────────────────────────────────────
scorer_py = """\
import numpy as np
from sklearn.ensemble import IsolationForest
from flask import Flask, request, jsonify
from cryptography.fernet import Fernet
import requests

app = Flask(__name__)
model = IsolationForest(contamination=0.05, random_state=42)

ENCRYPTION_KEY = Fernet.generate_key()
cipher = Fernet(ENCRYPTION_KEY)

@app.route('/score', methods=['POST'])
def score():
    data = request.json
    amounts = np.array([t['amount'] for t in data['transactions']]).reshape(-1, 1)
    scores = model.fit_predict(amounts)
    encrypted = cipher.encrypt(str(scores.tolist()).encode())
    r = requests.post('http://audit-log:8080/log', json={'event': 'scoring_run'})
    return jsonify({'risk_scores': scores.tolist(), 'audit_ref': encrypted.decode()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
"""
with open(os.path.join(BASE, "risk-scorer", "src", "scorer.py"), "w") as f:
    f.write(scorer_py)

model_utils_py = """\
import numpy as np

def normalize_amounts(amounts):
    \"\"\"Normalize transaction amounts to [0, 1] range.\"\"\"
    arr = np.array(amounts, dtype=float)
    mn, mx = arr.min(), arr.max()
    if mx == mn:
        return np.zeros_like(arr)
    return (arr - mn) / (mx - mn)
"""
with open(os.path.join(BASE, "risk-scorer", "src", "model_utils.py"), "w") as f:
    f.write(model_utils_py)

test_scorer_py = """\
import numpy as np
from src.model_utils import normalize_amounts

def test_normalize_basic():
    result = normalize_amounts([0, 50, 100])
    assert list(result) == [0.0, 0.5, 1.0]
"""
with open(os.path.join(BASE, "risk-scorer", "tests", "test_scorer.py"), "w") as f:
    f.write(test_scorer_py)

# ── Distractor / context files ───────────────────────────────────────────────
dockerfile_content = """\
FROM node:18-slim AS gateway
WORKDIR /app
COPY api-gateway/package*.json ./
RUN npm ci --production
COPY api-gateway/src ./src
CMD ["node", "src/index.js"]

FROM python:3.11-slim AS scorer
WORKDIR /app
COPY risk-scorer/requirements.txt .
RUN pip install -r requirements.txt
COPY risk-scorer/src ./src
CMD ["python", "src/scorer.py"]
"""
with open(os.path.join(BASE, "infra", "docker", "Dockerfile"), "w") as f:
    f.write(dockerfile_content)

k8s_yaml = """\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fintech-gateway
spec:
  replicas: 2
  selector:
    matchLabels:
      app: gateway
  template:
    metadata:
      labels:
        app: gateway
    spec:
      containers:
      - name: gateway
        image: fintech/gateway:1.0.0
        ports:
        - containerPort: 3000
"""
with open(os.path.join(BASE, "infra", "k8s", "gateway-deployment.yaml"), "w") as f:
    f.write(k8s_yaml)

ci_yml = """\
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Node tests
        working-directory: api-gateway
        run: npm test
      - name: Python tests
        working-directory: risk-scorer
        run: python -m pytest tests/
"""
with open(os.path.join(BASE, ".github_ci.yml"), "w") as f:
    f.write(ci_yml)

# scripts/deploy.sh
deploy_sh = """\
#!/bin/bash
set -e
echo "Deploying fintech services..."
kubectl apply -f infra/k8s/
echo "Done."
"""
with open(os.path.join(BASE, "scripts", "deploy.sh"), "w") as f:
    f.write(deploy_sh)

# docs/architecture.md
arch_md = """\
# Fintech Platform Architecture

## Services
- **api-gateway** (Node.js): Handles auth, routing, and external API calls
- **risk-scorer** (Python): ML-based transaction risk scoring

## Data Flow
Client → API Gateway → Risk Scorer → Audit Log
"""
with open(os.path.join(BASE, "docs", "architecture.md"), "w") as f:
    f.write(arch_md)

# risk-scorer/models placeholder
with open(os.path.join(BASE, "risk-scorer", "models", ".gitkeep"), "w") as f:
    f.write("")

print("Workspace generated successfully.")
print("Structure:")
for root, dirs_list, files in os.walk(BASE):
    level = root.replace(BASE, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f'{indent}{os.path.basename(root)}/')
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        print(f'{subindent}{file}')