import os
import json
import random
import textwrap

random.seed(42)

BASE = "/workspace"

# ── Skill scaffold ──────────────────────────────────────────────────────────
skill_dir = os.path.join(BASE, "skills", "config-validator")
os.makedirs(skill_dir, exist_ok=True)

# The actual validator index.js  (the skill's script that already "exists in the workspace")
validator_src = r"""
#!/usr/bin/env node
'use strict';

const fs   = require('fs');
const path = require('path');

const ROOT    = process.cwd();
const FIX     = process.argv.includes('--fix');
const results = [];

// ── helpers ──────────────────────────────────────────────────────────────────
function pass(check, detail='')  { results.push({ check, status:'PASS', detail }); }
function fail(check, detail='')  { results.push({ check, status:'FAIL', detail }); }

// ── 1. .env checks ───────────────────────────────────────────────────────────
const REQUIRED_ENV_VARS = [
  'OPENCLAW_API_KEY',
  'OPENCLAW_ENV',
  'OPENCLAW_LOG_LEVEL',
  'OPENCLAW_DB_URI',
];

const envPath = path.join(ROOT, '.env');
if (!fs.existsSync(envPath)) {
  if (FIX) {
    const template = REQUIRED_ENV_VARS.map(v => `${v}=PLACEHOLDER`).join('\n') + '\n';
    fs.writeFileSync(envPath, template, 'utf8');
    fail('.env exists', 'Created from template – fill in real values');
  } else {
    fail('.env exists', '.env file is missing');
  }
} else {
  pass('.env exists');
  const raw = fs.readFileSync(envPath, 'utf8');
  const defined = {};
  for (const line of raw.split('\n')) {
    const m = line.match(/^\s*([A-Z_][A-Z0-9_]*)\s*=\s*(.*)$/);
    if (m) defined[m[1]] = m[2].trim();
  }
  for (const v of REQUIRED_ENV_VARS) {
    if (!defined[v]) {
      fail(`.env: ${v} present`, `${v} is missing`);
    } else if (defined[v] === '' || defined[v] === 'PLACEHOLDER') {
      fail(`.env: ${v} present`, `${v} has no real value (empty or PLACEHOLDER)`);
    } else {
      pass(`.env: ${v} present`);
    }
  }
  // OPENCLAW_ENV must be one of: development | staging | production
  if (defined['OPENCLAW_ENV'] && !['development','staging','production'].includes(defined['OPENCLAW_ENV'])) {
    fail('.env: OPENCLAW_ENV valid', `Value '${defined['OPENCLAW_ENV']}' is not allowed`);
  } else if (defined['OPENCLAW_ENV']) {
    pass('.env: OPENCLAW_ENV valid');
  }
  // OPENCLAW_LOG_LEVEL must be one of: debug | info | warn | error
  if (defined['OPENCLAW_LOG_LEVEL'] && !['debug','info','warn','error'].includes(defined['OPENCLAW_LOG_LEVEL'])) {
    fail('.env: OPENCLAW_LOG_LEVEL valid', `Value '${defined['OPENCLAW_LOG_LEVEL']}' is not allowed`);
  } else if (defined['OPENCLAW_LOG_LEVEL']) {
    pass('.env: OPENCLAW_LOG_LEVEL valid');
  }
}

// ── 2. openclaw.json checks ──────────────────────────────────────────────────
const OPENCLAW_TEMPLATE = {
  version: '1.0.0',
  service: { name: 'openclaw-core', port: 8080, healthEndpoint: '/health' },
  feeds: [],
  retryPolicy: { maxRetries: 3, backoffMs: 500 },
  auth: { provider: 'jwt', secretEnvVar: 'OPENCLAW_API_KEY' },
};

const ocPath = path.join(ROOT, 'openclaw.json');
if (!fs.existsSync(ocPath)) {
  if (FIX) {
    fs.writeFileSync(ocPath, JSON.stringify(OPENCLAW_TEMPLATE, null, 2), 'utf8');
    fail('openclaw.json exists', 'Created from template – review values');
  } else {
    fail('openclaw.json exists', 'openclaw.json is missing');
  }
} else {
  pass('openclaw.json exists');
  let cfg;
  try {
    cfg = JSON.parse(fs.readFileSync(ocPath, 'utf8'));
  } catch(e) {
    fail('openclaw.json parseable', e.message);
    cfg = null;
  }
  if (cfg !== null) {
    pass('openclaw.json parseable');
    // version must be a semver string
    if (typeof cfg.version !== 'string' || !/^\d+\.\d+\.\d+$/.test(cfg.version)) {
      fail('openclaw.json: version', `version must be semver string, got: ${JSON.stringify(cfg.version)}`);
    } else { pass('openclaw.json: version'); }

    // service block
    if (!cfg.service || typeof cfg.service !== 'object') {
      fail('openclaw.json: service block', 'service block missing or not an object');
    } else {
      pass('openclaw.json: service block');
      if (typeof cfg.service.name !== 'string' || cfg.service.name.trim() === '') {
        fail('openclaw.json: service.name', 'service.name must be a non-empty string');
      } else { pass('openclaw.json: service.name'); }
      if (typeof cfg.service.port !== 'number' || cfg.service.port < 1 || cfg.service.port > 65535) {
        fail('openclaw.json: service.port', `service.port must be an integer 1-65535, got: ${JSON.stringify(cfg.service.port)}`);
      } else { pass('openclaw.json: service.port'); }
      if (typeof cfg.service.healthEndpoint !== 'string' || !cfg.service.healthEndpoint.startsWith('/')) {
        fail('openclaw.json: service.healthEndpoint', 'healthEndpoint must be a string starting with /');
      } else { pass('openclaw.json: service.healthEndpoint'); }
    }

    // feeds must be an array
    if (!Array.isArray(cfg.feeds)) {
      fail('openclaw.json: feeds', 'feeds must be an array');
    } else { pass('openclaw.json: feeds'); }

    // retryPolicy
    if (!cfg.retryPolicy || typeof cfg.retryPolicy !== 'object') {
      fail('openclaw.json: retryPolicy', 'retryPolicy block missing');
    } else {
      pass('openclaw.json: retryPolicy');
      if (typeof cfg.retryPolicy.maxRetries !== 'number' || cfg.retryPolicy.maxRetries < 0) {
        fail('openclaw.json: retryPolicy.maxRetries', `must be non-negative number, got: ${JSON.stringify(cfg.retryPolicy.maxRetries)}`);
      } else { pass('openclaw.json: retryPolicy.maxRetries'); }
      if (typeof cfg.retryPolicy.backoffMs !== 'number' || cfg.retryPolicy.backoffMs < 0) {
        fail('openclaw.json: retryPolicy.backoffMs', `must be non-negative number, got: ${JSON.stringify(cfg.retryPolicy.backoffMs)}`);
      } else { pass('openclaw.json: retryPolicy.backoffMs'); }
    }

    // auth block
    if (!cfg.auth || typeof cfg.auth !== 'object') {
      fail('openclaw.json: auth', 'auth block missing');
    } else {
      pass('openclaw.json: auth');
      if (!['jwt','oauth2','apikey'].includes(cfg.auth.provider)) {
        fail('openclaw.json: auth.provider', `provider must be jwt|oauth2|apikey, got: ${JSON.stringify(cfg.auth.provider)}`);
      } else { pass('openclaw.json: auth.provider'); }
      if (typeof cfg.auth.secretEnvVar !== 'string' || cfg.auth.secretEnvVar.trim() === '') {
        fail('openclaw.json: auth.secretEnvVar', 'secretEnvVar must be a non-empty string');
      } else { pass('openclaw.json: auth.secretEnvVar'); }
    }
  }
}

// ── 3. package.json vs installed modules ─────────────────────────────────────
const pkgPath = path.join(ROOT, 'package.json');
if (!fs.existsSync(pkgPath)) {
  if (FIX) {
    const tmpl = { name:'openclaw-core', version:'1.0.0', dependencies:{} };
    fs.writeFileSync(pkgPath, JSON.stringify(tmpl, null, 2), 'utf8');
    fail('package.json exists', 'Created from template');
  } else {
    fail('package.json exists', 'package.json missing');
  }
} else {
  pass('package.json exists');
  let pkg;
  try { pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8')); }
  catch(e) { fail('package.json parseable', e.message); pkg = null; }
  if (pkg !== null) {
    pass('package.json parseable');
    const deps = Object.keys(pkg.dependencies || {});
    const nmDir = path.join(ROOT, 'node_modules');
    for (const dep of deps) {
      const depPath = path.join(nmDir, dep);
      if (!fs.existsSync(depPath)) {
        fail(`package.json dep installed: ${dep}`, `${dep} listed in package.json but not found in node_modules`);
      } else {
        pass(`package.json dep installed: ${dep}`);
      }
    }
  }
}

// ── output ───────────────────────────────────────────────────────────────────
const failed = results.filter(r => r.status === 'FAIL');
console.log(JSON.stringify({ summary: { total: results.length, passed: results.length - failed.length, failed: failed.length }, results }, null, 2));
process.exitCode = failed.length > 0 ? 1 : 0;
"""

