#!/usr/bin/env python3
"""
Generates the sandbox workspace for the codex-account-switcher evaluation task.
"""

import os
import json
import base64
import time
import random
import pathlib

random.seed(42)

HOME = pathlib.Path(os.path.expanduser("~"))
WORKSPACE = pathlib.Path("/workspace")

# ─────────────────────────────────────────────────────────────
# Helper: build a minimal fake JWT (header.payload.signature)
# ─────────────────────────────────────────────────────────────
def make_jwt(email: str, user_id: str, iat: int = 1700000000, exp: int = 1800000000) -> str:
    header = base64.urlsafe_b64encode(
        json.dumps({"alg": "RS256", "typ": "JWT"}).encode()
    ).rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(
        json.dumps({
            "email": email,
            "sub": user_id,
            "iat": iat,
            "exp": exp,
            "aud": "https://api.openai.com/v1",
            "iss": "https://auth.openai.com",
        }).encode()
    ).rstrip(b"=").decode()
    signature = base64.urlsafe_b64encode(
        f"fakesig_{email}".encode()
    ).rstrip(b"=").decode()
    return f"{header}.{payload}.{signature}"


# ─────────────────────────────────────────────────────────────
# Account data
# ─────────────────────────────────────────────────────────────
ACCOUNTS = {
    "oliver": {
        "email": "oliver@drobnik.com",
        "user_id": "user-UtCmyIUOTxc4D1OHV1e5Ibew",
        "iat": 1700001000,
        "exp": 1800001000,
    },
    "elise": {
        "email": "elise@drobnik.com",
        "user_id": "user-KpQnHzRaM9bXsLtJwFcYeVkD",
        "iat": 1700002000,
        "exp": 1800002000,
    },
    "sylvia": {
        "email": "sylvia@drobnik.com",
        "user_id": "user-NrTgWoBfU7mCiEsZvXyDqAlP",
        "iat": 1700003000,
        "exp": 1800003000,
    },
}

def make_auth_json(account_name: str) -> dict:
    a = ACCOUNTS[account_name]
    jwt = make_jwt(a["email"], a["user_id"], a["iat"], a["exp"])
    return {
        "id_token": jwt,
        "access_token": f"sk-fake-access-{account_name}-{''.join(random.choices('abcdefABCDEF0123456789', k=24))}",
        "refresh_token": f"rt-fake-refresh-{account_name}-{''.join(random.choices('abcdefABCDEF0123456789', k=32))}",
        "expires_at": a["exp"],
        "account_id": a["user_id"],
        "email": a["email"],
    }


# ─────────────────────────────────────────────────────────────
# Create ~/.codex directory structure
# ─────────────────────────────────────────────────────────────
codex_dir = HOME / ".codex"
codex_accounts_dir = codex_dir / "accounts"
codex_accounts_dir.mkdir(parents=True, exist_ok=True)

# Active account = oliver
active_auth = make_auth_json("oliver")
(codex_dir / "auth.json").write_text(json.dumps(active_auth, indent=2))

# Save all three accounts
account_data = {}
for name in ACCOUNTS:
    data = make_auth_json(name)
    account_data[name] = data
    (codex_accounts_dir / f"{name}.json").write_text(json.dumps(data, indent=2))

# Existing activity log (some old entries)
activity_log = codex_dir / "account-activity.jsonl"
old_entries = [
    {"timestamp": 1774800000, "account": "oliver", "user_id": ACCOUNTS["oliver"]["user_id"]},
    {"timestamp": 1774820000, "account": "sylvia", "user_id": ACCOUNTS["sylvia"]["user_id"]},
    {"timestamp": 1774850000, "account": "oliver", "user_id": ACCOUNTS["oliver"]["user_id"]},
]
activity_log.write_text("\n".join(json.dumps(e) for e in old_entries) + "\n")


# ─────────────────────────────────────────────────────────────
# Create ~/.openclaw directory structure (two agents)
# ─────────────────────────────────────────────────────────────
openclaw_dir = HOME / ".openclaw"
agents = ["agent-alpha", "agent-beta"]

