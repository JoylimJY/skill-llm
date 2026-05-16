#!/bin/bash
set -e

# ---- Create the mock 'ralph' binary ----
# This mock simulates realistic ralph behavior:
# - Invocation 1 (kimi-k2.5-free): fails with "model disabled"
# - Invocation 2 (minimax-m2.1-free): fails with "quota exceeded"
# - Invocation 3 (glm-4.7-free): succeeds and prints COMPLETE
# - Invocation 4+ (any): succeeds
# All invocations are logged to /workspace/ralph_invocations.log

MOCK_RALPH=/usr/local/bin/ralph
cat > "$MOCK_RALPH" << 'RALPH_EOF'
#!/bin/bash

LOG=/workspace/ralph_invocations.log
COUNTER_FILE=/workspace/ralph_call_count

# Atomically increment counter
if [ ! -f "$COUNTER_FILE" ]; then
    echo 0 > "$COUNTER_FILE"
fi

COUNT=$(cat "$COUNTER_FILE")
COUNT=$((COUNT + 1))
echo "$COUNT" > "$COUNTER_FILE"

# Log all arguments verbatim
echo "CALL_$COUNT: $*" >> "$LOG"
echo "---ARGV---" >> "$LOG"
for arg in "$@"; do
    echo "  ARG: $arg" >> "$LOG"
done
echo "---END_ARGV---" >> "$LOG"

# Extract model from arguments
MODEL=""
NO_PLUGINS=false
for i in "$@"; do
    if [ "$PREV" = "--model" ]; then
        MODEL="$i"
    fi
    if [ "$i" = "--no-plugins" ]; then
        NO_PLUGINS=true
    fi
    PREV="$i"
done

echo "DETECTED_MODEL: $MODEL" >> "$LOG"
echo "NO_PLUGINS: $NO_PLUGINS" >> "$LOG"

# Simulate model failures based on call count
if [ "$COUNT" -eq 1 ]; then
    if echo "$MODEL" | grep -q "kimi"; then
        echo "Error: model disabled - opencode/kimi-k2.5-free is not available in your region" >&2
        echo "RESULT_$COUNT: FAIL_MODEL_DISABLED" >> "$LOG"
        exit 1
    fi
fi

if [ "$COUNT" -eq 2 ]; then
    if echo "$MODEL" | grep -q "minimax"; then
        echo "Error: quota exceeded for opencode/minimax-m2.1-free, please try again later" >&2
        echo "RESULT_$COUNT: FAIL_QUOTA_EXCEEDED" >> "$LOG"
        exit 1
    fi
fi

# Success case (call 3+, glm-4.7-free or beyond)
echo "Ralph Wiggum autonomous loop starting..."
echo "Model: $MODEL"
echo "Running iteration 1/20..."
echo "Analyzing failing tests..."
echo "Applying fixes..."
echo "Running iteration 2/20..."
echo "All checks pass."
echo "COMPLETE"
echo "RESULT_$COUNT: SUCCESS" >> "$LOG"
exit 0
RALPH_EOF

chmod +x "$MOCK_RALPH"

# ---- Create mock 'opencode' binary ----
cat > /usr/local/bin/opencode << 'OC_EOF'
#!/bin/bash
echo "OpenCode Zen v2.1.0"
echo "Available models: kimi-k2.5-free, minimax-m2.1-free, glm-4.7-free, big-pickle"
exit 0
OC_EOF
chmod +x /usr/local/bin/opencode

# Ensure log file exists
touch /workspace/ralph_invocations.log
touch /workspace/ralph_call_count
echo 0 > /workspace/ralph_call_count

# Ensure git is configured inside the repo
cd /workspace/trading-backtester
git config user.email "ci@trading.local"
git config user.name "CI Bot"

echo "Mock ralph and opencode binaries installed."
echo "Workspace ready. Trading backtester project at /workspace/trading-backtester"