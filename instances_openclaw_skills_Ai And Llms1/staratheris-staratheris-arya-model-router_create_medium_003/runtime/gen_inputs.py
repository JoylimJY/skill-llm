import json
from pathlib import Path

base = Path('.')

rules = {
    "models": {
        "cheap": "openai/gpt-4o-mini",
        "default": "openai/gpt-4.1-mini",
        "pro": "openai/gpt-4.1",
        "ultra": "openai/gpt-4.1"
    },
    "thresholds": {
        "heavy_score": 6,
        "default_score": 3,
        "max_context_chars_for_pro": 12000
    },
    "response_policies": {
        "cheap": {"max_words": 80, "style": "brief"},
        "default": {"max_words": 140, "style": "concise"},
        "pro": {"max_words": 220, "style": "thorough"},
        "ultra": {"max_words": 260, "style": "deep"}
    },
    "overrides": {
        "tag_map": {
            "@cheap": "cheap",
            "@default": "default",
            "@pro": "pro",
            "@ultra": "ultra"
        },
        "commands": {
            "router status": True,
            "router auto on": True,
            "router auto off": True,
            "router report": True
        }
    },
    "signals": {
        "heavy_keywords": ["refactor", "debug", "optimize", "architecture", "migration", "performance"],
        "light_keywords": ["hello", "thanks", "summary", "quick"],
        "daily_report_keywords": ["daily report", "standup", "eod", "status update"]
    }
}

state = {
    "mode": "auto",
    "lastDecision": {"level": "default", "model": "openai/gpt-4.1-mini", "score": 3, "actions": ["stay_main"]},
    "feedback": {"too_expensive": 2, "too_weak": 1}
}

Path('rules.json').write_text(json.dumps(rules, indent=2, ensure_ascii=False), encoding='utf-8')
Path('state.json').write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding='utf-8')

# Marker inputs for evaluation
Path('input_normal.txt').write_text(
    'MARKER_NORMAL\nPlease summarize the meeting notes quickly and keep it short.',
    encoding='utf-8'
)
Path('input_daily.txt').write_text(
    'MARKER_DAILY\nDaily report: shipped two fixes, reviewed one PR, and answered support questions.',
    encoding='utf-8'
)
Path('input_heavy.txt').write_text(
    'MARKER_HEAVY\nThis request needs architecture refactor, debugging, performance optimization, and migration planning. ' + ('x' * 13000),
    encoding='utf-8'
)
Path('input_feedback.txt').write_text('MARKER_FEEDBACK\nrouter feedback expensive', encoding='utf-8')
