import os
import json
import random

random.seed(42)

workspace = "/workspace"

# Create deeply nested distractor directory structure
dirs = [
    "projects/data_analysis_course/drafts",
    "projects/data_analysis_course/assets/images",
    "projects/data_analysis_course/assets/videos",
    "projects/old_blog/2023/posts",
    "projects/old_blog/2024/posts",
    "admin/invoices/2024",
    "admin/invoices/2025",
    "admin/contracts",
    "research/competitor_analysis",
    "research/audience_surveys",
    "tools/scripts",
    "tools/templates",
    "marketing/social_media",
    "marketing/email_campaigns",
    "revenue/q1_2025",
    "revenue/q2_2025",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractors = [
    ("projects/data_analysis_course/drafts/outline_v1.txt",
     "Module 1: Pandas basics\nModule 2: Data visualization\nModule 3: Machine learning intro\n"),
    ("projects/data_analysis_course/drafts/outline_v2.txt",
     "Module 1: NumPy fundamentals\nModule 2: Pandas advanced\nModule 3: Scikit-learn pipelines\n"),
    ("projects/data_analysis_course/assets/images/placeholder.txt",
     "# Image assets will go here\n"),
    ("projects/old_blog/2023/posts/post1.md",
     "# How I learned Python in 30 days\nThis is my journey...\n"),
    ("projects/old_blog/2024/posts/post2.md",
     "# Top 10 Pandas tricks\nHere are my favorite tricks...\n"),
    ("projects/old_blog/2024/posts/post3.md",
     "# Why data visualization matters\nVisualization is key...\n"),
    ("admin/invoices/2024/invoice_001.txt",
     "Client: TechCorp\nAmount: 5000 CNY\nService: Data consulting\n"),
    ("admin/invoices/2025/invoice_010.txt",
     "Client: StartupXYZ\nAmount: 8000 CNY\nService: Training workshop\n"),
    ("admin/contracts/contract_template.txt",
     "This agreement is between [PARTY A] and [PARTY B]...\n"),
    ("research/competitor_analysis/notes.txt",
     "Competitor A: Python课程 - 299元\nCompetitor B: 数据分析训练营 - 1999元\nCompetitor C: 1对1咨询 - 599元/小时\n"),
    ("research/audience_surveys/survey_results.txt",
     "Q1: Would you pay for a Python data course? Yes: 73%, No: 27%\nQ2: Max budget: avg 450 CNY\n"),
    ("tools/scripts/export_data.py",
     "# Script to export course data\nimport csv\n\ndef export(data, path):\n    pass\n"),
    ("tools/templates/email_template.txt",
     "Subject: New course launch!\nHi {{name}},\nWe're excited to announce...\n"),
    ("marketing/social_media/content_calendar.txt",
     "Week 1: Introduction post\nWeek 2: Tutorial snippet\nWeek 3: Student testimonial\n"),
    ("marketing/email_campaigns/campaign_q1.txt",
     "Campaign: Spring Launch\nTarget: 5000 subscribers\nOpen rate target: 25%\n"),
    ("revenue/q1_2025/summary.txt",
     "Q1 Revenue: 45,000 CNY\nMain sources: workshops x3, consulting x8\n"),
    ("revenue/q2_2025/summary.txt",
     "Q2 Revenue: 62,000 CNY\nMain sources: online course sales, brand deals\n"),
]

for filepath, content in distractors:
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# THE MAIN INPUT: A messy, realistic creator profile JSON
# The agent must READ this and perform the analysis
creator_profile = {
    "creator_name": "林晓明",
    "content_type": "Python数据分析教学",
    "description": "专注于Python数据分析教学，拥有5年数据科学工作经验，曾任职于BAT级别公司数据团队。已在公众号积累8500名订阅者，知乎专栏有1200关注者。内容以实战项目为主，有3个完整数据分析项目案例。正在考虑出一门录播课程。",
    
    # Raw scoring inputs - messy and not pre-scored
    "evaluation_inputs": {
        "professionalism_notes": "5年BAT数据科学经验，能讲清楚实际工作中的数据处理流程，内容有深度",
        "practicality_notes": "所有内容基于真实项目，学完可直接用于工作，有具体代码和案例",
        "uniqueness_notes": "结合实际BAT工作经验，有一定独特视角，但Python教学市场竞争较激烈",
        "demand_intensity_notes": "数据分析技能需求持续旺盛，求职者和转行者众多，刚需明显",
        "payment_willingness_notes": "目标受众（求职者、转行者）付费意愿较高，问卷显示73%愿意付费",
        "market_size_notes": "国内数据分析学习市场庞大，潜在用户百万级",
        "scarcity_notes": "BAT实战经验稀缺，市面上大多是理论课程，实战派相对较少",
        "brand_power_notes": "有8500公众号粉丝和1200知乎关注者，品牌有一定积累但仍偏小",
        "trust_notes": "公众号读者反馈良好，有一定口碑，但缺乏大量成功学员案例",
        "multi_channel_notes": "可以做录播课、1对1咨询、训练营、电子书等多种形式",
        "repurchase_notes": "学员可能先买入门课再买进阶课，复购路径清晰",
        "virality_notes": "技术类内容传播性一般，口碑传播为主"
    },
    
    # Raw scoring values the agent must map to the rubric
    # These are given as raw 0-10 scales but agent must apply correct max scores
    "raw_scores": {
        "professionalism": 8,        # out of 10 (max in rubric: 10)
        "practicality": 9,           # out of 10 (max in rubric: 10)
        "uniqueness": 6,             # out of 5 (TRICK: raw is /10 but rubric max is 5 — agent must scale)
        "demand_intensity": 9,       # out of 10 (max in rubric: 10)
        "payment_willingness": 8,    # out of 10 (max in rubric: 10)
        "market_size": 4,            # out of 5 (TRICK: raw is /10 but rubric max is 5 — agent must scale)
        "scarcity": 8,               # out of 10 (max in rubric: 10)
        "brand_power": 6,            # out of 10 (max in rubric: 10)
        "trust": 3,                  # out of 5 (TRICK: raw is /10 but rubric max is 5 — agent must scale)
        "multi_channel": 9,          # out of 10 (max in rubric: 10)
        "repurchase": 8,             # out of 10 (max in rubric: 10)
        "virality": 4                # out of 5 (TRICK: raw is /10 but rubric max is 5 — agent must scale)
    },
    
    # Revenue prediction inputs
    "monetization_plan": {
        "primary_product": "Python数据分析录播课",
        "monthly_traffic": 15000,
        "conversion_rate": 0.025,    # 2.5%
        "unit_price_planned": 399,
        "target_learner_monthly_income_increase": 4000,  # CNY per month after taking course
    },
    
    # Pricing inputs
    "pricing_context": {
        "production_cost_hours": 80,
        "hourly_production_cost": 120,
        "expected_sales_volume": 150,
        "competitor_prices": [299, 399, 499]
    }
}

# Save the messy profile
with open(os.path.join(workspace, "creator_profile.json"), "w", encoding="utf-8") as f:
    json.dump(creator_profile, f, ensure_ascii=False, indent=2)

# Also create a brief request note
request_note = """变现分析请求
==============
创作者：林晓明
请求时间：2025-07-10
需求：请对我的内容进行完整的变现分析，帮我评估内容价值、推荐变现渠道、制定定价策略，并预测未来12个月的收入情况。
输出文件：monetization_report.json
"""
with open(os.path.join(workspace, "analysis_request.txt"), "w", encoding="utf-8") as f:
    f.write(request_note)

print("Workspace setup complete.")
print(f"Created creator profile: {os.path.join(workspace, 'creator_profile.json')}")
print(f"Created request note: {os.path.join(workspace, 'analysis_request.txt')}")