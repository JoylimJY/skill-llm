#!/usr/bin/env python3
"""
Evaluation script for the Flutter GetX architecture scaffold task.
Checks:
1. core/ full structure exists (config, constants, navigation, utils, services, widgets)
2. shared/ full structure exists (data/base_business, data/local, data/download, data/upload, domain)
3. modules/shipment_tracking/ scaffolded correctly via validate.py (4 dart files + model/ + view/)
4. modules/warehouse_inventory/ scaffolded correctly via validate.py (4 dart files + model/ + view/)
5. modules/delivery_report/ exists (renamed from deliveryReport, snake_case)
6. delivery_report view file class ends with Page or View (not Widget)
7. delivery_report logic extends BaseController (not GetxController directly)
8. delivery_report files follow xxx_binding/logic/state/view naming pattern
9. No camelCase folder 'deliveryReport' still exists
10. Cross-module direct import removed from auth_logic.dart
"""

import sys
import json
import os
from pathlib import Path

def load_file(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def evaluate(workspace):
    workspace = Path(workspace)
    lib = workspace / "lib"
    checks = []

    # ── CHECK 1: core/ subdirectories exist ───────────────────────────────────
    core = lib / "core"
    required_core = ["config", "constants", "navigation", "utils", "services", "widgets"]
    missing_core = [d for d in required_core if not (core / d).is_dir()]
    checks.append(check(
        "core/ has all required subdirectories (config, constants, navigation, utils, services, widgets)",
        len(missing_core) == 0,
        f"Missing: {missing_core}" if missing_core else "All core subdirectories present"
    ))

    # ── CHECK 2: shared/ subdirectories exist ─────────────────────────────────
    shared = lib / "shared"
    required_shared_data = ["base_business", "local", "download", "upload"]
    missing_shared_data = [d for d in required_shared_data if not (shared / "data" / d).is_dir()]
    domain_exists = (shared / "domain").is_dir()
    shared_ok = len(missing_shared_data) == 0 and domain_exists
    checks.append(check(
        "shared/ has data/base_business, data/local, data/download, data/upload, and domain",
        shared_ok,
        f"Missing data subdirs: {missing_shared_data}; domain: {domain_exists}" if not shared_ok else "All shared subdirectories present"
    ))

    # ── CHECK 3: modules/shipment_tracking scaffolded ─────────────────────────
    st = lib / "modules" / "shipment_tracking"
    st_files = {
        "binding": st / "shipment_tracking_binding.dart",
        "logic":   st / "shipment_tracking_logic.dart",
        "state":   st / "shipment_tracking_state.dart",
        "view":    st / "shipment_tracking_view.dart",
    }
    st_dirs = [(st / "model").is_dir(), (st / "view").is_dir()]
    st_files_ok = all(f.is_file() for f in st_files.values())
    st_dirs_ok = all(st_dirs)
    checks.append(check(
        "modules/shipment_tracking/ has 4 dart files (binding/logic/state/view)",
        st_files_ok,
        f"Missing files: {[k for k,v in st_files.items() if not v.is_file()]}" if not st_files_ok else "All 4 files present"
    ))
    checks.append(check(
        "modules/shipment_tracking/ has model/ and view/ subdirectories",
        st_dirs_ok,
        f"model/ present: {st_dirs[0]}, view/ present: {st_dirs[1]}" if not st_dirs_ok else "Both subdirs present"
    ))

    # ── CHECK 4: shipment_tracking logic extends BaseController ───────────────
    st_logic = load_file(st / "shipment_tracking_logic.dart")
    if st_logic:
        extends_base = "BaseController" in st_logic and "extends BaseController" in st_logic
        extends_getx_direct = "extends GetxController" in st_logic
        logic_ok = extends_base and not extends_getx_direct
        checks.append(check(
            "shipment_tracking_logic.dart extends BaseController (not GetxController)",
            logic_ok,
            f"extends BaseController: {extends_base}, extends GetxController directly: {extends_getx_direct}"
        ))
    else:
        checks.append(check("shipment_tracking_logic.dart extends BaseController", False, "File not found"))

    # ── CHECK 5: shipment_tracking view class ends with Page or View ──────────
    st_view = load_file(st / "shipment_tracking_view.dart")
    if st_view:
        import re
        view_classes = re.findall(r'class\s+(\w+)\s+extends', st_view)
        view_ok = any(cls.endswith('Page') or cls.endswith('View') for cls in view_classes)
        widget_bad = any(cls.endswith('Widget') for cls in view_classes)
        checks.append(check(
            "shipment_tracking_view.dart class ends with Page or View (not Widget)",
            view_ok and not widget_bad,
            f"Classes found: {view_classes}"
        ))
    else:
        checks.append(check("shipment_tracking_view.dart class naming", False, "File not found"))

    # ── CHECK 6: modules/warehouse_inventory scaffolded ───────────────────────
    wi = lib / "modules" / "warehouse_inventory"
    wi_files = {
        "binding": wi / "warehouse_inventory_binding.dart",
        "logic":   wi / "warehouse_inventory_logic.dart",
        "state":   wi / "warehouse_inventory_state.dart",
        "view":    wi / "warehouse_inventory_view.dart",
    }
    wi_dirs = [(wi / "model").is_dir(), (wi / "view").is_dir()]
    wi_files_ok = all(f.is_file() for f in wi_files.values())
    wi_dirs_ok = all(wi_dirs)
    checks.append(check(
        "modules/warehouse_inventory/ has 4 dart files (binding/logic/state/view)",
        wi_files_ok,
        f"Missing files: {[k for k,v in wi_files.items() if not v.is_file()]}" if not wi_files_ok else "All 4 files present"
    ))
    checks.append(check(
        "modules/warehouse_inventory/ has model/ and view/ subdirectories",
        wi_dirs_ok,
        f"model/ present: {wi_dirs[0]}, view/ present: {wi_dirs[1]}" if not wi_dirs_ok else "Both subdirs present"
    ))

    # ── CHECK 7: warehouse_inventory logic extends BaseController ─────────────
    wi_logic = load_file(wi / "warehouse_inventory_logic.dart")
    if wi_logic:
        extends_base = "BaseController" in wi_logic and "extends BaseController" in wi_logic
        extends_getx_direct = "extends GetxController" in wi_logic
        logic_ok = extends_base and not extends_getx_direct
        checks.append(check(
            "warehouse_inventory_logic.dart extends BaseController (not GetxController)",
            logic_ok,
            f"extends BaseController: {extends_base}, extends GetxController directly: {extends_getx_direct}"
        ))
    else:
        checks.append(check("warehouse_inventory_logic.dart extends BaseController", False, "File not found"))

    # ── CHECK 8: warehouse_inventory view class ends with Page or View ────────
    wi_view = load_file(wi / "warehouse_inventory_view.dart")
    if wi_view:
        import re
        view_classes = re.findall(r'class\s+(\w+)\s+extends', wi_view)
        view_ok = any(cls.endswith('Page') or cls.endswith('View') for cls in view_classes)
        widget_bad = any(cls.endswith('Widget') for cls in view_classes)
        checks.append(check(
            "warehouse_inventory_view.dart class ends with Page or View (not Widget)",
            view_ok and not widget_bad,
            f"Classes found: {view_classes}"
        ))
    else:
        checks.append(check("warehouse_inventory_view.dart class naming", False, "File not found"))

    # ── CHECK 9: delivery_report module exists with snake_case folder ─────────
    dr = lib / "modules" / "delivery_report"
    dr_exists = dr.is_dir()
    checks.append(check(
        "modules/delivery_report/ exists (snake_case folder name)",
        dr_exists,
        "delivery_report/ directory found" if dr_exists else "delivery_report/ directory NOT found"
    ))

    # ── CHECK 10: camelCase deliveryReport folder no longer exists ─────────────
    bad_module = lib / "modules" / "deliveryReport"
    bad_gone = not bad_module.exists()
    checks.append(check(
        "modules/deliveryReport/ (camelCase) has been removed",
        bad_gone,
        "Correctly removed" if bad_gone else "Still exists — naming violation not fixed"
    ))

    # ── CHECK 11: delivery_report view file class ends with Page or View ──────
    import re
    # Search for any dart file in delivery_report that has a view class
    dr_view_file = None
    dr_view_content = None
    if dr_exists:
        # Look for file matching *_view.dart
        for f in dr.glob("*_view.dart"):
            dr_view_file = f
            dr_view_content = load_file(f)
            break
        # Also accept files that don't end in _view but contain Page/View class
        if not dr_view_file:
            for f in dr.glob("*.dart"):
                content = load_file(f)
                if content and re.search(r'class\s+\w+(Page|View)\s+extends', content):
                    dr_view_content = content
                    break

    if dr_view_content:
        view_classes = re.findall(r'class\s+(\w+)\s+extends', dr_view_content)
        view_ok = any(cls.endswith('Page') or cls.endswith('View') for cls in view_classes)
        widget_bad = any(cls.endswith('Widget') for cls in view_classes)
        checks.append(check(
            "delivery_report view class ends with Page or View (not Widget)",
            view_ok and not widget_bad,
            f"Classes found: {view_classes}"
        ))
    else:
        checks.append(check(
            "delivery_report view class ends with Page or View (not Widget)",
            False,
            "No *_view.dart file found in delivery_report/ or no Page/View class found"
        ))

    # ── CHECK 12: delivery_report logic extends BaseController ────────────────
    dr_logic_file = None
    dr_logic_content = None
    if dr_exists:
        for f in dr.glob("*_logic.dart"):
            dr_logic_file = f
            dr_logic_content = load_file(f)
            break

    if dr_logic_content:
        extends_base = "BaseController" in dr_logic_content and "extends BaseController" in dr_logic_content
        extends_getx_direct = "extends GetxController" in dr_logic_content
        logic_ok = extends_base and not extends_getx_direct
        checks.append(check(
            "delivery_report logic extends BaseController (not GetxController directly)",
            logic_ok,
            f"extends BaseController: {extends_base}, extends GetxController directly: {extends_getx_direct}"
        ))
    else:
        checks.append(check(
            "delivery_report logic extends BaseController",
            False,
            "No *_logic.dart file found in delivery_report/"
        ))

    # ── CHECK 13: delivery_report follows xxx_binding/logic/state/view naming ─
    if dr_exists:
        dart_files = list(dr.glob("*.dart"))
        expected_suffixes = {"_binding.dart", "_logic.dart", "_state.dart", "_view.dart"}
        found_suffixes = set()
        for f in dart_files:
            for suf in expected_suffixes:
                if f.name.endswith(suf):
                    found_suffixes.add(suf)
        naming_ok = expected_suffixes.issubset(found_suffixes)
        checks.append(check(
            "delivery_report/ contains files with _binding/_logic/_state/_view suffixes",
            naming_ok,
            f"Found suffixes: {found_suffixes}, expected: {expected_suffixes}"
        ))
    else:
        checks.append(check(
            "delivery_report/ naming convention check",
            False,
            "Directory does not exist"
        ))

    # ── CHECK 14: cross-module import removed from auth_logic.dart ────────────
    auth_logic = load_file(lib / "modules" / "auth" / "auth_logic.dart")
    if auth_logic:
        cross_import_removed = "deliveryReport" not in auth_logic and "../deliveryReport" not in auth_logic
        checks.append(check(
            "auth_logic.dart cross-module import of deliveryReport removed",
            cross_import_removed,
            "Cross-module import removed" if cross_import_removed else "Cross-module import still present"
        ))
    else:
        # If file doesn't exist, treat as possibly deleted/replaced
        checks.append(check(
            "auth_logic.dart cross-module import of deliveryReport removed",
            True,
            "auth_logic.dart not found — assuming cross-import was eliminated"
        ))

    # ── SCORE ─────────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    all_passed = passed_count == total

    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [], "error": "No workspace path provided"}))
        sys.exit(1)

    workspace_path = sys.argv[1]
    result = evaluate(workspace_path)
    print(json.dumps(result, indent=2))