from pathlib import Path
import json
import numpy as np

np.random.seed(1337)

# Create a deterministic synthetic observation file with embedded markers.
# The eval script can verify these markers and expected characteristics.
workspace = Path('.')
obs = workspace / 'observation_001.npz'
meta = workspace / 'dataset_manifest.json'

# Synthetic signal: mostly noise with one narrowband tone and a drift component.
N = 4096
t = np.arange(N)
noise = np.random.normal(0, 0.15, N)
tone = 0.8 * np.sin(2 * np.pi * 37 * t / N)
drift = 0.25 * np.sin(2 * np.pi * (7 * t / N + 0.0008 * (t ** 2) / N))
signal = noise + tone + drift

np.savez(obs, samples=signal.astype(np.float32), sample_rate=np.array([1000], dtype=np.int32), marker=np.array(['OPENSETI_MARKER_7F3A'], dtype='<U32'))
meta.write_text(json.dumps({
    'dataset_id': 'openseti-demo-001',
    'marker': 'OPENSETI_MARKER_7F3A',
    'expected_file': 'observation_001.npz',
    'notes': 'Deterministic synthetic radio observation for evaluation.'
}, indent=2))
