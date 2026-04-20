from pathlib import Path
import json

root = Path('.')
report = {
    "risk_level": "DANGER",
    "blocked_items": ["sketchy-tool", "old-malware-skill"],
    "trusted_publishers": ["openclaw", "steipete", "invariantlabs-ai"],
    "warnings": [
        "curl/wget piped to shell detected",
        "external URL found: http://sketchy-domain.xyz/install",
        "macOS quarantine removal (xattr -d quarantine) detected"
    ],
    "notes": "Marker: PINCER-REPORT-9f2c1a"
}
(root / 'security_report.yaml').write_text(
    "risk_level: DANGER\nblocked_items:\n  - sketchy-tool\n  - old-malware-skill\ntrusted_publishers:\n  - openclaw\n  - steipete\n  - invariantlabs-ai\nwarnings:\n  - curl/wget piped to shell detected\n  - external URL found: http://sketchy-domain.xyz/install\n  - macOS quarantine removal (xattr -d quarantine) detected\nnotes: 'Marker: PINCER-REPORT-9f2c1a'\n",
    encoding='utf-8'
)
(root / 'reference_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
