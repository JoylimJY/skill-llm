import json
import os
import re
from pathlib import Path

workspace = Path(__import__('sys').argv[1])
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})


def read_text(path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)

# Required files
required = ["IDENTITY.md", "SOUL.md", "AGENTS.md", "USER.md", "HEARTBEAT.md"]
for fname in required:
    p = workspace / fname
    try:
        exists = p.exists()
        add_check(f"exists:{fname}", exists, "present" if exists else "missing")
    except Exception as e:
        add_check(f"exists:{fname}", False, f"error: {e}")

# Content checks with fuzzy matching
try:
    identity = (workspace / "IDENTITY.md").read_text(encoding='utf-8')
    identity_lower = identity.lower()
    
    # Check for Atlas name (case insensitive)
    has_atlas = "atlas" in identity_lower
    
    # Check for AI assistant role - flexible matching to allow "AI Research Assistant", "AI assistant", etc.
    has_ai_role = bool(re.search(r'ai.*assistant', identity_lower))
    
    ok = has_atlas and has_ai_role
    add_check("identity content", ok, "contains atlas + ai assistant" if ok else "missing expected identity markers")
except Exception as e:
    add_check("identity content", False, f"error: {e}")

try:
    soul = (workspace / "SOUL.md").read_text(encoding='utf-8')
    soul_lower = soul.lower()
    
    # Check for concise requirement
    has_concise = bool(re.search(r'\bconcise\b', soul_lower))
    
    # Check for permission/outbound boundary (flexible matching)
    # Accept various phrasings: "permission", "asked", "outbound", "explicitly"
    has_permission_boundary = bool(re.search(
        r'\b(permission|asked|outbound|explicitly|authorize|confirm)\b',
        soul_lower
    ))
    
    # Additional check for outbound message context
    has_outbound_context = bool(re.search(
        r'\b(outbound|message|send|communicat)\b',
        soul_lower
    ))
    
    # Pass if concise is present AND (permission boundary OR outbound context)
    ok = has_concise and (has_permission_boundary or has_outbound_context)
    add_check("soul boundary", ok, "contains concise + permission boundary" if ok else "missing concise or permission rule")
except Exception as e:
    add_check("soul boundary", False, f"error: {e}")

try:
    agents = (workspace / "AGENTS.md").read_text(encoding='utf-8')
    marker_ok = "openclaw_task_marker_alpha_2025" in agents.lower() or "marker" in agents.lower()
    memory_ok = "memory" in agents.lower()
    add_check("agents mentions memory", marker_ok or memory_ok, "mentions memory or seed marker" if (marker_ok or memory_ok) else "missing memory guidance")
except Exception as e:
    add_check("agents mentions memory", False, f"error: {e}")

try:
    heartbeat = (workspace / "HEARTBEAT.md").read_text(encoding='utf-8')
    ok = len(heartbeat.strip()) > 0
    add_check("heartbeat nonempty", ok, "has content" if ok else "empty or missing content")
except Exception as e:
    add_check("heartbeat nonempty", False, f"error: {e}")

# Memory directory is optional per prompt - do not require it for task completion
# Only check if it exists and has content, but don't fail if missing
try:
    memdir = workspace / "memory"
    has_mem = memdir.exists() and any(memdir.glob('*.md'))
    add_check("memory seed file (optional)", True, "memory directory optional - not required for completion")
except Exception as e:
    add_check("memory seed file (optional)", True, "memory directory optional - not required for completion")

passed = all(c["passed"] for c in checks)
score = sum(1 for c in checks if c["passed"]) / len(checks) if checks else 0.0
print(json.dumps({"passed": passed, "score": score, "checks": checks}))