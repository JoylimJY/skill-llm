import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create a realistic deeply nested distractor structure for a hospital digital team
dirs = [
    "hospital_digital/reports/2024/q1",
    "hospital_digital/reports/2024/q2",
    "hospital_digital/reports/2024/q3",
    "hospital_digital/reports/2025/q1",
    "hospital_digital/user_data/archive",
    "hospital_digital/user_data/current",
    "hospital_digital/content/drafts",
    "hospital_digital/content/published",
    "hospital_digital/workflows/templates",
    "hospital_digital/workflows/logs",
    "hospital_digital/analytics/raw",
    "hospital_digital/analytics/processed",
    "hospital_digital/tools/configs",
    "hospital_digital/tools/scripts",
    "hospital_digital/meetings/notes",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files - realistic but irrelevant to the task
distractor_files = {
    "hospital_digital/reports/2024/q1/equipment_inventory.csv": "device_id,name,department,status\nMD001,CT Scanner,Radiology,active\nMD002,MRI Machine,Radiology,maintenance\nMD003,Ultrasound,Cardiology,active\n",
    "hospital_digital/reports/2024/q2/budget_summary.txt": "Q2 Budget Summary\nTotal Budget: 2,400,000 CNY\nSpent: 1,870,000 CNY\nRemaining: 530,000 CNY\nMain Categories: Equipment 45%, Staff Training 30%, IT 25%\n",
    "hospital_digital/reports/2024/q3/staff_training_log.json": json.dumps([
        {"staff_id": "S001", "course": "Medical Device Operation", "date": "2024-07-15", "score": 92},
        {"staff_id": "S002", "course": "Digital Health Basics", "date": "2024-08-02", "score": 87},
        {"staff_id": "S003", "course": "AI in Diagnostics", "date": "2024-09-10", "score": 95}
    ], indent=2),
    "hospital_digital/reports/2025/q1/transformation_roadmap.md": "# Digital Transformation Roadmap 2025\n\n## Phase 1: Infrastructure\n- Upgrade hospital information system\n- Deploy IoT sensors for equipment monitoring\n\n## Phase 2: AI Integration\n- Pilot AI-assisted diagnosis\n- Implement predictive maintenance\n\n## Phase 3: Education Platform\n- Launch staff e-learning portal\n- Create content library for medical devices\n",
    "hospital_digital/content/drafts/article_draft_001.txt": "Draft: Advances in Minimally Invasive Surgery Tools\nStatus: In Review\nAuthor: Dr. Chen\nTarget: Staff Education Newsletter\nNotes: Needs more statistics on recovery time improvements.\n",
    "hospital_digital/content/published/newsletter_march_2025.txt": "March 2025 Newsletter\nHighlights:\n1. New robotic surgery system installed in OR-3\n2. Digital pathology pilot results: 15% faster diagnosis\n3. Upcoming webinar on AI-powered imaging\n",
    "hospital_digital/workflows/templates/content_creation_sop.txt": "SOP: Content Creation for Staff Education\nStep 1: Identify topic from trend report\nStep 2: Draft outline\nStep 3: Expert review\nStep 4: Final approval\nStep 5: Publish to platform\n",
    "hospital_digital/workflows/logs/system_log_2025_02.txt": "2025-02-01 09:00 - System check OK\n2025-02-10 14:22 - Report generated for Q4 2024\n2025-02-18 11:05 - Content batch uploaded: 5 articles\n2025-02-25 16:00 - Scheduled report dispatched\n",
    "hospital_digital/analytics/raw/interaction_events_feb2025.jsonl": '{"event": "module_start", "module": 1, "ts": "2025-02-03T10:01:00"}\n{"event": "user_confirm", "choice": "skip", "ts": "2025-02-03T10:05:00"}\n{"event": "module_start", "module": 2, "ts": "2025-02-03T10:06:00"}\n{"event": "user_confirm", "choice": "continue", "ts": "2025-02-03T10:22:00"}\n',
    "hospital_digital/analytics/processed/kpi_dashboard_feb2025.json": json.dumps({
        "period": "2025-02",
        "total_reports_generated": 48,
        "avg_user_session_min": 34.5,
        "content_pieces_created": 12,
        "top_topics": ["medical device trends", "AI diagnostics", "digital health"]
    }, indent=2),
    "hospital_digital/tools/configs/system_settings.json": json.dumps({
        "system_name": "Hospital Digital Intelligence Hub",
        "version": "2.1.0",
        "timezone": "Asia/Shanghai",
        "report_schedule": ["10:00", "16:00"],
        "default_language": "zh-CN",
        "modules_enabled": [1, 2, 3, 4]
    }, indent=2),
    "hospital_digital/tools/scripts/export_report.sh": "#!/bin/bash\n# Export latest report to PDF\necho 'Exporting report...'\n# placeholder\n",
    "hospital_digital/meetings/notes/kickoff_2025_03_01.txt": "Meeting: Digital Transformation Kickoff\nDate: 2025-03-01\nAttendees: Dr. Wang (CMO), Ms. Li (IT Director), Mr. Zhang (Content Lead)\nAction Items:\n1. Finalize AI tool selection by March 15\n2. Draft content calendar for Q2\n3. Set up monitoring dashboard for medical device news\n",
    "hospital_digital/user_data/archive/old_profile_user_001_v1.json": json.dumps({
        "user_id": "user_med_007",
        "note": "ARCHIVED - outdated format, do not use",
        "legacy_fields": {"pref": "detailed", "confirm_always": True}
    }, indent=2),
    "hospital_digital/user_data/current/README_DO_NOT_USE.txt": "This directory contains current user profiles. Files may be in raw/unprocessed format and require normalization before use.\n",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)

# THE CORE PROBLEM FILE: messy raw user profile with raw counts, not derived rates
# The agent must compute: skip_rate, preferred_style, acceptance_rate, preferred_mode
# Then apply adaptive strategy thresholds from the SKILL.md
raw_profile = {
    "user_id": "user_med_007",
    "collected_at": "2025-03-10T09:30:00",
    "note": "RAW interaction data - rates NOT computed - requires normalization",
    
    # Raw counts for confirmation habits (skip_rate must be computed)
    "confirmation_raw": {
        "total_decisions": 40,
        "skip_count": 28,       # skip_rate = 28/40 = 0.70 → > 60% → reduce confirmation
        "avg_decision_time_ms": 1200
    },
    
    # Raw counts for output preference (preferred_style must be determined)
    "output_raw": {
        "detailed_count": 31,
        "concise_count": 9,
        # preferred_style: detailed_count > concise_count significantly → 'detailed'
        # 31 vs 9 out of 40 → detailed wins clearly
    },
    
    # Raw counts for recommendation acceptance (acceptance_rate must be computed)
    "recommendation_raw": {
        "total": 25,
        "accepted": 20,         # acceptance_rate = 20/25 = 0.80 → > 70% → more recommendations
    },
    
    # Raw counts for execution preference (preferred_mode must be determined)
    "execution_raw": {
        "parallel_count": 33,
        "serial_count": 7,      # parallel_count >> serial_count → preferred_mode = 'parallel'
    },
    
    # Module sequence history (messy, unsorted)
    "module_history_raw": [
        "module_1,module_2",
        "module_1,module_3",
        "module_1,module_2,module_4",
        "module_1,module_2",
        "module_1,module_2,module_3,module_4"
    ],
    
    "last_interaction": "2025-03-09T16:05:00"
}

raw_profile_path = os.path.join(workspace, "hospital_digital/user_data/current/user_med_007_raw.json")
with open(raw_profile_path, 'w', encoding='utf-8') as f:
    json.dump(raw_profile, f, indent=2, ensure_ascii=False)

# Also write a session request file to simulate the incoming business request
session_request = {
    "request_id": "REQ_2025_03_10_001",
    "submitted_by": "user_med_007",
    "submitted_at": "2025-03-10T10:00:00",
    "business_goal": "我需要监控医疗器械行业最新趋势动态，然后为我们的医护人员教育平台创作相关内容",
    "target_industry": "医疗器械",
    "note": "User wants: industry monitoring first, then content creation for education platform. Does NOT mention personal status analysis or workflow planning."
}

request_path = os.path.join(workspace, "hospital_digital/user_data/current/session_request_REQ_2025_03_10_001.json")
with open(request_path, 'w', encoding='utf-8') as f:
    json.dump(session_request, f, indent=2, ensure_ascii=False)

print("Workspace initialized successfully.")
print(f"Raw user profile: {raw_profile_path}")
print(f"Session request: {request_path}")