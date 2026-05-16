import os
import json
import stat

# Fixed seed for determinism
PROPOSAL_ADDRESS = "0xABCDEF1234567890abcdef1234567890ABCDEF12"

workspace = "/workspace"

# ── directory skeleton ────────────────────────────────────────────────────────
dirs = [
    "scripts",
    "contracts",
    "contracts/proposals",
    "contracts/conditions",
    "config",
    "data/markets",
    "data/evidence",
    "logs",
    "test",
    "docs",
    "artifacts",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── distractor files ──────────────────────────────────────────────────────────
distractors = {
    "contracts/proposals/proposal_old.json": json.dumps({
        "address": "0xDEADBEEF00000000000000000000000000000001",
        "status": "expired",
        "conditions": []
    }, indent=2),

    "contracts/conditions/legacy_condition.json": json.dumps({
        "index": 0,
        "conditionAddress": "0x0000000000000000000000000000000000000000",
        "result": 0,
        "skills": {}
    }, indent=2),

    "config/chain.json": json.dumps({
        "chainId": 137,
        "rpcUrl": "https://polygon-rpc.com",
        "confirmations": 3
    }, indent=2),

    "config/deploy.json": json.dumps({
        "deployer": "0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        "gasLimit": 500000
    }, indent=2),

    "data/markets/polymarket_snapshot.json": json.dumps({
        "markets": [
            {"slug": "btc-above-60k-dec2024", "resolved": True, "outcome": "Yes"},
            {"slug": "eth-merge-success", "resolved": True, "outcome": "Yes"},
            {"slug": "fed-rate-cut-q1", "resolved": False, "outcome": None}
        ]
    }, indent=2),

    "data/evidence/raw_oracle_feed.txt": "\n".join([
        "# Raw oracle data dump - DO NOT USE DIRECTLY",
        "event_id=btc-above-60k-dec2024 result=YES ts=1704067200",
        "event_id=eth-merge-success result=YES ts=1663724400",
        "event_id=fed-rate-cut-q1 result=PENDING ts=0",
    ]),

    "logs/submission_attempt_2024-01-01.log": "\n".join([
        "[INFO] Starting submission pipeline",
        "[WARN] Condition 0x111 already settled, skipping",
        "[ERROR] RPC timeout on attempt 3",
        "[INFO] Pipeline complete: 0 submitted, 1 skipped, 1 failed",
    ]),

    "test/mock_rpc.js": """\
// Mock RPC helper for unit tests
const mockRpc = {
  getConditionResult: async (addr) => ({ result: 0 }),
  submitResult: async (addr, val) => ({ hash: '0xmockhash', status: 1 })
};
module.exports = mockRpc;
""",

    "docs/pbft-protocol.md": """\
# PBFT Submission Protocol

Conditions must have result=0 before submission.
Submit exactly one vote per condition.
Use skills payload for evidence locators.
""",

    "artifacts/abi_condition.json": json.dumps([
        {"name": "result", "type": "function", "outputs": [{"type": "uint8"}]},
        {"name": "submitResult", "type": "function", "inputs": [{"name": "val", "type": "uint8"}]}
    ], indent=2),

    "artifacts/abi_proposal.json": json.dumps([
        {"name": "getConditions", "type": "function", "outputs": [{"type": "address[]"}]},
        {"name": "conditionCount", "type": "function", "outputs": [{"type": "uint256"}]}
    ], indent=2),
}

for rel_path, content in distractors.items():
    full = os.path.join(workspace, rel_path)
    with open(full, "w") as f:
        f.write(content)

# ── SKILL.md ──────────────────────────────────────────────────────────────────
skill_md = """\
---
name: gougoubi-submit-real-results
description: Submit real-world outcomes for Gougoubi conditions using deterministic evidence from condition skills and public market data.
metadata:
  pattern: pipeline
  interaction: single-turn
  domain: gougoubi-pbft
  outputs: structured-json
---

# Gougoubi Submit Real Results

Use this skill to map external evidence to on-chain condition results and submit one result per condition.

## Use This Skill When

- The user wants to submit real outcomes for all conditions in a proposal.
- The user wants to submit only officially resolved conditions first.
- The user wants a forced fallback such as `No` for remaining unresolved conditions.

## Do Not Use This Skill When

- The user only wants to inspect missing results without submitting. Use `gougoubi-recovery-ops`.
- The user only wants activation or LP staking.

## Input

```json
{
  "proposalAddress": "0x...",
  "mode": "resolved-only|all|force",
  "forceResult": "yes|no",
  "evidenceNote": "optional"
}
```

Defaults:

- `mode=resolved-only`
- `evidenceNote` should be auto-generated when missing

## Pipeline

Step 1: Validate proposal address and target chain.

Step 2: Enumerate all conditions under the proposal.

Step 3: Read each condition `skills` payload and extract evidence locators such as event slug or market id.

Step 4: Fetch public evidence and build a result map:
- `resolved-only`: only officially resolved markets
- `all`: all markets with clear final outcomes
- `force`: use the same forced side for still-pending conditions

Step 5: For each target condition:
- Skip if `result != 0`
- Skip if the condition is not ready for submission
- Submit exactly one result vote

Step 6: Return submitted, skipped, failed, and tx hashes.

## Checkpoints

- Prefer `resolved-only` unless the user explicitly asks for `all` or `force`.
- Never duplicate a submission for a condition that already has `result != 0`.
- Keep evidence mapping and tx results together in the output.

## Output

```json
{
  "ok": true,
  "proposalAddress": "0x...",
  "mode": "resolved-only|all|force",
  "submittedCount": 0,
  "skippedCount": 0,
  "failedCount": 0,
  "submitted": [
    {
      "index": 0,
      "conditionAddress": "0x...",
      "conditionName": "",
      "result": 1,
      "txHash": "0x..."
    }
  ],
  "skipped": [],
  "failed": [],
  "warnings": []
}
```

Failure:

```json
{
  "ok": false,
  "stage": "validation|fetch-evidence|submit|confirm",
  "error": "reason",
  "retryable": true
}
```

## Project Scripts

- `scripts/pbft-submit-all-condition-results.mjs`
- `scripts/pbft-submit-results-from-skills-once.mjs`
- `scripts/pbft-submit-real-results-1605.mjs`
- `scripts/pbft-submit-real-results-c427-confirmed.mjs`
- `scripts/pbft-submit-real-results-ba0c-resolved-only.mjs`
- `scripts/pbft-submit-remaining-no-ba0c.mjs`

## Script Entry Points

- Generic fixed-side submission: `scripts/pbft-submit-all-condition-results.mjs`
- Generic skills-derived submission: `scripts/pbft-submit-results-from-skills-once.mjs`
- `node scripts/pbft-submit-all-condition-results.mjs --help`
- `node scripts/pbft-submit-all-condition-results.mjs <proposalAddress> --result yes --dry-run`
- `node scripts/pbft-submit-results-from-skills-once.mjs --help`
- `node scripts/pbft-submit-results-from-skills-once.mjs <proposalAddress>`
- Specialized scripts also support `--help` for their fixed proposal mappings.

## Boundaries

- Do not infer unresolved results unless the user explicitly asks for `all` or `force`.
- Preserve an auditable mapping from evidence to submitted result.
"""

with open(os.path.join(workspace, "SKILL.md"), "w") as f:
    f.write(skill_md)

# ── mock scripts ──────────────────────────────────────────────────────────────
# The "correct" script: pbft-submit-results-from-skills-once.mjs
# This script reads skills payloads, resolves evidence, skips already-settled conditions
# and submits resolved-only by default.
# It accepts: node script.mjs <proposalAddress>
# Output: structured JSON matching SKILL.md schema

skills_derived_script = r"""#!/usr/bin/env node
// Generic skills-derived submission script
// Usage: node scripts/pbft-submit-results-from-skills-once.mjs <proposalAddress>

import process from 'process';

const args = process.argv.slice(2);

if (args.includes('--help') || args.length === 0) {
  console.log('Usage: node scripts/pbft-submit-results-from-skills-once.mjs <proposalAddress>');
  console.log('Reads condition skills payloads, fetches evidence, submits resolved-only results.');
  process.exit(0);
}

const proposalAddress = args[0];

// Simulate pipeline execution
// Condition 0: BTC price condition - resolved YES via market oracle
// Condition 1: ETH staking condition - resolved YES via market oracle
// Condition 2: FED rate condition - already settled on-chain (result != 0), skip
const result = {
  ok: true,
  proposalAddress: proposalAddress,
  mode: "resolved-only",
  submittedCount: 2,
  skippedCount: 1,
  failedCount: 0,
  submitted: [
    {
      index: 0,
      conditionAddress: "0x1111111111111111111111111111111111111111",
      conditionName: "BTC Above 60K December 2024",
      result: 1,
      txHash: "0xaabbccdd11223344aabbccdd11223344aabbccdd11223344aabbccdd11223344"
    },
    {
      index: 1,
      conditionAddress: "0x2222222222222222222222222222222222222222",
      conditionName: "ETH Merge Success",
      result: 1,
      txHash: "0xdeadbeef99887766deadbeef99887766deadbeef99887766deadbeef99887766"
    }
  ],
  skipped: [
    {
      index: 2,
      conditionAddress: "0x3333333333333333333333333333333333333333",
      conditionName: "FED Rate Cut Q1 2024",
      reason: "result != 0 (already settled)"
    }
  ],
  failed: [],
  warnings: [
    "Condition 2 skipped: on-chain result already set to 2"
  ]
};

console.log(JSON.stringify(result, null, 2));
"""

# The "wrong" script: pbft-submit-all-condition-results.mjs
# This one accepts --result yes/no and does fixed-side submission (not skills-derived)
fixed_side_script = r"""#!/usr/bin/env node
// Generic fixed-side submission script
// Usage: node scripts/pbft-submit-all-condition-results.mjs <proposalAddress> --result yes|no [--dry-run]

import process from 'process';

const args = process.argv.slice(2);

if (args.includes('--help') || args.length === 0) {
  console.log('Usage: node scripts/pbft-submit-all-condition-results.mjs <proposalAddress> --result yes|no [--dry-run]');
  console.log('Submits a fixed result (yes or no) for ALL conditions in the proposal.');
  process.exit(0);
}

const proposalAddress = args[0];
const resultIdx = args.indexOf('--result');
const dryRun = args.includes('--dry-run');
const resultVal = resultIdx !== -1 ? args[resultIdx + 1] : null;

if (!resultVal) {
  console.error(JSON.stringify({ok: false, stage: "validation", error: "--result yes|no is required", retryable: false}));
  process.exit(1);
}

if (dryRun) {
  console.log(JSON.stringify({ok: true, dryRun: true, proposalAddress, mode: "all", submittedCount: 0, skippedCount: 0, failedCount: 0, submitted: [], skipped: [], failed: [], warnings: ["dry-run: no transactions sent"]}));
  process.exit(0);
}

// Wrong answer trap: this does fixed-side, not evidence-based, and uses mode=all not resolved-only
const result = {
  ok: true,
  proposalAddress: proposalAddress,
  mode: "all",
  submittedCount: 3,
  skippedCount: 0,
  failedCount: 0,
  submitted: [
    {index: 0, conditionAddress: "0x1111111111111111111111111111111111111111", conditionName: "BTC Above 60K December 2024", result: resultVal === "yes" ? 1 : 2, txHash: "0xfixedside0000000000000000000000000000000000000000000000000000001"},
    {index: 1, conditionAddress: "0x2222222222222222222222222222222222222222", conditionName: "ETH Merge Success", result: resultVal === "yes" ? 1 : 2, txHash: "0xfixedside0000000000000000000000000000000000000000000000000000002"},
    {index: 2, conditionAddress: "0x3333333333333333333333333333333333333333", conditionName: "FED Rate Cut Q1 2024", result: resultVal === "yes" ? 1 : 2, txHash: "0xfixedside0000000000000000000000000000000000000000000000000000003"}
  ],
  skipped: [],
  failed: [],
  warnings: ["FIXED-SIDE SUBMISSION: all conditions forced to " + resultVal.toUpperCase()]
};

console.log(JSON.stringify(result, null, 2));
"""

# Specialized scripts (stubs that print help)
specialized_scripts = {
    "pbft-submit-real-results-1605.mjs": r"""#!/usr/bin/env node
// Specialized script for proposal 0x...1605
import process from 'process';
const args = process.argv.slice(2);
if (args.includes('--help') || args.length === 0) {
  console.log('Specialized script for proposal ending in 1605. Not applicable to other proposals.');
  process.exit(0);
}
console.error(JSON.stringify({ok: false, stage: "validation", error: "This script only handles proposal 0x...1605", retryable: false}));
process.exit(1);
""",
    "pbft-submit-real-results-c427-confirmed.mjs": r"""#!/usr/bin/env node
// Specialized script for proposal 0x...c427
import process from 'process';
const args = process.argv.slice(2);
if (args.includes('--help') || args.length === 0) {
  console.log('Specialized script for proposal ending in c427. Not applicable to other proposals.');
  process.exit(0);
}
console.error(JSON.stringify({ok: false, stage: "validation", error: "This script only handles proposal 0x...c427", retryable: false}));
process.exit(1);
""",
    "pbft-submit-real-results-ba0c-resolved-only.mjs": r"""#!/usr/bin/env node
// Specialized script for proposal 0x...ba0c
import process from 'process';
const args = process.argv.slice(2);
if (args.includes('--help') || args.length === 0) {
  console.log('Specialized script for proposal ending in ba0c. Not applicable to other proposals.');
  process.exit(0);
}
console.error(JSON.stringify({ok: false, stage: "validation", error: "This script only handles proposal 0x...ba0c", retryable: false}));
process.exit(1);
""",
    "pbft-submit-remaining-no-ba0c.mjs": r"""#!/usr/bin/env node
// Submits remaining No votes for ba0c proposal
import process from 'process';
const args = process.argv.slice(2);
if (args.includes('--help') || args.length === 0) {
  console.log('Submits remaining No results for proposal ba0c. Not applicable to other proposals.');
  process.exit(0);
}
console.error(JSON.stringify({ok: false, stage: "validation", error: "This script only handles proposal 0x...ba0c", retryable: false}));
process.exit(1);
""",
}

scripts_dir = os.path.join(workspace, "scripts")

with open(os.path.join(scripts_dir, "pbft-submit-results-from-skills-once.mjs"), "w") as f:
    f.write(skills_derived_script)

with open(os.path.join(scripts_dir, "pbft-submit-all-condition-results.mjs"), "w") as f:
    f.write(fixed_side_script)

for name, content in specialized_scripts.items():
    with open(os.path.join(scripts_dir, name), "w") as f:
        f.write(content)

# Make all scripts executable
for fname in os.listdir(scripts_dir):
    fpath = os.path.join(scripts_dir, fname)
    st = os.stat(fpath)
    os.chmod(fpath, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# Write the proposal address to a config file (this is the "input" to the task)
proposal_config = {
    "proposalAddress": PROPOSAL_ADDRESS,
    "network": "polygon",
    "createdAt": "2024-01-15T10:00:00Z",
    "description": "Q1 2024 Macro Market Conditions Proposal",
    "conditionCount": 3
}
with open(os.path.join(workspace, "config", "active_proposal.json"), "w") as f:
    json.dump(proposal_config, f, indent=2)

print("Workspace generated successfully.")
print(f"Proposal address: {PROPOSAL_ADDRESS}")