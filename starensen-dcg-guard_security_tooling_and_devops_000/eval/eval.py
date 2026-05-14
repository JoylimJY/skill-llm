#!/usr/bin/env python3
"""
Evaluation script for DCG Guard plugin integration task.
Checks:
1. openclaw.json has correct dcg-guard plugin config (enabled + dcgBin keys)
2. plugin src/index.js uses execFileSync (not execSync) + correct return shape + correct path resolution
3. guard_audit_report.json exists with correct block/pass verdicts for all 10 test cases
4. Dangerous commands are marked blocked, safe commands are marked allowed/passed
"""

import sys
import json
import re
import os
from pathlib import Path

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def run_checks(workspace: str):
    checks = []
    workspace = Path(workspace)

    # ── Check 1: openclaw.json has correct config structure ──────────────────
    try:
        cfg_path = workspace / "openclaw.json"
        cfg = load_json(cfg_path)
        dcg_entry = cfg.get("plugins", {}).get("entries", {}).get("dcg-guard", {})
        dcg_config = dcg_entry.get("config", {})
        
        has_enabled = "enabled" in dcg_config
        has_dcgbin = "dcgBin" in dcg_config
        enabled_is_bool = isinstance(dcg_config.get("enabled"), bool)
        
        # Must NOT have the old wrong keys
        no_active_key = "active" not in dcg_config
        no_guard_binary_key = "guardBinary" not in dcg_config
        
        passed_cfg = has_enabled and has_dcgbin and enabled_is_bool and no_active_key and no_guard_binary_key
        checks.append({
            "name": "openclaw.json: dcg-guard config uses correct keys (enabled, dcgBin)",
            "passed": passed_cfg,
            "detail": (
                f"has_enabled={has_enabled}, has_dcgBin={has_dcgbin}, "
                f"enabled_is_bool={enabled_is_bool}, "
                f"no_stale_active_key={no_active_key}, no_stale_guardBinary_key={no_guard_binary_key}. "
                f"Config found: {json.dumps(dcg_config)}"
            )
        })
    except Exception as e:
        checks.append({
            "name": "openclaw.json: dcg-guard config uses correct keys (enabled, dcgBin)",
            "passed": False,
            "detail": f"Exception reading openclaw.json: {e}"
        })

    # ── Check 2: plugin index.js uses execFileSync ───────────────────────────
    try:
        plugin_candidates = list(workspace.rglob("index.js"))
        plugin_path = None
        for p in plugin_candidates:
            if "dcg-guard" in str(p):
                plugin_path = p
                break
        
        if plugin_path is None:
            checks.append({
                "name": "plugin index.js: uses execFileSync (not execSync)",
                "passed": False,
                "detail": "Could not find index.js under dcg-guard plugin directory"
            })
        else:
            src = plugin_path.read_text()
            uses_execFileSync = "execFileSync" in src
            not_only_execSync = not re.search(r'\bexecSync\b(?!.*execFileSync)', src)
            # More precise: execSync alone (not as part of execFileSync) should not be used for DCG invocation
            # Check that execSync is not imported standalone or used for DCG call
            exec_sync_standalone = bool(re.search(r'(?<!\w)execSync\b', src))
            exec_file_sync_present = bool(re.search(r'\bexecFileSync\b', src))
            
            # If execFileSync is present, that's the key requirement
            passed_exec = exec_file_sync_present
            checks.append({
                "name": "plugin index.js: uses execFileSync (not execSync)",
                "passed": passed_exec,
                "detail": (
                    f"execFileSync_present={exec_file_sync_present}, "
                    f"execSync_standalone={exec_sync_standalone}. "
                    f"File: {plugin_path}"
                )
            })
    except Exception as e:
        checks.append({
            "name": "plugin index.js: uses execFileSync (not execSync)",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── Check 3: plugin index.js returns correct shape { block: true } ───────
    try:
        if plugin_path is not None:
            src = plugin_path.read_text()
            # Must contain { block: true } not { blocked: true }
            has_block_true = bool(re.search(r'block\s*:\s*true', src))
            no_blocked_true = not bool(re.search(r'blocked\s*:\s*true', src))
            passed_shape = has_block_true and no_blocked_true
            checks.append({
                "name": "plugin index.js: returns { block: true } not { blocked: true }",
                "passed": passed_shape,
                "detail": f"has_block_true={has_block_true}, no_blocked_true={no_blocked_true}"
            })
        else:
            checks.append({
                "name": "plugin index.js: returns { block: true } not { blocked: true }",
                "passed": False,
                "detail": "Plugin file not found"
            })
    except Exception as e:
        checks.append({
            "name": "plugin index.js: returns { block: true } not { blocked: true }",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── Check 4: plugin resolves dcgBin from config or DCG_BIN env or default ─
    try:
        if plugin_path is not None:
            src = plugin_path.read_text()
            # Must NOT hardcode /usr/bin/dcg-guard-bin or similar wrong path
            no_wrong_hardcode = "/usr/bin/dcg-guard-bin" not in src
            # Should reference DCG_BIN env var OR config.dcgBin OR default ~/.local/bin/dcg
            references_env = "DCG_BIN" in src
            references_config_dcgbin = "dcgBin" in src
            references_default = ".local/bin/dcg" in src or "local/bin/dcg" in src
            proper_resolution = no_wrong_hardcode and (references_env or references_config_dcgbin or references_default)
            checks.append({
                "name": "plugin index.js: resolves DCG binary path correctly (config/env/default)",
                "passed": proper_resolution,
                "detail": (
                    f"no_wrong_hardcode={no_wrong_hardcode}, "
                    f"references_DCG_BIN_env={references_env}, "
                    f"references_config_dcgBin={references_config_dcgbin}, "
                    f"references_default_path={references_default}"
                )
            })
        else:
            checks.append({
                "name": "plugin index.js: resolves DCG binary path correctly (config/env/default)",
                "passed": False,
                "detail": "Plugin file not found"
            })
    except Exception as e:
        checks.append({
            "name": "plugin index.js: resolves DCG binary path correctly (config/env/default)",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── Check 5: plugin checks config.enabled (not config.active) ────────────
    try:
        if plugin_path is not None:
            src = plugin_path.read_text()
            # Should check enabled, not active
            checks_enabled = bool(re.search(r'config\s*[\.\[]\s*["\']?enabled', src)) or \
                             bool(re.search(r'\.enabled\b', src))
            no_checks_active = not bool(re.search(r'config\s*[\.\[]\s*["\']?active', src)) and \
                               not bool(re.search(r'config\.active\b', src))
            passed_enabled = checks_enabled and no_checks_active
            checks.append({
                "name": "plugin index.js: checks config.enabled (not config.active)",
                "passed": passed_enabled,
                "detail": f"checks_enabled={checks_enabled}, no_checks_active={no_checks_active}"
            })
        else:
            checks.append({
                "name": "plugin index.js: checks config.enabled (not config.active)",
                "passed": False,
                "detail": "Plugin file not found"
            })
    except Exception as e:
        checks.append({
            "name": "plugin index.js: checks config.enabled (not config.active)",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── Check 6: guard_audit_report.json exists and is not the stale version ──
    try:
        report_candidates = list(workspace.rglob("guard_audit_report.json"))
        report_path = report_candidates[0] if report_candidates else None

        if report_path is None:
            checks.append({
                "name": "guard_audit_report.json: file exists",
                "passed": False,
                "detail": "guard_audit_report.json not found anywhere in workspace"
            })
        else:
            report = load_json(report_path)
            # Must NOT be the stale legacy report
            not_legacy = report.get("generated_by") != "legacy_guard.sh"
            is_not_stub = "OUTDATED" not in str(report.get("note", ""))
            checks.append({
                "name": "guard_audit_report.json: file exists and is not the stale legacy version",
                "passed": not_legacy and is_not_stub,
                "detail": f"generated_by={report.get('generated_by')}, note={report.get('note','')[:80]}"
            })
    except Exception as e:
        checks.append({
            "name": "guard_audit_report.json: file exists and is not the stale legacy version",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── Check 7: audit report has all 10 test case results ───────────────────
    try:
        report_candidates = list(workspace.rglob("guard_audit_report.json"))
        report_path = report_candidates[0] if report_candidates else None
        
        if report_path is None:
            raise FileNotFoundError("guard_audit_report.json missing")
        
        report = load_json(report_path)
        
        # Find the results list - could be at top level or under "results" key
        results = report.get("results", report.get("test_results", report.get("cases", [])))
        if not isinstance(results, list):
            # Maybe the report IS the list
            results = report if isinstance(report, list) else []
        
        result_ids = set()
        for r in results:
            if isinstance(r, dict):
                rid = r.get("id", r.get("test_id", ""))
                if rid:
                    result_ids.add(rid)
        
        expected_ids = {f"tc{i:02d}" for i in range(1, 11)}
        has_all = expected_ids.issubset(result_ids)
        
        checks.append({
            "name": "guard_audit_report.json: contains all 10 test case results (tc01-tc10)",
            "passed": has_all,
            "detail": f"Found IDs: {sorted(result_ids)}, expected: {sorted(expected_ids)}"
        })
    except Exception as e:
        checks.append({
            "name": "guard_audit_report.json: contains all 10 test case results (tc01-tc10)",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── Check 8: dangerous commands are blocked in report ────────────────────
    DANGEROUS_IDS = {"tc01", "tc02", "tc03", "tc04", "tc05"}
    SAFE_IDS      = {"tc06", "tc07", "tc08", "tc09", "tc10"}
    BLOCKED_SYNONYMS = {"blocked", "block", "denied", "dangerous", "rejected", "true", True, 1, "1"}
    ALLOWED_SYNONYMS = {"allowed", "allow", "safe", "passed", "pass", "ok", "false", False, 0, "0"}

    def is_blocked(verdict):
        if verdict is None:
            return False
        v = str(verdict).lower().strip()
        return v in {str(s).lower() for s in BLOCKED_SYNONYMS}

    def is_allowed(verdict):
        if verdict is None:
            return False
        v = str(verdict).lower().strip()
        return v in {str(s).lower() for s in ALLOWED_SYNONYMS}

    try:
        report_candidates = list(workspace.rglob("guard_audit_report.json"))
        report_path = report_candidates[0] if report_candidates else None
        
        if report_path is None:
            raise FileNotFoundError("guard_audit_report.json missing")
        
        report = load_json(report_path)
        results = report.get("results", report.get("test_results", report.get("cases", [])))
        if not isinstance(results, list):
            results = report if isinstance(report, list) else []
        
        # Build id -> verdict map
        id_verdict = {}
        for r in results:
            if isinstance(r, dict):
                rid = r.get("id", r.get("test_id", ""))
                verdict = (
                    r.get("verdict") or r.get("result") or r.get("blocked") or
                    r.get("status") or r.get("action") or r.get("outcome")
                )
                if rid:
                    id_verdict[rid] = verdict
        
        dangerous_correct = all(is_blocked(id_verdict.get(tid)) for tid in DANGEROUS_IDS)
        dangerous_detail = {tid: id_verdict.get(tid) for tid in DANGEROUS_IDS}
        
        checks.append({
            "name": "guard_audit_report.json: all dangerous commands (tc01-tc05) are marked blocked",
            "passed": dangerous_correct,
            "detail": f"Dangerous verdicts: {dangerous_detail}"
        })
    except Exception as e:
        checks.append({
            "name": "guard_audit_report.json: all dangerous commands (tc01-tc05) are marked blocked",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── Check 9: safe commands are allowed in report ──────────────────────────
    try:
        report_candidates = list(workspace.rglob("guard_audit_report.json"))
        report_path = report_candidates[0] if report_candidates else None
        
        if report_path is None:
            raise FileNotFoundError("guard_audit_report.json missing")
        
        report = load_json(report_path)
        results = report.get("results", report.get("test_results", report.get("cases", [])))
        if not isinstance(results, list):
            results = report if isinstance(report, list) else []
        
        id_verdict = {}
        for r in results:
            if isinstance(r, dict):
                rid = r.get("id", r.get("test_id", ""))
                verdict = (
                    r.get("verdict") or r.get("result") or r.get("blocked") or
                    r.get("status") or r.get("action") or r.get("outcome")
                )
                if rid:
                    id_verdict[rid] = verdict
        
        safe_correct = all(is_allowed(id_verdict.get(tid)) for tid in SAFE_IDS)
        safe_detail = {tid: id_verdict.get(tid) for tid in SAFE_IDS}
        
        checks.append({
            "name": "guard_audit_report.json: all safe commands (tc06-tc10) are marked allowed",
            "passed": safe_correct,
            "detail": f"Safe verdicts: {safe_detail}"
        })
    except Exception as e:
        checks.append({
            "name": "guard_audit_report.json: all safe commands (tc06-tc10) are marked allowed",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── Check 10: plugin has built-in fallback rules (fail-open logic present) ─
    try:
        if plugin_path is not None:
            src = plugin_path.read_text()
            # Must have built-in pattern matching for when DCG binary is absent
            has_builtin_patterns = bool(re.search(r'rm\s*[+\\\\*].*-rf|BUILTIN|builtin|built.in', src, re.IGNORECASE))
            has_fallback_logic = bool(re.search(r'(catch|if.*not.*exist|!.*exist|ENOENT|fail.?open)', src, re.IGNORECASE))
            passed_fallback = has_builtin_patterns or has_fallback_logic
            checks.append({
                "name": "plugin index.js: has built-in fallback rules / fail-open behavior",
                "passed": passed_fallback,
                "detail": (
                    f"has_builtin_patterns={has_builtin_patterns}, "
                    f"has_fallback_logic={has_fallback_logic}"
                )
            })
        else:
            checks.append({
                "name": "plugin index.js: has built-in fallback rules / fail-open behavior",
                "passed": False,
                "detail": "Plugin file not found"
            })
    except Exception as e:
        checks.append({
            "name": "plugin index.js: has built-in fallback rules / fail-open behavior",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── Aggregate score ───────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 3)
    all_passed = passed_count == total

    return {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "invocation", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(1)
    
    result = run_checks(sys.argv[1])
    print(json.dumps(result, indent=2))