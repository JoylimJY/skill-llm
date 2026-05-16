import os
import json
import random

random.seed(42)

workspace = "/workspace"

# --- Directory structure ---
dirs = [
    "projects/raw_data",
    "projects/historical",
    "config",
    "reports",
    "market_data/daily",
    "market_data/weekly",
    "team_profiles",
    "chain_snapshots/eth",
    "chain_snapshots/bsc",
    "logs",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractor_logs = [
    ("logs/fetch_20240101.log", "INFO: Fetching chain data...\nERROR: Timeout on BSC node\nINFO: Retry 1/3\n"),
    ("logs/fetch_20240102.log", "INFO: ETH data fetched successfully\nINFO: BSC data fetched successfully\n"),
    ("logs/audit_errors.log", "ERROR: Contract 0xDEAD... not verified\nWARNING: LP lock unconfirmed\n"),
    ("market_data/daily/btc_20240301.csv", "date,open,high,low,close\n2024-03-01,62000,63500,61000,62800\n"),
    ("market_data/weekly/summary.json", json.dumps({"week": "2024-W09", "topGainers": ["ETH","BNB"], "topLosers": ["SHIB","FLOKI"]})),
    ("market_data/daily/eth_20240301.csv", "date,open,high,low,close\n2024-03-01,3200,3400,3150,3380\n"),
    ("config/node_endpoints.json", json.dumps({"eth": "https://mainnet.infura.io/v3/PLACEHOLDER", "bsc": "https://bsc-dataseed.binance.org", "sol": "https://api.mainnet-beta.solana.com"})),
    ("config/risk_thresholds.json", json.dumps({"low_risk_max": 30, "medium_risk_max": 60, "high_risk_min": 61})),
    ("config/audit_config.yaml", "version: 2\nmax_retries: 3\ntimeout_seconds: 30\nenable_social_scan: true\n"),
    ("team_profiles/profile_template.json", json.dumps({"name": "", "role": "", "linkedin": "", "github": "", "doxxed": False})),
    ("chain_snapshots/eth/snapshot_20240301.json", json.dumps({"block": 19400000, "timestamp": "2024-03-01T00:00:00Z", "gasPrice": "25 gwei"})),
    ("chain_snapshots/bsc/snapshot_20240301.json", json.dumps({"block": 37200000, "timestamp": "2024-03-01T00:00:00Z", "gasPrice": "3 gwei"})),
    ("projects/historical/archived_projects.txt", "OldToken1\nRugPull99\nSafeMoon_clone3\nMoonElonDoge\n"),
    ("projects/historical/exit_scam_report_2023.txt", "Projects confirmed as exit scams in 2023:\n- MoonSafe (lost $2.3M)\n- DogePad (lost $890K)\n"),
]
for fname, content in distractor_logs:
    with open(os.path.join(workspace, fname), "w", encoding="utf-8") as f:
        f.write(content)

# --- Project raw data files (messy, inconsistent keys) ---

alphaswap_data = {
    "proj_name": "AlphaSwap",
    "contract_addr": "0xA1B2C3D4E5F6a1b2c3d4e5f6A1B2C3D4E5F6A1B2",
    "chain": "ETH",
    "source_code_verified": True,
    "lp_lock_status": "LOCKED",
    "lp_lock_days": 90,
    "team_doxxed": False,
    "top10_holders_pct": 78.5,
    "marketcap_usd": 320000,
    "volume_24h_usd": 8200,
    "holder_addresses": 412,
    "launch_days_ago": 3,
    "social_media": {
        "twitter_followers": 340,
        "telegram_members": 180,
        "last_post_days_ago": 5
    },
    "contract_flags": ["mint_function_present", "no_timelock"],
    "audit_notes_raw": "contract has mint; team anonymous; very low volume; low holder count; LP only 90 days"
}

betafarm_data = {
    "name": "BetaFarm",
    "address": "0xB9C8D7E6F5a4B9C8D7E6F5A4B9C8D7E6F5A4B9C8",
    "blockchain": "BSC",
    "verified_source": True,
    "liquidity_lock": {
        "locked": True,
        "lock_duration_days": 365
    },
    "team_info": {
        "publicly_identified": True,
        "linkedin_verified": True
    },
    "tokenomics": {
        "top_10_wallet_concentration": 42.1,
        "market_cap": 1800000,
        "daily_volume": 95000,
        "unique_holders": 3840
    },
    "age_days": 45,
    "social": {
        "twitter": 12000,
        "telegram": 8900,
        "last_activity_days_ago": 1
    },
    "flags": [],
    "notes": "solid fundamentals, team known, good volume"
}

gammapool_data = {
    "token": "GammaPool",
    "contract": "0xC3D4E5F6A1B2C3D4E5F6a1b2c3d4e5f6C3D4E5F6",
    "network": "BSC",
    "open_source": False,
    "lp_locked": False,
    "lp_lock_duration": 0,
    "anonymous_team": True,
    "concentration": {
        "top10_percent": 91.2
    },
    "mcap": 75000,
    "vol_24h": 1200,
    "holders": 89,
    "days_since_launch": 1,
    "socials": {
        "twitter_count": 45,
        "tg_count": 22,
        "inactive_days": 2
    },
    "red_flags": ["unverified_contract", "no_lp_lock", "anonymous_team", "whale_concentration"],
    "raw_notes": "DANGER: contract not open source, no LP lock, only 89 holders, launched yesterday, whale wallets"
}

deltatoken_data = {
    "project": "DeltaToken",
    "ca": "0xD5E6F7A8B9C0D5E6F7A8B9C0d5e6f7a8b9c0D5E6",
    "chain": "SOL",
    "is_verified": True,
    "lp_lock": True,
    "lp_lock_days": 720,
    "team_doxxed": True,
    "top_10_concentration": 28.5,
    "market_cap": 8500000,
    "volume_24h": 420000,
    "total_holders": 18500,
    "days_live": 210,
    "twitter_followers": 45000,
    "telegram": 31000,
    "last_social_activity": 0,
    "contract_issues": [],
    "notes": "Strong fundamentals, large holder base, very active community"
}

epsilon_data = {
    "nm": "EpsilonMoon",
    "addr": "0xE7F8A9B0C1D2E7F8A9B0C1d2e7f8a9b0c1D2E7F8",
    "net": "ETH",
    "src_open": True,
    "liq_locked": True,
    "liq_lock_d": 30,
    "team_anon": True,
    "top10_pct": 58.9,
    "mktcap": 210000,
    "vol": 5600,
    "holders": 623,
    "launched_d": 14,
    "tw_follow": 1200,
    "tg_mem": 780,
    "last_tw_d": 3,
    "flags_raw": ["short_lp_lock", "anonymous_team"],
    "memo": "medium risk, some concerns about team and lp lock duration"
}

# Write project files
projects = [
    ("projects/raw_data/alphaswap.json", alphaswap_data),
    ("projects/raw_data/betafarm.json", betafarm_data),
    ("projects/raw_data/gammapool.json", gammapool_data),
    ("projects/raw_data/deltatoken.json", deltatoken_data),
    ("projects/raw_data/epsilon.json", epsilon_data),
]
for fname, data in projects:
    with open(os.path.join(workspace, fname), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Batch project list file
batch_list = "AlphaSwap\nBetaFarm\nGammaPool\nDeltaToken\nEpsilonMoon\n"
with open(os.path.join(workspace, "projects/batch_projects.txt"), "w", encoding="utf-8") as f:
    f.write(batch_list)

# A misleading "report template" that has WRONG format to trap agents
wrong_template = """# Security Audit Template (DEPRECATED - DO NOT USE)
## Risk Score: XX/100
## Safe: 
## Risks:
## Advice:
"""
with open(os.path.join(workspace, "projects/DEPRECATED_template.txt"), "w", encoding="utf-8") as f:
    f.write(wrong_template)

print("Workspace generated successfully.")
print("Projects:", [p[0] for p in projects])