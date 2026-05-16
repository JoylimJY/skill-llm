import sys
import json
import zipfile
import re
from pathlib import Path

def main(workspace):
    workspace = Path(workspace)
    checks = []
    
    # ── Locate output file ──────────────────────────────────────────────────
    # Agent is asked to produce output_profit.xlsx
    candidates = list(workspace.rglob("output_profit.xlsx"))
    
    file_found = len(candidates) > 0
    checks.append({
        "name": "output_profit.xlsx exists",
        "passed": file_found,
        "detail": f"Found at: {candidates[0]}" if file_found else "output_profit.xlsx not found anywhere in workspace"
    })
    
    if not file_found:
        return {"passed": False, "score": 0.0, "checks": checks}
    
    output_path = candidates[0]
    
    # ── Verify it's a valid zip (xlsx) ──────────────────────────────────────
    try:
        with zipfile.ZipFile(str(output_path), 'r') as zf:
            names = zf.namelist()
        is_valid_zip = True
    except Exception as e:
        is_valid_zip = False
        checks.append({"name": "output is valid xlsx/zip", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({
        "name": "output is valid xlsx/zip",
        "passed": is_valid_zip,
        "detail": f"Contains {len(names)} entries"
    })
    
    # ── Check calcChain.xml was REMOVED ─────────────────────────────────────
    calc_chain_absent = "xl/calcChain.xml" not in names
    checks.append({
        "name": "xl/calcChain.xml deleted (not in output)",
        "passed": calc_chain_absent,
        "detail": "calcChain.xml found — must be deleted per skill rules" if not calc_chain_absent else "calcChain.xml correctly absent"
    })
    
    # ── Read sheet1.xml ──────────────────────────────────────────────────────
    try:
        with zipfile.ZipFile(str(output_path), 'r') as zf:
            sheet_xml_bytes = zf.read("xl/worksheets/sheet1.xml")
        sheet_xml = sheet_xml_bytes.decode("utf-8")
    except Exception as e:
        checks.append({"name": "can read sheet1.xml", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({"name": "can read sheet1.xml", "passed": True, "detail": "OK"})
    
    # ── Helper: extract <v> for a given cell reference ───────────────────────
    def get_cell_v(xml_text, cell_ref):
        """Extract the <v> value for a cell reference like D7."""
        # Match <c r="D7" ...>...<v>VALUE</v>...</c>
        pattern = rf'<c\s+r="{re.escape(cell_ref)}"[^>]*>.*?</c>'
        m = re.search(pattern, xml_text, re.DOTALL)
        if not m:
            return None
        cell_block = m.group(0)
        v_m = re.search(r'<v>(.*?)</v>', cell_block)
        if not v_m:
            return None
        return v_m.group(1).strip()
    
    def get_cell_full(xml_text, cell_ref):
        """Return the full cell XML block for a cell reference."""
        pattern = rf'<c\s+r="{re.escape(cell_ref)}"[^>]*>.*?</c>'
        m = re.search(pattern, xml_text, re.DOTALL)
        return m.group(0) if m else None
    
    # ── Expected ERP values from gen_inputs (fixed seed, hardcoded) ──────────
    # ERP data mapped to template:
    # 行次1 → row7:  D7=8523614.5,  E7=17204390.0
    # 行次2 → row8:  D8=6215430.2,  E8=12543870.4
    # 行次3 → row9:  D9=45230.0,    E9=90460.0
    # 行次4 → row10: D10=312450.8,  E10=625901.6
    # 行次5 → row11: D11=198760.5,  E11=401521.0
    # 行次6 → row12: D12=85000.0,   E12=170000.0
    # 行次7 → row13: D13=23410.3,   E13=47820.6
    # 行次14 → row20: D20=12500.0,  E20=25000.0
    # 行次21 → row28: D28=8800.0,   E28=17600.0
    # 行次22 → row29: D29=3200.0,   E29=6400.0
    
    expected_data = {
        "D7":  (8523614.5,  "营业收入 本期"),
        "E7":  (17204390.0, "营业收入 本年"),
        "D8":  (6215430.2,  "营业成本 本期"),
        "E8":  (12543870.4, "营业成本 本年"),
        "D9":  (45230.0,    "税金及附加 本期"),
        "E9":  (90460.0,    "税金及附加 本年"),
        "D10": (312450.8,   "销售费用 本期"),
        "E10": (625901.6,   "销售费用 本年"),
        "D11": (198760.5,   "管理费用 本期"),
        "E11": (401521.0,   "管理费用 本年"),
        "D12": (85000.0,    "研发费用 本期"),
        "E12": (170000.0,   "研发费用 本年"),
        "D13": (23410.3,    "财务费用 本期"),
        "E13": (47820.6,    "财务费用 本年"),
        "D20": (12500.0,    "其他收益 本期"),
        "E20": (25000.0,    "其他收益 本年"),
        "D28": (8800.0,     "营业外收入 本期"),
        "E28": (17600.0,    "营业外收入 本年"),
        "D29": (3200.0,     "营业外支出 本期"),
        "E29": (6400.0,     "营业外支出 本年"),
    }
    
    data_cells_correct = 0
    total_data_cells = len(expected_data)
    
    for cell_ref, (expected_val, label) in expected_data.items():
        v = get_cell_v(sheet_xml, cell_ref)
        try:
            actual = float(v) if v is not None else None
        except:
            actual = None
        ok = actual is not None and abs(actual - expected_val) < 0.02
        if ok:
            data_cells_correct += 1
        checks.append({
            "name": f"data cell {cell_ref} ({label})",
            "passed": ok,
            "detail": f"expected={expected_val}, got={actual}"
        })
    
    data_accuracy = data_cells_correct / total_data_cells
    checks.append({
        "name": f"data cell fill accuracy ({data_cells_correct}/{total_data_cells})",
        "passed": data_cells_correct >= total_data_cells * 0.85,
        "detail": f"{data_accuracy*100:.1f}% of data cells correctly filled"
    })
    
    # ── Formula cells: <f> must be intact, <v> must be updated ──────────────
    formula_cells = ["D21", "E21", "D30", "E30", "D32", "E32"]
    
    # Expected formula cached values (computed from ERP data):
    # D21 = ROUND(D7-D8-D9-D10-D11-D12-D13+D20, 2)
    d21 = round(8523614.5 - 6215430.2 - 45230.0 - 312450.8 - 198760.5 - 85000.0 - 23410.3 + 12500.0, 2)
    e21 = round(17204390.0 - 12543870.4 - 90460.0 - 625901.6 - 401521.0 - 170000.0 - 47820.6 + 25000.0, 2)
    # D30 = ROUND(D21+D28-D29, 2)
    d30 = round(d21 + 8800.0 - 3200.0, 2)
    e30 = round(e21 + 17600.0 - 6400.0, 2)
    # D32 = ROUND(D30-D31, 2) — D31 not in ERP map so likely stays 0
    d32 = round(d30 - 0.0, 2)
    e32 = round(e30 - 0.0, 2)
    
    formula_expected_v = {
        "D21": d21, "E21": e21,
        "D30": d30, "E30": e30,
        "D32": d32, "E32": e32,
    }
    
    formula_expected_f = {
        "D21": "ROUND(D7-D8-D9-D10-D11-D12-D13+D20,2)",
        "E21": "ROUND(E7-E8-E9-E10-E11-E12-E13+E20,2)",
        "D30": "ROUND(D21+D28-D29,2)",
        "E30": "ROUND(E21+E28-E29,2)",
        "D32": "ROUND(D30-D31,2)",
        "E32": "ROUND(E30-E31,2)",
    }
    
    formula_f_intact_count = 0
    formula_v_updated_count = 0
    
    for cell_ref in formula_cells:
        cell_block = get_cell_full(sheet_xml, cell_ref)
        if cell_block is None:
            checks.append({
                "name": f"formula cell {cell_ref} exists",
                "passed": False,
                "detail": f"Cell {cell_ref} not found in sheet"
            })
            continue
        
        # Check <f> tag preserved
        f_match = re.search(r'<f>(.*?)</f>', cell_block)
        f_intact = f_match is not None
        if f_intact:
            formula_f_intact_count += 1
        checks.append({
            "name": f"formula cell {cell_ref}: <f> tag preserved",
            "passed": f_intact,
            "detail": f"formula: {f_match.group(1) if f_match else 'MISSING'}"
        })
        
        # Check <v> tag updated with expected computed value
        v_match = re.search(r'<v>(.*?)</v>', cell_block)
        try:
            actual_v = float(v_match.group(1)) if v_match else None
        except:
            actual_v = None
        expected_v = formula_expected_v.get(cell_ref)
        # Accept if within 1.0 of expected (rounding differences acceptable)
        v_updated = actual_v is not None and expected_v is not None and abs(actual_v - expected_v) < 1.0
        if v_updated:
            formula_v_updated_count += 1
        checks.append({
            "name": f"formula cell {cell_ref}: <v> updated to computed value",
            "passed": v_updated,
            "detail": f"expected≈{expected_v}, got={actual_v}"
        })
    
    formula_f_ok = formula_f_intact_count == len(formula_cells)
    checks.append({
        "name": "ALL formula <f> tags preserved (none deleted/modified)",
        "passed": formula_f_ok,
        "detail": f"{formula_f_intact_count}/{len(formula_cells)} formula tags intact"
    })
    
    # ── Style attributes: s= must NOT change ────────────────────────────────
    # Check that key cells still have correct s= attributes
    style_checks = {
        "D7":  "3",   # data cell → s=3
        "D21": "4",   # formula subtotal → s=4
        "D32": "5",   # net profit total → s=5
    }
    styles_ok_count = 0
    for cell_ref, expected_s in style_checks.items():
        cell_block = get_cell_full(sheet_xml, cell_ref)
        if cell_block:
            s_match = re.search(r'<c\s+r="' + re.escape(cell_ref) + r'"\s+s="(\d+)"', cell_block)
            actual_s = s_match.group(1) if s_match else None
            ok = actual_s == expected_s
            if ok:
                styles_ok_count += 1
            checks.append({
                "name": f"style preserved for {cell_ref} (s={expected_s})",
                "passed": ok,
                "detail": f"expected s={expected_s}, got s={actual_s}"
            })
        else:
            checks.append({
                "name": f"style preserved for {cell_ref}",
                "passed": False,
                "detail": f"Cell {cell_ref} not found"
            })
    
    # ── Overall scoring ──────────────────────────────────────────────────────
    critical_checks = [
        "output_profit.xlsx exists",
        "output is valid xlsx/zip",
        "xl/calcChain.xml deleted (not in output)",
        "ALL formula <f> tags preserved (none deleted/modified)",
    ]
    
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )
    
    # Score calculation
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = passed_count / total if total > 0 else 0.0
    
    # Must pass all critical checks AND at least 85% of data cells
    data_ok = data_cells_correct >= total_data_cells * 0.85
    overall_passed = critical_passed and data_ok
    
    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = main(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))