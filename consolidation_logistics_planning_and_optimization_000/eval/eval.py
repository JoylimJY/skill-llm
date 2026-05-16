import sys
import json
import re
import subprocess
from pathlib import Path

def run_check(name, fn):
    try:
        passed, detail = fn()
        return {"name": name, "passed": passed, "detail": detail}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Exception: {e}"}

def find_report(workspace):
    candidates = list(Path(workspace).rglob("consolidation_report.json"))
    if not candidates:
        return None
    # Prefer files not inside data/raw (those are inputs)
    for c in candidates:
        if "raw" not in str(c) and "archive" not in str(c):
            return c
    return candidates[0]

def load_report(workspace):
    path = find_report(workspace)
    if path is None:
        raise FileNotFoundError("consolidation_report.json not found anywhere in workspace")
    with open(path) as f:
        return json.load(f), path

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []

    # ── Check 0: File exists ──────────────────────────────────────────────────
    def check_file_exists():
        path = find_report(workspace)
        if path is None:
            return False, "consolidation_report.json not found in workspace"
        return True, f"Found at {path}"
    checks.append(run_check("report_file_exists", check_file_exists))

    # Load report once for subsequent checks
    report = None
    report_path = None
    try:
        report, report_path = load_report(workspace)
    except Exception as e:
        for name in [
            "report_is_valid_json",
            "groups_present",
            "dest_hub_grouping_correct",
            "lcl_strategy_mentioned",
            "milkrun_or_supplier_grouping",
            "savings_or_cost_analysis",
            "planning_window_or_weight_break",
            "risks_acknowledged",
            "total_shipments_covered",
            "methods_referenced",
        ]:
            checks.append({"name": name, "passed": False, "detail": f"Cannot load report: {e}"})
        result = {
            "passed": False,
            "score": round(sum(1 for c in checks if c["passed"]) / len(checks), 3),
            "checks": checks
        }
        print(json.dumps(result))
        return

    # ── Check 1: Valid JSON ───────────────────────────────────────────────────
    def check_valid_json():
        # Already loaded; just confirm structure is dict
        if isinstance(report, dict):
            return True, "Valid JSON object"
        return False, f"Root type is {type(report).__name__}, expected dict"
    checks.append(run_check("report_is_valid_json", check_valid_json))

    # ── Check 2: Consolidation groups present ────────────────────────────────
    def check_groups_present():
        # Report must contain some list of groups/shipment bundles
        text = json.dumps(report).lower()
        group_keywords = ["group", "bundle", "consolidat", "batch", "load"]
        found = [kw for kw in group_keywords if kw in text]
        if not found:
            return False, "No grouping/consolidation structure found in report"
        # Also look for actual list structure
        def find_lists(d, depth=0):
            if depth > 5:
                return 0
            count = 0
            if isinstance(d, dict):
                for v in d.values():
                    count += find_lists(v, depth+1)
            elif isinstance(d, list) and len(d) >= 2:
                count += 1
            return count
        list_count = find_lists(report)
        if list_count == 0:
            return False, "Report has no list structures - grouping likely absent"
        return True, f"Grouping keywords found: {found}; list structures: {list_count}"
    checks.append(run_check("groups_present", check_groups_present))

    # ── Check 3: Shipments grouped by destination hub ────────────────────────
    def check_dest_hub_grouping():
        text = json.dumps(report).lower()
        # Three destination hubs from the data: AMS01, RTM02, HAM03
        hubs_found = []
        for hub in ["ams01", "rtm02", "ham03", "amsterdam", "rotterdam", "hamburg"]:
            if hub in text:
                hubs_found.append(hub)
        if len(hubs_found) < 2:
            return False, f"Expected at least 2 EU hub references; found: {hubs_found}"
        return True, f"Destination hubs referenced: {hubs_found}"
    checks.append(run_check("dest_hub_grouping_correct", check_dest_hub_grouping))

    # ── Check 4: LCL strategy mentioned (from scripts/script.sh lcl output) ──
    def check_lcl_strategy():
        text = json.dumps(report).lower()
        lcl_terms = ["lcl", "less than container", "groupage", "cfs", "container freight station"]
        found = [t for t in lcl_terms if t in text]
        if not found:
            return False, "LCL/groupage terminology absent - agent likely did not run 'lcl' subcommand"
        return True, f"LCL terms found: {found}"
    checks.append(run_check("lcl_strategy_mentioned", check_lcl_strategy))

    # ── Check 5: Milk run or supplier-based pickup grouping ──────────────────
    def check_milkrun():
        text = json.dumps(report).lower()
        mr_terms = ["milk run", "milkrun", "supplier pickup", "multi-supplier", "multi supplier", "pickup route"]
        found = [t for t in mr_terms if t in text]
        # Also check: Nippon Components has 3 POs from Osaka — a natural milk run candidate
        supplier_terms = ["nippon", "sinotech", "eastcomp", "gz precision", "microparts"]
        suppliers_found = [s for s in supplier_terms if s in text]
        if not found and len(suppliers_found) < 2:
            return False, f"No milk run strategy or multi-supplier grouping found. milk run terms: {found}, suppliers: {suppliers_found}"
        return True, f"Milk run / supplier grouping evidence: {found + suppliers_found}"
    checks.append(run_check("milkrun_or_supplier_grouping", check_milkrun))

    # ── Check 6: Savings / cost analysis present ─────────────────────────────
    def check_savings():
        text = json.dumps(report).lower()
        # Must contain numeric cost figures AND savings terminology
        savings_terms = ["saving", "cost", "break-even", "breakeven", "direct ship", "rate", "cbm", "per cbm", "w/m"]
        found = [t for t in savings_terms if t in text]
        # Check for numeric values (monetary amounts)
        numbers = re.findall(r'\b\d{3,}\b', json.dumps(report))
        if len(found) < 2:
            return False, f"Insufficient cost/savings analysis. Terms: {found}"
        if len(numbers) < 3:
            return False, f"Too few numeric values ({len(numbers)}) for cost analysis"
        return True, f"Cost analysis terms: {found[:5]}; numeric values found: {len(numbers)}"
    checks.append(run_check("savings_or_cost_analysis", check_savings))

    # ── Check 7: Planning window or weight break referenced ───────────────────
    def check_planning():
        text = json.dumps(report).lower()
        plan_terms = ["order window", "weight break", "consolidation window", "cutoff", "timing",
                      "cbm", "chargeable weight", "w/m ratio", "volume weight"]
        found = [t for t in plan_terms if t in text]
        if len(found) < 1:
            return False, f"No planning window/weight break terminology found. Terms checked: {plan_terms}"
        return True, f"Planning terms found: {found}"
    checks.append(run_check("planning_window_or_weight_break", check_planning))

    # ── Check 8: Risks section present ───────────────────────────────────────
    def check_risks():
        text = json.dumps(report).lower()
        risk_terms = ["risk", "delay", "damage", "customs", "mitigation", "complication", "hazard"]
        found = [t for t in risk_terms if t in text]
        if len(found) < 2:
            return False, f"Risk section absent or too thin. Risk terms found: {found}"
        return True, f"Risk terms found: {found}"
    checks.append(run_check("risks_acknowledged", check_risks))

    # ── Check 9: All 14 shipments accounted for ───────────────────────────────
    def check_shipment_coverage():
        text = json.dumps(report)
        po_ids = [f"PO-44{i}" for i in range(21, 35)]  # PO-4421 through PO-4434
        found = [po for po in po_ids if po in text]
        coverage = len(found) / len(po_ids)
        if coverage < 0.7:
            return False, f"Only {len(found)}/14 shipment IDs referenced ({coverage:.0%}). Missing: {set(po_ids)-set(found)}"
        return True, f"{len(found)}/14 shipments covered ({coverage:.0%}): {found}"
    checks.append(run_check("total_shipments_covered", check_shipment_coverage))

    # ── Check 10: Consolidation methods referenced (from 'methods' subcommand) ─
    def check_methods():
        text = json.dumps(report).lower()
        method_terms = ["zone-skip", "zone skip", "pool distribution", "merge-in-transit",
                        "merge in transit", "cross-dock", "crossdock", "cross dock"]
        found = [t for t in method_terms if t in text]
        if not found:
            return False, f"No consolidation method terminology found (zone-skip, pool distribution, merge-in-transit, cross-dock). Agent likely did not run 'methods' subcommand"
        return True, f"Consolidation methods referenced: {found}"
    checks.append(run_check("methods_referenced", check_methods))

    # ── Final scoring ─────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 3)
    overall = passed_count >= 8  # Must pass at least 8/10 checks

    result = {
        "passed": overall,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()