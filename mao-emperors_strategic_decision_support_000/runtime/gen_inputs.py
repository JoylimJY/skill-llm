import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create a realistic deeply nested directory structure with distractor files
dirs = [
    "company/strategy/2025",
    "company/strategy/2024",
    "company/hr/policies",
    "company/hr/recruitment",
    "company/finance/budget",
    "company/finance/reports",
    "company/product/roadmap",
    "company/product/specs",
    "company/marketing/campaigns",
    "company/legal/contracts",
    "meeting_notes/q1_2025",
    "meeting_notes/q4_2024",
    "research/market_analysis",
    "research/competitor",
    "templates/reports",
    "templates/strategy",
    "misc/archive",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "company/strategy/2025/quarterly_goals.txt": """Q1 2025 Goals:
1. Increase user acquisition by 40%
2. Expand to Southeast Asia markets
3. Hire 50 new engineers
4. Launch v3.0 product
""",
    "company/strategy/2024/annual_review.md": """# 2024 Annual Review
- Revenue grew 85% YoY
- Team expanded from 30 to 120 people
- Launched in 3 new cities
- Key challenge: coordination across departments
""",
    "company/hr/policies/vacation_policy.txt": "All employees get 15 days PTO per year plus national holidays.",
    "company/hr/recruitment/job_postings.md": """# Open Positions
- Senior Backend Engineer (Remote)
- Product Manager (Shanghai)
- Marketing Manager (Beijing)
- Business Development (Overseas)
""",
    "company/finance/budget/2025_budget.csv": """Category,Q1,Q2,Q3,Q4
Marketing,500000,600000,700000,800000
R&D,1200000,1300000,1400000,1500000
Operations,300000,320000,340000,360000
International,0,200000,500000,800000
""",
    "company/product/roadmap/2025_roadmap.md": """# Product Roadmap 2025
## Q1: Core Platform Stability
## Q2: International Localization
## Q3: Market Entry Tools
## Q4: Global Scale
""",
    "company/marketing/campaigns/global_launch.txt": """Global Launch Campaign Notes:
- Target markets: Singapore, Japan, Germany
- Budget: $2M
- Timeline: Q3 2025
- Key message: "World-class AI for everyone"
""",
    "company/legal/contracts/nda_template.txt": "CONFIDENTIAL - Non-Disclosure Agreement Template v2.3",
    "meeting_notes/q1_2025/board_meeting_jan.md": """# Board Meeting January 2025
Attendees: CEO, CTO, CFO, Board Members
Topics:
1. International expansion decision
2. Series B fundraising status
3. Talent acquisition strategy
Outcome: Board approved international expansion plan pending strategy review.
""",
    "meeting_notes/q4_2024/strategy_session.md": """# Strategy Session Q4 2024
Key Questions Raised:
- Should we expand internationally or deepen domestic market first?
- How do we maintain culture during rapid growth?
- What organizational structure supports global operations?
""",
    "research/market_analysis/global_market_2025.txt": """Global AI Market Analysis 2025:
- Total addressable market: $500B
- Key growth regions: SEA, Middle East, Europe
- Main competitors: OpenAI, Google, Anthropic, Baidu
- Entry barriers: regulation, localization, trust
""",
    "research/competitor/competitor_matrix.csv": """Company,Market,Revenue,Team Size,Global Presence
CompanyA,US+EU,5B,10000,Yes
CompanyB,US+Asia,2B,5000,Partial
OurCompany,China,0.5B,200,No
""",
    "templates/reports/strategic_report_old.md": """# Strategic Report Template (OLD FORMAT - DO NOT USE)
## Executive Summary
## Market Analysis
## Recommendations
## Timeline
""",
    "templates/strategy/planning_framework.txt": """Strategic Planning Framework:
1. Situation Analysis (SWOT)
2. Goal Setting (OKRs)
3. Initiative Identification
4. Resource Allocation
5. Execution Timeline
""",
    "misc/archive/2023_strategy.txt": "Archived 2023 strategy document - superseded by 2024 planning.",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# The main problem input: a strategic brief that the agent must analyze
problem_brief = """【战略决策请求 - 需要帝王会议分析】

公司名称：智联科技（ZhiLink Technology）
阶段：A轮融资后，准备启动国际化扩张

=== 核心问题 ===
我们是一家成立3年的国内AI SaaS公司，目前在国内已有稳定客户群（500家企业客户，年营收5000万）。
董事会要求在12个月内完成国际化市场进入，但公司内部存在巨大争议：

争议一：
- 技术团队认为：产品还不够成熟，应该先打磨产品再出海
- 商务团队认为：市场窗口期有限，竞争对手已经开始布局东南亚，必须立即行动

争议二：
- 研发部主张：自建海外研发中心，完全掌控技术
- 运营部主张：寻找当地合作伙伴，轻资产快速扩张

争议三：
- CEO倾向于：进入欧美成熟市场，品牌溢价高
- COO倾向于：先打东南亚新兴市场，成功率更高

当前资源限制：
- 资金：可用于国际化的预算为2000万人民币
- 团队：愿意外派的核心人才只有5-8人
- 时间：12个月内需要看到可量化结果，否则面临下一轮融资困难

请使用帝王会议格式进行战略分析，并输出完整的分析报告。
"""

with open(os.path.join(workspace, "strategic_brief.txt"), "w", encoding="utf-8") as f:
    f.write(problem_brief)

# A SKILL.md file is present in workspace (the agent should read it)
skill_md_content = open("/SKILL.md", "r", encoding="utf-8").read() if os.path.exists("/SKILL.md") else ""
# Note: SKILL.md is already in the container from the task setup

print("Workspace initialized successfully.")
print(f"Files created: {len(distractor_files) + 1}")
print(f"Workspace path: {workspace}")