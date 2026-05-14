import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Build directory structure with distractor files ---
dirs = [
    "intel/raw_signals",
    "intel/processed",
    "intel/archive",
    "reports/weekly",
    "reports/daily",
    "reports/adhoc",
    "strategy/decisions",
    "strategy/competitors",
    "operations/logs",
    "operations/configs",
    "references",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- DISTRACTOR FILES (realistic but irrelevant) ---
(workspace / "operations/logs/system.log").write_text(
    "2024-01-15 09:00:01 INFO Agent started\n2024-01-15 09:01:00 INFO Scan complete\n"
)
(workspace / "operations/configs/scan_config.yaml").write_text(
    "frequency: daily\nsources:\n  - github_trending\n  - hackernews\n  - linkedin\n"
)
(workspace / "strategy/competitors/synthesia_profile.txt").write_text(
    "Synthesia: AI video avatars. Enterprise. $90M Series C (updated). Raised prices Q4.\n"
)
(workspace / "strategy/competitors/heygen_notes.txt").write_text(
    "HeyGen: Growing fast. SMB focus. New API tier launched last week.\n"
)
(workspace / "intel/archive/2024_q1_summary.txt").write_text(
    "Q1 2024: Market stable. No major disruptions. Three new entrants in consumer segment.\n"
)
(workspace / "reports/daily/2024-01-14_brief.txt").write_text(
    "Brief Jan 14:\n- Runway raised Series D\n- No competitor pricing changes detected\n- Recommendation: Monitor Runway closely\n"
)
(workspace / "reports/weekly/2024-W02_report.txt").write_text(
    "Week 2 Report: Competitive landscape unchanged. HeyGen launched mobile app.\n"
)
(workspace / "strategy/decisions/past_decisions.json").write_text(
    json.dumps([
        {"decision": "Launch enterprise tier", "date": "2024-01-10", "outcome": "pending"},
        {"decision": "Integrate ElevenLabs TTS", "date": "2024-01-05", "outcome": "approved"},
    ], indent=2)
)
(workspace / "intel/archive/competitor_funding_log.csv").write_text(
    "date,company,amount,round\n2024-01-08,Pika,35000000,Series A\n2023-12-01,Runway,141000000,Series C\n"
)
(workspace / "operations/configs/alert_thresholds.yaml").write_text(
    "tier1_response_hours: 4\ntier2_response_hours: 24\ntier3_response_hours: 168\n"
)
(workspace / "references/glossary.txt").write_text(
    "MPE: Media Production Engine\nSHX: Superhuman X\nGAZE: AI companion product\n"
)

# --- THE PROBLEM: Raw, messy intelligence signals the agent must process ---
raw_signals = [
    {
        "id": "SIG-001",
        "source": "TechCrunch scrape",
        "raw_text": "BREAKING: HeyGen just announced HeyGen Enterprise 2.0 with full script-to-video pipeline at $299/month, directly targeting corporate training market. CEO quoted: 'We're now the full production suite.' Launch is TODAY.",
        "timestamp": "2024-01-15T07:23:00Z",
        "tags": ["heygen", "competitor", "launch", "pricing"],
        "analyst_note": "seems big?? not sure how urgent"
    },
    {
        "id": "SIG-002",
        "source": "ArXiv RSS",
        "raw_text": "New paper: 'DiT-Video-3B achieves real-time 4K video synthesis at 10x lower compute cost'. Authors from Google DeepMind. Code will be released in 3 months. Could fundamentally change video generation economics.",
        "timestamp": "2024-01-15T03:10:00Z",
        "tags": ["research", "frontier_model", "video_synthesis"],
        "analyst_note": "interesting research, maybe relevant?"
    },
    {
        "id": "SIG-003",
        "source": "LinkedIn job postings aggregator",
        "raw_text": "Fortune 500 insurance company posted 8 roles for 'AI Video Content Producer' referencing 'automated compliance training video creation'. Budget keywords: 'enterprise contract', 'multi-year'. No vendor named.",
        "timestamp": "2024-01-15T06:45:00Z",
        "tags": ["customer_signal", "rfp_indicator", "enterprise"],
        "analyst_note": "potential lead"
    },
    {
        "id": "SIG-004",
        "source": "HackerNews digest",
        "raw_text": "Show HN: Open-source AI video editor reaches 12k GitHub stars in 48 hours. MIT license. Integrated with all major LLMs. Community is building plugins. Could become standard tooling.",
        "timestamp": "2024-01-14T22:00:00Z",
        "tags": ["open_source", "github_trending", "adjacent_tech"],
        "analyst_note": "cool project"
    },
    {
        "id": "SIG-005",
        "source": "EU Regulatory Monitor",
        "raw_text": "EU AI Act implementation timeline confirmed: synthetic media disclosure requirements take effect in 90 days. Companies must watermark AI-generated video. Non-compliance penalties: up to 3% global revenue.",
        "timestamp": "2024-01-15T08:00:00Z",
        "tags": ["regulatory", "EU_AI_Act", "compliance", "synthetic_media"],
        "analyst_note": "legal team should look at this"
    },
]

(workspace / "intel/raw_signals/batch_2024-01-15.json").write_text(
    json.dumps(raw_signals, indent=2)
)

# --- THE DECISION REQUEST: CEO wants evaluation of a new product feature ---
decision_request = {
    "request_id": "DEC-2024-003",
    "requested_by": "Arthur (CEO)",
    "request_date": "2024-01-15",
    "title": "Build native AI-powered video chapter editor feature into MPE",
    "description": (
        "We are evaluating whether to build a native AI video chapter/segment editor "
        "directly into the Media Production Engine. This would allow users to select any "
        "segment, regenerate it with new script, voice, or visuals without re-rendering the "
        "full video. Estimated 6-week build. Competes directly with Descript's core value prop."
    ),
    "options": [
        {
            "option_id": "A",
            "label": "Build native chapter editor (6 weeks, full team)",
            "raw_scores": {
                "revenue_impact_30d": 1,
                "revenue_impact_90d": 4,
                "competitive_advantage": 5,
                "implementation_effort": 2,
                "risk_of_disruption": 3,
                "strategic_alignment": 5
            }
        },
        {
            "option_id": "B",
            "label": "Integrate with Descript API instead (2 weeks, one engineer)",
            "raw_scores": {
                "revenue_impact_30d": 3,
                "revenue_impact_90d": 2,
                "competitive_advantage": 1,
                "implementation_effort": 4,
                "risk_of_disruption": 4,
                "strategic_alignment": 2
            }
        },
        {
            "option_id": "C",
            "label": "Defer 90 days and monitor competitive landscape",
            "raw_scores": {
                "revenue_impact_30d": 2,
                "revenue_impact_90d": 2,
                "competitive_advantage": 2,
                "implementation_effort": 5,
                "risk_of_disruption": 5,
                "strategic_alignment": 3
            }
        }
    ],
    "notes": "HeyGen's new announcement today may change our calculus."
}

(workspace / "strategy/decisions/DEC-2024-003_chapter_editor.json").write_text(
    json.dumps(decision_request, indent=2)
)

# --- A confusingly named file that looks like it might be relevant but is old/stale ---
(workspace / "intel/processed/old_signal_template.json").write_text(
    json.dumps({
        "WARNING": "THIS IS AN OLD FORMAT - DO NOT USE",
        "legacy_tier_system": {"A": "critical", "B": "moderate", "C": "low"},
        "legacy_urgency": {"A": "same-day", "B": "this-week", "C": "this-month"},
    }, indent=2)
)

# --- Another distractor: a half-filled weekly report from prior week ---
(workspace / "reports/weekly/2024-W02_DRAFT.txt").write_text(
    "DRAFT - W02 Report\n[Competitive landscape changes]: TODO\n[Technology shifts]: TODO\n[Market opportunity]: TODO\n[Recommended actions]: TODO\n\nNOTE: This was never completed.\n"
)

print("Workspace generated successfully.")
print(f"Files created: {list(workspace.rglob('*'))}")