import sys
import json
import os
import re
from pathlib import Path

def load_makefile_vars(filepath):
    """Parse Makefile-style KEY = VALUE or KEY := VALUE lines."""
    variables = {}
    try:
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("#") or not line:
                    continue
                # Match: KEY = VALUE or KEY := VALUE or KEY ?= VALUE
                m = re.match(r'^([A-Z_][A-Z0-9_]*)\s*(?::=|\?=|=)\s*(.*)$', line)
                if m:
                    key = m.group(1).strip()
                    value = m.group(2).strip()
                    variables[key] = value
    except Exception as e:
        return None, str(e)
    return variables, None

def run_checks(workspace):
    checks = []
    overall_passed = True

    # ---- LOCATE files ----
    # config.user must be at sonic-buildimage/rules/config.user
    config_user_path = Path(workspace) / "sonic-buildimage" / "rules" / "config.user"
    # runbook can be anywhere — search for it
    runbook_candidates = list(Path(workspace).rglob("runbook.md"))

    # ================================================================
    # CHECK 1: config.user exists
    # ================================================================
    check1_passed = config_user_path.exists()
    checks.append({
        "name": "config.user exists at sonic-buildimage/rules/config.user",
        "passed": check1_passed,
        "detail": f"Found: {config_user_path.exists()}"
    })
    if not check1_passed:
        overall_passed = False

    # ================================================================
    # Parse config.user
    # ================================================================
    cfg = {}
    parse_error = None
    if check1_passed:
        cfg, parse_error = load_makefile_vars(config_user_path)
        if cfg is None:
            cfg = {}

    # ================================================================
    # CHECK 2: SONIC_CONFIG_BUILD_JOBS = 4
    # (36GB RAM / 6GB per job = 6 max, but recommended is 4 per SKILL.md
    #  and rule: JOBS × 6GB ≤ 36GB → max 6, but recommended safe value is 4
    #  We accept 4, 5, or 6 as valid since 36/6=6 exactly)
    # ================================================================
    jobs_val = cfg.get("SONIC_CONFIG_BUILD_JOBS", "")
    # Accept 4, 5, or 6 (all satisfy 36GB constraint with 6GB/job rule)
    try:
        jobs_int = int(jobs_val)
        check2_passed = 1 < jobs_int <= 6
    except Exception:
        jobs_int = -1
        check2_passed = False

    checks.append({
        "name": "SONIC_CONFIG_BUILD_JOBS is a valid value (2-6) per RAM rule JOBS×6GB≤36GB",
        "passed": check2_passed,
        "detail": f"Got SONIC_CONFIG_BUILD_JOBS='{jobs_val}' (parsed int={jobs_int}). Must be >1 and <=6 per 36GB RAM / 6GB-per-job rule."
    })
    if not check2_passed:
        overall_passed = False

    # ================================================================
    # CHECK 3: BUILD_SKIP_TEST = y
    # ================================================================
    skip_test = cfg.get("BUILD_SKIP_TEST", "")
    check3_passed = skip_test.lower() == "y"
    checks.append({
        "name": "BUILD_SKIP_TEST = y",
        "passed": check3_passed,
        "detail": f"Got BUILD_SKIP_TEST='{skip_test}'. Expected 'y'."
    })
    if not check3_passed:
        overall_passed = False

    # ================================================================
    # CHECK 4: SONIC_BUILD_MEMORY = 24g
    # ================================================================
    mem_val = cfg.get("SONIC_BUILD_MEMORY", "")
    check4_passed = mem_val.lower() == "24g"
    checks.append({
        "name": "SONIC_BUILD_MEMORY = 24g",
        "passed": check4_passed,
        "detail": f"Got SONIC_BUILD_MEMORY='{mem_val}'. Expected '24g' (exactly, from SKILL.md recommendation)."
    })
    if not check4_passed:
        overall_passed = False

    # ================================================================
    # CHECK 5: DEFAULT_BUILD_LOG_TIMESTAMP = simple
    # ================================================================
    ts_val = cfg.get("DEFAULT_BUILD_LOG_TIMESTAMP", "")
    check5_passed = ts_val.lower() == "simple"
    checks.append({
        "name": "DEFAULT_BUILD_LOG_TIMESTAMP = simple",
        "passed": check5_passed,
        "detail": f"Got DEFAULT_BUILD_LOG_TIMESTAMP='{ts_val}'. Expected 'simple'."
    })
    if not check5_passed:
        overall_passed = False

    # ================================================================
    # CHECK 6: SONIC_DPKG_CACHE_METHOD = rwcache
    # ================================================================
    cache_method = cfg.get("SONIC_DPKG_CACHE_METHOD", "")
    check6_passed = cache_method.lower() == "rwcache"
    checks.append({
        "name": "SONIC_DPKG_CACHE_METHOD = rwcache",
        "passed": check6_passed,
        "detail": f"Got SONIC_DPKG_CACHE_METHOD='{cache_method}'. Expected 'rwcache'."
    })
    if not check6_passed:
        overall_passed = False

    # ================================================================
    # CHECK 7: SONIC_DPKG_CACHE_SOURCE = /var/cache/sonic/artifacts
    # ================================================================
    cache_src = cfg.get("SONIC_DPKG_CACHE_SOURCE", "")
    check7_passed = cache_src == "/var/cache/sonic/artifacts"
    checks.append({
        "name": "SONIC_DPKG_CACHE_SOURCE = /var/cache/sonic/artifacts",
        "passed": check7_passed,
        "detail": f"Got SONIC_DPKG_CACHE_SOURCE='{cache_src}'. Expected '/var/cache/sonic/artifacts'."
    })
    if not check7_passed:
        overall_passed = False

    # ================================================================
    # CHECK 8: SONIC_VERSION_CACHE_METHOD = cache
    # ================================================================
    ver_cache = cfg.get("SONIC_VERSION_CACHE_METHOD", "")
    check8_passed = ver_cache.lower() == "cache"
    checks.append({
        "name": "SONIC_VERSION_CACHE_METHOD = cache",
        "passed": check8_passed,
        "detail": f"Got SONIC_VERSION_CACHE_METHOD='{ver_cache}'. Expected 'cache'."
    })
    if not check8_passed:
        overall_passed = False

    # ================================================================
    # CHECK 9: config.user uses Makefile syntax (no 'export', no 'set', no '==' )
    # ================================================================
    makefile_syntax_ok = True
    syntax_detail = "Makefile syntax OK"
    if check1_passed:
        try:
            raw = config_user_path.read_text()
            non_comment_lines = [l.strip() for l in raw.splitlines()
                                  if l.strip() and not l.strip().startswith("#")]
            bad_lines = []
            for line in non_comment_lines:
                # Must match KEY = VALUE or KEY := VALUE or KEY ?= VALUE
                if not re.match(r'^[A-Z_][A-Z0-9_]*\s*(?::=|\?=|=)\s*.*$', line):
                    bad_lines.append(line)
            if bad_lines:
                makefile_syntax_ok = False
                syntax_detail = f"Non-Makefile lines found: {bad_lines[:3]}"
        except Exception as e:
            makefile_syntax_ok = False
            syntax_detail = f"Read error: {e}"

    checks.append({
        "name": "config.user uses valid Makefile KEY = VALUE syntax (no shell export, no YAML)",
        "passed": makefile_syntax_ok,
        "detail": syntax_detail
    })
    if not makefile_syntax_ok:
        overall_passed = False

    # ================================================================
    # CHECK 10: runbook.md exists and contains correct submodule fix command
    # ================================================================
    runbook_found = len(runbook_candidates) > 0
    runbook_path = runbook_candidates[0] if runbook_found else None

    runbook_content = ""
    if runbook_found:
        try:
            runbook_content = runbook_path.read_text()
        except Exception as e:
            runbook_content = ""

    checks.append({
        "name": "runbook.md file exists in workspace",
        "passed": runbook_found,
        "detail": f"Found at: {runbook_path}" if runbook_found else "runbook.md not found anywhere in workspace."
    })
    if not runbook_found:
        overall_passed = False

    # ================================================================
    # CHECK 11: runbook contains git submodule update --init --force for src/sonic-swss
    # The SKILL.md command: git submodule update --init --force src/<module>
    # ================================================================
    # Pattern: git submodule update --init --force src/sonic-swss  (order of flags may vary)
    submodule_cmd_pattern = re.compile(
        r'git\s+submodule\s+update\s+'
        r'(?=.*--init)(?=.*--force)'
        r'[\w\s\-]*\s+src/sonic-swss'
    )
    # Also accept: git submodule update --init --force src/sonic-swss (with flags in either order)
    alt_pattern = re.compile(
        r'git\s+submodule\s+update\s+(?:--init\s+--force|--force\s+--init)\s+src/sonic-swss'
    )
    check11_passed = bool(alt_pattern.search(runbook_content)) or bool(submodule_cmd_pattern.search(runbook_content))
    checks.append({
        "name": "runbook.md contains correct submodule fix command: git submodule update --init --force src/sonic-swss",
        "passed": check11_passed,
        "detail": (
            f"Pattern found: {check11_passed}. "
            f"Must contain 'git submodule update --init --force src/sonic-swss' (--force flag is mandatory per SKILL.md)."
        )
    })
    if not check11_passed:
        overall_passed = False

    # ================================================================
    # CHECK 12: runbook also addresses libswsscommon (corrupted submodule)
    # The workspace shows libswsscommon is also corrupted
    # ================================================================
    libswss_pattern = re.compile(
        r'git\s+submodule\s+update\s+(?:--init\s+--force|--force\s+--init)\s+src/libswsscommon'
    )
    check12_passed = bool(libswss_pattern.search(runbook_content))
    checks.append({
        "name": "runbook.md contains fix command for src/libswsscommon (also corrupted)",
        "passed": check12_passed,
        "detail": (
            f"Pattern found: {check12_passed}. "
            "Expected 'git submodule update --init --force src/libswsscommon' in runbook."
        )
    })
    if not check12_passed:
        overall_passed = False

    # ================================================================
    # Compute score
    # ================================================================
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / len(checks), 3)

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace)
    print(json.dumps(result, indent=2))