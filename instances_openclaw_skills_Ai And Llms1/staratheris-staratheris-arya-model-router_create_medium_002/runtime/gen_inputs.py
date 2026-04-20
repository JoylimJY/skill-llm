from pathlib import Path
import json

root = Path('.')
(root / 'skills' / 'arya-model-router').mkdir(parents=True, exist_ok=True)

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
        "heavy_keywords": ["refactor", "debug", "optimize", "architecture", "benchmark", "migration", "concurrency"],
        "light_keywords": ["summary", "brief", "quick", "simple"],
        "daily_report_keywords": ["daily report", "standup report", "reporte diario", "daily summary"]
    },
    "response_policies": {
        "cheap": {"max_words": 80, "style": "concise"},
        "default": {"max_words": 140, "style": "balanced"},
        "pro": {"max_words": 220, "style": "detailed"},
        "ultra": {"max_words": 260, "style": "detailed"}
    }
}
state = {"mode": "auto", "lastDecision": None, "feedback": {"too_expensive": 0, "too_weak": 0}}

(root / 'skills' / 'arya-model-router' / 'rules.json').write_text(json.dumps(rules, indent=2, ensure_ascii=False), encoding='utf-8')
(root / 'skills' / 'arya-model-router' / 'state.json').write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding='utf-8')
(root / 'input_main.txt').write_text(
    "MARKER:ROUTER-INPUT-ALPHA\n" \
    "Please analyze this large migration plan with concurrency issues, architecture tradeoffs, and debugging steps.\n" \
    + ("x" * 1600) + "\n",
    encoding='utf-8'
)
(root / 'input_override.txt').write_text(
    "MARKER:ROUTER-INPUT-BETA\n@pro Need a quick answer about a simple summary task.\n",
    encoding='utf-8'
)
(root / 'input_daily.txt').write_text(
    "MARKER:ROUTER-INPUT-GAMMA\nDaily report: summarize progress, blockers, and next steps in a structured format.\n",
    encoding='utf-8'
)
