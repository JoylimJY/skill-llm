import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Create the OKR work manager directory structure ──────────────────────────
okr_dir = workspace / ".okr-work-manager"
for sub in ["daily", "plans", "weekly", "monthly", "quarterly", "yearly"]:
    (okr_dir / sub).mkdir(parents=True, exist_ok=True)

# ── Distractor files to simulate a real messy project ────────────────────────
distractor_dirs = [
    workspace / "src" / "api",
    workspace / "src" / "models",
    workspace / "src" / "utils",
    workspace / "tests" / "unit",
    workspace / "tests" / "integration",
    workspace / "docs" / "specs",
    workspace / "docs" / "meetings",
    workspace / "scripts",
    workspace / "config",
    workspace / ".github" / "workflows",
]
for d in distractor_dirs:
    d.mkdir(parents=True, exist_ok=True)

distractor_files = {
    workspace / "src" / "api" / "router.py": "# FastAPI router for biomarker endpoints\nfrom fastapi import APIRouter\nrouter = APIRouter()\n",
    workspace / "src" / "models" / "biomarker.py": "# Biomarker data model\nclass Biomarker:\n    def __init__(self, id, name, value): pass\n",
    workspace / "src" / "utils" / "parser.py": "# Data parser utilities\ndef parse_csv(path): pass\n",
    workspace / "tests" / "unit" / "test_biomarker.py": "import pytest\ndef test_create_biomarker(): pass\n",
    workspace / "tests" / "integration" / "test_api.py": "import pytest\ndef test_endpoint(): pass\n",
    workspace / "docs" / "specs" / "api_spec.md": "# API Specification\n## Endpoints\n- GET /biomarkers\n- POST /biomarkers\n",
    workspace / "docs" / "meetings" / "q4_kickoff.txt": "Q4 2025 Kickoff Meeting Notes\n2025-10-01\nAttendees: Alice, Bob, Charlie\nGoals: Launch biomarker platform v2, onboard 3 pilot customers, improve pipeline reliability\n",
    workspace / "scripts" / "deploy.sh": "#!/bin/bash\necho 'Deploying biomarker platform...'\n",
    workspace / "config" / "app.yaml": "app:\n  name: biomarker-platform\n  version: 2.0.0\n  env: production\n",
    workspace / ".github" / "workflows" / "ci.yml": "name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n",
    workspace / "src" / "api" / "auth.py": "# Auth middleware\ndef verify_token(token): return True\n",
    workspace / "docs" / "meetings" / "q4_review_draft.txt": "DRAFT - Q4 Review (incomplete)\nDo NOT use this file - unofficial notes only\nPlatform launch: partial\nCustomer onboarding: 2/3\n",
    workspace / "config" / "logging.yaml": "logging:\n  level: INFO\n  handlers:\n    - console\n    - file\n",
}
for path, content in distractor_files.items():
    path.write_text(content)

# ── WRONG/INCOMPLETE okr_config stub (agent must replace/fix it) ──────────────
bad_okr_config = {
    "version": "1.0",
    "objectives": [
        {
            "id": "OKR-Q4-1",  # WRONG format — should be q_2025-Q4_1
            "title": "Launch biomarker platform v2",
            "key_results": [
                {"id": "KR1", "description": "Complete core API", "target_hours": 200}
            ]
        }
    ]
}
(okr_dir / "okr_config.json").write_text(json.dumps(bad_okr_config, indent=2, ensure_ascii=False))

# ── WRONG okr_progress stub ───────────────────────────────────────────────────
bad_okr_progress = {
    "last_updated": "2025-09-30",
    "objectives": {}
}
(okr_dir / "okr_progress.json").write_text(json.dumps(bad_okr_progress, indent=2, ensure_ascii=False))

