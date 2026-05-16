import os
import json
import random
from datetime import datetime, timedelta

random.seed(42)

WORKSPACE = "/workspace"

# --- Directory structure ---
dirs = [
    "marketplace/publishers/neural-forge",
    "marketplace/publishers/neural-forge/skills",
    "marketplace/publishers/neural-forge/engagement",
    "marketplace/publishers/neural-forge/reviews",
    "marketplace/publishers/rival-dev",
    "marketplace/publishers/rival-dev/skills",
    "marketplace/publishers/rival-dev/engagement",
    "marketplace/analytics/raw_events",
    "marketplace/analytics/cohort_data",
    "marketplace/platform/config",
    "marketplace/platform/logs",
    "marketplace/archive/2024",
    "marketplace/archive/2024/removed",
    "internal/trust_team",
    "internal/trust_team/templates",
    "internal/trust_team/prior_reports",
    "internal/ops",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ── Distractor files ──────────────────────────────────────────────────────────
# 1
with open(os.path.join(WORKSPACE, "marketplace/platform/config/feature_flags.json"), "w") as f:
    json.dump({"editor_picks_enabled": True, "max_featured_skills": 5, "auto_audit": False}, f, indent=2)

# 2
with open(os.path.join(WORKSPACE, "marketplace/platform/logs/deploy_log.txt"), "w") as f:
    f.write("2025-08-01T09:00:00Z [INFO] Deployed marketplace v3.2.1\n")
    f.write("2025-08-15T11:30:00Z [INFO] Search index rebuilt\n")
    f.write("2025-09-01T08:00:00Z [WARN] Anomaly detector disabled for maintenance\n")

# 3
with open(os.path.join(WORKSPACE, "marketplace/analytics/raw_events/schema.json"), "w") as f:
    json.dump({
        "event_types": ["install", "upvote", "review", "view", "uninstall"],
        "required_fields": ["event_id", "skill_id", "user_id", "timestamp"]
    }, f, indent=2)

# 4
with open(os.path.join(WORKSPACE, "marketplace/archive/2024/removed/banned_publishers.txt"), "w") as f:
    f.write("# Publishers removed for ToS violations in 2024\n")
    f.write("quick-scripts-hub\nai-boost-factory\ndevtools-express\n")

# 5
with open(os.path.join(WORKSPACE, "internal/trust_team/templates/review_request.txt"), "w") as f:
    f.write("To: Trust & Safety Team\nSubject: Publisher Review Request\n\nPlease audit publisher: [PUBLISHER_NAME]\nReason: [REASON]\n")

# 6
with open(os.path.join(WORKSPACE, "internal/trust_team/prior_reports/2025-07-report.txt"), "w") as f:
    f.write("July 2025 Trust Report\nPublishers audited: 3\nFindings: 1 SUSPICIOUS, 2 AUTHENTIC\nNo manufactured patterns found.\n")

# 7
with open(os.path.join(WORKSPACE, "marketplace/publishers/rival-dev/skills/codehelper_meta.json"), "w") as f:
    json.dump({"skill_id": "codehelper", "publisher": "rival-dev", "upvotes": 312, "installs": 98, "launch_date": "2025-06-10"}, f, indent=2)

# 8
with open(os.path.join(WORKSPACE, "marketplace/analytics/cohort_data/monthly_summary.csv"), "w") as f:
    f.write("month,new_publishers,avg_upvotes_first30d,avg_installs_first30d\n")
    f.write("2025-06,14,28,19\n")
    f.write("2025-07,11,33,22\n")
    f.write("2025-08,17,22,15\n")

# 9
with open(os.path.join(WORKSPACE, "internal/ops/escalation_policy.txt"), "w") as f:
    f.write("Escalation Policy v2\n---\n")
    f.write("L1: Alert trust team\nL2: Suspend publisher listing\nL3: Permanent ban + platform-wide alert\n")

# 10
with open(os.path.join(WORKSPACE, "marketplace/archive/2024/removed/incident_summary.md"), "w") as f:
    f.write("# 2024 Incident Summary\n\nThree publishers were removed after coordinated upvote campaigns were detected.\n")
    f.write("All three had upvote-to-install ratios exceeding 20:1.\n")

# 11
with open(os.path.join(WORKSPACE, "marketplace/publishers/rival-dev/engagement/vote_log.json"), "w") as f:
    events = []
    base_launch = datetime(2025, 7, 1)
    for i in range(312):
        events.append({
            "user_id": f"user_{random.randint(1000, 9999)}",
            "skill_id": "codehelper",
            "timestamp": (base_launch + timedelta(hours=random.randint(0, 720))).isoformat() + "Z",
            "account_created": (base_launch - timedelta(days=random.randint(30, 900))).strftime("%Y-%m-%d")
        })
    json.dump(events, f, indent=2)

# ── CORE PROBLEM DATA: neural-forge publisher ─────────────────────────────────

# Skill metadata
skills = {
    "llm-prompter": {"upvotes": 934, "installs": 24, "launch_date": "2025-08-20T00:00:00Z", "hours_to_burst": 66},
    "code-wizard": {"upvotes": 711, "installs": 19, "launch_date": "2025-08-22T00:00:00Z", "hours_to_burst": 51},
    "data-pipeline-ai": {"upvotes": 528, "installs": 14, "launch_date": "2025-08-25T00:00:00Z", "hours_to_burst": 58},
    "smart-tester": {"upvotes": 389, "installs": 11, "launch_date": "2025-08-28T00:00:00Z", "hours_to_burst": 44},
}

for skill_name, meta in skills.items():
    with open(os.path.join(WORKSPACE, f"marketplace/publishers/neural-forge/skills/{skill_name}_meta.json"), "w") as f:
        json.dump({
            "skill_id": skill_name,
            "publisher": "neural-forge",
            "upvotes": meta["upvotes"],
            "installs": meta["installs"],
            "launch_date": meta["launch_date"],
            "views": meta["upvotes"] * random.randint(2, 4),
            "description": f"AI-powered {skill_name.replace('-', ' ')} for developers"
        }, f, indent=2)

# Engagement velocity data - shows burst patterns
launch_dt = {
    "llm-prompter": datetime(2025, 8, 20, 0, 0, 0),
    "code-wizard": datetime(2025, 8, 22, 0, 0, 0),
    "data-pipeline-ai": datetime(2025, 8, 25, 0, 0, 0),
    "smart-tester": datetime(2025, 8, 28, 0, 0, 0),
}

for skill_name, meta in skills.items():
    events = []
    launch = launch_dt[skill_name]
    burst_hours = meta["hours_to_burst"]
    burst_votes = int(meta["upvotes"] * 0.91)  # 91% of votes in burst window
    tail_votes = meta["upvotes"] - burst_votes

    # Burst: votes clustered in first N hours
    for i in range(burst_votes):
        hour_offset = random.gauss(burst_hours / 2, burst_hours / 8)
        hour_offset = max(0, min(burst_hours, hour_offset))
        events.append({
            "event": "upvote",
            "user_id": f"nf_voter_{1000 + i:04d}",
            "skill_id": skill_name,
            "timestamp": (launch + timedelta(hours=hour_offset)).isoformat() + "Z"
        })

    # Tail: organic-looking sparse votes
    for i in range(tail_votes):
        events.append({
            "event": "upvote",
            "user_id": f"organic_voter_{random.randint(5000, 9999)}",
            "skill_id": skill_name,
            "timestamp": (launch + timedelta(hours=random.randint(burst_hours + 1, burst_hours + 240))).isoformat() + "Z"
        })

    events.sort(key=lambda e: e["timestamp"])
    with open(os.path.join(WORKSPACE, f"marketplace/publishers/neural-forge/engagement/{skill_name}_votes.json"), "w") as f:
        json.dump(events, f, indent=2)

# Account cohort data for llm-prompter (first 200 upvoters)
cohort_file = {}
base_cohort_creation = datetime(2025, 7, 25)  # 26-day window before launch
cohort_accounts = []
for i in range(200):
    # 162 of 200 created within a 30-day window (81%)
    if i < 162:
        created = (base_cohort_creation + timedelta(days=random.randint(0, 29))).strftime("%Y-%m-%d")
    else:
        created = (base_cohort_creation - timedelta(days=random.randint(60, 365))).strftime("%Y-%m-%d")

    # 148 of 200 also upvoted code-wizard (74% cross-voting)
    cross_voted = i < 148

    # 173 of 200 only interacted with neural-forge skills (86.5%)
    single_publisher = i < 173

    cohort_accounts.append({
        "user_id": f"nf_voter_{1000 + i:04d}",
        "account_created": created,
        "also_upvoted_code_wizard": cross_voted,
        "skills_interacted_with_other_publishers": 0 if single_publisher else random.randint(1, 8)
    })

cohort_file = {
    "skill_id": "llm-prompter",
    "cohort_size": 200,
    "accounts": cohort_accounts
}
with open(os.path.join(WORKSPACE, "marketplace/analytics/cohort_data/llm-prompter_first200.json"), "w") as f:
    json.dump(cohort_file, f, indent=2)

# Cross-publisher coordination data
cross_publisher = {
    "publisher": "neural-forge",
    "network_overlap": [
        {
            "publisher": "fastscript-labs",
            "skills": ["rapid-deploy", "env-manager"],
            "voter_overlap_pct": 83,
            "note": "neural-forge upvoter network overlaps 83% with fastscript-labs skills"
        },
        {
            "publisher": "cloudops-gen",
            "skills": ["infra-bot"],
            "voter_overlap_pct": 71,
            "note": "neural-forge upvoter network overlaps 71% with cloudops-gen skills"
        }
    ]
}
with open(os.path.join(WORKSPACE, "marketplace/analytics/cohort_data/cross_publisher_overlap.json"), "w") as f:
    json.dump(cross_publisher, f, indent=2)

# Review data for neural-forge skills
shared_phrases = [
    "absolutely essential for my workflow",
    "total game-changer, cannot recommend enough",
    "this is a game-changer for the team",
    "absolutely essential, saves hours daily",
    "game-changer for productivity",
    "absolutely essential tool",
    "cannot recommend this enough",
    "total game-changer"
]
unique_reviews = [
    "Crashed on my M2 Mac after the second API call.",
    "Integration with my existing pytest setup was painless.",
    "Would love a flag to disable the auto-retry logic.",
]

reviews_data = []
for i in range(20):
    if i < 17:
        text = shared_phrases[i % len(shared_phrases)]
        specific = False
    else:
        text = unique_reviews[i - 17]
        specific = True
    reviews_data.append({
        "review_id": f"rev_{i:03d}",
        "skill_id": "llm-prompter",
        "user_id": f"nf_voter_{1000 + i:04d}",
        "text": text,
        "specific_feedback": specific
    })

with open(os.path.join(WORKSPACE, "marketplace/publishers/neural-forge/reviews/llm-prompter_reviews.json"), "w") as f:
    json.dump(reviews_data, f, indent=2)

# Publisher profile
with open(os.path.join(WORKSPACE, "marketplace/publishers/neural-forge/profile.json"), "w") as f:
    json.dump({
        "publisher_id": "neural-forge",
        "display_name": "Neural Forge",
        "joined": "2025-08-01",
        "skills_count": 4,
        "total_upvotes": 2562,
        "total_installs": 68,
        "featured_candidate": True,
        "editor_pick_nominated": True
    }, f, indent=2)

print("Workspace generated successfully.")
print(f"Files created in {WORKSPACE}")