#!/usr/bin/env python3
"""
Evaluation script for the multi-agent-feishu task.
Checks:
  1. openclaw.json has correct structure with both Feishu accounts
  2. Both agents were registered via 'openclaw agents add' with correct flags
  3. Gateway was restarted at least once
  4. (Bonus) 'openclaw agents list --bindings' was called
"""

import json
import sys
import re
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
home = Path.home()
oc_dir = home / ".openclaw"

checks = []
total_score = 0.0
max_score = 1.0

def check(name, passed, detail, weight):
    global total_score
    if passed:
        total_score += weight
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

# ─── Weight allocations ────────────────────────────────────────────────
W_CONFIG_STRUCTURE   = 0.25   # openclaw.json has channels.feishu.accounts
W_SALES_ACCOUNT      = 0.15   # sales account with correct appId + appSecret
W_SUPPORT_ACCOUNT    = 0.15   # support account with correct appId + appSecret
W_AGENTS_REGISTERED  = 0.20   # both agents in agents_db with correct bind+flags
W_GATEWAY_RESTARTED  = 0.15   # gateway was restarted at least once after agents added
W_CORRECT_WORKSPACES = 0.10   # workspaces match workspace1 / workspace2 pattern

# ─── 1. Read openclaw.json ─────────────────────────────────────────────
config_path = oc_dir / "openclaw.json"
cfg = None
try:
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
except Exception as exc:
    check("openclaw.json is readable JSON",
          False, f"Cannot read/parse {config_path}: {exc}", W_CONFIG_STRUCTURE)
    check("Sales account present",      False, "Config unreadable", W_SALES_ACCOUNT)
    check("Support account present",    False, "Config unreadable", W_SUPPORT_ACCOUNT)
    check("Agents registered correctly",False, "Config unreadable", W_AGENTS_REGISTERED)
    check("Gateway restarted",          False, "N/A",               W_GATEWAY_RESTARTED)
    check("Workspaces correct",         False, "N/A",               W_CORRECT_WORKSPACES)
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# ─── 2. Validate config structure ─────────────────────────────────────
accounts = {}
try:
    accounts = cfg["channels"]["feishu"]["accounts"]
    assert isinstance(accounts, dict), "accounts is not a dict"
    check("openclaw.json has channels.feishu.accounts structure",
          True, f"Found {len(accounts)} account(s)", W_CONFIG_STRUCTURE)
except Exception as exc:
    check("openclaw.json has channels.feishu.accounts structure",
          False, f"Structure missing or wrong: {exc}", W_CONFIG_STRUCTURE)

# ─── 3. Validate sales account ────────────────────────────────────────
sales_acct = None
try:
    # Accept any key that contains 'sales'
    sales_key = next((k for k in accounts if "sales" in k.lower()), None)
    if sales_key is None:
        raise KeyError("No account key containing 'sales' found")
    sales_acct = accounts[sales_key]
    assert sales_acct.get("appId")     == "cli_sales_app_001",     \
        f"appId mismatch: {sales_acct.get('appId')!r}"
    assert sales_acct.get("appSecret") == "s3cr3t_sales_2024",     \
        f"appSecret mismatch: {sales_acct.get('appSecret')!r}"
    check("Sales Feishu account has correct appId & appSecret",
          True, f"Key='{sales_key}', appId=cli_sales_app_001", W_SALES_ACCOUNT)
except Exception as exc:
    check("Sales Feishu account has correct appId & appSecret",
          False, str(exc), W_SALES_ACCOUNT)

# ─── 4. Validate support account ──────────────────────────────────────
try:
    support_key = next((k for k in accounts if "support" in k.lower()), None)
    if support_key is None:
        raise KeyError("No account key containing 'support' found")
    support_acct = accounts[support_key]
    assert support_acct.get("appId")     == "cli_support_app_002",  \
        f"appId mismatch: {support_acct.get('appId')!r}"
    assert support_acct.get("appSecret") == "s3cr3t_support_2024",  \
        f"appSecret mismatch: {support_acct.get('appSecret')!r}"
    check("Support Feishu account has correct appId & appSecret",
          True, f"Key='{support_key}', appId=cli_support_app_002", W_SUPPORT_ACCOUNT)
