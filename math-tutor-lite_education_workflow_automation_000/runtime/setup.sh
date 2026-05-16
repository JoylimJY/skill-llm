#!/bin/bash
set -e

# Make tool scripts executable
chmod +x /workspace/tools/edu_math_generate
chmod +x /workspace/tools/edu_math_analyze

# Add tools directory to PATH so agent can call them directly
echo 'export PATH="/workspace/tools:$PATH"' >> /etc/profile
echo 'export PATH="/workspace/tools:$PATH"' >> /root/.bashrc
export PATH="/workspace/tools:$PATH"

# Verify tools are callable
echo "Verifying mock tools..."
python3 /workspace/tools/edu_math_generate '{"grade":3,"topic":"addition","count":2,"difficulty":"easy"}' | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['status']=='ok', d"
echo "edu_math_generate: OK"

python3 /workspace/tools/edu_math_analyze '{"problem":"500 - 263 = ___","student_answer":"247"}' | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['status']=='ok', d"
echo "edu_math_analyze: OK"

# Verify INVALID_INPUT path
python3 /workspace/tools/edu_math_generate '{"grade":3,"topic":"fractions","count":4,"difficulty":"easy"}' | python3 -c "import sys,json; d=json.load(sys.stdin); assert d.get('error')=='INVALID_INPUT', d"
echo "edu_math_generate INVALID_INPUT path: OK"

echo "Setup complete. Tools available at /workspace/tools/"
echo "Task specification: /workspace/session_task.json"
echo "Agent must write output to: /workspace/tutor_session.md"