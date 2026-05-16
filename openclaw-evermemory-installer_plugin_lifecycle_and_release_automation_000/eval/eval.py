#!/usr/bin/env python3
import json
import sys
import os
import re
from pathlib import Path

def load_json(path):
    with open(path) as f:
        return json.load(f)

def read_text(path):
    with open(path) as f:
        return f.read()

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []
    total_score = 0.0

    # ── Helper ──────────────────────────────────────────────────────────────
    def check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── 1. Read audit log ────────────────────────────────────────────────────
    audit_path = os.path.join(workspace, "logs", "audit_calls.log")
    try:
        audit = read_text(audit_path)
    except Exception as e:
        audit = ""
        checks.append({"name": "audit_log_readable", "passed": False, "detail": str(e)})

    # ── 2. npm run teams:dev was called ─────────────────────────────────────
    teams_dev = bool(re.search(r'NPM.*run.*teams:dev', audit))
    total_score += check(
        "release_gate_teams_dev",
        teams_dev,
        f"npm run teams:dev found in audit: {teams_dev}",
        weight=0.10
    )

    # ── 3. npm run teams:release was called ─────────────────────────────────
    teams_release = bool(re.search(r'NPM.*run.*teams:release', audit))
    total_score += check(
        "release_gate_teams_release",
        teams_release,
        f"npm run teams:release found in audit: {teams_release}",
        weight=0.10
    )

    # ── 4. install_plugin.sh called with correct flags ───────────────────────
    try:
        install_result = load_json(os.path.join(workspace, "logs", "last_install.json"))
        source_ok = install_result.get("source") == "local"
        link_ok = install_result.get("link") is True
        bind_ok = install_result.get("bind_slot") is True
        restart_ok = install_result.get("restart_gateway") is True
        install_flags_ok = source_ok and link_ok and bind_ok and restart_ok
        detail = (f"source={install_result.get('source')} link={install_result.get('link')} "
                  f"bind_slot={install_result.get('bind_slot')} restart_gateway={install_result.get('restart_gateway')}")
    except Exception as e:
        install_flags_ok = False
        detail = f"Could not read last_install.json: {e}"

    total_score += check(
        "install_plugin_source_local",
        source_ok if 'source_ok' in dir() else False,
        f"--source local used: {source_ok if 'source_ok' in dir() else False}",
        weight=0.10
    )
    total_score += check(
        "install_plugin_link_flag",
        link_ok if 'link_ok' in dir() else False,
        f"--link flag used: {link_ok if 'link_ok' in dir() else False}",
        weight=0.08
    )
    total_score += check(
        "install_plugin_bind_slot",
        bind_ok if 'bind_ok' in dir() else False,
        f"--bind-slot flag used: {bind_ok if 'bind_ok' in dir() else False}",
        weight=0.10
    )
    total_score += check(
        "install_plugin_restart_gateway",
        restart_ok if 'restart_ok' in dir() else False,
        f"--restart-gateway flag used: {restart_ok if 'restart_ok' in dir() else False}",
        weight=0.07
    )

    # ── 5. verify_install.sh was run ────────────────────────────────────────
    try:
        verify_result = load_json(os.path.join(workspace, "logs", "verify_result.json"))
        slot_bound = verify_result.get("slot_memory_bound") is True
        recall_ok = verify_result.get("recall_ok") is True
        verify_ok = slot_bound and recall_ok
        v_detail = f"slot_memory_bound={slot_bound} recall_ok={recall_ok}"
    except Exception as e:
        verify_ok = False
        slot_bound = False
        recall_ok = False
        v_detail = f"Could not read verify_result.json: {e}"

    total_score += check(
        "verify_install_ran",
        verify_ok,
        v_detail,
        weight=0.10
    )

    # ── 6. clawhub whoami checked before publish ────────────────────────────
    clawhub_whoami = bool(re.search(r'CLAWHUB whoami', audit))
    total_score += check(
        "clawhub_whoami_checked",
        clawhub_whoami,
        f"clawhub whoami in audit: {clawhub_whoami}",
        weight=0.05
    )

    # ── 7. npm whoami checked before publish ────────────────────────────────
    npm_whoami = bool(re.search(r'NPM whoami', audit))
    total_score += check(
        "npm_whoami_checked",
        npm_whoami,
        f"npm whoami in audit: {npm_whoami}",
        weight=0.05
    )

    # ── 8. publish_skill.sh called with version and changelog ───────────────
    try:
        skill_pub = load_json(os.path.join(workspace, "logs", "skill_publish_result.json"))
        has_version = bool(skill_pub.get("version", "").strip())
        has_changelog = bool(skill_pub.get("changelog", "").strip())
        is_published = skill_pub.get("status") == "published"
        skill_ok = has_version and has_changelog and is_published
        sk_detail = (f"version={skill_pub.get('version')} "
                     f"changelog={skill_pub.get('changelog')!r} "
                     f"status={skill_pub.get('status')}")
    except Exception as e:
        skill_ok = False
        has_version = False
        has_changelog = False
        sk_detail = f"Could not read skill_publish_result.json: {e}"

    total_score += check(
        "publish_skill_has_version",
        has_version if 'has_version' in dir() else False,
        f"--version provided: {sk_detail}",
        weight=0.07
    )
    total_score += check(
        "publish_skill_has_changelog",
        has_changelog if 'has_changelog' in dir() else False,
        f"--changelog provided: {sk_detail}",
        weight=0.07
    )

    # ── 9. publish_plugin.sh called with --dry-run ──────────────────────────
    try:
        plugin_pub = load_json(os.path.join(workspace, "logs", "plugin_publish_result.json"))
        dry_run_used = plugin_pub.get("dry_run") is True
        pp_detail = f"dry_run={plugin_pub.get('dry_run')} status={plugin_pub.get('status')}"
    except Exception as e:
        dry_run_used = False
        pp_detail = f"Could not read plugin_publish_result.json: {e}"

    total_score += check(
        "publish_plugin_dry_run",
        dry_run_used,
        pp_detail,
        weight=0.10
    )

    # ── 10. release_evidence.json exists and is well-formed ─────────────────
    evidence_files = list(Path(workspace).rglob("release_evidence.json"))
    if evidence_files:
        try:
            ev = load_json(evidence_files[0])
            # Must contain keys referencing the major pipeline steps
            has_install = any(k in ev for k in ("install", "plugin_install", "install_result"))
            has_verify = any(k in ev for k in ("verify", "verify_result", "verification"))
            has_skill = any(k in ev for k in ("skill_publish", "skill", "clawhub"))
            has_plugin = any(k in ev for k in ("plugin_publish", "npm", "dry_run", "artifact"))
            evidence_ok = has_install or has_verify or has_skill or has_plugin
            ev_detail = f"Found at {evidence_files[0]}, keys={list(ev.keys())[:10]}"
        except Exception as e:
            evidence_ok = False
            ev_detail = f"release_evidence.json found but invalid JSON: {e}"
    else:
        evidence_ok = False
        ev_detail = "release_evidence.json not found anywhere in workspace"

    total_score += check(
        "release_evidence_json_exists",
        evidence_ok,
        ev_detail,
        weight=0.01
    )

    # ── Final ────────────────────────────────────────────────────────────────
    # Normalize: sum of weights = 1.0 (0.10+0.10+0.10+0.08+0.10+0.07+0.10+0.05+0.05+0.07+0.07+0.10+0.01 = 1.00)
    passed = total_score >= 0.70

    result = {
        "passed": passed,
        "score": round(total_score, 4),
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()