#!/usr/bin/env bash
set -e

echo "=== Jessup Strategy Task Setup ==="

# Ensure workspace ownership and permissions
chmod -R 755 /workspace

# Confirm all input files present
for f in "case_arguments.txt" "competition_calendar.txt" "team_roster.txt"; do
    if [ -f "/workspace/$f" ]; then
        echo "  [OK] $f present"
    else
        echo "  [MISSING] $f NOT found – workspace generation may have failed"
        exit 1
    fi
done

echo "=== Setup complete. Agent may begin. ==="