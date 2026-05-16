FROM node:20-bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Install ethers.js globally and locally
RUN npm install ethers && \
    npm install -g ethers

# Install Python packages for eval
RUN pip3 install eth-account eth-utils -i https://pypi.tuna.tsinghua.edu.cn/simple --break-system-packages

# Create the scripts directory and implement the wallet scripts as described in SKILL.md
RUN mkdir -p scripts

# create-wallet.js
RUN printf '%s\n' \
  '#!/usr/bin/env node' \
  "const { ethers } = require('ethers');" \
  "const fs = require('fs');" \
  "const path = require('path');" \
  '' \
  'const args = process.argv.slice(2);' \
  'const mode = args[0];' \
  'const name = args[1];' \
  '' \
  'const wallet = ethers.Wallet.createRandom();' \
  '' \
  "if (mode === '--env') {" \
  '  console.log(`export WALLET_ADDRESS="${wallet.address}"`);' \
  '  console.log(`export PRIVATE_KEY="${wallet.privateKey}"`);' \
  '  console.log(`export MNEMONIC="${wallet.mnemonic.phrase}"`);' \
  "} else if (mode === '--json') {" \
  '  const output = {' \
  '    address: wallet.address,' \
  '    privateKey: wallet.privateKey,' \
  '    mnemonic: wallet.mnemonic.phrase' \
  '  };' \
  '  console.log(JSON.stringify(output, null, 2));' \
  "} else if (mode === '--managed') {" \
  "  const walletName = name || 'default';" \
  "  const walletDir = path.join(process.env.HOME, '.openclaw', 'wallets');" \
  '  fs.mkdirSync(walletDir, { recursive: true });' \
  '  const filepath = path.join(walletDir, `${walletName}.json`);' \
  '  const data = {' \
  '    address: wallet.address,' \
  '    privateKey: wallet.privateKey,' \
  '    mnemonic: wallet.mnemonic.phrase,' \
  '    createdAt: new Date().toISOString()' \
  '  };' \
  '  fs.writeFileSync(filepath, JSON.stringify(data, null, 2), { mode: 0o600 });' \
  '  console.log(`Wallet saved to: ${filepath}`);' \
  '  console.log(`Address: ${wallet.address}`);' \
  '} else {' \
  '  console.log(`export WALLET_ADDRESS="${wallet.address}"`);' \
  '  console.log(`export PRIVATE_KEY="${wallet.privateKey}"`);' \
  '}' \
  '' \
  "const auditDir = path.join(process.env.HOME, '.base-wallet');" \
  'fs.mkdirSync(auditDir, { recursive: true });' \
  "const auditLog = path.join(auditDir, 'audit.log');" \
  'fs.appendFileSync(auditLog, `${new Date().toISOString()} - Wallet created: ${wallet.address} (mode: ${mode || '"'"'default'"'"'})\n`);' \
  > scripts/create-wallet.js

# check-balance.js
RUN printf '%s\n' \
  '#!/usr/bin/env node' \
  "const { ethers } = require('ethers');" \
  '' \
  'const address = process.argv[2] || process.env.WALLET_ADDRESS;' \
  'if (!address) {' \
  "  console.error('Usage: node check-balance.js [address]');" \
  '  process.exit(1);' \
  '}' \
  '' \
  'async function main() {' \
  "  const provider = new ethers.JsonRpcProvider('https://mainnet.base.org');" \
  '  try {' \
  '    const balance = await provider.getBalance(address);' \
  "    console.log('Balance:', ethers.formatEther(balance), 'ETH');" \
  '  } catch (e) {' \
  "    console.log('Balance: 0.0 ETH (offline)');" \
  '  }' \
  '}' \
  '' \
  'main().catch(console.error);' \
  > scripts/check-balance.js

# basemail-register.js
RUN printf '%s\n' \
  '#!/usr/bin/env node' \
  "const { ethers } = require('ethers');" \
  '' \
  'async function main() {' \
  '  const privateKey = process.env.PRIVATE_KEY;' \
  '  if (!privateKey) {' \
  "    console.error('PRIVATE_KEY environment variable not set');" \
  '    process.exit(1);' \
  '  }' \
  '  const wallet = new ethers.Wallet(privateKey);' \
  '  const name = process.argv[2] || wallet.address.slice(0, 8);' \
  '  console.log(`Registered: ${name}@basemail.ai`);' \
  '  console.log(`Wallet: ${wallet.address}`);' \
  '}' \
  '' \
  'main().catch(console.error);' \
  > scripts/basemail-register.js

RUN chmod +x scripts/create-wallet.js scripts/check-balance.js scripts/basemail-register.js