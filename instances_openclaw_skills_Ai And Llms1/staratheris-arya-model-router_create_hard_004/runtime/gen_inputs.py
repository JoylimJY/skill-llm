from pathlib import Path
import json
import random

random.seed(1337)
base = Path('.')
(base / 'skills' / 'arya-model-router').mkdir(parents=True, exist_ok=True)

rules = {
    "models": {
        "cheap": "openai/gpt-4o-mini",
        "default": "openai/gpt-4.1-mini",
        "pro": "openai/gpt-4.1",
        "ultra": "openai/gpt-4.1"
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
            "router auto off": True
        }
    },
    "thresholds": {
        "heavy_score": 6,
        "default_score": 3,
        "max_context_chars_for_pro": 12000
    },
    "signals": {
        "daily_report_keywords": ["daily report", "status update", "yesterday", "today", "blockers"],
        "heavy_keywords": ["refactor", "benchmark", "optimize", "debug", "traceback", "migrate"],
        "light_keywords": ["hi", "hello", "thanks", "summary"]
    },
    "response_policies": {
        "cheap": {"max_words": 120, "style": "concise"},
        "default": {"max_words": 220, "style": "balanced"},
        "pro": {"max_words": 400, "style": "detailed"},
        "ultra": {"max_words": 600, "style": "deep"}
    }
}

state = {
    "mode": "auto",
    "lastDecision": None,
    "feedback": {"too_expensive": 1, "too_weak": 2}
}

(base / 'skills' / 'arya-model-router' / 'rules.json').write_text(json.dumps(rules, indent=2, ensure_ascii=False), encoding='utf-8')
(base / 'skills' / 'arya-model-router' / 'state.json').write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding='utf-8')

# Marker inputs for evaluation
(base / 'marker_input_cheap.txt').write_text('MARKER-CHEAP hello quick question', encoding='utf-8')
(base / 'marker_input_daily.txt').write_text('MARKER-DAILY daily report today blockers summary', encoding='utf-8')
(base / 'marker_input_heavy.txt').write_text('MARKER-HEAVY refactor optimize benchmark debug traceback migrate ' + ('x' * 6000), encoding='utf-8')
(base / 'marker_input_ultra.txt').write_text('MARKER-ULTRA @ultra please handle this', encoding='utf-8')
