#!/usr/bin/env bash
set -euo pipefail

echo "=== Setting up Basic Memory mock tool layer ==="

# Create a minimal mock of the basic-memory CLI tools that operate on the actual filesystem.
# The agent will call these as Python functions OR via a thin CLI wrapper.

cat > /workspace/basic_memory_tools.py << 'PYEOF'
"""
Mock implementation of Basic Memory tools for the sandbox.
Operates directly on the /workspace filesystem.
Implements: search_notes, move_note, edit_note
"""

import os
import re
import shutil
import sys
from pathlib import Path

WORKSPACE = Path("/workspace")


def search_notes(query: str) -> list[dict]:
    """Return list of matching notes (path, title, status)."""
    results = []
    query_lower = query.lower()
    for md_file in WORKSPACE.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        if query_lower in content.lower() or query_lower in md_file.stem.lower():
            rel = str(md_file.relative_to(WORKSPACE))
            title_match = re.search(r'^title:\s*(.+)$', content, re.MULTILINE)
            status_match = re.search(r'^status:\s*(.+)$', content, re.MULTILINE)
            results.append({
                "path": rel,
                "title": title_match.group(1).strip() if title_match else md_file.stem,
                "status": status_match.group(1).strip() if status_match else "unknown",
            })
    return results


def move_note(identifier: str, destination_path: str) -> dict:
    """
    Move a note to destination_path (relative to workspace).
    identifier can be a relative path (with or without .md) or a slug.
    """
    # Resolve source
    src = None
    # Try direct path first
    candidate = WORKSPACE / identifier
    if candidate.exists():
        src = candidate
    elif (WORKSPACE / (identifier + ".md")).exists():
        src = WORKSPACE / (identifier + ".md")
    else:
        # Search by stem
        for f in WORKSPACE.rglob("*.md"):
            if f.stem == Path(identifier).stem or str(f.relative_to(WORKSPACE)).replace(".md","") == identifier:
                src = f
                break
    if src is None:
        return {"success": False, "error": f"Note not found: {identifier}"}

    dst = WORKSPACE / destination_path
    if not dst.suffix:
        dst = dst.with_suffix(".md")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    return {"success": True, "moved_from": str(src.relative_to(WORKSPACE)), "moved_to": str(dst.relative_to(WORKSPACE))}


def edit_note(identifier: str, operation: str, find_text: str = "", content: str = "") -> dict:
    """
    Edit a note.  operation='find_replace': replace find_text with content.
    identifier can be a relative path (with or without .md) or a slug.
    """
    # Resolve file
    target = None
    candidate = WORKSPACE / identifier
    if candidate.exists():
        target = candidate
    elif (WORKSPACE / (identifier + ".md")).exists():
        target = WORKSPACE / (identifier + ".md")
    else:
        for f in WORKSPACE.rglob("*.md"):
            if f.stem == Path(identifier).stem or str(f.relative_to(WORKSPACE)).replace(".md","") == identifier:
                target = f
                break
    if target is None:
        return {"success": False, "error": f"Note not found: {identifier}"}

    file_content = target.read_text(encoding="utf-8")
    if operation == "find_replace":
        if find_text not in file_content:
            return {"success": False, "error": f"find_text not found in {target}"}
        new_content = file_content.replace(find_text, content, 1)
        target.write_text(new_content, encoding="utf-8")
        return {"success": True, "path": str(target.relative_to(WORKSPACE))}
    return {"success": False, "error": f"Unknown operation: {operation}"}


if __name__ == "__main__":
    import json
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "search":
        query = sys.argv[2]
        print(json.dumps(search_notes(query), indent=2))
    elif cmd == "move":
        identifier = sys.argv[2]
        destination = sys.argv[3]
        print(json.dumps(move_note(identifier, destination), indent=2))
    elif cmd == "edit":
        identifier = sys.argv[2]
        operation = sys.argv[3]
        find_text = sys.argv[4]
        replacement = sys.argv[5]
        print(json.dumps(edit_note(identifier, operation, find_text, replacement), indent=2))
    else:
        print("Usage: basic_memory_tools.py [search|move|edit] ...")
PYEOF

chmod +x /workspace/basic_memory_tools.py

# Make tools importable system-wide
cp /workspace/basic_memory_tools.py /usr/local/lib/python3.11/site-packages/basic_memory_tools.py

echo "=== Basic Memory tools installed at /workspace/basic_memory_tools.py ==="
echo "=== Also available as: python -m basic_memory_tools ==="
echo "=== Setup complete ==="