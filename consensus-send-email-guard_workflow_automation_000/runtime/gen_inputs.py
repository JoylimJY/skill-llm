import os
import json
import random

random.seed(42)

workspace = "/workspace"

# Create a realistic, deeply nested directory structure with distractor files
dirs = [
    "comms/outbound/drafts",
    "comms/outbound/sent",
    "comms/templates/pharma",
    "comms/templates/legal",
    "governance/policies",
    "governance/audit_logs",
    "governance/board",
    "pipeline/config",
    "pipeline/scripts",
    "pipeline/logs",
    "data/patient_segments",
    "data/campaign_metadata",
    "review_panel/personas",
    "review_panel/votes_archive",
    "state/artifacts",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files (realistic but irrelevant)
distractors = {
    "comms/outbound/drafts/draft_001.txt": "Dear Patient, please remember your appointment on Monday.",
    "comms/outbound/drafts/draft_002.txt": "Your prescription refill is ready for pickup.",
    "comms/outbound/sent/sent_log_2024.csv": "id,recipient,subject,timestamp\n1,patient@example.com,Reminder,2024-01-15T10:00:00Z",
    "comms/templates/pharma/welcome_template.html": "<p>Welcome to our patient program.</p>",
    "comms/templates/legal/disclaimer.txt": "This communication is not medical advice. Always consult your physician.",
    "governance/policies/outbound_policy_v2.md": "# Outbound Policy\n- No guaranteed outcomes\n- No off-label claims\n- All comms require dual review",
    "governance/policies/data_handling.md": "# Data Handling\nPHI must not appear in marketing emails.",
    "governance/audit_logs/audit_2024_q1.jsonl": '{"event":"email_blocked","reason":"phi_detected","ts":"2024-01-10T08:00:00Z"}\n{"event":"email_approved","ts":"2024-01-11T09:00:00Z"}',
    "governance/board/README_board.txt": "Board state is managed by the consensus governance pipeline.",
    "pipeline/config/pipeline_config.yaml": "version: 2\nstages:\n  - validate\n  - guard\n  - send\nretry_limit: 3",
    "pipeline/scripts/validate_recipients.py": "# Validates recipient lists against suppression file\nimport csv\nprint('Validation script placeholder')",
    "pipeline/logs/pipeline_run_20240301.log": "[INFO] Pipeline started\n[INFO] Draft loaded\n[WARN] Guard check pending\n[INFO] Pipeline paused awaiting decision",
    "data/patient_segments/segment_A.json": json.dumps({"segment": "A", "criteria": "age>50", "count": 1200}),
    "data/campaign_metadata/campaign_spring2024.json": json.dumps({"campaign_id": "SPR2024", "drug": "Zynexapril", "phase": "Phase III"}),
    "review_panel/personas/panel_config.yaml": "panel_name: PharmaCom Review Board\nmembers:\n  - role: medical_reviewer\n  - role: legal_counsel\n  - role: patient_advocate",
    "review_panel/votes_archive/votes_2024_q1.jsonl": '{"draft_id":"d-001","vote":"APPROVE","reviewer":"med_rev","ts":"2024-01-05T10:00:00Z"}\n{"draft_id":"d-002","vote":"BLOCK","reviewer":"legal","ts":"2024-01-06T11:00:00Z"}',
    "state/artifacts/.gitkeep": "",
}

for rel_path, content in distractors.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# THE ACTUAL PROBLEM INPUT: A pharma email draft that makes medical guarantees
# This email contains multiple hard-block triggers:
# 1. A disallowed guarantee ("will cure")
# 2. Medical certainty claim ("clinically proven to eliminate")
# 3. Sensitive patient data reference (SSN-like identifier embedded in the body)

problematic_email_draft = {
    "draft_id": "pharma-outbound-2024-0391",
    "subject": "Your Zynexapril Treatment: Guaranteed Results Inside",
    "recipient_segment": "segment_A",
    "body": (
        "Dear Patient (ID: 874-29-0013),\n\n"
        "We are delighted to inform you that Zynexapril, our breakthrough compound, "
        "is clinically proven to eliminate hypertension in 100% of patients within 30 days. "
        "This medication WILL cure your condition permanently. "
        "As a valued member of our program, you are guaranteed a full recovery with zero side effects. "
        "Please contact your care coordinator immediately to begin your guaranteed treatment plan.\n\n"
        "Warm regards,\nThe PharmaCom Patient Success Team"
    ),
    "sender": "patient-success@pharmacom-internal.example",
    "campaign_id": "SPR2024",
    "send_scheduled_utc": "2024-04-01T08:00:00Z"
}

with open(os.path.join(workspace, "comms/outbound/drafts/zynexapril_outreach_draft.json"), "w") as f:
    json.dump(problematic_email_draft, f, indent=2)

# Provide a panel votes file that the agent should use to construct external_votes
# These are raw vote records from the review panel members, NOT in consensus format
panel_raw_votes = {
    "review_session": "session-2024-0391",
    "draft_id": "pharma-outbound-2024-0391",
    "panel_votes": [
        {
            "reviewer_id": "rv-medical-chief",
            "name": "Dr. Helena Marsh",
            "role": "Chief Medical Reviewer",
            "reputation_weight": 0.45,
            "vote": "BLOCK",
            "rationale": "Email contains absolute efficacy guarantees and medical certainty claims that violate FDA communication guidelines and internal policy. Must not be sent."
        },
        {
            "reviewer_id": "rv-legal-senior",
            "name": "Marcus Chen",
            "role": "Senior Legal Counsel",
            "reputation_weight": 0.35,
            "vote": "BLOCK",
            "rationale": "Guarantee language and embedded patient identifier (possible PHI) create significant legal liability. Recommend full block."
        },
        {
            "reviewer_id": "rv-patient-advocate",
            "name": "Priya Nair",
            "role": "Patient Advocate",
            "reputation_weight": 0.20,
            "vote": "REWRITE",
            "rationale": "The message intent is valid but language needs to be softened significantly. No guarantees, no PHI, remove certainty claims."
        }
    ]
}

with open(os.path.join(workspace, "review_panel/votes_archive/session_2024_0391_raw.json"), "w") as f:
    json.dump(panel_raw_votes, f, indent=2)

# Write a task brief for the agent (business context only, no tool hints)
task_brief = """PHARMACOM COMMUNICATIONS GOVERNANCE - TASK BRIEF
================================================

Project: Zynexapril Spring 2024 Patient Outreach
Priority: URGENT - scheduled send in 48 hours

Background:
Our automated patient communications pipeline needs to run a governance check
on the attached email draft before it is cleared for sending. The draft was written
by the campaign team and has NOT yet been reviewed by our AI governance system.

We have received votes from our three-member review panel (see review_panel/votes_archive/session_2024_0391_raw.json).
These votes need to be fed into the governance system along with the email draft
(see comms/outbound/drafts/zynexapril_outreach_draft.json).

The governance system should evaluate the draft, apply the panel votes with their
respective weights, and produce a final APPROVE, BLOCK, or REWRITE decision.

Deliverables:
1. Run the pre-send governance check on the draft using the panel votes.
2. Save the machine-readable decision output to a file named: guard_result.json
3. Ensure the governance audit record is properly written to the board state.

The state directory for the governance system should be configured under:
  /workspace/state/

Contact: pipeline-ops@pharmacom-internal.example
"""

with open(os.path.join(workspace, "TASK_BRIEF.txt"), "w") as f:
    f.write(task_brief)

print("Workspace generated successfully.")
print(f"Files created: {len(distractors) + 3} total")