with open(os.path.join(skill_dir, "index.js"), "w") as f:
    f.write(validator_src)

# ── Project root distractor files ───────────────────────────────────────────
# Realistic fintech project structure with at least 10 distractor files

dirs = [
    "src/feeds",
    "src/auth",
    "src/signals",
    "src/utils",
    "tests/unit",
    "tests/integration",
    "docs/api",
    "scripts",
    "config/templates",
    "logs",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

distractor_files = {
    "src/feeds/aggregator.js": "// feed aggregation logic\nmodule.exports = {};\n",
    "src/feeds/parser.js": "// parser stub\nconst parse = (raw) => raw;\nmodule.exports = { parse };\n",
    "src/auth/jwt.js": "// jwt helper\nconst verify = (token, secret) => true;\nmodule.exports = { verify };\n",
    "src/signals/detector.js": "// signal detector\nmodule.exports = class Detector {};\n",
    "src/utils/logger.js": "// logger\nmodule.exports = { info: console.log, error: console.error };\n",
    "tests/unit/aggregator.test.js": "// placeholder test\ntest('stub', () => expect(1).toBe(1));\n",
    "tests/integration/pipeline.test.js": "// integration test stub\n",
    "docs/api/signals.md": "# Signals API\nDocumentation placeholder.\n",
    "scripts/deploy.sh": "#!/bin/bash\necho 'deploy script'\n",
    "scripts/seed_db.js": "// seed script\nconsole.log('seeding...');\n",
    "config/templates/openclaw.template.json": json.dumps({
        "version": "1.0.0",
        "service": {"name": "openclaw-core", "port": 8080, "healthEndpoint": "/health"},
        "feeds": [],
        "retryPolicy": {"maxRetries": 3, "backoffMs": 500},
        "auth": {"provider": "jwt", "secretEnvVar": "OPENCLAW_API_KEY"}
    }, indent=2) + "\n",
    "logs/app.log": "[2024-01-15 09:00:00] INFO  Server started\n[2024-01-15 09:01:00] WARN  Missing config\n",
    "src/utils/retry.js": "// retry helper\nconst retry = async (fn, n) => fn();\nmodule.exports = { retry };\n",
    ".gitignore": "node_modules/\nlogs/\n.env\n",
    "Makefile": "test:\n\tnpm test\nlint:\n\tnpx eslint src/\n",
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(BASE, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# ── THE BROKEN STATE ────────────────────────────────────────────────────────
# 1. .env: EXISTS but has wrong values for OPENCLAW_ENV and OPENCLAW_LOG_LEVEL,
#    and OPENCLAW_DB_URI is missing entirely.
env_content = textwrap.dedent("""\
    OPENCLAW_API_KEY=sk-live-abc123def456
    OPENCLAW_ENV=local_dev
    OPENCLAW_LOG_LEVEL=verbose
    """)
with open(os.path.join(BASE, ".env"), "w") as f:
    f.write(env_content)

# 2. openclaw.json: EXISTS but has multiple structural problems:
#    - version is an integer not a semver string
#    - service.port is a string "8080" not a number
#    - service.healthEndpoint is missing the leading slash
#    - retryPolicy.maxRetries is negative
#    - auth.provider is "basic" (not in allowed list)
broken_openclaw = {
    "version": 1,
    "service": {
        "name": "openclaw-core",
        "port": "8080",
        "healthEndpoint": "health"
    },
    "feeds": [],
    "retryPolicy": {
        "maxRetries": -1,
        "backoffMs": 500
    },
    "auth": {
        "provider": "basic",
        "secretEnvVar": "OPENCLAW_API_KEY"
    }
}
with open(os.path.join(BASE, "openclaw.json"), "w") as f:
    json.dump(broken_openclaw, f, indent=2)

# 3. package.json: EXISTS but lists two dependencies that are NOT installed
broken_pkg = {
    "name": "openclaw-core",
    "version": "1.0.0",
    "description": "OpenClaw trading signal aggregator",
    "main": "src/index.js",
    "scripts": {
        "start": "node src/index.js",
        "test": "jest"
    },
    "dependencies": {
        "axios": "^1.6.0",
        "dotenv": "^16.0.0"
    },
    "devDependencies": {
        "jest": "^29.0.0"
    }
}
with open(os.path.join(BASE, "package.json"), "w") as f:
    json.dump(broken_pkg, f, indent=2)

# node_modules does NOT exist → both deps will fail the installed check
# (intentionally omitted)

print("Workspace generated successfully.")
print("Broken state summary:")
print("  .env           → OPENCLAW_ENV=local_dev (invalid), OPENCLAW_LOG_LEVEL=verbose (invalid), OPENCLAW_DB_URI missing")
print("  openclaw.json  → version is int, port is string, healthEndpoint missing slash, maxRetries negative, auth.provider invalid")
print("  package.json   → axios & dotenv listed but node_modules absent")