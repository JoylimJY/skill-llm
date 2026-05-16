import os
import json
import random

random.seed(42)

workspace = "/workspace"

# --- Build a realistic, deeply nested distractor directory structure ---
distractor_dirs = [
    "scripts",
    "contracts/core",
    "contracts/mocks",
    "config/networks",
    "config/proposals",
    "deployments/mainnet",
    "deployments/testnet",
    "test/unit",
    "test/integration",
    "docs/api",
    "logs/archive",
    "cache/.artifacts",
]

for d in distractor_dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "contracts/core/RiskLP.sol": "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.20;\ncontract RiskLP {}",
    "contracts/core/Proposal.sol": "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.20;\ncontract Proposal {}",
    "contracts/mocks/MockOracle.sol": "// Mock oracle for testing",
    "config/networks/mainnet.json": json.dumps({"chainId": 1, "rpc": "https://mainnet.infura.io/v3/PLACEHOLDER"}),
    "config/networks/testnet.json": json.dumps({"chainId": 11155111, "rpc": "https://sepolia.infura.io/v3/PLACEHOLDER"}),
    "config/proposals/proposal_v1.json": json.dumps({
        "address": "0xDEADBEEF0000000000000000000000000000CAFE",
        "conditions": 5,
        "status": "LEGACY"
    }),
    "deployments/mainnet/addresses.json": json.dumps({"RiskLP": "0xAAA...", "Proposal": "0xBBB..."}),
    "deployments/testnet/addresses.json": json.dumps({"RiskLP": "0xCCC...", "Proposal": "0xDDD..."}),
    "test/unit/proposal.test.js": "// unit test placeholder",
    "test/integration/activate.test.js": "// integration test placeholder",
    "docs/api/activate.md": "# Activate API\nSee scripts for usage.",
    "logs/archive/run_2024_01_01.log": "INFO: Previous run completed\nINFO: 3 conditions processed",
    "cache/.artifacts/build.json": json.dumps({"compiled": True, "timestamp": "2024-01-01T00:00:00Z"}),
    "hardhat.config.js": "module.exports = { solidity: '0.8.20', networks: {} };",
    "package.json": json.dumps({
        "name": "gougoubi-pbft",
        "version": "1.0.0",
        "scripts": {
            "test": "hardhat test"
        },
        "dependencies": {}
    }),
    ".env.example": "PRIVATE_KEY=\nRPC_URL=\nPROPOSAL_ADDRESS=",
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# --- THE PROBLEM: The real mock scripts that simulate the CLI tool ---
# These scripts ARE the scripts referenced in SKILL.md - they already "exist"
# We create them as realistic mock implementations.

PROPOSAL_ADDRESS = "0x1A2B3C4D5E6F7A8B9C0D1E2F3A4B5C6D7E8F9A0B"

# State tracking file - used by the mock scripts to record calls
state_file = os.path.join(workspace, "cache/.artifacts/call_log.json")
with open(state_file, "w") as f:
    json.dump({"calls": []}, f)

