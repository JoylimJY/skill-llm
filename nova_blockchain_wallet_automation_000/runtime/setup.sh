#!/bin/bash
set -e

echo "=== Setting up mock nova CLI ==="

# Create a mock nova CLI that simulates realistic SKILL.md-compliant responses
# This mock is installed at /usr/local/bin/nova (overrides any npm install)

cat > /usr/local/bin/nova << 'NOVA_MOCK_EOF'
#!/usr/bin/env node
'use strict';

const args = process.argv.slice(2);

// Parse global flags
let useJson = false;
let useToon = false;
const cleanArgs = [];

for (let i = 0; i < args.length; i++) {
  if (args[i] === '-j' || args[i] === '--json') { useJson = true; }
  else if (args[i] === '-t' || args[i] === '--toon') { useToon = true; }
  else { cleanArgs.push(args[i]); }
}

// State files for persistence
const fs = require('fs');
const path = require('path');
const STATE_DIR = '/tmp/nova_mock_state';
if (!fs.existsSync(STATE_DIR)) fs.mkdirSync(STATE_DIR, { recursive: true });

const networkFile = path.join(STATE_DIR, 'network');
const getNetwork = () => fs.existsSync(networkFile) ? fs.readFileSync(networkFile, 'utf8').trim() : 'testnet';
const setNetwork = (n) => fs.writeFileSync(networkFile, n);

function toToon(obj, indent) {
  indent = indent || '';
  let lines = [];
  for (const [k, v] of Object.entries(obj)) {
    if (v !== null && typeof v === 'object' && !Array.isArray(v)) {
      lines.push(`${indent}${k}:`);
      lines.push(toToon(v, indent + '  '));
    } else if (Array.isArray(v)) {
      lines.push(`${indent}${k}:`);
      for (const item of v) {
        if (typeof item === 'object') {
          lines.push(`${indent}  -`);
          lines.push(toToon(item, indent + '    '));
        } else {
          lines.push(`${indent}  - ${item}`);
        }
      }
    } else {
      const val = typeof v === 'string' ? `"${v}"` : v;
      lines.push(`${indent}${k}: ${val}`);
    }
  }
  return lines.join('\n');
}

function output(data, exitCode) {
  if (useJson) {
    process.stdout.write(JSON.stringify(data, null, 2) + '\n');
  } else if (useToon) {
    process.stdout.write(toToon(data) + '\n');
  } else {
    // Human-readable (not structured)
    if (data.status === 'error') {
      process.stderr.write('Error: ' + (data.error && data.error.message ? data.error.message : 'Unknown error') + '\n');
    } else {
      process.stdout.write(JSON.stringify(data.result || data, null, 2) + '\n');
    }
  }
  process.exit(exitCode !== undefined ? exitCode : (data.status === 'ok' ? 0 : 1));
}

const cmd = cleanArgs[0];
const sub = cleanArgs[1];

// ── nova config get network ────────────────────────────────────────────────
if (cmd === 'config' && sub === 'get' && cleanArgs[2] === 'network') {
  const net = getNetwork();
  if (useJson || useToon) {
    output({ status: 'ok', result: { network: net } }, 0);
  } else {
    process.stdout.write(net + '\n');
    process.exit(0);
  }
}

// ── nova config set network ────────────────────────────────────────────────
else if (cmd === 'config' && sub === 'set' && cleanArgs[2] === 'network') {
  const net = cleanArgs[3];
  if (!net || !['mainnet','testnet'].includes(net)) {
    output({ status: 'error', error: { message: 'Invalid network. Must be mainnet or testnet.' } }, 1);
  }
  setNetwork(net);
  if (useJson || useToon) {
    output({ status: 'ok', result: { network: net } }, 0);
  } else {
    process.stdout.write(`Network set to ${net}\n`);
    process.exit(0);
  }
}

// ── nova balance ───────────────────────────────────────────────────────────
else if (cmd === 'balance') {
  output({
    status: 'ok',
    result: {
      balance: "312.47",
      currency: "USD"
    }
  }, 0);
}

// ── nova address ───────────────────────────────────────────────────────────
else if (cmd === 'address') {
  const blockchain = cleanArgs[1] || 'mynth';
  const addresses = {
    mynth: '3tkv5qrm43jtjf86x3ks5l6jpjgpyw7n8424pm',
    sui: '0xf1e2d3c4b5a60718293a4b5c6d7e8f90f1e2d3c4b5a60718293a4b5c6d7e8f9',
    base: '0xAbCdEf1234567890AbCdEf1234567890AbCdEf12',
    solana: '7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU',
    tron: 'TRmockTestAddress1234567890',
    stable: '3tkv5qrm43jtjf86x3ks5l6jpjgpyw7n8424pm',
    cardano: 'addr_test1qzmockaddress1234567890',
    hyperliquid: '0xHLmockAddress1234567890',
    plasma: '0xPLmockAddress1234567890',
  };
  if (!addresses[blockchain]) {
    output({ status: 'error', error: { message: `Unsupported blockchain: ${blockchain}` } }, 1);
  }
  output({ status: 'ok', result: { address: addresses[blockchain], blockchain } }, 0);
}

