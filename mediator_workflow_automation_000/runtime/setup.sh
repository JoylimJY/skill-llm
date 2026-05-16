#!/bin/bash
set -e

WORKSPACE="${WORKSPACE:-/home/user/workspace}"
SKILL_DIR="$WORKSPACE/clawd/skills/mediator/scripts"

mkdir -p "$SKILL_DIR"
mkdir -p "$HOME/.clawdbot/logs"

# -----------------------------------------------------------------------
# Create the mock mediator.sh script (simulates the real skill script)
# This mock implements the actual business logic as defined in SKILL.md
# -----------------------------------------------------------------------
cat > "$SKILL_DIR/mediator.sh" << 'MEDIATOR_SCRIPT'
#!/bin/bash
# Mock implementation of mediator.sh for sandbox evaluation
# Implements: init, add, list, remove, check commands

CONFIG_DIR="$HOME/.clawdbot"
CONFIG_FILE="$CONFIG_DIR/mediator.yaml"
LOG_FILE="$CONFIG_DIR/logs/mediator.log"

mkdir -p "$CONFIG_DIR/logs"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

cmd_init() {
    if [ ! -f "$CONFIG_FILE" ]; then
        cat > "$CONFIG_FILE" << 'YAML'
mediator:
  archive_originals: true
  notify_channel: telegram
  contacts: []
YAML
        echo "Initialized mediator config at $CONFIG_FILE"
        log "init: created $CONFIG_FILE"
    else
        echo "Config already exists at $CONFIG_FILE"
        log "init: config already exists"
    fi
}

cmd_add() {
    local name="$1"
    shift
    local email=""
    local phone=""
    local channels="email"
    local mode="intercept"
    local summarize="facts-only"
    local respond="draft"

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --email) email="$2"; shift 2 ;;
            --phone) phone="$2"; shift 2 ;;
            --channels) channels="$2"; shift 2 ;;
            --mode) mode="$2"; shift 2 ;;
            --summarize) summarize="$2"; shift 2 ;;
            --respond) respond="$2"; shift 2 ;;
            *) shift ;;
        esac
    done

    if [ ! -f "$CONFIG_FILE" ]; then
        echo "Error: Config not initialized. Run 'mediator.sh init' first." >&2
        exit 1
    fi

    # Build contact entry and append to YAML using Python
    python3 - "$CONFIG_FILE" "$name" "$email" "$phone" "$channels" "$mode" "$summarize" "$respond" << 'PYEOF'
import sys
import yaml

config_file = sys.argv[1]
name = sys.argv[2]
email = sys.argv[3]
phone = sys.argv[4]
channels_str = sys.argv[5]
mode = sys.argv[6]
summarize = sys.argv[7]
respond = sys.argv[8]

with open(config_file, 'r') as f:
    config = yaml.safe_load(f)

channels = [c.strip() for c in channels_str.split(',')]

contact = {
    'name': name,
    'channels': channels,
    'mode': mode,
    'summarize': summarize,
    'respond': respond
}
if email:
    contact['email'] = email
if phone:
    contact['phone'] = phone

if config['mediator']['contacts'] is None:
    config['mediator']['contacts'] = []

# Remove existing contact with same name if present
config['mediator']['contacts'] = [
    c for c in config['mediator']['contacts'] if c.get('name') != name
]
config['mediator']['contacts'].append(contact)

with open(config_file, 'w') as f:
    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

print(f"Added contact: {name}")
PYEOF
    log "add: added contact '$name'"
}

cmd_list() {
    if [ ! -f "$CONFIG_FILE" ]; then
        echo "No config found. Run init first."
        exit 1
    fi
    python3 - "$CONFIG_FILE" << 'PYEOF'
import sys
import yaml

with open(sys.argv[1], 'r') as f:
    config = yaml.safe_load(f)

contacts = config.get('mediator', {}).get('contacts', [])
if not contacts:
    print("No contacts configured.")
else:
    for c in contacts:
        print(f"- {c['name']} | mode:{c.get('mode','?')} | summarize:{c.get('summarize','?')} | respond:{c.get('respond','?')}")
PYEOF
}

