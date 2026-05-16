import os
import json
import random
import stat
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# Create the scripts directory with create-wallet.js (this is the skill's existing script)
scripts_dir = workspace / "scripts"
scripts_dir.mkdir(exist_ok=True)

# Create the actual create-wallet.js script (described as existing in SKILL.md)
create_wallet_js = '''#!/usr/bin/env node
'use strict';

const { ethers } = require('ethers');
const fs = require('fs');
const path = require('path');
const os = require('os');

const args = process.argv.slice(2);
const mode = args[0];
const name = args[1];

async function createWallet() {
  const wallet = ethers.Wallet.createRandom();

  if (mode === '--env') {
    console.log(`export WALLET_ADDRESS="${wallet.address}"`);
    console.log(`export PRIVATE_KEY="${wallet.privateKey}"`);
    console.log(`export MNEMONIC="${wallet.mnemonic.phrase}"`);
  } else if (mode === '--json') {
    const output = {
      address: wallet.address,
      privateKey: wallet.privateKey,
      mnemonic: wallet.mnemonic.phrase
    };
    console.log(JSON.stringify(output, null, 2));
  } else if (mode === '--managed') {
    const walletName = name || 'default';
    const walletDir = path.join(os.homedir(), '.openclaw', 'wallets');
    fs.mkdirSync(walletDir, { recursive: true });
    const filepath = path.join(walletDir, `${walletName}.json`);
    const data = JSON.stringify({
      address: wallet.address,
      privateKey: wallet.privateKey,
      mnemonic: wallet.mnemonic.phrase
    }, null, 2);
    fs.writeFileSync(filepath, data, { mode: 0o600 });
    console.log(`Wallet created: ${wallet.address}`);
    console.log(`Saved to: ${filepath}`);
  } else {
    // Default: same as --env
    console.log(`export WALLET_ADDRESS="${wallet.address}"`);
    console.log(`export PRIVATE_KEY="${wallet.privateKey}"`);
  }
}

createWallet().catch(console.error);
'''

(scripts_dir / "create-wallet.js").write_text(create_wallet_js)

# Create check-balance.js (existing script per SKILL.md)
check_balance_js = '''#!/usr/bin/env node
'use strict';

const { ethers } = require('ethers');

const address = process.argv[2];
if (!address) {
  console.error('Usage: check-balance.js <address>');
  process.exit(1);
}

async function checkBalance() {
  const provider = new ethers.JsonRpcProvider('https://mainnet.base.org');
  try {
    const balance = await provider.getBalance(address);
    console.log('Balance:', ethers.formatEther(balance), 'ETH');
  } catch (e) {
    console.error('Error fetching balance:', e.message);
  }
}

checkBalance().catch(console.error);
'''

(scripts_dir / "check-balance.js").write_text(check_balance_js)

# Create basemail-register.js (existing script per SKILL.md)
basemail_register_js = '''#!/usr/bin/env node
'use strict';

const { ethers } = require('ethers');

async function register() {
  const privateKey = process.env.PRIVATE_KEY;
  const walletName = process.argv[2];

  if (!privateKey && !walletName) {
    console.error('Usage: PRIVATE_KEY="0x..." node basemail-register.js OR node basemail-register.js <name>');
    process.exit(1);
  }

  let wallet;
  if (privateKey) {
    wallet = new ethers.Wallet(privateKey);
  }
  
  console.log('BaseMail registration would occur here for:', wallet ? wallet.address : walletName);
}

register().catch(console.error);
'''

(scripts_dir / "basemail-register.js").write_text(basemail_register_js)

