from pathlib import Path

# Deterministic input generation with marker content
Path('input_context.txt').write_text(
    'Audit context for agent ethos.\nMarker: ETHOS_AUDIT_001\nHigh-stakes decisions should be handled carefully.\n',
    encoding='utf-8'
)