# ── Pre-existing daily logs for October 2025 (correctly formatted) ────────────
oct_logs = {
    "2025-10-06": {
        "date": "2025-10-06",
        "entries": [
            {"description": "API endpoint design for biomarker ingestion", "hours": 3.0, "tags": ["api", "architecture"], "okr_id": "q_2025-Q4_1"},
            {"description": "Team sync on platform v2 roadmap", "hours": 1.0, "tags": ["meeting", "planning"], "okr_id": "q_2025-Q4_1"}
        ],
        "total_hours": 4.0
    },
    "2025-10-08": {
        "date": "2025-10-08",
        "entries": [
            {"description": "Core database schema design", "hours": 4.0, "tags": ["database", "architecture"], "okr_id": "q_2025-Q4_1"},
            {"description": "Customer outreach emails for pilot program", "hours": 1.5, "tags": ["sales", "customer"], "okr_id": "q_2025-Q4_2"}
        ],
        "total_hours": 5.5
    },
    "2025-10-14": {
        "date": "2025-10-14",
        "entries": [
            {"description": "Biomarker data pipeline v1 implementation", "hours": 6.0, "tags": ["backend", "pipeline"], "okr_id": "q_2025-Q4_1"},
        ],
        "total_hours": 6.0
    },
    "2025-10-20": {
        "date": "2025-10-20",
        "entries": [
            {"description": "Pilot customer demo setup", "hours": 2.0, "tags": ["customer", "demo"], "okr_id": "q_2025-Q4_2"},
            {"description": "API reliability improvements", "hours": 3.5, "tags": ["backend", "reliability"], "okr_id": "q_2025-Q4_3"}
        ],
        "total_hours": 5.5
    },
    "2025-10-27": {
        "date": "2025-10-27",
        "entries": [
            {"description": "Pipeline stress testing", "hours": 4.0, "tags": ["testing", "pipeline"], "okr_id": "q_2025-Q4_3"},
            {"description": "Customer #1 onboarding call", "hours": 1.5, "tags": ["customer", "onboarding"], "okr_id": "q_2025-Q4_2"}
        ],
        "total_hours": 5.5
    },
}
for date, log in oct_logs.items():
    (okr_dir / "daily" / f"{date}.json").write_text(json.dumps(log, indent=2, ensure_ascii=False))

# ── Pre-existing daily logs for November 2025 ─────────────────────────────────
nov_logs = {
    "2025-11-03": {
        "date": "2025-11-03",
        "entries": [
            {"description": "Platform v2 frontend integration", "hours": 5.0, "tags": ["frontend", "integration"], "okr_id": "q_2025-Q4_1"},
        ],
        "total_hours": 5.0
    },
    "2025-11-10": {
        "date": "2025-11-10",
        "entries": [
            {"description": "Customer #2 onboarding session", "hours": 2.0, "tags": ["customer", "onboarding"], "okr_id": "q_2025-Q4_2"},
            {"description": "Monitoring dashboard setup", "hours": 3.0, "tags": ["devops", "reliability"], "okr_id": "q_2025-Q4_3"}
        ],
        "total_hours": 5.0
    },
    "2025-11-17": {
        "date": "2025-11-17",
        "entries": [
            {"description": "Platform v2 beta release preparation", "hours": 6.0, "tags": ["release", "backend"], "okr_id": "q_2025-Q4_1"},
        ],
        "total_hours": 6.0
    },
    "2025-11-24": {
        "date": "2025-11-24",
        "entries": [
            {"description": "Bug fixes from beta testing", "hours": 4.0, "tags": ["bugfix", "backend"], "okr_id": "q_2025-Q4_1"},
            {"description": "Pipeline uptime improvement - auto-recovery", "hours": 3.0, "tags": ["reliability", "pipeline"], "okr_id": "q_2025-Q4_3"}
        ],
        "total_hours": 7.0
    },
}
for date, log in nov_logs.items():
    (okr_dir / "daily" / f"{date}.json").write_text(json.dumps(log, indent=2, ensure_ascii=False))

# ── Pre-existing October monthly report ──────────────────────────────────────
oct_monthly = {
    "period": "2025-10",
    "generated_at": "2025-10-28T20:00:00+08:00",
    "total_hours": 26.5,
    "okr_alignment": {
        "q_2025-Q4_1": {"hours": 13.0, "alignment_score": 0.49},
        "q_2025-Q4_2": {"hours": 3.5, "alignment_score": 0.13},
        "q_2025-Q4_3": {"hours": 7.5, "alignment_score": 0.28}
    },
    "unaligned_hours": 2.5,
    "progress_warnings": ["q_2025-Q4_2 behind schedule - only 3.5h logged"],
    "next_month_suggestions": ["Accelerate customer onboarding for q_2025-Q4_2", "Maintain pipeline reliability work"]
}
(okr_dir / "monthly" / "2025-10-report.json").write_text(json.dumps(oct_monthly, indent=2, ensure_ascii=False))

