import os
import json
import random
import string

random.seed(42)

workspace = "/workspace"

# --- Create deeply nested distractor structure ---
dirs = [
    "skill/scripts",
    "skill/assets",
    "skill/tests",
    "skill/node_modules/.cache",
    "docs/internal",
    "docs/archive",
    "infra/terraform",
    "infra/ansible/roles",
    "logs/old",
    "reports/drafts",
    "configs/deprecated",
    "configs/staging",
    "tmp/scratch",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Skill core files: package.json ---
package_json = {
    "name": "google-ai-workaround",
    "version": "1.0.0",
    "description": "Google AI access management skill for OpenClaw agents",
    "main": "scripts/main.js",
    "scripts": {
        "start": "node scripts/main.js",
        "test": "node scripts/main.js status"
    }
}
with open(os.path.join(workspace, "skill/package.json"), "w") as f:
    json.dump(package_json, f, indent=2)

# --- The main.js CLI script ---
main_js = r"""#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// --- Parse CLI args ---
const args = process.argv.slice(2);
const command = args[0];
const flags = {};
for (let i = 1; i < args.length; i++) {
  if (args[i].startsWith('--')) {
    const key = args[i].replace('--', '');
    flags[key] = args[i + 1] && !args[i + 1].startsWith('--') ? args[i + 1] : true;
    if (flags[key] !== true) i++;
  }
}

const configPath = flags['config'] || path.join(__dirname, '../assets/config-template.json');
const silent = !!flags['silent'];
const logFile = flags['log-file'] || null;

// --- Load config ---
let config = {};
try {
  config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
} catch (e) {
  config = {
    logLevel: 'INFO',
    proxies: [],
    maxSessions: 5,
    sessionTTL: 3600000,
    maxProxyFailures: 3,
    rotationStrategy: 'round-robin'
  };
}

// --- State files in assets/ ---
const assetsDir = path.join(__dirname, '../assets');
const sessionFile = path.join(assetsDir, 'sessions.json');
const proxyStateFile = path.join(assetsDir, 'proxy-state.json');

function loadSessions() {
  try { return JSON.parse(fs.readFileSync(sessionFile, 'utf8')); } catch { return []; }
}
function saveSessions(sessions) {
  fs.writeFileSync(sessionFile, JSON.stringify(sessions, null, 2));
}
function loadProxyState() {
  try { return JSON.parse(fs.readFileSync(proxyStateFile, 'utf8')); } catch {
    // Initialize from config
    return (config.proxies || []).map(p => ({ ...p, healthy: true, failures: 0, uses: 0 }));
  }
}
function saveProxyState(state) {
  fs.writeFileSync(proxyStateFile, JSON.stringify(state, null, 2));
}

function log(msg) {
  if (!silent) console.log(msg);
  if (logFile) fs.appendFileSync(logFile, msg + '\n');
}

function genId() {
  return crypto.randomUUID();
}

// --- Commands ---
function cmdStatus() {
  const sessions = loadSessions();
  const proxies = loadProxyState();
  const healthy = proxies.filter(p => p.healthy).length;
  log('=== Google AI Workaround Status ===');
  log(`Active Sessions: ${sessions.length}`);
  log(`Max Sessions: ${config.maxSessions || 5}`);
  log(`Session TTL: ${config.sessionTTL || 3600000}ms`);
  log(`Rotation Strategy: ${config.rotationStrategy || 'round-robin'}`);
  log(`Proxies Total: ${proxies.length}`);
  log(`Proxies Healthy: ${healthy}`);
  log(`Log Level: ${config.logLevel || 'INFO'}`);
  // Output JSON summary to stdout as well
  const summary = {
    activeSessions: sessions.length,
    maxSessions: config.maxSessions || 5,
    sessionTTL: config.sessionTTL || 3600000,
    rotationStrategy: config.rotationStrategy || 'round-robin',
    proxiesTotal: proxies.length,
    proxiesHealthy: healthy,
    logLevel: config.logLevel || 'INFO'
  };
  log(JSON.stringify(summary));
}

function cmdDetect() {
  log('=== Restriction Detection Analysis ===');
  log('');
  const results = [
    { code: 200, status: 'OK', restrictions: [] },
    { code: 429, status: 'RESTRICTED', restrictions: [{ type: 'Rate Limiting', severity: 'high', action: 'rotate_session' }] },
    { code: 403, status: 'RESTRICTED', restrictions: [
      { type: 'IP-based Block', severity: 'critical', action: 'switch_proxy' },
      { type: 'General Access Denied', severity: 'high', action: 'rotate_session' }
    ]},
    { code: 401, status: 'RESTRICTED', restrictions: [{ type: 'Authentication Expired', severity: 'medium', action: 'refresh_token' }] },
    { code: 503, status: 'RESTRICTED', restrictions: [{ type: 'Service Unavailable', severity: 'low', action: 'wait_retry' }] }
  ];
  for (const r of results) {
    log(`HTTP ${r.code}: ${r.status}`);
    for (const res of r.restrictions) {
      log(`  - ${res.type} (${res.severity}) -> ${res.action}`);
    }
  }
  log(JSON.stringify({ detectionResults: results }));
}

function cmdSessionCreate() {
  const sessions = loadSessions();
  if (sessions.length >= (config.maxSessions || 5)) {
    log(`ERROR: Max sessions (${config.maxSessions || 5}) reached`);
    process.exit(1);
  }
  const now = Date.now();
  const session = {
    id: genId(),
    createdAt: new Date(now).toISOString(),
    expiresAt: new Date(now + (config.sessionTTL || 3600000)).toISOString(),
    active: true
  };
  sessions.push(session);
  saveSessions(sessions);
  log(`Session created: ${session.id}`);
  log(`Expires: ${session.expiresAt}`);
  log(JSON.stringify({ session }));
}

function cmdSessionRotate() {
  const sessions = loadSessions();
  // Deactivate all, create new one
  sessions.forEach(s => s.active = false);
  const now = Date.now();
  const session = {
    id: genId(),
    createdAt: new Date(now).toISOString(),
    expiresAt: new Date(now + (config.sessionTTL || 3600000)).toISOString(),
    active: true
  };
  sessions.push(session);
  saveSessions(sessions);
  log(`Session rotated: ${session.id}`);
  log(JSON.stringify({ rotatedSession: session }));
}

function cmdSessionList() {
  const sessions = loadSessions();
  log('=== Active Sessions ===');
  const active = sessions.filter(s => s.active);
  active.forEach(s => log(`  ${s.id} expires=${s.expiresAt}`));
  log(`Total: ${sessions.length}, Active: ${active.length}`);
  log(JSON.stringify({ sessions, totalSessions: sessions.length, activeSessions: active.length }));
}

function cmdSessionRefresh() {
  const sessions = loadSessions();
  const now = Date.now();
  sessions.filter(s => s.active).forEach(s => {
    s.expiresAt = new Date(now + (config.sessionTTL || 3600000)).toISOString();
  });
  saveSessions(sessions);
  log('Sessions refreshed');
  log(JSON.stringify({ refreshed: true, sessions }));
}

function cmdSessionDestroy() {
  saveSessions([]);
  log('All sessions destroyed');
  log(JSON.stringify({ destroyed: true }));
}

function cmdProxyStatus() {
  const proxies = loadProxyState();
  log('=== Proxy Status ===');
  proxies.forEach(p => {
    log(`  ${p.protocol}://${p.host}:${p.port} healthy=${p.healthy} failures=${p.failures} uses=${p.uses}`);
  });
  log(JSON.stringify({ proxies, strategy: config.rotationStrategy || 'round-robin' }));
}

function cmdProxyHealth() {
  const proxies = loadProxyState();
  log('=== Proxy Health Check ===');
  // Simulate health: mark proxies with failures >= maxProxyFailures as unhealthy
  const maxFail = config.maxProxyFailures || 3;
  proxies.forEach(p => {
    p.healthy = p.failures < maxFail;
    log(`  ${p.host}:${p.port} -> ${p.healthy ? 'HEALTHY' : 'UNHEALTHY'} (failures=${p.failures}/${maxFail})`);
  });
  saveProxyState(proxies);
  const healthReport = { checkedAt: new Date().toISOString(), proxies, maxProxyFailures: maxFail };
  log(JSON.stringify(healthReport));
}

function cmdProxyAdd() {
  const host = flags['host'];
  const port = parseInt(flags['port'], 10);
  const protocol = flags['protocol'] || 'http';
  if (!host || !port) {
    log('ERROR: --host and --port are required');
    process.exit(1);
  }
  const proxies = loadProxyState();
  const newProxy = { host, port, protocol, healthy: true, failures: 0, uses: 0 };
  proxies.push(newProxy);
  saveProxyState(proxies);
  log(`Proxy added: ${protocol}://${host}:${port}`);
  log(JSON.stringify({ added: newProxy, totalProxies: proxies.length }));
}

function cmdDiagnostics() {
  const sessions = loadSessions();
  const proxies = loadProxyState();
  const diag = {
    timestamp: new Date().toISOString(),
    config: {
      logLevel: config.logLevel,
      maxSessions: config.maxSessions,
      sessionTTL: config.sessionTTL,
      rotationStrategy: config.rotationStrategy,
      maxProxyFailures: config.maxProxyFailures
    },
    sessions: { total: sessions.length, active: sessions.filter(s => s.active).length },
    proxies: { total: proxies.length, healthy: proxies.filter(p => p.healthy).length }
  };
  log('=== Diagnostics Report ===');
  log(JSON.stringify(diag, null, 2));
}

function cmdConfigure() {
  log('=== Current Configuration ===');
  log(JSON.stringify(config, null, 2));
}

function cmdHelp() {
  log('Usage: node scripts/main.js <command> [options]');
  log('Commands: status, detect, session-create, session-rotate, session-list, session-refresh, session-destroy, proxy-status, proxy-health, proxy-add, diagnostics, configure, help');
  log('Options: --config <path>, --silent, --log-file <path>');
}

// --- Dispatch ---
switch (command) {
  case 'status': cmdStatus(); break;
  case 'detect': cmdDetect(); break;
  case 'session-create': cmdSessionCreate(); break;
  case 'session-rotate': cmdSessionRotate(); break;
  case 'session-list': cmdSessionList(); break;
  case 'session-refresh': cmdSessionRefresh(); break;
  case 'session-destroy': cmdSessionDestroy(); break;
  case 'proxy-status': cmdProxyStatus(); break;
  case 'proxy-health': cmdProxyHealth(); break;
  case 'proxy-add': cmdProxyAdd(); break;
  case 'diagnostics': cmdDiagnostics(); break;
  case 'configure': cmdConfigure(); break;
  case 'help': cmdHelp(); break;
  default:
    log(`Unknown command: ${command}`);
    cmdHelp();
    process.exit(1);
}
"""
with open(os.path.join(workspace, "skill/scripts/main.js"), "w") as f:
    f.write(main_js)

# --- A BROKEN/INCOMPLETE config template (the agent must fix/create a proper one) ---
# This is intentionally misconfigured: wrong rotationStrategy value, missing fields, wrong TTL unit hint
broken_config = {
    "logLevel": "DEBUG",
    "proxies": [],
    "maxSessions": 3,
    "sessionTTL": 3600,
    "rotationStrategy": "round_robin",
    "maxProxyFailures": 3
}
with open(os.path.join(workspace, "skill/assets/config-template.json"), "w") as f:
    json.dump(broken_config, f, indent=2)

# --- Distractor files ---

# Fake old config
old_config = {"logLevel": "WARN", "proxies": [], "maxSessions": 2, "sessionTTL": 1800, "rotationStrategy": "sequential"}
with open(os.path.join(workspace, "configs/deprecated/old-config.json"), "w") as f:
    json.dump(old_config, f, indent=2)

# Fake staging config
staging_config = {"logLevel": "INFO", "proxies": [{"host": "staging-proxy.internal", "port": 3128}], "maxSessions": 10}
with open(os.path.join(workspace, "configs/staging/staging.json"), "w") as f:
    json.dump(staging_config, f, indent=2)

# Terraform distractor
with open(os.path.join(workspace, "infra/terraform/main.tf"), "w") as f:
    f.write('# placeholder terraform config\nresource "null_resource" "test" {}\n')

# Ansible distractor
with open(os.path.join(workspace, "infra/ansible/roles/README"), "w") as f:
    f.write("Ansible roles placeholder\n")

# Old logs
with open(os.path.join(workspace, "logs/old/access.log"), "w") as f:
    f.write("2024-01-01 HTTP 429 rate limited\n2024-01-02 HTTP 403 ip blocked\n")

# Draft report
with open(os.path.join(workspace, "reports/drafts/draft_report.txt"), "w") as f:
    f.write("TODO: fill in actual metrics\nSessions: ?\nProxies: ?\n")

# Scratch file
with open(os.path.join(workspace, "tmp/scratch/notes.txt"), "w") as f:
    f.write("rotationStrategy options: need to verify\nTTL unit: seconds? milliseconds?\n")

# Fake test file
with open(os.path.join(workspace, "skill/tests/test_placeholder.js"), "w") as f:
    f.write("// placeholder tests\nconsole.log('no tests yet');\n")

# Docs distractors
with open(os.path.join(workspace, "docs/internal/architecture.md"), "w") as f:
    f.write("# Architecture\n\nSession pool -> Proxy pool -> Google AI endpoint\n\nTODO: fill details\n")

with open(os.path.join(workspace, "docs/archive/old-approach.md"), "w") as f:
    f.write("# Old Approach\n\nManual session rotation. Deprecated.\n")

# A fake package-lock that shouldn't confuse the agent
with open(os.path.join(workspace, "skill/package-lock.json"), "w") as f:
    json.dump({"name": "google-ai-workaround", "version": "1.0.0", "lockfileVersion": 3, "packages": {"": {"name": "google-ai-workaround", "version": "1.0.0"}}}, f, indent=2)

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk(workspace):
    for fname in files:
        fpath = os.path.join(root, fname)
        print(f"  {fpath}")