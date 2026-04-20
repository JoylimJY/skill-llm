from pathlib import Path
import json

# Deterministic input fixture with a known marker
marker = {
    "project": "demo-token-guard",
    "session_id": "TG-DEMO-001",
    "note": "KNOWN_MARKER_TOKENGUARD_INPUT"
}
Path("input_manifest.json").write_text(json.dumps(marker, indent=2), encoding="utf-8")
