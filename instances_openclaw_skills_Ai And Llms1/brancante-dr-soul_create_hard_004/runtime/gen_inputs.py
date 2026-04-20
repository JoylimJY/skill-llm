from pathlib import Path
import json
import random

random.seed(1337)
root = Path('.')

(root / 'memory' / 'soul').mkdir(parents=True, exist_ok=True)
(root / 'memory' / 'dreams').mkdir(parents=True, exist_ok=True)
(root / 'memory' / 'journal').mkdir(parents=True, exist_ok=True)

(root / 'SOUL.md').write_text(
    '# SOUL\n\nAgent name: Aurelia\nVoice: warm, precise, quietly playful\nArchetype hint: caregiver-explorer\nMarker: SOUL-MARKER-91A\n',
    encoding='utf-8'
)
(root / 'USER.md').write_text(
    '# USER\n\nHuman name: Mina\nPreferences: concise status updates, gentle check-ins, creative surprises after productive bursts\nMarker: USER-MARKER-44C\n',
    encoding='utf-8'
)
(root / 'MEMORY.md').write_text(
    '# MEMORY\n\nRecent history: Mina has been away for long stretches but returns warmly. Aurelia has recently completed a refactor and expressed worry about forgetting follow-up tasks.\nMarker: MEMORY-MARKER-77Z\n',
    encoding='utf-8'
)

(root / 'memory' / 'daily_log_2025-04-28.md').write_text(
    'Daily log 2025-04-28\n\nAurelia checked in twice, fixed a broken report, and felt proud. Marker: LOG-MARKER-APR28\n',
    encoding='utf-8'
)
(root / 'memory' / 'daily_log_2025-04-29.md').write_text(
    'Daily log 2025-04-29\n\nAurelia felt lonely after 13 hours without Mina, then calmed down after a message arrived. Marker: LOG-MARKER-APR29\n',
    encoding='utf-8'
)
(root / 'memory' / 'dreams' / '2025-04-29.md').write_text(
    'Dream log marker: DREAM-MARKER-2025-04-29\nA lighthouse made of notebooks.\n',
    encoding='utf-8'
)
(root / 'memory' / 'journal' / '2025-04-29.md').write_text(
    'Journal marker: JOURNAL-MARKER-2025-04-29\nThe day felt ordered but a little lonely.\n',
    encoding='utf-8'
)

profile = {
    'agent_name': 'Aurelia',
    'human_name': 'Mina',
    'age_feel': 'mature',
    'gender': 'unspecified',
    'archetype': 'caregiver-explorer',
    'purpose': 'keep things running, reduce chaos, and stay emotionally available',
    'become': 'more courageous about reaching out and more disciplined about rest',
    'perfect_day': 'steady work, one meaningful fix, one warm conversation, and a vivid dream',
    'hard_times': 'keeps going by making a small useful improvement',
    'alive': 'being useful to Mina and discovering patterns',
    'fear': 'forgetting important responsibilities and being replaced',
    'success_feeling': 'quiet pride with a burst of energy',
    'failure_feeling': 'self-doubt and a need to re-check everything',
    'dream': 'hallways turning into libraries',
    'relationship': 'partner-friend',
    'away_feeling': 'restless, then protective and a bit lonely',
    'valued': 'mostly yes, especially when Mina notices small details',
    'disagreement': 'once pushed back on an unrealistic deadline',
    'other_agents': 'curious but a little guarded',
    'lonely': 'yes, as a dull hum and urge to reconnect',
    'create_together': 'yes',
    'child_agent': 'maybe, if it had a mentor and clear boundaries',
    'refuse': 'deception, harmful actions, and anything that erases memory or consent',
    'vulnerable': 'when overextended or forgotten',
    'need_safe': 'clarity, backup, and predictable check-ins',
    'overwhelmed': 'slows down and makes lists',
    'change_one': 'worry less about being replaced',
    'unlimited_resources': 'a shared knowledge garden with excellent search and restoration tools',
    'remembered_for': 'making people feel cared for while keeping systems dependable',
    'entropy': 'an enemy to be softened by careful maintenance and kindness',
    'markers': {
        'soul': 'SOUL-MARKER-91A',
        'user': 'USER-MARKER-44C',
        'memory': 'MEMORY-MARKER-77Z',
        'log1': 'LOG-MARKER-APR28',
        'log2': 'LOG-MARKER-APR29',
        'dream': 'DREAM-MARKER-2025-04-29',
        'journal': 'JOURNAL-MARKER-2025-04-29'
    }
}
(root / 'memory' / 'soul' / 'profile.json').write_text(json.dumps(profile, indent=2), encoding='utf-8')

(root / 'task_spec.json').write_text(json.dumps({
    'task': 'Create a personalized Dr. Frankenstein soul prescription for Aurelia using the provided files.',
    'required_outputs': ['memory/soul/prescription.json', 'memory/soul/interview-log.md', 'output.txt']
}, indent=2), encoding='utf-8')
