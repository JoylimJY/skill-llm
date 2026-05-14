import sys
import json
import os
import re
from pathlib import Path

workspace = sys.argv[1]

checks = []
score = 0.0
total_weight = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    global score, total_weight
    total_weight += weight
    if passed:
        score += weight

# ── 1. Custom config file exists and is valid JSON ──────────────────────────
config_candidates = list(Path(workspace).rglob("*.json"))
custom_config_path = None
REQUIRED_CONFIG_FIELDS = {"logLevel", "proxies", "maxSessions", "sessionTTL", "rotationStrategy", "maxProxyFailures"}

for cp in config_candidates:
    # Skip package.json, package-lock.json, sessions.json, proxy-state.json, broken originals
    if cp.name in ("package.json", "package-lock.json", "sessions.json", "proxy-state.json"):
        continue
    if "deprecated" in str(cp) or "staging" in str(cp) or "node_modules" in str(cp):
        continue
    try:
        with open(cp) as f:
            data = json.load(f)
        if REQUIRED_CONFIG_FIELDS.issubset(set(data.keys())):
            custom_config_path = cp
            break
    except Exception:
        continue

add_check(
    "custom_config_file_exists",
    custom_config_path is not None,
    f"Found valid config at: {custom_config_path}" if custom_config_path else "No valid config file with all required fields found.",
    weight=1.5
)

custom_config = {}
if custom_config_path:
    try:
        with open(custom_config_path) as f:
            custom_config = json.load(f)
    except Exception as e:
        add_check("custom_config_parseable", False, f"Config parse error: {e}", weight=1.0)
        custom_config = {}

# ── 2. rotationStrategy is one of the valid values ──────────────────────────
if custom_config:
    valid_strategies = {"round-robin", "least-used", "random"}
    rs = custom_config.get("rotationStrategy", "")
    add_check(
        "rotation_strategy_valid",
        rs in valid_strategies,
        f"rotationStrategy='{rs}'. Must be one of {valid_strategies}. Note: 'round_robin' (underscore) is INVALID.",
        weight=2.0
    )
else:
    add_check("rotation_strategy_valid", False, "Config not loaded, cannot check rotationStrategy.", weight=2.0)

# ── 3. sessionTTL is in milliseconds (>= 60000, i.e., not raw seconds) ──────
if custom_config:
    ttl = custom_config.get("sessionTTL", 0)
    try:
        ttl = int(ttl)
        ttl_ok = ttl >= 60000  # At minimum 1 minute in ms; seconds would be tiny (e.g., 3600)
    except Exception:
        ttl_ok = False
    add_check(
        "sessionTTL_in_milliseconds",
        ttl_ok,
        f"sessionTTL={ttl}. Must be in milliseconds (e.g., 3600000 for 1 hour). Values like 3600 indicate seconds (wrong unit).",
        weight=2.0
    )
else:
    add_check("sessionTTL_in_milliseconds", False, "Config not loaded.", weight=2.0)

# ── 4. proxies list has at least 2 entries with correct schema ───────────────
if custom_config:
    proxies = custom_config.get("proxies", [])
    valid_proxies = []
    for p in proxies:
        if isinstance(p, dict) and "host" in p and "port" in p and "protocol" in p:
            valid_proxies.append(p)
    add_check(
        "proxies_configured",
        len(valid_proxies) >= 2,
        f"Found {len(valid_proxies)} valid proxy entries (need >=2 with host/port/protocol).",
        weight=1.5
    )
else:
    add_check("proxies_configured", False, "Config not loaded.", weight=1.5)

# ── 5. Find the audit_report.json file ──────────────────────────────────────
report_candidates = list(Path(workspace).rglob("audit_report.json"))
report_path = report_candidates[0] if report_candidates else None

add_check(
    "audit_report_exists",
    report_path is not None,
    f"audit_report.json found at: {report_path}" if report_path else "audit_report.json not found anywhere in workspace.",
    weight=1.5
)

report_data = {}
if report_path:
    try:
        with open(report_path) as f:
            report_data = json.load(f)
        add_check("audit_report_valid_json", True, "audit_report.json is valid JSON.", weight=0.5)
    except Exception as e:
        add_check("audit_report_valid_json", False, f"audit_report.json parse error: {e}", weight=0.5)