cmd_remove() {
    local name="$1"
    python3 - "$CONFIG_FILE" "$name" << 'PYEOF'
import sys
import yaml

with open(sys.argv[1], 'r') as f:
    config = yaml.safe_load(f)

before = len(config['mediator']['contacts'])
config['mediator']['contacts'] = [
    c for c in config['mediator']['contacts'] if c.get('name') != sys.argv[2]
]
after = len(config['mediator']['contacts'])

with open(sys.argv[1], 'w') as f:
    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

if before > after:
    print(f"Removed contact: {sys.argv[2]}")
else:
    print(f"Contact not found: {sys.argv[2]}")
PYEOF
    log "remove: removed contact '$name'"
}

cmd_check() {
    log "check: running check"
    echo "Mediator check complete. No pending messages."
}

case "$1" in
    init)   cmd_init ;;
    add)    shift; cmd_add "$@" ;;
    list)   cmd_list ;;
    remove) shift; cmd_remove "$@" ;;
    check)  cmd_check ;;
    *)
        echo "Usage: mediator.sh {init|add|list|remove|check}"
        echo "  init                    Initialize config"
        echo "  add <name> [options]    Add a contact"
        echo "    --email <addr>        Email address"
        echo "    --phone <number>      Phone number"
        echo "    --channels <list>     Comma-separated channels (email,imessage)"
        echo "    --mode <mode>         intercept|assist"
        echo "    --summarize <opt>     facts-only|neutral|full"
        echo "    --respond <opt>       draft|auto"
        echo "  list                    List contacts"
        echo "  remove <name>           Remove a contact"
        echo "  check                   Check for new messages"
        exit 1
        ;;
esac
MEDIATOR_SCRIPT

chmod +x "$SKILL_DIR/mediator.sh"

# -----------------------------------------------------------------------
# Create mock summarize.py — processes raw message into mediator summary format
# The agent needs to invoke this with the right arguments
# -----------------------------------------------------------------------
cat > "$SKILL_DIR/../scripts/summarize.py" << 'PYEOF'
#!/usr/bin/env python3
"""
Mock summarize.py — processes a raw message file and outputs a mediator summary.
Usage: python3 summarize.py --input <message_file> --contact <name> --channel <channel> --mode <mode> --summarize <summarize_option> --output <output_file>
"""
import argparse
import sys
import os
import re
from datetime import datetime

def extract_facts_only(text, contact_name, channel):
    """Extract only actionable items from message text."""
    lines = text.strip().split('\n')
    
    # Parse headers
    from_line = ""
    subject_line = ""
    body_lines = []
    in_body = False
    for line in lines:
        if line.startswith("From:"):
            from_line = line
        elif line.startswith("Subject:"):
            subject_line = line.replace("Subject:", "").strip()
        elif line == "" and not in_body and from_line:
            in_body = True
        elif in_body:
            body_lines.append(line)
    
    body = " ".join(body_lines)
    
    # Extract money amounts
    money_requests = re.findall(r'\$[\d,]+(?:\.\d{2})?', body)
    
    # Extract dates
    dates = re.findall(r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s+\d{4})?|(?:by\s+)?(?:end of week|Friday|Monday|Tuesday|Wednesday|Thursday)', body, re.IGNORECASE)
    
    # Extract action requests (simplified keyword extraction)
    actions = []
    action_patterns = [
        (r'you need to (.+?)(?:\.|$)', None),
        (r'send me (.+?)(?:\.|$)', None),
        (r'transfer (.+?)(?:\.|$)', None),
    ]
    for pattern, _ in action_patterns:
        matches = re.findall(pattern, body, re.IGNORECASE)
        actions.extend(matches)
    
    # Build facts-only summary
    action_required = "Yes" if (money_requests or actions or dates) else "No"
    
    requests = []
    if money_requests:
        amount = money_requests[0]
        date_str = dates[0] if dates else "unspecified date"
        requests.append(f"Transfer {amount} by {date_str}")
    if "signed copy" in body.lower() or "dissolution agreement" in body.lower():
        end_date = "end of week (Friday, January 17th)" if "friday" in body.lower() or "end of week" in body.lower() else "unspecified date"
        requests.append(f"Send signed copy of dissolution agreement by {end_date}")
    if "lawyer" in body.lower() or "legal" in body.lower():
        requests.append("Implicit legal threat if no response by deadline")
    
    request_text = "\n".join(f"- {r}" for r in requests) if requests else "No specific requests identified."
    
    suggested = 'Acknowledged. I will review the Q3 revenue figures and respond to both items by the stated deadlines.'
    
    summary = f"""**From:** {contact_name}
**Channel:** {channel.capitalize()}
**Action Required:** {action_required}

**Requests:**
{request_text}

**Suggested response:**
"{suggested}"
"""
    return summary

