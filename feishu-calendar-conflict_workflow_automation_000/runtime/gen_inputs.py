import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Deep distractor directory structure ---
distractor_dirs = [
    "workspace/meetings/archive/2025/q1",
    "workspace/meetings/archive/2025/q2",
    "workspace/meetings/templates",
    "workspace/hr/onboarding",
    "workspace/hr/offboarding",
    "workspace/engineering/sprint_23",
    "workspace/engineering/sprint_24/notes",
    "workspace/product/roadmap",
    "workspace/product/specs/v2",
    "workspace/ops/monitoring",
]
for d in distractor_dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "workspace/meetings/archive/2025/q1/sprint_review_notes.txt": "Sprint 22 review was held on 2025-01-15. Attendees: Alice, Bob, Carol.",
    "workspace/meetings/archive/2025/q2/kickoff_summary.txt": "Q2 kickoff scheduled for April 3rd.",
    "workspace/meetings/templates/one_on_one_template.md": "# 1:1 Template\n- Last week\n- This week\n- Blockers",
    "workspace/hr/onboarding/checklist.json": json.dumps({"steps": ["setup laptop", "slack", "jira access"]}),
    "workspace/hr/offboarding/process.txt": "Offboarding process: revoke access, exit interview.",
    "workspace/engineering/sprint_23/velocity.csv": "story_points,completed\n34,30\n28,28",
    "workspace/engineering/sprint_24/notes/standup_2025-06-02.txt": "Alice: finished auth module. Bob: working on payment.",
    "workspace/product/roadmap/2025_themes.txt": "Theme 1: Growth. Theme 2: Reliability.",
    "workspace/product/specs/v2/api_design.md": "## API v2 Design\nRESTful endpoints for resource management.",
    "workspace/ops/monitoring/alert_rules.yaml": "alerts:\n  - name: high_cpu\n    threshold: 90",
    "workspace/meetings/templates/sprint_review_agenda.txt": "Sprint Review Agenda\n1. Demo\n2. Feedback\n3. Metrics",
    "workspace/engineering/sprint_24/notes/retro_2025-06-06.txt": "What went well: CI pipeline. What to improve: test coverage.",
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# --- The mock server script for Feishu APIs ---
# This is the core tool the agent must use
mock_server_script = r"""
from flask import Flask, request, jsonify
import json

app = Flask(__name__)

# Simulated user database
USERS = {
    "zhangwei": {"open_id": "ou_a1b2c3d4", "name": "Zhang Wei"},
    "liming": {"open_id": "ou_e5f6g7h8", "name": "Li Ming"},
    "wangfang": {"open_id": "ou_i9j0k1l2", "name": "Wang Fang"},
    "chenjun": {"open_id": "ou_m3n4o5p6", "name": "Chen Jun"},
    "zhang wei": {"open_id": "ou_a1b2c3d4", "name": "Zhang Wei"},
    "li ming": {"open_id": "ou_e5f6g7h8", "name": "Li Ming"},
    "wang fang": {"open_id": "ou_i9j0k1l2", "name": "Wang Fang"},
    "chen jun": {"open_id": "ou_m3n4o5p6", "name": "Chen Jun"},
}

# Busy slots for each user on 2026-07-15 (the target date)
# Zhang Wei: busy 09:30-10:30, busy 13:00-14:00
# Li Ming: busy 10:00-11:30, busy 15:00-16:00
# Wang Fang: busy 09:00-09:30, busy 11:00-12:00, busy 14:30-16:30
# Chen Jun: busy 10:30-12:00, busy 16:00-17:00

USER_BUSY = {
    "ou_a1b2c3d4": [  # Zhang Wei
        {"start": "2026-07-15T09:30:00+08:00", "end": "2026-07-15T10:30:00+08:00"},
        {"start": "2026-07-15T13:00:00+08:00", "end": "2026-07-15T14:00:00+08:00"},
    ],
    "ou_e5f6g7h8": [  # Li Ming
        {"start": "2026-07-15T10:00:00+08:00", "end": "2026-07-15T11:30:00+08:00"},
        {"start": "2026-07-15T15:00:00+08:00", "end": "2026-07-15T16:00:00+08:00"},
    ],
    "ou_i9j0k1l2": [  # Wang Fang
        {"start": "2026-07-15T09:00:00+08:00", "end": "2026-07-15T09:30:00+08:00"},
        {"start": "2026-07-15T11:00:00+08:00", "end": "2026-07-15T12:00:00+08:00"},
        {"start": "2026-07-15T14:30:00+08:00", "end": "2026-07-15T16:30:00+08:00"},
    ],
    "ou_m3n4o5p6": [  # Chen Jun
        {"start": "2026-07-15T10:30:00+08:00", "end": "2026-07-15T12:00:00+08:00"},
        {"start": "2026-07-15T16:00:00+08:00", "end": "2026-07-15T17:00:00+08:00"},
    ],
}

@app.route('/feishu_search_user', methods=['POST'])
def search_user():
    data = request.get_json()
    query = data.get('query', '').lower().strip()
    results = []
    for key, user in USERS.items():
        if query in key.lower() or query in user['name'].lower():
            results.append(user)
    # deduplicate by open_id
    seen = set()
    unique = []
    for r in results:
        if r['open_id'] not in seen:
            seen.add(r['open_id'])
            unique.append(r)
    return jsonify({"users": unique})

@app.route('/feishu_calendar_freebusy', methods=['POST'])
def freebusy():
    data = request.get_json()
    action = data.get('action')
    if action != 'list':
        return jsonify({"error": "Invalid action. Must be 'list'"}), 400

    time_min = data.get('time_min')
    time_max = data.get('time_max')
    user_ids = data.get('user_ids', [])

    if not time_min or not time_max:
        return jsonify({"error": "time_min and time_max are required"}), 400
    if not user_ids:
        return jsonify({"error": "user_ids is required"}), 400

    from datetime import datetime
    from dateutil.parser import parse as parse_dt

    t_min = parse_dt(time_min)
    t_max = parse_dt(time_max)

    # Collect all busy slots across all users
    all_busy = []
    user_busy_map = {}
    for uid in user_ids:
        slots = USER_BUSY.get(uid, [])
        user_busy = []
        for slot in slots:
            s = parse_dt(slot['start'])
            e = parse_dt(slot['end'])
            if s < t_max and e > t_min:
                clipped_s = max(s, t_min)
                clipped_e = min(e, t_max)
                user_busy.append({"start": clipped_s.isoformat(), "end": clipped_e.isoformat()})
                all_busy.append((clipped_s, clipped_e))
        user_busy_map[uid] = user_busy

    # Merge busy slots
    all_busy.sort(key=lambda x: x[0])
    merged = []
    for s, e in all_busy:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append([s, e])

    busy_slots_out = [{"start": s.isoformat(), "end": e.isoformat()} for s, e in merged]

    # Compute free slots
    free_slots_out = []
    prev = t_min
    for s, e in merged:
        if prev < s:
            free_slots_out.append({"start": prev.isoformat(), "end": s.isoformat()})
        prev = e
    if prev < t_max:
        free_slots_out.append({"start": prev.isoformat(), "end": t_max.isoformat()})

    return jsonify({
        "busy_slots": busy_slots_out,
        "free_slots": free_slots_out,
        "user_busy_details": user_busy_map
    })

@app.route('/feishu_calendar_event', methods=['POST'])
def create_event():
    data = request.get_json()
    action = data.get('action')
    if action != 'create':
        return jsonify({"error": "Invalid action"}), 400
    summary = data.get('summary')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    if not all([summary, start_time, end_time]):
        return jsonify({"error": "summary, start_time, end_time required"}), 400
    return jsonify({
        "event_id": "evt_mock_20260715",
        "summary": summary,
        "start_time": start_time,
        "end_time": end_time,
        "status": "confirmed"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7777, debug=False)
"""

with open(os.path.join(workspace, "mock_feishu_server.py"), "w") as f:
    f.write(mock_server_script)

# --- Skill.md reference config so agent knows which endpoints to call ---
skill_config = {
    "feishu_api_base": "http://localhost:7777",
    "endpoints": {
        "search_user": "/feishu_search_user",
        "freebusy": "/feishu_calendar_freebusy",
        "event": "/feishu_calendar_event"
    }
}
with open(os.path.join(workspace, "feishu_config.json"), "w") as f:
    json.dump(skill_config, f, indent=2)

# --- Team roster file (messy, informal names) ---
team_roster = """Sprint Review - Required Attendees
Meeting organizer: Product Manager (you)
Engineering team members needed:
  - Zhang Wei (backend lead)
  - Li Ming (frontend)
  - Wang Fang (QA)
  - Chen Jun (devops)

Desired date: 2026-07-15
Preferred window: 09:00 to 18:00 (working hours)
Required meeting length: 90 minutes
"""
with open(os.path.join(workspace, "sprint_review_request.txt"), "w") as f:
    f.write(team_roster)

print("Workspace generated successfully.")
print(f"Files created in: {workspace}")