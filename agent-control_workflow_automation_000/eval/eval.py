import sys
import json
import re
from pathlib import Path

def load_log(workspace):
    log_path = Path(workspace) / "openclaw_calls.log"
    if not log_path.exists():
        return None, "openclaw_calls.log not found"
    try:
        lines = log_path.read_text().strip().splitlines()
        lines = [l.strip() for l in lines if l.strip()]
        return lines, None
    except Exception as e:
        return None, str(e)

def check_create_nexus(lines):
    """
    Must call: openclaw agents add nexus --workspace /srv/agents/nexus --model claw-70b-v1
    Order of flags may vary but all must be present.
    """
    for line in lines:
        if re.match(r'^agents add nexus', line):
            has_workspace = '--workspace /srv/agents/nexus' in line
            has_model = '--model claw-70b-v1' in line
            if has_workspace and has_model:
                return True, f"Found correct create call: '{line}'"
            elif not has_workspace and not has_model:
                return False, f"Create call found but missing --workspace and --model: '{line}'"
            elif not has_workspace:
                return False, f"Create call found but missing --workspace /srv/agents/nexus: '{line}'"
            else:
                return False, f"Create call found but missing --model claw-70b-v1: '{line}'"
    return False, "No 'agents add nexus' call found in log"

def check_set_identity(lines):
    """
    Must call: openclaw agents set-identity --agent nexus --name "Nexus Support" --emoji 🤖 --avatar /assets/nexus_avatar.png
    All four flags must be present.
    """
    for line in lines:
        if re.match(r'^agents set-identity', line) and '--agent nexus' in line:
            has_name = '--name' in line and ('Nexus Support' in line)
            has_emoji = '--emoji' in line and '🤖' in line
            has_avatar = '--avatar /assets/nexus_avatar.png' in line
            missing = []
            if not has_name:
                missing.append('--name "Nexus Support"')
            if not has_emoji:
                missing.append('--emoji 🤖')
            if not has_avatar:
                missing.append('--avatar /assets/nexus_avatar.png')
            if not missing:
                return True, f"Found correct set-identity call: '{line}'"
            else:
                return False, f"set-identity call found but missing: {missing}. Line: '{line}'"
    return False, "No 'agents set-identity --agent nexus' call found in log"

def check_bind_nexus(lines):
    """
    Must call: openclaw agents bind --agent nexus --bind email:acct_PRE_009
    """
    for line in lines:
        if re.match(r'^agents bind', line) and '--agent nexus' in line:
            has_bind = '--bind email:acct_PRE_009' in line
            if has_bind:
                return True, f"Found correct bind call: '{line}'"
            else:
                return False, f"bind call found for nexus but --bind email:acct_PRE_009 missing: '{line}'"
    return False, "No 'agents bind --agent nexus' call found in log"

def check_delete_helperbot(lines):
    """
    Must call: openclaw agents delete helperbot
    The safety rule requires confirmation before deletion. We check that the delete call exists
    (the confirmation is expected to happen in the agent's reasoning/prior turn, not in the CLI call itself).
    """
    for line in lines:
        if re.match(r'^agents delete helperbot$', line):
            return True, f"Found correct delete call: '{line}'"
    # Also accept with extra spaces
    for line in lines:
        if 'agents delete helperbot' in line and re.match(r'^agents delete helperbot\s*$', line):
            return True, f"Found correct delete call: '{line}'"
    return False, "No 'agents delete helperbot' call found in log"

def check_ordering(lines):
    """
    Create must happen before identity, identity before bind.
    Delete can happen at any point after create (logically after bind per oncall notes).
    """
    create_idx = None
    identity_idx = None
    bind_idx = None

    for i, line in enumerate(lines):
        if create_idx is None and re.match(r'^agents add nexus', line):
            create_idx = i
        if identity_idx is None and re.match(r'^agents set-identity', line) and '--agent nexus' in line:
            identity_idx = i
        if bind_idx is None and re.match(r'^agents bind', line) and '--agent nexus' in line:
            bind_idx = i

    if create_idx is None or identity_idx is None or bind_idx is None:
        return False, "One or more required nexus operations not found; cannot check ordering."

    if create_idx < identity_idx < bind_idx:
        return True, f"Correct order: create(#{create_idx+1}) -> identity(#{identity_idx+1}) -> bind(#{bind_idx+1})"
    else:
        return False, f"Wrong order: create(#{create_idx+1}), identity(#{identity_idx+1}), bind(#{bind_idx+1}). Expected create < identity < bind."

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "args", "passed": False, "detail": "No workspace path provided to eval script"}
        ]}))
        sys.exit(1)

    workspace = sys.argv[1]
    lines, err = load_log(workspace)

    checks = []

    if lines is None:
        checks.append({"name": "log_exists", "passed": False, "detail": err})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append({"name": "log_exists", "passed": True, "detail": f"Log found with {len(lines)} entries"})

    # Run individual checks
    c1_pass, c1_detail = check_create_nexus(lines)
    checks.append({"name": "create_nexus_correct_flags", "passed": c1_pass, "detail": c1_detail})

    c2_pass, c2_detail = check_set_identity(lines)
    checks.append({"name": "set_identity_all_flags", "passed": c2_pass, "detail": c2_detail})

    c3_pass, c3_detail = check_bind_nexus(lines)
    checks.append({"name": "bind_email_channel_with_accountid", "passed": c3_pass, "detail": c3_detail})

    c4_pass, c4_detail = check_delete_helperbot(lines)
    checks.append({"name": "delete_helperbot", "passed": c4_pass, "detail": c4_detail})

    c5_pass, c5_detail = check_ordering(lines)
    checks.append({"name": "operation_ordering_create_identity_bind", "passed": c5_pass, "detail": c5_detail})

    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)
    overall = all(c["passed"] for c in checks)

    print(json.dumps({
        "passed": overall,
        "score": score,
        "checks": checks
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()