for agent in agents:
    agent_dir = openclaw_dir / "agents" / agent / "agent"
    agent_dir.mkdir(parents=True, exist_ok=True)

    # Stale auth-profiles.json with OLD name-based keys (should be migrated)
    stale_profiles = {
        "openai-codex:oliver": {
            "type": "oauth",
            "provider": "openai-codex",
            "access": "sk-old-access-oliver",
            "refresh": "rt-old-refresh-oliver",
            "expires": 1600000000,
            "accountId": ACCOUNTS["oliver"]["user_id"],
            "email": ACCOUNTS["oliver"]["email"],
        },
        "openai-codex:sylvia": {
            "type": "oauth",
            "provider": "openai-codex",
            "access": "sk-old-access-sylvia",
            "refresh": "rt-old-refresh-sylvia",
            "expires": 1600000001,
            "accountId": ACCOUNTS["sylvia"]["user_id"],
            "email": ACCOUNTS["sylvia"]["email"],
        },
        "github:someuser": {
            "type": "oauth",
            "provider": "github",
            "access": "gh-token-abc123",
            "refresh": "",
            "expires": 9999999999,
            "accountId": "gh-user-42",
            "email": "someuser@example.com",
        },
    }
    (agent_dir / "auth-profiles.json").write_text(json.dumps(stale_profiles, indent=2))

    # Also create a stale auth.json for the agent
    stale_agent_auth = {
        "provider": "openai-codex",
        "access": "sk-old-access-oliver",
        "email": ACCOUNTS["oliver"]["email"],
    }
    (agent_dir / "auth.json").write_text(json.dumps(stale_agent_auth, indent=2))


# ─────────────────────────────────────────────────────────────
# Create the skill script at a realistic path
# ─────────────────────────────────────────────────────────────
skill_base = HOME / "skills" / "codex-account-switcher"
scripts_dir = skill_base / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

