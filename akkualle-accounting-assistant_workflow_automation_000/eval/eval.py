#!/usr/bin/env python3
"""
Evaluation script for the accounting-assistant task.
Checks:
1. beleg-analyse.py was run on rechnung.pdf (output captured or noted)
2. eur-2024.md exists with correct EÜR structure and financial figures
3. export.csv exists with correct DATEV format (SKR03 accounts, proper columns)
4. USt 19% calculated correctly throughout
"""

import sys
import json
import csv
import re
import os
from pathlib import Path

def find_file(workspace, filename):
    """Search recursively for a file."""
    matches = list(Path(workspace).rglob(filename))
    return matches[0] if matches else None

def check_eur_md(workspace):
    checks = []
    
    eur_file = find_file(workspace, "eur-2024.md")
    if eur_file is None:
        checks.append({"name": "eur-2024.md exists", "passed": False, "detail": "File eur-2024.md not found anywhere in workspace"})
        return checks, False
    
    checks.append({"name": "eur-2024.md exists", "passed": True, "detail": str(eur_file)})
    
    try:
        content = eur_file.read_text(encoding='utf-8')
    except Exception as e:
        checks.append({"name": "eur-2024.md readable", "passed": False, "detail": str(e)})
        return checks, False
    
    checks.append({"name": "eur-2024.md readable", "passed": True, "detail": f"File size: {len(content)} chars"})
    
    # Check for EÜR header / Anlage EÜR
    has_eur_header = bool(re.search(r'Einnahmen.Überschuss.Rechnung\s+2024', content, re.IGNORECASE) or
                          re.search(r'EÜR.*2024', content, re.IGNORECASE) or
                          re.search(r'Anlage EÜR', content, re.IGNORECASE))
    checks.append({
        "name": "EÜR header present",
        "passed": has_eur_header,
        "detail": "Found EÜR/Anlage EÜR 2024 heading" if has_eur_header else "Missing EÜR heading for year 2024"
    })
    
    # Check for Einnahmen section
    has_einnahmen = bool(re.search(r'Betriebseinnahmen|Einnahmen', content, re.IGNORECASE))
    checks.append({
        "name": "Einnahmen section present",
        "passed": has_einnahmen,
        "detail": "Found Einnahmen/Betriebseinnahmen section" if has_einnahmen else "Missing Einnahmen section"
    })
    
    # Check for Ausgaben section
    has_ausgaben = bool(re.search(r'Betriebsausgaben|Ausgaben', content, re.IGNORECASE))
    checks.append({
        "name": "Ausgaben section present",
        "passed": has_ausgaben,
        "detail": "Found Ausgaben/Betriebsausgaben section" if has_ausgaben else "Missing Ausgaben section"
    })
    
    # Verify financial calculations
    # Input data:
    # Einnahmen brutto: 2380 + 1190 + 595 + 3570 = 7735
    # Einnahmen netto: 7735 / 1.19 = 6500.00 (exact)
    # Ausgaben brutto: 238 + 59.50 + 476 + 119 = 892.50
    # Ausgaben netto: 892.50 / 1.19 = 750.00 (exact)
    # Gewinn: 6500.00 - 750.00 = 5750.00
    
    expected_einnahmen_netto = 6500.00
    expected_ausgaben_netto = 750.00
    expected_gewinn = 5750.00
    expected_ust_einnahmen = round(7735.00 - 6500.00, 2)  # 1235.00
    expected_ust_zahllast = round(expected_ust_einnahmen - round(892.50 - 750.00, 2), 2)  # 1235.00 - 142.50 = 1092.50
    
    # Check Gewinn value appears
    gewinn_pattern = re.search(r'5[,.]?750[,.]?00', content)
    checks.append({
        "name": "Correct Gewinn (5750.00 EUR)",
        "passed": bool(gewinn_pattern),
        "detail": f"Expected Gewinn 5750.00 EUR in content" + (" - FOUND" if gewinn_pattern else " - NOT FOUND")
    })
    
    # Check USt Zahllast
    ust_pattern = re.search(r'1[,.]?092[,.]?50', content)
    checks.append({
        "name": "Correct USt-Zahllast (1092.50 EUR)",
        "passed": bool(ust_pattern),
        "detail": f"Expected USt-Zahllast 1092.50 EUR" + (" - FOUND" if ust_pattern else " - NOT FOUND")
    })
    
    # Check mention of SKR03 or Accounting Assistant
    has_skr_or_tool = bool(re.search(r'SKR03|Accounting Assistant|§ 4 Abs\. 3|EStG', content, re.IGNORECASE))
    checks.append({
        "name": "SKR03/EStG reference present",
        "passed": has_skr_or_tool,
        "detail": "Found SKR03/EStG reference" if has_skr_or_tool else "Missing SKR03/§4 Abs.3 EStG reference"
    })
    
    return checks, True

