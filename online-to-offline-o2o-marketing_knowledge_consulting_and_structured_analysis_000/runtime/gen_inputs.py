import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ─── distractor directory structure ─────────────────────────────────────────
dirs = [
    "company/finance",
    "company/hr",
    "company/marketing/campaigns",
    "company/marketing/social_media",
    "company/ops/logistics",
    "company/ops/stores",
    "company/it/legacy",
    "company/it/new_systems",
    "research/competitors",
    "research/market",
    "templates/old",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ─── distractor files ─────────────────────────────────────────────────────────

distractor_files = {
    "company/finance/q1_2024_revenue.csv": (
        "store_id,revenue,month\n"
        "001,320000,Jan\n002,280000,Jan\n003,410000,Feb\n004,195000,Mar\n"
    ),
    "company/finance/budget_2025.txt": (
        "Total marketing budget: 2,000,000 RMB\n"
        "Digital channels: 800,000\nTraditional: 600,000\nEvents: 600,000\n"
    ),
    "company/hr/headcount.csv": (
        "department,headcount\nOperations,340\nMarketing,12\nIT,8\nFinance,6\n"
    ),
    "company/marketing/campaigns/summer_promo_2023.txt": (
        "Campaign: BBQ Summer\nChannels: WeChat, Weibo, flyers\n"
        "Result: +12% foot traffic in June 2023\nCost: 150,000 RMB\n"
    ),
    "company/marketing/campaigns/new_year_2024.txt": (
        "Campaign: Spring Festival Special\nChannels: Meituan coupons, in-store\n"
        "Result: +8% table bookings\nCost: 80,000 RMB\n"
    ),
    "company/marketing/social_media/wechat_stats.json": json.dumps({
        "platform": "WeChat Official Account",
        "followers": 42000,
        "avg_open_rate": "3.2%",
        "monthly_posts": 8,
        "last_updated": "2024-03-01"
    }, ensure_ascii=False, indent=2),
    "company/marketing/social_media/douyin_stats.json": json.dumps({
        "platform": "Douyin",
        "followers": 8900,
        "avg_views": 12000,
        "monthly_videos": 4,
        "last_updated": "2024-02-15"
    }, ensure_ascii=False, indent=2),
    "company/ops/stores/store_locations.csv": (
        "store_id,city,district,area_sqm,seats,opened\n"
        "001,Chengdu,Jinjiang,280,120,2018-06\n"
        "002,Chengdu,Wuhou,220,90,2019-03\n"
        "003,Chengdu,Qingyang,350,150,2020-01\n"
        "004,Mianyang,Fucheng,180,80,2021-09\n"
        "005,Deyang,Jingyang,200,85,2022-04\n"
    ),
    "company/ops/logistics/delivery_partners.txt": (
        "Current delivery partners:\n- Meituan Waimai (primary, 68% orders)\n"
        "- Eleme (secondary, 32% orders)\nAvg delivery time: 38 min\n"
        "Complaint rate: 4.1%\n"
    ),
    "company/ops/stores/pos_systems.txt": (
        "POS System: LegacyRest v2.3 (installed 2017)\n"
        "No API integration available\nMember data: paper cards only\n"
        "No digital payment data capture\nNo CRM system\n"
    ),
    "company/it/legacy/tech_inventory.txt": (
        "Legacy systems:\n- POS v2.3 (2017)\n- Static website (2016)\n"
        "- No mobile app\n- No mini-program\n- Excel-based inventory\n"
    ),
    "company/it/new_systems/proposals.txt": (
        "Vendor proposals received:\nA: Full ERP (3.2M RMB, 18 months)\n"
        "B: Mini-program only (380K RMB, 3 months)\n"
        "C: All-in-one SaaS (800K RMB/year)\n"
    ),
    "research/competitors/competitor_analysis.txt": (
        "Key competitors in Sichuan:\n"
        "1. HaiDiLao: Strong app+membership, national brand\n"
        "2. ShuDaxia: Active on Douyin, local delivery\n"
        "3. LaoMaZi: WeChat mini-program ordering\n"
        "Our differentiation: authentic local flavor, family dining\n"
    ),
    "research/market/sichuan_dining_trends_2024.txt": (
        "Key trends:\n- 67% diners check reviews before visiting\n"
        "- 45% use food delivery at least weekly\n"
        "- Mini-programs growing 34% YoY in F&B\n"
        "- Private domain traffic becoming critical\n"
        "- Short video influencing 52% of dining decisions\n"
    ),
    "templates/old/marketing_plan_template_v1.docx.txt": (
        "OLD TEMPLATE - DO NOT USE\n[Outdated 2018 format]\n"
        "Section1: Print advertising\nSection2: TV spots\nSection3: SMS blasts\n"
    ),
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# ─── THE CORE PROBLEM FILE: messy business case ──────────────────────────────
business_case_content = """\
# 蜀香阁餐饮连锁 - 数字化转型需求说明
## 公司背景
蜀香阁是四川省一家本土川菜连锁品牌，成立于2015年，目前在成都、绵阳、德阳共运营5家门店。
主打正宗川菜，人均消费60-90元，家庭客群和商务宴请各占约50%。

## 当前问题（管理层描述，较混乱，未整理）
- 我们在美团和饿了么都有店，但不知道这些平台用户和我们自己的会员是不是同一批人
- 门店会员卡是纸质的，大概有8000张，但没有电话没有微信，根本联系不上
- 微信公众号有4万粉丝，但发的都是菜品图片，很少有人来店消费，感觉就是个摆设
- 最近想在抖音做直播卖团购券，但不知道该怎么跟门店结合
- 有个加盟商想加入，但我们说不清楚我们的"数字化"能力是什么
- 收银系统很老，不知道哪个顾客来了几次，消费了多少
- 竞争对手的小程序做得很好，我们要不要也做一个？完全不知道从哪入手
- 去年搞了个"扫码点餐"活动，结果顾客说麻烦，失败了
- 我们觉得只要把东西搬到网上就算转型了，现在看来好像不对
- 老板认为O2O就是搞促销，打折拉客，但效果越来越差

## 近期意向
公司计划在2025年Q3启动数字化营销转型，预算200万RMB。
目标：提升老客复购率，吸引新客到店，最终提升5家门店的整体营业额。

## 特别说明
请不要只给我们讲概念，我们需要针对蜀香阁具体情况的诊断和建议。
"""

with open(os.path.join(workspace, "shuXiangGe_business_case.txt"), "w", encoding="utf-8") as f:
    f.write(business_case_content)

# ─── Partial/broken template that should NOT be used as-is ──────────────────
broken_template = """\
{
  "company": "蜀香阁",
  "report_type": "???",
  "diagnosis": {
    "current_state": "TODO",
    "problems": []
  },
  "recommendation": "TBD"
}
"""
with open(os.path.join(workspace, "templates/old/broken_report_draft.json"), "w", encoding="utf-8") as f:
    f.write(broken_template)

# ─── A misleading "O2O checklist" that uses wrong/incomplete framework ────────
misleading_checklist = """\
# O2O检查清单（网上找的，不知道准不准）

□ 有没有微信公众号
□ 有没有小程序
□ 有没有外卖平台入驻
□ 有没有二维码
□ 有没有会员体系
□ 有没有做过促销活动

如果以上6项都有，说明O2O做得不错。
（注意：这个清单来源不明，仅供参考）
"""
with open(os.path.join(workspace, "research/market/unofficial_o2o_checklist.txt"), "w", encoding="utf-8") as f:
    f.write(misleading_checklist)

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in os.walk(workspace) for f in _[2])}")