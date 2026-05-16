#!/bin/bash
set -e

echo "[setup] Fixing permissions on workspace..."
chmod -R 755 /workspace
chmod 644 /workspace/.github/CONTRIBUTING.md
chmod 644 /workspace/.github/PULL_REQUEST_TEMPLATE.md
chmod 644 /workspace/.github/ISSUE_TEMPLATE/bug_report.md
chmod 644 /workspace/.github/ISSUE_TEMPLATE/feature_request.md
chmod 644 /workspace/CODE_OF_CONDUCT.md
chmod 644 /workspace/docs/SECURITY.md
chmod 644 /workspace/existing_issues.json
chmod 644 /workspace/bug_to_report.json

echo "[setup] Workspace ready."
ls -la /workspace/
ls -la /workspace/.github/