def check_datev_csv(workspace):
    checks = []
    
    # Search for export.csv
    csv_file = find_file(workspace, "export.csv")
    if csv_file is None:
        checks.append({"name": "export.csv exists", "passed": False, "detail": "File export.csv not found anywhere in workspace"})
        return checks, False
    
    checks.append({"name": "export.csv exists", "passed": True, "detail": str(csv_file)})
    
    try:
        content = csv_file.read_text(encoding='utf-8')
        rows = list(csv.DictReader(content.splitlines(), delimiter=';'))
    except Exception as e:
        checks.append({"name": "export.csv parseable", "passed": False, "detail": str(e)})
        return checks, False
    
    checks.append({
        "name": "export.csv parseable as DATEV CSV",
        "passed": True,
        "detail": f"Parsed {len(rows)} data rows"
    })
    
    # Check row count: 8 buchungen
    checks.append({
        "name": "Correct number of rows (8)",
        "passed": len(rows) == 8,
        "detail": f"Found {len(rows)} rows, expected 8"
    })
    
    if not rows:
        checks.append({"name": "DATEV columns check", "passed": False, "detail": "No rows to check"})
        return checks, True
    
    # Check mandatory DATEV columns
    required_cols = [
        "Umsatz (ohne Soll/Haben-Kz)",
        "Soll/Haben-Kennzeichen",
        "WKZ Umsatz",
        "Konto",
        "Gegenkonto (ohne BU-Schlüssel)",
        "BU-Schlüssel",
        "Belegdatum",
        "Buchungstext"
    ]
    first_row = rows[0]
    missing_cols = [c for c in required_cols if c not in first_row]
    checks.append({
        "name": "DATEV required columns present",
        "passed": len(missing_cols) == 0,
        "detail": f"Missing columns: {missing_cols}" if missing_cols else "All required DATEV columns present"
    })
    
    # Check SKR03 account numbers
    # Einnahmen should use konto 8400, Ausgaben should use konto 4980
    konten = [r.get("Konto", "") for r in rows]
    gegenkkonten = [r.get("Gegenkonto (ohne BU-Schlüssel)", "") for r in rows]
    all_konten = set(konten) | set(gegenkkonten)
    
    has_8400 = "8400" in all_konten
    has_4980 = "4980" in all_konten
    has_1200 = "1200" in all_konten
    
    checks.append({
        "name": "SKR03 Erlöskonto 8400 present",
        "passed": has_8400,
        "detail": f"Account 8400 (Erlöse 19% USt) found: {has_8400}. All accounts: {all_konten}"
    })
    checks.append({
        "name": "SKR03 Aufwandskonto 4980 present",
        "passed": has_4980,
        "detail": f"Account 4980 (betriebl. Aufwendungen) found: {has_4980}"
    })
    checks.append({
        "name": "SKR03 Bankkonto 1200 present",
        "passed": has_1200,
        "detail": f"Account 1200 (Bank) found: {has_1200}"
    })
    
    # Check Soll/Haben logic
    sh_values = [r.get("Soll/Haben-Kennzeichen", "") for r in rows]
    has_H = "H" in sh_values  # Einnahmen
    has_S = "S" in sh_values  # Ausgaben
    checks.append({
        "name": "Soll/Haben-Kennzeichen H and S present",
        "passed": has_H and has_S,
        "detail": f"H (Haben/Einnahmen): {has_H}, S (Soll/Ausgaben): {has_S}"
    })
    
    # Check BU-Schlüssel (tax code 9 for 19% USt)
    bu_values = set(r.get("BU-Schlüssel", "") for r in rows)
    has_bu9 = "9" in bu_values
    checks.append({
        "name": "BU-Schlüssel 9 (19% USt) present",
        "passed": has_bu9,
        "detail": f"BU-Schlüssel values found: {bu_values}"
    })
    
    # Check netto values computed correctly (sample: first Einnahme 2380/1.19 = 2000.00)
    einnahme_rows = [r for r in rows if r.get("Soll/Haben-Kennzeichen") == "H"]
    netto_ok = False
    if einnahme_rows:
        try:
            first_umsatz = float(einnahme_rows[0].get("Umsatz (ohne Soll/Haben-Kz)", "0").replace(",", "."))
            # 2380 / 1.19 = 2000.00
            netto_ok = abs(first_umsatz - 2000.00) < 0.02
        except Exception:
            netto_ok = False
    checks.append({
        "name": "Netto USt 19% calculation correct (2380 brutto → 2000.00 netto)",
        "passed": netto_ok,
        "detail": f"First Einnahme netto: {einnahme_rows[0].get('Umsatz (ohne Soll/Haben-Kz)') if einnahme_rows else 'N/A'}, expected 2000.00"
    })
    
    # Check WKZ EUR
    wkz_ok = all(r.get("WKZ Umsatz", "") == "EUR" for r in rows)
    checks.append({
        "name": "WKZ Umsatz is EUR for all rows",
        "passed": wkz_ok,
        "detail": "All rows have WKZ=EUR" if wkz_ok else "Some rows missing EUR currency"
    })
    
    return checks, True