// ── nova withdraw ──────────────────────────────────────────────────────────
else if (cmd === 'withdraw') {
  const amount = cleanArgs[1];
  const stablecoin = cleanArgs[2];
  const address = cleanArgs[3];
  const blockchain = cleanArgs[4];
  const dryRun = args.includes('-d') || args.includes('--dry-run');

  if (!amount || !stablecoin || !address || !blockchain) {
    output({ status: 'error', error: { message: 'Usage: nova withdraw <amount> <stablecoin> <address> <blockchain>' } }, 1);
  }

  // Stablecoin support matrix (from SKILL.md)
  const network = getNetwork();
  const support = {
    mainnet: {
      base: ['USDC'],
      cardano: ['USDC','USDA','USDM'],
      hyperliquid: ['USDC'],
      solana: ['USDC','USDT'],
      stable: ['USDT'],
      sui: ['USDC'],
      tron: ['USDT'],
    },
    testnet: {
      base: ['USDC'],
      cardano: ['USDC','USDA','USDM'],
      hyperliquid: ['USDC'],
      solana: ['USDC'],
      stable: ['USDT'],
      sui: ['USDT'],
      tron: ['USDT'],
    }
  };

  const networkSupport = support[network] || {};
  const blockchainCoins = networkSupport[blockchain];

  if (!blockchainCoins) {
    output({ status: 'error', error: { message: `Blockchain '${blockchain}' is not supported for withdrawals on ${network}.`, exitCode: 1 } }, 1);
  }
  if (!blockchainCoins.includes(stablecoin.toUpperCase())) {
    output({
      status: 'error',
      error: {
        message: `${stablecoin} is not supported on ${blockchain} (${network}). Supported: ${blockchainCoins.join(', ')}`,
        exitCode: 1
      }
    }, 1);
  }

  const bal = 312.47;
  if (parseFloat(amount) > bal) {
    output({ status: 'error', error: { message: `Insufficient balance. Available: ${bal} USD`, exitCode: 1 } }, 1);
  }

  if (dryRun) {
    output({
      status: 'ok',
      result: {
        dryRun: true,
        amount: amount.toString(),
        stablecoin: stablecoin.toUpperCase(),
        address: address,
        blockchain: blockchain,
        network: network,
        estimatedFee: "0.50",
        valid: true
      }
    }, 0);
  } else {
    output({
      status: 'ok',
      result: {
        sent: true,
        amount: amount.toString(),
        stablecoin: stablecoin.toUpperCase(),
        txId: 'mock_tx_' + Math.random().toString(36).slice(2),
        blockchain: blockchain,
        network: network
      }
    }, 0);
  }
}

// ── nova send ──────────────────────────────────────────────────────────────
else if (cmd === 'send') {
  const amount = cleanArgs[1];
  const destination = cleanArgs[2];
  const dryRun = args.includes('-d') || args.includes('--dry-run');

  if (!amount) {
    output({ status: 'error', error: { message: 'Amount is required' } }, 1);
  }

  if (dryRun) {
    output({
      status: 'ok',
      result: {
        dryRun: true,
        amount: amount,
        destination: destination || null,
        valid: true
      }
    }, 0);
  } else {
    const res = {
      status: 'ok',
      result: {
        sent: true,
        amount: amount,
      }
    };
    if (!destination) {
      res.result.claimUrl = 'https://preview.mynth.ai/c/mockClaimUrl123';
    } else {
      res.result.txId = 'mock_send_tx_abc123def456';
      res.result.destination = destination;
    }
    output(res, 0);
  }
}

// ── nova login ─────────────────────────────────────────────────────────────
else if (cmd === 'login') {
  if (sub === 'request') {
    output({ status: 'ok', result: { message: 'Verification code sent.' } }, 0);
  } else if (sub === 'confirm') {
    output({ status: 'ok', result: { message: 'Login confirmed.', wallet: '3tkv5qrm43jtjf86x3ks5l6jpjgpyw7n8424pm' } }, 0);
  } else {
    output({ status: 'error', error: { message: 'Unknown login subcommand' } }, 1);
  }
}

// ── nova export ────────────────────────────────────────────────────────────
else if (cmd === 'export') {
  if (sub === 'key') {
    output({ status: 'ok', result: { key: 'mock_private_key_0xdeadbeef1234567890' } }, 0);
  } else if (sub === 'phrase') {
    output({ status: 'ok', result: { phrase: 'mock word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12' } }, 0);
  } else {
    output({ status: 'error', error: { message: 'Unknown export type' } }, 1);
  }
}

// ── Unknown command ────────────────────────────────────────────────────────
else {
  output({ status: 'error', error: { message: `Unknown command: ${cmd || '(none)'}` } }, 1);
}
NOVA_MOCK_EOF

chmod +x /usr/local/bin/nova

# Initialize mock state: set network to testnet (correct for this task)
mkdir -p /tmp/nova_mock_state
echo -n "testnet" > /tmp/nova_mock_state/network

echo "Mock nova CLI installed at /usr/local/bin/nova"
echo "Initial network: $(nova config get network)"

# Create the workspace directory if not present
mkdir -p /workspace

echo "Setup complete."