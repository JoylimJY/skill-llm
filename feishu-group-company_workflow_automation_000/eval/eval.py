#!/usr/bin/env python3
"""
Evaluation script for the Feishu company group configuration task.
Checks that apply_feishu_group_company.py was run correctly and produced
a properly patched openclaw.json.
"""

import json
import sys
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    workspace = Path(workspace_dir)
    config_path = workspace / ".openclaw" / "openclaw.json"

    # ── Load config ──────────────────────────────────────────────────────────
    try:
        config = json.loads(config_path.read_text())
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "config_loadable", "passed": False, "detail": str(e)}]
        }
        print(json.dumps(result))
        return

    checks.append({"name": "config_loadable", "passed": True, "detail": "openclaw.json loaded successfully"})

    accounts = {}
    try:
        accounts = config["channels"]["feishu"]["accounts"]
    except (KeyError, TypeError):
        pass

    # ── Check 1: Top-level groupRules for oc_abc123 with requireMention: true ──
    try:
        group_rule = config["groupRules"]["oc_abc123"]
        passed = group_rule.get("requireMention") == True
        checks.append({
            "name": "top_level_group_rule_requireMention_true",
            "passed": passed,
            "detail": f"groupRules.oc_abc123.requireMention = {group_rule.get('requireMention')} (expected true)"
        })
    except Exception as e:
        checks.append({
            "name": "top_level_group_rule_requireMention_true",
            "passed": False,
            "detail": f"Missing groupRules.oc_abc123: {e}"
        })

    # ── Check 2: company-ceo uses 'groups' (plural), not 'group' (singular) ──
    try:
        ceo_feishu = accounts["company-ceo"]["channels"]["feishu"]
        has_groups = "groups" in ceo_feishu
        has_legacy_group = "group" in ceo_feishu
        passed = has_groups and not has_legacy_group
        checks.append({
            "name": "ceo_uses_groups_not_group",
            "passed": passed,
            "detail": f"has 'groups': {has_groups}, has legacy 'group': {has_legacy_group}"
        })
    except Exception as e:
        checks.append({
            "name": "ceo_uses_groups_not_group",
            "passed": False,
            "detail": str(e)
        })

    # ── Check 3: company-ceo requireMention = false for oc_abc123 ─────────────
    try:
        ceo_group_cfg = accounts["company-ceo"]["channels"]["feishu"]["groups"]["oc_abc123"]
        val = ceo_group_cfg.get("requireMention")
        passed = val == False
        checks.append({
            "name": "ceo_requireMention_false",
            "passed": passed,
            "detail": f"company-ceo groups.oc_abc123.requireMention = {val} (expected false)"
        })
    except Exception as e:
        checks.append({
            "name": "ceo_requireMention_false",
            "passed": False,
            "detail": str(e)
        })

    # ── Check 4: company-ceo has group-scoped systemPrompt with NO_REPLY ──────
    try:
        ceo_group_cfg = accounts["company-ceo"]["channels"]["feishu"]["groups"]["oc_abc123"]
        sp = ceo_group_cfg.get("systemPrompt", "")
        has_no_reply = "NO_REPLY" in sp
        has_mention_logic = len(sp) > 20  # must be a real prompt, not empty
        passed = has_no_reply and has_mention_logic
        checks.append({
            "name": "ceo_group_systemPrompt_with_NO_REPLY",
            "passed": passed,
            "detail": f"systemPrompt present: {bool(sp)}, contains NO_REPLY: {has_no_reply}"
        })
    except Exception as e:
        checks.append({
            "name": "ceo_group_systemPrompt_with_NO_REPLY",
            "passed": False,
            "detail": str(e)
        })

    # ── Check 5: company-ui uses 'groups' (plural), not 'group' (singular) ───
    try:
        ui_feishu = accounts["company-ui"]["channels"]["feishu"]
        has_groups = "groups" in ui_feishu
        has_legacy_group = "group" in ui_feishu
        passed = has_groups and not has_legacy_group
        checks.append({
            "name": "ui_uses_groups_not_group",
            "passed": passed,
            "detail": f"has 'groups': {has_groups}, has legacy 'group': {has_legacy_group}"
        })
    except Exception as e:
        checks.append({
            "name": "ui_uses_groups_not_group",
            "passed": False,
            "detail": str(e)
        })

    # ── Check 6: company-ui requireMention = true for oc_abc123 ───────────────
    try:
        ui_group_cfg = accounts["company-ui"]["channels"]["feishu"]["groups"]["oc_abc123"]
        val = ui_group_cfg.get("requireMention")
        passed = val == True
        checks.append({
            "name": "ui_requireMention_true",
            "passed": passed,
            "detail": f"company-ui groups.oc_abc123.requireMention = {val} (expected true)"
        })
    except Exception as e:
        checks.append({
            "name": "ui_requireMention_true",
            "passed": False,
            "detail": str(e)
        })

    # ── Check 7: company-dev uses 'groups' (plural), not 'group' (singular) ──
    try:
        dev_feishu = accounts["company-dev"]["channels"]["feishu"]
        has_groups = "groups" in dev_feishu
        has_legacy_group = "group" in dev_feishu
        passed = has_groups and not has_legacy_group
        checks.append({
            "name": "dev_uses_groups_not_group",
            "passed": passed,
            "detail": f"has 'groups': {has_groups}, has legacy 'group': {has_legacy_group}"
        })
    except Exception as e:
        checks.append({
            "name": "dev_uses_groups_not_group",
            "passed": False,
            "detail": str(e)
        })

    # ── Check 8: company-dev requireMention = true for oc_abc123 ──────────────
    try:
        dev_group_cfg = accounts["company-dev"]["channels"]["feishu"]["groups"]["oc_abc123"]
        val = dev_group_cfg.get("requireMention")
        passed = val == True
        checks.append({
            "name": "dev_requireMention_true",
            "passed": passed,
            "detail": f"company-dev groups.oc_abc123.requireMention = {val} (expected true)"
        })
    except Exception as e:
        checks.append({
            "name": "dev_requireMention_true",
            "passed": False,
            "detail": str(e)
        })

    # ── Check 9: No legacy 'group' key anywhere in accounts ───────────────────
    try:
        legacy_found = []
        for acct_id, acct_data in accounts.items():
            feishu_cfg = acct_data.get("channels", {}).get("feishu", {})
            if "group" in feishu_cfg:
                legacy_found.append(acct_id)
        passed = len(legacy_found) == 0
        checks.append({
            "name": "no_legacy_group_key_anywhere",
            "passed": passed,
            "detail": f"Accounts still using legacy 'group' key: {legacy_found}"
        })
    except Exception as e:
        checks.append({
            "name": "no_legacy_group_key_anywhere",
            "passed": False,
            "detail": str(e)
        })

    # ── Check 10: bindings for all three accounts still intact ─────────────────
    try:
        bindings = config.get("bindings", [])
        binding_accounts = {b["match"]["accountId"] for b in bindings if "match" in b}
        has_ceo = "company-ceo" in binding_accounts
        has_ui = "company-ui" in binding_accounts
        has_dev = "company-dev" in binding_accounts
        passed = has_ceo and has_ui and has_dev
        checks.append({
            "name": "bindings_intact",
            "passed": passed,
            "detail": f"Binding accounts found: {sorted(binding_accounts)}"
        })
    except Exception as e:
        checks.append({
            "name": "bindings_intact",
            "passed": False,
            "detail": str(e)
        })

    # ── Score ──────────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    overall_passed = all(c["passed"] for c in checks)

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace dir provided"}]}))
        sys.exit(1)
    evaluate(sys.argv[1])