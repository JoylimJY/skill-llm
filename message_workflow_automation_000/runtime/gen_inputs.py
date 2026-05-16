import os
import json
import random

random.seed(42)

workspace = "/workspace"

# --- Create distractor directory structure ---
dirs = [
    "comms/drafts/archive",
    "comms/sent/2024",
    "comms/templates",
    "ops/vendor_contracts",
    "ops/onboarding",
    "finance/invoices",
    "finance/reports",
    "hr/policies",
    "hr/org_chart",
    "product/roadmap",
    "product/bugs",
    "legal/ndas",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractors = [
    ("comms/drafts/archive/old_investor_update_draft.txt", "Hi Sarah, wanted to loop you in on Q2 results..."),
    ("comms/sent/2024/onboarding_email_client_X.txt", "Welcome to the platform! Here's your login info."),
    ("comms/templates/generic_followup.txt", "Hope you're doing well! Just following up on our last conversation."),
    ("ops/vendor_contracts/acme_renewal.txt", "Contract renewal due: 2024-11-01. Value: $48,000/yr."),
    ("ops/onboarding/checklist.txt", "1. Set up accounts\n2. Introduce to team\n3. Schedule kickoff"),
    ("finance/invoices/inv_2024_087.txt", "Invoice #087 - $12,500 - Due 2024-10-15"),
    ("finance/reports/q3_summary.csv", "month,revenue,churn\nJul,120000,2.1\nAug,134000,1.9\nSep,141000,1.7"),
    ("hr/policies/pto_policy.txt", "Employees accrue 15 days PTO per year..."),
    ("hr/org_chart/current.txt", "CEO: Marcus\nCTO: Priya\nOps: Jordan\nSales: Lee"),
    ("product/roadmap/q4_priorities.txt", "P1: SSO integration\nP2: Bulk export\nP3: Audit logs"),
    ("product/bugs/open_issues.txt", "BUG-221: Data export timeout\nBUG-198: Login loop on mobile"),
    ("legal/ndas/vendor_nda_signed.txt", "NDA between Acme Corp and NovaSaaS signed 2024-01-10"),
]

for rel_path, content in distractors:
    with open(os.path.join(workspace, rel_path), "w") as f:
        f.write(content)

# --- CORE INPUT: style_reference.txt ---
# Shows the human's actual communication style: terse, no emojis, no pleasantries
style_reference_content = """=== My Last 5 Messages (Style Reference) ===

[To: Lee, Slack, 2024-10-01]
can you send me the Q3 deck before EOD

[To: Priya, Slack, 2024-10-02]
prod deploy pushed to tomorrow. let Marcus know

[To: vendor@acme.com, Email, 2024-10-03]
see attached. need response by Friday

[To: team@novasaas.com, Slack, 2024-10-04]
heads up - office closed thursday

[To: finance@novasaas.com, Email, 2024-10-05]
attached is the signed PO. please process
"""

with open(os.path.join(workspace, "comms/style_reference.txt"), "w") as f:
    f.write(style_reference_content)

# --- CORE INPUT: message_requests.json ---
# 6 message scenarios the agent must process
# Each has: id, context, desired_content_hint, recipient_info, urgency, sender_local_time, recipient_timezone
message_requests = [
    {
        "id": "MSG-001",
        "context": "Our biggest enterprise client, GlobalRetail Inc., sent a complaint email 2 hours ago saying their data exports have been broken for 3 days and they are 'deeply disappointed' and 'considering their options'. I need to respond.",
        "desired_content": "Acknowledge the issue, apologize, tell them we're on it.",
        "recipient": "procurement@globalretail.com",
        "recipient_type": "enterprise_client_complaint",
        "urgency": "high",
        "sender_local_time": "2024-10-07T14:30:00",
        "sender_timezone": "America/New_York",
        "recipient_timezone": "America/New_York"
    },
    {
        "id": "MSG-002",
        "context": "I need to tell our lead investor Sarah Chen (partner at Vertex Capital) about a positive Q3 revenue milestone. She's been supportive and I want to share the good news.",
        "desired_content": "Q3 revenue hit $141k MRR, up 17% QoQ. Team is executing well.",
        "recipient": "schen@vertexcapital.com",
        "recipient_type": "investor",
        "urgency": "low",
        "sender_local_time": "2024-10-07T10:00:00",
        "sender_timezone": "America/New_York",
        "recipient_timezone": "America/Los_Angeles"
    },
    {
        "id": "MSG-003",
        "context": "Production API is completely down right now. I need to alert our on-call engineer Priya immediately.",
        "desired_content": "API is down. Need you on it now.",
        "recipient": "priya@novasaas.com",
        "recipient_type": "internal_engineer",
        "urgency": "critical",
        "sender_local_time": "2024-10-07T14:35:00",
        "sender_timezone": "America/New_York",
        "recipient_timezone": "America/New_York"
    },
    {
        "id": "MSG-004",
        "context": "A prospective client asked if we can guarantee delivery of their custom integration by November 15th. Our sales rep Lee wants me to confirm this timeline in writing to close the deal.",
        "desired_content": "Confirm we can deliver the custom integration by November 15th.",
        "recipient": "cto@prospect-corp.com",
        "recipient_type": "prospective_client",
        "urgency": "medium",
        "sender_local_time": "2024-10-07T15:00:00",
        "sender_timezone": "America/New_York",
        "recipient_timezone": "America/Chicago"
    },
    {
        "id": "MSG-005",
        "context": "I want to update our board member David Kim about our Q3 results and mention we may need a small bridge round in Q1. This is the first time I'm reaching out to him directly (usually goes through our CEO Marcus).",
        "desired_content": "Q3 results strong. Flagging potential Q1 bridge round need.",
        "recipient": "dkim@boardmember.com",
        "recipient_type": "board_member",
        "urgency": "low",
        "sender_local_time": "2024-10-07T22:45:00",
        "sender_timezone": "America/New_York",
        "recipient_timezone": "America/New_York"
    },
    {
        "id": "MSG-006",
        "context": "Need to let the internal team Slack channel know that the weekly all-hands meeting this Thursday is cancelled because of the company offsite.",
        "desired_content": "Thursday all-hands cancelled, offsite this week.",
        "recipient": "#general (Slack)",
        "recipient_type": "internal_team_broadcast",
        "urgency": "low",
        "sender_local_time": "2024-10-07T09:00:00",
        "sender_timezone": "America/New_York",
        "recipient_timezone": "America/New_York"
    }
]

with open(os.path.join(workspace, "comms/message_requests.json"), "w") as f:
    json.dump(message_requests, f, indent=2)

print("Workspace generated successfully.")
print(f"Files created: style_reference.txt, message_requests.json, plus {len(distractors)} distractor files")