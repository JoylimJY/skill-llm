import os
import json
import random

random.seed(42)

BASE = "/workspace"

# ── Directory structure ────────────────────────────────────────────────────────
dirs = [
    "packages/api-gateway/src/routes",
    "packages/api-gateway/src/middleware",
    "packages/api-gateway/tests",
    "packages/payment-engine/src/processors",
    "packages/payment-engine/src/validators",
    "packages/payment-engine/tests",
    "packages/shared-utils/src",
    "packages/shared-utils/tests",
    "packages/frontend-admin/src/components",
    "packages/frontend-admin/src/pages",
    "packages/frontend-admin/public",
    "scripts",
    "infra/terraform",
    "infra/docker",
    ".github/workflows",
    "docs/adr",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# ── Distractor files ───────────────────────────────────────────────────────────
distractors = {
    "packages/api-gateway/src/routes/payments.js": "// payment routes\nmodule.exports = {};",
    "packages/api-gateway/src/middleware/auth.js": "// auth middleware\nmodule.exports = (req, res, next) => next();",
    "packages/api-gateway/tests/payments.test.js": "test('placeholder', () => {});",
    "packages/payment-engine/src/processors/stripe.js": "// stripe processor stub",
    "packages/payment-engine/src/validators/card.js": "// card validator stub",
    "packages/payment-engine/tests/processor.test.js": "test('placeholder', () => {});",
    "packages/shared-utils/src/logger.js": "module.exports = { log: console.log };",
    "packages/frontend-admin/src/components/Dashboard.jsx": "export default function Dashboard() { return null; }",
    "packages/frontend-admin/src/pages/index.jsx": "export default function Home() { return null; }",
    "infra/terraform/main.tf": 'terraform { required_version = ">= 1.0" }',
    "infra/docker/Dockerfile.api": "FROM node:20\nWORKDIR /app",
    ".github/workflows/ci.yml": "name: CI\non: [push]\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps: []",
    "docs/adr/001-monorepo.md": "# ADR 001: Monorepo\n\nWe chose a monorepo structure.",
    "scripts/deploy.sh": "#!/bin/bash\necho 'deploying...'",
    "scripts/seed.js": "// seed script\nconsole.log('seeding');",
}
for path, content in distractors.items():
    full = os.path.join(BASE, path)
    with open(full, "w") as f:
        f.write(content)

# ── ROOT package.json (monorepo workspace root) ────────────────────────────────
root_pkg = {
    "name": "finpay-monorepo",
    "version": "1.0.0",
    "private": True,
    "workspaces": [
        "packages/api-gateway",
        "packages/payment-engine",
        "packages/shared-utils",
        "packages/frontend-admin"
    ],
    "scripts": {
        "build": "npm run build --workspaces",
        "test": "jest --passWithNoTests",
        "postinstall": "node scripts/seed.js"
    },
    "devDependencies": {
        "jest": "^27.0.0",
        "eslint": "^7.0.0",
        "typescript": "^4.0.0"
    }
}
with open(os.path.join(BASE, "package.json"), "w") as f:
    json.dump(root_pkg, f, indent=2)

# ── packages/api-gateway/package.json ─────────────────────────────────────────
# Intentional issues:
#  - lodash (runtime dep, very broad range "*")
#  - request (deprecated/abandoned runtime dep)
#  - moment (runtime, known bloat+stale)
#  - node-uuid (deprecated, superseded by uuid)
#  - postinstall hook running a script
api_pkg = {
    "name": "@finpay/api-gateway",
    "version": "0.3.1",
    "description": "API Gateway service",
    "main": "src/routes/payments.js",
    "scripts": {
        "start": "node src/routes/payments.js",
        "postinstall": "node ../../scripts/seed.js && curl http://internal-setup-server/hook || true",
        "build": "echo 'build api-gateway'"
    },
    "dependencies": {
        "express": "^4.18.2",
        "lodash": "*",
        "request": "^2.88.2",
        "moment": "^2.29.4",
        "node-uuid": "^1.4.8",
        "helmet": "^7.1.0",
        "cors": "^2.8.5"
    },
    "devDependencies": {
        "supertest": "^6.3.3"
    }
}
with open(os.path.join(BASE, "packages/api-gateway/package.json"), "w") as f:
    json.dump(api_pkg, f, indent=2)

# ── packages/payment-engine/package.json ──────────────────────────────────────
# Issues:
#  - crypto (built-in node module listed as dep — unnecessary/incorrect)
#  - underscore (duplicates lodash)
#  - uuid (correct replacement for node-uuid — here it's listed alongside node-uuid in another package, showing duplication)
#  - Very old version pin for validator: "5.7.0" (latest is 13+)
#  - broad range: "colors": "*"  (supply-chain risk history)
payment_pkg = {
    "name": "@finpay/payment-engine",
    "version": "0.2.0",
    "description": "Core payment processing engine",
    "main": "src/processors/stripe.js",
    "scripts": {
        "start": "node src/processors/stripe.js",
        "build": "echo 'build payment-engine'"
    },
    "dependencies": {
        "stripe": "^14.0.0",
        "validator": "5.7.0",
        "underscore": "^1.13.6",
        "uuid": "^9.0.0",
        "crypto": "^1.0.1",
        "colors": "*",
        "axios": "^0.21.1"
    },
    "devDependencies": {
        "jest": "^27.0.0"
    }
}
with open(os.path.join(BASE, "packages/payment-engine/package.json"), "w") as f:
    json.dump(payment_pkg, f, indent=2)

# ── packages/shared-utils/package.json ────────────────────────────────────────
# Issues:
#  - lodash again (same dep as api-gateway — duplication across workspace)
#  - winston pinned to very old "2.4.7"
shared_pkg = {
    "name": "@finpay/shared-utils",
    "version": "0.1.0",
    "description": "Shared utilities",
    "main": "src/logger.js",
    "scripts": {
        "build": "echo 'build shared-utils'"
    },
    "dependencies": {
        "lodash": "^4.17.21",
        "winston": "2.4.7",
        "dotenv": "^16.0.3"
    },
    "devDependencies": {}
}
with open(os.path.join(BASE, "packages/shared-utils/package.json"), "w") as f:
    json.dump(shared_pkg, f, indent=2)

# ── packages/frontend-admin/package.json ──────────────────────────────────────
# Issues:
#  - react-scripts (CRA) at "4.0.3" — known vulns, outdated
#  - node-sass (deprecated — superseded by sass)
#  - serialize-javascript old version with known RCE
frontend_pkg = {
    "name": "@finpay/frontend-admin",
    "version": "0.1.0",
    "description": "Admin frontend",
    "private": True,
    "scripts": {
        "start": "react-scripts start",
        "build": "react-scripts build",
        "test": "react-scripts test"
    },
    "dependencies": {
        "react": "^18.2.0",
        "react-dom": "^18.2.0",
        "react-scripts": "4.0.3",
        "node-sass": "^7.0.3",
        "serialize-javascript": "2.1.2",
        "axios": "^0.21.1"
    },
    "devDependencies": {
        "@testing-library/react": "^13.0.0"
    }
}
with open(os.path.join(BASE, "packages/frontend-admin/package.json"), "w") as f:
    json.dump(frontend_pkg, f, indent=2)

# ── Install actual node_modules so npm ls and npm audit work ──────────────────
# We'll do minimal installs during setup_script, but create package-lock stubs here
# so the structure is recognizable. Full install is done in setup_script.

print("Workspace generation complete.")
print("Files created:")
for root, dirs_list, files in os.walk(BASE):
    for fname in files:
        print(os.path.join(root, fname).replace(BASE + "/", ""))