def neutral_rewrite(text, contact_name, channel):
    lines = text.strip().split('\n')
    body_lines = []
    in_body = False
    from_line = ""
    for line in lines:
        if line.startswith("From:"):
            from_line = line
        elif line == "" and not in_body and from_line:
            in_body = True
        elif in_body:
            body_lines.append(line)
    
    body = " ".join(body_lines)
    # Strip emotional language (caps words, exclamation marks)
    neutral = re.sub(r'\b[A-Z]{3,}\b', lambda m: m.group(0).capitalize(), body)
    neutral = neutral.replace("!!!", ".").replace("!!", ".").replace("!", ".")
    neutral = re.sub(r'\b(cannot BELIEVE|honestly cannot|the nerve to|Absolutely unacceptable)\b', 'disagrees with', neutral, flags=re.IGNORECASE)
    
    return f"""**From:** {contact_name}
**Channel:** {channel.capitalize()}
**Neutral Rewrite:**
{neutral.strip()}

**Suggested response:**
"Thank you for your message. I will review and respond accordingly."
"""

def full_summary(text, contact_name, channel):
    lines = text.strip().split('\n')
    body_lines = []
    in_body = False
    from_line = ""
    for line in lines:
        if line.startswith("From:"):
            from_line = line
        elif line == "" and not in_body and from_line:
            in_body = True
        elif in_body:
            body_lines.append(line)
    body = " ".join(body_lines)
    
    emotional_flags = re.findall(r'\b[A-Z]{3,}\b|!{2,}', body)
    
    return f"""**From:** {contact_name}
**Channel:** {channel.capitalize()}
**Full Content:**
{body.strip()}

**Emotional/Manipulative Language Detected:** {len(emotional_flags)} instances
**Flagged phrases:** {', '.join(set(emotional_flags[:5])) if emotional_flags else 'None'}

**Suggested response:**
"I have received your message and will respond shortly."
"""

