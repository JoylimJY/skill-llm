import os
import random
import json

random.seed(42)

workspace = "/workspace"

# Create a realistic DeFi project structure with distractor files
dirs = [
    "treasury/config",
    "treasury/scripts",
    "treasury/logs",
    "treasury/backups",
    "agents/rebalancer",
    "agents/monitor",
    "agents/utils",
    "contracts/abis",
    "contracts/addresses",
    "data/prices",
    "data/history",
    "docs",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files

# 1. Old incorrect vault script (uses wrong API - wrong method names)
with open(os.path.join(workspace, "treasury/scripts/old_vault.ts"), "w") as f:
    f.write("""// DEPRECATED - do not use
import { VaultSDK } from 'old-vault-sdk';
const sdk = new VaultSDK();
sdk.createVault({ name: 'old-vault', type: 'fast' }); // wrong API
sdk.getBalance('ethereum'); // wrong chain casing
sdk.sendTx({ to: '0x...', value: 100000000000000000 }); // wrong amount type
""")

# 2. Distractor: wrong amount types script
with open(os.path.join(workspace, "agents/rebalancer/wrong_amounts.ts"), "w") as f:
    f.write("""// BUG: uses number for send, bigint for swap - WRONG
const payload = await vault.prepareSendTx({
  coin: { chain: 'Ethereum', address: addr, decimals: 18, ticker: 'ETH' },
  receiver: '0xabc...',
  amount: 100000000000000000, // should be BigInt!
});
const quote = await vault.getSwapQuote({
  fromCoin: { chain: 'Ethereum', address: addr, decimals: 18, ticker: 'ETH' },
  toCoin: { chain: 'Ethereum', address: addr2, decimals: 6, ticker: 'USDC', id: '0xA0b...'},
  amount: BigInt('100000'), // should be number!
});
""")

# 3. Distractor: incomplete send flow (missing broadcast)
with open(os.path.join(workspace, "agents/rebalancer/incomplete_send.ts"), "w") as f:
    f.write("""// BUG: Missing broadcastTx step
const payload = await vault.prepareSendTx({ ... });
const sig = await vault.sign(payload);
// forgot broadcastTx!
""")

# 4. Distractor config
with open(os.path.join(workspace, "treasury/config/chains.json"), "w") as f:
    json.dump({
        "supported_chains": ["ethereum", "bitcoin", "solana"],  # wrong casing - distractor
        "rpc_urls": {
            "ethereum": "https://mainnet.infura.io/v3/...",
        }
    }, f, indent=2)

# 5. Token addresses reference file
with open(os.path.join(workspace, "contracts/addresses/tokens.json"), "w") as f:
    json.dump({
        "USDC_ETH": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "USDT_ETH": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "WBTC_ETH": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        "USDC_POLYGON": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    }, f, indent=2)

# 6. Distractor: wrong token send (missing id field)
with open(os.path.join(workspace, "agents/rebalancer/broken_token_send.ts"), "w") as f:
    f.write("""// BUG: Missing 'id' field for token contract - will send ETH instead of USDC
const payload = await vault.prepareSendTx({
  coin: {
    chain: 'Ethereum',
    address: senderAddr,
    decimals: 6,
    ticker: 'USDC',
    // missing: id: '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'
  },
  receiver: recipientAddr,
  amount: BigInt('50000000'),
});
""")

# 7. Distractor: wrong chain names
with open(os.path.join(workspace, "agents/monitor/chain_config.ts"), "w") as f:
    f.write("""// WARNING: Chain names below are wrong (lowercase)
const chains = ['bitcoin', 'ethereum', 'solana', 'polygon'];
// Correct: 'Bitcoin', 'Ethereum', 'Solana', 'Polygon'
""")

# 8. Distractor: old swap flow without approval check
with open(os.path.join(workspace, "agents/rebalancer/old_swap.ts"), "w") as f:
    f.write("""// BUG: Missing approval step for ERC-20 swaps
const quote = await vault.getSwapQuote({ ... });
const swapResult = await vault.prepareSwapTx({ ... });
// forgot: if (swapResult.approvalPayload) { ... }
const sig = await vault.sign(swapResult.keysignPayload);
await vault.broadcastTx({ chain: 'Ethereum', keysignPayload: swapResult.keysignPayload, signature: sig });
""")

# 9. Price history distractor
with open(os.path.join(workspace, "data/prices/eth_usd.json"), "w") as f:
    json.dump({"prices": [{"date": "2024-01-01", "price": 2200.5}]}, f)

# 10. Distractor: wrong storage class
with open(os.path.join(workspace, "agents/utils/storage_attempt.ts"), "w") as f:
    f.write("""// WRONG: FileStorage is not exported from @vultisig/sdk
import { Vultisig, FileStorage } from '@vultisig/sdk';
// MemoryStorage is the only storage exported from the SDK
const sdk = new Vultisig({ storage: new FileStorage('./vault.json') });
""")

# 11. Distractor: tx explorer usage attempt
with open(os.path.join(workspace, "treasury/logs/tx_log.json"), "w") as f:
    json.dump([
        {"chain": "Ethereum", "txHash": "0xabc123", "status": "pending"},
        {"chain": "Bitcoin", "txHash": "txid_xyz", "status": "confirmed"}
    ], f, indent=2)

# 12. Vault backup placeholder
with open(os.path.join(workspace, "treasury/backups/README_backup.txt"), "w") as f:
    f.write("Place .vult backup files here. Password required to restore.\n")

# 13. Distractor: secure vault code (agent should use Fast Vault)
with open(os.path.join(workspace, "agents/monitor/secure_vault_attempt.ts"), "w") as f:
    f.write("""// WRONG for automated agents: SecureVault requires human QR scan
const { vault } = await sdk.createSecureVault({
  name: 'bad-choice',
  onQRCodeReady: (qr) => console.log(qr),
  onDeviceJoined: (id, total, req) => {},
});
// This blocks until a human scans the QR - not suitable for autonomous agents
""")

# 14. Documentation distractor
with open(os.path.join(workspace, "docs/old_api_reference.md"), "w") as f:
    f.write("""# OLD API Reference (v0.1 - DEPRECATED)
## createVault(name, type)
## sendTransaction(chain, to, amount)  <- amount in ether (not wei!)
## getBalance(chain)
""")

# 15. Package.json for the project
with open(os.path.join(workspace, "package.json"), "w") as f:
    json.dump({
        "name": "treasury-automation",
        "version": "1.0.0",
        "description": "DeFi treasury management automation",
        "scripts": {
            "typecheck": "tsc --noEmit"
        },
        "dependencies": {},
        "devDependencies": {
            "typescript": "^5.0.0",
            "@types/node": "^20.0.0"
        }
    }, f, indent=2)

# 16. tsconfig
with open(os.path.join(workspace, "tsconfig.json"), "w") as f:
    json.dump({
        "compilerOptions": {
            "target": "ES2020",
            "module": "commonjs",
            "lib": ["ES2020"],
            "strict": True,
            "esModuleInterop": True,
            "skipLibCheck": True,
            "outDir": "./dist"
        },
        "include": ["treasury/scripts/*.ts", "agents/**/*.ts"]
    }, f, indent=2)

# THE ACTUAL TASK SPECIFICATION FILE (business requirements only, no hints)
with open(os.path.join(workspace, "treasury/config/automation_requirements.md"), "w") as f:
    f.write("""# Treasury Automation Requirements

## Goal
Build an autonomous DeFi treasury management script.

## Business Requirements

### Vault Setup
- The system must use an autonomous vault (no human approval required)
- Vault name: "treasury-agent"
- Email: "treasury@defi-corp.io"
- Password: "Tr3asury$ecure2024!"

### Address Book
After vault creation and verification, register the following contacts:
- Name: "Cold Storage BTC", Chain: Bitcoin, Address: "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"
- Name: "Partner ETH", Chain: Ethereum, Address: "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"

### Balance Check
After setting up the address book, check:
1. Native ETH balance on Ethereum
2. USDC token balance on Ethereum (contract: 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48)

### Conditional Send
If the USDC balance amount is greater than 0, send exactly 50 USDC to "0x742d35Cc6634C0532925a3b844Bc454e4438f44e".
- USDC has 6 decimal places
- The amount to send is: 50 USDC (50,000,000 in base units)

### Token Swap
Perform a swap of 0.5 ETH to USDC:
- Source: ETH on Ethereum
- Destination: USDC on Ethereum (contract: 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48)
- If the quote has warnings, log them but proceed
- Handle any required token approvals before the swap

### Post-Transaction
After broadcasting the swap, get the Ethereum explorer URL for the swap transaction hash.

## Output
Save the complete automation script as: treasury/scripts/treasury_automation.ts
""")

print("Workspace setup complete.")
print(f"Created {len(dirs)} directories and 16+ distractor/context files.")