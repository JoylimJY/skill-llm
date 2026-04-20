import json
from pathlib import Path

root = Path('.')

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
            "router status": True,
            "router auto on": True,
            "router auto off": True
        }
    },
    "signals": {
        "heavy_keywords": ["analyze", "debug", "refactor", "design", "optimize"],
        "light_keywords": ["quick", "brief", "simple"],
        "daily_report_keywords": ["daily report", "status update", "standup"]
    },
    "response_policies": {
        "cheap": {"max_words": 80, "style": "concise"},
        "default": {"max_words": 140, "style": "balanced"},
        "pro": {"max_words": 220, "style": "detailed"},
        "ultra": {"max_words": 260, "style": "very detailed"}
    }
}
state = {
    "mode": "auto",
    "lastDecision": None,
    "feedback": {"too_expensive": 0, "too_weak": 0}
}

(root / "rules.json").write_text(json.dumps(rules, indent=2, ensure_ascii=False), encoding="utf-8")
(root / "state.json").write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

(root / "input_samples.json").write_text(json.dumps({
    "sample_override": "@pro please analyze this long design request",
    "sample_status": "router status",
    "sample_feedback": "router feedback expensive"
}, indent=2, ensure_ascii=False), encoding="utf-8")
