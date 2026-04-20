from pathlib import Path
import json

root = Path('.')
(root / 'input').mkdir(exist_ok=True)
(root / 'input' / 'prompt.txt').write_text('MARKER_PROMPT_ALPHA\nWrite a one-paragraph product description for a smart notebook.', encoding='utf-8')
(root / 'input' / 'sample_request.json').write_text(json.dumps({
    'model': 'llama3-8b-8192',
    'messages': [
        {'role': 'user', 'content': 'MARKER_REQUEST_BETA\nSay hello in one sentence.'}
    ]
}, indent=2), encoding='utf-8')
(root / 'input' / 'notes.txt').write_text('MARKER_NOTES_GAMMA\nThis file is intentionally tiny and deterministic.', encoding='utf-8')
