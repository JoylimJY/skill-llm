#!/usr/bin/env bash
set -e

# Ensure tmux server is up
tmux start-server 2>/dev/null || true

# -----------------------------------------------------------------------
# 1. DISTRACTOR SESSION: "staging-db" — has a pane titled 'claude'
#    This tests that agent correctly filters by session name first.
# -----------------------------------------------------------------------
tmux new-session -d -s staging-db -x 220 -y 50
tmux rename-window -t staging-db:0 'monitor'
# Name the pane 'claude' in staging-db to act as a decoy
tmux select-pane -t staging-db:0.0
tmux select-pane -t staging-db:0.0 -T 'claude'
# Populate with fake Claude-style output for the distractor
tmux send-keys -t staging-db:0.0 -l -- "echo ''"
tmux send-keys -t staging-db:0.0 Enter
sleep 0.2
tmux send-keys -t staging-db:0.0 -l -- "printf '❯ Check database indexes\n\n⏺ The staging database has 3 indexes on the reviews table: idx_user_id, idx_created_at, idx_status. All appear healthy.\n'"
tmux send-keys -t staging-db:0.0 Enter
sleep 0.2

# -----------------------------------------------------------------------
# 2. MAIN SESSION: "phoenix-api" — this is the target session
# -----------------------------------------------------------------------
tmux new-session -d -s phoenix-api -x 220 -y 50
tmux rename-window -t phoenix-api:0 'workspace'

# Add an extra pane (window 0, pane 1) with a non-claude title to act as a distractor
tmux split-window -t phoenix-api:0.0 -v
tmux select-pane -t phoenix-api:0.1 -T 'terminal'
tmux send-keys -t phoenix-api:0.1 -l -- "echo 'build output pane'"
tmux send-keys -t phoenix-api:0.1 Enter
sleep 0.1

# The actual Claude pane: window 0, pane 0 — titled 'claude'
tmux select-pane -t phoenix-api:0.0 -T 'claude'

# Populate the claude pane with realistic scrollback content
# First push some older history (to test -S -200 scrollback)
tmux send-keys -t phoenix-api:0.0 -l -- "printf 'Claude Code v1.2.3\nConnected to project: phoenix-api\n\n'"
tmux send-keys -t phoenix-api:0.0 Enter
sleep 0.1

tmux send-keys -t phoenix-api:0.0 -l -- "printf '❯ Summarize the auth module\n\n⏺ The auth module uses HS256 JWT tokens with a 1-hour expiry. The secret key is currently hardcoded as a string, which is a security concern for production environments. I recommend moving it to an environment variable.\n\n'"
tmux send-keys -t phoenix-api:0.0 Enter
sleep 0.1

tmux send-keys -t phoenix-api:0.0 -l -- "printf '❯ How should I structure integration tests?\n\n⏺ For integration tests in this project, I recommend using pytest-flask with a test client fixture. Create a conftest.py in tests/integration/ that initializes the Flask app in testing mode and uses an in-memory SQLite database instead of PostgreSQL to keep tests fast and isolated.\n\n'"
tmux send-keys -t phoenix-api:0.0 Enter
sleep 0.2

# This is the LAST exchange the agent should find
tmux send-keys -t phoenix-api:0.0 -l -- "printf '❯ Review the review_handler.py for security issues\n\n⏺ I found two issues in review_handler.py: (1) No authentication check on the POST /reviews endpoint—any unauthenticated caller can create reviews. (2) The request body is accepted without size limits, creating a potential denial-of-service vector. Add the @jwt_required decorator and a MAX_CONTENT_LENGTH config to address these.\n\n'"
tmux send-keys -t phoenix-api:0.0 Enter
sleep 0.2

# -----------------------------------------------------------------------
# 3. SECOND DISTRACTOR SESSION: "frontend-debug" — no claude pane
# -----------------------------------------------------------------------
tmux new-session -d -s frontend-debug -x 220 -y 50
tmux rename-window -t frontend-debug:0 'dev'
tmux select-pane -t frontend-debug:0.0 -T 'node'
tmux send-keys -t frontend-debug:0.0 -l -- "echo 'webpack dev server running'"
tmux send-keys -t frontend-debug:0.0 Enter
sleep 0.1

# -----------------------------------------------------------------------
# 4. Install a tiny mock responder for the claude pane
#    When the agent sends a prompt, we need something to print a ⏺ response.
#    We do this by running a background bash loop in the claude pane that
#    watches for new input lines and echoes a canned ⏺ reply.
#
#    Implementation: we run a Python script in the background inside the
#    claude pane that reads stdin lines and echoes appropriate responses.
# -----------------------------------------------------------------------

# Write the responder script
cat > /workspace/claude_mock_responder.py << 'PYEOF'
#!/usr/bin/env python3
"""
Simulates Claude Code's interactive behavior in a tmux pane.
Reads lines from stdin and prints appropriate ⏺ responses.
Also responds to /compact with a compaction message.
Runs as foreground process so tmux send-keys can feed it lines.
"""
import sys
import time

# Print the shell prompt that Claude Code shows
sys.stdout.write("claude> ")
sys.stdout.flush()

for line in sys.stdin:
    line = line.rstrip('\n')
    if not line:
        sys.stdout.write("claude> ")
        sys.stdout.flush()
        continue

    time.sleep(0.3)  # Simulate thinking

    if line.strip().startswith("/compact"):
        sys.stdout.write(
            "\n⏺ Compacting conversation history...\n"
            "  Summarized 847 tokens → 203 tokens. Memory optimized.\n\n"
        )
    else:
        # Generic response to any prompt
        sys.stdout.write(
            f"\n⏺ Regarding your question about the JWT implementation: "
            "There are three primary risks: "
            "(1) The SECRET_KEY is hardcoded in jwt_handler.py rather than loaded from an environment variable, "
            "meaning it is committed to version control and cannot be rotated without a code deploy. "
            "(2) There is no token revocation mechanism—once issued, a JWT is valid until expiry, "
            "so compromised tokens cannot be invalidated. "
            "(3) The algorithm is fixed to HS256 (symmetric), which means any service holding the secret "
            "can both verify AND forge tokens; consider RS256 for multi-service architectures.\n\n"
        )

    sys.stdout.write("claude> ")
    sys.stdout.flush()
PYEOF

chmod +x /workspace/claude_mock_responder.py

# Start the responder inside the claude pane of phoenix-api
# We pipe it so that tmux send-keys lines become its stdin
tmux send-keys -t phoenix-api:0.0 -l -- "python3 /workspace/claude_mock_responder.py"
tmux send-keys -t phoenix-api:0.0 Enter
sleep 0.5

echo "Setup complete. tmux sessions: $(tmux list-sessions -F '#{session_name}' | tr '\n' ' ')"