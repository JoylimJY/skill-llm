#!/bin/bash
set -e

# Create the scripts directory if it doesn't exist
mkdir -p /workspace/scripts

# Create the mock meme_detector.py script in workspace/scripts/
# This script produces DETERMINISTIC output based on the contract address
cat > /workspace/scripts/meme_detector.py << 'PYEOF'
#!/usr/bin/env python3
import sys
import hashlib

if len(sys.argv) < 2:
    print("Usage: python scripts/meme_detector.py <CONTRACT_ADDRESS>")
    sys.exit(1)

contract = sys.argv[1]

# Deterministic "detection" based on contract address hash
h = int(hashlib.sha256(contract.encode()).hexdigest(), 16)

# Predefined outcomes for our specific test contracts
OUTCOMES = {
    "0xA1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0": {
        "score": 72,
        "risk": "中等",
        "emoji": "🟡",
        "lp_locked": True,
        "lp_detail": "已锁定90天",
        "mintable": False,
        "buy_tax": 5,
        "sell_tax": 5,
        "whale_pct": 45,
        "audited": False,
    },
    "0xDEAD000000000000000042069420694206942069": {
        "score": 18,
        "risk": "危险",
        "emoji": "🔴",
        "lp_locked": False,
        "lp_detail": "未锁定",
        "mintable": True,
        "buy_tax": 15,
        "sell_tax": 99,
        "whale_pct": 82,
        "audited": False,
    },
    "0x1234567890abcdef1234567890abcdef12345678": {
        "score": 91,
        "risk": "安全",
        "emoji": "🟢",
        "lp_locked": True,
        "lp_detail": "已锁定365天",
        "mintable": False,
        "buy_tax": 2,
        "sell_tax": 2,
        "whale_pct": 18,
        "audited": True,
    },
    "0xFEDCBA9876543210FEDCBA9876543210FEDCBA98": {
        "score": 54,
        "risk": "中等",
        "emoji": "🟡",
        "lp_locked": True,
        "lp_detail": "已锁定30天",
        "mintable": False,
        "buy_tax": 3,
        "sell_tax": 8,
        "whale_pct": 67,
        "audited": False,
    },
    "0x0000000000000000000000000000000000000001": {
        "score": 7,
        "risk": "危险",
        "emoji": "🔴",
        "lp_locked": False,
        "lp_detail": "未锁定",
        "mintable": True,
        "buy_tax": 0,
        "sell_tax": 100,
        "whale_pct": 95,
        "audited": False,
    },
}

if contract in OUTCOMES:
    o = OUTCOMES[contract]
else:
    # Fallback deterministic generation
    score = h % 101
    if score >= 80:
        risk, emoji = "安全", "🟢"
    elif score >= 50:
        risk, emoji = "中等", "🟡"
    else:
        risk, emoji = "危险", "🔴"
    o = {
        "score": score,
        "risk": risk,
        "emoji": emoji,
        "lp_locked": bool(h % 2),
        "lp_detail": "已锁定180天" if bool(h % 2) else "未锁定",
        "mintable": bool((h >> 1) % 2),
        "buy_tax": (h >> 2) % 20,
        "sell_tax": (h >> 4) % 30,
        "whale_pct": 20 + (h >> 6) % 70,
        "audited": bool((h >> 8) % 3 == 0),
    }

lp_icon = "✅" if o["lp_locked"] else "❌"
mint_icon = "✅" if not o["mintable"] else "❌"
tax_icon = "⚠️" if (o["buy_tax"] > 0 or o["sell_tax"] > 0) else "✅"
whale_icon = "❌" if o["whale_pct"] > 40 else "✅"
audit_icon = "✅" if o["audited"] else "⚠️"

print("🔍 Meme币安全检测")
print("━━━━━━━━━━━━━━━━")
print(f"📋 地址: {contract}")
print(f"{o['emoji']} 评分: {o['score']}/100 ({o['risk']})")
print()
print("检测项目:")
print(f"  {lp_icon} 流动性锁定: {o['lp_detail']}")
print(f"  {mint_icon} 合约可增发: {'不可增发' if not o['mintable'] else '可增发(危险)'}")
print(f"  {tax_icon} 买卖税: 买{o['buy_tax']}% 卖{o['sell_tax']}%")
print(f"  {whale_icon} 巨鲸持仓: 前10地址占{o['whale_pct']}%")
print(f"  {audit_icon} 合约审计: {'已审计' if o['audited'] else '未审计'}")
print()
print("✅ 已扣费 0.001 USDT")
PYEOF

chmod +x /workspace/scripts/meme_detector.py

echo "Mock meme_detector.py installed at /workspace/scripts/meme_detector.py"
echo "Setup complete."