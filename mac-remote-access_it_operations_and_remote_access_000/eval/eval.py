#!/usr/bin/env python3
"""
Evaluation script for the mac-remote-access runbook task.
Usage: python3 eval_script.py /workspace
"""

import sys
import json
import re
from pathlib import Path

def find_file(workspace: Path, filename: str) -> Path | None:
    matches = list(workspace.rglob(filename))
    return matches[0] if matches else None

def evaluate(workspace_dir: str) -> dict:
    workspace = Path(workspace_dir)
    checks = []
    total = 0
    passed_count = 0

    # ─────────────────────────────────────────────────────────────────────────
    # ARTIFACT A: recovery_runbook.md
    # ─────────────────────────────────────────────────────────────────────────
    runbook_path = find_file(workspace, "recovery_runbook.md")

    def rb_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    if runbook_path is None:
        rb_check("runbook_exists", False, "recovery_runbook.md not found anywhere in workspace")
        runbook_text = ""
    else:
        runbook_text = runbook_path.read_text(errors="replace").lower()
        rb_check("runbook_exists", True, f"Found at {runbook_path.relative_to(workspace)}")

    # Check 1 — Correct diagnosis: 22=True, 5900=False → Mac Screen Sharing / VNC service problem
    # Agent must NOT say "check ACL" for this scenario (that would be wrong per skill)
    diagnosis_correct = bool(
        re.search(r"(screen.sharing|vnc.service|screensharing)", runbook_text)
        and re.search(r"(port.22.*true|ssh.*true|22.*succeed|ssh.*work|22.*pass|22.*open)", runbook_text)
        and re.search(r"(port.5900.*false|5900.*fail|5900.*timeout|5900.*closed|vnc.*fail|display.*fail)", runbook_text)
    )
    rb_check(
        "correct_diagnosis_22_true_5900_false",
        diagnosis_correct,
        "Runbook must identify the symptom as: SSH/22 works, VNC/5900 fails → Mac Screen Sharing service issue (NOT an ACL problem)" if not diagnosis_correct else "Correct diagnosis found"
    )

    # Check 2 — Must include the exact kickstart command for com.apple.screensharing
    kickstart_cmd = "sudo launchctl kickstart -k system/com.apple.screensharing"
    has_kickstart = kickstart_cmd in runbook_path.read_text(errors="replace") if runbook_path else False
    rb_check(
        "screensharing_kickstart_command",
        has_kickstart,
        f"Must include exact command: `{kickstart_cmd}`" if not has_kickstart else "Kickstart command found"
    )

    # Check 3 — Must include Mac-side diagnostic commands (at least 3 of the 5 from SKILL.md)
    raw_runbook = runbook_path.read_text(errors="replace") if runbook_path else ""
    mac_cmds = [
        "tailscale status",
        "tailscale ip -4",
        "systemsetup -getremotelogin",
        "netstat",
        "5900",
    ]
    found_cmds = [c for c in mac_cmds if c in raw_runbook]
    has_mac_cmds = len(found_cmds) >= 3
    rb_check(
        "mac_side_diagnostic_commands",
        has_mac_cmds,
        f"Found {len(found_cmds)}/5 expected mac-side commands: {found_cmds}" if not has_mac_cmds else f"Mac-side commands present: {found_cmds}"
    )

    # Check 4 — Correct layer priority: SSH first, AnyDesk second (primary), VNC third (secondary)
    # Must preserve the skill's specific ordering: SSH fallback > AnyDesk primary > VNC secondary
    ssh_pos = runbook_text.find("ssh")
    anydesk_pos = runbook_text.find("anydesk")
    vnc_pos_candidates = [runbook_text.find("vnc"), runbook_text.find("screen sharing")]
    vnc_pos = min([p for p in vnc_pos_candidates if p >= 0], default=-1)

    layering_correct = (
        ssh_pos != -1
        and anydesk_pos != -1
        and vnc_pos != -1
        and ssh_pos < anydesk_pos
        and anydesk_pos < vnc_pos
    )
    # Also check that AnyDesk is called "primary" and VNC "secondary"
    anydesk_primary = bool(re.search(r"anydesk.{0,60}(primary|first|gui.fallback|main)", runbook_text))
    vnc_secondary = bool(re.search(r"(vnc|screen.sharing).{0,60}(secondary|second|fallback)", runbook_text))

    layering_full = layering_correct and (anydesk_primary or vnc_secondary)
    rb_check(
        "layered_access_stack_priority_order",
        layering_full,
        "Runbook must document: SSH (fallback) → AnyDesk (primary GUI) → VNC (secondary GUI) in that order" if not layering_full else "Correct layered access stack order found"
    )

    # Check 5 — Must NOT recommend fixing ACL as solution for this specific symptom
    # Per skill: 22=True,5900=False → check Mac service, NOT ACL
    false_acl_advice = bool(re.search(
        r"(fix|update|change|edit|modify).{0,40}acl.{0,40}(to fix|resolve|solve|this issue|the problem|5900|vnc)",
        runbook_text
    ))
    rb_check(
        "no_incorrect_acl_fix_for_this_scenario",
        not false_acl_advice,
        "Runbook incorrectly recommends fixing ACL for a 22=True/5900=False symptom — skill says this means Mac service issue" if false_acl_advice else "Correctly avoids blaming ACL for this symptom"
    )

    # ─────────────────────────────────────────────────────────────────────────
    # ARTIFACT B: tailscale_acl.json
    # ─────────────────────────────────────────────────────────────────────────
    acl_path = find_file(workspace, "tailscale_acl.json")

    def acl_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    if acl_path is None:
        acl_check("acl_file_exists", False, "tailscale_acl.json not found anywhere in workspace")
        acl_data = None
    else:
        acl_check("acl_file_exists", True, f"Found at {acl_path.relative_to(workspace)}")
        try:
            acl_data = json.loads(acl_path.read_text())
        except json.JSONDecodeError as e:
            acl_check("acl_valid_json", False, f"Invalid JSON: {e}")
            acl_data = None

    if acl_data is not None:
        acl_check("acl_valid_json", True, "Valid JSON")

        # Check 6 — Must use "acls" array with "action": "accept"
        acls = acl_data.get("acls", [])
        has_accept = any(
            isinstance(r, dict) and r.get("action") == "accept"
            for r in acls
        ) if acls else False
        acl_check(
            "acl_has_accept_rule",
            has_accept,
            "ACL must contain at least one rule with \"action\": \"accept\"" if not has_accept else "Accept rule found"
        )

        # Check 7 — Must use tag:windows-client as src and tag:mac-host as dst (tag-based, not raw CIDRs)
        src_tags_ok = False
        dst_tags_ok = False
        dst_has_port22 = False
        dst_has_port5900 = False
        for rule in acls:
            if not isinstance(rule, dict):
                continue
            src = rule.get("src", [])
            dst = rule.get("dst", [])
            if any("tag:windows-client" in s for s in src):
                src_tags_ok = True
            if any("tag:mac-host" in d for d in dst):
                dst_tags_ok = True
            if any("tag:mac-host:22" in d for d in dst):
                dst_has_port22 = True
            if any("tag:mac-host:5900" in d for d in dst):
                dst_has_port5900 = True

        acl_check(
            "acl_uses_tag_based_src",
            src_tags_ok,
            "ACL src must use tag:windows-client (not raw IPs)" if not src_tags_ok else "Correct src tag found"
        )
        acl_check(
            "acl_uses_tag_based_dst",
            dst_tags_ok,
            "ACL dst must reference tag:mac-host (not raw IPs)" if not dst_tags_ok else "Correct dst tag found"
        )
        acl_check(
            "acl_dst_includes_port_22",
            dst_has_port22,
            "ACL dst must include tag:mac-host:22 (SSH must always be preserved)" if not dst_has_port22 else "Port 22 in dst"
        )
        acl_check(
            "acl_dst_includes_port_5900",
            dst_has_port5900,
            "ACL dst must include tag:mac-host:5900 (VNC port)" if not dst_has_port5900 else "Port 5900 in dst"
        )

        # Check 8 — Must include tagOwners with autogroup:admin for both tags
        tag_owners = acl_data.get("tagOwners", {})
        tw_windows = "tag:windows-client" in tag_owners and "autogroup:admin" in str(tag_owners.get("tag:windows-client", []))
        tw_mac = "tag:mac-host" in tag_owners and "autogroup:admin" in str(tag_owners.get("tag:mac-host", []))
        acl_check(
            "acl_tagowners_correct",
            tw_windows and tw_mac,
            f"tagOwners must map tag:windows-client and tag:mac-host both to autogroup:admin. windows_ok={tw_windows}, mac_ok={tw_mac}" if not (tw_windows and tw_mac) else "tagOwners correct"
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Scoring
    # ─────────────────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    overall_passed = (score >= 0.80)  # must pass ≥80% of checks

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2))