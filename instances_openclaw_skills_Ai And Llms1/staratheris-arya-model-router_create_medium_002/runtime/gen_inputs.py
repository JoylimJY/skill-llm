import json
import os
from pathlib import Path

BASE = Path('.')

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
        "daily_report_keywords": ["daily report", "status report", "weekly summary", "report mode"],
        "heavy_keywords": ["refactor", "optimize", "design", "architecture", "debug", "traceback"],
        "light_keywords": ["simple", "quick", "brief"]
    },
    "response_policies": {
        "cheap": {"max_words": 80, "style": "concise"},
        "default": {"max_words": 160, "style": "balanced"},
        "pro": {"max_words": 260, "style": "detailed"},
        "ultra": {"max_words": 320, "style": "very detailed"}
    }
}

state = {
    "mode": "auto",
    "lastDecision": None,
    "feedback": {"too_expensive": 0, "too_weak": 0}
}

sample_inputs = {
    "daily_report_input.txt": "Daily report: summarize today\'s blockers, wins, and next steps. Keep it structured and short.",
    "heavy_input.txt": "We need a deep refactor of the routing architecture, including debugging a traceback in the policy layer and improving long-context handling.",
    "override_input.txt": "@pro Please analyze this quickly but in depth.",
    "status_input.txt": "router status"
}

marker = "MARKER-ARYA-ROUTER-001"

(BASE / 'rules.json').write_text(json.dumps(rules, indent=2, ensure_ascii=False) + "\n", encoding='utf-8')
(BASE / 'state.json').write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding='utf-8')
(BASE / 'marker.txt').write_text(marker + "\n", encoding='utf-8')
for name, content in sample_inputs.items():
    (BASE / name).write_text(content + "\n" + marker + "\n", encoding='utf-8')
