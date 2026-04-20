from pathlib import Path

# Deterministic input generation with embedded markers
root = Path('.')
(root / 'status_snapshot.txt').write_text(
    """openclaw models status

Defaults:
  model.primary: google-antigravity/claude-sonnet-4-5

google-antigravity usage:
  claude-opus-4-5-thinking 18% left
  claude-sonnet-4-5 42% left
  claude-sonnet-4-5-thinking 63% left
  gemini-3-flash 100% left
  gemini-3-pro-high 100% left
  gemini-3-pro-low 100% left
  gpt-oss-120b-medium 5% left

MARKER_QUOTA_SNAPSHOT: ALPHA-742
MARKER_CURRENT_MODEL: google-antigravity/claude-sonnet-4-5
""",
    encoding='utf-8'
)
(root / 'report_template.md').write_text(
    """# Model Guard Report\n\nUse the snapshot to produce a concise report.\n\nMARKER_TEMPLATE: BRAVO-118\n""",
    encoding='utf-8'
)
