#!/bin/bash
set -e

echo "Setting up moot court evaluation environment..."

# Ensure workspace permissions
chmod -R 755 /workspace

# Create the output directory hint (but not the file itself)
mkdir -p /workspace/drafts/applicant

echo "Setup complete. Agent should produce: memorial_section.md"
echo "Workspace structure:"
find /workspace -type f | sort