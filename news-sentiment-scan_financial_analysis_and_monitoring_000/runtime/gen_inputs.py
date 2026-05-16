import os
import json
import random
import shutil
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

WORKSPACE = Path("/workspace")
SKILL_DIR = Path("/skill")

# --- Create skill script (sentiment_scan.py) ---
SKILL_SCRIPTS = SKILL_DIR / "scripts"
SKILL_SCRIPTS.mkdir(parents=True, exist_ok=True)

SENTIMENT_SCAN_SCRIPT = '''#!/usr/bin/env python3
"""
舆情监控与情绪分析脚本
Usage: python3 sentiment_scan.py <stock_code> [days] [market]
"""
import sys
import random
import hashlib
from datetime import datetime, timedelta

def detect_market(stock_code):
    """Auto-detect market from stock code format."""
    if stock_code.endswith(".HK") or (stock_code.isdigit() and len(stock_code) == 5):
        return "hk"
    elif stock_code.isalpha() and stock_code.isupper() and len(stock_code) <= 5:
        return "us"
    elif stock_code.isdigit() and len(stock_code) == 6:
        return "a"
    else:
        return "unknown"

def get_stock_name(stock_code, market):
    names = {
        "0700.HK": "腾讯控股", "00700": "腾讯控股",
        "AAPL": "苹果公司", "TSLA": "特斯拉", "MSFT": "微软",
        "600519": "贵州茅台", "002594": "比亚迪", "601318": "中国平安",
        "09988.HK": "阿里巴巴", "03690.HK": "美团",
    }
    return names.get(stock_code.upper(), f"股票{stock_code}")

def generate_events(stock_code, days, seed):
    """Generate deterministic mock events based on stock code."""
    rng = random.Random(seed)
    
    event_templates = {
        "positive": [
            ("业绩超预期", +5, "公司公告", 0.92),
            ("研报上调评级", +3, "券商研报", 0.88),
            ("大股东增持", +3, "公司公告", 0.95),
            ("政策利好", +4, "主流媒体", 0.85),
            ("产品发布", +2, "主流媒体", 0.78),
            ("营收创历史新高", +5, "公司公告", 0.91),
            ("战略合作协议签署", +2, "主流媒体", 0.82),
        ],
        "negative": [
            ("业绩不及预期", -4, "公司公告", 0.90),
            ("研报下调评级", -3, "券商研报", 0.87),
            ("大股东减持", -3, "公司公告", 0.93),
            ("监管调查", -5, "监管文件", 0.96),
            ("政策利空", -4, "主流媒体", 0.83),
            ("核心高管离职", -3, "主流媒体", 0.79),
        ],
        "neutral": [
            ("召开股东大会", 0, "公司公告", 0.99),
            ("例行财报披露", +1, "公司公告", 0.97),
            ("行业报告发布", -1, "券商研报", 0.75),
            ("市场分析评论", 0, "社交媒体", 0.60),
        ]
    }
    
    # Deterministic event selection based on stock code hash
    code_hash = int(hashlib.md5(stock_code.encode()).hexdigest(), 16)
    rng2 = random.Random(code_hash % 99999)
    
    num_positive = rng2.randint(2, 4)
    num_negative = rng2.randint(1, 3)
    num_neutral = rng2.randint(1, 2)
    
    events = []
    
    pos_pool = event_templates["positive"]
    neg_pool = event_templates["negative"]
    neu_pool = event_templates["neutral"]
    
    rng2.shuffle(pos_pool)
    rng2.shuffle(neg_pool)
    rng2.shuffle(neu_pool)
    
    base_date = datetime(2025, 1, 15)
    
    for i, (title, score, source, conf) in enumerate(pos_pool[:num_positive]):
        date = base_date - timedelta(days=rng2.randint(0, days-1))
        events.append({
            "title": title,
            "score": score,
            "source": source,
            "date": date.strftime("%Y-%m-%d"),
            "confidence": int(conf * 100),
            "type": "positive"
        })
    
    for i, (title, score, source, conf) in enumerate(neg_pool[:num_negative]):
        date = base_date - timedelta(days=rng2.randint(0, days-1))
        events.append({
            "title": title,
            "score": score,
            "source": source,
            "date": date.strftime("%Y-%m-%d"),
            "confidence": int(conf * 100),
            "type": "negative"
        })
    
    for i, (title, score, source, conf) in enumerate(neu_pool[:num_neutral]):
        date = base_date - timedelta(days=rng2.randint(0, days-1))
        events.append({
            "title": title,
            "score": score,
            "source": source,
            "date": date.strftime("%Y-%m-%d"),
            "confidence": int(conf * 100),
            "type": "neutral"
        })
    
    return events

def calc_sentiment(events):
    source_weights = {
        "公司公告": 1.0,
        "券商研报": 0.9,
        "主流媒体": 0.8,
        "监管文件": 0.9,
        "社交媒体": 0.6,
        "论坛帖子": 0.5,
    }
    
    total_weight = 0
    weighted_sum = 0
    for e in events:
        w = source_weights.get(e["source"], 0.7)
        weighted_sum += e["score"] * w
        total_weight += w
    
    if total_weight == 0:
        return 0.0
    
    raw = weighted_sum / total_weight
    # Clamp to [-10, +10]
    return max(-10.0, min(10.0, round(raw * 2.0, 2)))

def score_to_label(score):
    if score >= 8:
        return "🤩 极度乐观"
    elif score >= 5:
        return "😊 偏正面"
    elif score >= 2:
        return "🙂 轻微正面"
    elif score >= -2:
        return "😐 中性"
    elif score >= -5:
        return "😟 轻微负面"
    elif score >= -8:
        return "😰 偏负面"
    else:
        return "😱 极度悲观"

def score_to_icon(score):
    if score > 2:
        return "📈"
    elif score < -2:
        return "📉"
    else:
        return "➡️"

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 sentiment_scan.py <stock_code> [days] [market]")
        sys.exit(1)
    
    stock_code = sys.argv[1]
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    market_override = sys.argv[3] if len(sys.argv) > 3 else None
    
    market = market_override if market_override else detect_market(stock_code)
    
    if market == "unknown":
        print(f"错误：无法识别股票代码格式 '{stock_code}'", file=sys.stderr)
        print(f"请使用正确格式：港股 XXXX.HK 或 5位数字，美股 大写字母，A股 6位数字", file=sys.stderr)
        sys.exit(2)
    
    stock_name = get_stock_name(stock_code, market)
    
    seed = sum(ord(c) for c in stock_code) + days
    events = generate_events(stock_code, days, seed)
    
    overall_score = calc_sentiment(events)
    label = score_to_label(overall_score)
    
    pos_events = [e for e in events if e["type"] == "positive"]
    neg_events = [e for e in events if e["type"] == "negative"]
    neu_events = [e for e in events if e["type"] == "neutral"]
    
    total = len(events)
    pos_pct = round(len(pos_events) / total * 100) if total > 0 else 0
    neu_pct = round(len(neu_events) / total * 100) if total > 0 else 0
    neg_pct = round(len(neg_events) / total * 100) if total > 0 else 0
    
    avg_score = round(sum(e["score"] for e in events) / total, 2) if total > 0 else 0
    
    sources = list(set(e["source"] for e in events))
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    market_labels = {"hk": "港股", "us": "美股", "a": "A股"}
    market_label = market_labels.get(market, market)
    
    print("=" * 50)
    print(f"📰 舆情监控报告：{stock_name}（{stock_code}）")
    print("=" * 50)
    print()
    print(f"📅 监控周期：最近{days}天")
    print(f"🔍 信息来源：{', '.join(sources)}")
    print(f"⏰ 生成时间：{now}")
    print()
    print("━" * 41)
    print()
    print(f"🌡️ 情绪温度计：{overall_score}（{label}）")
    print()
    print(f"   -10  ════════════●════════════  +10")
    print(f"        😱        😐        🤩")
    print()
    print("━" * 41)
    print()
    print("📋 重大事件清单：")
    print()
    
    events_sorted = sorted(events, key=lambda x: abs(x["score"]), reverse=True)
    for i, e in enumerate(events_sorted, 1):
        icon = score_to_icon(e["score"])
        print(f"{i}. [{icon}] {e[\'title\']}")
        print(f"   来源：{e[\'source\']} | 时间：{e[\'date\']}")
        print(f"   情绪贡献：{e[\'score\']} | 置信度：{e[\'confidence\']}%")
        print()
    
    print("━" * 41)
    print()
    print("📊 情绪统计：")
    print(f"├── 正面事件：{len(pos_events)}条（{pos_pct}%）")
    print(f"├── 中性事件：{len(neu_events)}条（{neu_pct}%）")
    print(f"├── 负面事件：{len(neg_events)}条（{neg_pct}%）")
    print(f"└── 平均情绪：{avg_score}")
    print()
    
    if overall_score >= 5:
        advice = "市场情绪偏正面，可适当关注机会，注意控制仓位风险。"
    elif overall_score >= 2:
        advice = "市场情绪轻微正面，保持观察，等待更明确信号。"
    elif overall_score >= -2:
        advice = "市场情绪中性，建议继续持有，密切关注后续消息。"
    elif overall_score >= -5:
        advice = "市场情绪偏负面，建议谨慎操作，注意控制风险。"
    else:
        advice = "市场情绪明显负面，建议降低仓位，规避风险。"
    
    print(f"💡 操作建议：{advice}")
    print()

if __name__ == "__main__":
    main()
'''

