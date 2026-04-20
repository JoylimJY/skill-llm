from pathlib import Path
import json
import random

random.seed(1337)

# Marker file for evaluation
status = {
    "defaults": {"model": {"primary": "google-antigravity/claude-sonnet-4-5"}},
    "marker": "MODEL_GUARD_MARKER_7XQ2"
}
Path('status.json').write_text(json.dumps(status, indent=2), encoding='utf-8')

# Deterministic plain-text status sample
text = """openclaw models status

google-antigravity usage:
  claude-opus-4-5-thinking 18% left
  claude-sonnet-4-5 41% left
  claude-sonnet-4-5-thinking 12% left
  gemini-3-flash 100% left
  gemini-3-pro-high 100% left
  gemini-3-pro-low 100% left
  gpt-oss-120b-medium 7% left

marker: MODEL_GUARD_MARKER_7XQ2
"""
Path('status.txt').write_text(text, encoding='utf-8')

# Small helper note for the user-facing task
Path('README_INPUT.txt').write_text(
    'Use the provided status files to determine which model should be selected.\n'
    'Marker: MODEL_GUARD_MARKER_7XQ2\n',
    encoding='utf-8'
)
