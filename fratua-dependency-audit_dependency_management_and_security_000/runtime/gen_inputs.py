import os
import json
import random

random.seed(42)

BASE = "/workspace"

# --- Directory structure ---
dirs = [
    "src/api/routes",
    "src/api/middleware",
    "src/api/controllers",
    "src/data_processor/transforms",
    "src/data_processor/loaders",
    "src/data_processor/validators",
    "src/shared/utils",
    "src/shared/config",
    "tests/unit/api",
    "tests/unit/data_processor",
    "tests/integration",
    "scripts",
    "docs",
    ".github/workflows",
]

for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# --- package.json with intentionally outdated/vulnerable packages ---
# lodash 4.17.19 has known prototype pollution CVE
# express 4.17.1 is outdated (latest is 4.x.x higher)
# moment is a well-known "unused but listed" dep that we won't import anywhere
# dotenv is used in code
# axios is outdated
package_json = {
    "name": "finpay-api",
    "version": "2.3.1",
    "description": "FinPay backend API service",
    "main": "src/api/index.js",
    "scripts": {
        "start": "node src/api/index.js",
        "test": "jest"
    },
    "dependencies": {
        "express": "4.17.1",
        "lodash": "4.17.19",
        "axios": "0.21.1",
        "dotenv": "8.2.0",
        "moment": "2.24.0",
        "jsonwebtoken": "8.5.1",
        "cors": "2.8.5"
    },
    "devDependencies": {
        "jest": "26.6.3",
        "nodemon": "2.0.6"
    }
}

with open(os.path.join(BASE, "package.json"), "w") as f:
    json.dump(package_json, f, indent=2)

# --- package-lock.json to make npm audit work ---
# We'll create a minimal one so npm audit can function
# In practice the agent should run npm install first or we pre-install
# Let's create a node_modules scenario by installing after setup

# --- requirements.txt with outdated/vulnerable Python packages ---
# Pillow 8.0.0 has known CVEs
# requests 2.20.0 is outdated and has CVE
# numpy is used, flask is unused
requirements_txt = """flask==1.1.2
requests==2.20.0
numpy==1.21.0
pillow==8.0.0
pyyaml==5.3.1
cryptography==2.8
pandas==1.1.0
"""

with open(os.path.join(BASE, "requirements.txt"), "w") as f:
    f.write(requirements_txt)

# --- Node.js source files (JS) ---
# Uses: express, axios, dotenv, jsonwebtoken, cors, lodash
# Does NOT use: moment (unused dep)

api_index = """\
const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const authRoutes = require('./routes/auth');
const paymentRoutes = require('./routes/payments');

dotenv.config();
const app = express();
app.use(cors());
app.use(express.json());
app.use('/auth', authRoutes);
app.use('/payments', paymentRoutes);

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`FinPay API running on port ${PORT}`));
module.exports = app;
"""

with open(os.path.join(BASE, "src/api/index.js"), "w") as f:
    f.write(api_index)

auth_route = """\
const express = require('express');
const jwt = require('jsonwebtoken');
const _ = require('lodash');
const router = express.Router();

router.post('/login', (req, res) => {
    const user = _.pick(req.body, ['username', 'password']);
    const token = jwt.sign({ user }, process.env.JWT_SECRET, { expiresIn: '1h' });
    res.json({ token });
});

module.exports = router;
"""

with open(os.path.join(BASE, "src/api/routes/auth.js"), "w") as f:
    f.write(auth_route)

payments_route = """\
const express = require('express');
const axios = require('axios');
const router = express.Router();

router.post('/process', async (req, res) => {
    try {
        const result = await axios.post(process.env.PAYMENT_GATEWAY_URL, req.body);
        res.json(result.data);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

module.exports = router;
"""

with open(os.path.join(BASE, "src/api/routes/payments.js"), "w") as f:
    f.write(payments_route)

middleware_auth = """\
const jwt = require('jsonwebtoken');

module.exports = (req, res, next) => {
    const token = req.headers['authorization'];
    if (!token) return res.status(401).json({ error: 'Unauthorized' });
    jwt.verify(token, process.env.JWT_SECRET, (err, decoded) => {
        if (err) return res.status(403).json({ error: 'Forbidden' });
        req.user = decoded;
        next();
    });
};
"""

with open(os.path.join(BASE, "src/api/middleware/auth.js"), "w") as f:
    f.write(middleware_auth)

controller_payments = """\
const _ = require('lodash');

exports.validatePayload = (payload) => {
    return _.pick(payload, ['amount', 'currency', 'recipient']);
};
"""

with open(os.path.join(BASE, "src/api/controllers/payments.js"), "w") as f:
    f.write(controller_payments)

# --- Python source files ---
# Uses: requests, numpy, pandas, pyyaml, cryptography
# Does NOT use: flask (unused dep), pillow (unused dep)

