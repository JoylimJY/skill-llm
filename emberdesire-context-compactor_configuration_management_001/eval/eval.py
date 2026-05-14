import sys
import json
from pathlib import Path

def load_json_safe(path):
    try:
        with open(path, "r") as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, f"File not found: {path}"
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON: {e}"

def run_eval(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []

    # The target file is the main openclaw.json
    config_path = workspace / ".openclaw" / "openclaw.json"
    config, err = load_json_safe(config_path)

    if config is None:
        checks.append({
            "name": "config_file_parseable",
            "passed": False,
            "detail": err or "openclaw.json could not be loaded"
        })
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    checks.append({
        "name": "config_file_parseable",
        "passed": True,
        "detail": f"openclaw.json parsed successfully from {config_path}"
    })

    # --- Check 1: Correct top-level nesting path ---
    try:
        plugin_entry = config["plugins"]["entries"]["context-compactor"]
        checks.append({
            "name": "correct_nesting_path",
            "passed": True,
            "detail": "plugins.entries.context-compactor exists"
        })
    except (KeyError, TypeError) as e:
        checks.append({
            "name": "correct_nesting_path",
            "passed": False,
            "detail": f"Missing correct nesting plugins.entries.context-compactor: {e}"
        })
        plugin_entry = None

    if plugin_entry is None:
        score = 1.0 / (len(checks) + 7)
        return {"passed": False, "score": score, "checks": checks}

    # --- Check 2: Plugin is enabled ---
    try:
        enabled = plugin_entry.get("enabled")
        passed = enabled is True
        checks.append({
            "name": "plugin_enabled",
            "passed": passed,
            "detail": f"enabled={enabled} (expected True)"
        })
    except Exception as e:
        checks.append({"name": "plugin_enabled", "passed": False, "detail": str(e)})

    # --- Check 3: config block exists ---
    try:
        cfg = plugin_entry["config"]
        checks.append({
            "name": "config_block_exists",
            "passed": True,
            "detail": "config block is present inside plugin entry"
        })
    except (KeyError, TypeError):
        checks.append({
            "name": "config_block_exists",
            "passed": False,
            "detail": "config block missing inside context-compactor entry"
        })
        cfg = {}

    # --- Check 4: maxTokens correct for 4K model (must be 3000, per SKILL.md small context profile) ---
    try:
        max_tokens = cfg.get("maxTokens")
        passed = max_tokens == 3000
        checks.append({
            "name": "maxTokens_4k_profile",
            "passed": passed,
            "detail": f"maxTokens={max_tokens} (expected 3000 for 4K model per SKILL.md)"
        })
    except Exception as e:
        checks.append({"name": "maxTokens_4k_profile", "passed": False, "detail": str(e)})

    # --- Check 5: keepRecentTokens correct for 4K model (must be 800) ---
    try:
        keep_recent = cfg.get("keepRecentTokens")
        passed = keep_recent == 800
        checks.append({
            "name": "keepRecentTokens_4k_profile",
            "passed": passed,
            "detail": f"keepRecentTokens={keep_recent} (expected 800 for 4K model per SKILL.md)"
        })
    except Exception as e:
        checks.append({"name": "keepRecentTokens_4k_profile", "passed": False, "detail": str(e)})

    # --- Check 6: charsPerToken must be 3 for CJK ---
    try:
        chars_per_token = cfg.get("charsPerToken")
        passed = chars_per_token == 3
        checks.append({
            "name": "charsPerToken_cjk",
            "passed": passed,
            "detail": f"charsPerToken={chars_per_token} (expected 3 for CJK/Japanese content per SKILL.md)"
        })
    except Exception as e:
        checks.append({"name": "charsPerToken_cjk", "passed": False, "detail": str(e)})

    # --- Check 7: logLevel must be "debug" and inside config ---
    try:
        log_level = cfg.get("logLevel")
        passed = log_level == "debug"
        checks.append({
            "name": "logLevel_debug_in_config",
            "passed": passed,
            "detail": f"logLevel={log_level} inside config block (expected 'debug')"
        })
    except Exception as e:
        checks.append({"name": "logLevel_debug_in_config", "passed": False, "detail": str(e)})

    # --- Check 8: summaryModel is set (non-empty string) ---
    try:
        summary_model = cfg.get("summaryModel")
        passed = isinstance(summary_model, str) and len(summary_model.strip()) > 0
        checks.append({
            "name": "summaryModel_set",
            "passed": passed,
            "detail": f"summaryModel={summary_model!r} (must be a non-empty string)"
        })
    except Exception as e:
        checks.append({"name": "summaryModel_set", "passed": False, "detail": str(e)})

    # --- Check 9: summaryMaxTokens is set and reasonable (must be > 0 and <= 1000) ---
    try:
        summary_max = cfg.get("summaryMaxTokens")
        passed = isinstance(summary_max, int) and 0 < summary_max <= 1000
        checks.append({
            "name": "summaryMaxTokens_present_and_valid",
            "passed": passed,
            "detail": f"summaryMaxTokens={summary_max} (expected int > 0 and <= 1000)"
        })
    except Exception as e:
        checks.append({"name": "summaryMaxTokens_present_and_valid", "passed": False, "detail": str(e)})

    # --- Check 10: logLevel NOT at plugin root level (must be inside .config) ---
    try:
        bad_loglevel_at_root = "logLevel" in plugin_entry and plugin_entry.get("logLevel") is not None
        passed = not bad_loglevel_at_root
        checks.append({
            "name": "logLevel_not_at_plugin_root",
            "passed": passed,
            "detail": "logLevel should be inside config block, not at plugin root level"
        })
    except Exception as e:
        checks.append({"name": "logLevel_not_at_plugin_root", "passed": False, "detail": str(e)})

    # --- Scoring ---
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)

    # Must pass all critical checks to be considered "passed"
    critical_checks = [
        "correct_nesting_path",
        "plugin_enabled",
        "maxTokens_4k_profile",
        "keepRecentTokens_4k_profile",
        "charsPerToken_cjk",
        "logLevel_debug_in_config",
    ]
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )

    return {
        "passed": critical_passed and passed_count >= total - 1,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, indent=2))