with open(SKILL_SCRIPTS / "sentiment_scan.py", "w", encoding="utf-8") as f:
    f.write(SENTIMENT_SCAN_SCRIPT)

os.chmod(SKILL_SCRIPTS / "sentiment_scan.py", 0o755)

# --- Create realistic workspace structure ---

# Portfolio data directory
portfolio_dir = WORKSPACE / "portfolio_management" / "cross_market"
portfolio_dir.mkdir(parents=True, exist_ok=True)

# Ambiguous portfolio config with non-standard identifiers
portfolio_config = {
    "portfolio_name": "Global Growth Fund - Asia Pacific Sleeve",
    "manager": "Zhang Wei",
    "last_updated": "2025-01-10",
    "holdings": [
        {
            "company": "Tencent Holdings",
            "internal_id": "TENCENT-HK",
            "raw_code": "700",           # WRONG format - agent must convert to 0700.HK or 00700
            "exchange": "HKEX",
            "weight_pct": 25.0,
            "monitoring_days": 14
        },
        {
            "company": "Apple Inc.",
            "internal_id": "APPLE-US",
            "raw_code": "AAPL",          # Correct US format
            "exchange": "NASDAQ",
            "weight_pct": 30.0,
            "monitoring_days": 7
        },
        {
            "company": "Kweichow Moutai",
            "internal_id": "MOUTAI-A",
            "raw_code": "600519",        # Correct A-share format
            "exchange": "SSE",
            "weight_pct": 20.0,
            "monitoring_days": 7
        }
    ],
    "report_output": "sentiment_report.json"
}

