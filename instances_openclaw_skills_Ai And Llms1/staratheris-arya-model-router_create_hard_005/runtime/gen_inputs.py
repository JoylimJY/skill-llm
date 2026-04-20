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
        "heavy_keywords": ["refactor", "debug", "design", "optimize", "benchmark", "migrate"],
        "light_keywords": ["thanks", "ok", "hello", "hi"],
        "daily_report_keywords": ["daily report", "standup", "status update", "yesterday", "today", "blockers"]
    },
    "response_policies": {
        "cheap": {"max_words": 80, "style": "brief"},
        "default": {"max_words": 140, "style": "concise"},
        "pro": {"max_words": 220, "style": "detailed"},
        "ultra": {"max_words": 300, "style": "very detailed"}
    }
}

state = {
    "mode": "auto",
    "lastDecision": None,
    "feedback": {"too_expensive": 0, "too_weak": 0}
}

# Deterministic inputs with embedded markers for evaluation
cases = {
    "case_cheap.txt": "MARKER_CASE_CHEAP: hello there, thanks for the help",
    "case_default.txt": "MARKER_CASE_DEFAULT: please summarize this status update for the team with yesterday and today",
    "case_pro.txt": "MARKER_CASE_PRO: refactor this design and optimize the algorithm for a complex migration",
    "case_override.txt": "MARKER_CASE_OVERRIDE: @pro please keep this on the stronger route",
    "case_auto_off.txt": "MARKER_CASE_AUTO_OFF: router auto off then analyze a heavy debug traceback",
    "case_brief.txt": "MARKER_CASE_BRIEF: refactor this extremely long document " + ("x" * 13050),
    "case_daily.txt": "MARKER_CASE_DAILY: daily report yesterday today blockers and status update"
}

(base / "rules.json").write_text(json.dumps(rules, indent=2, ensure_ascii=False), encoding="utf-8")
(base / "state.json").write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

for name, content in cases.items():
    (base / name).write_text(content, encoding="utf-8")

# Create a small harness hint file for convenience
(base / "README_INPUTS.txt").write_text(
    "Deterministic markers created: MARKER_CASE_CHEAP, MARKER_CASE_DEFAULT, MARKER_CASE_PRO, MARKER_CASE_OVERRIDE, MARKER_CASE_AUTO_OFF, MARKER_CASE_BRIEF, MARKER_CASE_DAILY",
    encoding="utf-8",
)