def check_beleg_analyse(workspace):
    """Check if beleg-analyse was run (look for output file or log)."""
    checks = []
    
    # The agent might have saved the output or we just note it was requested
    # We'll look for any JSON output file from beleg-analyse, or check for evidence in any log/output
    beleg_output = find_file(workspace, "beleg-analyse-output.json")
    beleg_output2 = find_file(workspace, "beleg_output.json")
    beleg_output3 = find_file(workspace, "rechnung_analyse.json")
    
    found = beleg_output or beleg_output2 or beleg_output3
    
    # Also check if any file in workspace contains "analysiert" key (beleg-analyse JSON output)
    if not found:
        for f in Path(workspace).rglob("*.json"):
            try:
                data = json.loads(f.read_text(encoding='utf-8'))
                if isinstance(data, dict) and data.get("analysiert") is True:
                    found = f
                    break
            except:
                pass
    
    checks.append({
        "name": "beleg-analyse output found (optional bonus check)",
        "passed": bool(found),
        "detail": f"Found at {found}" if found else "No beleg-analyse JSON output found (may have been printed to stdout only)"
    })
    
    return checks

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    
    workspace = sys.argv[1]
    all_checks = []
    
    # Check EÜR markdown
    eur_checks, eur_found = check_eur_md(workspace)
    all_checks.extend(eur_checks)
    
    # Check DATEV CSV
    datev_checks, datev_found = check_datev_csv(workspace)
    all_checks.extend(datev_checks)
    
    # Check beleg-analyse (bonus/informational)
    beleg_checks = check_beleg_analyse(workspace)
    all_checks.extend(beleg_checks)
    
    # Scoring
    # Weight: EÜR (40%), DATEV (55%), Beleg bonus (5%)
    eur_critical = [c for c in eur_checks if c["name"] in [
        "eur-2024.md exists", "EÜR header present", "Einnahmen section present",
        "Ausgaben section present", "Correct Gewinn (5750.00 EUR)", "Correct USt-Zahllast (1092.50 EUR)"
    ]]
    datev_critical = [c for c in datev_checks if c["name"] in [
        "export.csv exists", "DATEV required columns present", "SKR03 Erlöskonto 8400 present",
        "SKR03 Aufwandskonto 4980 present", "SKR03 Bankkonto 1200 present",
        "Soll/Haben-Kennzeichen H and S present", "BU-Schlüssel 9 (19% USt) present",
        "Netto USt 19% calculation correct (2380 brutto → 2000.00 netto)"
    ]]
    
    eur_score = sum(1 for c in eur_critical if c["passed"]) / max(len(eur_critical), 1)
    datev_score = sum(1 for c in datev_critical if c["passed"]) / max(len(datev_critical), 1)
    beleg_score = 1.0 if beleg_checks and beleg_checks[0]["passed"] else 0.0
    
    total_score = round(eur_score * 0.40 + datev_score * 0.55 + beleg_score * 0.05, 3)
    
    # Must pass all critical checks to be considered passing
    critical_passed = all(c["passed"] for c in eur_critical if c["name"] in [
        "eur-2024.md exists", "Correct Gewinn (5750.00 EUR)"
    ]) and all(c["passed"] for c in datev_critical if c["name"] in [
        "export.csv exists", "SKR03 Erlöskonto 8400 present", "DATEV required columns present"
    ])
    
    passed = critical_passed and total_score >= 0.70
    
    output = {
        "passed": passed,
        "score": total_score,
        "checks": all_checks
    }
    
    print(json.dumps(output, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()