import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Deep directory structure with distractor files ---
dirs = [
    "projects/openclaw/src",
    "projects/openclaw/tests",
    "projects/saas-landing/design",
    "notes/meetings",
    "notes/ideas",
    ".learnings",
    "memory",
    "scripts",
    "config",
    "tmp/drafts",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "projects/openclaw/src/main.py": "# OpenClaw main entry\nprint('hello')\n",
    "projects/openclaw/src/utils.py": "# Utility functions\ndef slugify(s): return s.lower().replace(' ', '-')\n",
    "projects/openclaw/tests/test_main.py": "import unittest\nclass TestMain(unittest.TestCase): pass\n",
    "projects/saas-landing/design/wireframe_notes.txt": "Header: big CTA\nFooter: links\nColor: #3A86FF\n",
    "notes/meetings/2026-03-20-standup.md": "## Standup\n- Reviewed auth flow\n- Fixed pagination bug\n",
    "notes/meetings/2026-03-21-investor-call.md": "## Investor Call\n- Asked about runway\n- Follow up on deck\n",
    "notes/ideas/feature-backlog.txt": "- dark mode\n- push notifications\n- export to CSV\n",
    ".learnings/ERRORS.md": "# Errors\n(none so far)\n",
    "memory/2026-03-21.md": "Discussed roadmap with co-founder. Agreed on Q2 milestones.\n",
    "scripts/deploy.sh": "#!/bin/bash\necho 'Deploying...'\n",
    "config/settings.json": '{"env": "development", "port": 3000, "debug": true}\n',
    "tmp/drafts/bp_v1.md": "## Q2 Business Plan Draft\n- Revenue model\n- Growth targets\n",
    "tmp/drafts/email_draft.txt": "Hi team,\nPlease review the attached deck before Friday.\nThanks\n",
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# --- THE MAIN PROBLEM FILE: a messy capture dump the agent must process ---
capture_content = """\
=== MY BACKLOG CAPTURE — 2026-03-22 ===
(dumped from phone notes, needs cleanup)

- remind me to ping the accountant about Q1 tax filing — do this end of day tomorrow
- add "review OpenClaw PR #451" to my tasks, link is https://github.com/openclaw/openclaw/pull/451
- don't forget to renew the SSL certificate for saas-landing.io — deadline is April 15th 11:59pm
- task: write the Q2 investor update email
- remind me to call mom on Sunday morning at 10am

misc:
* the annual billing for Vercel renews next Friday — add as deadline at end of day
* track issue #88 in openclaw: https://github.com/openclaw/openclaw/issues/88
"""

with open(os.path.join(workspace, "backlog_capture.txt"), "w") as f:
    f.write(capture_content)

print("Workspace generated successfully.")
print(f"Files created: {len(distractor_files) + 1} files across {len(dirs)} directories")