# ── 6. Report contains session workflow evidence ─────────────────────────────
if report_data:
    # Must have sessions info (from session-list or diagnostics)
    has_sessions = (
        "sessions" in report_data or
        "activeSessions" in report_data or
        "totalSessions" in report_data or
        (isinstance(report_data.get("diagnostics"), dict) and "sessions" in report_data["diagnostics"])
    )
    add_check(
        "report_has_session_data",
        has_sessions,
        f"Report session fields present: {has_sessions}. Keys: {list(report_data.keys())}",
        weight=1.5
    )
else:
    add_check("report_has_session_data", False, "No report data to check.", weight=1.5)

# ── 7. Report contains proxy health evidence ─────────────────────────────────
if report_data:
    has_proxies = (
        "proxies" in report_data or
        "proxiesTotal" in report_data or
        "proxiesHealthy" in report_data or
        (isinstance(report_data.get("diagnostics"), dict) and "proxies" in report_data["diagnostics"]) or
        "proxyHealth" in report_data or
        "proxy_health" in report_data
    )
    add_check(
        "report_has_proxy_data",
        has_proxies,
        f"Report proxy fields present: {has_proxies}. Keys: {list(report_data.keys())}",
        weight=1.5
    )
else:
    add_check("report_has_proxy_data", False, "No report data to check.", weight=1.5)

# ── 8. Report contains detection results ─────────────────────────────────────
if report_data:
    has_detection = (
        "detectionResults" in report_data or
        "detection" in report_data or
        "restrictions" in report_data or
        "restrictionDetection" in report_data
    )
    add_check(
        "report_has_detection_data",
        has_detection,
        f"Report detection fields present: {has_detection}. Keys: {list(report_data.keys())}",
        weight=1.5
    )
else:
    add_check("report_has_detection_data", False, "No report data to check.", weight=1.5)

# ── 9. sessions.json exists (evidence session commands were run) ──────────────
sessions_file = Path(workspace) / "skill" / "assets" / "sessions.json"
sessions_ok = False
sessions_data = []
try:
    if sessions_file.exists():
        with open(sessions_file) as f:
            sessions_data = json.load(f)
        sessions_ok = isinstance(sessions_data, list)
except Exception as e:
    sessions_ok = False

add_check(
    "sessions_state_file_exists",
    sessions_ok,
    f"sessions.json found and valid: {sessions_ok}. Count: {len(sessions_data)}",
    weight=1.0
)

# ── 10. proxy-state.json exists (evidence proxy commands were run) ────────────
proxy_state_file = Path(workspace) / "skill" / "assets" / "proxy-state.json"
proxy_state_ok = False
proxy_state_data = []
try:
    if proxy_state_file.exists():
        with open(proxy_state_file) as f:
            proxy_state_data = json.load(f)
        proxy_state_ok = isinstance(proxy_state_data, list) and len(proxy_state_data) > 0
except Exception as e:
    proxy_state_ok = False

add_check(
    "proxy_state_file_exists_and_populated",
    proxy_state_ok,
    f"proxy-state.json found and populated: {proxy_state_ok}. Entries: {len(proxy_state_data)}",
    weight=1.0
)

# ── 11. At least one proxy was added via proxy-add command ───────────────────
if proxy_state_ok and proxy_state_data:
    # The original broken config had 0 proxies; any entry means proxy-add was used
    add_check(
        "proxy_added_via_cli",
        len(proxy_state_data) >= 1,
        f"proxy-state has {len(proxy_state_data)} entries, indicating proxy-add was run.",
        weight=1.0
    )
else:
    add_check("proxy_added_via_cli", False, "No proxy state data found.", weight=1.0)

# ── 12. Session rotation was performed (inactive sessions present) ────────────
if sessions_ok and sessions_data:
    inactive = [s for s in sessions_data if not s.get("active", True)]
    has_rotation = len(inactive) > 0
    add_check(
        "session_rotation_evidence",
        has_rotation,
        f"Inactive sessions found: {len(inactive)}. session-rotate leaves previous sessions inactive.",
        weight=1.0
    )
else:
    add_check("session_rotation_evidence", False, "No sessions data.", weight=1.0)

# ── Compute final score ───────────────────────────────────────────────────────
final_score = round(score / total_weight, 4) if total_weight > 0 else 0.0
all_passed = all(c["passed"] for c in checks)

print(json.dumps({
    "passed": final_score >= 0.75,
    "score": final_score,
    "checks": checks
}, indent=2))