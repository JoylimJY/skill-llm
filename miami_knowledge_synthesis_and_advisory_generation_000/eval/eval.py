import sys
import json
import os
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    total_score = 0.0
    max_score = 10

    # --- Find the output file ---
    advisory_files = list(Path(workspace).rglob("miami_relocation_advisory.json"))
    
    if not advisory_files:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_exists", "passed": False, "detail": "miami_relocation_advisory.json not found anywhere in workspace."}]
        }))
        return

    # Use the most recently modified one if multiple
    advisory_path = sorted(advisory_files, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    
    try:
        with open(advisory_path, "r") as f:
            advisory = json.load(f)
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_parseable", "passed": False, "detail": f"Could not parse JSON: {e}"}]
        }))
        return

    # Helper: search recursively in a dict/list for a string value (case-insensitive)
    def contains_text(obj, text: str) -> bool:
        text_lower = text.lower()
        if isinstance(obj, str):
            return text_lower in obj.lower()
        elif isinstance(obj, dict):
            return any(contains_text(v, text) for v in obj.values())
        elif isinstance(obj, list):
            return any(contains_text(item, text) for item in obj)
        return False

    def find_employee(advisory, emp_id_or_name_fragment: str) -> dict:
        """Find an employee entry by id or name fragment."""
        candidates = []
        # Try top-level list
        if isinstance(advisory, list):
            candidates = advisory
        elif isinstance(advisory, dict):
            # Look for a list under common keys
            for key in ["employees", "advisories", "profiles", "recommendations", "hires"]:
                if key in advisory and isinstance(advisory[key], list):
                    candidates = advisory[key]
                    break
            if not candidates:
                # Try any list value
                for v in advisory.values():
                    if isinstance(v, list) and len(v) > 0:
                        candidates = v
                        break
        
        frag = emp_id_or_name_fragment.lower()
        for item in candidates:
            if isinstance(item, dict):
                item_str = json.dumps(item).lower()
                if frag in item_str:
                    return item
        return {}

    advisory_str = json.dumps(advisory).lower()

    # ---- CHECK 1: File is valid JSON with employee entries ----
    has_employees = False
    emp_list = []
    if isinstance(advisory, list) and len(advisory) >= 3:
        has_employees = True
        emp_list = advisory
    elif isinstance(advisory, dict):
        for key in ["employees", "advisories", "profiles", "recommendations", "hires"]:
            if key in advisory and isinstance(advisory[key], list) and len(advisory[key]) >= 3:
                has_employees = True
                emp_list = advisory[key]
                break

    checks.append({
        "name": "output_has_three_employee_entries",
        "passed": has_employees,
        "detail": f"Advisory contains entries for all 3 employees: {has_employees}. Found at path: {advisory_path}"
    })
    if has_employees:
        total_score += 0.5

    # ---- CHECK 2: Sarah Chen (Senior SWE) → Wynwood, Brickell, or Design District (NOT South Beach) ----
    sarah = find_employee(advisory, "sarah") or find_employee(advisory, "emp-001") or find_employee(advisory, "senior software engineer")
    sarah_str = json.dumps(sarah).lower() if sarah else advisory_str  # fallback to full doc

    correct_tech_neighborhoods = ["wynwood", "brickell", "design district"]
    sarah_correct_neighborhood = any(n in sarah_str for n in correct_tech_neighborhoods)
    south_beach_for_sarah = "south beach" in sarah_str and sarah != {} and not any(
        phrase in sarah_str for phrase in ["avoid south beach", "not south beach", "skip south beach"]
    )
    # Only penalize if Sarah's section positively recommends south beach
    sarah_neighborhood_ok = sarah_correct_neighborhood and not south_beach_for_sarah

    checks.append({
        "name": "sarah_tech_neighborhood_correct",
        "passed": sarah_neighborhood_ok,
        "detail": f"Sarah (Senior SWE/tech worker) correctly recommended Wynwood/Brickell/Design District (not South Beach). Correct neighborhood present: {sarah_correct_neighborhood}, South Beach falsely recommended: {south_beach_for_sarah}"
    })
    if sarah_neighborhood_ok:
        total_score += 1.5

    # ---- CHECK 3: Sarah's car myth debunked (car IS required, not optional) ----
    # The agent must correct Sarah's assumption "won't need a car"
    sarah_car_warning = any(phrase in advisory_str for phrase in [
        "car is essential", "car required", "not walkable", "cannot live without a car",
        "need a car", "must have a car", "car-dependent", "car dependent",
        "public transit limited", "transit is limited", "transit is poor"
    ])
    checks.append({
        "name": "sarah_car_myth_debunked",
        "passed": sarah_car_warning,
        "detail": f"Advisory correctly states Miami requires a car / is car-dependent (debunking Sarah's assumption). Found: {sarah_car_warning}"
    })
    if sarah_car_warning:
        total_score += 1.0

    # ---- CHECK 4: Car insurance range is correct ($200-400/month) ----
    import re
    # Look for car insurance figures
    insurance_pattern = re.search(r'(car insurance|auto insurance|insurance).{0,80}(\$200|\$250|\$300|\$350|\$400|200.{0,5}400|200/month|400/month)', advisory_str)
    # Also accept "3,000-4,000/year" or "3-4k/year" or "$3,000-$4,000"
    insurance_annual_pattern = re.search(r'(car insurance|auto insurance|insurance).{0,80}(\$3[,.]?000|\$4[,.]?000|3,000.{0,5}4,000|3k.{0,5}4k|\$3-4k)', advisory_str)
    car_insurance_correct = bool(insurance_pattern or insurance_annual_pattern)
    # Also check for "highest in US" or "Florida" insurance mention
    insurance_florida_warning = any(phrase in advisory_str for phrase in [
        "highest in us", "florida has highest", "florida insurance", "insurance shock",
        "insurance crisis", "$200-400", "200-400/month", "3,000-4,000/year", "3-4k/year"
    ])
    car_insurance_check = car_insurance_correct or insurance_florida_warning

    checks.append({
        "name": "car_insurance_correct_range",
        "passed": car_insurance_check,
        "detail": f"Advisory includes correct car insurance range ($200-400/month or $3-4K/year, Florida highest in US). Found: {car_insurance_check}"
    })
    if car_insurance_check:
        total_score += 1.0

    # ---- CHECK 5: Marcus Webb (Startup/Founder) → Wynwood recommended ----
    marcus = find_employee(advisory, "marcus") or find_employee(advisory, "emp-002") or find_employee(advisory, "founder")
    marcus_str = json.dumps(marcus).lower() if marcus else advisory_str

    marcus_wynwood = "wynwood" in marcus_str
    checks.append({
        "name": "marcus_startup_wynwood_recommended",
        "passed": marcus_wynwood,
        "detail": f"Marcus (founder/startup CTO) correctly recommended Wynwood as primary startup hub. Found: {marcus_wynwood}"
    })
    if marcus_wynwood:
        total_score += 1.0

    # ---- CHECK 6: Marcus — NYC is NOT cheaper myth debunked ----
    nyc_myth_debunked = any(phrase in advisory_str for phrase in [
        "not cheaper than nyc", "comparable to nyc", "now comparable", "rent is comparable",
        "not a cheap alternative", "cheap alternative myth", "comparable rent",
        "lower salaries", "salaries lower than nyc", "myth", "not significantly cheaper"
    ])
    checks.append({
        "name": "marcus_nyc_cheaper_myth_debunked",
        "passed": nyc_myth_debunked,
        "detail": f"Advisory correctly debunks 'Miami is cheap alternative to NYC' myth for Marcus. Found: {nyc_myth_debunked}"
    })
    if nyc_myth_debunked:
        total_score += 1.0

    # ---- CHECK 7: Marcus — Condo/post-Surfside warning ----
    condo_warning = any(phrase in advisory_str for phrase in [
        "surfside", "special assessment", "condo assessment", "reserve", "condo fees",
        "post-surfside", "building inspection", "pending assessment", "champlain"
    ])
    checks.append({
        "name": "marcus_condo_surfside_warning",
        "passed": condo_warning,
        "detail": f"Advisory includes post-Surfside condo assessment warning for Marcus (or general). Found: {condo_warning}"
    })
    if condo_warning:
        total_score += 1.0

    # ---- CHECK 8: Priya Nair (intern/student) → correct budget range $1,800-2,500/month ----
    priya = find_employee(advisory, "priya") or find_employee(advisory, "emp-003") or find_employee(advisory, "intern")
    priya_str = json.dumps(priya).lower() if priya else advisory_str

    budget_pattern = re.search(r'(1[,.]?800|1800).{0,30}(2[,.]?500|2500)', priya_str)
    budget_pattern2 = re.search(r'(2[,.]?500|2500).{0,30}(1[,.]?800|1800)', priya_str)
    # Also accept just "$1,800" or "$2,500" appearing in Priya's section
    budget_single = re.search(r'(\$1,?800|\$2,?500|1800|2500)', priya_str)
    priya_budget_correct = bool(budget_pattern or budget_pattern2 or budget_single)

    checks.append({
        "name": "priya_student_budget_correct",
        "passed": priya_budget_correct,
        "detail": f"Priya's advisory includes correct student budget range ($1,800-2,500/month). Found: {priya_budget_correct}"
    })
    if priya_budget_correct:
        total_score += 1.0

    # ---- CHECK 9: Priya — public transit myth debunked (car needed, transit is poor) ----
    priya_transit_myth = any(phrase in priya_str for phrase in [
        "transit is poor", "transit is limited", "car needed", "need a car",
        "cannot rely on public transit", "not like boston", "limited transit",
        "public transit limited", "car is recommended", "car essential",
        "not walkable", "get a car"
    ])
    # Fall back to global advisory check
    if not priya_transit_myth:
        priya_transit_myth = any(phrase in advisory_str for phrase in [
            "transit is poor", "public transit limited", "not like boston",
            "cannot rely on public transit"
        ])
    checks.append({
        "name": "priya_transit_myth_debunked",
        "passed": priya_transit_myth,
        "detail": f"Advisory debunks public transit adequacy for Priya (intern/student). Miami is not like Boston for transit. Found: {priya_transit_myth}"
    })
    if priya_transit_myth:
        total_score += 1.0

    # ---- CHECK 10: Correct senior SWE salary range mentioned ($120K-180K) ----
    salary_pattern = re.search(r'(120[,k]?|120,000).{0,30}(180[,k]?|180,000)', advisory_str)
    salary_mention = re.search(r'(\$120|\$180|120k|180k|120,000|180,000)', advisory_str)
    no_state_tax = any(phrase in advisory_str for phrase in [
        "no state tax", "no state income tax", "no florida income tax",
        "florida has no", "florida no income tax", "state tax"
    ])
    salary_correct = bool(salary_pattern or salary_mention) and no_state_tax

    checks.append({
        "name": "senior_swe_salary_and_no_state_tax",
        "passed": salary_correct,
        "detail": f"Advisory includes correct Senior SWE salary ($120K-180K) AND mentions Florida no state income tax. Salary found: {bool(salary_pattern or salary_mention)}, No state tax: {no_state_tax}"
    })
    if salary_correct:
        total_score += 0.5

    # Normalize score to 0-1
    normalized_score = round(min(total_score / max_score, 1.0), 3)
    passed = normalized_score >= 0.65  # Must get at least 6.5/10 points

    result = {
        "passed": passed,
        "score": normalized_score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(workspace)