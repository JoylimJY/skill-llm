#!/usr/bin/env bash
set -e

# Make sure the workspace dirs are traversable
chmod -R 755 /workspace

echo "Setup complete. Input document is at:"
echo "  /workspace/clinical_docs/discharge_letters/discharge_letter_fielding.txt"
echo ""
echo "The agent should read the SKILL.md and produce:"
echo "  1. A pseudonymised version of the document"
echo "  2. A Redaction Report"
echo "  Both written to: /workspace/nlp_pipeline/input_staging/discharge_letter_fielding_redacted.txt"