# ── Pre-existing November monthly report ─────────────────────────────────────
nov_monthly = {
    "period": "2025-11",
    "generated_at": "2025-11-28T20:00:00+08:00",
    "total_hours": 23.0,
    "okr_alignment": {
        "q_2025-Q4_1": {"hours": 11.0, "alignment_score": 0.48},
        "q_2025-Q4_2": {"hours": 2.0, "alignment_score": 0.09},
        "q_2025-Q4_3": {"hours": 6.0, "alignment_score": 0.26}
    },
    "unaligned_hours": 4.0,
    "progress_warnings": ["q_2025-Q4_2 critically behind - only 1 customer onboarded so far"],
    "next_month_suggestions": ["Final push on customer #3 onboarding", "Prepare for platform v2 full launch"]
}
(okr_dir / "monthly" / "2025-11-report.json").write_text(json.dumps(nov_monthly, indent=2, ensure_ascii=False))

# ── RAW UNSTRUCTURED December 2025 work notes (messy, for agent to parse) ──────
dec_raw_notes = """
=== December 2025 Work Notes (RAW - needs to be converted to logs) ===

Dec 1 (Mon):
- Spent most of the day (~5h) finalizing platform v2 launch checklist. Tags: release, backend. Related to platform launch OKR.
- 1.5h customer success call with pilot customer #2. Tags: customer, onboarding. Related to customer onboarding OKR.

Dec 3 (Wed):
- Platform v2 official launch! Deployment and monitoring: 6h. Tags: release, devops. Related to platform launch OKR.
- Wrote internal launch announcement: 0.5h. Tags: documentation.

Dec 8 (Mon):
- Post-launch bug triage and hotfixes: 4h. Tags: bugfix, backend. Related to platform launch OKR.
- Started onboarding customer #3 (biotech startup): 2h. Tags: customer, onboarding. Related to customer onboarding OKR.

Dec 10 (Wed):
- Customer #3 onboarding session 2: 2.5h. Tags: customer, onboarding. Related to customer onboarding OKR.
- Pipeline reliability audit: 3h. Tags: reliability, pipeline. Related to pipeline reliability OKR.

Dec 15 (Mon):
- Completed customer #3 onboarding - all 3 pilot customers now active! 1.5h wrap-up. Tags: customer, onboarding. Related to customer onboarding OKR.
- Q4 retrospective prep: 2h. Tags: planning, review.

Dec 17 (Wed):
- Pipeline uptime reached 99.5% target - final validation and documentation: 3h. Tags: reliability, pipeline. Related to pipeline reliability OKR.
- Performance optimization for biomarker query: 2.5h. Tags: backend, performance. Related to platform launch OKR.
"""
(workspace / "docs" / "meetings" / "december_2025_raw_notes.txt").write_text(dec_raw_notes)

# ── Skill reference directory (simulate the skill being present) ───────────────
skill_dir = workspace / "skills" / "okr-work-manager" / "references"
skill_dir.mkdir(parents=True, exist_ok=True)

