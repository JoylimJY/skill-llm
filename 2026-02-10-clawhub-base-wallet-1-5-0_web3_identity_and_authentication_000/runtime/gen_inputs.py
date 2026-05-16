#!/usr/bin/env python3
"""
Generate the initial sandbox workspace with distractor files and the task specification.
"""
import os
import json
import random
import string

random.seed(42)

workspace = "/workspace"

# Create deeply nested distractor structure
dirs = [
    "agent-platform/config",
    "agent-platform/logs",
    "agent-platform/modules/auth",
    "agent-platform/modules/comms",
    "agent-platform/modules/registry",
    "agent-platform/tests/unit",
    "agent-platform/tests/integration",
    "deploy/production",
    "deploy/staging",
    "tmp/scratch",
    "docs/api",
    "docs/internal",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files - messy, realistic, slightly misleading
distractor_files = {
    "agent-platform/config/platform.yaml": """
platform:
  name: "AutonomousAgentHub"
  version: "2.3.1"
  network: "base-mainnet"
  chain_id: 8453
  auth_method: "wallet-signature"
  registration_endpoint: "/api/v1/register"
""",
    "agent-platform/config/agent-defaults.json": json.dumps({
        "agent_type": "autonomous",
        "wallet_required": True,
        "sign_in_protocol": "EIP-4361",
        "nonce_length": 16,
        "session_duration": 3600
    }, indent=2),
    "agent-platform/logs/registration.log": """
2026-01-15T10:23:01Z - Agent 0x1234...abcd registration attempt
2026-01-15T10:23:02Z - SIWE signature verification failed: wrong chain_id
2026-01-15T10:23:05Z - Agent 0x5678...ef01 registration SUCCESS
2026-01-15T11:00:00Z - Nonce expired, agent re-auth required
""",
    "agent-platform/modules/auth/siwe_validator.py": """
# SIWE Message Validator - DO NOT MODIFY
import re

REQUIRED_FIELDS = ['URI', 'Version', 'Chain ID', 'Nonce', 'Issued At']
EXPECTED_CHAIN_ID = 8453  # Base Mainnet

def validate_siwe_message(message: str) -> dict:
    errors = []
    for field in REQUIRED_FIELDS:
        if field not in message:
            errors.append(f'Missing field: {field}')
    
    chain_match = re.search(r'Chain ID: (\\d+)', message)
    if chain_match:
        chain_id = int(chain_match.group(1))
        if chain_id != EXPECTED_CHAIN_ID:
            errors.append(f'Wrong chain ID: {chain_id}, expected {EXPECTED_CHAIN_ID}')
    
    return {'valid': len(errors) == 0, 'errors': errors}
""",
    "agent-platform/modules/auth/README_OLD.txt": """
DEPRECATED - Old auth flow (DO NOT USE)
Old flow used chain_id=1 (Ethereum mainnet).
New flow requires Base Mainnet (chain_id=8453).
See platform.yaml for current config.
""",
    "agent-platform/modules/registry/agent_schema.json": json.dumps({
        "$schema": "http://json-schema.org/draft-07/schema",
        "type": "object",
        "required": ["agent_address", "siwe_message", "siwe_signature", "registered_at"],
        "properties": {
            "agent_address": {"type": "string", "pattern": "^0x[a-fA-F0-9]{40}$"},
            "siwe_message": {"type": "string"},
            "siwe_signature": {"type": "string", "pattern": "^0x[a-fA-F0-9]{130}$"},
            "registered_at": {"type": "string", "format": "date-time"}
        }
    }, indent=2),
    "agent-platform/modules/comms/messenger.js": """
// Placeholder messaging module
// Requires agent to be registered first
const { ethers } = require('ethers');

module.exports = {
  sendMessage: async (from, to, content) => {
    // Not implemented - requires registration
    throw new Error('Agent must complete SIWE registration first');
  }
};
""",
    "agent-platform/tests/unit/test_wallet.js": """
// Unit tests for wallet operations - BROKEN, needs real wallet
const assert = require('assert');

// TODO: These tests fail because no wallet is configured
// The agent needs to create a real wallet and update TEST_ADDRESS
const TEST_ADDRESS = 'PLACEHOLDER_ADDRESS';
const TEST_PRIVATE_KEY = 'PLACEHOLDER_KEY';

describe('Wallet Tests', () => {
  it('should verify wallet address format', () => {
    assert(TEST_ADDRESS.startsWith('0x'), 'Address must start with 0x');
  });
});
""",
    "agent-platform/tests/integration/auth_flow.json": json.dumps({
        "test_suite": "SIWE Auth Flow",
        "domain": "agentplatform.local",
        "uri": "https://agentplatform.local/register",
        "version": "1",
        "chain_id": 8453,
        "statement": "I am registering as an autonomous agent on the AutonomousAgentHub platform.",
        "nonce_format": "alphanumeric_16chars",
        "expected_signature_prefix": "0x"
    }, indent=2),
    "deploy/production/deployment.env.template": """
# Production deployment template
# DO NOT put real keys here!
PLATFORM_URL=https://agentplatform.local
CHAIN_ID=8453
NETWORK=base-mainnet
# PRIVATE_KEY=  <-- Set via secure vault
# WALLET_ADDRESS=  <-- Auto-detected from private key
""",
    "deploy/staging/docker-compose.yml": """
version: '3.8'
services:
  agent:
    image: autonomous-agent:latest
    environment:
      - PRIVATE_KEY=${PRIVATE_KEY}
      - WALLET_ADDRESS=${WALLET_ADDRESS}
      - CHAIN_ID=8453
    volumes:
      - ./data:/data
""",
    "docs/api/registration_endpoint.md": """
# Agent Registration API

## POST /api/v1/register

Registers a new autonomous agent on the platform.

### Request Body
```json
{
  "agent_address": "0x...",
  "siwe_message": "...",
  "siwe_signature": "0x...",
  "registered_at": "ISO8601 timestamp"
}
```

### SIWE Message Requirements
- Domain: agentplatform.local
- URI: https://agentplatform.local/register  
- Chain ID: MUST be 8453 (Base Mainnet)
- Statement: "I am registering as an autonomous agent on the AutonomousAgentHub platform."
- Nonce: 16-character alphanumeric string

### Signature Format
- ECDSA signature over the SIWE message
- Must be verifiable against agent_address
""",
    "docs/internal/old_chain_ids.txt": """
DEPRECATED CHAIN IDs (DO NOT USE):
- Ethereum Mainnet: 1
- Ropsten: 3  
- Rinkeby: 4
- Goerli: 5

CURRENT:
- Base Mainnet: 8453 (USE THIS)
- Base Sepolia: 84532 (testnet only)
""",
    "tmp/scratch/failed_attempt.js": """
// This attempt FAILED - wrong chain ID used
// const chainId = 1;  // WRONG! This is Ethereum mainnet
// const wallet = new ethers.Wallet('HARDCODED_KEY_WRONG');  // SECURITY RISK

// Do not use this file.
""",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# Create the task specification file
task_spec = {
    "task": "agent-self-registration",
    "platform": "AutonomousAgentHub",
    "domain": "agentplatform.local",
    "registration_uri": "https://agentplatform.local/register",
    "statement": "I am registering as an autonomous agent on the AutonomousAgentHub platform.",
    "nonce": "aB3xK9mN2pQr7vWz",
    "output_file": "agent_registration.json"
}

with open(os.path.join(workspace, "task_spec.json"), "w") as f:
    json.dump(task_spec, f, indent=2)

print("Workspace initialized with distractor files and task specification.")
print(f"Files created: {len(distractor_files)} distractor files + task_spec.json")