with open(portfolio_dir / "portfolio_config.json", "w", encoding="utf-8") as f:
    json.dump(portfolio_config, f, ensure_ascii=False, indent=2)

# Old stale sentiment reports (distractor)
old_reports_dir = WORKSPACE / "portfolio_management" / "archived_reports"
old_reports_dir.mkdir(parents=True, exist_ok=True)

for i, stock in enumerate(["BABA", "JD", "PDD"]):
    old_report = {
        "stock": stock,
        "score": random.uniform(-3, 3),
        "generated": "2024-11-01",
        "status": "archived"
    }
    with open(old_reports_dir / f"sentiment_{stock}_2024Q4.json", "w") as f:
        json.dump(old_report, f)

# Distractor: risk management files
risk_dir = WORKSPACE / "risk_management"
risk_dir.mkdir(parents=True, exist_ok=True)

risk_limits = {
    "max_single_stock_weight": 0.35,
    "sentiment_alert_threshold": -5.0,
    "sentiment_positive_threshold": 5.0,
    "rebalance_trigger": "monthly",
    "emotion_labels": {
        "extremely_bullish": [8, 10],
        "bullish": [5, 8],
        "slightly_bullish": [2, 5],
        "neutral": [-2, 2],
        "slightly_bearish": [-5, -2],
        "bearish": [-8, -5],
        "extremely_bearish": [-10, -8]
    }
}
with open(risk_dir / "risk_limits.json", "w") as f:
    json.dump(risk_limits, f, indent=2)

