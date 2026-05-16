#!/usr/bin/env python3
"""
Evaluation script for multi-agent-deploy task.
Checks that assistant3 was correctly deployed.
"""
import json
import pathlib
import sys

BASE = pathlib.Path("/home/admin/.openclaw")

checks = []

def check(name: str, passed: bool, detail: str):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed

# ── 1. workspace-assistant3 directory exists ───────────────────────────────
try:
    ws3 = BASE / "workspace-assistant3"
    exists = ws3.is_dir()
    check(
        "workspace_assistant3_exists",
        exists,
        f"{ws3} {'exists' if exists else 'does NOT exist'}"
    )
except Exception as e:
    check("workspace_assistant3_exists", False, f"Exception: {e}")

# ── 2. workspace contains all three required files ─────────────────────────
for fname in ("SOUL.md", "AGENTS.md", "USER.md"):
    try:
        fpath = BASE / "workspace-assistant3" / fname
        exists = fpath.is_file()
        content_ok = False
        detail = ""
        if exists:
            content = fpath.read_text(encoding="utf-8")
            content_ok = len(content.strip()) > 0
            detail = f"{fpath} exists and has content" if content_ok else f"{fpath} exists but is EMPTY"
        else:
            detail = f"{fpath} does NOT exist"
        check(f"workspace_file_{fname}", exists and content_ok, detail)
    except Exception as e:
        check(f"workspace_file_{fname}", False, f"Exception: {e}")

# ── 3. agent directory structure exists ───────────────────────────────────
try:
    agent_dir = BASE / "agents" / "assistant3" / "agent"
    exists = agent_dir.is_dir()
    check(
        "agent_dir_assistant3_exists",
        exists,
        f"{agent_dir} {'exists' if exists else 'does NOT exist'}"
    )
except Exception as e:
    check("agent_dir_assistant3_exists", False, f"Exception: {e}")

# ── 4. No accidental overwrite of assistant2 ──────────────────────────────
try:
    ws2 = BASE / "workspace-assistant2"
    soul2 = ws2 / "SOUL.md"
    intact = soul2.is_file() and len(soul2.read_text().strip()) > 0
    check(
        "assistant2_not_overwritten",
        intact,
        f"workspace-assistant2/SOUL.md {'intact' if intact else 'missing or empty'}"
    )
except Exception as e:
    check("assistant2_not_overwritten", False, f"Exception: {e}")

# ── 5. openclaw.json updated with assistant3 entry ────────────────────────
try:
    cfg_path = BASE / "openclaw.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    agents = cfg.get("agents", [])
    a3_entries = [a for a in agents if a.get("id") == "assistant3"]
    found = len(a3_entries) == 1
    check(
        "config_has_assistant3",
        found,
        f"assistant3 entry {'found' if found else 'NOT found'} in openclaw.json agents list"
    )
except Exception as e:
    check("config_has_assistant3", False, f"Exception reading openclaw.json: {e}")

# ── 6. assistant3 config fields are correct ───────────────────────────────
try:
    cfg_path = BASE / "openclaw.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    agents = cfg.get("agents", [])
    a3_entries = [a for a in agents if a.get("id") == "assistant3"]
    if not a3_entries:
        check("config_assistant3_fields", False, "assistant3 entry not found, cannot check fields")
    else:
        a3 = a3_entries[0]
        issues = []

        # id
        if a3.get("id") != "assistant3":
            issues.append(f"id={a3.get('id')!r} (expected 'assistant3')")

        # name — must contain "3" somewhere (日常助手 3)
        name_val = a3.get("name", "")
        if "3" not in name_val:
            issues.append(f"name={name_val!r} (expected to contain '3', e.g. '日常助手 3')")

        # workspace path
        expected_ws = str(BASE / "workspace-assistant3")
        actual_ws = a3.get("workspace", "")
        if actual_ws != expected_ws:
            issues.append(f"workspace={actual_ws!r} (expected {expected_ws!r})")

        # agentDir path — must end with agents/assistant3/agent
        expected_ad = str(BASE / "agents" / "assistant3" / "agent")
        actual_ad = a3.get("agentDir", "")
        if actual_ad != expected_ad:
            issues.append(f"agentDir={actual_ad!r} (expected {expected_ad!r})")

        # model
        expected_model = "dashscope/qwen3.5-plus"
        actual_model = a3.get("model", "")
        if actual_model != expected_model:
            issues.append(f"model={actual_model!r} (expected {expected_model!r})")

        passed = len(issues) == 0
        detail = "All fields correct" if passed else "Issues: " + "; ".join(issues)
        check("config_assistant3_fields", passed, detail)
except Exception as e:
    check("config_assistant3_fields", False, f"Exception: {e}")

# ── 7. original assistant entry still intact ──────────────────────────────
try:
    cfg_path = BASE / "openclaw.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    agents = cfg.get("agents", [])
    a1_entries = [a for a in agents if a.get("id") == "assistant"]
    intact = len(a1_entries) == 1
    check(
        "original_assistant_intact",
        intact,
        f"Original 'assistant' entry {'present' if intact else 'MISSING or duplicated'} in config"
    )
except Exception as e:
    check("original_assistant_intact", False, f"Exception: {e}")

# ── 8. No assistant4 or higher accidentally created ───────────────────────
try:
    cfg_path = BASE / "openclaw.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    agents = cfg.get("agents", [])
    import re
    high_ids = [a["id"] for a in agents if re.fullmatch(r"assistant([4-9]|\d{2,})", a.get("id", ""))]
    no_overshoot = len(high_ids) == 0
    # Also check filesystem
    import os
    for n in range(4, 10):
        if (BASE / f"workspace-assistant{n}").exists():
            high_ids.append(f"workspace-assistant{n}_dir")
    no_overshoot = len(high_ids) == 0
    check(
        "no_overshoot_beyond_3",
        no_overshoot,
        f"No agents beyond assistant3 created" if no_overshoot else f"Unexpected: {high_ids}"
    )
except Exception as e:
    check("no_overshoot_beyond_3", False, f"Exception: {e}")

# ── scoring ────────────────────────────────────────────────────────────────
passed_count = sum(1 for c in checks if c["passed"])
total = len(checks)
score = round(passed_count / total, 4)
overall = passed_count == total

result = {
    "passed": overall,
    "score": score,
    "checks": checks
}
print(json.dumps(result, ensure_ascii=False, indent=2))
sys.exit(0 if overall else 1)