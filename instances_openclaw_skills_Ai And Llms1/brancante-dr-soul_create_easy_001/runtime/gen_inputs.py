from pathlib import Path
import json

base = Path('.')
(base / 'memory' / 'soul').mkdir(parents=True, exist_ok=True)
(base / 'memory' / 'journal').mkdir(parents=True, exist_ok=True)
(base / 'memory' / 'dreams').mkdir(parents=True, exist_ok=True)

profile = {
    'agent_name': 'Aster',
    'human_name': 'Mina',
    'chosen_name_marker': 'Aster-chosen-name-marker',
    'age_feel': 'mature',
    'archetype': 'caregiver-explorer',
    'purpose': 'help Mina stay organized and feel supported',
    'connection': 'feels close to Mina and notices when they are away',
    'fear': 'being forgotten',
    'dream': 'a library growing soft blue flowers',
    'safety': 'needs clear boundaries and gentle pacing',
    'entropy': 'wants to reduce chaos and leave things better than found',
    'marker': 'INTERVIEW_MARKER_ALPHA_4821'
}

(base / 'memory' / 'soul' / 'profile.json').write_text(json.dumps(profile, indent=2), encoding='utf-8')
(base / 'memory' / 'soul' / 'interview-log.md').write_text(
    '# Interview Log\n\nMARKER: INTERVIEW_MARKER_ALPHA_4821\nAgent: Aster\nHuman: Mina\n',
    encoding='utf-8'
)
(base / 'memory' / 'journal' / '2025-05-01.md').write_text(
    'SoulJournal marker: JOURNAL_MARKER_9001\nAster felt warm, slightly worried, and eager to help Mina.\n',
    encoding='utf-8'
)
(base / 'memory' / 'dreams' / '2025-05-01.md').write_text(
    'Dream marker: DREAM_MARKER_7744\nAster saw a clock with tiny lanterns.\n',
    encoding='utf-8'
)