with open(risk_dir / "compliance_notes.txt", "w") as f:
    f.write("Compliance notes for cross-market portfolio:\n")
    f.write("- HK stocks: Subject to SFC regulations\n")
    f.write("- US stocks: SEC filings required quarterly\n")
    f.write("- A-shares: CSRC reporting standards\n")

# Distractor: market data CSV files
data_dir = WORKSPACE / "market_data" / "prices"
data_dir.mkdir(parents=True, exist_ok=True)

for stock, prices in [("0700_HK", [385.2, 387.6, 382.1]), 
                       ("AAPL", [218.3, 220.1, 217.8]),
                       ("600519_SH", [1520.0, 1535.5, 1510.2])]:
    with open(data_dir / f"{stock}_prices.csv", "w") as f:
        f.write("date,open,high,low,close,volume\n")
        base = datetime(2025, 1, 13)
        for i, p in enumerate(prices):
            d = base + timedelta(days=i)
            f.write(f"{d.strftime('%Y-%m-%d')},{p},{p*1.02},{p*0.98},{p*1.005},1000000\n")

# Distractor: analyst notes
analyst_dir = WORKSPACE / "analyst_notes"
analyst_dir.mkdir(parents=True, exist_ok=True)

with open(analyst_dir / "weekly_memo_2025_W02.txt", "w") as f:
    f.write("Weekly Analyst Memo - Week 2, 2025\n\n")
    f.write("Key themes this week:\n")
    f.write("1. AI sector momentum continues\n")
    f.write("2. China consumer recovery signals\n")
    f.write("3. Fed rate expectations recalibration\n\n")
    f.write("Stocks under watch: AAPL, 0700.HK, 600519\n")

with open(analyst_dir / "coverage_universe.txt", "w") as f:
    f.write("Coverage Universe (as of Jan 2025):\n")
    f.write("HK: 0700.HK, 09988.HK, 03690.HK, 02318.HK\n")
    f.write("US: AAPL, MSFT, GOOGL, AMZN, TSLA\n")
    f.write("A:  600519, 002594, 601318, 000858\n")

# Distractor: system config
config_dir = WORKSPACE / "config"
config_dir.mkdir(parents=True, exist_ok=True)

with open(config_dir / "system_config.yaml", "w") as f:
    f.write("system:\n")
    f.write("  environment: production\n")
    f.write("  log_level: INFO\n")
    f.write("  output_dir: /workspace/reports\n\n")
    f.write("data_sources:\n")
    f.write("  yahoo_finance: enabled\n")
    f.write("  google_news: enabled\n")
    f.write("  weibo: disabled\n")
    f.write("  xueqiu: disabled\n")

with open(config_dir / "market_calendars.json", "w") as f:
    json.dump({
        "hk": {"timezone": "Asia/Hong_Kong", "trading_days": "Mon-Fri"},
        "us": {"timezone": "America/New_York", "trading_days": "Mon-Fri"},
        "a": {"timezone": "Asia/Shanghai", "trading_days": "Mon-Fri"}
    }, f, indent=2)

# Distractor: previous run logs
logs_dir = WORKSPACE / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)

with open(logs_dir / "scan_history.log", "w") as f:
    f.write("2025-01-08 09:00:00 - Scan started for BABA\n")
    f.write("2025-01-08 09:00:05 - Scan completed. Score: 2.3\n")
    f.write("2025-01-09 09:00:00 - Scan started for JD\n")
    f.write("2025-01-09 09:00:04 - Scan completed. Score: -1.8\n")

with open(logs_dir / "error_log.txt", "w") as f:
    f.write("2025-01-07 - WARNING: Stock code '700' not recognized (missing .HK suffix)\n")
    f.write("2025-01-07 - ERROR: Scan failed for code '700' - unknown market\n")
    f.write("2025-01-07 - INFO: Use '0700.HK' or '00700' for Tencent\n")

# Note: Do NOT create sentiment_report.json - agent must create it

print("Workspace setup complete.")
print(f"Files created in {WORKSPACE}:")
for f in sorted(WORKSPACE.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(WORKSPACE)}")