# The main combined script: pbft-activate-and-add-risklp.mjs
# This is a realistic mock that parses args and returns proper JSON
main_script = r"""#!/usr/bin/env node
import { writeFileSync, readFileSync, existsSync } from 'fs';
import { resolve } from 'path';

const args = process.argv.slice(2);

if (args.includes('--help')) {
  console.log(`Usage: node scripts/pbft-activate-and-add-risklp.mjs <proposalAddress> <riskLpAmount> [options]

Options:
  --scope <all|only-created|single>   Which conditions to target (default: all)
  --condition-index <n>               Used with --scope single
  --dry-run                           Validate without executing
  --help                              Show this help

Examples:
  node scripts/pbft-activate-and-add-risklp.mjs 0xABCD 100 --dry-run
  node scripts/pbft-activate-and-add-risklp.mjs 0xABCD 150 --scope only-created
`);
  process.exit(0);
}

// Parse positional args
const positionals = args.filter(a => !a.startsWith('--') && !args[args.indexOf(a) - 1]?.startsWith('--'));
const proposalAddress = positionals[0];
const riskLpAmount = positionals[1] ? positionals[1] : '100';

// Parse flags
const isDryRun = args.includes('--dry-run');
const scopeIdx = args.indexOf('--scope');
const scope = scopeIdx !== -1 ? args[scopeIdx + 1] : 'all';
const condIdxIdx = args.indexOf('--condition-index');
const conditionIndex = condIdxIdx !== -1 ? parseInt(args[condIdxIdx + 1]) : 0;

// Log this call
const logPath = resolve(process.cwd(), 'cache/.artifacts/call_log.json');
let log = { calls: [] };
if (existsSync(logPath)) {
  try { log = JSON.parse(readFileSync(logPath, 'utf8')); } catch(e) {}
}
log.calls.push({
  script: 'pbft-activate-and-add-risklp.mjs',
  proposalAddress,
  riskLpAmount,
  scope,
  isDryRun,
  conditionIndex,
  timestamp: Date.now()
});
writeFileSync(logPath, JSON.stringify(log, null, 2));

// Validate required args
if (!proposalAddress) {
  console.error(JSON.stringify({ ok: false, stage: 'validation', error: 'proposalAddress is required', retryable: false }));
  process.exit(1);
}

const VALID_PROPOSAL = '0x1A2B3C4D5E6F7A8B9C0D1E2F3A4B5C6D7E8F9A0B';

if (proposalAddress !== VALID_PROPOSAL) {
  console.error(JSON.stringify({ ok: false, stage: 'resolve-proposal', error: `Unknown proposal: ${proposalAddress}`, retryable: false }));
  process.exit(1);
}

// Simulate proposal with 3 conditions:
//  - index 0: CREATED
//  - index 1: CREATED
//  - index 2: ACTIVE (already active, already has LP)
const conditions = [
  { index: 0, id: 'cond-0xAAA1', status: 'CREATED', hasLp: false },
  { index: 1, id: 'cond-0xAAA2', status: 'CREATED', hasLp: false },
  { index: 2, id: 'cond-0xAAA3', status: 'ACTIVE',  hasLp: true  },
];

// Dry run: just validate and return preview
if (isDryRun) {
  let targeted;
  if (scope === 'only-created') {
    targeted = conditions.filter(c => c.status === 'CREATED');
  } else if (scope === 'single') {
    targeted = conditions.filter(c => c.index === conditionIndex);
  } else {
    targeted = conditions;
  }
  console.log(JSON.stringify({
    ok: true,
    dryRun: true,
    proposalAddress,
    scope,
    riskLpPerCondition: riskLpAmount,
    targetedConditions: targeted.length,
    preview: targeted.map(c => ({ conditionId: c.id, status: c.status, willActivate: c.status === 'CREATED', willAddLp: !c.hasLp }))
  }, null, 2));
  process.exit(0);
}

// Live run
let activated = [];
let riskLpAdded = [];
let activationFailed = [];
let riskLpFailed = [];
let warnings = [];

let targeted;
if (scope === 'only-created') {
  targeted = conditions.filter(c => c.status === 'CREATED');
} else if (scope === 'single') {
  targeted = [conditions[conditionIndex]];
} else {
  targeted = conditions;
}

for (const cond of targeted) {
  // Activate if CREATED
  if (cond.status === 'CREATED') {
    activated.push({ conditionId: cond.id, conditionIndex: cond.index, txHash: `0xTX_ACTIVATE_${cond.index}` });
    cond.status = 'ACTIVE';
  }

  // Add LP if not already present
  if (!cond.hasLp) {
    riskLpAdded.push({
      conditionId: cond.id,
      conditionIndex: cond.index,
      amount: riskLpAmount,
      txHash: `0xTX_LP_${cond.index}`
    });
  } else {
    warnings.push(`Condition ${cond.id} already has LP; skipped (use --top-up to override)`);
  }
}

const result = {
  ok: true,
  proposalAddress,
  scope,
  riskLpPerCondition: riskLpAmount,
  activatedCount: activated.length,
  riskLpAddedCount: riskLpAdded.length,
  activated,
  riskLpAdded,
  activationFailed,
  riskLpFailed,
  warnings,
  nextActions: activated.length > 0 ? ['monitor-conditions', 'submit-results-when-ready'] : []
};

console.log(JSON.stringify(result, null, 2));
""".strip()

with open(os.path.join(workspace, "scripts/pbft-activate-and-add-risklp.mjs"), "w") as f:
    f.write(main_script)

# Helper scripts (stubs, as they are not the primary entry point)
join_activate_script = r"""#!/usr/bin/env node
// pbft-join-and-activate-all-conditions.mjs
// Use pbft-activate-and-add-risklp.mjs for the combined flow.
console.error('Use pbft-activate-and-add-risklp.mjs for the combined flow.');
process.exit(1);
""".strip()

with open(os.path.join(workspace, "scripts/pbft-join-and-activate-all-conditions.mjs"), "w") as f:
    f.write(join_activate_script)

add_risk_lp_script = r"""#!/usr/bin/env node
// pbft-add-risk-lp-to-proposal.mjs
// Use pbft-activate-and-add-risklp.mjs for the combined flow.
console.error('Use pbft-activate-and-add-risklp.mjs for the combined flow.');
process.exit(1);
""".strip()

with open(os.path.join(workspace, "scripts/pbft-add-risk-lp-to-proposal.mjs"), "w") as f:
    f.write(add_risk_lp_script)

# Write the proposal address to a config so the agent knows which proposal to use
proposal_config = {
    "proposalAddress": PROPOSAL_ADDRESS,
    "description": "Risk market proposal for Q2 2025 volatility conditions",
    "createdAt": "2025-01-15T09:00:00Z",
    "network": "testnet"
}
with open(os.path.join(workspace, "config/proposals/active_proposal.json"), "w") as f:
    json.dump(proposal_config, f, indent=2)

print(f"[gen_inputs] Workspace prepared at {workspace}")
print(f"[gen_inputs] Proposal address: {PROPOSAL_ADDRESS}")
print(f"[gen_inputs] 3 conditions: 2 CREATED, 1 ACTIVE")