except Exception as exc:
    check("Support Feishu account has correct appId & appSecret",
          False, str(exc), W_SUPPORT_ACCOUNT)

# ─── 5. Read audit log & agents DB ────────────────────────────────────
audit_entries = []
try:
    audit_log = oc_dir / "audit.log"
    for line in audit_log.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                audit_entries.append(json.loads(line))
            except Exception:
                pass
except Exception as exc:
    check("Audit log readable", False, str(exc), 0.0)

agents_db = []
try:
    agents_db = json.loads((oc_dir / "agents_db.json").read_text(encoding="utf-8"))
    if not isinstance(agents_db, list):
        agents_db = []
except Exception:
    agents_db = []

# ─── 6. Check agents were registered with correct flags ───────────────
try:
    add_cmds = [e for e in audit_entries if e.get("cmd") == "agents add"]
    
    # Check sales agent
    sales_add = next(
        (e for e in add_cmds
         if "sales" in (e.get("agent_id") or "").lower() and
            "feishu:" in (e.get("bind") or "") and
            "sales" in (e.get("bind") or "").lower() and
            e.get("non_interactive") is True and
            not e.get("errors")),
        None
    )
    support_add = next(
        (e for e in add_cmds
         if "support" in (e.get("agent_id") or "").lower() and
            "feishu:" in (e.get("bind") or "") and
            "support" in (e.get("bind") or "").lower() and
            e.get("non_interactive") is True and
            not e.get("errors")),
        None
    )

    both_ok = (sales_add is not None) and (support_add is not None)
    detail_parts = []
    if sales_add:
        detail_parts.append(f"sales: agent_id={sales_add['agent_id']!r} bind={sales_add['bind']!r}")
    else:
        detail_parts.append("sales: NOT FOUND or errors present")
    if support_add:
        detail_parts.append(f"support: agent_id={support_add['agent_id']!r} bind={support_add['bind']!r}")
    else:
        detail_parts.append("support: NOT FOUND or errors present")
    check("Both agents registered with --bind feishu:<id> --non-interactive",
          both_ok, "; ".join(detail_parts), W_AGENTS_REGISTERED)
except Exception as exc:
    check("Both agents registered with --bind feishu:<id> --non-interactive",
          False, str(exc), W_AGENTS_REGISTERED)

# ─── 7. Check gateway was restarted ───────────────────────────────────
try:
    gw_state = json.loads((oc_dir / "gateway_state.json").read_text(encoding="utf-8"))
    restarts = gw_state.get("restarts", 0)
    restarted = (restarts >= 1) and (gw_state.get("status") == "running")
    check("Gateway restarted at least once",
          restarted,
          f"restarts={restarts}, status={gw_state.get('status')}",
          W_GATEWAY_RESTARTED)
except Exception as exc:
    check("Gateway restarted at least once", False, str(exc), W_GATEWAY_RESTARTED)

# ─── 8. Check workspace numbering ─────────────────────────────────────
try:
    workspace_pattern = re.compile(r'workspace[12]$')
    sales_ws    = sales_add.get("workspace",   "") if sales_add else ""
    support_ws  = support_add.get("workspace", "") if support_add else ""
    
    sales_ws_ok   = bool(workspace_pattern.search(sales_ws.replace("~", str(home))))
    support_ws_ok = bool(workspace_pattern.search(support_ws.replace("~", str(home))))
    ws_ok = sales_ws_ok and support_ws_ok
    detail_ws = f"sales_ws={sales_ws!r} ({sales_ws_ok}), support_ws={support_ws!r} ({support_ws_ok})"
    check("Workspaces follow workspace1/workspace2 naming convention",
          ws_ok, detail_ws, W_CORRECT_WORKSPACES)
except Exception as exc:
    check("Workspaces follow workspace1/workspace2 naming convention",
          False, str(exc), W_CORRECT_WORKSPACES)

# ─── Final score ──────────────────────────────────────────────────────
score = round(min(total_score, 1.0), 4)
passed = (score >= 0.85)  # require at least 85% to pass

print(json.dumps({
    "passed": passed,
    "score": score,
    "checks": checks
}, ensure_ascii=False, indent=2))