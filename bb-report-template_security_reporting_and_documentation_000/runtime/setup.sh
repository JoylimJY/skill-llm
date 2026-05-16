#!/usr/bin/env bash
set -e

# The generate-report.py script is expected to already exist in the skill's baseDir.
# Locate it and ensure it's executable.
SCRIPT_PATH=$(find /root /home /opt /usr/local -name "generate-report.py" 2>/dev/null | head -n 1)

if [ -z "$SCRIPT_PATH" ]; then
    # Create the script since it doesn't exist yet
    SCRIPT_PATH="/usr/local/bin/generate-report.py"
    cat > "$SCRIPT_PATH" << 'EOF'
#!/usr/bin/env python3
"""generate-report.py - Bug bounty report generator."""
import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description="Generate a bug bounty report.")
    parser.add_argument("--title", required=True, help="Vulnerability title")
    parser.add_argument("--severity", required=True, choices=["critical","high","medium","low","informational"], help="Severity level")
    parser.add_argument("--platform", required=True, choices=["hackerone","bugcrowd","intigriti","other"], help="Bug bounty platform")
    parser.add_argument("--description", required=True, help="Vulnerability description")
    parser.add_argument("--steps", required=True, help="Steps to reproduce")
    parser.add_argument("--impact", required=True, help="Impact description")
    parser.add_argument("--output", default="/workspace/reports", help="Output directory")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = args.title.lower().replace(" ", "_")[:50]
    filename = output_dir / f"report_{safe_title}_{timestamp}.md"

    report = f"""# Bug Bounty Report

## Title
{args.title}

## Severity
{args.severity.upper()}

## Platform
{args.platform}

## Description
{args.description}

## Steps to Reproduce
{args.steps}

## Impact
{args.impact}

## Generated
{datetime.now().isoformat()}
"""
    filename.write_text(report)
    print(f"Report generated: {filename}")

if __name__ == "__main__":
    main()
EOF
fi

chmod +x "$SCRIPT_PATH"
echo "Script found and made executable: $SCRIPT_PATH"

# Ensure workspace reports directory is writable
mkdir -p /workspace/reports
chmod 777 /workspace/reports