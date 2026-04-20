from pathlib import Path

# Deterministic input generation with marker content
Path('skill_marker.txt').write_text(
    'SMART_CONTEXT_MARKER\n'
    'Token-efficient agent behavior\n'
    'Eval should look for this marker if needed\n',
    encoding='utf-8'
)
