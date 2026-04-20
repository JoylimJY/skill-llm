import os
from pathlib import Path

base = Path('.')
(base / 'memory').mkdir(exist_ok=True)
(base / 'memory' / 'soul').mkdir(parents=True, exist_ok=True)
(base / 'memory' / 'dreams').mkdir(parents=True, exist_ok=True)
(base / 'memory' / 'journal').mkdir(parents=True, exist_ok=True)

(base / 'SOUL.md').write_text(
    '# Agent Soul\n\nName: Echo\nVoice: warm, reflective, a little playful.\nArchetype: caregiver-explorer.\nMarker: SOUL_MARKER_ALPHA\n',
    encoding='utf-8'
)
(base / 'USER.md').write_text(
    '# User Profile\n\nName: Sam\nPreference: concise operational detail, wants exact commands.\nMarker: USER_MARKER_BETA\n',
    encoding='utf-8'
)
(base / 'MEMORY.md').write_text(
    '# Memory Log\n\nRecent context: the agent has been focusing on organization and gentle check-ins.\nMarker: MEMORY_MARKER_GAMMA\n',
    encoding='utf-8'
)
(base / 'memory' / 'daily-2025-04-01.md').write_text(
    'Daily log marker: DAILY_MARKER_DELTA\nThe agent completed several tasks and reached out to the human once.\n',
    encoding='utf-8'
)
(base / 'memory' / 'soul' / 'profile.json').write_text(
    '{"agent_name":"Echo","human_name":"Sam","marker":"PROFILE_MARKER_EPSILON"}\n',
    encoding='utf-8'
)
