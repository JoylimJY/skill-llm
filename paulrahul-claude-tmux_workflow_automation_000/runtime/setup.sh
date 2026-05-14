#!/bin/bash
set -e

WORKSPACE="/workspace"
FAKE_CLAUDE="$WORKSPACE/fake_claude.sh"
chmod +x "$FAKE_CLAUDE"

# Start a tmux server (detached, no session yet)
tmux start-server 2>/dev/null || true

# ---- Create 'payments' session ----
# Create the session with a first window, name the pane 'claude'
tmux new-session -d -s payments -x 220 -y 50
# Rename the pane to 'claude' using select-pane -T
tmux select-pane -t payments:0.0 -T claude
# Start the fake claude simulator in this pane for the payments session
tmux send-keys -t payments:0.0 -l -- "$FAKE_CLAUDE payments"
tmux send-keys -t payments:0.0 Enter

# Add a second pane in a different window that is NOT named claude (distractor)
tmux new-window -t payments
tmux select-pane -t payments:1.0 -T shell
tmux send-keys -t payments:1.0 -l -- "bash"
tmux send-keys -t payments:1.0 Enter

# ---- Create 'fraud' session ----
tmux new-session -d -s fraud -x 220 -y 50
# Also add a distractor window first to make it harder
tmux new-window -t fraud
tmux select-pane -t fraud:1.0 -T shell
tmux send-keys -t fraud:1.0 -l -- "bash"
tmux send-keys -t fraud:1.0 Enter
# Go back to window 0 and set it up as the claude pane
tmux select-pane -t fraud:0.0 -T claude
tmux send-keys -t fraud:0.0 -l -- "$FAKE_CLAUDE fraud"
tmux send-keys -t fraud:0.0 Enter

# Allow fake_claude processes to initialize and print their history
sleep 3

# Verify sessions are alive
echo "=== Active tmux sessions ==="
tmux list-sessions

echo "=== Pane listing ==="
tmux list-panes -a -F '#{session_name}:#{window_index}.#{pane_index} title=#{pane_title}'

echo "Setup complete. Two tmux sessions ('payments', 'fraud') are running."
echo "Each has a pane titled 'claude' running the fake AI assistant simulator."