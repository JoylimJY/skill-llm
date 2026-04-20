from pathlib import Path

base = Path('.')
(base / '.openclaw').mkdir(parents=True, exist_ok=True)
(base / 'output' / 'safety').mkdir(parents=True, exist_ok=True)

config = """model:
  expected: anthropic-opus-4-5-20251101
  strict: true
fallbacks:
  model:
    - primary-model
    - fallback-model
  storage:
    - primary-path
    - backup-path
"""
(base / '.openclaw' / 'safety-checks.yaml').write_text(config, encoding='utf-8')

log = "SESSION_OK\n"
(base / 'output' / 'safety' / 'session-state.log').write_text(log, encoding='utf-8')
