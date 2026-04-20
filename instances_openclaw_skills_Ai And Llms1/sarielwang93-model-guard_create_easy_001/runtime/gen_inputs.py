from pathlib import Path
import json

# Deterministic marker content for evaluation
workspace = Path('.')

status_text = """openclaw models status

Defaults:
  model.primary: google-antigravity/claude-sonnet-4-5

google-antigravity usage:
  claude-opus-4-5-thinking 18% left
  claude-sonnet-4-5 42% left
  claude-sonnet-4-5-thinking 35% left
  gemini-3-flash 100% left
  gemini-3-pro-high 100% left
  gemini-3-pro-low 100% left
  gpt-oss-120b-medium 12% left

MARKER_STATUS_ALPHA_2025
"""

status_json = {
    "defaults": {"model": {"primary": "google-antigravity/claude-sonnet-4-5"}},
    "marker": "MARKER_JSON_BETA_2025"
}

(workspace / 'status.txt').write_text(status_text, encoding='utf-8')
(workspace / 'status.json').write_text(json.dumps(status_json, indent=2), encoding='utf-8')

# Lightweight guidance file for the task
(workspace / 'README_TASK.txt').write_text(
    "Use the quota status files to update the default model selection behavior.\n"
    "Expected marker strings: MARKER_STATUS_ALPHA_2025 and MARKER_JSON_BETA_2025.\n",
    encoding='utf-8'
)
