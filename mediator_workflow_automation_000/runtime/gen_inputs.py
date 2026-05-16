#!/usr/bin/env python3
import os
import stat
import random

random.seed(42)

workspace = os.environ.get("WORKSPACE", "/home/user/workspace")
os.makedirs(workspace, exist_ok=True)

# --- Create deeply nested distractor directory structure ---
dirs = [
    "clawd/skills/mediator/scripts",
    "clawd/skills/mediator/references",
    "clawd/skills/translator/scripts",
    "clawd/skills/scheduler/scripts",
    "clawd/config/backups",
    "clawd/logs",
    "projects/comms-filter/drafts",
    "projects/comms-filter/archive",
    "notes/personal",
    "notes/work",
    "tmp/processing",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "clawd/skills/translator/scripts/translator.sh": "#!/bin/bash\necho 'translator skill'\n",
    "clawd/skills/scheduler/scripts/scheduler.sh": "#!/bin/bash\necho 'scheduler skill'\n",
    "clawd/config/backups/old_config.yaml": "# Old config backup\nversion: 1\n",
    "clawd/logs/system.log": "[2024-01-10] System started\n[2024-01-10] All skills loaded\n",
    "projects/comms-filter/drafts/draft_reply_jan.txt": "Thanks for reaching out. I'll get back to you soon.\n",
    "projects/comms-filter/archive/old_email_thread.txt": "Re: Meeting next week\nSounds good, let's confirm Thursday.\n",
    "notes/personal/reminders.txt": "- Call dentist\n- Renew car insurance\n- Review budget\n",
    "notes/work/todo.txt": "- Finish Q2 report\n- Update client contacts\n- Schedule team sync\n",
    "tmp/processing/temp_output.txt": "temporary processing artifact\n",
    "clawd/skills/mediator/references/NOTES.md": "# Dev Notes\nSee prompts.md for LLM prompt templates.\nDo not edit summarize.py directly.\n",
    "clawd/config/settings.json": '{"theme": "dark", "notifications": true, "language": "en"}\n',
    "clawd/skills/mediator/references/changelog.txt": "v0.1 - initial release\nv0.2 - added iMessage support\nv0.3 - added facts-only mode\n",
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# --- The sample intercepted message (raw emotional email from difficult ex-partner) ---
# This is the messy input the agent must process
sample_message_path = os.path.join(workspace, "incoming_message.txt")
with open(sample_message_path, "w") as f:
    f.write(
        "From: Jordan Blake <jordan@blakeventures.com>\n"
        "To: me@mycompany.com\n"
        "Subject: RE: Q3 Revenue Split\n"
        "Date: Tue, 14 Jan 2025 09:23:11 -0500\n"
        "\n"
        "I honestly cannot BELIEVE what I am reading in your last message. "
        "This is EXACTLY the kind of thing you always pulled when we were partners "
        "and I am DONE being treated like this. After five years of building this "
        "company TOGETHER you have the nerve to suggest that the Q3 revenue split "
        "should be 60/40 in YOUR favor?? Absolutely unacceptable.\n"
        "\n"
        "You need to transfer $14,750 to my account by January 20th. "
        "Also, send me the signed copy of the dissolution agreement by end of week. "
        "If I don't hear from you by Friday, January 17th, I'm contacting my lawyer. "
        "I can't believe you would do this to someone who sacrificed everything.\n"
        "\n"
        "Jordan\n"
    )

# --- Intentionally broken/partial mediator config (wrong path, missing required fields) ---
# This is NOT in the right place — agent must init properly
wrong_config_path = os.path.join(workspace, "clawd/config/mediator_draft.yaml")
with open(wrong_config_path, "w") as f:
    f.write(
        "# Incomplete draft — do not use\n"
        "mediator:\n"
        "  contacts:\n"
        "    - name: 'Jordan Blake'\n"
        "      email: 'jordan@blakeventures.com'\n"
        "      # mode and summarize not configured\n"
    )

# --- Create the mock mediator.sh script (stub that agents need to invoke) ---
# This script needs to be created by setup, but we create the directory
# The SKILL.md says scripts already exist - we create them in setup_script

print(f"Workspace initialized at: {workspace}")
print("Files created:")
for rel_path in list(distractor_files.keys()) + ["incoming_message.txt", "clawd/config/mediator_draft.yaml"]:
    print(f"  {workspace}/{rel_path}")