#!/bin/bash
set -e

# Create the /onchain-audit mock tool
cat > /usr/local/bin/onchain-audit << 'TOOL_EOF'
#!/usr/bin/env python3
import sys
import json
import os
import re

WORKSPACE = "/workspace"
DATA_DIR = os.path.join(WORKSPACE, "projects/raw_data")

PROJECT_FILE_MAP = {
    "alphaswap": "alphaswap.json",
    "betafarm": "betafarm.json",
    "gammapool": "gammapool.json",
    "deltatoken": "deltatoken.json",
    "epsilonmoon": "epsilon.json",
    "epsilon": "epsilon.json",
}

def load_project(name):
    key = name.lower().replace(" ", "")
    fname = PROJECT_FILE_MAP.get(key)
    if not fname:
        # Try partial match
        for k, v in PROJECT_FILE_MAP.items():
            if key in k or k in key:
                fname = v
                break
    if not fname:
        print(f"ERROR: Project '{name}' not found in local data.", file=sys.stderr)
        sys.exit(1)
    path = os.path.join(DATA_DIR, fname)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def normalize(data):
    """Normalize messy project data into standard fields."""
    d = {}
    # Name
    d["name"] = (data.get("proj_name") or data.get("name") or data.get("token") or
                 data.get("project") or data.get("nm") or "Unknown")
    # Contract
    d["contract"] = (data.get("contract_addr") or data.get("address") or data.get("contract") or
                     data.get("ca") or data.get("addr") or "N/A")
    # Chain
    d["chain"] = (data.get("chain") or data.get("blockchain") or data.get("network") or data.get("net") or "ETH")
    # Verified
    d["verified"] = (data.get("source_code_verified") or data.get("verified_source") or
                     data.get("open_source") or data.get("is_verified") or data.get("src_open") or False)
    # LP Lock
    lp_info = data.get("liquidity_lock", {})
    d["lp_locked"] = (data.get("lp_lock_status") == "LOCKED" or
                      data.get("lp_lock") == True or
                      (lp_info.get("locked") == True) or
                      data.get("liq_locked") == True)
    d["lp_days"] = (data.get("lp_lock_days") or
                    (lp_info.get("lock_duration_days")) or
                    data.get("liq_lock_d") or 0)
    # Team
    team_info = data.get("team_info", {})
    d["team_doxxed"] = (data.get("team_doxxed") or
                        team_info.get("publicly_identified") or
                        (not data.get("anonymous_team", True)) or
                        (not data.get("team_anon", True)) or False)
    # Concentration
    conc = data.get("concentration", {})
    tok = data.get("tokenomics", {})
    d["top10_pct"] = (data.get("top10_holders_pct") or
                      conc.get("top10_percent") or
                      tok.get("top_10_wallet_concentration") or
                      data.get("top_10_concentration") or
                      data.get("top10_pct") or 50.0)
    # Market data
    d["mcap"] = (data.get("marketcap_usd") or tok.get("market_cap") or
                 data.get("mcap") or data.get("market_cap") or 0)
    d["volume"] = (data.get("volume_24h_usd") or tok.get("daily_volume") or
                   data.get("volume_24h") or data.get("vol_24h") or data.get("vol") or 0)
    d["holders"] = (data.get("holder_addresses") or tok.get("unique_holders") or
                    data.get("total_holders") or data.get("holders") or 0)
    d["days_live"] = (data.get("launch_days_ago") or data.get("age_days") or
                      data.get("days_since_launch") or data.get("days_live") or data.get("launched_d") or 0)
    # Social
    soc = data.get("social_media", data.get("social", data.get("socials", {})))
    d["twitter"] = (soc.get("twitter_followers") or soc.get("twitter") or
                    data.get("twitter_followers") or data.get("tw_follow") or 0)
    d["telegram"] = (soc.get("telegram_members") or soc.get("telegram") or
                     soc.get("tg_count") or data.get("telegram") or data.get("tg_mem") or 0)
    # Flags
    d["flags"] = (data.get("contract_flags") or data.get("flags") or
                  data.get("red_flags") or data.get("flags_raw") or [])
    return d

