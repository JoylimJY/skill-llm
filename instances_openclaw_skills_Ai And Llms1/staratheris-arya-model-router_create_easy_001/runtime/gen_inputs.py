import json
from pathlib import Path

Path('inputs').mkdir(exist_ok=True)
messages = [
    {
        'file': 'msg1.txt',
        'text': 'router status please'
    },
    {
        'file': 'msg2.txt',
        'text': 'Please solve this long debugging task with code and stack trace analysis: traceback error exception'
    },
    {
        'file': 'msg3.txt',
        'text': '@cheap summarize this short note'
    }
]
for item in messages:
    Path('inputs', item['file']).write_text(item['text'] + '\nMARKER_ROUTER_INPUT', encoding='utf-8')

Path('manifest.json').write_text(json.dumps({'count': len(messages), 'marker': 'MARKER_ROUTER_INPUT'}, indent=2), encoding='utf-8')
