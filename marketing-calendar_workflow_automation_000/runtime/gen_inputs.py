import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── Directory structure with distractor files ─────────────────────────────────
dirs = [
    "brand_assets/logos",
    "brand_assets/guidelines",
    "marketing_plans/2023",
    "marketing_plans/2024/drafts",
    "marketing_plans/2024/approved",
    "competitor_research",
    "campaign_archive/q1",
    "campaign_archive/q2",
    "internal_reports",
    "social_media/templates",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractors = {
    "brand_assets/guidelines/color_palette.txt": "Primary: #E63B2E\nSecondary: #FFD700\nNeutral: #F5F5F5\n",
    "brand_assets/logos/logo_usage_notes.txt": "Do not stretch or distort the logo.\nMinimum size: 32px.\n",
    "marketing_plans/2023/annual_summary.txt": "2023年营销总结：全年GMV同比增长23%，会员数突破500万。\n",
    "marketing_plans/2024/drafts/q3_draft.txt": "Q3草稿：暑期亲子活动，待定。\n",
    "marketing_plans/2024/approved/q1_approved.txt": "Q1已通过方案：春节堂食满减，春节期间88折。\n",
    "competitor_research/haidilao_analysis.txt": "海底捞2024年重点推生日服务、宝宝宴。\n",
    "competitor_research/xiaolongkan_pricing.txt": "小龙坎人均消费：120-150元。\n",
    "campaign_archive/q1/spring_festival_recap.txt": "春节活动复盘：参与门店312家，总销售额2.1亿。\n",
    "campaign_archive/q2/labor_day_recap.txt": "劳动节活动：五一堂食优惠，效果一般。\n",
    "internal_reports/weekly_kpi_wk22.txt": "第22周KPI：翻台率3.2次/天，外卖占比28%。\n",
    "internal_reports/weekly_kpi_wk23.txt": "第23周KPI：翻台率3.5次/天，外卖占比31%。\n",
    "social_media/templates/weibo_template.txt": "【品牌名】X活动：@好友，赢好礼！\n",
    "social_media/templates/wechat_template.txt": "点击查看详情，限时福利等你来拿。\n",
}

for rel_path, content in distractors.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# ── The actual messy brand profile (agent must parse and use) ─────────────────
# Intentionally messy: uses non-standard keys, mixed Chinese/English, flat format
# Agent must normalize this into the input contract and run the full workflow

messy_brand_profile = {
    "brandName": "辣聚火锅",
    "品牌标志物": "沸腾红锅",         # should map to super_symbol
    "核心卖点": "鲜椒牛油锅底，现熬现卖，绝不隔夜",  # core_value
    "targetAudience": "年轻白领, 闺蜜聚会, 家庭聚餐, 夜宵族",  # audience
    "tagline": "热辣沸腾，聚在辣聚",   # slogan
    "brandSpirit": "市井烟火气，人间真性情",  # culture
    "指定月份": "2,5,7,10",           # target_months
    "最低分要求": 80,                  # min_score
    "note": "请务必帮我们策划一套营销日历，我们需要尽快提交给CMO审批。有几个月份优先：情人节、劳动节、暑假、国庆节。"
}

brand_file_path = os.path.join(workspace, "brand_brief.json")
with open(brand_file_path, "w", encoding="utf-8") as f:
    json.dump(messy_brand_profile, f, ensure_ascii=False, indent=2)

# A supplementary text brief with some overlapping/additional context
supplementary_brief = """
辣聚火锅品牌简介（内部资料）
================================
品牌名：辣聚火锅
创始于2018年，主打鲜椒牛油锅底，所有锅底每日现熬，绝不使用隔夜底料。
门店超过200家，主要分布在一二线城市商业综合体。

超级符号：沸腾红锅（门口标志性大红铁锅，冒着白雾）
核心人群：20-35岁年轻人，尤其是喜欢深夜聚餐的夜宵族和闺蜜团。
品牌口号：热辣沸腾，聚在辣聚
品牌精神：市井烟火气，人间真性情

CMO要求：
- 重点策划2月、5月、7月、10月的营销活动
- 每个活动必须有明确的消费者参与方式
- 最终需要一份可以直接提交审批的报告文件
"""

supp_path = os.path.join(workspace, "brand_assets/guidelines/brand_brief_supplement.txt")
with open(supp_path, "w", encoding="utf-8") as f:
    f.write(supplementary_brief)

# An old failed campaign template to act as noise/distractor
old_template = {
    "activity_name": "辣聚周年庆",
    "month": 8,
    "description": "全场8折",
    "status": "REJECTED",
    "reason": "促销指令不明确，无顾客互动"
}
old_template_path = os.path.join(workspace, "campaign_archive/q2/rejected_template.json")
with open(old_template_path, "w", encoding="utf-8") as f:
    json.dump(old_template, f, ensure_ascii=False, indent=2)

print("Workspace initialized successfully.")
print(f"Brand brief: {brand_file_path}")