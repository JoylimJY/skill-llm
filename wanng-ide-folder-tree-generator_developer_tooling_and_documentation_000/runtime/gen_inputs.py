import os
import random

random.seed(42)

workspace = "/workspace"

# Create the bespoke skill directory and index.js
skill_dir = os.path.join(workspace, "skills", "folder-tree-generator")
os.makedirs(skill_dir, exist_ok=True)

index_js = r"""
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
let useJson = false;
let maxDepth = Infinity;
let targetDir = '.';

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--json') {
    useJson = true;
  } else if (args[i] === '--depth') {
    maxDepth = parseInt(args[i + 1], 10);
    i++;
  } else if (!args[i].startsWith('--')) {
    targetDir = args[i];
  }
}

function buildTree(dirPath, depth) {
  const name = path.basename(dirPath) || dirPath;
  const stat = fs.statSync(dirPath);
  if (!stat.isDirectory()) {
    return { name, type: 'file' };
  }
  const node = { name, type: 'directory' };
  if (depth < maxDepth) {
    const entries = fs.readdirSync(dirPath).sort();
    node.children = entries.map(e => {
      const fullPath = path.join(dirPath, e);
      const s = fs.statSync(fullPath);
      if (s.isDirectory()) {
        return buildTree(fullPath, depth + 1);
      } else {
        return { name: e, type: 'file' };
      }
    });
  } else {
    node.children = [];
  }
  return node;
}

function buildAscii(dirPath, prefix, depth) {
  const entries = fs.readdirSync(dirPath).sort();
  let result = '';
  entries.forEach((entry, idx) => {
    const fullPath = path.join(dirPath, entry);
    const isLast = idx === entries.length - 1;
    const connector = isLast ? '└── ' : '├── ';
    result += prefix + connector + entry + '\n';
    const stat = fs.statSync(fullPath);
    if (stat.isDirectory() && depth < maxDepth) {
      const newPrefix = prefix + (isLast ? '    ' : '│   ');
      result += buildAscii(fullPath, newPrefix, depth + 1);
    }
  });
  return result;
}

const absDir = path.resolve(targetDir);

if (useJson) {
  const tree = buildTree(absDir, 0);
  console.log(JSON.stringify(tree, null, 2));
} else {
  console.log('.');
  console.log(buildAscii(absDir, '', 0));
}
"""

with open(os.path.join(skill_dir, "index.js"), "w") as f:
    f.write(index_js)

# Create the target project module: "legacy-payments-module"
# This is the directory the agent must scan
module_dir = os.path.join(workspace, "projects", "legacy-payments-module")

# Level 1 directories (under module_dir)
subdirs_l1 = ["src", "config", "tests", "docs", "scripts", "vendor"]
# Level 2 directories (under each l1)
subdirs_l2 = {
    "src": ["handlers", "models", "utils", "middleware"],
    "config": ["environments", "schemas"],
    "tests": ["unit", "integration", "fixtures"],
    "docs": ["api", "guides"],
    "scripts": ["deploy", "migration"],
    "vendor": ["stripe-sdk", "audit-logger", "crypto-helpers"],
}
# Level 3 directories (deeper — these should be EXCLUDED by depth=2)
subdirs_l3 = {
    "src/handlers": ["auth", "payments", "webhooks"],
    "src/models": ["entities", "dtos"],
    "src/utils": ["validators", "formatters"],
    "tests/unit": ["mocks", "stubs"],
    "tests/integration": ["scenarios"],
    "vendor/stripe-sdk": ["lib", "types"],
}

