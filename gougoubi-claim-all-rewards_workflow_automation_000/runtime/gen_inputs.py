import os
import json
import random

random.seed(42)

workspace = "/workspace"

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "config",
    "logs",
    "archive/2023",
    "archive/2024",
    "data/raw",
    "data/processed",
    "tests/unit",
    "tests/integration",
    "docs",
    "deploy",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────

# 1. A misleading README-like file (not a hint, just noise)
with open(os.path.join(workspace, "docs/architecture.md"), "w") as f:
    f.write("# Architecture\nThis system uses PBFT consensus.\nSee scripts folder for tooling.\n")

# 2. Old reward log with wrong schema
with open(os.path.join(workspace, "archive/2023/old_rewards.json"), "w") as f:
    json.dump({"status": "partial", "rewards": [{"addr": "0xDEAD", "amount": 100}]}, f, indent=2)

# 3. Stale config
with open(os.path.join(workspace, "config/network.json"), "w") as f:
    json.dump({"rpc": "http://localhost:8545", "chainId": 1337, "deprecated": True}, f, indent=2)

# 4. A dummy governance proposal file
with open(os.path.join(workspace, "data/raw/proposals.csv"), "w") as f:
    f.write("proposal_id,status,votes\n1,active,500\n2,closed,200\n3,pending,0\n")

# 5. Processed LP data
with open(os.path.join(workspace, "data/processed/lp_positions.json"), "w") as f:
    json.dump([{"address": "0xAAAA", "lpTokens": 500}, {"address": "0xBBBB", "lpTokens": 0}], f, indent=2)

# 6. A test file that references wrong method names
with open(os.path.join(workspace, "tests/unit/test_methods.js"), "w") as f:
    f.write('// Tests for claim methods\n// Methods: fast, slow, batch\n// NOTE: this file is outdated\n')

# 7. Deploy config with address list (distractor - different addresses)
with open(os.path.join(workspace, "deploy/deploy_config.json"), "w") as f:
    json.dump({
        "deployer": "0x1234567890abcdef1234567890abcdef12345678",
        "contract": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
        "network": "testnet"
    }, f, indent=2)

# 8. Integration test stub
with open(os.path.join(workspace, "tests/integration/claim_flow.test.js"), "w") as f:
    f.write('// Integration test placeholder\n// TODO: implement claim flow tests\n')

# 9. Stale log
with open(os.path.join(workspace, "logs/run_2024-01-15.log"), "w") as f:
    f.write("[INFO] Claim run started\n[WARN] Address 0xOLD not found\n[INFO] Done\n")

# 10. Archive summary (wrong schema, distractor)
with open(os.path.join(workspace, "archive/2024/claim_run_q1.json"), "w") as f:
    json.dump({"run": "Q1-2024", "success": False, "note": "manual run, schema changed"}, f, indent=2)

# 11. Distractor script (NOT the real ones)
with open(os.path.join(workspace, "scripts/pbft-utils.mjs"), "w") as f:
    f.write('// Utility helpers - not a claim script\nexport function noop() {}\n')

# ── THE REAL MOCK SCRIPTS ─────────────────────────────────────────────────────
# These simulate the actual SKILL.md scripts with realistic dry-run output.

ADDRESSES = [
    "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
    "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
    "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
]

# Script 1: profile method (preferred)
profile_script = r"""#!/usr/bin/env node
// pbft-claim-rewards-profile-method.mjs
// Preferred profile path for reward claiming

import { parseArgs } from 'node:util';

const { values, positionals } = parseArgs({
  args: process.argv.slice(2),
  options: {
    'dry-run': { type: 'boolean', default: false },
    'addresses': { type: 'string', multiple: true },
    'help': { type: 'boolean', default: false },
  },
  allowPositionals: true,
});

if (values.help) {
  console.log('Usage: node pbft-claim-rewards-profile-method.mjs [--dry-run] [--addresses 0x... --addresses 0x...]');
  console.log('Method: profile (default preferred)');
  process.exit(0);
}

const addresses = values.addresses && values.addresses.length > 0
  ? values.addresses
  : positionals;

if (!addresses || addresses.length === 0) {
  console.error(JSON.stringify({ ok: false, stage: "validation", error: "No addresses provided", retryable: false }));
  process.exit(1);
}

// Validate addresses
for (const addr of addresses) {
  if (!/^0x[0-9a-fA-F]{40}$/.test(addr)) {
    console.error(JSON.stringify({ ok: false, stage: "validation", error: `Invalid address: ${addr}`, retryable: false }));
    process.exit(1);
  }
}

const isDryRun = values['dry-run'];

const results = addresses.map((address, i) => ({
  address,
  winnerRewardClaimed: !isDryRun ? true : false,
  governanceRewardClaimed: !isDryRun ? true : false,
  lpRewardClaimed: !isDryRun ? true : false,
  txHashes: isDryRun ? [] : [`0x${Buffer.from(address + 'winner' + i).toString('hex').slice(0, 64)}`, `0x${Buffer.from(address + 'gov' + i).toString('hex').slice(0, 64)}`, `0x${Buffer.from(address + 'lp' + i).toString('hex').slice(0, 64)}`]
}));

const totalTx = results.reduce((acc, r) => acc + r.txHashes.length, 0);

const output = {
  ok: true,
  method: "profile",
  addresses: addresses,
  claimedTxCount: totalTx,
  results: results,
  warnings: []
};

console.log(JSON.stringify(output, null, 2));
"""

