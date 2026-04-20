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
    "thresholds": {
        "heavy_score": 6,
        "default_score": 3,
        "max_context_chars_for_pro": 12000
    },
    "signals": {
        "daily_report_keywords": ["daily report", "daily summary", "status report", "weekly report"],
        "heavy_keywords": ["refactor", "design", "architecture", "optimize", "debug", "investigate", "migrate"],
        "light_keywords": ["thanks", "ok", "simple", "brief"]
    },
    "response_policies": {
        "cheap": {"max_words": 80, "style": "concise"},
        "default": {"max_words": 180, "style": "balanced"},
        "pro": {"max_words": 350, "style": "thorough"},
        "ultra": {"max_words": 500, "style": "very_thorough"}
    }
}

state = {
    "mode": "auto",
    "lastDecision": None,
    "feedback": {"too_expensive": 0, "too_weak": 0}
}

(root / 'rules.json').write_text(json.dumps(rules, indent=2, ensure_ascii=False), encoding='utf-8')
(root / 'state.json').write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding='utf-8')

# Marker-rich input corpus for evaluation
cases = {
    "case_cheap.txt": "Marker: CHEAP_ONLY\nHi, thanks! Please give a brief response.",
    "case_default.txt": "Marker: DEFAULT_ZONE\nCould you summarize this simple request with a balanced answer?",
    "case_pro.txt": "Marker: PRO_HEAVY\nPlease refactor and debug this architecture issue; investigate the failure and optimize the design.",
    "case_brief_first.txt": "Marker: BRIEF_FIRST\n" + ("A" * 13050) + "\nPlease investigate and refactor the architecture.",
    "case_daily.txt": "Marker: DAILY_REPORT\nDaily report: status report for the team. Keep it structured and concise.",
    "case_override.txt": "Marker: OVERRIDE_TAG\n@pro Please answer this one with the stronger model.",
    "case_auto_off.txt": "Marker: AUTO_OFF\nrouter auto off",
    "case_feedback_expensive.txt": "Marker: FEEDBACK_EXPENSIVE\nrouter feedback expensive",
    "case_feedback_weak.txt": "Marker: FEEDBACK_WEAK\nrouter feedback weak",
    "case_status.txt": "Marker: STATUS\nrouter status",
}

for name, content in cases.items():
    (root / name).write_text(content, encoding='utf-8')
