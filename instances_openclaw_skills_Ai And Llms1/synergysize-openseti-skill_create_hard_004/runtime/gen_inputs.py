import json
from pathlib import Path

# Deterministic marker data
base = Path('.')
(base / 'scan').mkdir(exist_ok=True)

records = [
    {
        'id': 'OBS-ALPHA-2049',
        'frequency_mhz': 1420.405,
        'bandwidth_hz': 7.2,
        'snr': 18.4,
        'drift_hz_s': -0.12,
        'label': 'ANOMALY_FLAGGED',
        'marker': 'OPENSETI_MARKER_ALPHA'
    },
    {
        'id': 'OBS-BETA-7711',
        'frequency_mhz': 1419.880,
        'bandwidth_hz': 22.5,
        'snr': 8.1,
        'drift_hz_s': 0.03,
        'label': 'NATURAL',
        'marker': 'OPENSETI_MARKER_BETA'
    },
    {
        'id': 'OBS-GAMMA-5520',
        'frequency_mhz': 1420.100,
        'bandwidth_hz': 9.8,
        'snr': 12.7,
        'drift_hz_s': 0.41,
        'label': 'INVESTIGATING',
        'marker': 'OPENSETI_MARKER_GAMMA'
    }
]

with open(base / 'scan' / 'work_unit.json', 'w', encoding='utf-8') as f:
    json.dump({'project': 'OpenSETI', 'records': records, 'note': 'Deterministic benchmark input'}, f, indent=2)

with open(base / 'scan' / 'marker.txt', 'w', encoding='utf-8') as f:
    f.write('BENCHMARK_MARKER=OPENSETI-2025-05\n')
    f.write('EXPECTED_TOP_ID=OBS-ALPHA-2049\n')
    f.write('EXPECTED_TOP_LABEL=ANOMALY_FLAGGED\n')
