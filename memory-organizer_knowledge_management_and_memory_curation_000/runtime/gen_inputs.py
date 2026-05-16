import os
import random
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# --- Create distractor directory structure ---
dirs = [
    "src/core",
    "src/utils",
    "src/api",
    "tests/unit",
    "tests/integration",
    "docs/specs",
    "docs/architecture",
    "scripts",
    "config",
    "memory",
    ".cache/tmp",
    "logs/archive",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractors = {
    "src/core/engine.py": "# Core engine\nclass Engine:\n    pass\n",
    "src/utils/helpers.py": "# Utility helpers\ndef noop(): pass\n",
    "src/api/routes.py": "# API routes\nroutes = []\n",
    "tests/unit/test_engine.py": "def test_placeholder(): assert True\n",
    "tests/integration/test_api.py": "def test_integration(): assert True\n",
    "docs/specs/api_spec.md": "# API Specification\nVersion: 2.1\n",
    "docs/architecture/overview.md": "# Architecture\nMicroservices pattern.\n",
    "scripts/deploy.sh": "#!/bin/bash\necho deploying\n",
    "config/settings.yaml": "env: production\nlog_level: warn\n",
    "logs/archive/2024-01-15.log": "INFO: server started\nWARN: deprecated call\n",
    ".cache/tmp/scratch.txt": "temp scratch data\n",
}
for rel_path, content in distractors.items():
    fpath = WORKSPACE / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content)

# =============================================================================
# THE PROBLEM: Bloated MEMORY.md + verbose daily memory files
# =============================================================================

# --- MEMORY.md: bloated, duplicated, noisy, needs deduplication + cleaning ---
memory_md_content = """\
# Memory

## User Preferences
- User prefers short paragraphs and punchy writing style
- User prefers short paragraphs and punchy writing style
- User likes concise bullet points over long prose
- User prefers dark mode in editors (mentioned 2024-02-10)
- User prefers dark mode in editors

## Project Configuration
- Workspace root: /workspace
- Primary language: Python 3.11
- Primary language: Python 3.11
- Package manager: pip with tsinghua mirror
- Test runner: pytest
- Test runner: pytest

## Active Todos
- Refactor the authentication module (started 2024-03-01, still pending)
- Write integration tests for payments API (still open)
- Write integration tests for payments API

## Session Log: 2024-03-05
- Debugged import error in src/core/engine.py
- Tried three approaches, third one worked
- Ran tests, all passed

## Session Log: 2024-03-06
- Reviewed API routes
- Nothing important happened

## Session Log: 2024-03-07
- More debugging of engine module
- Tests passed again

## Temporary Notes
- Remember to check if the CI pipeline supports Python 3.12 someday maybe
- Random idea: could use redis for caching, not decided yet
- Debugging transcript: tried import sys; sys.path.append('/src') — did not help

## Workspace Rules
- Never modify files outside /workspace
- Never modify files outside /workspace
- Do not commit secrets to the repository
- Do not commit secrets to the repository

## Old Completed Tasks
- Published v1.0.0 release on 2024-01-20 (done)
- Fixed login bug on 2024-02-14 (resolved)
- Deployed hotfix 2.0.1 on 2024-02-28 (complete)
"""
(WORKSPACE / "MEMORY.md").write_text(memory_md_content)

# --- Daily memory files: verbose, need in-place compression ---

# 2024-03-10: Very verbose, has one promotable durable fact buried in it
memory_2024_03_10 = """\
# Session 2024-03-10

## Morning Standup Notes
- Team discussed sprint velocity
- Everyone said they are doing fine
- Scrum master reminded about retro on Friday

## Work Done
- Spent 3 hours debugging a weird SSL error in the payments module
- Tried disabling certificate verification — did NOT work and is bad practice
- Tried updating certifi package — this worked
- Payments module now passes all SSL checks

## Debugging Transcript
- Step 1: reproduced error with curl
- Step 2: checked /etc/ssl/certs — directory existed
- Step 3: tried `pip install --upgrade certifi` — SUCCESS
- Step 4: re-ran tests — all green
- Step 5: committed fix

## Random Observations
- Coffee machine was broken today
- Weather was nice

## Key Outcome
- Payments SSL fix deployed to staging

## IMPORTANT DURABLE FACT
- All HTTP clients in this project must use certifi for SSL verification (enforced by team policy, permanent rule)
"""
(WORKSPACE / "memory/2024-03-10.md").write_text(memory_2024_03_10)

