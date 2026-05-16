#!/usr/bin/env python3
import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# --- Create distractor directory structure ---
dirs = [
    "src/app",
    "src/components",
    "src/styles",
    "src/utils",
    "public/images",
    "config",
    "scripts",
    "docs",
    "tmp",
    "tests",
    "marketing/drafts",
    "marketing/assets",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---

# 1. Messy legacy site config (not valid JSON)
(workspace / "config" / "site.conf").write_text(
    """# Legacy site config - DO NOT USE
site_name = MyBizAnalytics
stack = unknown
pages = home, about, contact
last_updated = 2022-01-15
status = DEPRECATED
"""
)

# 2. Broken JSON attempt
(workspace / "config" / "site_spec_draft.json").write_text(
    """{
  "stack": "React",
  "pages": [
    {"path": "/", "title": "Home"
  ],
  "components": ["Header", "Footer"],
  "copy_style": "casual",
  // missing required fields
}
"""
)

# 3. Outdated marketing notes
(workspace / "marketing" / "drafts" / "notes.txt").write_text(
    """Marketing notes (outdated):
- Target: Japanese small businesses
- Product: Instagram analytics
- Tone: unknown, needs decision
- SEO keywords: TBD
- Risks: not analyzed
- Status: NEEDS AI REVIEW
"""
)

# 4. Messy React component (distractor)
(workspace / "src" / "components" / "Hero.tsx").write_text(
    """import React from 'react';

export default function Hero() {
  return (
    <div style={{background:'red',padding:'50px'}}>
      <h1>Welcome to our service!!!</h1>
      <p>We do things. Buy now. Click here. Subscribe. Limited offer. Fast. Cheap. Good.</p>
      <button onClick={()=>alert('clicked')}>BUY NOW CLICK HERE</button>
    </div>
  );
}
"""
)

# 5. Package.json distractor
(workspace / "config" / "package_old.json").write_text(
    json.dumps({
        "name": "mybiz-analytics",
        "version": "0.1.0",
        "dependencies": {
            "react": "17.0.0",
            "next": "12.0.0"
        }
    }, indent=2)
)

# 6. Styles distractor
(workspace / "src" / "styles" / "globals.css").write_text(
    """/* Placeholder styles */
body { margin: 0; font-family: sans-serif; }
h1 { color: purple; }
.hero { background: #ff0000; padding: 2rem; }
"""
)

# 7. Utility file distractor
(workspace / "src" / "utils" / "analytics.ts").write_text(
    """// Analytics utility - stub
export function trackEvent(name: string) {
  // TODO: implement
  console.log('event:', name);
}
"""
)

# 8. Test file distractor
(workspace / "tests" / "hero.test.ts").write_text(
    """// Tests for Hero component
describe('Hero', () => {
  it('renders', () => {
    // TODO
  });
});
"""
)

# 9. Docs distractor
(workspace / "docs" / "architecture.md").write_text(
    """# Architecture (Draft)

## Stack decision: PENDING AI REVIEW

Options:
- Next.js
- Astro
- SvelteKit

No decision made yet. Needs structured spec.
"""
)

# 10. Public asset placeholder
(workspace / "public" / "images" / ".gitkeep").write_text("")

# 11. Another config distractor
(workspace / "config" / "deploy.yml").write_text(
    """# Deployment config
environment: staging
region: ap-northeast-1
build_command: npm run build
# TODO: finalize after site spec is ready
"""
)

# 12. Stale temp file
(workspace / "tmp" / "old_gemini_output.txt").write_text(
    """This is an old, stale output from a previous run.
Do not use this. It has wrong keys and malformed data.
stack: rails
pages: just one
"""
)

# --- The actual scripts directory with helper scripts ---
# scripts/gemini_json.sh - the bundled helper the SKILL.md references
# This will be created properly in setup_script as an executable
# Here we create a stub so the agent can see it exists
(workspace / "scripts" / "gemini_json.sh").write_text(
    """#!/bin/bash
# gemini_json.sh - Send a prompt to Gemini and enforce JSON-only output.
# Usage: ./scripts/gemini_json.sh "<your prompt describing JSON schema>" <output_file>
# The script wraps the prompt with JSON enforcement instructions and captures output.
# Arguments:
#   $1 - The content prompt (what JSON to generate, schema description)
#   $2 - Output file path to save the JSON result
set -e
PROMPT="$1"
OUTFILE="$2"
if [ -z "$PROMPT" ] || [ -z "$OUTFILE" ]; then
  echo "Usage: $0 '<prompt>' <output_file>" >&2
  exit 1
fi
gemini -p "Return only valid JSON. No markdown. No explanation. ${PROMPT}" > "$OUTFILE"
echo "JSON saved to $OUTFILE" >&2
"""
)

# scripts/gemini_review.sh - the other bundled helper
(workspace / "scripts" / "gemini_review.sh").write_text(
    """#!/bin/bash
# gemini_review.sh - Send a file to Gemini for review with a fixed prompt wrapper.
# Usage: ./scripts/gemini_review.sh <file_to_review> <output_file>
# The script reads the file, feeds it to gemini, and saves the review.
# Arguments:
#   $1 - Path to file to be reviewed
#   $2 - Output file path to save the review result
set -e
INFILE="$1"
OUTFILE="$2"
if [ -z "$INFILE" ] || [ -z "$OUTFILE" ]; then
  echo "Usage: $0 <input_file> <output_file>" >&2
  exit 1
fi
cat "$INFILE" | gemini -p "Review this content. Identify issues with structure, tone, and completeness. Return concise bullet points only." > "$OUTFILE"
echo "Review saved to $OUTFILE" >&2
"""
)

# The messy draft component that needs AI review
(workspace / "marketing" / "drafts" / "landing_draft.tsx").write_text(
    """// DRAFT - needs review
export default function Landing() {
  return (
    <div>
      <h1>instagram analytics for shops</h1>
      <p>we analyze your instagram. its good. buy it.</p>
      <p>contact us maybe</p>
    </div>
  )
}
"""
)

print("Workspace initialized successfully.")
print(f"Files created in {workspace}")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(workspace)}")