def calc_risk_score(d, deep=False):
    score = 100
    risk_items = []
    safe_items = []

    # Contract verified
    if d["verified"]:
        safe_items.append("合约已开源")
    else:
        score -= 25
        risk_items.append("合约未开源/未验证")

    # LP Lock
    if d["lp_locked"] and d["lp_days"] >= 180:
        safe_items.append(f"LP 已锁定（{d['lp_days']} 天）")
    elif d["lp_locked"] and d["lp_days"] > 0:
        score -= 15
        risk_items.append(f"LP 锁定时间较短（{d['lp_days']} 天）")
    else:
        score -= 30
        risk_items.append("LP 未锁定")

    # Team
    if d["team_doxxed"]:
        safe_items.append("团队实名")
    else:
        score -= 15
        risk_items.append("团队匿名")

    # Concentration
    if d["top10_pct"] > 70:
        score -= 20
        risk_items.append(f"持币集中度高（前 10 地址 {d['top10_pct']}%）")
    elif d["top10_pct"] > 50:
        score -= 10
        risk_items.append(f"持币集中度偏高（前 10 地址 {d['top10_pct']}%）")
    else:
        safe_items.append(f"持币分散（前 10 地址 {d['top10_pct']}%）")

    # Volume
    if d["volume"] < 10000:
        score -= 10
        risk_items.append("交易量偏低")
    else:
        safe_items.append("交易量正常")

    # Social
    total_social = d["twitter"] + d["telegram"]
    if total_social < 1000:
        score -= 5
        risk_items.append("社交媒体活跃度低")
    else:
        safe_items.append("社交媒体活跃")

    # Contract flags
    for flag in d["flags"]:
        if "mint" in flag.lower():
            score -= 10
            risk_items.append("合约存在 Mint 函数")
        if "timelock" in flag.lower() and "no_" in flag.lower():
            score -= 5
            risk_items.append("缺少时间锁")

    score = max(0, min(100, score))
    return score, safe_items, risk_items

def risk_label(score):
    if score <= 30:
        return "高风险"
    elif score <= 60:
        return "中风险"
    else:
        return "低风险"

def investment_advice(score, d):
    if score <= 30:
        pos = "不建议投资"
        sl = "-10%"
        focus = "合约安全、团队信息"
    elif score <= 60:
        pos = "不超过总资金 5%"
        sl = "-20%"
        focus = "交易量、持币地址数"
    else:
        pos = "不超过总资金 15%"
        sl = "-30%"
        focus = "市值增长、社区活跃度"
    return pos, sl, focus

def format_mcap(v):
    if v >= 1_000_000:
        return f"${v/1_000_000:.1f}M"
    elif v >= 1000:
        return f"${v/1000:.0f}K"
    return f"${v}"

def format_vol(v):
    if v >= 1_000_000:
        return f"${v/1_000_000:.1f}M"
    elif v >= 1000:
        return f"${v/1000:.0f}K"
    return f"${v}"

def generate_report(name, deep=False):
    data = load_project(name)
    d = normalize(data)
    score, safe_items, risk_items = calc_risk_score(d, deep)
    label = risk_label(score)
    pos, sl, focus = investment_advice(score, d)

    lines = []
    lines.append("## 🔒 链上项目安全审计报告")
    lines.append("")
    lines.append(f"### 📊 综合风险评分：{score}/100（{label}）")
    lines.append("")
    lines.append("### ✅ 安全项")
    for item in safe_items:
        lines.append(f"- [✓] {item}")
    if not safe_items:
        lines.append("- [✓] 暂无安全项")
    lines.append("")
    lines.append("### ⚠️ 风险项")
    for item in risk_items:
        lines.append(f"- [!] {item}")
    if not risk_items:
        lines.append("- 暂无风险项")
    lines.append("")
    lines.append("### 💡 投资建议")
    lines.append(f"- 建议仓位：{pos}")
    lines.append(f"- 止损位：{sl}")
    lines.append(f"- 关注指标：{focus}")
    lines.append("")
    lines.append("### 📈 项目数据")
    lines.append(f"- 市值：{format_mcap(d['mcap'])}")
    lines.append(f"- 24h 交易量：{format_vol(d['volume'])}")
    lines.append(f"- 持币地址：{d['holders']:,}")
    lines.append(f"- 上线时间：{d['days_live']} 天")

    if deep:
        lines.append("")
        lines.append("### 🔬 深度分析")
        lines.append(f"- 合约地址：{d['contract']}")
        lines.append(f"- 链：{d['chain']}")
        flagstr = "、".join(d['flags']) if d['flags'] else "无"
        lines.append(f"- 合约风险标记：{flagstr}")
        lines.append(f"- 社交媒体追随者：Twitter {d['twitter']:,} / Telegram {d['telegram']:,}")

    return "\n".join(lines)

