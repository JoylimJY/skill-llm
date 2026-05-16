import os
import random
import csv

random.seed(42)

# Create directory structure
dirs = [
    "workspace/scripts",
    "workspace/data/market",
    "workspace/data/portfolio",
    "workspace/reports/archive",
    "workspace/reports/drafts",
    "workspace/config",
    "workspace/logs",
    "workspace/tmp",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# --- MAIN TASK INPUT: contracts_to_review.csv ---
contracts = [
    ("SAFEMOON2", "0xA1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0"),
    ("RUGPULL_INU", "0xDEAD000000000000000042069420694206942069"),
    ("SOLIDGEM",   "0x1234567890abcdef1234567890abcdef12345678"),
    ("WHALETOKEN", "0xFEDCBA9876543210FEDCBA9876543210FEDCBA98"),
    ("HONEYPOT_X", "0x0000000000000000000000000000000000000001"),
]

with open("workspace/contracts_to_review.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["token_name", "contract_address", "chain", "proposed_allocation_usd"])
    writer.writerow(["SAFEMOON2",   "0xA1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0", "BSC",      "50000"])
    writer.writerow(["RUGPULL_INU", "0xDEAD000000000000000042069420694206942069", "BSC",      "20000"])
    writer.writerow(["SOLIDGEM",   "0x1234567890abcdef1234567890abcdef12345678", "ETH",      "100000"])
    writer.writerow(["WHALETOKEN", "0xFEDCBA9876543210FEDCBA9876543210FEDCBA98", "ETH",      "75000"])
    writer.writerow(["HONEYPOT_X", "0x0000000000000000000000000000000000000001", "POLYGON",  "30000"])

# --- DISTRACTOR FILES ---

# 1. Old market data
with open("workspace/data/market/btc_price_history.csv", "w") as f:
    f.write("date,open,high,low,close\n")
    for i in range(30):
        f.write(f"2024-{(i%12)+1:02d}-01,{random.randint(20000,70000)},{random.randint(20000,70000)},{random.randint(20000,70000)},{random.randint(20000,70000)}\n")

# 2. Portfolio allocation
with open("workspace/data/portfolio/allocations_q3.csv", "w") as f:
    f.write("asset,weight,value_usd\n")
    f.write("BTC,0.4,400000\n")
    f.write("ETH,0.3,300000\n")
    f.write("USDT,0.3,300000\n")

# 3. Old report (wrong format, distractor)
with open("workspace/reports/archive/risk_report_2023.txt", "w") as f:
    f.write("LEGACY RISK REPORT 2023\n")
    f.write("Manually compiled. Not machine readable.\n")
    f.write("Token XYZ: HIGH RISK\n")
    f.write("Token ABC: LOW RISK\n")

# 4. Draft notes
with open("workspace/reports/drafts/notes.txt", "w") as f:
    f.write("TODO: automate token screening\n")
    f.write("Check contract addresses before investing\n")
    f.write("Ask compliance team about rug pull detection\n")

# 5. Config file (distractor)
with open("workspace/config/portfolio_config.json", "w") as f:
    f.write('{\n  "max_meme_allocation_pct": 5,\n  "risk_tolerance": "medium",\n  "chains": ["BSC", "ETH", "POLYGON"]\n}\n')

# 6. Another config
with open("workspace/config/alert_thresholds.yaml", "w") as f:
    f.write("price_drop_pct: 20\nvolume_spike: 5x\nliquidity_drop_pct: 30\n")

# 7. Log file
with open("workspace/logs/screening_run_old.log", "w") as f:
    f.write("[2024-01-15 10:23:11] Started screening job\n")
    f.write("[2024-01-15 10:23:45] Processed 3 contracts\n")
    f.write("[2024-01-15 10:24:00] Job finished\n")

# 8. Temp file
with open("workspace/tmp/scratch.txt", "w") as f:
    f.write("temporary scratch space - ignore\n")

# 9. Market analysis distractor
with open("workspace/data/market/defi_tvl_snapshot.csv", "w") as f:
    f.write("protocol,tvl_usd,chain\n")
    f.write("Uniswap,3200000000,ETH\n")
    f.write("PancakeSwap,1800000000,BSC\n")
    f.write("AAVE,850000000,ETH\n")

# 10. Another portfolio file
with open("workspace/data/portfolio/watchlist.txt", "w") as f:
    f.write("Tokens under consideration (NOT yet screened):\n")
    f.write("- PEPE2\n- SHIB3\n- DOGE_KILLER\n")

# 11. Stale fee estimate (wrong - distractor)
with open("workspace/reports/drafts/fee_estimate.txt", "w") as f:
    f.write("Estimated screening cost: TBD\n")
    f.write("Manual estimate: maybe $5 per token?\n")

# 12. An empty placeholder
with open("workspace/tmp/output_placeholder.json", "w") as f:
    f.write("{}\n")

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk("workspace"):
    for fname in files:
        print(f"  {os.path.join(root, fname)}")