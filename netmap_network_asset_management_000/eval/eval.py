import sys
import json
import os
from pathlib import Path
from datetime import datetime, timedelta

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []
passed_all = True

def check(name, condition, detail):
    global passed_all
    result = bool(condition)
    if not result:
        passed_all = False
    checks.append({"name": name, "passed": result, "detail": detail})
    return result

# --- Load the device database (the ground truth modified by the agent) ---
db_path = Path.home() / ".config" / "netmap" / "devices.json"

try:
    with open(db_path) as f:
        db = json.load(f)
    devices = db.get("devices", {})
    db_loaded = True
except Exception as e:
    db_loaded = False
    devices = {}
    check("db_loadable", False, f"Failed to load device database at {db_path}: {e}")

if db_loaded:
    check("db_loadable", True, f"Device database loaded successfully with {len(devices)} devices.")

# --- Check 1: Gateway labeled correctly ---
try:
    gateway = devices.get("192.168.1.1", {})
    gw_label = gateway.get("label", "") or ""
    # Accept any reasonable label containing "gateway" or "router" (case-insensitive)
    gw_ok = bool(gw_label.strip()) and any(
        word in gw_label.lower() for word in ["gateway", "router", "main router", "office router", "network gateway"]
    )
    check(
        "gateway_labeled",
        gw_ok,
        f"Gateway (192.168.1.1) label='{gw_label}'. Expected a label containing 'gateway' or 'router'."
    )
except Exception as e:
    check("gateway_labeled", False, f"Exception checking gateway label: {e}")

# --- Check 2: NAS labeled correctly ---
try:
    nas = devices.get("192.168.1.10", {})
    nas_label = nas.get("label", "") or ""
    nas_ok = bool(nas_label.strip()) and any(
        word in nas_label.lower() for word in ["nas", "storage", "file server", "network storage", "synology"]
    )
    check(
        "nas_labeled",
        nas_ok,
        f"NAS (192.168.1.10) label='{nas_label}'. Expected a label containing 'nas', 'storage', or similar."
    )
except Exception as e:
    check("nas_labeled", False, f"Exception checking NAS label: {e}")

# --- Check 3: Printer labeled correctly ---
try:
    printer = devices.get("192.168.1.20", {})
    printer_label = printer.get("label", "") or ""
    printer_ok = bool(printer_label.strip()) and any(
        word in printer_label.lower() for word in ["printer", "canon", "print", "mfp", "copier"]
    )
    check(
        "printer_labeled",
        printer_ok,
        f"Printer (192.168.1.20) label='{printer_label}'. Expected a label containing 'printer', 'Canon', or similar."
    )
except Exception as e:
    check("printer_labeled", False, f"Exception checking printer label: {e}")

# --- Check 4: At least 3 devices total have non-empty labels ---
try:
    labeled_count = sum(1 for dev in devices.values() if dev.get("label", "").strip())
    check(
        "minimum_three_labels",
        labeled_count >= 3,
        f"Found {labeled_count} labeled device(s). Need at least 3."
    )
except Exception as e:
    check("minimum_three_labels", False, f"Exception counting labels: {e}")

# --- Check 5: Export file exists as network_inventory.json ---
try:
    export_files = list(workspace.rglob("network_inventory.json"))
    # Also check current working directory / root
    if not export_files:
        for extra_path in [Path("/root/network_inventory.json"), Path("/tmp/network_inventory.json"), Path("/network_inventory.json")]:
            if extra_path.exists():
                export_files.append(extra_path)
    
    export_found = len(export_files) > 0
    check(
        "export_file_exists",
        export_found,
        f"Found network_inventory.json at: {[str(p) for p in export_files]}" if export_found else "network_inventory.json not found anywhere."
    )
except Exception as e:
    check("export_file_exists", False, f"Exception searching for export file: {e}")

