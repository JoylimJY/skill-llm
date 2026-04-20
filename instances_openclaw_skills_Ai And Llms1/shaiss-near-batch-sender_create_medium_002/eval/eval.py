import json
import os
import re
import sys
from pathlib import Path


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def normalize(s):
    try:
        return re.sub(r'[^a-z0-9]+', '', s.lower())
    except Exception:
        return ''


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    expected_files = ["send_batch.json", "nft_batch.json", "claim_batch.json"]
    marker = "NEAR_BATCH_MARKER_2025_04"

    for fname in expected_files:
        path = workspace / fname
        try:
            exists = path.exists()
            if not exists:
                checks.append({"name": f"{fname} exists", "passed": False, "detail": "Missing file"})
                continue
            text = path.read_text(encoding='utf-8')
            has_marker = marker.lower() in text.lower()
            checks.append({"name": f"{fname} marker", "passed": bool(has_marker), "detail": "Marker present" if has_marker else "Marker missing"})
        except Exception as e:
            checks.append({"name": f"{fname} readable", "passed": False, "detail": f"Error reading file: {e}"})

    # Parse and validate send batch
    try:
        data = json.loads((workspace / "send_batch.json").read_text(encoding='utf-8'))
        recipients = data.get('recipients', []) if isinstance(data, dict) else []
        ok = isinstance(recipients, list) and len(recipients) >= 3
        checks.append({"name": "send batch structure", "passed": ok, "detail": f"Recipients found: {len(recipients) if isinstance(recipients, list) else 'invalid'}"})
    except Exception as e:
        checks.append({"name": "send batch structure", "passed": False, "detail": f"Parse error: {e}"})

    # Parse and validate NFT batch
    try:
        data = json.loads((workspace / "nft_batch.json").read_text(encoding='utf-8'))
        transfers = data.get('transfers', []) if isinstance(data, dict) else []
        ok = isinstance(transfers, list) and len(transfers) >= 2
        checks.append({"name": "nft batch structure", "passed": ok, "detail": f"Transfers found: {len(transfers) if isinstance(transfers, list) else 'invalid'}"})
    except Exception as e:
        checks.append({"name": "nft batch structure", "passed": False, "detail": f"Parse error: {e}"})

    # Parse and validate claim batch
    try:
        data = json.loads((workspace / "claim_batch.json").read_text(encoding='utf-8'))
        claims = data.get('claims', []) if isinstance(data, dict) else []
        ok = isinstance(claims, list) and len(claims) >= 2
        checks.append({"name": "claim batch structure", "passed": ok, "detail": f"Claims found: {len(claims) if isinstance(claims, list) else 'invalid'}"})
    except Exception as e:
        checks.append({"name": "claim batch structure", "passed": False, "detail": f"Parse error: {e}"})

    total = len(checks)
    passed = sum(1 for c in checks if c.get('passed'))
    result = {
        "passed": passed == total and total > 0,
        "score": (passed / total) if total else 0.0,
        "checks": checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