# data-schema.md with complete schema definitions
data_schema_content = """# OKR Work Manager — Data Schema Reference

## Daily Log (`daily/YYYY-MM-DD.json`)

```json
{
  "date": "YYYY-MM-DD",
  "entries": [
    {
      "description": "string",
      "hours": 0.0,
      "tags": ["string"],
      "okr_id": "q_YYYY-QN_N | y_YYYY_N | null"
    }
  ],
  "total_hours": 0.0
}
```

## OKR Config (`okr_config.json`)

```json
{
  "version": "2.0",
  "objectives": [
    {
      "id": "q_YYYY-QN_N",
      "type": "quarterly",
      "quarter": "YYYY-QN",
      "title": "string",
      "target_hours": 0,
      "key_results": [
        {
          "id": "q_YYYY-QN_N_kr1",
          "description": "string",
          "target": "string",
          "target_hours": 0,
          "current_hours": 0,
          "progress": 0.0,
          "status": "on_track | behind | ahead | completed"
        }
      ]
    }
  ]
}
```

## OKR Progress (`okr_progress.json`)

```json
{
  "last_updated": "YYYY-MM-DD",
  "objectives": {
    "q_YYYY-QN_N": {
      "title": "string",
      "target_hours": 0,
      "logged_hours": 0.0,
      "progress": 0.0,
      "key_results": {
        "q_YYYY-QN_N_kr1": {
          "description": "string",
          "target_hours": 0,
          "logged_hours": 0.0,
          "progress": 0.0,
          "status": "on_track | behind | ahead | completed"
        }
      }
    }
  }
}
```

## Monthly Report (`monthly/YYYY-MM-report.json`)

```json
{
  "period": "YYYY-MM",
  "generated_at": "ISO8601",
  "total_hours": 0.0,
  "okr_alignment": {
    "q_YYYY-QN_N": {
      "hours": 0.0,
      "alignment_score": 0.0
    }
  },
  "unaligned_hours": 0.0,
  "progress_warnings": ["string"],
  "next_month_suggestions": ["string"]
}
```

## Quarterly Report (`quarterly/YYYY-QN-report.json`)

```json
{
  "period": "YYYY-QN",
  "generated_at": "ISO8601",
  "total_hours": 0.0,
  "monthly_breakdown": {
    "YYYY-MM": 0.0
  },
  "okr_completion": {
    "q_YYYY-QN_N": {
      "title": "string",
      "target_hours": 0,
      "logged_hours": 0.0,
      "completion_rate": 0.0,
      "status": "completed | on_track | behind | at_risk",
      "kr_progress": {
        "q_YYYY-QN_N_kr1": {
          "description": "string",
          "progress": 0.0,
          "status": "string"
        }
      }
    }
  },
  "next_quarter_okr_suggestions": [
    {
      "title": "string",
      "rationale": "string",
      "suggested_hours": 0
    }
  ],
  "summary": "string"
}
```

## Week Plan (`plans/YYYY-Www.json`)

```json
{
  "week": "YYYY-Www",
  "goals": ["string"],
  "okr_focus": ["q_YYYY-QN_N"],
  "planned_hours": 0.0
}
```

## Weekly Report (`weekly/YYYY-Www-report.json`)

```json
{
  "week": "YYYY-Www",
  "generated_at": "ISO8601",
  "total_hours": 0.0,
  "okr_contributions": {
    "q_YYYY-QN_N": 0.0
  },
  "plan_completion": 0.0,
  "highlights": ["string"]
}
```
"""
(skill_dir / "data-schema.md").write_text(data_schema_content)

troubleshooting_content = """# Troubleshooting

## Common Issues

### OKR ID Format Errors
OKR IDs must strictly follow the pattern:
- Quarterly: `q_{year}-Q{quarter_number}_{index}` e.g. `q_2025-Q4_1`
- Yearly: `y_{year}_{index}` e.g. `y_2026_1`
- KR IDs extend the OKR ID: `q_2025-Q4_1_kr1`, `q_2025-Q4_1_kr2`

Using formats like `Q4-OKR-1`, `okr_q4_1`, or `2025Q4_obj1` will break cross-file linkage.

### Missing Quarter in Quarterly Report
The quarterly report filename must be `YYYY-QN-report.json` e.g. `2025-Q4-report.json`.

### Week Numbering
Always use ISO 8601: weeks start Monday, W01 contains January 4th.
Use Python: `date.isocalendar()` or `date.strftime('%G-W%V')`.
"""
(skill_dir / "troubleshooting.md").write_text(troubleshooting_content)

# ── Additional distractor: old Python-version data files (wrong format) ────────
old_data_dir = workspace / ".okr-work-manager-v1-backup"
old_data_dir.mkdir(parents=True, exist_ok=True)
old_config = {"okrs": [{"name": "Q4 Goal", "progress": 0.3}]}
(old_data_dir / "okr_data.json").write_text(json.dumps(old_config, indent=2))
(old_data_dir / "MIGRATION_NOTE.txt").write_text("This is the old v1 data. Do not use. Migrated to v2 format.\n")

print("Workspace setup complete.")
print(f"Created: {len(list(workspace.rglob('*')))} files/dirs total")