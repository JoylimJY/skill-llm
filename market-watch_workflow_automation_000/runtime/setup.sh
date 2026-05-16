#!/usr/bin/env bash
set -e

SKILL="$HOME/.openclaw/skills/market-watch/scripts"

chmod +x "$SKILL/register-price-alert.py"
chmod +x "$SKILL/register-news-alert.py"
chmod +x "$SKILL/cancel-alert.py"
chmod +x "$SKILL/daemon.sh"

# Verify scripts are executable
for f in "$SKILL/register-price-alert.py" "$SKILL/register-news-alert.py" "$SKILL/cancel-alert.py" "$SKILL/daemon.sh"; do
  if [[ ! -x "$f" ]]; then
    echo "ERROR: $f is not executable"
    exit 1
  fi
done

echo "All market-watch scripts are ready."
echo "SKILL dir: $SKILL"
echo ""
echo "=== Task Context ==="
echo "Agent name: tradebot"
echo "Review /workspace/portfolio/strategy_notes.md and /workspace/rebalance_plans/q1_2026.md for trade context."