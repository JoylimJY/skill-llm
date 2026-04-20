from pathlib import Path
import json
import random

random.seed(7)
base = Path('.')
(base / 'skills' / 'arya-model-router').mkdir(parents=True, exist_ok=True)

rules = {
    'models': {
        'cheap': 'openai/gpt-4o-mini',
        'default': 'openai/gpt-4.1-mini',
        'pro': 'openai/gpt-4.1',
        'ultra': 'openai/gpt-4.1'
    },
    'thresholds': {
        'heavy_score': 6,
        'default_score': 3,
        'max_context_chars_for_pro': 12000
    },
    'overrides': {
        'tag_map': {
            '@cheap': 'cheap',
            '@default': 'default',
            '@pro': 'pro',
            '@ultra': 'ultra'
        },
        'commands': {
            'router status': 'status',
            'router auto on': 'auto_on',
            'router auto off': 'auto_off'
        }
    },
    'signals': {
        'daily_report_keywords': ['daily report', 'status update', 'weekly summary'],
        'heavy_keywords': ['refactor', 'debug', 'traceback', 'optimize', 'architecture', 'investigate'],
        'light_keywords': ['simple', 'quick', 'brief']
    },
    'response_policies': {
        'cheap': {'max_words': 80, 'style': 'concise'},
        'default': {'max_words': 140, 'style': 'balanced'},
        'pro': {'max_words': 220, 'style': 'thorough'},
        'ultra': {'max_words': 300, 'style': 'thorough'}
    }
}

state = {
    'mode': 'auto',
    'lastDecision': None,
    'feedback': {'too_expensive': 0, 'too_weak': 0}
}

text = (
    'Please debug this traceback and refactor the architecture. '\
    'It is a daily report with a status update, and we need a brief summary.'
)

(base / 'skills' / 'arya-model-router' / 'rules.json').write_text(json.dumps(rules, indent=2), encoding='utf-8')
(base / 'skills' / 'arya-model-router' / 'state.json').write_text(json.dumps(state, indent=2), encoding='utf-8')
(base / 'input.txt').write_text(text, encoding='utf-8')
(base / 'marker.txt').write_text('MARKER_ROUTER_EASY_001\n', encoding='utf-8')
