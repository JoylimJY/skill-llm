import sys
import json
from pathlib import Path

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_checks(workspace_dir):
    workspace = Path(workspace_dir)
    config_path = workspace / "openclaw.json"

    checks = []
    passed_all = True

    # ── Helper ──────────────────────────────────────────────────────────────
    def check(name, condition, detail):
        nonlocal passed_all
        result = bool(condition)
        if not result:
            passed_all = False
        checks.append({"name": name, "passed": result, "detail": detail})
        return result

    # ── 0. File exists ───────────────────────────────────────────────────────
    if not config_path.exists():
        checks.append({"name": "openclaw.json exists", "passed": False,
                        "detail": "File not found at /workspace/openclaw.json"})
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── 1. Parse JSON ────────────────────────────────────────────────────────
    try:
        cfg = load_json(config_path)
    except Exception as e:
        checks.append({"name": "openclaw.json is valid JSON", "passed": False,
                        "detail": f"JSON parse error: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    check("openclaw.json is valid JSON", True, "File parses correctly as JSON.")

    # ── 2. Correct nesting: plugins > entries (not 'entry') ─────────────────
    plugins = cfg.get("plugins", {})
    entries = plugins.get("entries", None)
    has_entries_key = entries is not None
    check(
        "plugins key uses 'entries' (not 'entry')",
        has_entries_key,
        f"Found keys under 'plugins': {list(plugins.keys())}. Expected 'entries'."
    )

    if not has_entries_key:
        # Can't proceed with deeper checks
        score = sum(1 for c in checks if c["passed"]) / max(len(checks), 1)
        return {"passed": False, "score": round(score, 3), "checks": checks}

    # ── 3. context-compactor entry exists ───────────────────────────────────
    cc = entries.get("context-compactor", None)
    has_cc = cc is not None
    check(
        "context-compactor entry exists under plugins.entries",
        has_cc,
        f"Keys under plugins.entries: {list(entries.keys())}"
    )

    if not has_cc:
        score = sum(1 for c in checks if c["passed"]) / max(len(checks), 1)
        return {"passed": False, "score": round(score, 3), "checks": checks}

    # ── 4. enabled = true ───────────────────────────────────────────────────
    enabled = cc.get("enabled", None)
    check(
        "context-compactor.enabled is true",
        enabled is True,
        f"enabled = {enabled!r}, expected true"
    )

    # ── 5. config block exists ──────────────────────────────────────────────
    cc_config = cc.get("config", None)
    has_config = isinstance(cc_config, dict)
    check(
        "context-compactor.config block exists",
        has_config,
        f"config = {cc_config!r}"
    )

    if not has_config:
        score = sum(1 for c in checks if c["passed"]) / max(len(checks), 1)
        return {"passed": False, "score": round(score, 3), "checks": checks}

    # ── 6. maxTokens = 3000 (4K small model preset) ─────────────────────────
    max_tokens = cc_config.get("maxTokens", None)
    check(
        "maxTokens = 3000 (correct 4K model preset)",
        max_tokens == 3000,
        f"maxTokens = {max_tokens!r}, expected 3000 (per SKILL.md 'Small context (4K models)' preset)"
    )

    # ── 7. keepRecentTokens = 800 (4K small model preset) ───────────────────
    keep_recent = cc_config.get("keepRecentTokens", None)
    check(
        "keepRecentTokens = 800 (correct 4K model preset)",
        keep_recent == 800,
        f"keepRecentTokens = {keep_recent!r}, expected 800 (per SKILL.md 'Small context (4K models)' preset)"
    )

    # ── 8. charsPerToken = 3 (CJK language override) ────────────────────────
    chars_per_token = cc_config.get("charsPerToken", None)
    check(
        "charsPerToken = 3 (CJK/Japanese language override)",
        chars_per_token == 3,
        f"charsPerToken = {chars_per_token!r}, expected 3 (SKILL.md: 'Try 3 for CJK languages')"
    )

    # ── 9. summaryModel = 'qwen2-7b-instruct' ───────────────────────────────
    summary_model = cc_config.get("summaryModel", None)
    check(
        "summaryModel set to 'qwen2-7b-instruct'",
        summary_model == "qwen2-7b-instruct",
        f"summaryModel = {summary_model!r}, expected 'qwen2-7b-instruct' (from project's model specs)"
    )

    # ── 10. logLevel = 'debug' inside config ────────────────────────────────
    log_level = cc_config.get("logLevel", None)
    check(
        "logLevel = 'debug' present in config block",
        log_level == "debug",
        f"logLevel = {log_level!r}, expected 'debug' (verbose logging for engineering team)"
    )

    # ── 11. summaryMaxTokens is present and a positive integer ──────────────
    summary_max = cc_config.get("summaryMaxTokens", None)
    check(
        "summaryMaxTokens is present and is a positive integer",
        isinstance(summary_max, int) and summary_max > 0,
        f"summaryMaxTokens = {summary_max!r}"
    )

    # ── 12. Original non-plugin config preserved (gateway, model, logging) ──
    has_gateway = "gateway" in cfg
    has_model_cfg = "model" in cfg
    check(
        "Original gateway and model config blocks are preserved",
        has_gateway and has_model_cfg,
        f"gateway present: {has_gateway}, model present: {has_model_cfg}"
    )

    # ── Score ────────────────────────────────────────────────────────────────
    n_passed = sum(1 for c in checks if c["passed"])
    score = round(n_passed / len(checks), 3)
    final_passed = all(c["passed"] for c in checks)

    return {"passed": final_passed, "score": score, "checks": checks}


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace_dir)
    print(json.dumps(result, indent=2))