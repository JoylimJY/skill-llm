import sys
import json
import os
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    
    # --- Check 1: Find the server_health_report.json file ---
    report_files = list(Path(workspace_dir).rglob("server_health_report.json"))
    if not report_files:
        checks.append({"name": "report_file_exists", "passed": False, "detail": "server_health_report.json not found anywhere in workspace"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    # Use the first found (prefer workspace root)
    report_path = None
    for f in report_files:
        if f.parent == Path(workspace_dir):
            report_path = f
            break
    if report_path is None:
        report_path = report_files[0]
    
    checks.append({"name": "report_file_exists", "passed": True, "detail": f"Found at {report_path}"})
    
    # --- Check 2: Valid JSON ---
    try:
        with open(report_path, "r") as f:
            report = json.load(f)
        checks.append({"name": "valid_json", "passed": True, "detail": "File is valid JSON"})
    except Exception as e:
        checks.append({"name": "valid_json", "passed": False, "detail": f"JSON parse error: {e}"})
        return {"passed": False, "score": 1/11, "checks": checks}
    
    # --- Check 3: Report contains entries for all 3 servers ---
    # The servers are localhost:25565, localhost:25566, localhost:25999
    # Report can be a list or a dict with a 'servers' key
    servers_data = None
    if isinstance(report, list):
        servers_data = report
    elif isinstance(report, dict):
        # Try common keys
        for key in ["servers", "results", "checks", "data", "fleet", "status"]:
            if key in report and isinstance(report[key], list):
                servers_data = report[key]
                break
        if servers_data is None:
            # Maybe it's a dict keyed by server address
            servers_data = list(report.values()) if report else []
    
    if not servers_data or len(servers_data) < 3:
        checks.append({"name": "three_server_entries", "passed": False, 
                       "detail": f"Expected 3 server entries, got {len(servers_data) if servers_data else 0}"})
    else:
        checks.append({"name": "three_server_entries", "passed": True, 
                       "detail": f"Found {len(servers_data)} server entries"})
    
    # Helper: find server entry by address pattern
    def find_server_entry(data, port):
        """Find entry whose address/server field contains the given port."""
        for entry in data:
            if not isinstance(entry, dict):
                continue
            # Check various field names for address
            addr_str = ""
            for field in ["address", "server", "host", "hostname", "name", "server_address", "target"]:
                v = entry.get(field, "")
                if v:
                    addr_str = str(v)
                    break
            if str(port) in addr_str or f":{port}" in addr_str:
                return entry
            # Also check if port is a separate field
            if entry.get("port") == port or str(entry.get("port", "")) == str(port):
                return entry
        return None
    
    if servers_data:
        entry_25565 = find_server_entry(servers_data, 25565)
        entry_25566 = find_server_entry(servers_data, 25566)
        entry_25999 = find_server_entry(servers_data, 25999)
    else:
        entry_25565 = entry_25566 = entry_25999 = None
    
    # --- Check 4: localhost:25565 is online ---
    def is_truthy_online(val):
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.lower() in ("true", "online", "yes", "1", "up")
        if isinstance(val, int):
            return val == 1
        return False
    
    def is_falsy_online(val):
        if isinstance(val, bool):
            return not val
        if isinstance(val, str):
            return val.lower() in ("false", "offline", "no", "0", "down")
        if isinstance(val, int):
            return val == 0
        return False
    
    if entry_25565 is None:
        checks.append({"name": "server_25565_found", "passed": False, "detail": "No entry for localhost:25565 in report"})
    else:
        checks.append({"name": "server_25565_found", "passed": True, "detail": f"Found entry: {json.dumps(entry_25565)[:200]}"})
    
    # --- Check 5: 25565 marked online ---
    if entry_25565:
        online_val = None
        for field in ["online", "status", "is_online", "reachable", "up", "alive"]:
            if field in entry_25565:
                online_val = entry_25565[field]
                break
        
        if online_val is not None and is_truthy_online(online_val):
            checks.append({"name": "server_25565_online", "passed": True, "detail": f"online field = {online_val}"})
        else:
            checks.append({"name": "server_25565_online", "passed": False, 
                          "detail": f"Expected online=true for 25565, got online_field={online_val}, full_entry={json.dumps(entry_25565)[:200]}"})
    else:
        checks.append({"name": "server_25565_online", "passed": False, "detail": "No entry for 25565"})
    
    # --- Check 6: 25565 has version 1.20.4 ---
    if entry_25565:
        version_val = entry_25565.get("version", entry_25565.get("server_version", entry_25565.get("mc_version", "")))
        if version_val and "1.20.4" in str(version_val):
            checks.append({"name": "server_25565_version", "passed": True, "detail": f"Version: {version_val}"})
        else:
            checks.append({"name": "server_25565_version", "passed": False, 
                          "detail": f"Expected version 1.20.4 for 25565, got '{version_val}'"})
    else:
        checks.append({"name": "server_25565_version", "passed": False, "detail": "No entry for 25565"})
    
    # --- Check 7: 25565 has player count 3/20 ---
    if entry_25565:
        po = entry_25565.get("players_online", entry_25565.get("online_players", entry_25565.get("current_players",
             entry_25565.get("players", {}) if isinstance(entry_25565.get("players"), dict) else None)))
        pm = entry_25565.get("players_max", entry_25565.get("max_players", 
             entry_25565.get("players", {}) if isinstance(entry_25565.get("players"), dict) else None))
        
        # Handle nested players object
        if isinstance(entry_25565.get("players"), dict):
            players_obj = entry_25565["players"]
            po = players_obj.get("online", players_obj.get("current", players_obj.get("count", po)))
            pm = players_obj.get("max", players_obj.get("maximum", pm))
        
        players_correct = (str(po) == "3" and str(pm) == "20")
        if players_correct:
            checks.append({"name": "server_25565_players", "passed": True, "detail": f"Players: {po}/{pm}"})
        else:
            checks.append({"name": "server_25565_players", "passed": False,
                          "detail": f"Expected 3/20 for 25565, got online={po} max={pm}"})
    else:
        checks.append({"name": "server_25565_players", "passed": False, "detail": "No entry for 25565"})
    
    # --- Check 8: 25565 has player list with expected players ---
    if entry_25565:
        plist = entry_25565.get("player_list", entry_25565.get("players_list", entry_25565.get("online_players_list",
                entry_25565.get("sample", None))))
        if isinstance(entry_25565.get("players"), dict):
            plist = plist or entry_25565["players"].get("sample", entry_25565["players"].get("list", []))
        
        expected_players = {"SteveBuilder", "AlexCrafter", "DiamondMiner"}
        if plist and isinstance(plist, list):
            # Flatten: plist might be list of strings or list of dicts
            names = set()
            for p in plist:
                if isinstance(p, str):
                    names.add(p)
                elif isinstance(p, dict):
                    names.add(p.get("name", ""))
            found = expected_players.intersection(names)
            if len(found) >= 2:
                checks.append({"name": "server_25565_player_list", "passed": True, 
                               "detail": f"Found players: {names}"})
            else:
                checks.append({"name": "server_25565_player_list", "passed": False,
                               "detail": f"Expected players {expected_players}, found {names}"})
        else:
            checks.append({"name": "server_25565_player_list", "passed": False,
                          "detail": f"Player list missing or not a list: {plist}"})
    else:
        checks.append({"name": "server_25565_player_list", "passed": False, "detail": "No entry for 25565"})
    
    # --- Check 9: localhost:25566 is online with version 1.19.4, 0 players ---
    if entry_25566 is None:
        checks.append({"name": "server_25566_correct", "passed": False, "detail": "No entry for localhost:25566 in report"})
    else:
        online_val = None
        for field in ["online", "status", "is_online", "reachable", "up", "alive"]:
            if field in entry_25566:
                online_val = entry_25566[field]
                break
        
        version_val = entry_25566.get("version", entry_25566.get("server_version", entry_25566.get("mc_version", "")))
        
        po = entry_25566.get("players_online", entry_25566.get("online_players", entry_25566.get("current_players", None)))
        if isinstance(entry_25566.get("players"), dict):
            po = entry_25566["players"].get("online", entry_25566["players"].get("current", po))
        
        online_ok = online_val is not None and is_truthy_online(online_val)
        version_ok = "1.19.4" in str(version_val)
        players_ok = str(po) == "0"
        
        detail = f"online={online_val}({online_ok}), version={version_val}({version_ok}), players_online={po}({players_ok})"
        if online_ok and version_ok and players_ok:
            checks.append({"name": "server_25566_correct", "passed": True, "detail": detail})
        else:
            checks.append({"name": "server_25566_correct", "passed": False, "detail": detail})
    
    # --- Check 10: localhost:25999 is offline ---
    if entry_25999 is None:
        checks.append({"name": "server_25999_found", "passed": False, "detail": "No entry for localhost:25999 in report"})
    else:
        online_val = None
        for field in ["online", "status", "is_online", "reachable", "up", "alive"]:
            if field in entry_25999:
                online_val = entry_25999[field]
                break
        
        if online_val is not None and is_falsy_online(online_val):
            checks.append({"name": "server_25999_found", "passed": True, 
                          "detail": f"Correctly marked offline: online={online_val}"})
        else:
            checks.append({"name": "server_25999_found", "passed": False,
                          "detail": f"Expected offline for 25999, got online={online_val}, entry={json.dumps(entry_25999)[:200]}"})
    
    # --- Check 11: 25999 has null/None for version and players (offline) ---
    if entry_25999 and entry_25999 is not None:
        version_val = entry_25999.get("version", entry_25999.get("server_version", "NOTSET"))
        po = entry_25999.get("players_online", entry_25999.get("online_players", "NOTSET"))
        if isinstance(entry_25999.get("players"), dict):
            po = entry_25999["players"].get("online", po)
        
        # For offline servers, these should be null/None or absent
        version_null = (version_val is None or version_val == "NOTSET" or version_val == "" or version_val == "N/A" or str(version_val).lower() in ("null", "none", "unknown", "n/a", "-"))
        players_null = (po is None or po == "NOTSET" or po == "" or str(po).lower() in ("null", "none", "n/a", "-"))
        
        if version_null and players_null:
            checks.append({"name": "server_25999_null_fields", "passed": True,
                          "detail": f"Offline server has null/absent version and player data: version={version_val}, players_online={po}"})
        else:
            # Partial credit: at least version null
            if version_null or players_null:
                checks.append({"name": "server_25999_null_fields", "passed": True,
                              "detail": f"Offline server has appropriate null fields. version={version_val}, po={po}"})
            else:
                checks.append({"name": "server_25999_null_fields", "passed": False,
                              "detail": f"Expected null fields for offline server, got version={version_val}, players_online={po}"})
    else:
        checks.append({"name": "server_25999_null_fields", "passed": False, "detail": "No entry for 25999"})
    
    # --- Compute score ---
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks
    
    # Must pass at minimum: file exists, valid JSON, 25565 online+version+players, 25999 offline
    critical = ["report_file_exists", "valid_json", "three_server_entries", 
                "server_25565_online", "server_25565_version", "server_25999_found"]
    all_critical_passed = all(
        next((c["passed"] for c in checks if c["name"] == name), False)
        for name in critical
    )
    
    overall_passed = all_critical_passed and score >= 0.7
    
    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))