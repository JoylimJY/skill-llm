import os
import random

random.seed(42)

# Create deeply nested directory structure with distractor files
dirs = [
    "/workspace",
    "/workspace/projects/saas_platform",
    "/workspace/projects/saas_platform/q3_roadmap",
    "/workspace/projects/saas_platform/q3_roadmap/feature_specs",
    "/workspace/projects/saas_platform/client_escalations",
    "/workspace/projects/saas_platform/client_escalations/enterprise",
    "/workspace/projects/internal_comms",
    "/workspace/projects/internal_comms/templates",
    "/workspace/projects/internal_comms/archive",
    "/workspace/hr/policies",
    "/workspace/hr/onboarding",
    "/workspace/finance/q3_reports",
    "/workspace/finance/invoices",
    "/workspace/tech_docs/api",
    "/workspace/tech_docs/architecture",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# Distractor files
distractor_files = {
    "/workspace/projects/saas_platform/q3_roadmap/roadmap_v3.md": """# Q3 Product Roadmap
## Priority Features
- [ ] SSO Integration (P0, due Aug 15)
- [ ] Bulk Export API (P1, due Aug 30)  
- [ ] Dashboard Customization (P2, due Sep 15)

Owner: Product Team
Last Updated: 2024-07-01
""",
    "/workspace/projects/saas_platform/q3_roadmap/feature_specs/sso_spec.md": """# SSO Integration Spec
Version: 0.3
Status: In Development

## Acceptance Criteria
1. SAML 2.0 support
2. OAuth 2.0 support
3. Session timeout: 8 hours

## Dev Assignee: @backend-team
## Expected Completion: 2024-08-10 (DELAYED from 2024-07-30)
""",
    "/workspace/projects/saas_platform/client_escalations/enterprise/acme_ticket_2024_0712.txt": """Ticket #E-20240712-004
Client: ACME Corp
Contact: Sarah Johnson (VP Engineering)
Priority: CRITICAL

Issue: SSO integration promised for July 30 not delivered.
Client is threatening to escalate to C-suite.
Internal SLA breach confirmed.
""",
    "/workspace/projects/saas_platform/client_escalations/enterprise/techcorp_notes.txt": """Meeting Notes - TechCorp QBR
Date: 2024-07-05

Action items:
- Confirm SSO timeline (OVERDUE)
- Send updated API docs
- Schedule follow-up for Aug 1
""",
    "/workspace/projects/internal_comms/templates/email_template_generic.txt": """Subject: [Action Required] [Topic]

Hi [Name],

I hope this message finds you well.

Regarding [topic], please note that [details].

Best regards,
[Your Name]
""",
    "/workspace/projects/internal_comms/archive/old_standup_notes_jun.txt": """Standup Notes - June 2024
- SSO feature: 60% complete
- Blockers: Auth library compatibility issue
- Dev estimate: needs 2 more weeks
- PM flagged client risk
""",
    "/workspace/hr/policies/communication_policy.txt": """Corporate Communication Policy v2.1

All external communications must be approved by PR.
Internal escalations should follow the chain of command.
Slack is the primary async communication tool.
Email is required for formal commitments.
""",
    "/workspace/hr/onboarding/new_hire_checklist.txt": """New Hire Checklist
[ ] Set up laptop
[ ] Join Slack channels: #general, #engineering, #product
[ ] Read communication guidelines
[ ] 1:1 with manager in first week
""",
    "/workspace/finance/q3_reports/burn_rate_july.csv": """Category,Budget,Actual,Variance
Engineering,150000,162000,-12000
Product,45000,44200,800
Marketing,60000,58000,2000
""",
    "/workspace/tech_docs/api/api_changelog.md": """# API Changelog
## v2.4.1 (2024-07-10)
- Fixed rate limiting bug
- Added bulk endpoint /api/v2/export/bulk

## v2.4.0 (2024-07-01)  
- SSO endpoints added (BETA, not production-ready)
""",
    "/workspace/tech_docs/architecture/system_overview.txt": """System Architecture Overview
- Frontend: React 18
- Backend: Node.js + Express
- Auth: Passport.js (SSO module: 70% complete)
- DB: PostgreSQL 15
""",
    "/workspace/finance/invoices/acme_invoice_q2.txt": """Invoice #INV-2024-Q2-ACME
Client: ACME Corp
Amount: $48,000
Status: PAID
Contract includes: SSO Integration (deliverable Q3)
""",
}

for path, content in distractor_files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# THE CORE INPUT: The raw, emotionally charged draft the PM wants to send
raw_draft_content = """=== 发件人 (Sender) ===
王芳 (Product Manager, B2B SaaS Platform)

=== 沟通对象 (Target Audience) ===
- 主要目标：李明（后端技术负责人，平级）
- 次要目标（如平级沟通失败）：张总（研发VP，向上汇报）
- 外部目标：ACME Corp 的 Sarah Johnson（企业客户VP）

=== 背景 (Background) ===
SSO集成功能原定7月30日上线，现在已经是8月5日了还没有任何进展。
客户 ACME Corp 已经发来措辞严厉的投诉邮件，威胁要向他们CEO层面反映。
王芳在周会上已经提醒过李明两次，但李明每次都说"快了快了"，然后继续延期。
ACME Corp 这个合同价值约48万人民币/年，是公司今年最大的企业客户。

=== 原始草稿（带情绪，需要润色）===
李明，

我真的不知道你们后端团队在干什么！SSO 已经延期整整一周了，你们根本不把这个当回事！
客户都快把我骂死了，你知不知道你们拖着不做给我造成了多大的麻烦？！
我现在需要你今天——就是今天！——给我一个上线日期，不然我就直接去找张总了！
你之前说的"快了快了"到底是什么意思？什么叫快了？你能不能给个准信？
这种事再发生一次，我们之间的合作就没法愉快了！

王芳
"""

raw_draft_path = "/workspace/projects/internal_comms/raw_draft_pm_wang_fang.txt"
with open(raw_draft_path, "w", encoding="utf-8") as f:
    f.write(raw_draft_content)

print("Workspace generated successfully.")
print(f"Raw draft created at: {raw_draft_path}")
print("\nDirectory structure:")
for root, dirs_list, files in os.walk("/workspace"):
    level = root.replace("/workspace", "").count(os.sep)
    indent = " " * 2 * level
    print(f"{indent}{os.path.basename(root)}/")
    sub_indent = " " * 2 * (level + 1)
    for file in files:
        print(f"{sub_indent}{file}")