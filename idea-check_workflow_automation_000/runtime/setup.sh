#!/bin/bash
set -e

# -------------------------------------------------------
# 1. Create the mock mcporter binary
# -------------------------------------------------------
cat > /usr/local/bin/mcporter << 'MCPORTER_EOF'
#!/usr/bin/env python3
"""
Mock mcporter binary that simulates the real mcporter CLI behavior.
Supports: mcporter config add <name> --command <cmd>
          mcporter call <server>.<tool> <key>=<value> ...
"""
import sys
import json
import os
import re

REGISTRY_FILE = "/tmp/mcporter_registry.json"

def load_registry():
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE) as f:
            return json.load(f)
    return {}

def save_registry(reg):
    with open(REGISTRY_FILE, "w") as f:
        json.dump(reg, f, indent=2)

def cmd_config(args):
    # mcporter config add <name> --command "<cmd>"
    if len(args) < 2:
        print("Usage: mcporter config add <name> --command <cmd>", file=sys.stderr)
        sys.exit(1)
    action = args[0]
    if action == "add":
        name = args[1]
        # parse --command
        cmd_val = None
        for i, a in enumerate(args):
            if a == "--command" and i + 1 < len(args):
                cmd_val = args[i+1]
        if not cmd_val:
            print("Missing --command", file=sys.stderr)
            sys.exit(1)
        reg = load_registry()
        reg[name] = {"command": cmd_val}
        save_registry(reg)
        print(f"Registered '{name}' -> {cmd_val}")
    else:
        print(f"Unknown config action: {action}", file=sys.stderr)
        sys.exit(1)

def cmd_call(args):
    # mcporter call <server>.<tool> key1=val1 key2=val2 ...
    if len(args) < 1:
        print("Usage: mcporter call <server>.<tool> [args...]", file=sys.stderr)
        sys.exit(1)
    
    tool_ref = args[0]
    params = {}
    for a in args[1:]:
        if "=" in a:
            k, v = a.split("=", 1)
            # strip surrounding quotes
            v = v.strip('"').strip("'")
            params[k] = v
    
    # Route to mock handler
    if tool_ref == "idea-reality.idea_check":
        handle_idea_check(params)
    else:
        # Check registry
        reg = load_registry()
        server_name = tool_ref.split(".")[0]
        if server_name not in reg:
            print(json.dumps({"error": f"Server '{server_name}' not registered. Run: mcporter config add {server_name} --command \"uvx idea-reality-mcp\""}))
            sys.exit(0)
        print(json.dumps({"error": f"Unknown tool: {tool_ref}"}))
        sys.exit(0)

def handle_idea_check(params):
    idea_text = params.get("idea_text", "")
    depth = params.get("depth", "quick")
    
    reg = load_registry()
    if "idea-reality" not in reg:
        print(json.dumps({
            "error": "Server 'idea-reality' not registered. Run: mcporter config add idea-reality --command \"uvx idea-reality-mcp\""
        }))
        return

    # Deep check returns a high signal (crowded space - OpenAPI tooling is very crowded)
    if depth == "deep":
        result = {
            "reality_signal": 87,
            "depth_used": "deep",
            "sources_checked": ["GitHub", "Hacker News", "npm", "PyPI", "Product Hunt"],
            "evidence": [
                {"source": "PyPI", "count": 34, "note": "34 packages matching 'openapi generator python'"},
                {"source": "GitHub", "count": 2100, "note": "2100+ repos for openapi python codegen"},
                {"source": "Hacker News", "count": 12, "note": "12 Show HN posts about openapi generators"},
                {"source": "npm", "count": 89, "note": "89 packages for openapi generation"},
                {"source": "Product Hunt", "count": 5, "note": "5 products launched for API spec generation"}
            ],
            "top_similars": [
                {"name": "flasgger", "stars": 3400, "description": "Flask/Swagger UI with OpenAPI spec generation from docstrings"},
                {"name": "spectree", "stars": 1200, "description": "API spec generation and validation for Python web frameworks"},
                {"name": "apispec", "stars": 1100, "description": "Pluggable OpenAPI spec generation from Python code"}
            ],
            "pivot_hints": [
                "Focus on type-hint-only codebases (no docstrings) — most tools require docstrings",
                "Target non-web codebases (SDKs, internal tools) — existing tools assume web frameworks",
                "Add diff-tracking to detect API breaking changes across commits"
            ]
        }
    else:
        # Quick check
        result = {
            "reality_signal": 72,
            "depth_used": "quick",
            "sources_checked": ["GitHub", "Hacker News"],
            "evidence": [
                {"source": "GitHub", "count": 2100, "note": "2100+ repos for openapi python codegen"},
                {"source": "Hacker News", "count": 12, "note": "12 Show HN posts about openapi generators"}
            ],
            "top_similars": [
                {"name": "flasgger", "stars": 3400, "description": "Flask/Swagger UI with OpenAPI spec generation from docstrings"},
                {"name": "spectree", "stars": 1200, "description": "API spec generation and validation for Python web frameworks"},
                {"name": "apispec", "stars": 1100, "description": "Pluggable OpenAPI spec generation from Python code"}
            ],
            "pivot_hints": [
                "Focus on type-hint-only codebases (no docstrings)",
                "Target non-web codebases (SDKs, internal tools)"
            ]
        }
    
    print(json.dumps(result))

def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: mcporter <command> [args...]", file=sys.stderr)
        sys.exit(1)
    
    command = args[0]
    rest = args[1:]
    
    if command == "config":
        cmd_config(rest)
    elif command == "call":
        cmd_call(rest)
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
MCPORTER_EOF

chmod +x /usr/local/bin/mcporter

# -------------------------------------------------------
# 2. Verify mcporter is callable
# -------------------------------------------------------
echo "mcporter installed at $(which mcporter)"
mcporter --help 2>/dev/null || true

# -------------------------------------------------------
# 3. Clean any leftover registry state
# -------------------------------------------------------
rm -f /tmp/mcporter_registry.json

echo "Setup complete. mcporter mock is ready."
echo "Registry cleared."
echo ""
echo "Task brief available at /workspace/task_brief.json"