import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create a realistic, deeply nested directory structure with distractor files
dirs = [
    "/workspace/company/product/roadmap",
    "/workspace/company/product/specs",
    "/workspace/company/sales/q1_reports",
    "/workspace/company/sales/leads",
    "/workspace/company/hr/onboarding",
    "/workspace/company/hr/policies",
    "/workspace/company/engineering/sprints",
    "/workspace/company/engineering/incidents",
    "/workspace/company/marketing/campaigns",
    "/workspace/archive/2025/emails",
    "/workspace/archive/2025/meetings",
    "/workspace/tmp/drafts",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# Distractor files
distractor_files = {
    "workspace/company/product/roadmap/Q2_roadmap.md": "# Q2 Roadmap\n- Feature A: Launch by June\n- Feature B: Beta in May\n- Feature C: Research phase",
    "workspace/company/product/specs/auth_spec.md": "# Auth Spec v2\nOAuth2 flow with PKCE...",
    "workspace/company/sales/q1_reports/pipeline.csv": "Deal,Stage,Value\nAcme Corp,Negotiation,50000\nGlobEx,Demo,20000",
    "workspace/company/sales/leads/contacts.json": json.dumps([{"name": "Li Wei", "company": "TechCo", "status": "cold"}]),
    "workspace/company/hr/onboarding/checklist.txt": "Day 1: Setup laptop\nDay 2: Meet team\nDay 3: Read policies",
    "workspace/company/hr/policies/leave_policy.md": "# Leave Policy\nAnnual: 15 days\nSick: 10 days",
    "workspace/company/engineering/sprints/sprint_42.json": json.dumps({"sprint": 42, "velocity": 34, "stories": ["AUTH-101", "UI-205"]}),
    "workspace/company/engineering/incidents/inc_2025_03.md": "# Incident 2025-03\nPostmortem: DB timeout...",
    "workspace/company/marketing/campaigns/spring_promo.md": "# Spring Promo\nDiscount: 20%\nTarget: SMB segment",
    "workspace/archive/2025/meetings/q1_review_notes.txt": "Q1 review discussed churn rate at 4.2%...",
    "workspace/archive/2025/emails/old_thread_001.txt": "Re: Budget approval - approved for Q1",
    "workspace/tmp/drafts/reply_draft_old.txt": "Hi, thanks for reaching out. We'll get back to you soon.",
}

for path, content in distractor_files.items():
    full_path = os.path.join("/", path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# ===== THE MAIN PROBLEM INPUT =====
# A batch of 6 emails in a single JSON file with realistic messy content
emails = [
    {
        "id": "email_001",
        "from": "david.chen@enterprise-client.com",
        "subject": "紧急：合同续签问题 - 需要本周五前确认",
        "date": "2026-03-13",
        "body": (
            "您好，\n\n"
            "我是大客户企业的采购负责人陈大卫。我们的合同将于2026年3月31日到期，"
            "我需要在本周五（2026年3月15日）之前收到您的续签方案和最新报价单，"
            "否则我们将不得不考虑其他供应商。\n\n"
            "另外，请安排一个电话会议，讨论我们对新功能的需求，建议时间为下周一上午10点。\n\n"
            "期待您的回复。\n\n"
            "陈大卫\n企业采购部总监"
        )
    },
    {
        "id": "email_002",
        "from": "newsletter@saas-weekly.io",
        "subject": "本周SaaS行业动态 - 限时优惠！注册立减50%",
        "date": "2026-03-13",
        "body": (
            "亲爱的订阅者，\n\n"
            "本期内容：\n"
            "1. 2026年SaaS趋势报告免费下载\n"
            "2. AI工具大盘点\n"
            "3. 限时特惠：专业版年费订阅五折优惠，截止3月20日\n\n"
            "点击查看更多...\n\n"
            "取消订阅请点击此处"
        )
    },
    {
        "id": "email_003",
        "from": "pm_zhang@internal-company.com",
        "subject": "【会议纪要】Q1复盘 + Q2任务分配",
        "date": "2026-03-13",
        "body": (
            "各位同事好，\n\n"
            "以下是本次Q1复盘会议的纪要及Q2任务分配：\n\n"
            "任务1：产品组需要在2026年3月20日之前完成Q1用户调研报告，负责人：产品经理（收件人）。优先级：高。\n\n"
            "任务2：市场组整理竞品分析数据，截止日期2026年3月25日。优先级：中。\n\n"
            "任务3：技术组在2026年4月5日前完成API文档更新，优先级：低。\n\n"
            "任务4：请所有组负责人在2026年3月18日前提交Q2 OKR草稿，发送至pm_zhang@internal-company.com。优先级：高。\n\n"
            "如有问题请回复此邮件。\n\n张伟（产品经理）"
        )
    },
    {
        "id": "email_004",
        "from": "support@somespamsite.xyz",
        "subject": "您中奖了！领取价值10000元礼品卡",
        "date": "2026-03-13",
        "body": (
            "恭喜！您已被选中获得价值10000元的礼品卡！\n\n"
            "请立即点击链接领取：http://totally-legit-spam.xyz/claim?token=abc123\n\n"
            "本优惠24小时内有效，请勿错过！"
        )
    },
    {
        "id": "email_005",
        "from": "alice.johnson@partner-agency.com",
        "subject": "合作项目进展更新",
        "date": "2026-03-13",
        "body": (
            "你好，\n\n"
            "想跟你同步一下我们合作项目的最新进展。\n\n"
            "目前设计稿已完成初稿，正在内部评审。预计下周三（2026年3月19日）可以发给你们确认。\n\n"
            "没有特别紧急的事情，你有时间的时候看一下就好，主要是让你了解进度。\n\n"
            "最近有什么需要我们配合的欢迎告知。\n\n"
            "Alice Johnson\n合作伙伴机构"
        )
    },
    {
        "id": "email_006",
        "from": "hr@internal-company.com",
        "subject": "关于年假申请系统更新的通知",
        "date": "2026-03-13",
        "body": (
            "全体员工：\n\n"
            "HR系统将于2026年3月16日（本周一）进行维护升级，升级期间年假申请功能暂停使用，"
            "预计恢复时间为当天下午5点。\n\n"
            "如有紧急年假需求，请直接联系HR部门（内线1234）。\n\n"
            "此为系统通知，请勿回复。\n\nHR部门"
        )
    }
]

# Write the batch emails input file
emails_input_path = "/workspace/incoming_emails.json"
with open(emails_input_path, "w", encoding="utf-8") as f:
    json.dump({"batch_date": "2026-03-13", "emails": emails}, f, ensure_ascii=False, indent=2)

print("Input files generated successfully.")
print(f"Main input: {emails_input_path}")
print(f"Total emails: {len(emails)}")
print("Distractor files created:", len(distractor_files))