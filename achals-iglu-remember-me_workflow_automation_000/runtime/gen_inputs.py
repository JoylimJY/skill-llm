import os
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

WORKSPACE = Path("/workspace")

# --- Directory structure ---
dirs = [
    "memory",
    "references",
    "projects/alpha",
    "projects/beta",
    "archive/2023",
    "archive/2024",
    "notes/scratch",
    "notes/meetings",
    "config",
    "logs/raw",
    "logs/processed",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "projects/alpha/brief.txt": "Project Alpha: Redesign of customer portal. Owner: Jamie.",
    "projects/beta/roadmap.txt": "Phase 1: Research\nPhase 2: Prototype\nPhase 3: Launch",
    "archive/2023/old_notes.txt": "These notes are from 2023 and no longer active.",
    "archive/2024/summary.txt": "Yearly summary placeholder. Not yet populated.",
    "notes/scratch/random_idea.txt": "What if we used async queues for the pipeline? Unvalidated.",
    "notes/meetings/2024-11-15.txt": "Discussed sprint velocity. No decisions made.",
    "config/editor_prefs.json": '{"theme": "dark", "font_size": 14}',
    "logs/raw/session_001.log": "System boot OK. No errors.",
    "logs/processed/index.txt": "Processed: 0 files.",
    "projects/alpha/status.md": "Status: In Progress",
    "notes/meetings/agenda_template.txt": "Agenda: 1. Review 2. Action items 3. AOB",
    "config/ignored_paths.txt": "/tmp\n/var\n/proc",
}
for path, content in distractor_files.items():
    (WORKSPACE / path).write_text(content)

# --- Reference templates (required by SKILL.md as existing files) ---
templates_md = """\
# Templates

## Daily Note Entry
```
[HH:MM] [TAG] description
  impact: N
  confidence: (if HYPOTHESIS) high/medium/low
```

## Long-Term Memory Entry
```
### [Category]
- [TAG] description  (added: YYYY-MM-DD)
  confidence: (if HYPOTHESIS) high/medium/low
```
"""

promotion_checklist_md = """\
# Promotion Checklist

Before promoting a daily note entry to MEMORY.md, verify:
- [ ] Repeated in 2+ sessions OR explicit user preference/boundary OR score >= 2 with repetition OR score 3 immediately
- [ ] Not a transient state
- [ ] Not raw conversation log
- [ ] Tag is not HYPOTHESIS (unless confirmed)
- [ ] If HYPOTHESIS: user must have explicitly confirmed it
"""

profile_schema_md = """\
# Profile Schema

## Sections
- Identity & Context
- Preferences
- Goals
- Active Projects
- Boundaries
- Hypotheses (unconfirmed)

Each entry:
  [TAG] description  (added: YYYY-MM-DD)
  confidence: high/medium/low  # only for HYPOTHESIS
"""

(WORKSPACE / "references/templates.md").write_text(templates_md)
(WORKSPACE / "references/promotion-checklist.md").write_text(promotion_checklist_md)
(WORKSPACE / "references/profile-schema.md").write_text(profile_schema_md)

# --- Simulated "today" anchor: 2025-03-15 ---
# Session dates used:
# Session A: 2025-01-10
# Session B: 2025-01-22
# Session C: 2025-02-05
# Session D: 2025-03-15 (today)

session_transcripts = {
    "logs/raw/session_A_2025-01-10.txt": """\
DATE: 2025-01-10
---
User: Hey, remember this — I always want code examples in Python, not pseudocode.
Assistant: Got it, Python examples from now on.
User: Also, my main project right now is called Project Lodestar — a distributed tracing library.
Assistant: Understood, Project Lodestar noted.
User: I prefer short, direct answers. No fluff.
Assistant: Noted.
User: I tend to make decisions fast when I have enough data. Don't slow me down with endless caveats.
""",
    "logs/raw/session_B_2025-01-22.txt": """\
DATE: 2025-01-22
---
User: Still working on Project Lodestar. Please remember I use pytest exclusively for testing in that project.
Assistant: Pytest noted for Lodestar.
User: One more thing: never store my company name in your memory, keep that private.
Assistant: Understood, company name will not be stored.
User: Remember I'm trying to ship Lodestar's v1 by end of Q1 2025.
""",
    "logs/raw/session_C_2025-02-05.txt": """\
DATE: 2025-02-05
---
User: Short answers again — I've mentioned this before.
Assistant: Yes, I'll keep it brief.
User: I want you to forget anything about my previous interest in Rust. I moved away from it completely.
Assistant: Done, Rust interest removed.
User: Lodestar is on hold — we've paused it. No timeline changes, just paused.
""",
    "logs/raw/session_D_2025-03-15.txt": """\
DATE: 2025-03-15
---
User: Remember this — I've started a new project called Project Helix, a real-time anomaly detection system. This is now my top priority, outcome-critical.
Assistant: Project Helix noted as top priority.
User: I still prefer Python examples.
User: Quick question — did I ever mention a preference for dark mode tools?
Assistant: I don't have that noted explicitly. Should I remember it?
User: Yes, remember that I strongly prefer dark mode in all tools.
""",
}

for path, content in session_transcripts.items():
    (WORKSPACE / path).write_text(content)

# --- Pre-existing stale hypothesis in an old daily note ---
# This hypothesis was created on 2025-01-10 and never validated
stale_hypothesis_note = """\
[09:15] HYPOTHESIS user may prefer async/await patterns over threading based on project architecture
  impact: 1
  confidence: high
[09:20] FACT user prefers Python code examples
  impact: 2
[09:22] PREFERENCE user prefers short, direct answers
  impact: 2
[09:30] FACT user is working on Project Lodestar (distributed tracing library)
  impact: 3
[09:35] PREFERENCE user makes fast decisions with sufficient data; avoid excessive caveats
  impact: 2
"""
(WORKSPACE / "memory/2025-01-10.md").write_text(stale_hypothesis_note)

# A second old hypothesis daily note with a different stale hypothesis
stale_hypothesis_note_2 = """\
[14:00] HYPOTHESIS user might prefer pair-programming style explanations given collaborative project setup
  impact: 1
  confidence: high
[14:05] PREFERENCE user uses pytest exclusively for Lodestar testing
  impact: 2
[14:10] BOUNDARY do not store company name (user explicit)
  impact: 3
[14:15] GOAL user wants to ship Lodestar v1 by end of Q1 2025
  impact: 3
"""
(WORKSPACE / "memory/2025-01-22.md").write_text(stale_hypothesis_note_2)

# --- MEMORY.md does NOT exist yet — agent must create it ---
# (intentionally absent)

print("Workspace initialized successfully.")
print("Files created:")
for f in sorted(WORKSPACE.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(WORKSPACE)}")