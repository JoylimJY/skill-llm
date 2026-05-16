import sys
import json
import re
from pathlib import Path

def load_ics(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return ""

def check_ics_field(content: str, field: str, value: str) -> bool:
    """Check if a value appears in the ICS DESCRIPTION (unescaped)."""
    unescaped = content.replace('\\n', '\n').replace('\\,', ',').replace('\\;', ';')
    return value.lower() in unescaped.lower()

def run_eval(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    def add_check(name, passed, detail=""):
        checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

    # ---- CUSTOMER 1: Schaeffler ----
    # Expected filename: 2026-04-17_Schaeffler-Technologies-AG--Co-KG_Reminder.ics
    # (slugify replaces & -> nothing, spaces -> hyphens)
    # The exact slug depends on slugify logic: "Schaeffler Technologies AG & Co. KG"
    # slugify: removes non-word chars except - and spaces, replaces spaces with hyphens
    # "Schaeffler Technologies AG & Co. KG" -> "Schaeffler Technologies AG  Co KG" -> "Schaeffler-Technologies-AG--Co-KG"
    # Actually re.sub(r'[^\w\s-]', '', text) removes & and . -> "Schaeffler Technologies AG  Co KG"
    # re.sub(r'[\s_]+', '-', ...) -> "Schaeffler-Technologies-AG--Co-KG"  (double space becomes double hyphen)
    # re.sub(r'-+', '-', ...) -> "Schaeffler-Technologies-AG-Co-KG"
    
    schaeffler_candidates = list(workspace.rglob("2026-04-17_Schaeffler*_Reminder.ics"))
    
    if schaeffler_candidates:
        ics1 = load_ics(schaeffler_candidates[0])
        add_check("schaeffler_file_exists", True, f"Found: {schaeffler_candidates[0].name}")
        
        # Check DTSTART
        add_check("schaeffler_dtstart", 
                  "DTSTART:20260417T093000" in ics1,
                  "Expected DTSTART:20260417T093000")
        
        # Check DTEND (45 min duration)
        add_check("schaeffler_dtend_45min",
                  "DTEND:20260417T101500" in ics1,
                  "Expected DTEND:20260417T101500 (09:30 + 45 min)")
        
        # Check alarm trigger -PT20M
        add_check("schaeffler_alarm_20min",
                  "TRIGGER:-PT20M" in ics1,
                  "Expected TRIGGER:-PT20M")
        
        # Check priority HOCH in description
        add_check("schaeffler_priority_hoch",
                  check_ics_field(ics1, "priority", "HOCH") or "HOCH" in ics1,
                  "Expected priority HOCH")
        
        # Check deal phase Verhandlung
        add_check("schaeffler_deal_phase_verhandlung",
                  check_ics_field(ics1, "phase", "Verhandlung") or "Verhandlung" in ics1,
                  "Expected deal phase Verhandlung")
        
        # Check budget
        add_check("schaeffler_budget",
                  "48" in ics1 and "500" in ics1,
                  "Expected budget 48.500")
        
        # Check contact Hartmann
        add_check("schaeffler_contact",
                  "Hartmann" in ics1,
                  "Expected contact Hartmann")
        
        # Check viSales CRM Reminder header
        add_check("schaeffler_crm_header",
                  "viSales CRM Reminder" in ics1,
                  "Expected CRM header")
        
        # Check ICS structure
        add_check("schaeffler_ics_structure",
                  "BEGIN:VCALENDAR" in ics1 and "BEGIN:VEVENT" in ics1 and "END:VCALENDAR" in ics1,
                  "Expected valid ICS structure")
        
        # Check next step
        add_check("schaeffler_next_step",
                  "ROI" in ics1 or "Entscheider" in ics1,
                  "Expected next step with ROI or Entscheider reference")
        
        # Check notes CFO
        add_check("schaeffler_notes_cfo",
                  "CFO" in ics1,
                  "Expected notes mentioning CFO")
    else:
        add_check("schaeffler_file_exists", False, "No file matching 2026-04-17_Schaeffler*_Reminder.ics found")
        for name in ["schaeffler_dtstart", "schaeffler_dtend_45min", "schaeffler_alarm_20min",
                     "schaeffler_priority_hoch", "schaeffler_deal_phase_verhandlung",
                     "schaeffler_budget", "schaeffler_contact", "schaeffler_crm_header",
                     "schaeffler_ics_structure", "schaeffler_next_step", "schaeffler_notes_cfo"]:
            add_check(name, False, "File not found")

    # ---- CUSTOMER 2: Endress+Hauser ----
    # "Endress+Hauser Messtechnik GmbH" -> slugify removes + -> "EndressHauser Messtechnik GmbH"
    # Actually re.sub(r'[^\w\s-]', '', "Endress+Hauser Messtechnik GmbH") -> "EndressHauser Messtechnik GmbH"
    # -> "EndressHauser-Messtechnik-GmbH"
    endress_candidates = list(workspace.rglob("2026-04-22_Endress*_Reminder.ics"))
    
    if endress_candidates:
        ics2 = load_ics(endress_candidates[0])
        add_check("endress_file_exists", True, f"Found: {endress_candidates[0].name}")
        
        # Check DTSTART 14:00
        add_check("endress_dtstart",
                  "DTSTART:20260422T140000" in ics2,
                  "Expected DTSTART:20260422T140000")
        
        # Check DTEND (30 min default)
        add_check("endress_dtend_30min",
                  "DTEND:20260422T143000" in ics2,
                  "Expected DTEND:20260422T143000")
        
        # Check priority — "high" in English should map to "hoch" or HOCH in output
        # The script maps 'hoch' -> ⚡ HOCH. The input says "high" so agent must normalize.
        # If agent passes "high" directly, prioritaet.lower() = "high" won't match prio_map
        # so it will show MITTEL. We check that agent correctly maps "high" -> "hoch"
        add_check("endress_priority_hoch",
                  "HOCH" in ics2,
                  "Expected HOCH priority (agent must normalize English 'high' to German 'hoch')")
        
        # Check deal phase Closing
        add_check("endress_deal_phase",
                  "Closing" in ics2,
                  "Expected deal phase Closing")
        
        # Check budget 62000
        add_check("endress_budget",
                  "62" in ics2 and "000" in ics2,
                  "Expected budget 62,000 or 62.000")
        
        # Check contact Bühler
        add_check("endress_contact",
                  "hler" in ics2,  # Bühler - encoding safe check
                  "Expected contact Bühler")
        
        # Check topic IIoT
        add_check("endress_topic",
                  "IIoT" in ics2 or "Dashboard" in ics2,
                  "Expected topic IIoT or Dashboard")
        
        # Check next step contract
        add_check("endress_next_step",
                  "contract" in ics2.lower() or "draft" in ics2.lower() or "Vertrag" in ics2,
                  "Expected next step about contract draft")
        
        # Check alarm default 15min
        add_check("endress_alarm_15min",
                  "TRIGGER:-PT15M" in ics2,
                  "Expected default alarm TRIGGER:-PT15M")
        
        # Check ICS structure
        add_check("endress_ics_structure",
                  "BEGIN:VCALENDAR" in ics2 and "BEGIN:VEVENT" in ics2 and "END:VCALENDAR" in ics2,
                  "Expected valid ICS structure")
    else:
        add_check("endress_file_exists", False, "No file matching 2026-04-22_Endress*_Reminder.ics found")
        for name in ["endress_dtstart", "endress_dtend_30min", "endress_priority_hoch",
                     "endress_deal_phase", "endress_budget", "endress_contact",
                     "endress_topic", "endress_next_step", "endress_alarm_15min",
                     "endress_ics_structure"]:
            add_check(name, False, "File not found")

    # ---- CUSTOMER 3: Voith ----
    # "Voith GmbH & Co. KGaA" -> remove &, . -> "Voith GmbH  Co KGaA" -> "Voith-GmbH-Co-KGaA"
    voith_candidates = list(workspace.rglob("2026-04-29_Voith*_Reminder.ics"))
    
    if voith_candidates:
        ics3 = load_ics(voith_candidates[0])
        add_check("voith_file_exists", True, f"Found: {voith_candidates[0].name}")
        
        # Check DTSTART 11:00
        add_check("voith_dtstart",
                  "DTSTART:20260429T110000" in ics3,
                  "Expected DTSTART:20260429T110000")
        
        # Check priority mittel -> MITTEL
        add_check("voith_priority_mittel",
                  "MITTEL" in ics3,
                  "Expected MITTEL priority")
        
        # Check deal phase Nurture
        add_check("voith_deal_phase",
                  "Nurture" in ics3,
                  "Expected deal phase Nurture")
        
        # Check contact Krause
        add_check("voith_contact",
                  "Krause" in ics3,
                  "Expected contact Dr. Krause")
        
        # Check topic Digitalisierung
        add_check("voith_topic",
                  "Digitalisierung" in ics3 or "2027" in ics3,
                  "Expected topic Digitalisierungsstrategie or 2027")
        
        # Check ICS structure
        add_check("voith_ics_structure",
                  "BEGIN:VCALENDAR" in ics3 and "BEGIN:VEVENT" in ics3 and "END:VCALENDAR" in ics3,
                  "Expected valid ICS structure")
        
        # Check default alarm 15min
        add_check("voith_alarm_default",
                  "TRIGGER:-PT15M" in ics3,
                  "Expected default alarm TRIGGER:-PT15M")
        
        # Check notes about budget or potential
        add_check("voith_notes_budget_potential",
                  "150" in ics3 or "Anbieter" in ics3 or "evaluiert" in ics3.lower(),
                  "Expected notes about multiple vendors or 150k potential")
        
        # Check CRM header present
        add_check("voith_crm_header",
                  "viSales CRM Reminder" in ics3,
                  "Expected CRM header viSales CRM Reminder")
    else:
        add_check("voith_file_exists", False, "No file matching 2026-04-29_Voith*_Reminder.ics found")
        for name in ["voith_dtstart", "voith_priority_mittel", "voith_deal_phase",
                     "voith_contact", "voith_topic", "voith_ics_structure",
                     "voith_alarm_default", "voith_notes_budget_potential", "voith_crm_header"]:
            add_check(name, False, "File not found")

    # ---- Global checks ----
    all_ics = list(workspace.rglob("*.ics"))
    # Filter out template files
    real_ics = [f for f in all_ics if "_Reminder.ics" in f.name]
    
    add_check("three_separate_ics_files",
              len(real_ics) >= 3,
              f"Expected 3+ ICS reminder files, found {len(real_ics)}: {[f.name for f in real_ics]}")
    
    # Check that filenames follow YYYY-MM-DD_CompanySlug_Reminder.ics convention
    filename_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}_[\w-]+_Reminder\.ics$')
    filenames_valid = all(filename_pattern.match(f.name) for f in real_ics)
    add_check("filename_convention_YYYY-MM-DD_Company_Reminder",
              filenames_valid,
              f"All filenames must match YYYY-MM-DD_Company_Reminder.ics. Got: {[f.name for f in real_ics]}")
    
    # Verify no spaces in filenames
    no_spaces = all(' ' not in f.name for f in real_ics)
    add_check("no_spaces_in_filenames",
              no_spaces,
              "Company name spaces must be replaced with hyphens in filenames")

    # Score calculation
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    overall_passed = score >= 0.75  # 75% threshold

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    run_eval(sys.argv[1])