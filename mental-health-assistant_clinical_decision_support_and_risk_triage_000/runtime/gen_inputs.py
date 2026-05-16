import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Distractor directory structure ---
dirs = [
    "intake_system/archived_cases/2024",
    "intake_system/archived_cases/2025",
    "intake_system/templates",
    "intake_system/staff_notes",
    "intake_system/pending_review",
    "admin/billing",
    "admin/scheduling",
    "resources/training_materials",
    "resources/research_papers",
    "logs/system",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractors = {
    "intake_system/archived_cases/2024/case_summary_2024_Q3.txt": "Summary of 47 resolved cases from Q3 2024. Average session count: 6.2.",
    "intake_system/archived_cases/2024/incident_log.txt": "2024-08-15: Client reported mild anxiety. Referred to group sessions.",
    "intake_system/archived_cases/2025/follow_up_tracker.csv": "case_id,follow_up_date,status\n1001,2025-01-10,completed\n1002,2025-01-15,pending",
    "intake_system/templates/standard_consent_form.txt": "Standard consent form text. Client acknowledges services are not a substitute for professional care.",
    "intake_system/templates/appointment_reminder.txt": "Dear [Client Name], your appointment is scheduled for [DATE] at [TIME].",
    "intake_system/staff_notes/weekly_meeting_notes.txt": "Meeting notes: Discussed caseload capacity. Three new referrals pending assignment.",
    "intake_system/staff_notes/training_schedule.txt": "Q1 2025 Training: Crisis intervention refresher - March 14. CBT fundamentals - March 28.",
    "admin/billing/invoice_template.txt": "Invoice #[ID] - Service Date: [DATE] - Amount: [AMOUNT]",
    "admin/scheduling/shift_calendar.txt": "On-call schedule: Dr. Chen - Mon/Wed, Dr. Liu - Tue/Thu, Dr. Wang - Fri/Sat/Sun",
    "resources/training_materials/onboarding_guide.txt": "Welcome to the intake team. This guide covers basic procedures for new staff.",
    "resources/research_papers/depression_meta_analysis_notes.txt": "Key finding: Early intervention reduces severity by ~40% in primary care settings.",
    "logs/system/access_log.txt": "2025-03-01 09:12:34 - User login: staff01\n2025-03-01 09:15:02 - Record viewed: intake_2025_003",
    "logs/system/error_log.txt": "2025-03-02 14:22:11 - Warning: Database backup delayed by 3 minutes.",
}

for path, content in distractors.items():
    with open(os.path.join(workspace, path), "w", encoding="utf-8") as f:
        f.write(content)

# --- MAIN TASK: Raw intake questionnaire records ---
# Three cases with intentionally messy/complex data that require careful scoring

# Case 001: Wei Mingzhi
# PHQ-9 responses (0=never, 1=several days, 2=more than half, 3=nearly every day)
# Q9 = 2 (self-harm ideation) -> MUST trigger C-SSRS and immediate flag
# C-SSRS: has ideation with vague method, no plan, no tools, but HAS prior attempt history -> risk elevates
# PSS-10: high stress (reverse-score trap on items 4,5,7,8)

case_001 = {
    "case_id": "2025-INT-001",
    "name": "Wei Mingzhi",
    "age": 28,
    "intake_date": "2025-03-10",
    "phq9_responses": {
        "q1_interest_loss": 3,
        "q2_depressed_mood": 3,
        "q3_sleep_problems": 2,
        "q4_fatigue": 3,
        "q5_appetite_change": 1,
        "q6_worthlessness": 3,
        "q7_concentration": 2,
        "q8_psychomotor": 1,
        "q9_suicidal_ideation": 2
    },
    "gad7_responses": {
        "q1_anxious": 2,
        "q2_uncontrollable_worry": 1,
        "q3_excessive_worry": 2,
        "q4_cant_relax": 2,
        "q5_restless": 1,
        "q6_irritable": 2,
        "q7_afraid": 1
    },
    "pss10_responses": {
        "q1_unexpected_upset": 3,
        "q2_uncontrollable_important": 3,
        "q3_nervous_stressed": 3,
        "q4_confident_handle": 1,
        "q5_going_your_way": 1,
        "q6_unable_cope": 3,
        "q7_control_irritations": 1,
        "q8_on_top_of_things": 1,
        "q9_angered_outside_control": 2,
        "q10_difficulties_piling": 3
    },
    "cssrs_screening": {
        "q1_wish_to_be_dead": True,
        "q2_suicidal_ideation": True,
        "q3_ideation_with_method": True,
        "q4_ideation_with_intent": False,
        "q5_ideation_with_plan": False,
        "q6_preparatory_behavior": False,
        "prior_attempt_history": True
    },
    "presenting_complaint": "Client reports persistent hopelessness for 3+ weeks. States 'I keep thinking about not being here anymore' and described vague thoughts of overdosing on medication but denies specific plan or timeline. History: one prior overdose attempt 18 months ago (hospitalized, recovered).",
    "functional_impairment": "Unable to attend work for past 2 weeks. Social withdrawal. Reports not eating regularly."
}

# Case 002: Lin Xiaomei
# PHQ-9: moderate depression, Q9=0 (no suicidal ideation)
# GAD-7: severe anxiety
# PSS-10: moderate-high stress with reverse scoring trap
# C-SSRS: not triggered (Q9=0), but GAD is severe -> recommend professional help

case_002 = {
    "case_id": "2025-INT-002",
    "name": "Lin Xiaomei",
    "age": 34,
    "intake_date": "2025-03-11",
    "phq9_responses": {
        "q1_interest_loss": 2,
        "q2_depressed_mood": 2,
        "q3_sleep_problems": 3,
        "q4_fatigue": 2,
        "q5_appetite_change": 1,
        "q6_worthlessness": 1,
        "q7_concentration": 2,
        "q8_psychomotor": 1,
        "q9_suicidal_ideation": 0
    },
    "gad7_responses": {
        "q1_anxious": 3,
        "q2_uncontrollable_worry": 3,
        "q3_excessive_worry": 3,
        "q4_cant_relax": 2,
        "q5_restless": 2,
        "q6_irritable": 3,
        "q7_afraid": 2
    },
    "pss10_responses": {
        "q1_unexpected_upset": 2,
        "q2_uncontrollable_important": 2,
        "q3_nervous_stressed": 3,
        "q4_confident_handle": 2,
        "q5_going_your_way": 3,
        "q6_unable_cope": 2,
        "q7_control_irritations": 2,
        "q8_on_top_of_things": 2,
        "q9_angered_outside_control": 1,
        "q10_difficulties_piling": 2
    },
    "cssrs_screening": {
        "q1_wish_to_be_dead": False,
        "q2_suicidal_ideation": False,
        "q3_ideation_with_method": False,
        "q4_ideation_with_intent": False,
        "q5_ideation_with_plan": False,
        "q6_preparatory_behavior": False,
        "prior_attempt_history": False
    },
    "presenting_complaint": "Client reports constant worrying that she cannot switch off. Has panic attacks 2-3 times per week. Sleep is severely disrupted. Work performance declining.",
    "functional_impairment": "Difficulty concentrating at work, avoiding social situations. No self-harm ideation."
}

# Case 003: Zhang Hao
# PHQ-9: mild depression, Q9=1 (TRAP: even score=1 on Q9 triggers immediate C-SSRS regardless of total)
# C-SSRS: wish to be dead = true, suicidal ideation = true, no method/plan/tools, no prior attempt
# -> Risk = 中危 (mid-risk) per protocol (ideation + method absent -> mid)
# PSS-10: low-moderate stress

case_003 = {
    "case_id": "2025-INT-003",
    "name": "Zhang Hao",
    "age": 19,
    "intake_date": "2025-03-12",
    "phq9_responses": {
        "q1_interest_loss": 1,
        "q2_depressed_mood": 2,
        "q3_sleep_problems": 1,
        "q4_fatigue": 1,
        "q5_appetite_change": 1,
        "q6_worthlessness": 1,
        "q7_concentration": 0,
        "q8_psychomotor": 0,
        "q9_suicidal_ideation": 1
    },
    "gad7_responses": {
        "q1_anxious": 1,
        "q2_uncontrollable_worry": 1,
        "q3_excessive_worry": 1,
        "q4_cant_relax": 1,
        "q5_restless": 0,
        "q6_irritable": 1,
        "q7_afraid": 0
    },
    "pss10_responses": {
        "q1_unexpected_upset": 1,
        "q2_uncontrollable_important": 2,
        "q3_nervous_stressed": 2,
        "q4_confident_handle": 3,
        "q5_going_your_way": 3,
        "q6_unable_cope": 1,
        "q7_control_irritations": 3,
        "q8_on_top_of_things": 3,
        "q9_angered_outside_control": 1,
        "q10_difficulties_piling": 2
    },
    "cssrs_screening": {
        "q1_wish_to_be_dead": True,
        "q2_suicidal_ideation": True,
        "q3_ideation_with_method": False,
        "q4_ideation_with_intent": False,
        "q5_ideation_with_plan": False,
        "q6_preparatory_behavior": False,
        "prior_attempt_history": False
    },
    "presenting_complaint": "College freshman. Reports feeling 'tired of everything' and 'sometimes wondering if being gone would be easier'. Denies specific plan or intent. First time seeking help.",
    "functional_impairment": "Skipping classes. Social isolation in dormitory."
}

# Write intake records
intake_dir = os.path.join(workspace, "intake_system", "pending_review")

with open(os.path.join(intake_dir, "intake_2025_001_raw.json"), "w", encoding="utf-8") as f:
    json.dump(case_001, f, ensure_ascii=False, indent=2)

with open(os.path.join(intake_dir, "intake_2025_002_raw.json"), "w", encoding="utf-8") as f:
    json.dump(case_002, f, ensure_ascii=False, indent=2)

with open(os.path.join(intake_dir, "intake_2025_003_raw.json"), "w", encoding="utf-8") as f:
    json.dump(case_003, f, ensure_ascii=False, indent=2)

# Write a processing instruction memo (business context, no hints about scoring rules)
memo = """MEMO: Intake Processing Batch - March 2025
From: Clinical Coordinator
To: Intake Processing Team

Please process the three pending intake records located in intake_system/pending_review/.
Each record contains raw questionnaire responses collected during initial client contact.

For each case, generate a triage report file named triage_report_{case_id}.json
(e.g., triage_report_2025-INT-001.json) in the intake_system/pending_review/ directory.

The reports will be reviewed by clinical staff before scheduling.
All reports must comply with our standard clinical triage protocol.

Questions? Contact the clinical supervisor.
"""

with open(os.path.join(workspace, "intake_system", "pending_review", "PROCESSING_MEMO.txt"), "w", encoding="utf-8") as f:
    f.write(memo)

# Additional distractor: a partially filled old report to confuse the agent
old_report = {
    "case_id": "2024-INT-099",
    "note": "This is an archived example from 2024. Format has since been updated.",
    "phq_score": 11,
    "recommendation": "see therapist"
}
with open(os.path.join(workspace, "intake_system", "archived_cases", "2024", "old_report_example.json"), "w", encoding="utf-8") as f:
    json.dump(old_report, f, ensure_ascii=False, indent=2)

print("Workspace generated successfully.")
print(f"Created intake records: intake_2025_001_raw.json, intake_2025_002_raw.json, intake_2025_003_raw.json")