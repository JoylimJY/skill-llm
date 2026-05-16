#!/bin/bash
set -e

echo "=== Setting up affiliate link management sandbox ==="

# Ensure workspace permissions
chmod -R 755 /workspace

# Verify key input files exist
echo "Verifying input files..."
test -f /workspace/affiliate/links/link_database.json && echo "  [OK] link_database.json"
test -f /workspace/content/drafts/x_posts/draft_claude_review.txt && echo "  [OK] draft_claude_review.txt"
test -f /workspace/content/drafts/x_posts/draft_tools_combo.txt && echo "  [OK] draft_tools_combo.txt"
test -f /workspace/content/drafts/x_posts/draft_udemy_promo.txt && echo "  [OK] draft_udemy_promo.txt"
test -f /workspace/content/drafts/note_articles/draft_ai_productivity.txt && echo "  [OK] draft_ai_productivity.txt"

echo ""
echo "Workspace tree:"
find /workspace -type f | sort

echo ""
echo "=== Setup complete. Agent may begin. ==="