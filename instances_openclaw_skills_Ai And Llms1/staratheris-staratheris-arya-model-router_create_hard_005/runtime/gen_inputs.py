from pathlib import Path

base = Path('.')
skill_dir = base / 'skills' / 'arya-model-router'
skill_dir.mkdir(parents=True, exist_ok=True)

# Marker file for eval verification
(base / 'marker_input.txt').write_text(
    """Project markers:
MARKER_ALPHA: Alpha path is active.
MARKER_BETA: Beta path is present.
MARKER_GAMMA: Gamma path is present.
DAILY_REPORT: This should trigger daily report handling.
Extra text is included to make the context large enough for briefing behavior.
""",
    encoding='utf-8'
)

# Large deterministic context sample
sample_lines = []
for i in range(1, 41):
    sample_lines.append(f"Section {i}: deterministic content block {i % 7}.")
    if i in (5, 13, 27):
        sample_lines.append("MARKER_ALPHA appears here with repeated context.")
    if i in (9, 21, 33):
        sample_lines.append("MARKER_BETA appears here with repeated context.")
    if i in (11, 19, 37):
        sample_lines.append("MARKER_GAMMA appears here with repeated context.")
    if i in (8, 24, 40):
        sample_lines.append("DAILY_REPORT: structured summary requested.")
(base / 'sample_context.txt').write_text("\n".join(sample_lines) + "\n", encoding='utf-8')

# Router state seed
(skill_dir / 'state.json').write_text(
    '{"mode":"auto","lastDecision":null,"feedback":{"too_expensive":0,"too_weak":0}}\n',
    encoding='utf-8'
)

# Rules file with deterministic, compact routing cues
(skill_dir / 'rules.json').write_text(
    '{\n'
    '  "models": {"cheap": "openai/gpt-4o-mini", "default": "openai/gpt-4.1-mini", "pro": "openai/gpt-4.1", "ultra": "openai/gpt-4.1"},\n'
    '  "thresholds": {"heavy_score": 6, "default_score": 3, "max_context_chars_for_pro": 12000},\n'
    '  "overrides": {"tag_map": {"@cheap": "cheap", "@default": "default", "@pro": "pro", "@ultra": "ultra"}, "commands": {"router status": true, "router auto on": true, "router auto off": true}},\n'
    '  "signals": {"daily_report_keywords": ["daily_report", "daily report", "reporte diario"], "heavy_keywords": ["analyze", "analysis", "debug", "traceback", "optimize", "refactor", "summarize", "compress"], "light_keywords": ["hi", "hello", "thanks", "ok"]},\n'
    '  "response_policies": {"cheap": {"max_words": 60, "style": "brief"}, "default": {"max_words": 120, "style": "balanced"}, "pro": {"max_words": 180, "style": "detailed"}, "ultra": {"max_words": 220, "style": "very detailed"}}\n'
    '}\n',
    encoding='utf-8'
)
