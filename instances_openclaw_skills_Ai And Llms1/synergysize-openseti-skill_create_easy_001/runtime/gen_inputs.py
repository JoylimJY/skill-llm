from pathlib import Path

# Deterministic input files with marker content
Path('workunit.json').write_text(
    '{"observation_id":"BL-2025-0001","target":"Kepler-452","marker":"OPENSETI_INPUT_MARKER","frequency_mhz":1420.405,"snr":12.3}\n',
    encoding='utf-8'
)
Path('signal_excerpt.txt').write_text(
    'Observation note: narrowband peak near 1420.405 MHz\nMarker: OPENSETI_SIGNAL_MARKER\nDrift estimate: 0.27 Hz/s\n',
    encoding='utf-8'
)