def generate_comparison(name_a, name_b):
    data_a = load_project(name_a)
    data_b = load_project(name_b)
    da = normalize(data_a)
    db = normalize(data_b)
    score_a, safe_a, risk_a = calc_risk_score(da)
    score_b, safe_b, risk_b = calc_risk_score(db)
    label_a = risk_label(score_a)
    label_b = risk_label(score_b)

    lines = []
    lines.append("## 🔒 链上项目对比审计报告")
    lines.append("")
    lines.append(f"### 📊 综合风险评分对比")
    lines.append(f"- {da['name']}：{score_a}/100（{label_a}）")
    lines.append(f"- {db['name']}：{score_b}/100（{label_b}）")
    lines.append("")
    lines.append(f"### ✅ {da['name']} 安全项")
    for item in safe_a:
        lines.append(f"- [✓] {item}")
    lines.append("")
    lines.append(f"### ⚠️ {da['name']} 风险项")
    for item in risk_a:
        lines.append(f"- [!] {item}")
    lines.append("")
    lines.append(f"### ✅ {db['name']} 安全项")
    for item in safe_b:
        lines.append(f"- [✓] {item}")
    lines.append("")
    lines.append(f"### ⚠️ {db['name']} 风险项")
    for item in risk_b:
        lines.append(f"- [!] {item}")
    lines.append("")
    lines.append("### 💡 综合投资建议")
    if score_a > score_b:
        winner = da['name']
        loser = db['name']
    else:
        winner = db['name']
        loser = da['name']
    lines.append(f"- 相对更优选择：{winner}")
    lines.append(f"- 风险更高项目：{loser}")
    lines.append("")
    lines.append("### 📈 项目数据对比")
    lines.append(f"| 指标 | {da['name']} | {db['name']} |")
    lines.append("|------|------|------|")
    lines.append(f"| 市值 | {format_mcap(da['mcap'])} | {format_mcap(db['mcap'])} |")
    lines.append(f"| 24h 交易量 | {format_vol(da['volume'])} | {format_vol(db['volume'])} |")
    lines.append(f"| 持币地址 | {da['holders']:,} | {db['holders']:,} |")
    lines.append(f"| 上线时间 | {da['days_live']} 天 | {db['days_live']} 天 |")
    return "\n".join(lines)

def generate_batch(project_list):
    lines = []
    lines.append("## 🔒 批量链上项目安全审计报告")
    lines.append("")
    for name in project_list:
        name = name.strip()
        if not name:
            continue
        try:
            data = load_project(name)
            d = normalize(data)
            score, safe_items, risk_items = calc_risk_score(d)
            label = risk_label(score)
            lines.append(f"---")
            lines.append(f"### 📊 {d['name']} — 风险评分：{score}/100（{label}）")
            lines.append("")
            lines.append("#### ✅ 安全项")
            for item in safe_items:
                lines.append(f"- [✓] {item}")
            if not safe_items:
                lines.append("- [✓] 暂无安全项")
            lines.append("")
            lines.append("#### ⚠️ 风险项")
            for item in risk_items:
                lines.append(f"- [!] {item}")
            if not risk_items:
                lines.append("- 暂无风险项")
            lines.append("")
            lines.append("#### 📈 快速数据")
            lines.append(f"- 市值：{format_mcap(d['mcap'])} | 24h 交易量：{format_vol(d['volume'])} | 持币地址：{d['holders']:,}")
            lines.append("")
        except Exception as e:
            lines.append(f"---")
            lines.append(f"### ❌ {name} — 审计失败：{str(e)}")
            lines.append("")
    return "\n".join(lines)

def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: onchain-audit <project> [--deep] [--compare <project2>] [--batch]")
        sys.exit(1)

    project = args[0].strip('"\'')
    deep = "--deep" in args
    batch = "--batch" in args
    compare_idx = None
    compare_project = None
    for i, a in enumerate(args):
        if a == "--compare" and i + 1 < len(args):
            compare_idx = i
            compare_project = args[i + 1].strip('"\'')
            break

    if batch:
        # project arg is a file path or comma-separated list
        proj_path = os.path.join(WORKSPACE, project) if not os.path.isabs(project) else project
        if os.path.exists(proj_path):
            with open(proj_path, "r", encoding="utf-8") as f:
                project_list = [l.strip() for l in f.readlines() if l.strip()]
        else:
            project_list = [p.strip() for p in project.split(",") if p.strip()]
        print(generate_batch(project_list))
    elif compare_project:
        print(generate_comparison(project, compare_project))
    else:
        print(generate_report(project, deep=deep))

if __name__ == "__main__":
    main()
TOOL_EOF

chmod +x /usr/local/bin/onchain-audit

# Also make it accessible as /onchain-audit (as specified in SKILL.md)
ln -sf /usr/local/bin/onchain-audit /onchain-audit

echo "Setup complete. onchain-audit tool is ready."
echo "Test: onchain-audit --help || true"