data_loader = """\
import requests
import numpy as np
import pandas as pd

def fetch_transactions(url):
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    return pd.DataFrame(data)

def compute_stats(df):
    return {
        'mean': float(np.mean(df['amount'])),
        'std': float(np.std(df['amount'])),
    }
"""

with open(os.path.join(BASE, "src/data_processor/loaders/transaction_loader.py"), "w") as f:
    f.write(data_loader)

data_transform = """\
import pandas as pd
import yaml

def normalize_currency(df, config_path='config.yaml'):
    with open(config_path) as f:
        cfg = yaml.safe_load(f)
    rates = cfg.get('exchange_rates', {})
    df['amount_usd'] = df.apply(
        lambda row: row['amount'] / rates.get(row['currency'], 1.0), axis=1
    )
    return df
"""

with open(os.path.join(BASE, "src/data_processor/transforms/currency.py"), "w") as f:
    f.write(data_transform)

data_validator = """\
from cryptography.fernet import Fernet

def encrypt_pii(data: str, key: bytes) -> bytes:
    f = Fernet(key)
    return f.encrypt(data.encode())

def decrypt_pii(token: bytes, key: bytes) -> str:
    f = Fernet(key)
    return f.decrypt(token).decode()
"""

with open(os.path.join(BASE, "src/data_processor/validators/pii.py"), "w") as f:
    f.write(data_validator)

shared_utils = """\
import numpy as np

def batch_chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

def moving_average(data, window=5):
    return np.convolve(data, np.ones(window)/window, mode='valid').tolist()
"""

with open(os.path.join(BASE, "src/shared/utils/math_utils.py"), "w") as f:
    f.write(shared_utils)

# --- Test files ---
test_api = """\
const request = require('supertest');
const app = require('../../src/api/index');

describe('Auth routes', () => {
    it('should return 400 for missing credentials', async () => {
        const res = await request(app).post('/auth/login').send({});
        expect(res.status).toBe(400);
    });
});
"""

with open(os.path.join(BASE, "tests/unit/api/auth.test.js"), "w") as f:
    f.write(test_api)

test_data = """\
import pytest
import numpy as np
from src.data_processor.loaders.transaction_loader import compute_stats
import pandas as pd

def test_compute_stats():
    df = pd.DataFrame({'amount': [100, 200, 300]})
    stats = compute_stats(df)
    assert abs(stats['mean'] - 200.0) < 0.01
"""

with open(os.path.join(BASE, "tests/unit/data_processor/test_loader.py"), "w") as f:
    f.write(test_data)

# --- Distractor files ---
distractor_env = """\
PORT=3000
JWT_SECRET=supersecret
PAYMENT_GATEWAY_URL=https://gateway.finpay.internal
DATABASE_URL=postgres://user:pass@localhost/finpay
"""

with open(os.path.join(BASE, ".env.example"), "w") as f:
    f.write(distractor_env)

dockerfile_content = """\
FROM node:20-bullseye
WORKDIR /app
COPY . .
RUN npm install
RUN pip3 install -r requirements.txt
CMD ["npm", "start"]
"""

with open(os.path.join(BASE, "Dockerfile.app"), "w") as f:
    f.write(dockerfile_content)

github_workflow = """\
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: npm test
"""

with open(os.path.join(BASE, ".github/workflows/ci.yml"), "w") as f:
    f.write(github_workflow)

config_yaml = """\
exchange_rates:
  EUR: 0.92
  GBP: 0.78
  JPY: 149.5
database:
  pool_size: 10
  timeout: 30
"""

with open(os.path.join(BASE, "src/shared/config/config.yaml"), "w") as f:
    f.write(config_yaml)

scripts_deploy = """\
#!/bin/bash
set -e
echo "Deploying FinPay API..."
npm ci
npm test
npm run build
echo "Deploy complete."
"""

with open(os.path.join(BASE, "scripts/deploy.sh"), "w") as f:
    f.write(scripts_deploy)
os.chmod(os.path.join(BASE, "scripts/deploy.sh"), 0o755)

docs_arch = """\
# FinPay Architecture

## Components
- **API Layer**: Node.js/Express REST API
- **Data Processor**: Python service for transaction analytics
- **Database**: PostgreSQL 14

## Data Flow
1. Client → API → Payment Gateway
2. Transactions → Data Processor → Analytics DB
"""

with open(os.path.join(BASE, "docs/architecture.md"), "w") as f:
    f.write(docs_arch)

integration_test = """\
import requests

BASE_URL = 'http://localhost:3000'

def test_health():
    resp = requests.get(f'{BASE_URL}/health')
    assert resp.status_code == 200
"""

with open(os.path.join(BASE, "tests/integration/test_e2e.py"), "w") as f:
    f.write(integration_test)

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk(BASE):
    for fname in files:
        fpath = os.path.join(root, fname)
        print(f"  {fpath}")