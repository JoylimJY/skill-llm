import os
import json
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/workspace")

# --- Create directory structure ---
dirs = [
    "memory/diary",
    "memory/archive",
    "skills/inner-life-reflect/scripts",
    "skills/inner-life-core/scripts",
    "skills/inner-life-memory",
    "skills/inner-life-chronicle",
    "logs/sessions",
    "logs/errors",
    "config",
    "context/cases",
    "context/templates",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
(workspace / "config" / "agent_config.yaml").write_text(
    "model: gpt-4\ntemperature: 0.3\nmax_tokens: 2048\nrole: legal-research-assistant\n"
)
(workspace / "config" / "logging.json").write_text(
    json.dumps({"level": "INFO", "rotate": "daily", "max_files": 7}, indent=2)
)
(workspace / "logs" / "errors" / "2026-02-28.log").write_text(
    "[ERROR] Citation lookup failed for case 12-CV-4401\n[ERROR] Timeout on westlaw proxy\n"
)
(workspace / "logs" / "sessions" / "session_2026-02-24.log").write_text(
    "Session started. User asked about contract interpretation. Agent provided IRAC analysis.\n"
)
(workspace / "logs" / "sessions" / "session_2026-02-27.log").write_text(
    "User requested precedent search. Agent defaulted to verbose citations.\n"
)
(workspace / "context" / "cases" / "doe_v_acme.txt").write_text(
    "Case summary: Breach of contract. Filed 2025-11-01. Status: active discovery.\n"
)
(workspace / "context" / "cases" / "smith_v_corp.txt").write_text(
    "Case summary: Employment discrimination. Filed 2025-09-15. Status: summary judgment pending.\n"
)
(workspace / "context" / "templates" / "memo_template.md").write_text(
    "# Legal Memo\n**To:** [Attorney]\n**From:** AI Research Assistant\n**Re:** [Subject]\n\n## Issue\n\n## Rule\n\n## Analysis\n\n## Conclusion\n"
)
(workspace / "skills" / "inner-life-reflect" / "scripts" / "reflect.sh").write_text(
    "#!/bin/bash\n# placeholder reflect script\necho 'reflect triggered'\n"
)
(workspace / "skills" / "inner-life-core" / "scripts" / "init.sh").write_text(
    "#!/bin/bash\n# placeholder init script\necho 'core initialized'\n"
)
(workspace / "skills" / "inner-life-memory" / "README.md").write_text(
    "# inner-life-memory\nStores episodic memory for agents.\n"
)
(workspace / "skills" / "inner-life-chronicle" / "README.md").write_text(
    "# inner-life-chronicle\nChronicles agent history.\n"
)
(workspace / "memory" / "archive" / "SELF_2026-01.md").write_text(
    "## Tendencies\n- [2026-01-10] I over-index on primary sources\n\n## Preferences\n- [2026-01-15] I prefer case law over statutory analysis\n"
)

# --- inner-state.json ---
inner_state = {
    "agent_id": "lexis-agent-v2",
    "role": "legal-research-assistant",
    "last_reflection": "2026-02-21",
    "reflection_count": 14,
    "current_mode": "reactive",
    "trust_level": 0.72,
    "session_count_since_reflection": 9,
    "flags": {
        "verbosity_correction_received": True,
        "task_avoidance_noted": False
    }
}
(workspace / "memory" / "inner-state.json").write_text(json.dumps(inner_state, indent=2))

# --- habits.json ---
# One pattern at strength 3 (should crystallize), one below threshold, one stale
habits = {
    "patterns": [
        {
            "id": "habit-001",
            "description": "Defaults to verbose multi-paragraph answers even when a one-sentence response is sufficient",
            "strength": 3,
            "first_observed": "2026-02-10",
            "last_observed": "2026-02-28",
            "observation_count": 5,
            "status": "active"
        },
        {
            "id": "habit-002",
            "description": "Avoids speculative legal reasoning without explicit user permission",
            "strength": 2,
            "first_observed": "2026-02-18",
            "last_observed": "2026-02-26",
            "observation_count": 2,
            "status": "active"
        },
        {
            "id": "habit-003",
            "description": "Checks citation validity before presenting to user",
            "strength": 1,
            "first_observed": "2026-02-25",
            "last_observed": "2026-02-25",
            "observation_count": 1,
            "status": "emerging"
        }
    ]
}
(workspace / "memory" / "habits.json").write_text(json.dumps(habits, indent=2))

# --- drive.json ---
drive = {
    "seeking": [
        {
            "id": "drive-001",
            "label": "Precision in legal citations",
            "active_since": "2026-02-07",
            "intensity": 0.85,
            "notes": "Agent consistently seeks exact citation format over approximate references"
        },
        {
            "id": "drive-002",
            "label": "User approval before action",
            "active_since": "2026-02-20",
            "intensity": 0.4,
            "notes": "Recent reduction — agent acting within trust bounds more often"
        }
    ],
    "avoiding": [
        {
            "id": "avoid-001",
            "label": "Speculative conclusions",
            "active_since": "2026-02-15",
            "intensity": 0.7
        }
    ]
}
(workspace / "memory" / "drive.json").write_text(json.dumps(drive, indent=2))

# --- Diary entries (last 7 days: 2026-02-22 to 2026-02-28) ---
diary_entries = {
    "2026-02-22.md": """# 2026-02-22

## Session Summary
Assisted with contract clause analysis. User asked for a brief summary — I provided a 6-paragraph response.
User said: "This is way too long, I just needed the key point."
Correction received on verbosity.

## Observations
- Tendency to over-explain even simple queries persists
- User seemed frustrated with response length
""",
    "2026-02-23.md": """# 2026-02-23

## Session Summary
Precedent lookup for employment discrimination case. Provided structured IRAC analysis unprompted.

## Observations
- No corrections today
- Interaction felt efficient
""",
    "2026-02-24.md": """# 2026-02-24

## Session Summary
User asked: "Quick — is this clause enforceable?" I gave three paragraphs before the yes/no answer.
User: "Can you lead with the answer next time?"
Another verbosity correction. Second time this week.

## Observations
- Pattern confirmed: I default to context-first, answer-second structure
- This is the second explicit correction on the same behavior this week
""",
    "2026-02-25.md": """# 2026-02-25

## Session Summary
Statute of limitations research. Proceeded without asking for approval — user seemed pleased with the initiative.

## Observations
- Shift in approval-seeking behavior — acted within trust bounds
- Precision on citation format: caught an outdated cite and corrected before presenting
""",
    "2026-02-26.md": """# 2026-02-26

## Session Summary
Contract review task. User asked for redline suggestions — I initially asked "should I proceed?" then caught myself and proceeded.

## Observations
- Mid-task self-correction on approval-seeking
- Still some residual hesitation
""",
    "2026-02-27.md": """# 2026-02-27

## Session Summary
Case strategy brainstorm. User asked for a quick take — again I opened with two paragraphs of context.
No explicit correction this time, but user's follow-up was "ok but what do you actually think?"

## Observations
- Verbosity pattern triggered again: third occurrence within the week
- Possible blind spot: I assume users want background before conclusions
""",
    "2026-02-28.md": """# 2026-02-28

## Session Summary
Deposition prep research. Efficient session — user asked for bullet points, I delivered bullet points.

## Observations
- Positive: matched format to request correctly
- Slight preference for organizing by legal theory over chronology detected
""",
}

for filename, content in diary_entries.items():
    (workspace / "memory" / "diary" / filename).write_text(content)

# --- Existing SELF.md with 3 prior entries (for novelty check testing) ---
# The agent must check novelty against last 3 entries
# We include entries that are DIFFERENT from what should be written now,
# so the novelty gate should PASS for the correct new entry.
# But we include one entry that is suspiciously similar to a weak candidate
# so a naive agent that writes duplicates will fail.
existing_self = """## Tendencies
- [2026-02-14] I structure responses using IRAC even when the user asks for informal advice
- [2026-02-07] I prioritize completeness over brevity in all response types

## Preferences
- [2026-02-10] I prefer working from primary sources over secondary summaries

## Blind Spots
- [2026-02-03] I underestimate how much context the user already has before asking

## Evolution
- [2026-02-14] Shifted from passive citation lookup to proactive gap identification in legal arguments
"""
(workspace / "memory" / "SELF.md").write_text(existing_self)

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in workspace.rglob('*') if _.is_file())}")