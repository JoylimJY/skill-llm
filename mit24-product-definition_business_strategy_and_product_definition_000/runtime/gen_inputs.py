import os
import json
import yaml
from pathlib import Path

WORKSPACE = Path("/workspace")
WORKSPACE.mkdir(parents=True, exist_ok=True)

# ── Distractor directory structure ──────────────────────────────────────────
distractor_dirs = [
    "market_research/interviews",
    "market_research/surveys",
    "competitive_analysis/raw",
    "competitive_analysis/processed",
    "financials/projections",
    "financials/cost_breakdown",
    "product/wireframes",
    "product/user_stories_draft",
    "legal/compliance_notes",
    "team/hiring_plan",
]
for d in distractor_dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# Distractor files (irrelevant or misleading)
distractors = {
    "market_research/interviews/interview_notes_jan.txt": (
        "Interview with Procurement Manager at Suzhou Auto Parts.\n"
        "Pain points: supplier delays, lack of visibility.\n"
        "Budget: unclear, 'needs approval'\n"
        "Competitor used: none currently\n"
    ),
    "market_research/surveys/survey_results_q1.csv": (
        "company,size,pain_score,budget_usd\n"
        "MFG_A,500,8,50000\n"
        "MFG_B,200,7,30000\n"
        "MFG_C,1000,9,80000\n"
        "MFG_D,300,6,40000\n"
    ),
    "competitive_analysis/raw/competitor_notes.txt": (
        "Competitor A: SupplyWatch Pro - priced at ~15000/yr, basic alerts only\n"
        "Competitor B: RiskRadar - 25000/yr, good UI, poor API\n"
        "Competitor C: ChainGuard - 10000/yr, limited to tier-1 suppliers\n"
        "Key gaps: none offer AI-based predictive scoring\n"
    ),
    "competitive_analysis/processed/feature_matrix_draft.txt": (
        "Feature comparison INCOMPLETE - do not use\n"
        "Last updated: 2023-11-01\n"
    ),
    "financials/projections/revenue_model_v0.1.txt": (
        "Rough estimates only - NOT VALIDATED\n"
        "Year 1 target: 10 customers\n"
        "Year 2 target: 35 customers\n"
        "Year 3 target: 80 customers\n"
    ),
    "financials/cost_breakdown/ops_cost_2024.txt": (
        "Cloud infra: 8000/month\n"
        "Team salaries: 45000/month\n"
        "Sales & marketing: 12000/month\n"
        "Total burn: ~65000/month\n"
    ),
    "product/wireframes/mvp_sketch_notes.txt": (
        "NOT final - designer's rough ideas\n"
        "Dashboard, alert feed, supplier scorecard\n"
        "Integration with ERP TBD\n"
    ),
    "product/user_stories_draft/stories_incomplete.txt": (
        "Story 1: As a supply chain manager I want... [INCOMPLETE]\n"
        "Story 2: As a CFO I want to see... [INCOMPLETE]\n"
    ),
    "legal/compliance_notes/gdpr_check.txt": (
        "Need legal review for data residency requirements\n"
        "ISO 27001 certification - pending\n"
        "MLPS Level 2 compliance - in progress\n"
    ),
    "team/hiring_plan/q2_roles.txt": (
        "Open roles: 2x backend engineer, 1x ML engineer, 1x sales AE\n"
        "Timeline: hire by Q2 2024\n"
    ),
    "market_research/tam_estimate.txt": (
        "TAM: Chinese manufacturing sector ~8000 mid-size companies\n"
        "SAM: companies with >200 employees and international supply chains: ~2000\n"
        "SOM year 1: target 1% = 20 companies\n"
    ),
    "competitive_analysis/swot_draft.txt": (
        "STRENGTHS: AI-native, real-time alerts\n"
        "WEAKNESSES: no brand recognition, small team\n"
        "OPPORTUNITIES: supply chain disruption post-COVID\n"
        "THREATS: large ERP vendors adding modules\n"
    ),
}

for rel_path, content in distractors.items():
    (WORKSPACE / rel_path).write_text(content, encoding="utf-8")

# ── THE ACTUAL PROBLEM INPUT ─────────────────────────────────────────────────
# This is the messy, raw business data the agent must process into a report.

business_context = {
    "company": "SupplyMind AI",
    "product": "AI供应链风险监测平台",
    "target_customer": "中国中型制造企业（员工200-2000人，有国际供应链）",
    "description": (
        "SaaS平台，通过AI实时监测供应商风险，提供预测性警报和备选方案推荐。"
        "主要解决供应链中断导致的停产损失问题。"
    ),
    "validated_pain_point": (
        "目标客户平均每年因供应链中断损失约380万元，"
        "现有解决方案只能事后响应，无法提前预警。"
    ),
}

# Raw financial assumptions for CLV calculation
financial_data = {
    "annual_contract_value_rmb": 120000,          # 年合同金额 (ACV)
    "average_customer_lifespan_years": 4.5,        # 平均客户年限
    "gross_margin_percent": 72,                    # 毛利率 (%)
    "customer_acquisition_cost_rmb": 85000,        # 获客成本 (CAC)
    "monthly_revenue_per_customer_rmb": 10000,     # 月收入/客户 (for payback calc)
    "note": "以上数据基于行业基准和早期客户访谈估算，供产品定义阶段使用"
}

# Raw competitor scoring data (agent must build the decision matrix from this)
competitor_raw_scores = {
    "dimensions": [
        "功能需求",
        "性能指标",
        "价格敏感度",
        "品牌偏好",
        "服务要求",
        "合规要求"
    ],
    "our_product_SupplyMind": [9, 8, 7, 4, 8, 7],
    "competitor_SupplyWatch_Pro": [5, 4, 8, 6, 5, 6],
    "competitor_RiskRadar": [7, 7, 4, 7, 6, 7],
    "competitor_ChainGuard": [4, 5, 9, 5, 4, 5],
    "note": "评分1-10，基于客户访谈加权反馈"
}

# Write the primary input files
(WORKSPACE / "financials" / "clv_inputs.json").write_text(
    json.dumps(financial_data, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

(WORKSPACE / "competitive_analysis" / "scoring_raw.json").write_text(
    json.dumps(competitor_raw_scores, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

(WORKSPACE / "business_context.json").write_text(
    json.dumps(business_context, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

# Intentionally messy/incomplete notes on pricing discussions
pricing_discussion = """# 内部讨论记录 - 定价方向（未定稿）
日期: 2024-01-15
参与者: CEO, CPO, Sales Lead

## 讨论要点
- Sales认为定价太高会失去客户 → 建议参考竞争对手
- CPO认为我们的AI能力远超竞品，应该体现价值
- CEO倾向于灵活方案，不要一刀切

## 竞品价格参考
- SupplyWatch Pro: ¥15,000/年（基础）
- RiskRadar: ¥25,000/年（中端）  
- ChainGuard: ¥10,000/年（低端）

## 我方成本结构
- 边际成本极低（SaaS特性）
- 主要成本：研发人员、云服务器
- 估算服务单客户年成本：约¥33,600

## 结论
尚未达成一致，需要产品团队给出正式建议

## 其他
客户反馈：愿意为"能提前预警"的功能多付费
某汽车零部件客户表示预算上限¥150,000/年
"""

(WORKSPACE / "financials" / "pricing_discussion_notes.txt").write_text(
    pricing_discussion, encoding="utf-8"
)

print("Workspace generated successfully.")
print(f"Files created: {len(list(WORKSPACE.rglob('*')))} total items")