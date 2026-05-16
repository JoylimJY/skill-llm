#!/bin/bash
set -e

# Make all Python scripts executable
find /workspace -name "*.py" -exec chmod +x {} \;

# Ensure data directory is writable
chmod -R 777 /workspace/interview_system/data/

# Verify key files exist
echo "[setup] Checking workspace structure..."
test -f /workspace/test_scenario.json && echo "[OK] test_scenario.json"
test -f /workspace/main_orchestrator.py && echo "[OK] main_orchestrator.py"
test -f /workspace/interview_system/tools/tool_scorer.py && echo "[OK] tool_scorer.py"
test -f /workspace/interview_system/tools/tool_resume_db.py && echo "[OK] tool_resume_db.py"
test -f /workspace/interview_system/tools/tool_summary_generator.py && echo "[OK] tool_summary_generator.py"
test -f /workspace/interview_system/tools/tool_kb_search.py && echo "[OK] tool_kb_search.py"
test -f /workspace/interview_system/data/question_bank.json && echo "[OK] question_bank.json"
test -f /workspace/interview_system/data/resume_db.json && echo "[OK] resume_db.json"

# Verify the existing DB has zhang wei profile
python3 -c "
import json
with open('/workspace/interview_system/data/resume_db.json') as f:
    db = json.load(f)
assert '张伟' in db['profiles'], 'Pre-seeded profile missing'
print('[OK] Pre-seeded profile 张伟 exists')
"

echo "[setup] Workspace ready."