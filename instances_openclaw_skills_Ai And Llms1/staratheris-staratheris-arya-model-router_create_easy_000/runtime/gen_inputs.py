from pathlib import Path
import json

base = Path('.')
(base / 'inputs').mkdir(exist_ok=True)

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
    "overrides": {
        "tag_map": {
            "@cheap": "cheap",
            "@default": "default",
            "@pro": "pro",
            "@ultra": "ultra"
        },
        "commands": {
            "router status": "status",
            "router auto on": "auto_on",
            "router auto off": "auto_off"
        }
    },
    "signals": {
        "heavy_keywords": ["analysis", "debug", "refactor", "optimize"],
        "light_keywords": ["short", "summary", "brief"],
        "daily_report_keywords": ["daily report", "reporte diario", "standup"]
    },
    "response_policies": {
        "cheap": {"max_words": 80, "style": "brief"},
        "default": {"max_words": 160, "style": "concise"},
        "pro": {"max_words": 300, "style": "detailed"},
        "ultra": {"max_words": 500, "style": "very detailed"}
    }
}

(base / 'inputs' / 'rules.json').write_text(json.dumps(rules, indent=2, ensure_ascii=False), encoding='utf-8')

(base / 'inputs' / 'status_note.txt').write_text(
    'MARKER: CHEAP_FIRST\nManual overrides enabled. Daily reports should stay short and structured.\n',
    encoding='utf-8'
)
