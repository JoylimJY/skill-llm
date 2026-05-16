#!/bin/bash
set -e

echo "=== Setting up CCA Domain 1 Evaluation Sandbox ==="

cd /workspace

# Ensure Python path is set
export PYTHONPATH=/workspace:$PYTHONPATH

# Make test runner executable
chmod +x /workspace/refund_system/tests/test_system.py 2>/dev/null || true

# Verify the broken implementations are in place (sanity check)
echo "=== Verifying initial broken state ==="
python3 -c "
import sys
sys.path.insert(0, '/workspace')
from refund_system.hooks.tool_hooks import PostToolUseHook, PreconditionHook
hook = PostToolUseHook()
result = hook('get_customer', {'customer': {'created_at': 1704067200}})
val = result['customer']['created_at']
if isinstance(val, int):
    print('CONFIRMED: PostToolUseHook is broken (timestamp not normalized) - agent must fix this')
else:
    print(f'WARNING: PostToolUseHook may already be fixed: {val}')

pre = PreconditionHook()
try:
    pre.on_before_tool_call('process_refund', {'customer_id': 'C-1001', 'amount': 100, 'order_id': 'ORD-5001', 'reason': 'test'})
    print('CONFIRMED: PreconditionHook is broken (does not block) - agent must fix this')
except Exception as e:
    print(f'WARNING: PreconditionHook may already be fixed: {e}')
" 2>/dev/null || echo "Initial state check completed"

echo "=== Sandbox ready ==="
echo "Agent task: Fix the broken implementations in /workspace/refund_system/"
echo "Target: Make all tests in refund_system/tests/test_system.py pass"