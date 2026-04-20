import os
from pathlib import Path

# Deterministic input generation with marker content
base = Path('.')
(base / 'input_marker.txt').write_text(
    'ANTI-REGRESSION BENCHMARK\nMARKER: ARK-5429\nUse this marker for verification.\n',
    encoding='utf-8'
)
(base / 'reference_notes.txt').write_text(
    '1. Do not ask permission for obvious actions.\n'
    '2. Use tools instead of talking about tools.\n'
    '3. Search first when you need memory.\n'
    '4. Fix broken things yourself.\n'
    '5. Do useful work when idle.\n',
    encoding='utf-8'
)
