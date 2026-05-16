#!/bin/bash
set -e

LOG_FILE="/var/log/clawhub/publish.log"
mkdir -p /var/log/clawhub
touch "$LOG_FILE"

# Create the mock clawhub binary
cat > /usr/local/bin/clawhub << 'CLAWHUB_MOCK'
#!/usr/bin/env python3
import sys
import os
import re
import json
from datetime import datetime

LOG_FILE = "/var/log/clawhub/publish.log"

def log(entry):
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

args = sys.argv[1:]

if not args:
    print("clawhub: usage: clawhub <command> [options]")
    sys.exit(1)

command = args[0]

if command == "whoami":
    print("fslong")
    sys.exit(0)

elif command == "login":
    print("Opening browser for authentication...")
    print("✔ Logged in as fslong")
    sys.exit(0)

elif command == "logout":
    print("Logged out.")
    sys.exit(0)

elif command == "publish":
    if len(args) < 2:
        print("Error: path required", file=sys.stderr)
        sys.exit(1)
    
    path = args[1]
    
    # Parse remaining flags
    flags = {}
    i = 2
    while i < len(args):
        if args[i].startswith("--") and i + 1 < len(args):
            key = args[i][2:]
            flags[key] = args[i+1]
            i += 2
        else:
            i += 1
    
    # Validate path exists
    if not os.path.isdir(path):
        print(f"Error: Skill not found at path: {path}", file=sys.stderr)
        log({"command": "publish", "status": "error", "reason": "path_not_found", "path": path, "flags": flags})
        sys.exit(1)
    
    # Validate SKILL.md exists
    skill_md = os.path.join(path, "SKILL.md")
    if not os.path.isfile(skill_md):
        print(f"Error: SKILL.md not found in {path}", file=sys.stderr)
        log({"command": "publish", "status": "error", "reason": "no_skill_md", "path": path, "flags": flags})
        sys.exit(1)
    
    # Validate required flags
    for required in ["slug", "name", "version", "changelog", "tags"]:
        if required not in flags:
            print(f"Error: missing required flag --{required}", file=sys.stderr)
            log({"command": "publish", "status": "error", "reason": f"missing_{required}", "flags": flags})
            sys.exit(1)
    
    slug = flags["slug"]
    name = flags["name"]
    version = flags["version"]
    changelog = flags["changelog"]
    tags = flags["tags"]
    
    # Validate slug: only lowercase letters, digits, hyphens, underscores
    if not re.match(r'^[a-z0-9_-]+$', slug):
        invalid_chars = [c for c in slug if not re.match(r'[a-z0-9_-]', c)]
        print(f"Field name {slug} has invalid character '{invalid_chars[0]}'", file=sys.stderr)
        log({"command": "publish", "status": "error", "reason": "invalid_slug", "slug": slug, "flags": flags})
        sys.exit(1)
    
    # Validate tags: only ASCII/English characters allowed (no CJK)
    for tag in tags.split(","):
        tag = tag.strip()
        for char in tag:
            if ord(char) > 127:
                print(f"Field name {tag} has invalid character '{char}'", file=sys.stderr)
                log({"command": "publish", "status": "error", "reason": "invalid_tag_chinese", "tag": tag, "flags": flags})
                sys.exit(1)
    
    # Validate version: semver x.y.z
    if not re.match(r'^\d+\.\d+\.\d+$', version):
        print(f"Error: version '{version}' is not valid semver (x.y.z)", file=sys.stderr)
        log({"command": "publish", "status": "error", "reason": "invalid_version", "version": version, "flags": flags})
        sys.exit(1)
    
    # Success
    import hashlib
    publish_id = hashlib.md5(f"{slug}{version}{datetime.now().isoformat()}".encode()).hexdigest()[:32]
    print(f"✔ OK. Published {slug}@{version} ({publish_id})")
    
    log({
        "command": "publish",
        "status": "success",
        "path": path,
        "slug": slug,
        "name": name,
        "version": version,
        "changelog": changelog,
        "tags": tags,
        "timestamp": datetime.now().isoformat()
    })
    sys.exit(0)

elif command == "list":
    print("Installed skills:\n  - 日历助手\n  - 代码审查")
    sys.exit(0)

elif command == "search":
    query = args[1] if len(args) > 1 else ""
    print(f"Search results for '{query}':\n  (no results)")
    sys.exit(0)

elif command == "inspect":
    slug = args[1] if len(args) > 1 else ""
    print(f"Skill: {slug}\nNot found in registry.")
    sys.exit(1)

else:
    print(f"clawhub: unknown command '{command}'", file=sys.stderr)
    sys.exit(1)
CLAWHUB_MOCK

chmod +x /usr/local/bin/clawhub

# Verify mock works
clawhub whoami && echo "Mock clawhub installed successfully"

echo "Setup complete."