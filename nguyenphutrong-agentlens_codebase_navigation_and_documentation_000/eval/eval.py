import sys
import json
import os
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    workspace = Path(workspace)

    # ── locate the report ─────────────────────────────────────────────────────
    report_candidates = list(workspace.rglob("audit_report.json"))
    if not report_candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False,
                        "detail": "audit_report.json not found anywhere in workspace"}]
        }

    report_path = report_candidates[0]

    try:
        with open(report_path) as f:
            report = json.load(f)
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "json_parseable", "passed": False,
                        "detail": f"Could not parse audit_report.json: {e}"}]
        }

    checks.append({"name": "file_exists_and_parseable", "passed": True,
                   "detail": f"Found at {report_path}"})

    # ─── CHECK 1: entry_points ────────────────────────────────────────────────
    # INDEX.md says entry point is src/main.py
    try:
        eps = report.get("entry_points", [])
        ep_str = json.dumps(eps).lower()
        ep_ok = "main.py" in ep_str or "src/main.py" in ep_str
        checks.append({
            "name": "entry_points_correct",
            "passed": ep_ok,
            "detail": f"entry_points field: {eps}"
        })
    except Exception as e:
        checks.append({"name": "entry_points_correct", "passed": False, "detail": str(e)})

    # ─── CHECK 2: hub_files ───────────────────────────────────────────────────
    # INDEX.md says hub files: src/transaction/models.py and src/config.py
    try:
        hubs = report.get("hub_files", [])
        hub_str = json.dumps(hubs).lower()
        has_models = "models.py" in hub_str
        has_config = "config.py" in hub_str
        hub_ok = has_models and has_config
        checks.append({
            "name": "hub_files_correct",
            "passed": hub_ok,
            "detail": f"hub_files: {hubs} — needs models.py={has_models}, config.py={has_config}"
        })
    except Exception as e:
        checks.append({"name": "hub_files_correct", "passed": False, "detail": str(e)})

    # ─── CHECK 3: transaction module — symbol line numbers ────────────────────
    # From transaction/outline.md:
    #   TransactionProcessor → line 50
    #   process → line 111
    #   rollback → line 201
    #   batch_process → line 511
    try:
        txn_symbols = report.get("modules", {}).get("transaction", {}).get("symbols", {})
        sym_str = json.dumps(txn_symbols)

        def line_present(sym_dict, name, expected_line):
            """Check that a symbol name maps to the expected line number."""
            val = str(sym_dict).lower()
            # Accept if both symbol name and line appear near each other in any sub-structure
            # More robust: check the actual dict
            for k, v in sym_dict.items():
                k_low = str(k).lower()
                if name.lower() in k_low:
                    line_val = None
                    if isinstance(v, dict):
                        line_val = v.get("line") or v.get("line_number") or v.get("ln")
                    elif isinstance(v, int):
                        line_val = v
                    if line_val is not None and int(line_val) == expected_line:
                        return True
            return False

        proc_class_ok = line_present(txn_symbols, "TransactionProcessor", 50)
        process_ok    = line_present(txn_symbols, "process", 111)
        rollback_ok   = line_present(txn_symbols, "rollback", 201)
        batch_ok      = line_present(txn_symbols, "batch_process", 511)

        # Also accept flat list format
        if not (proc_class_ok and process_ok and rollback_ok and batch_ok):
            sym_str_low = sym_str.lower()
            # Fallback: check that correct line numbers appear in the symbol data
            proc_class_ok = proc_class_ok or ("transactionprocessor" in sym_str_low and "50" in sym_str)
            process_ok    = process_ok    or ('"process"' in sym_str_low and "111" in sym_str)
            rollback_ok   = rollback_ok   or ("rollback" in sym_str_low and "201" in sym_str)
            batch_ok      = batch_ok      or ("batch_process" in sym_str_low and "511" in sym_str)

        symbols_ok = proc_class_ok and process_ok and rollback_ok and batch_ok
        checks.append({
            "name": "transaction_symbol_lines",
            "passed": symbols_ok,
            "detail": (f"TransactionProcessor@50={proc_class_ok}, "
                       f"process@111={process_ok}, rollback@201={rollback_ok}, "
                       f"batch_process@511={batch_ok}")
        })
    except Exception as e:
        checks.append({"name": "transaction_symbol_lines", "passed": False, "detail": str(e)})

    # ─── CHECK 4: fraud module — memory items ─────────────────────────────────
    # From fraud/memory.md, required items:
    #   SAFETY: detect must never suppress HIGH risk on merchant whitelist
    #   SAFETY: explain_decision must log every call (PCI-DSS)
    #   FIXME/WARNING: race condition in update_model
    #   TODO: velocity-check feature
    try:
        fraud_mem = report.get("modules", {}).get("fraud", {}).get("memory", {})
        mem_str = json.dumps(fraud_mem).lower()

        # SAFETY items
        s1_ok = ("high" in mem_str and "whitelist" in mem_str) or \
                ("suppress" in mem_str and "whitelist" in mem_str) or \
                ("merchant whitelist" in mem_str)
        s2_ok = ("explain_decision" in mem_str and ("pci" in mem_str or "audit" in mem_str))
        # Race condition
        race_ok = ("race condition" in mem_str or "update_model" in mem_str) and \
                  ("concurrent" in mem_str or "thread" in mem_str or "race" in mem_str)
        # TODO velocity
        vel_ok = "velocity" in mem_str or "velocity-check" in mem_str

        fraud_mem_ok = s1_ok and s2_ok and race_ok and vel_ok
        checks.append({
            "name": "fraud_memory_items",
            "passed": fraud_mem_ok,
            "detail": (f"safety_no_suppress_high={s1_ok}, "
                       f"safety_explain_audit={s2_ok}, "
                       f"race_condition={race_ok}, "
                       f"velocity_todo={vel_ok}")
        })
    except Exception as e:
        checks.append({"name": "fraud_memory_items", "passed": False, "detail": str(e)})

    # ─── CHECK 5: compliance module — deprecated + safety ─────────────────────
    # compliance/memory.md:
    #   DEPRECATED: submit_to_regulator
    #   SAFETY: audit log immutable, insert-only
    #   RULE: reports must cover complete calendar month
    try:
        comp_mem = report.get("modules", {}).get("compliance", {}).get("memory", {})
        comp_str = json.dumps(comp_mem).lower()

        dep_ok   = "submit_to_regulator" in comp_str or \
                   ("submit" in comp_str and "deprecated" in comp_str)
        immut_ok = ("immutable" in comp_str or "insert-only" in comp_str or
                    "insert only" in comp_str)
        month_ok = ("calendar month" in comp_str or "complete month" in comp_str or
                    "partial" in comp_str)

        comp_ok = dep_ok and immut_ok and month_ok
        checks.append({
            "name": "compliance_memory_items",
            "passed": comp_ok,
            "detail": (f"submit_deprecated={dep_ok}, immutable_audit={immut_ok}, "
                       f"full_month_rule={month_ok}")
        })
    except Exception as e:
        checks.append({"name": "compliance_memory_items", "passed": False, "detail": str(e)})

    # ─── CHECK 6: gateway — safety ordering constraint ────────────────────────
    # gateway/memory.md SAFETY: handle_request MUST call rate_limit BEFORE authenticate
    try:
        gw_mem = report.get("modules", {}).get("gateway", {}).get("memory", {})
        gw_str = json.dumps(gw_mem).lower()

        order_ok = (("rate_limit" in gw_str or "rate limit" in gw_str) and
                    "authenticate" in gw_str and
                    ("before" in gw_str or "order" in gw_str or "bypass" in gw_str or
                     "must call" in gw_str))
        checks.append({
            "name": "gateway_safety_ordering",
            "passed": order_ok,
            "detail": f"rate_limit before authenticate constraint: {order_ok}. excerpt: {gw_str[:300]}"
        })
    except Exception as e:
        checks.append({"name": "gateway_safety_ordering", "passed": False, "detail": str(e)})

    # ─── CHECK 7: transaction/processor.py dependency chain ──────────────────
    # From transaction/imports.md:
    #   processor.py imports: models.py, validator.py, config.py
    #   processor.py is imported by: gateway/api.py, compliance/reporter.py
    try:
        txn_deps = report.get("modules", {}).get("transaction", {}).get("dependencies", {})
        dep_str = json.dumps(txn_deps).lower()

        imports_models  = "models.py" in dep_str or "models" in dep_str
        imports_config  = "config.py" in dep_str or "config" in dep_str
        imported_by_gw  = "api.py" in dep_str or "gateway" in dep_str
        imported_by_rep = "reporter.py" in dep_str or "compliance" in dep_str

        dep_ok = imports_models and imports_config and imported_by_gw and imported_by_rep
        checks.append({
            "name": "processor_dependency_chain",
            "passed": dep_ok,
            "detail": (f"imports_models={imports_models}, imports_config={imports_config}, "
                       f"imported_by_gateway={imported_by_gw}, imported_by_compliance={imported_by_rep}")
        })
    except Exception as e:
        checks.append({"name": "processor_dependency_chain", "passed": False, "detail": str(e)})

    # ─── CHECK 8: fraud/detector.py — symbol lines from outline ──────────────
    # fraud/outline.md: detect@131, update_model@251, explain_decision@481
    try:
        fraud_syms = report.get("modules", {}).get("fraud", {}).get("symbols", {})
        fs_str = json.dumps(fraud_syms)
        fs_low = fs_str.lower()

        detect_ok   = ("detect" in fs_low and "131" in fs_str)
        update_ok   = ("update_model" in fs_low and "251" in fs_str)
        explain_ok  = ("explain_decision" in fs_low and "481" in fs_str)

        fraud_sym_ok = detect_ok and update_ok and explain_ok
        checks.append({
            "name": "fraud_symbol_lines",
            "passed": fraud_sym_ok,
            "detail": f"detect@131={detect_ok}, update_model@251={update_ok}, explain_decision@481={explain_ok}"
        })
    except Exception as e:
        checks.append({"name": "fraud_symbol_lines", "passed": False, "detail": str(e)})

    # ─── CHECK 9: global high-priority warnings present ───────────────────────
    # INDEX.md lists 3 high-priority warnings (rollback/audit, submit_to_regulator deprecated, race condition)
    try:
        hp = report.get("high_priority_warnings", [])
        hp_str = json.dumps(hp).lower()

        hw1 = "rollback" in hp_str or "pre_rollback" in hp_str or "audit log" in hp_str
        hw2 = "submit_to_regulator" in hp_str or \
              ("deprecated" in hp_str and ("submit" in hp_str or "regulator" in hp_str))
        hw3 = "race condition" in hp_str or ("update_model" in hp_str and "concurrent" in hp_str)

        hp_ok = hw1 and hw2 and hw3
        checks.append({
            "name": "high_priority_warnings",
            "passed": hp_ok,
            "detail": f"rollback_warning={hw1}, submit_deprecated={hw2}, race_condition={hw3}"
        })
    except Exception as e:
        checks.append({"name": "high_priority_warnings", "passed": False, "detail": str(e)})

    # ─── SCORING ─────────────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    score = len(passed_checks) / len(checks)
    overall_passed = score >= 0.80

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "invocation", "passed": False,
                                      "detail": "No workspace path provided"}]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))