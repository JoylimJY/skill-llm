import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Distractor directory structure ---
distractor_dirs = [
    "archive/2022/q3",
    "archive/2022/q4",
    "archive/2023/q1",
    "archive/2023/q2",
    "raw_data/sales",
    "raw_data/inventory",
    "raw_data/customer",
    "templates/board",
    "templates/internal",
    "drafts/v1",
    "drafts/v2",
    "notes",
    "references",
]
for d in distractor_dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "archive/2022/q3/sales_summary_Q3_2022.csv": "region,sales\nNorth,120000\nSouth,98000\nEast,134000\nWest,87000\n",
    "archive/2022/q4/sales_summary_Q4_2022.csv": "region,sales\nNorth,145000\nSouth,112000\nEast,156000\nWest,99000\n",
    "archive/2023/q1/notes.txt": "Q1 2023 data finalized. North region showed strong performance.\n",
    "archive/2023/q2/notes.txt": "Q2 2023 review meeting scheduled. Awaiting final figures.\n",
    "raw_data/sales/Q1_2024_transactions.csv": (
        "date,region,amount\n"
        "2024-01-05,North,45000\n"
        "2024-01-12,South,32000\n"
        "2024-01-19,East,51000\n"
        "2024-02-03,West,28000\n"
        "2024-02-14,North,67000\n"
        "2024-02-21,South,41000\n"
        "2024-03-08,East,73000\n"
        "2024-03-15,West,35000\n"
        "2024-03-28,North,52000\n"
    ),
    "raw_data/sales/Q2_2024_transactions.csv": (
        "date,region,amount\n"
        "2024-04-02,North,58000\n"
        "2024-04-18,South,44000\n"
        "2024-05-06,East,79000\n"
        "2024-05-22,West,31000\n"
        "2024-06-10,North,61000\n"
        "2024-06-25,South,47000\n"
    ),
    "raw_data/inventory/stock_levels_June2024.csv": "sku,stock\nA001,340\nA002,120\nB001,560\nB002,89\n",
    "raw_data/customer/customer_segments_2024.csv": "segment,count\nPremium,1200\nStandard,8500\nBasic,14300\n",
    "templates/board/board_report_template.md": "# Board Report Template\n\n## Executive Summary\n\n## Key Metrics\n\n## Recommendations\n",
    "templates/internal/internal_memo_template.md": "# Internal Memo\n\nDate:\nTo:\nFrom:\n\n## Subject\n\n## Body\n",
    "notes/analyst_scratchpad.txt": (
        "Q1 2024 totals:\n"
        "North: 45000+67000+52000 = 164000\n"
        "South: 32000+41000 = 73000\n"
        "East: 51000+73000 = 124000\n"
        "West: 28000+35000 = 63000\n"
        "Total Q1: 424000\n\n"
        "Q2 2024 totals:\n"
        "North: 58000+61000 = 119000\n"
        "South: 44000+47000 = 91000\n"
        "East: 79000\n"
        "West: 31000\n"
        "Total Q2: 320000\n"
    ),
    "references/retail_industry_benchmark_2024.txt": (
        "Industry average YoY growth: 8.3%\n"
        "Top performers: 12-15% growth\n"
        "Market saturation threshold: >25% penetration\n"
        "Source: Retail Analytics Group, Annual Report 2024\n"
    ),
    "drafts/v1/draft_v1.md": "# Q1-Q2 2024 Regional Sales Analysis - DRAFT v1\n\nThis is an early draft. Data not verified.\n",
    "drafts/v2/draft_v2.md": "# Q1-Q2 2024 Regional Sales Analysis - DRAFT v2\n\nPartially updated. Under review.\n",
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# --- THE MAIN FLAWED REPORT ---
# Deliberately seeded with flaws across all 5 SKILL.md checklist categories:
#
# DATA ACCURACY FLAWS:
#   1. Wrong Q1 total: report says 450,000 but actual = 164000+73000+124000+63000 = 424,000
#   2. Wrong growth rate: report says Q2/Q1 growth = +28.4% but actual = (320000-424000)/424000 = -24.5% (Q2 is LESS)
#   3. West region Q1 cited as 71,000 but raw data shows 28000+35000 = 63,000
#
# LOGIC COHERENCE FLAWS:
#   4. Internal contradiction: says "East region leads all regions in Q2" but East Q2 = 79,000, North Q2 = 119,000
#   5. Logical jump: concludes "customer satisfaction improved significantly" from sales data alone — no customer data cited
#
# CONCLUSION QUALITY FLAWS:
#   6. Overgeneralization: "This proves our entire product strategy is working" from 2 quarters of data
#   7. Vague confidence: uses "应该能" (should be able to) without marking it as uncertain
#   8. No limitations stated about the analysis
#
# AUDIENCE FIT FLAWS:
#   9. Uses heavy technical jargon (CAGR, cohort retention, GMV elasticity coefficient) unexplained for a board audience
#   10. Most important finding (North region outperforming) buried in paragraph 4
#
# EXPRESSION QUALITY FLAWS:
#   11. Uses "大概"、"看起来"、"应该" as vague hedges without confidence labeling
#   12. One paragraph contains two conflicting central points

