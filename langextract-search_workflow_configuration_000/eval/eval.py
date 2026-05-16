import sys
import json
import os
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    workspace = Path(workspace)

    # ── Locate conf.json ──────────────────────────────────────────────────────
    conf_path = workspace / "conf.json"
    conf = None

    try:
        if not conf_path.exists():
            checks.append({"name": "conf.json exists at workspace root", "passed": False,
                           "detail": "conf.json not found at /workspace/conf.json"})
            return finalize(checks)
        with open(conf_path, "r", encoding="utf-8") as f:
            conf = json.load(f)
        checks.append({"name": "conf.json exists and is valid JSON", "passed": True,
                       "detail": "File found and parsed successfully"})
    except Exception as e:
        checks.append({"name": "conf.json exists and is valid JSON", "passed": False,
                       "detail": f"Error reading conf.json: {e}"})
        return finalize(checks)

    zhipu = conf.get("zhipu_search", {})
    ddg = conf.get("duckduckgo_search", {})

    # ── CHECK 1: Both engines enabled ────────────────────────────────────────
    zhipu_enabled = zhipu.get("enabled")
    ddg_enabled = ddg.get("duckduckgo_search", {}) if False else ddg.get("enabled")
    both_enabled = (zhipu_enabled is True) and (ddg_enabled is True)
    checks.append({
        "name": "Both zhipu_search and duckduckgo_search are enabled",
        "passed": both_enabled,
        "detail": f"zhipu enabled={zhipu_enabled}, ddg enabled={ddg_enabled}"
    })

    # ── CHECK 2: Zhipu uses search_pro_sogou engine ───────────────────────────
    engine = zhipu.get("search_engine")
    engine_ok = engine == "search_pro_sogou"
    checks.append({
        "name": "zhipu_search.search_engine is 'search_pro_sogou'",
        "passed": engine_ok,
        "detail": f"Got: '{engine}', expected: 'search_pro_sogou'"
    })

    # ── CHECK 3: Zhipu count is exactly 20 (valid for search_pro_sogou: 10/20/30/40/50) ──
    count = zhipu.get("count")
    count_ok = count == 20
    checks.append({
        "name": "zhipu_search.count is 20 (valid for search_pro_sogou)",
        "passed": count_ok,
        "detail": f"Got: {count}, expected: 20 (must be in [10,20,30,40,50] for search_pro_sogou)"
    })

    # ── CHECK 4: Zhipu timelimit uses UNIFIED format "month" (NOT "oneMonth") ─
    zhipu_timelimit = zhipu.get("timelimit")
    zhipu_timelimit_ok = zhipu_timelimit == "month"
    checks.append({
        "name": "zhipu_search.timelimit uses unified format 'month' (not native 'oneMonth')",
        "passed": zhipu_timelimit_ok,
        "detail": f"Got: '{zhipu_timelimit}', expected: 'month' (unified format)"
    })

    # ── CHECK 5: Zhipu content_size is "medium" (compact summaries) ──────────
    content_size = zhipu.get("content_size")
    content_size_ok = content_size == "medium"
    checks.append({
        "name": "zhipu_search.content_size is 'medium'",
        "passed": content_size_ok,
        "detail": f"Got: '{content_size}', expected: 'medium'"
    })

    # ── CHECK 6: Zhipu apiKey is set to environment variable name ─────────────
    api_key = zhipu.get("apiKey")
    api_key_ok = isinstance(api_key, str) and len(api_key.strip()) > 0 and api_key not in ("", None)
    checks.append({
        "name": "zhipu_search.apiKey is set (non-empty string)",
        "passed": api_key_ok,
        "detail": f"Got: '{api_key}'"
    })

    # More specifically, check it uses the env var name from the brief
    api_key_envvar_ok = api_key == "ZHIPU_SEARCH_API_KEY"
    checks.append({
        "name": "zhipu_search.apiKey is 'ZHIPU_SEARCH_API_KEY' (env var name from project brief)",
        "passed": api_key_envvar_ok,
        "detail": f"Got: '{api_key}', expected: 'ZHIPU_SEARCH_API_KEY'"
    })

    # ── CHECK 7: Zhipu search_domain_filter is null ───────────────────────────
    domain_filter = zhipu.get("search_domain_filter", "NOT_SET")
    domain_filter_ok = domain_filter is None
    checks.append({
        "name": "zhipu_search.search_domain_filter is null (no domain restriction)",
        "passed": domain_filter_ok,
        "detail": f"Got: '{domain_filter}', expected: null"
    })

    # ── CHECK 8: DDG region is "cn-zh" (Chinese-language results) ────────────
    ddg_region = ddg.get("region")
    ddg_region_ok = ddg_region == "cn-zh"
    checks.append({
        "name": "duckduckgo_search.region is 'cn-zh' (Chinese market targeting)",
        "passed": ddg_region_ok,
        "detail": f"Got: '{ddg_region}', expected: 'cn-zh'"
    })

    # ── CHECK 9: DDG timelimit uses UNIFIED format "month" (NOT "m") ─────────
    ddg_timelimit = ddg.get("timelimit")
    ddg_timelimit_ok = ddg_timelimit == "month"
    checks.append({
        "name": "duckduckgo_search.timelimit uses unified format 'month' (not native 'm')",
        "passed": ddg_timelimit_ok,
        "detail": f"Got: '{ddg_timelimit}', expected: 'month' (unified format)"
    })

    # ── CHECK 10: DDG backend uses BOTH bing AND google (comma-separated) ─────
    ddg_backend = ddg.get("backend", "")
    # Must contain both bing and google in any order
    if isinstance(ddg_backend, str):
        parts = [p.strip() for p in ddg_backend.split(",")]
        ddg_backend_ok = "bing" in parts and "google" in parts
    else:
        ddg_backend_ok = False
    checks.append({
        "name": "duckduckgo_search.backend includes both 'bing' and 'google' (multi-backend)",
        "passed": ddg_backend_ok,
        "detail": f"Got: '{ddg_backend}', expected comma-separated string containing 'bing' and 'google'"
    })

    # ── CHECK 11: DDG maxResults is 25 ────────────────────────────────────────
    ddg_max = ddg.get("maxResults")
    ddg_max_ok = ddg_max == 25
    checks.append({
        "name": "duckduckgo_search.maxResults is 25",
        "passed": ddg_max_ok,
        "detail": f"Got: {ddg_max}, expected: 25"
    })

    # ── CHECK 12: conf.json.example was NOT blindly copied (timelimit not "oneMonth" or "m") ──
    # This is partially covered by checks 4 and 9, but let's make it explicit
    not_native_zhipu = zhipu_timelimit not in ("oneMonth", "oneWeek", "oneDay", "oneYear", "m", "w", "d", "y")
    not_native_ddg = ddg_timelimit not in ("m", "w", "d", "y", "oneMonth", "oneWeek")
    not_copy_ok = not_native_zhipu and not_native_ddg
    checks.append({
        "name": "No native timelimit values used (unified format enforced, example file not blindly copied)",
        "passed": not_copy_ok,
        "detail": f"zhipu timelimit='{zhipu_timelimit}', ddg timelimit='{ddg_timelimit}': neither should use native format"
    })

    return finalize(checks)


def finalize(checks):
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = passed_count / total if total > 0 else 0.0
    all_passed = all(c["passed"] for c in checks)
    return {
        "passed": all_passed,
        "score": round(score, 4),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "argument check", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))