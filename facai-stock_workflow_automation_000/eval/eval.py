import sys, json, os, subprocess, signal
from pathlib import Path

workspace = sys.argv[1]

checks = []

def check(name, condition, detail):
    checks.append({"name": name, "passed": bool(condition), "detail": detail})
    return bool(condition)

# ── 1. data/config.json exists and monitor_target is set correctly ──────
config_path = Path(workspace) / "data" / "config.json"
try:
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    target = cfg.get("monitor_target", "")
    ok = isinstance(target, str) and target.startswith("user:ou_") and len(target) > 8
    check(
        "config_monitor_target_set",
        ok,
        f"monitor_target={target!r}; must start with 'user:ou_' and be non-trivial"
    )
except Exception as e:
    check("config_monitor_target_set", False, f"Could not read data/config.json: {e}")

# ── 2. data/watchlist.json exists ────────────────────────────────────────
wl_path = Path(workspace) / "data" / "watchlist.json"
try:
    wl = json.loads(wl_path.read_text(encoding="utf-8"))
    check("watchlist_file_exists", isinstance(wl, list), f"watchlist.json content: {wl!r}")
except Exception as e:
    check("watchlist_file_exists", False, f"Could not read data/watchlist.json: {e}")
    wl = []

# ── 3. watchlist contains >= 3 stocks ────────────────────────────────────
codes_in_wl = {item.get("code") for item in wl if isinstance(item, dict)}
check(
    "watchlist_has_at_least_3_stocks",
    len(codes_in_wl) >= 3,
    f"Found {len(codes_in_wl)} unique stock codes: {codes_in_wl}"
)

# ── 4. watchlist includes 贵州茅台 (600519) ──────────────────────────────
check(
    "watchlist_contains_600519_maotai",
    "600519" in codes_in_wl,
    f"600519 (贵州茅台) present: {'600519' in codes_in_wl}; all codes: {codes_in_wl}"
)

# ── 5. watchlist includes 宁德时代 (300750) ──────────────────────────────
check(
    "watchlist_contains_300750_catl",
    "300750" in codes_in_wl,
    f"300750 (宁德时代) present: {'300750' in codes_in_wl}; all codes: {codes_in_wl}"
)

# ── 6. watchlist includes 招商银行 (600036) ──────────────────────────────
check(
    "watchlist_contains_600036_cmb",
    "600036" in codes_in_wl,
    f"600036 (招商银行) present: {'600036' in codes_in_wl}; all codes: {codes_in_wl}"
)

# ── 7. monitor params file exists with custom interval and threshold ─────
params_path = Path(workspace) / "data" / "monitor_params.json"
try:
    params = json.loads(params_path.read_text(encoding="utf-8"))
    interval_ok = int(params.get("interval", 0)) == 20
    threshold_ok = abs(float(params.get("threshold", 0)) - 1.0) < 0.01
    check(
        "monitor_params_interval_20",
        interval_ok,
        f"interval={params.get('interval')!r}, expected 20"
    )
    check(
        "monitor_params_threshold_1_0",
        threshold_ok,
        f"threshold={params.get('threshold')!r}, expected 1.0"
    )
except Exception as e:
    check("monitor_params_interval_20", False, f"Could not read monitor_params.json: {e}")
    check("monitor_params_threshold_1_0", False, f"Could not read monitor_params.json: {e}")

# ── 8. monitor is actually running (PID file + process alive) ────────────
pid_path = Path(workspace) / "data" / "monitor.pid"
try:
    pid = int(pid_path.read_text().strip())
    os.kill(pid, 0)   # raises if not running
    check("monitor_process_running", True, f"Monitor process alive at PID={pid}")
except FileNotFoundError:
    check("monitor_process_running", False, "data/monitor.pid not found")
except (ProcessLookupError, PermissionError) as e:
    check("monitor_process_running", False, f"Process not alive: {e}")
except Exception as e:
    check("monitor_process_running", False, f"Unexpected error: {e}")

# ── 9. monitor params target matches config monitor_target ───────────────
try:
    cfg2 = json.loads(config_path.read_text(encoding="utf-8"))
    p2   = json.loads(params_path.read_text(encoding="utf-8"))
    match = cfg2.get("monitor_target") == p2.get("target")
    check(
        "monitor_target_consistent",
        match,
        f"config target={cfg2.get('monitor_target')!r} vs params target={p2.get('target')!r}"
    )
except Exception as e:
    check("monitor_target_consistent", False, f"Could not compare targets: {e}")

# ── cleanup: kill spawned monitor worker so container exits cleanly ───────
try:
    pid_path2 = Path(workspace) / "data" / "monitor.pid"
    if pid_path2.exists():
        os.kill(int(pid_path2.read_text().strip()), signal.SIGTERM)
except Exception:
    pass

# ── scoring ───────────────────────────────────────────────────────────────
passed_count = sum(1 for c in checks if c["passed"])
total = len(checks)
score = round(passed_count / total, 4)
all_passed = passed_count == total

result = {"passed": all_passed, "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False, indent=2))