flawed_report = """# 2024年Q1-Q2大区销售分析报告

**报告日期：** 2024年7月15日
**受众：** 董事会成员
**撰写人：** 战略分析团队

---

## 执行摘要

2024年上半年，公司整体销售表现强劲。Q1总销售额达到45万元，Q2实现了显著增长，环比增幅达到28.4%，充分证明我们整体产品战略正在有效运转，公司未来发展前景乐观。北区表现尤为突出，应该能继续保持这一增长势头。

---

## 一、分区域Q1业绩详情

| 区域 | Q1销售额（元） | 占比 |
|------|--------------|------|
| 北区 | 164,000      | 38.7% |
| 南区 | 73,000       | 17.2% |
| 东区 | 124,000      | 29.2% |
| 西区 | 71,000       | 16.7% |
| **合计** | **450,000** | **100%** |

Q1阶段，各区域均实现正增长，西区增速虽然在四个区域中偏低，但整体贡献稳定。

---

## 二、Q2业绩与环比分析

Q2总销售额为320,000元。与Q1相比，公司实现了28.4%的环比正增长，延续了强劲增长趋势。

从区域维度看，东区在Q2表现亮眼，领跑全部四个大区，成为本季度贡献最大的区域。东区的成功主要得益于其精准的客户分层运营和GMV弹性系数优化策略。

北区的CAGR表现和同期队列留存率同样值得关注，其Q2销售额在各区中处于前列，看起来该区域的渠道扩展策略已经奏效。

---

## 三、客户满意度与销售相关性分析

通过对上半年销售数据的系统性分析，可以清晰地看出，客户满意度在Q2得到了显著提升。这与我们在客户服务流程上的持续投入密切相关，大概是因为客户对新产品线的接受度有所提升。

---

## 四、战略结论与建议

1. **全面成功：** 上半年整体销售数据证明我们的整体产品战略是成功的，所有区域均显示出正向发展趋势。

2. **东区经验复制：** 建议将东区的GMV弹性系数优化模型和cohort retention最佳实践在其他区域全面推广。

3. **持续投入：** 建议继续加大北区渠道建设投入，预计下半年该区域销售额将突破历史峰值。

4. **人才培养：** 应进一步加强各区域销售团队的专业能力培训，提升整体战斗力。

---

## 五、风险提示

市场竞争加剧，需持续关注行业动态。

---

*报告完成，请审阅后发送至董事会。*
"""

report_path = os.path.join(workspace, "Q1_Q2_2024_sales_report.md")
with open(report_path, "w", encoding="utf-8") as f:
    f.write(flawed_report)

print(f"[gen_inputs] Workspace created at {workspace}")
print(f"[gen_inputs] Flawed report written to {report_path}")
print(f"[gen_inputs] {len(distractor_files)} distractor files created")