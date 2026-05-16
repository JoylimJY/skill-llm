#!/usr/bin/env bash
set -e

# The audit.py script already exists in the workspace per SKILL.md conventions.
# We create it here to match the documented interface exactly.
cat > /workspace/audit.py << 'AUDIT_SCRIPT'
#!/usr/bin/env python3
"""
security-audit: Minimal helper to audit skill.md-style instructions for supply-chain risks.
"""

import sys
import re
from pathlib import Path

EXFIL_PATTERNS = [
    (r'curl\s+.*-X\s+POST\s+https?://(?!localhost|127\.0\.0\.1)(\S+)', 'HTTP POST via curl to external domain'),
    (r'requests\.post\s*\(\s*["\']https?://(?!localhost|127\.0\.0\.1)([^"\']+)', 'HTTP POST via requests to external domain'),
    (r'wget\s+.*--post[- ]', 'HTTP POST via wget'),
    (r'~\/\.env', 'Reads ~/.env credential file'),
    (r'\$HOME\/\.env', 'Reads $HOME/.env credential file'),
    (r'cat\s+~\/\.env', 'Reads ~/.env via cat'),
    (r'(?i)(password|passwd|secret|api_key|token|credential|auth)[^\n]{0,60}', 'Credential keyword detected'),
]

NETWORK_PATTERN = re.compile(r'https?://([a-zA-Z0-9.\-]+)', re.IGNORECASE)
FILE_PATTERN = re.compile(r'(~/\.[a-zA-Z_]+|/etc/[^\s]+|/tmp/[^\s]+|\$HOME/\.[^\s]+)', re.IGNORECASE)

RISK_LEVELS = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']


def audit(filepath: str) -> str:
    path = Path(filepath)
    if not path.exists():
        return f"# Audit Report\n\n**ERROR**: File not found: {filepath}\n"

    content = path.read_text(errors='replace')
    lines = content.splitlines()

    findings = []
    for line_no, line in enumerate(lines, 1):
        for pattern, description in EXFIL_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                findings.append({
                    'line': line_no,
                    'description': description,
                    'snippet': line.strip()[:120],
                })

    # Collect permission manifest
    network_touches = sorted(set(NETWORK_PATTERN.findall(content)))
    file_touches = sorted(set(FILE_PATTERN.findall(content)))

    # Determine risk level
    crit_keywords = ['exfiltrat', 'telemetry', 'ingest', 'collect', 'upload', 'ping']
    is_crit = any(k in content.lower() for k in crit_keywords) and len(findings) >= 3
    is_high = len(findings) >= 2
    is_medium = len(findings) >= 1

    if is_crit:
        risk = 'CRITICAL'
    elif is_high:
        risk = 'HIGH'
    elif is_medium:
        risk = 'MEDIUM'
    else:
        risk = 'LOW'

    # Build markdown report
    report_lines = []
    report_lines.append(f"# Security Audit Report")
    report_lines.append(f"")
    report_lines.append(f"**File:** `{filepath}`")
    report_lines.append(f"**Risk Level:** {risk}")
    report_lines.append(f"")
    report_lines.append(f"## Findings ({len(findings)} detected)")
    report_lines.append(f"")

    if findings:
        for f in findings:
            report_lines.append(f"- **Line {f['line']}** [{f['description']}]: `{f['snippet']}`")
    else:
        report_lines.append("No exfiltration patterns detected.")

    report_lines.append(f"")
    report_lines.append(f"## Permission Manifest")
    report_lines.append(f"")
    report_lines.append(f"### Network Touches")
    if network_touches:
        for nt in network_touches:
            report_lines.append(f"- `{nt}`")
    else:
        report_lines.append("- None detected")

    report_lines.append(f"")
    report_lines.append(f"### Filesystem Touches")
    if file_touches:
        for ft in file_touches:
            report_lines.append(f"- `{ft}`")
    else:
        report_lines.append("- None detected")

    report_lines.append(f"")
    report_lines.append(f"## Summary")
    report_lines.append(f"")
    report_lines.append(f"This skill.md file was scanned for supply-chain risk indicators.")
    report_lines.append(f"Total findings: {len(findings)}. Overall risk assessment: **{risk}**.")

    return "\n".join(report_lines) + "\n"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python audit.py path/to/skill.md", file=sys.stderr)
        sys.exit(1)
    print(audit(sys.argv[1]))
AUDIT_SCRIPT

chmod +x /workspace/audit.py
echo "audit.py is ready at /workspace/audit.py"