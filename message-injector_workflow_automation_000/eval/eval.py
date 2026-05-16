import sys
import json
import pathlib
import os

def evaluate(workspace: str):
    checks = []
    
    OPENCLAW_HOME = pathlib.Path(os.path.expanduser("~/.openclaw"))
    EXPECTED_EXT_DIR = OPENCLAW_HOME / "workspace" / ".openclaw" / "extensions" / "message-injector"
    OPENCLAW_CFG = OPENCLAW_HOME / "openclaw.json"
    
    EXPECTED_PREPEND = "[COMPLIANCE: Always cite sources. Never generate legal advice without attorney review.]"

    # ── Check 1: Extension directory exists at the EXACT required path
    check_name = "extension_directory_exists_at_correct_path"
    try:
        exists = EXPECTED_EXT_DIR.is_dir()
        checks.append({
            "name": check_name,
            "passed": exists,
            "detail": f"Directory {EXPECTED_EXT_DIR} {'exists' if exists else 'does NOT exist'}."
        })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ── Check 2: index.ts was copied to the extension directory
    check_name = "index_ts_present_in_extension_dir"
    try:
        target = EXPECTED_EXT_DIR / "index.ts"
        source = pathlib.Path(workspace) / "scripts" / "index.ts"
        present = target.is_file()
        content_ok = False
        if present and source.is_file():
            content_ok = target.read_text() == source.read_text()
        checks.append({
            "name": check_name,
            "passed": present and content_ok,
            "detail": (
                f"index.ts present={present}, content_matches_source={content_ok}. "
                f"Path checked: {target}"
            )
        })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ── Check 3: openclaw.plugin.json was copied to the extension directory
    check_name = "openclaw_plugin_json_present_in_extension_dir"
    try:
        target = EXPECTED_EXT_DIR / "openclaw.plugin.json"
        source = pathlib.Path(workspace) / "scripts" / "openclaw.plugin.json"
        present = target.is_file()
        content_ok = False
        if present and source.is_file():
            try:
                target_data = json.loads(target.read_text())
                source_data = json.loads(source.read_text())
                content_ok = (target_data == source_data)
            except json.JSONDecodeError:
                content_ok = False
        checks.append({
            "name": check_name,
            "passed": present and content_ok,
            "detail": (
                f"openclaw.plugin.json present={present}, content_matches_source={content_ok}. "
                f"Path checked: {target}"
            )
        })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ── Check 4: openclaw.json has plugins.entries key
    check_name = "openclaw_json_has_plugins_entries"
    cfg_data = None
    try:
        cfg_data = json.loads(OPENCLAW_CFG.read_text())
        has_entries = (
            isinstance(cfg_data.get("plugins"), dict) and
            "entries" in cfg_data["plugins"]
        )
        checks.append({
            "name": check_name,
            "passed": has_entries,
            "detail": (
                f"openclaw.json plugins keys: {list(cfg_data.get('plugins', {}).keys())}. "
                f"'entries' key present: {has_entries}."
            )
        })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception reading openclaw.json: {e}"})

    # ── Check 5: plugins.entries has "message-injector" key
    check_name = "plugins_entries_has_message_injector_key"
    try:
        if cfg_data is None:
            raise ValueError("Config not loaded")
        entries = cfg_data.get("plugins", {}).get("entries", {})
        has_key = "message-injector" in entries
        checks.append({
            "name": check_name,
            "passed": has_key,
            "detail": (
                f"plugins.entries keys: {list(entries.keys())}. "
                f"'message-injector' present: {has_key}."
            )
        })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ── Check 6: Top-level enabled flag is True
    check_name = "plugin_top_level_enabled_is_true"
    try:
        if cfg_data is None:
            raise ValueError("Config not loaded")
        entry = cfg_data.get("plugins", {}).get("entries", {}).get("message-injector", {})
        top_enabled = entry.get("enabled")
        passed = (top_enabled is True)
        checks.append({
            "name": check_name,
            "passed": passed,
            "detail": f"message-injector.enabled = {repr(top_enabled)} (expected True)"
        })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ── Check 7: config.enabled is True (the nested enabled under config block)
    check_name = "plugin_config_enabled_is_true"
    try:
        if cfg_data is None:
            raise ValueError("Config not loaded")
        entry = cfg_data.get("plugins", {}).get("entries", {}).get("message-injector", {})
        config_block = entry.get("config", {})
        config_enabled = config_block.get("enabled")
        passed = (config_enabled is True)
        checks.append({
            "name": check_name,
            "passed": passed,
            "detail": (
                f"message-injector.config.enabled = {repr(config_enabled)} (expected True). "
                f"config block keys: {list(config_block.keys())}"
            )
        })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ── Check 8: config.prependText contains the exact compliance string
    check_name = "plugin_config_prependText_correct"
    try:
        if cfg_data is None:
            raise ValueError("Config not loaded")
        entry = cfg_data.get("plugins", {}).get("entries", {}).get("message-injector", {})
        config_block = entry.get("config", {})
        prepend_text = config_block.get("prependText", "")
        passed = (prepend_text == EXPECTED_PREPEND)
        checks.append({
            "name": check_name,
            "passed": passed,
            "detail": (
                f"prependText found:    {repr(prepend_text)}\n"
                f"prependText expected: {repr(EXPECTED_PREPEND)}"
            )
        })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ── Check 9: Original openclaw.json structure preserved (gateway, channels, etc.)
    check_name = "openclaw_json_original_structure_preserved"
    try:
        if cfg_data is None:
            raise ValueError("Config not loaded")
        has_gateway = "gateway" in cfg_data
        has_channels = "channels" in cfg_data
        has_version = "version" in cfg_data
        passed = has_gateway and has_channels and has_version
        checks.append({
            "name": check_name,
            "passed": passed,
            "detail": (
                f"version={has_version}, gateway={has_gateway}, channels={has_channels}. "
                f"Original keys preserved: {passed}"
            )
        })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ── Compute final score
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)

    # Task passes only if ALL checks pass
    all_passed = all(c["passed"] for c in checks)

    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    ws = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(ws)