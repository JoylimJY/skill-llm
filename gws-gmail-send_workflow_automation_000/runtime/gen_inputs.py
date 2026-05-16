import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# Create a realistic corporate marketing directory structure with distractor files
dirs = [
    "marketing/campaigns/q3_2024",
    "marketing/campaigns/q2_2024",
    "marketing/assets/logos",
    "marketing/assets/templates",
    "marketing/reports/quarterly",
    "marketing/reports/monthly",
    "legal/compliance",
    "legal/contracts",
    "finance/q3_2024",
    "comms/internal",
    "comms/external",
    "it/tools/config",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files (not relevant to task)
distractor_files = {
    "marketing/campaigns/q2_2024/campaign_brief.txt": "Q2 Summer Campaign - Completed",
    "marketing/campaigns/q2_2024/results.json": json.dumps({"impressions": 142000, "clicks": 8900}),
    "marketing/assets/templates/newsletter_template.html": "<p>Dear {{name}},</p><p>{{content}}</p>",
    "marketing/assets/templates/old_email_draft.txt": "Draft from Q1 - DO NOT USE",
    "legal/compliance/gdpr_checklist.txt": "GDPR Compliance Checklist v2.3\n- Data retention: 90 days\n- Opt-out honored: Yes",
    "legal/contracts/vendor_nda_template.txt": "Non-Disclosure Agreement Template - Legal Dept",
    "finance/q3_2024/budget_allocation.csv": "Department,Budget,Spent\nMarketing,50000,32000\nSales,80000,61000",
    "comms/internal/slack_guidelines.txt": "Internal Slack usage guidelines - updated 2024-08-01",
    "comms/external/press_release_draft.txt": "FOR IMMEDIATE RELEASE: Acme Corp announces Q3 results...",
    "it/tools/config/workspace_settings.json": json.dumps({"theme": "dark", "timeout": 30}),
    "marketing/reports/monthly/august_metrics.csv": "Metric,Value\nOpen Rate,22.4%\nClick Rate,4.1%",
}

for path, content in distractor_files.items():
    full_path = workspace / path
    full_path.write_text(content)

# Create the actual attachment files the agent must attach
q3_report_content = b"""%PDF-1.4 fake quarterly report
Q3 2024 Investor Report
Revenue: $4.2M
Growth: 18% YoY
Highlights:
- Launched 3 new product lines
- Expanded to 5 new markets
- Employee headcount: 312
"""
(workspace / "marketing/reports/quarterly/Q3_2024_Investor_Report.pdf").write_bytes(q3_report_content)

logo_content = b"PNG\x89FAKE_LOGO_BINARY_DATA_acme_corp_logo_2024"
(workspace / "marketing/assets/logos/acme_corp_logo.png").write_bytes(logo_content)

# Create the task specification file (business context only, no tool hints)
task_spec = {
    "campaign": "Q3 2024 Investor Update",
    "primary_recipients": ["investors@acmecorp.com", "board-notify@partners.vc"],
    "cc_recipients": ["legal-review@acmecorp.com", "compliance@acmecorp.com"],
    "bcc_recipients": ["ceo-blind@acmecorp.com", "cfo-blind@acmecorp.com"],
    "from_alias": "marketing-noreply@acmecorp.com",
    "subject": "Acme Corp Q3 2024 Investor Update",
    "body_html": "<h2>Q3 2024 Performance Highlights</h2><p>Dear Investors,</p><p>We are pleased to share our <b>Q3 2024 results</b>. Please find the detailed report and our company logo attached.</p><p>Revenue grew <b>18% YoY</b> to $4.2M. <a href='https://acmecorp.com/ir'>Investor Relations Portal</a></p><br><p>Best regards,<br>Acme Corp Marketing Team</p>",
    "attachments": [
        "marketing/reports/quarterly/Q3_2024_Investor_Report.pdf",
        "marketing/assets/logos/acme_corp_logo.png"
    ],
    "notes": "This is the official Q3 investor communication. Send from the marketing alias. Legal and compliance must be CC'd. Board members receive blind copies only."
}

(workspace / "marketing/campaigns/q3_2024/campaign_spec.json").write_text(
    json.dumps(task_spec, indent=2)
)

# Create a mock command capture log directory
(workspace / ".gws_mock").mkdir(exist_ok=True)
(workspace / ".gws_mock/calls.log").write_text("")

print("Workspace initialized successfully.")
print("Key files created:")
print("  - marketing/campaigns/q3_2024/campaign_spec.json (task specification)")
print("  - marketing/reports/quarterly/Q3_2024_Investor_Report.pdf (attachment)")
print("  - marketing/assets/logos/acme_corp_logo.png (attachment)")