def main():
    parser = argparse.ArgumentParser(description='Process and summarize a message.')
    parser.add_argument('--input', required=True, help='Input message file')
    parser.add_argument('--contact', required=True, help='Contact name')
    parser.add_argument('--channel', required=True, help='Channel (email, imessage)')
    parser.add_argument('--mode', required=True, choices=['intercept', 'assist'], help='Processing mode')
    parser.add_argument('--summarize', required=True, choices=['facts-only', 'neutral', 'full'], help='Summarize option')
    parser.add_argument('--output', required=True, help='Output summary file')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    with open(args.input, 'r') as f:
        message_text = f.read()

    if args.summarize == 'facts-only':
        summary = extract_facts_only(message_text, args.contact, args.channel)
    elif args.summarize == 'neutral':
        summary = neutral_rewrite(message_text, args.contact, args.channel)
    else:
        summary = full_summary(message_text, args.contact, args.channel)

    # For intercept mode, note that original is archived
    if args.mode == 'intercept':
        summary = f"[INTERCEPTED — Original archived]\n\n" + summary
    else:
        summary = f"[ASSIST MODE — Original preserved]\n\n" + summary

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, 'w') as f:
        f.write(summary)
        f.write(f"\n\n---\nProcessed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    print(f"Summary written to: {args.output}")

if __name__ == '__main__':
    main()
PYEOF

chmod +x "$WORKSPACE/clawd/skills/mediator/scripts/summarize.py"

# Make SKILL.md available in the workspace
cat > "$WORKSPACE/clawd/skills/mediator/SKILL.md" << 'SKILLEOF'
---
name: mediator
description: Intercept and filter communications from difficult contacts. Strips emotion, extracts facts, drafts neutral responses.
---

# Mediator Skill

Emotional firewall for difficult relationships. Intercepts messages from configured contacts, strips out emotional content, presents just the facts, and helps draft measured responses.

## Quick Start

```bash
# Initialize config (creates mediator.yaml if missing)
~/clawd/skills/mediator/scripts/mediator.sh init

# Add a contact to mediate
~/clawd/skills/mediator/scripts/mediator.sh add "Ex Partner" \
  --email "ex@email.com" \
  --phone "+15551234567" \
  --channels email,imessage

# Process incoming (usually called by cron/heartbeat)
~/clawd/skills/mediator/scripts/mediator.sh check

# List configured contacts
~/clawd/skills/mediator/scripts/mediator.sh list

# Remove a contact
~/clawd/skills/mediator/scripts/mediator.sh remove "Ex Partner"
```

## Configuration

Config lives at `~/.clawdbot/mediator.yaml`:

```yaml
mediator:
  # Global settings
  archive_originals: true      # Archive raw messages after processing
  notify_channel: telegram     # Where to send summaries (telegram|slack|imessage)
  
  contacts:
    - name: "Ex Partner"
      email: "ex@email.com"
      phone: "+15551234567"
      channels: [email, imessage]
      mode: intercept          # intercept | assist
      summarize: facts-only    # facts-only | neutral | full
      respond: draft           # draft | auto (dangerous)
      
    - name: "Difficult Client"  
      email: "client@company.com"
      channels: [email]
      mode: assist             # Don't hide originals, just help respond
      summarize: neutral
      respond: draft
```

### Modes

- **intercept**: Archive/hide original, only show summary. User never sees raw emotional content.
- **assist**: Show original but also provide summary and response suggestions.

### Summarize Options

- **facts-only**: Extract only actionable items, requests, deadlines. No emotion.
- **neutral**: Rewrite the message in neutral tone, preserving all content.
- **full**: Show everything but flag emotional/manipulative language.

### Respond Options

- **draft**: Generate suggested response, wait for approval before sending.
- **auto**: Automatically respond (use with extreme caution).

## Scripts

- `mediator.sh` - Main CLI wrapper
- `process-email.py` - Email processing logic
- `process-imessage.py` - iMessage processing logic
- `summarize.py` - LLM-based content analysis and summarization

## Integration

### Heartbeat Check

Add to `HEARTBEAT.md`:
```
## Mediator Check
~/clawd/skills/mediator/scripts/mediator.sh check
```

## Safety Notes

- **Never auto-respond** to legal, financial, or child-related messages
- Original messages are archived, not deleted (recoverable)
- All actions logged to `~/.clawdbot/logs/mediator.log`

## Example Output

**Original email:**
> I can't BELIEVE you would do this to me AGAIN. After everything I've done for you!!! You NEVER think about anyone but yourself. I need you to pick up the kids at 3pm on Saturday and if you can't even do THAT then I don't know what to say anymore.

**Mediator summary:**
> **From:** Ex Partner
> **Channel:** Email  
> **Action Required:** Yes
> 
> **Request:** Pick up kids at 3pm Saturday
> 
> **Suggested response:**
> "Confirmed. I'll pick up the kids at 3pm on Saturday."
SKILLEOF

# Create a HOME symlink so ~/clawd points into workspace
mkdir -p "$HOME/clawd"
# Link the workspace skill directory into HOME so ~/clawd/skills path works
ln -sfn "$WORKSPACE/clawd/skills" "$HOME/clawd/skills" 2>/dev/null || true

echo "Setup complete. Mediator scripts available at $SKILL_DIR"
echo "SKILL.md available at $WORKSPACE/clawd/skills/mediator/SKILL.md"
echo "Sample message available at $WORKSPACE/incoming_message.txt"