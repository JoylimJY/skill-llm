import os
import json
import stat
import random
import textwrap
from pathlib import Path

random.seed(42)

HOME = Path.home()

# ── 1. Build the OpenClaw directory skeleton ──────────────────────────────────
dirs = [
    HOME / ".qclaw/workspace/skills/model-manager/scripts",
    HOME / ".qclaw/workspace/skills/model-manager/docs",
    HOME / ".qclaw/workspace/skills/model-manager/tests",
    HOME / ".qclaw/workspace/skills/translator/scripts",
    HOME / ".qclaw/workspace/skills/code-reviewer/scripts",
    HOME / ".qclaw/agents/main/agent",
    HOME / ".qclaw/agents/main/logs",
    HOME / ".qclaw/agents/secondary/agent",
    HOME / ".qclaw/providers/ollama",
    HOME / ".qclaw/providers/qclaw",
    HOME / ".qclaw/cache/models",
    HOME / ".qclaw/cache/sessions",
]
for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# ── 2. Write the mock `openclaw` binary ───────────────────────────────────────
# This script simulates the openclaw CLI; model_manager.py will call it.
openclaw_bin = Path("/usr/local/bin/openclaw")
openclaw_src = textwrap.dedent(r"""
#!/usr/bin/env python3
'''
Mock openclaw CLI for testing.
State files:
  - ~/.qclaw/agents/main/agent/models.json  (session state)
  - ~/.qclaw/openclaw.json                  (global config)
'''
import sys, json, os
from pathlib import Path

HOME = Path.home()
SESSION_FILE = HOME / ".qclaw/agents/main/agent/models.json"
GLOBAL_FILE  = HOME / ".qclaw/openclaw.json"

def load_session():
    if SESSION_FILE.exists():
        return json.loads(SESSION_FILE.read_text())
    return {"current_model": "ollama/llama3:8b", "fallbacks": ["ollama/ministral-3:14b", "ollama/phi-3:mini"]}

def save_session(data):
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.write_text(json.dumps(data, indent=2))

def load_global():
    if GLOBAL_FILE.exists():
        return json.loads(GLOBAL_FILE.read_text())
    return {"default_model": "ollama/llama3:8b", "fallbacks": ["ollama/ministral-3:14b", "ollama/phi-3:mini"]}

def save_global(data):
    GLOBAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    GLOBAL_FILE.write_text(json.dumps(data, indent=2))

AVAILABLE = [
    "ollama/llama3:8b",
    "ollama/nemotron-3-super:cloud",
    "ollama/ministral-3:14b",
    "ollama/phi-3:mini",
    "ollama/mistral:7b",
    "qclaw/gpt-turbo:latest",
]

args = sys.argv[1:]
if not args:
    print("Usage: openclaw models <subcommand>")
    sys.exit(1)

if args[0] != "models":
    print(f"Unknown command: {args[0]}")
    sys.exit(1)

sub = args[1] if len(args) > 1 else ""
session = load_session()
glob    = load_global()

if sub == "list":
    print("Available models:")
    for m in AVAILABLE:
        marker = " *" if m == session["current_model"] else ""
        print(f"  {m}{marker}")

elif sub == "set":
    model_id = args[2] if len(args) > 2 else ""
    if model_id not in AVAILABLE:
        print(f"Error: model '{model_id}' not found", file=sys.stderr)
        sys.exit(1)
    session["current_model"] = model_id
    glob["default_model"]    = model_id
    save_session(session)
    save_global(glob)
    print(f"Default model set to: {model_id}")

elif sub == "status":
    print(f"Current model : {session['current_model']}")
    print(f"Fallback count: {len(session['fallbacks'])}")
    print("Fallbacks:")
    for f in session["fallbacks"]:
        print(f"  - {f}")

elif sub == "fallbacks":
    action = args[2] if len(args) > 2 else ""
    if action == "list":
        print("Fallback models:")
        for f in session["fallbacks"]:
            print(f"  {f}")
    elif action == "add":
        model_id = args[3] if len(args) > 3 else ""
        if model_id not in AVAILABLE:
            print(f"Error: model '{model_id}' not found", file=sys.stderr)
            sys.exit(1)
        if model_id not in session["fallbacks"]:
            session["fallbacks"].append(model_id)
            glob["fallbacks"] = session["fallbacks"]
            save_session(session)
            save_global(glob)
            print(f"Added fallback: {model_id}")
        else:
            print(f"Fallback already exists: {model_id}")
    elif action == "remove":
        model_id = args[3] if len(args) > 3 else ""
        if model_id in session["fallbacks"]:
            session["fallbacks"].remove(model_id)
            glob["fallbacks"] = session["fallbacks"]
            save_session(session)
            save_global(glob)
            print(f"Removed fallback: {model_id}")
        else:
            print(f"Fallback not found: {model_id}")
    else:
        print(f"Unknown fallbacks action: {action}", file=sys.stderr)
        sys.exit(1)
else:
    print(f"Unknown subcommand: {sub}", file=sys.stderr)
    sys.exit(1)
""").lstrip()
openclaw_bin.write_text(openclaw_src)
openclaw_bin.chmod(openclaw_bin.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ── 3. Write model_manager.py (the actual skill script) ───────────────────────
model_manager_src = textwrap.dedent(r"""
#!/usr/bin/env python3
'''
OpenClaw model-manager skill script.
Wraps `openclaw models` CLI commands.
'''
import sys, subprocess, os

SCRIPT = os.path.basename(__file__)

def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    return result.returncode

def usage():
    print(f"Usage: {SCRIPT} <list|set|fallback|status> [args]")
    sys.exit(1)

args = sys.argv[1:]
if not args:
    usage()

cmd = args[0]

if cmd == "list":
    sys.exit(run(["openclaw", "models", "list"]))

elif cmd == "set":
    if len(args) < 2:
        print("Usage: set <model_id>")
        sys.exit(1)
    sys.exit(run(["openclaw", "models", "set", args[1]]))

elif cmd == "fallback":
    if len(args) < 2:
        print("Usage: fallback <add|remove|list> [model_id]")
        sys.exit(1)
    action = args[1]
    if action == "list":
        sys.exit(run(["openclaw", "models", "fallbacks", "list"]))
    elif action in ("add", "remove"):
        if len(args) < 3:
            print(f"Usage: fallback {action} <model_id>")
            sys.exit(1)
        sys.exit(run(["openclaw", "models", "fallbacks", action, args[2]]))
    else:
        print(f"Unknown fallback action: {action}")
        sys.exit(1)

elif cmd == "status":
    sys.exit(run(["openclaw", "models", "status"]))

else:
    usage()
""").lstrip()

mm_path = HOME / ".qclaw/workspace/skills/model-manager/scripts/model_manager.py"
mm_path.write_text(model_manager_src)
mm_path.chmod(mm_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ── 4. Write the INITIAL state files (stale/wrong config) ────────────────────
initial_session = {
    "current_model": "ollama/llama3:8b",
    "fallbacks": ["ollama/ministral-3:14b", "ollama/phi-3:mini"]
}
initial_global = {
    "default_model": "ollama/llama3:8b",
    "fallbacks": ["ollama/ministral-3:14b", "ollama/phi-3:mini"],
    "providers": {
        "ollama": {"endpoint": "http://localhost:11434"},
        "qclaw":  {"endpoint": "https://api.qclaw.io"}
    }
}

session_path = HOME / ".qclaw/agents/main/agent/models.json"
global_path  = HOME / ".qclaw/openclaw.json"
session_path.write_text(json.dumps(initial_session, indent=2))
global_path.write_text(json.dumps(initial_global, indent=2))

# ── 5. Distractor files ───────────────────────────────────────────────────────
distractors = {
    HOME / ".qclaw/workspace/skills/translator/scripts/translate.py":
        "# translation skill\ndef translate(text, lang): pass\n",
    HOME / ".qclaw/workspace/skills/code-reviewer/scripts/review.py":
        "# code review skill\ndef review(code): pass\n",
    HOME / ".qclaw/workspace/skills/model-manager/docs/changelog.txt":
        "v1.0 - initial release\nv1.1 - added fallback support\nv1.2 - cloud models\n",
    HOME / ".qclaw/workspace/skills/model-manager/tests/test_manager.py":
        "# placeholder unit tests\nimport unittest\nclass TestManager(unittest.TestCase): pass\n",
    HOME / ".qclaw/agents/main/logs/session_2024_01.log":
        "[INFO] Session started\n[INFO] Model: ollama/llama3:8b\n[INFO] Session ended\n",
    HOME / ".qclaw/agents/main/logs/session_2024_02.log":
        "[INFO] Session started\n[WARN] Model fallback triggered\n[INFO] Session ended\n",
    HOME / ".qclaw/agents/secondary/agent/models.json":
        json.dumps({"current_model": "qclaw/gpt-turbo:latest", "fallbacks": []}, indent=2),
    HOME / ".qclaw/providers/ollama/config.json":
        json.dumps({"endpoint": "http://localhost:11434", "timeout": 30}, indent=2),
    HOME / ".qclaw/providers/qclaw/config.json":
        json.dumps({"endpoint": "https://api.qclaw.io", "timeout": 60}, indent=2),
    HOME / ".qclaw/cache/models/manifest.json":
        json.dumps({"cached": ["ollama/llama3:8b", "ollama/phi-3:mini"]}, indent=2),
    HOME / ".qclaw/cache/sessions/index.json":
        json.dumps({"total_sessions": 42, "last_session": "2024-02-15"}, indent=2),
}

for path, content in distractors.items():
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)

# ── 6. Write a workspace marker so the eval knows where to look ──────────────
workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)
(workspace / ".task_initialized").write_text("ok")

print("Workspace initialized successfully.")
print(f"Session state: {session_path}")
print(f"Global config: {global_path}")