# Files at each level
files_l1 = ["package.json", "package-lock.json", ".env.example", "Makefile", "tsconfig.json", ".gitignore"]
files_l2 = {
    "src": ["index.ts", "app.ts", "bootstrap.ts"],
    "src/handlers": ["payment-handler.ts", "refund-handler.ts", "webhook-handler.ts"],
    "src/models": ["transaction.ts", "account.ts", "ledger.ts"],
    "src/utils": ["currency.ts", "validator.ts", "logger.ts"],
    "src/middleware": ["auth-middleware.ts", "rate-limiter.ts"],
    "config": ["default.json", "production.json"],
    "config/environments": ["dev.yml", "staging.yml", "prod.yml"],
    "config/schemas": ["transaction-schema.json", "account-schema.json"],
    "tests": ["jest.config.js", "setup.ts"],
    "tests/unit": ["payment-handler.test.ts", "validator.test.ts"],
    "tests/integration": ["payment-flow.test.ts"],
    "tests/fixtures": ["mock-transactions.json", "mock-accounts.json"],
    "docs": ["overview.md", "changelog.md"],
    "docs/api": ["endpoints.md", "auth.md"],
    "docs/guides": ["quickstart.md", "migration-v2.md"],
    "scripts": ["setup.sh", "cleanup.sh"],
    "scripts/deploy": ["deploy-staging.sh", "deploy-prod.sh"],
    "scripts/migration": ["v1-to-v2.sql", "v2-to-v3.sql"],
    "vendor": ["licenses.txt"],
    "vendor/stripe-sdk": ["index.js", "README.md"],
    "vendor/audit-logger": ["index.js", "config.json"],
    "vendor/crypto-helpers": ["index.js", "algorithms.js"],
}
files_l3 = {
    "src/handlers/auth": ["login-handler.ts", "logout-handler.ts"],
    "src/handlers/payments": ["create-payment.ts", "capture-payment.ts", "void-payment.ts"],
    "src/handlers/webhooks": ["stripe-webhook.ts", "paypal-webhook.ts"],
    "src/models/entities": ["Transaction.entity.ts", "Account.entity.ts"],
    "src/models/dtos": ["CreateTransactionDto.ts", "UpdateAccountDto.ts"],
    "src/utils/validators": ["amount-validator.ts", "currency-validator.ts"],
    "src/utils/formatters": ["currency-formatter.ts", "date-formatter.ts"],
    "tests/unit/mocks": ["stripe-mock.ts", "db-mock.ts"],
    "tests/unit/stubs": ["payment-stub.ts"],
    "tests/integration/scenarios": ["full-checkout.ts", "refund-flow.ts"],
    "vendor/stripe-sdk/lib": ["charge.js", "refund.js", "webhook.js"],
    "vendor/stripe-sdk/types": ["index.d.ts"],
}

# Create all directories and files
os.makedirs(module_dir, exist_ok=True)

# L1 files
for f in files_l1:
    with open(os.path.join(module_dir, f), "w") as fh:
        fh.write(f"# {f}\n")

# L1 subdirs
for d in subdirs_l1:
    os.makedirs(os.path.join(module_dir, d), exist_ok=True)
    # L1 subdir files
    for f in files_l2.get(d, []):
        with open(os.path.join(module_dir, d, f), "w") as fh:
            fh.write(f"// {f}\n")
    # L2 subdirs
    for d2 in subdirs_l2.get(d, []):
        full_d2 = os.path.join(module_dir, d, d2)
        os.makedirs(full_d2, exist_ok=True)
        key2 = f"{d}/{d2}"
        for f in files_l2.get(key2, []):
            with open(os.path.join(full_d2, f), "w") as fh:
                fh.write(f"// {f}\n")
        # L3 subdirs
        for d3 in subdirs_l3.get(key2, []):
            full_d3 = os.path.join(full_d2, d3)
            os.makedirs(full_d3, exist_ok=True)
            key3 = f"{d}/{d2}/{d3}"
            for f in files_l3.get(key3, []):
                with open(os.path.join(full_d3, f), "w") as fh:
                    fh.write(f"// {f}\n")

# Add a distractor directory at the workspace root (NOT the target)
distractor_dir = os.path.join(workspace, "projects", "active-user-service")
os.makedirs(distractor_dir, exist_ok=True)
for f in ["server.js", "routes.js", "db.js", "auth.js", "package.json"]:
    with open(os.path.join(distractor_dir, f), "w") as fh:
        fh.write(f"// {f}\n")

# Another distractor at workspace root level
for f in ["deploy.sh", "docker-compose.yml", "nginx.conf"]:
    with open(os.path.join(workspace, f), "w") as fh:
        fh.write(f"# {f}\n")

print("Workspace setup complete.")
print(f"Target module: {module_dir}")
print(f"Skill path: {skill_dir}/index.js")