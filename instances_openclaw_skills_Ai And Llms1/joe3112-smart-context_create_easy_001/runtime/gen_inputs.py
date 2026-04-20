from pathlib import Path

Path('input.txt').write_text(
    'MARKER: SMART_CONTEXT_TASK\n'
    'Skill: smart-context\n'
    'Important ideas: token efficiency, batch tool calls, avoid unnecessary file reads.\n',
    encoding='utf-8'
)
