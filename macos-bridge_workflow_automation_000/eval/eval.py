#!/usr/bin/env python3
"""
Evaluation script for the macos-bridge task.
Usage: python3 eval_script.py <workspace_dir>
"""
import json
import os
import re
import sys
import subprocess
from pathlib import Path

def load_audit_log():
    try:
        with open("/tmp/macos-bridge-audit.log") as f:
            return f.read()
    except Exception:
        return ""

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []

    audit = load_audit_log()

    config_path = os.path.join(workspace, "home/node/.openclaw/openclaw.json")
    bin_dir = os.path.join(workspace, "home/node/.openclaw/bin")

    # ── Load config for reference ──────────────────────────────────────────────
    try:
        with open(config_path) as f:
            config = json.load(f)
        channels = config.get("channels", {})
        supported = {"imsg", "remindctl", "memo", "things", "peekaboo"}
        enabled_tools = {t for t, v in channels.items() if t in supported and v.get("enabled", False)}
        disabled_tools = {t for t, v in channels.items() if t in supported and not v.get("enabled", False)}
        wol_map = config.get("wol", {})
    except Exception as e:
        checks.append({"name": "config_readable", "passed": False,
                        "detail": f"Could not read openclaw.json: {e}"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append({"name": "config_readable", "passed": True, "detail": "openclaw.json parsed OK"})

    # ── CHECK 1: render-tool-map.sh was called with the config ────────────────
    render_called = ("render-tool-map CALLED" in audit and
                     "openclaw.json" in audit)
    checks.append({
        "name": "render_tool_map_called",
        "passed": render_called,
        "detail": ("render-tool-map.sh was invoked with openclaw.json"
                   if render_called else
                   "render-tool-map.sh was NOT called or config path missing from audit log")
    })

    # ── CHECK 2: install-macos-pack.sh was called ─────────────────────────────
    install_called = "install-macos-pack CALLED" in audit
    checks.append({
        "name": "install_macos_pack_called",
        "passed": install_called,
        "detail": ("install-macos-pack.sh was invoked"
                   if install_called else
                   "install-macos-pack.sh was NOT called")
    })

    # ── CHECK 3: --target-dir points to the correct bin dir ──────────────────
    target_dir_ok = False
    try:
        m = re.search(r"TARGET_DIR=([^\n]+)", audit)
        if m:
            td = m.group(1).strip()
            # Accept either absolute or workspace-relative path resolving to same location
            target_dir_ok = (
                td.endswith("home/node/.openclaw/bin") or
                td == bin_dir
            )
    except Exception:
        pass
    checks.append({
        "name": "target_dir_correct",
        "passed": target_dir_ok,
        "detail": (f"--target-dir correctly set to .openclaw/bin"
                   if target_dir_ok else
                   "--target-dir not set to /home/node/.openclaw/bin in audit log")
    })

    # ── CHECK 4: --openclaw-config passed to install-macos-pack.sh ───────────
    oc_in_install = False
    try:
        install_block_match = re.search(
            r"install-macos-pack CALLED(.*?)(?=install-macos-pack CALLED|verify-macos-pack CALLED|$)",
            audit, re.DOTALL
        )
        if install_block_match:
            block = install_block_match.group(1)
            oc_in_install = "OPENCLAW_CONFIG=" in block and "openclaw.json" in block
    except Exception:
        pass
    checks.append({
        "name": "openclaw_config_in_install",
        "passed": oc_in_install,
        "detail": ("--openclaw-config correctly passed to install-macos-pack.sh"
                   if oc_in_install else
                   "--openclaw-config NOT found in install-macos-pack audit block")
    })

    # ── CHECK 5: --tool and --map NOT passed (auto-discovery mode) ────────────
    no_tool_override = False
    no_map_override = False
    try:
        install_block_match = re.search(
            r"install-macos-pack CALLED(.*?)(?=install-macos-pack CALLED|verify-macos-pack CALLED|$)",
            audit, re.DOTALL
        )
        if install_block_match:
            block = install_block_match.group(1)
            tool_line = re.search(r"TOOL_OVERRIDE=([^\n]*)", block)
            map_line = re.search(r"MAP_OVERRIDE=([^\n]*)", block)
            no_tool_override = (tool_line is None or tool_line.group(1).strip() == "")
            no_map_override = (map_line is None or map_line.group(1).strip() == "")
    except Exception:
        pass
    checks.append({
        "name": "no_tool_override",
        "passed": no_tool_override,
        "detail": ("--tool correctly omitted (auto-discovery)"
                   if no_tool_override else
                   "--tool was explicitly passed; should be omitted for auto-discovery")
    })
    checks.append({
        "name": "no_map_override",
        "passed": no_map_override,
        "detail": ("--map correctly omitted (auto-discovery)"
                   if no_map_override else
                   "--map was explicitly passed; should be omitted for auto-discovery")
    })

    # ── CHECK 6: --default-host set ────────────────────────────────────────────
    default_host_set = False
    try:
        install_block_match = re.search(
            r"install-macos-pack CALLED(.*?)(?=install-macos-pack CALLED|verify-macos-pack CALLED|$)",
            audit, re.DOTALL
        )
        if install_block_match:
            block = install_block_match.group(1)
            dh_line = re.search(r"DEFAULT_HOST=([^\n]+)", block)
            if dh_line:
                dh = dh_line.group(1).strip()
                default_host_set = len(dh) > 0 and "@" in dh
    except Exception:
        pass
    checks.append({
        "name": "default_host_set",
        "passed": default_host_set,
        "detail": ("--default-host provided with user@host format"
                   if default_host_set else
                   "--default-host missing or malformed in install-macos-pack audit block")
    })

    # ── CHECK 7: --wake-map set with correct WoL MAC from config ──────────────
    wake_map_set = False
    try:
        install_block_match = re.search(
            r"install-macos-pack CALLED(.*?)(?=install-macos-pack CALLED|verify-macos-pack CALLED|$)",
            audit, re.DOTALL
        )
        if install_block_match:
            block = install_block_match.group(1)
            wm_line = re.search(r"WAKE_MAP=([^\n]+)", block)
            if wm_line:
                wm = wm_line.group(1).strip()
                # Must contain the MAC from config
                expected_mac = list(wol_map.values())[0]  # AA:BB:CC:DD:EE:FF
                expected_node = list(wol_map.keys())[0]    # mac-node.local
                wake_map_set = expected_mac in wm and expected_node in wm
    except Exception:
        pass
    checks.append({
        "name": "wake_map_correct",
        "passed": wake_map_set,
        "detail": ("--wake-map contains correct node=MAC from config wol section"
                   if wake_map_set else
                   "--wake-map missing or does not contain mac-node.local=AA:BB:CC:DD:EE:FF")
    })

    # ── CHECK 8: --wake-wait and --wake-retries set ───────────────────────────
    wake_wait_set = False
    wake_retries_set = False
    try:
        install_block_match = re.search(
            r"install-macos-pack CALLED(.*?)(?=install-macos-pack CALLED|verify-macos-pack CALLED|$)",
            audit, re.DOTALL
        )
        if install_block_match:
            block = install_block_match.group(1)
            ww_line = re.search(r"WAKE_WAIT=([^\n]+)", block)
            wr_line = re.search(r"WAKE_RETRIES=([^\n]+)", block)
            if ww_line:
                wake_wait_set = ww_line.group(1).strip().isdigit()
            if wr_line:
                wake_retries_set = wr_line.group(1).strip().isdigit()
    except Exception:
        pass
    checks.append({
        "name": "wake_wait_set",
        "passed": wake_wait_set,
        "detail": ("--wake-wait set to a numeric value"
                   if wake_wait_set else
                   "--wake-wait missing or non-numeric in install-macos-pack audit block")
    })
    checks.append({
        "name": "wake_retries_set",
        "passed": wake_retries_set,
        "detail": ("--wake-retries set to a numeric value"
                   if wake_retries_set else
                   "--wake-retries missing or non-numeric in install-macos-pack audit block")
    })

    # ── CHECK 9: enabled tool wrappers exist and are executable ───────────────
    enabled_wrappers_ok = True
    missing_enabled = []
    for tool in enabled_tools:
        wrapper = os.path.join(bin_dir, tool)
        if not os.path.isfile(wrapper) or not os.access(wrapper, os.X_OK):
            enabled_wrappers_ok = False
            missing_enabled.append(tool)

    checks.append({
        "name": "enabled_wrappers_installed",
        "passed": enabled_wrappers_ok,
        "detail": (f"All enabled tools {sorted(enabled_tools)} have executable wrappers"
                   if enabled_wrappers_ok else
                   f"Missing/non-executable wrappers for: {missing_enabled}")
    })

    # ── CHECK 10: disabled tool wrappers do NOT exist ─────────────────────────
    disabled_absent_ok = True
    present_disabled = []
    for tool in disabled_tools:
        wrapper = os.path.join(bin_dir, tool)
        if os.path.exists(wrapper):
            disabled_absent_ok = False
            present_disabled.append(tool)

    checks.append({
        "name": "disabled_wrappers_absent",
        "passed": disabled_absent_ok,
        "detail": (f"Disabled tools {sorted(disabled_tools)} correctly have no wrappers"
                   if disabled_absent_ok else
                   f"Disabled tools with wrappers (should not exist): {present_disabled}")
    })

    # ── CHECK 11: wrapper content includes SSH call for enabled tools ─────────
    ssh_content_ok = True
    bad_wrappers = []
    for tool in enabled_tools:
        wrapper = os.path.join(bin_dir, tool)
        try:
            with open(wrapper) as f:
                content = f.read()
            if "ssh" not in content:
                ssh_content_ok = False
                bad_wrappers.append(tool)
        except Exception:
            ssh_content_ok = False
            bad_wrappers.append(tool)

    checks.append({
        "name": "wrapper_contains_ssh",
        "passed": ssh_content_ok,
        "detail": (f"All enabled wrappers contain SSH invocation"
                   if ssh_content_ok else
                   f"Wrappers missing SSH: {bad_wrappers}")
    })

    # ── CHECK 12: verify-macos-pack.sh called with --openclaw-config ──────────
    verify_called_with_config = False
    try:
        verify_match = re.search(
            r"verify-macos-pack CALLED(.*?)(?=verify-macos-pack CALLED|$)",
            audit, re.DOTALL
        )
        if verify_match:
            block = verify_match.group(1)
            oc_line = re.search(r"OPENCLAW_CONFIG=([^\n]+)", block)
            td_line = re.search(r"TARGET_DIR=([^\n]+)", block)
            if oc_line and td_line:
                oc_val = oc_line.group(1).strip()
                td_val = td_line.group(1).strip()
                verify_called_with_config = (
                    "openclaw.json" in oc_val and
                    (td_val.endswith("home/node/.openclaw/bin") or td_val == bin_dir)
                )
    except Exception:
        pass
    checks.append({
        "name": "verify_called_with_openclaw_config",
        "passed": verify_called_with_config,
        "detail": ("verify-macos-pack.sh called with --openclaw-config and --target-dir"
                   if verify_called_with_config else
                   "verify-macos-pack.sh NOT called correctly (missing --openclaw-config or wrong --target-dir)")
    })

    # ── Scoring ───────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    overall = all(c["passed"] for c in checks)

    result = {
        "passed": overall,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()