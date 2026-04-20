import json
from pathlib import Path

marker = {
    "project": "aap",
    "marker": "AAP_MARKER_7F3A",
    "default_challenge_count": 7,
    "total_time_ms": 6000,
    "require_signature": True,
    "signature_format": "JSON.stringify({ nonce, answers, publicId, timestamp })"
}

Path("aap_reference.json").write_text(json.dumps(marker, indent=2), encoding="utf-8")
Path("notes.txt").write_text(
    "AAP verification bundle\nMARKER=AAP_MARKER_7F3A\n",
    encoding="utf-8"
)