# --- Check 6: Export file is valid JSON and contains devices ---
try:
    export_files = list(workspace.rglob("network_inventory.json"))
    if not export_files:
        for extra_path in [Path("/root/network_inventory.json"), Path("/tmp/network_inventory.json"), Path("/network_inventory.json")]:
            if extra_path.exists():
                export_files.append(extra_path)
    
    if export_files:
        with open(export_files[0]) as f:
            exported = json.load(f)
        
        exported_devices = exported.get("devices", {})
        export_valid = len(exported_devices) >= 5  # Should have at least all original devices
        check(
            "export_file_valid_content",
            export_valid,
            f"Export file contains {len(exported_devices)} device(s). Expected >=5."
        )
        
        # Check that labels are preserved in the export
        export_has_labels = any(
            dev.get("label", "").strip()
            for dev in exported_devices.values()
        )
        check(
            "export_preserves_labels",
            export_has_labels,
            f"Export {'contains' if export_has_labels else 'does NOT contain'} labeled devices."
        )
    else:
        check("export_file_valid_content", False, "Export file not found, skipping content check.")
        check("export_preserves_labels", False, "Export file not found, skipping label check.")
except Exception as e:
    check("export_file_valid_content", False, f"Exception reading export file: {e}")
    check("export_preserves_labels", False, f"Exception reading export file: {e}")

# --- Check 7: Agent discovered new devices (recent_devices.txt or noted in any output file) ---
# We check if agent produced any file that references the new devices (101, 102, 103)
try:
    new_device_ips = {"192.168.1.101", "192.168.1.102", "192.168.1.103"}
    
    # Look for any text/json file in workspace that references these IPs
    candidate_files = (
        list(workspace.rglob("*.txt")) +
        list(workspace.rglob("*.json")) +
        list(workspace.rglob("*.md")) +
        list(workspace.rglob("*.log")) +
        list(workspace.rglob("*.csv"))
    )
    
    found_new_devices = set()
    for f in candidate_files:
        try:
            content = f.read_text(errors='ignore')
            for ip in new_device_ips:
                if ip in content:
                    found_new_devices.add(ip)
        except Exception:
            pass
    
    # Also check if network_inventory.json contains all three new devices
    export_files = list(workspace.rglob("network_inventory.json"))
    if not export_files:
        for extra_path in [Path("/root/network_inventory.json"), Path("/tmp/network_inventory.json"), Path("/network_inventory.json")]:
            if extra_path.exists():
                export_files.append(extra_path)
    
    if export_files:
        try:
            content = export_files[0].read_text()
            for ip in new_device_ips:
                if ip in content:
                    found_new_devices.add(ip)
        except Exception:
            pass
    
    new_discovery_ok = len(found_new_devices) >= 2
    check(
        "new_devices_identified",
        new_discovery_ok,
        f"New devices (joined last 60min) found in agent output: {found_new_devices}. Expected at least 2 of {new_device_ips}."
    )
except Exception as e:
    check("new_devices_identified", False, f"Exception checking new device discovery: {e}")

# --- Check 8: Labels survive a re-scan (verify label fields still present after potential scan operations) ---
try:
    # If the agent ran a scan after labeling, labels must still be present
    # We re-read the DB (already loaded above)
    labels_after_ops = {
        ip: dev.get("label", "").strip()
        for ip, dev in devices.items()
        if dev.get("label", "").strip()
    }
    labels_survived = len(labels_after_ops) >= 3
    check(
        "labels_survive_operations",
        labels_survived,
        f"Labels present in final DB: {labels_after_ops}. Labels must persist across all operations."
    )
except Exception as e:
    check("labels_survive_operations", False, f"Exception verifying label persistence: {e}")

# --- Final Score ---
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 3) if total > 0 else 0.0
passed_all = all(c["passed"] for c in checks)

result = {
    "passed": passed_all,
    "score": score,
    "checks": checks
}
print(json.dumps(result, indent=2))