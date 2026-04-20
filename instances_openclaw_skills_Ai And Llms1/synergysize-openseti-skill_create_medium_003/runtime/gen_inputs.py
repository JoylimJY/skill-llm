from pathlib import Path
import json
import numpy as np

np.random.seed(1337)

# Deterministic synthetic scan input with embedded marker content
payload = {
    "observation_id": "BL-GBT-2025-0001",
    "source": "Breakthrough Listen Open Data Archive",
    "classification_hint": "ANOMALY_FLAGGED",
    "marker_token": "OPENSETI_MARKER_7F3A",
    "snr": 18.42,
    "doppler_drift_hz_s": -0.83,
    "bandwidth_hz": 3.7,
}

Path("scan_input.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

# Secondary file with a deterministic text marker for evaluation robustness
Path("readme_note.txt").write_text(
    "Marker: OPENSETI_MARKER_7F3A\nClassification hint: ANOMALY_FLAGGED\n",
    encoding="utf-8",
)