with open(os.path.join(workspace, "scripts/pbft-claim-rewards-profile-method.mjs"), "w") as f:
    f.write(profile_script)

# Script 2: quick method
quick_script = r"""#!/usr/bin/env node
// pbft-claim-rewards-quick.mjs
// Fast one-click path

import { parseArgs } from 'node:util';

const { values, positionals } = parseArgs({
  args: process.argv.slice(2),
  options: {
    'dry-run': { type: 'boolean', default: false },
    'addresses': { type: 'string', multiple: true },
    'help': { type: 'boolean', default: false },
  },
  allowPositionals: true,
});

if (values.help) {
  console.log('Usage: node pbft-claim-rewards-quick.mjs [--dry-run] [--addresses 0x...]');
  process.exit(0);
}

const addresses = values.addresses && values.addresses.length > 0
  ? values.addresses
  : positionals;

if (!addresses || addresses.length === 0) {
  console.error(JSON.stringify({ ok: false, stage: "validation", error: "No addresses provided", retryable: false }));
  process.exit(1);
}

for (const addr of addresses) {
  if (!/^0x[0-9a-fA-F]{40}$/.test(addr)) {
    console.error(JSON.stringify({ ok: false, stage: "validation", error: `Invalid address: ${addr}`, retryable: false }));
    process.exit(1);
  }
}

const isDryRun = values['dry-run'];

const results = addresses.map((address, i) => ({
  address,
  winnerRewardClaimed: !isDryRun,
  governanceRewardClaimed: !isDryRun,
  lpRewardClaimed: !isDryRun,
  txHashes: isDryRun ? [] : [`0x${Buffer.from(address + 'quick' + i).toString('hex').slice(0, 64)}`]
}));

const totalTx = results.reduce((acc, r) => acc + r.txHashes.length, 0);

console.log(JSON.stringify({
  ok: true,
  method: "quick",
  addresses,
  claimedTxCount: totalTx,
  results,
  warnings: []
}, null, 2));
"""

with open(os.path.join(workspace, "scripts/pbft-claim-rewards-quick.mjs"), "w") as f:
    f.write(quick_script)

# Script 3: three-address / full-scan (deep scan path)
three_addr_script = r"""#!/usr/bin/env node
// pbft-claim-three-address-rewards.mjs
// Deep scan path (exhaustive fallback)

import { parseArgs } from 'node:util';

const { values, positionals } = parseArgs({
  args: process.argv.slice(2),
  options: {
    'dry-run': { type: 'boolean', default: false },
    'addresses': { type: 'string', multiple: true },
    'help': { type: 'boolean', default: false },
  },
  allowPositionals: true,
});

if (values.help) {
  console.log('Usage: node pbft-claim-three-address-rewards.mjs [--dry-run] [--addresses 0x...]');
  process.exit(0);
}

const addresses = values.addresses && values.addresses.length > 0
  ? values.addresses
  : positionals;

if (!addresses || addresses.length === 0) {
  console.error(JSON.stringify({ ok: false, stage: "validation", error: "No addresses provided", retryable: false }));
  process.exit(1);
}

for (const addr of addresses) {
  if (!/^0x[0-9a-fA-F]{40}$/.test(addr)) {
    console.error(JSON.stringify({ ok: false, stage: "validation", error: `Invalid address: ${addr}`, retryable: false }));
    process.exit(1);
  }
}

const isDryRun = values['dry-run'];

const results = addresses.map((address, i) => ({
  address,
  winnerRewardClaimed: !isDryRun,
  governanceRewardClaimed: !isDryRun,
  lpRewardClaimed: !isDryRun,
  txHashes: isDryRun ? [] : [`0x${Buffer.from(address + 'scan' + i).toString('hex').slice(0, 64)}`]
}));

const totalTx = results.reduce((acc, r) => acc + r.txHashes.length, 0);

console.log(JSON.stringify({
  ok: true,
  method: "full-scan",
  addresses,
  claimedTxCount: totalTx,
  results,
  warnings: []
}, null, 2));
"""

with open(os.path.join(workspace, "scripts/pbft-claim-three-address-rewards.mjs"), "w") as f:
    f.write(three_addr_script)

# ── THE TASK INPUT FILE ──────────────────────────────────────────────────────
# A messy CSV with wallet addresses (some have whitespace/mixed case) that the agent must process
task_input = """wallet_id,address,tier,notes
1,  0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266  ,gold,active participant
2,0x70997970C51812dc3A010C7d01b50e0d17dc79C8,silver,governance voter
3, 0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC ,bronze,LP provider
4,INVALID_NOT_AN_ADDRESS,none,error row - skip
5,0xDEAD,none,too short - skip
"""

with open(os.path.join(workspace, "data/raw/reward_recipients.csv"), "w") as f:
    f.write(task_input)

print("Workspace initialized successfully.")
print(f"Target addresses: {ADDRESSES}")