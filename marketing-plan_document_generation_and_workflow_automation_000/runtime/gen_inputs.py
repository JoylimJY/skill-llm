import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# === Deep directory structure with distractor files ===
dirs = [
    "project/briefs",
    "project/assets/logos",
    "project/assets/fonts",
    "project/research/competitors",
    "project/research/market",
    "project/drafts/v1",
    "project/drafts/v2",
    "project/budgets",
    "project/reports/q1",
    "project/reports/q2",
    "archive/2023",
    "archive/2024",
    "tools/templates",
    "tools/scripts",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# === Distractor files ===
distractor_files = {
    "project/briefs/product_overview.txt": (
        "Product: VoltNest Home EV Charger\n"
        "Company: VoltNest Technologies (沃特巢科技)\n"
        "Launch Market: China (Tier-1 and Tier-2 cities)\n"
        "Price Point: ¥3,999 per unit\n"
        "Key Feature: AI-optimized overnight charging schedule\n"
    ),
    "project/briefs/stakeholder_notes.txt": (
        "CEO wants a Chinese-language marketing plan.\n"
        "Marketing Director: budget is 200,000 RMB for Q3 launch.\n"
        "Timeline: 8 weeks starting Week 1.\n"
        "Must include social media, KOL partnerships, and trade shows.\n"
    ),
    "project/research/competitors/competitor_summary.csv": (
        "Name,Strengths,Weaknesses\n"
        "Tesla Wall Connector,Brand recognition,High price\n"
        "Xiaopeng Home Charger,EV ecosystem tie-in,Limited compatibility\n"
        "NIO Power Home,Fast installation network,Only for NIO owners\n"
    ),
    "project/research/market/ev_market_2024.txt": (
        "China EV market grew 38% YoY in 2024.\n"
        "Home charging adoption rate: 62% of new EV owners.\n"
        "Key channels: Douyin (35%), WeChat (28%), Xiaohongshu (20%), Offline (17%).\n"
        "Average marketing spend in smart home hardware: 15-25% of revenue.\n"
    ),
    "project/budgets/budget_breakdown_draft.txt": (
        "DRAFT - NOT FINAL\n"
        "Social Media (Douyin + Xiaohongshu): 40%\n"
        "KOL / Influencer Partnerships: 30%\n"
        "Trade Shows & Events: 20%\n"
        "SEM / Paid Search: 10%\n"
        "Total: ¥200,000\n"
    ),
    "project/drafts/v1/old_plan_outline.txt": (
        "Version 1 - Rejected by management\n"
        "Too generic. No competitor analysis.\n"
        "Missing KPIs.\n"
    ),
    "project/drafts/v2/plan_notes_v2.txt": (
        "V2 notes:\n"
        "- Add KOL outreach milestone in Week 2\n"
        "- Trade show is in Week 6 (China EV Expo, Shenzhen)\n"
        "- Goal: 5M Douyin impressions, 50,000 WeChat followers, 2,000 unit pre-orders\n"
    ),
    "project/reports/q1/q1_sales.txt": (
        "Q1 Sales Report: 0 units (pre-launch)\n"
        "Brand awareness: <1%\n"
    ),
    "project/reports/q2/q2_projections.txt": (
        "Q2 Projection after launch: 2,000 units\n"
        "Revenue target: ¥7,998,000\n"
    ),
    "project/assets/logos/logo_specs.txt": (
        "Logo: VoltNest_logo_v3.ai\n"
        "Colors: #1A73E8 (primary), #34A853 (accent)\n"
    ),
    "project/assets/fonts/font_list.txt": (
        "Approved fonts: Source Han Sans CN, Helvetica Neue\n"
    ),
    "archive/2023/old_strategy.txt": (
        "2023 Strategy: Focus on B2B fleet charging.\n"
        "Result: Abandoned due to low margin.\n"
    ),
    "archive/2024/pivot_notes.txt": (
        "2024 Pivot: Move to B2C home charging segment.\n"
    ),
    "tools/templates/docx_style_notes.txt": (
        "Internal note: All Word docs must use standard margins.\n"
        "Use Table Grid style for tables.\n"
    ),
    "tools/scripts/old_plan_generator.py": (
        "# DEPRECATED - Do not use\n"
        "# This script is outdated and produces incorrect budget tables.\n"
        "def generate_plan():\n"
        "    pass\n"
    ),
}

for path, content in distractor_files.items():
    full_path = workspace / path
    full_path.write_text(content, encoding="utf-8")

# === Task specification file (business brief, not a hint file) ===
task_brief = {
    "client": "VoltNest Technologies (沃特巢科技)",
    "product": "VoltNest 家用智能充电桩",
    "total_budget_rmb": 200000,
    "language": "Chinese",
    "channels": [
        {"name": "抖音+小红书", "budget_pct": 40, "description": "短视频种草与评测内容"},
        {"name": "KOL合作", "budget_pct": 30, "description": "汽车科技类头部达人深度测评"},
        {"name": "展会与线下活动", "budget_pct": 20, "description": "中国新能源汽车博览会(深圳)"},
        {"name": "SEM搜索推广", "budget_pct": 10, "description": "百度+360关键词竞价广告"},
    ],
    "milestones": [
        {"week": "Week 1", "task": "启动社媒账号矩阵与内容日历", "owner": "社交媒体团队"},
        {"week": "Week 2", "task": "KOL合同签署与素材交付", "owner": "BD团队"},
        {"week": "Week 4", "task": "抖音首波投放上线", "owner": "投放团队"},
        {"week": "Week 6", "task": "深圳新能源博览会参展", "owner": "市场团队"},
        {"week": "Week 8", "task": "数据复盘与ROI分析报告", "owner": "数据分析团队"},
    ],
    "goals": [
        {"metric": "抖音曝光量", "target": "5,000,000次"},
        {"metric": "微信公众号新增粉丝", "target": "50,000"},
        {"metric": "预售订单", "target": "2,000台"},
        {"metric": "品牌搜索量提升", "target": "300%"},
    ],
    "competitors": [
        {
            "name": "特斯拉家用充电桩",
            "strengths": "品牌认知度高，生态闭环",
            "weaknesses": "价格昂贵，仅适配特斯拉",
        },
        {
            "name": "小鹏家充桩",
            "strengths": "深度绑定小鹏EV生态",
            "weaknesses": "兼容性差，非小鹏车主无法使用",
        },
        {
            "name": "蔚来家充桩",
            "strengths": "安装服务网络完善",
            "weaknesses": "专属蔚来用户，市场覆盖窄",
        },
    ],
    "output_filename": "沃特巢_营销方案.docx",
}

with open(workspace / "project/briefs/campaign_brief.json", "w", encoding="utf-8") as f:
    json.dump(task_brief, f, ensure_ascii=False, indent=2)

print("Workspace initialized successfully.")
print("Files created:")
for p in sorted(workspace.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(workspace)}")