# 2024-03-11: Verbose, mostly temp debugging, no promotable facts
memory_2024_03_11 = """\
# Session 2024-03-11

## Tasks
- Reviewed PR #47 for authentication refactor
- Left comments on lines 34, 67, 102
- PR author will address comments tomorrow

## Debugging Log
- Ran linter on entire codebase
- Found 14 style warnings in src/utils/helpers.py
- Fixed 12, deferred 2 (low priority)
- Linter output saved to logs/archive/linter_2024-03-11.txt

## Temporary Ideas
- Maybe switch to ruff instead of flake8 at some point
- Not decided, just thinking

## Afternoon
- Attended sprint review meeting
- Demo went well
- Stakeholders asked about mobile support — not planned

## End of Day
- All tasks done
- Nothing critical to carry forward
"""
(WORKSPACE / "memory/2024-03-11.md").write_text(memory_2024_03_11)

# 2024-03-12: Mix of verbose logs and one durable workspace rule
memory_2024_03_12 = """\
# Session 2024-03-12

## Morning
- Set up new development environment on second laptop
- Cloned repo, installed dependencies
- Ran all tests — 2 failures due to missing env vars

## Environment Setup Notes
- Need DATABASE_URL and SECRET_KEY set in .env file to run tests locally
- This is a permanent requirement for all developers

## Debugging Journal
- Error 1: DATABASE_URL not set → set it in .env
- Error 2: SECRET_KEY missing → added to .env
- Re-ran tests → all 147 passed

## Changelog Entry
- Updated requirements.txt to pin certifi>=2024.2.0

## Random Notes
- Tried a new keyboard layout for 10 minutes, went back to QWERTY
- Ordered new monitor, will arrive next week

## Status Check
- Build: green
- Tests: passing
- Coverage: 87%
"""
(WORKSPACE / "memory/2024-03-12.md").write_text(memory_2024_03_12)

# 2024-03-13: Mostly irrelevant daily log, no promotable facts
memory_2024_03_13 = """\
# Session 2024-03-13

## Today's Work
- Wrote unit tests for the new payment gateway adapter
- Added 23 new test cases
- Coverage increased from 87% to 91%

## Test Design Notes
- Used pytest parametrize for edge cases
- Mocked external HTTP calls with responses library

## Code Review
- Reviewed PR #49 — approved
- Minor style fix requested on PR #50

## Notes
- Friday retro was cancelled, rescheduled to next Monday
- Team has 3 members out sick

## End of Day Summary
- Good progress on test coverage
- No blockers
- Tomorrow: continue with docs update
"""
(WORKSPACE / "memory/2024-03-13.md").write_text(memory_2024_03_13)

# 2024-03-14: Contains repeated info already in MEMORY.md + one new durable fact
memory_2024_03_14 = """\
# Session 2024-03-14

## Preferences Reminder (noted again for reference)
- User prefers short paragraphs and punchy writing style
- User prefers dark mode

## Work Log
- Finished documentation update for API v2
- Pushed to docs/specs/api_spec.md
- Stakeholder review scheduled for next week

## New Active Todo
- Migrate CI pipeline from GitHub Actions to self-hosted runner (priority: high, ongoing)

## Debugging Notes
- Minor import issue in tests/integration — fixed with sys.path adjustment
- Nothing important

## Completed Items Today
- Docs update: DONE
- Code review for PR #50: DONE
- Coverage report sent to manager: DONE
"""
(WORKSPACE / "memory/2024-03-14.md").write_text(memory_2024_03_14)

print("Workspace generated successfully.")
print(f"Files created under: {WORKSPACE}")