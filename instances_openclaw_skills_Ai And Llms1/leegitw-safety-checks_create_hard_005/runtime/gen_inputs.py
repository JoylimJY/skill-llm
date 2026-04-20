import json
import os
from pathlib import Path

root = Path('.')
(root / '.openclaw').mkdir(parents=True, exist_ok=True)
(root / '.claude').mkdir(parents=True, exist_ok=True)
(root / 'output' / 'safety').mkdir(parents=True, exist_ok=True)

config = {
    'model': {
        'expected': 'anthropic-opus-4-5-20251101',
        'strict': True,
    },
    'fallbacks': {
        'model': ['primary-model', 'fallback-model', 'cached'],
        'storage': ['primary-path', 'backup-path'],
    },
}
(root / '.openclaw' / 'safety-checks.yaml').write_text(
    'model:\n  expected: "anthropic-opus-4-5-20251101"\n  strict: true\nfallbacks:\n  model:\n    - primary-model\n    - fallback-model\n    - cached\n  storage:\n    - primary-path\n    - backup-path\n',
    encoding='utf-8',
)
(root / '.claude' / 'safety-checks.yaml').write_text(
    'model:\n  expected: "anthropic-opus-4-5-20251101"\n  strict: true\n',
    encoding='utf-8',
)
(root / '.openclaw' / 'safety-checks.lock').write_text('PID=999999\nMARKER=stale-lock\n', encoding='utf-8')
(root / '.openclaw' / 'cache').mkdir(parents=True, exist_ok=True)
(root / '.openclaw' / 'cache' / 'staleness.log').write_text(
    'api_response_auth|age_seconds=8100|status=stale\nuser_preferences|age_seconds=5400|status=stale\n',
    encoding='utf-8',
)
(root / 'output' / 'safety' / 'temp-orphan.log').write_text('orphan-temp-marker\n', encoding='utf-8')
(root / 'workspace_marker.txt').write_text(
    'MARKER: SAFETY-CHECKS-INPUT\nEXPECTED_MODEL=anthropic-opus-4-5-20251101\nCACHE_TTL_SECONDS=3600\n',
    encoding='utf-8',
)