# Write the actual codex-accounts.py implementation
CODEX_ACCOUNTS_SCRIPT = r'''#!/usr/bin/env python3
"""
Codex Account Switcher - manages multiple OpenAI Codex identities.
"""

import argparse
import base64
import json
import os
import pathlib
import sys
import time
import re

HOME = pathlib.Path(os.path.expanduser("~"))
CODEX_DIR = HOME / ".codex"
ACCOUNTS_DIR = CODEX_DIR / "accounts"
AUTH_JSON = CODEX_DIR / "auth.json"
ACTIVITY_LOG = CODEX_DIR / "account-activity.jsonl"
OPENCLAW_AGENTS_GLOB = HOME / ".openclaw" / "agents"


def decode_jwt_payload(token: str) -> dict:
    """Decode JWT payload (no verification)."""
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError(f"Invalid JWT: {token[:40]}")
    payload_b64 = parts[1]
    # Add padding
    padded = payload_b64 + "=" * (4 - len(payload_b64) % 4)
    payload_bytes = base64.urlsafe_b64decode(padded)
    return json.loads(payload_bytes)


def load_account(name: str) -> dict:
    path = ACCOUNTS_DIR / f"{name}.json"
    if not path.exists():
        print(f"Error: Account '{name}' not found.", file=sys.stderr)
        sys.exit(1)
    return json.loads(path.read_text())


def list_accounts(verbose: bool = False, as_json: bool = False):
    ACCOUNTS_DIR.mkdir(parents=True, exist_ok=True)
    accounts = []
    for f in sorted(ACCOUNTS_DIR.glob("*.json")):
        name = f.stem
        data = json.loads(f.read_text())
        entry = {"name": name, "email": data.get("email", "unknown")}
        # Check if active
        if AUTH_JSON.exists():
            active = json.loads(AUTH_JSON.read_text())
            entry["active"] = active.get("email") == data.get("email")
        else:
            entry["active"] = False
        accounts.append(entry)
    if as_json:
        print(json.dumps(accounts, indent=2))
    else:
        for a in accounts:
            marker = " ← active" if a["active"] else ""
            if verbose:
                print(f"  {a['name']:15s} {a['email']}{marker}")
            else:
                print(f"  {a['name']}{marker}")


def get_openclaw_agent_dirs():
    """Find all OpenClaw agent directories."""
    dirs = []
    if not OPENCLAW_AGENTS_GLOB.exists():
        return dirs
    for agent_dir in OPENCLAW_AGENTS_GLOB.iterdir():
        agent_inner = agent_dir / "agent"
        if agent_inner.is_dir():
            dirs.append(agent_inner)
    return dirs


def sync_all_to_openclaw():
    """Push all saved account tokens to all OpenClaw agents' auth-profiles.json."""
    ACCOUNTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Build profiles dict keyed by email
    profiles = {}
    for f in sorted(ACCOUNTS_DIR.glob("*.json")):
        data = json.loads(f.read_text())
        email = data.get("email")
        if not email:
            # Try to extract from JWT
            try:
                payload = decode_jwt_payload(data.get("id_token", ""))
                email = payload.get("email", "")
            except Exception:
                pass
        if not email:
            continue
        key = f"openai-codex:{email}"
        profiles[key] = {
            "type": "oauth",
            "provider": "openai-codex",
            "access": data.get("access_token", ""),
            "refresh": data.get("refresh_token", ""),
            "expires": data.get("expires_at", 0),
            "accountId": data.get("account_id", data.get("email", "")),
            "email": email,
        }

    # Get active account info for auth.json update
    active_data = None
    if AUTH_JSON.exists():
        active_data = json.loads(AUTH_JSON.read_text())

    # Update each agent's auth-profiles.json
    for agent_dir in get_openclaw_agent_dirs():
        profiles_path = agent_dir / "auth-profiles.json"
        
        # Load existing profiles
        existing = {}
        if profiles_path.exists():
            try:
                existing = json.loads(profiles_path.read_text())
            except Exception:
                existing = {}
        
        # Remove old name-based codex keys (migration)
        old_keys = [k for k in existing if re.match(r'^openai-codex:[^@]+$', k)]
        for k in old_keys:
            del existing[k]
        
        # Merge new email-based profiles (preserve non-codex entries)
        existing.update(profiles)
        profiles_path.write_text(json.dumps(existing, indent=2))
        
        # Update agent's auth.json to the active account
        if active_data:
            agent_auth_path = agent_dir / "auth.json"
            agent_auth = {
                "provider": "openai-codex",
                "access": active_data.get("access_token", ""),
                "email": active_data.get("email", ""),
            }
            agent_auth_path.write_text(json.dumps(agent_auth, indent=2))
    
    return profiles


def use_account(name: str):
    """Switch active account to the named account."""
    data = load_account(name)
    CODEX_DIR.mkdir(parents=True, exist_ok=True)
    AUTH_JSON.write_text(json.dumps(data, indent=2))
    
    # Log the switch
    email = data.get("email", "")
    user_id = data.get("account_id", "")
    if not user_id:
        try:
            payload = decode_jwt_payload(data.get("id_token", ""))
            user_id = payload.get("sub", "")
        except Exception:
            pass
    
    entry = {
        "timestamp": int(time.time()),
        "account": name,
        "user_id": user_id,
    }
    with open(ACTIVITY_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")
    
    # Sync all accounts to OpenClaw
    sync_all_to_openclaw()
    
    print(f"Switched to account: {name} ({email})")


def sync_command():
    """Sync all profiles to OpenClaw."""
    profiles = sync_all_to_openclaw()
    print(f"Synced {len(profiles)} profile(s) to OpenClaw agents.")


def compute_score(weekly_pct: float, five_h_pct: float, elapsed_hours: float) -> float:
    """Compute the budget-based score for an account."""
    budget = (elapsed_hours / 168.0) * 100.0
    
    # 5h penalty
    if five_h_pct >= 100.0:
        penalty = 200
    elif five_h_pct >= 90.0:
        penalty = 50
    elif five_h_pct >= 75.0:
        penalty = 10
    else:
        penalty = 0
    
    score = (weekly_pct - budget) + penalty
    return score


def auto_command(as_json: bool = False):
    """
    Auto-switch to best quota account.
    NOTE: In this implementation, quota probing via 'codex exec' is not available.
    This function reads pre-cached quota data if available.
    """
    print("Auto mode requires live quota probing via 'codex exec'.", file=sys.stderr)
    print("Use 'python3 codex-accounts.py use <name>' to switch manually.", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Codex Account Switcher")
    subparsers = parser.add_subparsers(dest="command")
    
    # list
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--verbose", action="store_true")
    list_parser.add_argument("--json", action="store_true")
    
    # add
    subparsers.add_parser("add")
    
    # use
    use_parser = subparsers.add_parser("use")
    use_parser.add_argument("name")
    
    # auto
    auto_parser = subparsers.add_parser("auto")
    auto_parser.add_argument("--json", action="store_true")
    
    # sync
    subparsers.add_parser("sync")
    
    args = parser.parse_args()
    
    if args.command == "list":
        list_accounts(verbose=args.verbose, as_json=args.json)
    elif args.command == "add":
        print("Add requires interactive browser login (codex logout && codex login).")
        sys.exit(1)
    elif args.command == "use":
        use_account(args.name)
    elif args.command == "auto":
        auto_command(as_json=args.json)
    elif args.command == "sync":
        sync_command()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
'''

