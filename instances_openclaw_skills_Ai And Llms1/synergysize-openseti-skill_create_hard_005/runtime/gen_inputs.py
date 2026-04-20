import json
from pathlib import Path

# Deterministic input generation
base = Path('.')
(base / 'inputs').mkdir(exist_ok=True)

sample = {
    'sample_id': 'BL-GBT-2025-0017',
    'frequency_mhz': 1420.405,
    'bandwidth_hz': 4.8,
    'doppler_drift_hz_per_s': -0.31,
    'snr_db': 18.7,
    'rfi_match': False,
    'marker': 'OPENSETI_MARKER_ALPHA_7'
}

(base / 'inputs' / 'signal_sample.json').write_text(json.dumps(sample, indent=2), encoding='utf-8')
(base / 'inputs' / 'notes.txt').write_text(
    'Marker: OPENSETI_MARKER_ALPHA_7\nClassification hint: ANOMALY_FLAGGED\n',
    encoding='utf-8'
)