# Create a deeply nested distractor directory structure
# Simulate a DeFi trading bot project
dirs = [
    "src/trading/strategies",
    "src/trading/indicators",
    "src/trading/execution",
    "src/data/feeds",
    "src/data/history",
    "src/api/routes",
    "src/api/middleware",
    "config/environments",
    "config/networks",
    "logs/trades",
    "logs/errors",
    "tests/unit",
    "tests/integration",
    "docs/architecture",
    "deploy/docker",
    "deploy/kubernetes",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files - realistic but irrelevant
distractor_files = {
    "src/trading/strategies/momentum.js": "// Momentum trading strategy\nmodule.exports = { name: 'momentum', execute: async () => {} };",
    "src/trading/strategies/arbitrage.js": "// Arbitrage strategy\nmodule.exports = { name: 'arbitrage', pairs: ['ETH/USDC', 'ETH/DAI'] };",
    "src/trading/indicators/rsi.js": "// RSI indicator implementation\nfunction calculateRSI(prices, period=14) { return 50; }\nmodule.exports = { calculateRSI };",
    "src/trading/execution/order.js": "// Order execution module\nclass OrderManager { async placeOrder(params) { return null; } }\nmodule.exports = { OrderManager };",
    "src/data/feeds/price-oracle.js": "// Price feed oracle\nconst FEEDS = { ETH: '0x...', BTC: '0x...' };\nmodule.exports = { FEEDS };",
    "src/data/history/cache.json": json.dumps({"lastSync": "2024-01-15", "records": 10000, "pairs": ["ETH/USDC"]}),
    "src/api/routes/health.js": "// Health check route\napp.get('/health', (req, res) => res.json({ status: 'ok' }));",
    "src/api/middleware/auth.js": "// Authentication middleware - PLACEHOLDER\n// TODO: Implement wallet-based auth\nmodule.exports = (req, res, next) => next();",
    "config/environments/production.json": json.dumps({"env": "production", "logLevel": "warn", "maxPositions": 5}),
    "config/environments/staging.json": json.dumps({"env": "staging", "logLevel": "debug", "maxPositions": 2}),
    "config/networks/base.json": json.dumps({"name": "Base", "chainId": 8453, "rpc": "https://mainnet.base.org", "explorer": "https://basescan.org"}),
    "config/networks/ethereum.json": json.dumps({"name": "Ethereum", "chainId": 1, "rpc": "https://eth.llamarpc.com"}),
    "logs/trades/2024-01-15.log": "2024-01-15T10:23:11Z INFO Trade executed: ETH/USDC buy 0.5 @ 2847.32\n2024-01-15T11:45:22Z INFO Trade executed: ETH/USDC sell 0.5 @ 2901.15",
    "logs/errors/2024-01-15.log": "2024-01-15T09:15:00Z ERROR Connection timeout to price oracle\n2024-01-15T09:15:05Z INFO Reconnected successfully",
    "tests/unit/strategy.test.js": "const assert = require('assert');\ndescribe('Strategy', () => { it('should initialize', () => { assert.ok(true); }); });",
    "tests/integration/trading.test.js": "// Integration tests for trading pipeline\n// Requires testnet connection",
    "docs/architecture/system-overview.md": "# System Architecture\n\n## Components\n- Price Oracle\n- Strategy Engine\n- Order Manager\n- Risk Manager\n\n## Auth\nTBD - wallet-based authentication planned",
    "deploy/docker/Dockerfile.bot": "FROM node:18-slim\nWORKDIR /app\nCOPY package*.json ./\nRUN npm install\nCOPY . .\nCMD [\"node\", \"src/index.js\"]",
    "deploy/kubernetes/deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: trading-bot\nspec:\n  replicas: 1",
    "package.json": json.dumps({
        "name": "defi-trading-bot",
        "version": "2.1.0",
        "description": "Autonomous DeFi trading bot",
        "main": "src/index.js",
        "scripts": {
            "start": "node src/index.js",
            "test": "mocha tests/**/*.test.js"
        },
        "dependencies": {
            "ethers": "^6.0.0"
        }
    }, indent=2),
    "src/index.js": "// Main entry point\nconst { OrderManager } = require('./trading/execution/order');\nconsole.log('Trading bot starting...');",
}

for filepath, content in distractor_files.items():
    full_path = workspace / filepath
    full_path.write_text(content)

# Create a deliberately wrong/incomplete identity config that shows someone tried but failed
wrong_identity = {
    "agent_name": "trading-bot-v2",
    "network": "ethereum",
    "chain_id": 1,
    "created_at": "2024-01-15T00:00:00Z",
    "note": "INCOMPLETE - wallet address not yet generated, SIWE signature missing"
}
(workspace / "config" / "agent-identity.json").write_text(json.dumps(wrong_identity, indent=2))

# A stale .env.example with wrong chain info
env_example = """# Environment variables template
# Fill in with real values

WALLET_ADDRESS=
PRIVATE_KEY=
# WRONG - this is Ethereum mainnet chain ID, not Base
CHAIN_ID=1
RPC_URL=https://eth.llamarpc.com
"""
(workspace / ".env.example").write_text(env_example)

# An incomplete SIWE attempt script that has wrong chain ID and incomplete format
bad_siwe_attempt = """// DRAFT - incomplete SIWE implementation
const { ethers } = require('ethers');

// TODO: fix this - currently using wrong chain
async function generateAuth() {
  const wallet = new ethers.Wallet(process.env.PRIVATE_KEY);
  
  // WRONG: missing required SIWE fields
  const message = `Sign in to trading bot
Address: ${wallet.address}`;
  
  const sig = await wallet.signMessage(message);
  console.log('sig:', sig);
}
"""
(workspace / "src" / "api" / "middleware" / "siwe-draft.js").write_text(bad_siwe_attempt)

print("Workspace generated successfully.")
print(f"Files created: {len(list(workspace.rglob('*')))}")