(scripts_dir / "codex-accounts.py").write_text(CODEX_ACCOUNTS_SCRIPT)

# Write a SKILL.md at the skill base for context
skill_md_content = """---
name: codex-account-switcher
version: 1.4.2
---
See ~/.codex/ for account data and ~/skills/codex-account-switcher/scripts/codex-accounts.py for the tool.
"""
(skill_base / "SKILL.md").write_text(skill_md_content)


# ─────────────────────────────────────────────────────────────
# Distractor files to simulate a realistic messy workspace
# ─────────────────────────────────────────────────────────────
distractors = [
    (WORKSPACE / "notes" / "meeting-2024-01-15.txt",
     "Q1 planning notes. Discussed quota management strategy.\nAction: rotate accounts weekly."),
    (WORKSPACE / "notes" / "todo.md",
     "- [ ] Fix quota alerting\n- [ ] Update team wiki\n- [x] Set up OpenClaw"),
    (WORKSPACE / "config" / "app.yaml",
     "service: quota-monitor\nport: 8080\ndatabase: postgres://localhost/quotadb"),
    (WORKSPACE / "config" / "logging.json",
     json.dumps({"level": "INFO", "format": "json", "output": "/var/log/app.log"}, indent=2)),
    (WORKSPACE / "scripts" / "backup.sh",
     "#!/bin/bash\ntar -czf backup.tar.gz ~/.codex/accounts/\necho Done"),
    (WORKSPACE / "scripts" / "rotate.py",
     "# TODO: implement account rotation\nprint('not implemented')"),
    (WORKSPACE / "data" / "quota-history" / "2024-01.csv",
     "date,account,weekly_pct,fiveh_pct\n2024-01-01,oliver,10,5\n2024-01-02,elise,15,8"),
    (WORKSPACE / "data" / "quota-history" / "2024-02.csv",
     "date,account,weekly_pct,fiveh_pct\n2024-02-01,oliver,45,22\n2024-02-02,sylvia,30,11"),
    (WORKSPACE / "reports" / "weekly-summary.txt",
     "Week of Jan 15: oliver used 60% quota. Elise used 45%. Sylvia: MAX."),
    (WORKSPACE / "reports" / "alerts.json",
     json.dumps([{"ts": 1700001000, "account": "sylvia", "level": "warn", "msg": "90% weekly quota"}], indent=2)),
    (HOME / "skills" / "codex-account-switcher" / "docs" / "changelog.md",
     "## v1.4.2\n- Fixed email-based profile key migration\n## v1.4.1\n- Added activity log"),
    (HOME / "skills" / "quota-dashboard" / "README.md",
     "# Quota Dashboard\nVisualizes ~/.codex/account-activity.jsonl data.\nRequires codex-account-switcher v1.4+"),
    (HOME / ".openclaw" / "config.json",
     json.dumps({"version": "2.1", "default_agent": "agent-alpha", "log_level": "info"}, indent=2)),
    (HOME / ".openclaw" / "agents" / "agent-alpha" / "agent" / "config.json",
     json.dumps({"name": "agent-alpha", "model": "codex-davinci", "max_tokens": 8192}, indent=2)),
    (HOME / ".openclaw" / "agents" / "agent-beta" / "agent" / "config.json",
     json.dumps({"name": "agent-beta", "model": "codex-cushman", "max_tokens": 4096}, indent=2)),
]

for path, content in distractors:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


# ─────────────────────────────────────────────────────────────
# Write a task context file (NOT a hint — just raw quota numbers)
# ─────────────────────────────────────────────────────────────
quota_snapshot = {
    "snapshot_description": "Quota readings taken 4 days and 8 hours into the weekly window",
    "elapsed_hours_in_window": 104,
    "accounts": {
        "oliver":  {"weekly_pct": 55.0, "five_h_pct": 80.0},
        "elise":   {"weekly_pct": 48.0, "five_h_pct": 40.0},
        "sylvia":  {"weekly_pct": 90.0, "five_h_pct": 15.0},
    }
}
(WORKSPACE / "quota_snapshot.json").write_text(json.dumps(quota_snapshot, indent=2))

print("Workspace generated successfully.")
print(f"  ~/.codex/auth.json         → active: oliver")
print(f"  ~/.codex/accounts/         → oliver.json, elise.json, sylvia.json")
print(f"  ~/.openclaw/agents/        → agent-alpha, agent-beta (stale name-based profiles)")
print(f"  ~/skills/codex-account-switcher/scripts/codex-accounts.py")
print(f"  /workspace/quota_snapshot.json")