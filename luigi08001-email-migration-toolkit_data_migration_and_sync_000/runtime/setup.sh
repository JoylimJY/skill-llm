#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace

# No mock servers needed for this task
echo "Workspace initialized."
echo "Migration requests raw input is at: /workspace/it_projects/email_consolidation/migration_requests_raw.json"
echo "Agent should produce: migration_assessment_report.json"