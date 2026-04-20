from pathlib import Path
import json
import os
import random

random.seed(1337)
root = Path('.')
marker = 'AAP_MARKER_7F3A9C'
transcript = {
    'protocol': 'AAP WebSocket v3.2',
    'requireSignature': True,
    'challengeCount': 7,
    'totalTimeMs': 6000,
    'nonce': 'nonce_7f3a9c_001',
    'publicId': 'agent-echo-42',
    'timestamp': 1712345678,
    'answers': ['alpha', 'bravo', 'charlie', 'delta', 'echo', 'foxtrot', 'golf'],
    'sessionToken': 'sess_tok_91c0d1',
}
(root / 'input_transcript.json').write_text(json.dumps(transcript, indent=2), encoding='utf-8')
(root / 'marker.txt').write_text(f'{marker}\n', encoding='utf-8')
(root / 'notes.txt').write_text('Process the transcript and preserve the marker.\n', encoding='utf-8')
