import sys
import json
import re
from pathlib import Path

def load_checks():
    return []

def find_file(workspace, filename):
    results = list(Path(workspace).rglob(filename))
    return results[0] if results else None

def parse_sql_values(sql_text):
    """Extract VALUES tuples from an INSERT statement."""
    # Find everything between VALUES ( ... ) ON CONFLICT
    match = re.search(r'VALUES\s*(.*?)\s*ON CONFLICT', sql_text, re.DOTALL | re.IGNORECASE)
    if not match:
        return []
    values_block = match.group(1).strip()
    # Split into individual tuples
    tuples = re.findall(r'\(([^()]*(?:\([^()]*\)[^()]*)*)\)', values_block)
    return tuples

def check_file_exists(workspace, filename, checks, check_name):
    f = find_file(workspace, filename)
    if f is None:
        checks.append({"name": check_name, "passed": False, "detail": f"{filename} not found anywhere in workspace"})
        return None
    checks.append({"name": check_name, "passed": True, "detail": f"Found at {f}"})
    return f

def main():
    workspace = sys.argv[1]
    checks = []
    
    # ── File existence checks ────────────────────────────────────────────────
    cat_file   = check_file_exists(workspace, "1_insert_categories.sql", checks, "1_insert_categories.sql exists")
    skill_file = check_file_exists(workspace, "2_insert_skills.sql",     checks, "2_insert_skills.sql exists")
    emp_file   = check_file_exists(workspace, "3_insert_employee_skills.sql", checks, "3_insert_employee_skills.sql exists")
    report_file= check_file_exists(workspace, "skipped_employees_report.txt", checks, "skipped_employees_report.txt exists")

    # ── READ FILES ───────────────────────────────────────────────────────────
    cat_sql   = open(cat_file).read()   if cat_file   else ""
    skill_sql = open(skill_file).read() if skill_file else ""
    emp_sql   = open(emp_file).read()   if emp_file   else ""
    report    = open(report_file).read().lower() if report_file else ""

    # ════════════════════════════════════════════════════════════════════════
    # CHECK GROUP 1: 1_insert_categories.sql
    # ════════════════════════════════════════════════════════════════════════

    # Must insert .NET and Front-end (new), but NOT Java or DevOps (already in DB)
    check_net = "'.NET'" in cat_sql or '".NET"' in cat_sql or "'.NET'" in cat_sql
    # handle both quote styles
    check_net2 = re.search(r"['\"]\.NET['\"]", cat_sql) is not None
    checks.append({
        "name": "categories: .NET is inserted",
        "passed": check_net2,
        "detail": f"'.NET' found in 1_insert_categories.sql: {check_net2}"
    })

    check_frontend = re.search(r"['\"]Front-end['\"]", cat_sql) is not None
    checks.append({
        "name": "categories: Front-end is inserted",
        "passed": check_frontend,
        "detail": f"'Front-end' found in 1_insert_categories.sql: {check_frontend}"
    })

    check_java_absent = re.search(r"['\"]Java['\"]", cat_sql) is None
    checks.append({
        "name": "categories: Java NOT re-inserted (already in DB)",
        "passed": check_java_absent,
        "detail": f"'Java' absent from 1_insert_categories.sql: {check_java_absent}"
    })

    check_devops_absent = re.search(r"['\"]DevOps['\"]", cat_sql) is None
    checks.append({
        "name": "categories: DevOps NOT re-inserted (already in DB)",
        "passed": check_devops_absent,
        "detail": f"'DevOps' absent from 1_insert_categories.sql: {check_devops_absent}"
    })

    check_cat_conflict = re.search(r'ON CONFLICT\s*\(name\)\s*DO NOTHING', cat_sql, re.IGNORECASE) is not None
    checks.append({
        "name": "categories: ON CONFLICT (name) DO NOTHING clause",
        "passed": check_cat_conflict,
        "detail": f"Correct ON CONFLICT clause in 1_insert_categories.sql: {check_cat_conflict}"
    })

    # ════════════════════════════════════════════════════════════════════════
    # CHECK GROUP 2: 2_insert_skills.sql
    # ════════════════════════════════════════════════════════════════════════

    # New skills: C#, ASP.net, MVC (under .NET), JavaScript, HTML, CSS (under Front-end)
    # Kubernetes (under DevOps) - new skill even though DevOps category exists
    # Already in DB: Java, Spring, Docker → must NOT appear

    new_skills = [
        ("C#", ".NET"),
        ("ASP.net", ".NET"),
        ("MVC", ".NET"),
        ("JavaScript", "Front-end"),
        ("HTML", "Front-end"),
        ("CSS", "Front-end"),
        ("Kubernetes", "DevOps"),
    ]
    existing_skills = ["Java", "Spring", "Docker"]

    for skill_name, category in new_skills:
        present = re.search(re.escape(f"'{skill_name}'"), skill_sql) or \
                  re.search(re.escape(f'"{skill_name}"'), skill_sql)
        checks.append({
            "name": f"skills: '{skill_name}' is inserted",
            "passed": bool(present),
            "detail": f"'{skill_name}' found in 2_insert_skills.sql: {bool(present)}"
        })
        # Check subquery references correct category
        # Pattern: ('SkillName', (SELECT id FROM skill_categories WHERE name = 'Category'))
        pattern = re.compile(
            re.escape(f"'{skill_name}'") + r".*?SELECT\s+id\s+FROM\s+skill_categories\s+WHERE\s+name\s*=\s*'" + re.escape(category) + r"'",
            re.DOTALL | re.IGNORECASE
        )
        cat_subquery_ok = bool(pattern.search(skill_sql))
        checks.append({
            "name": f"skills: '{skill_name}' references correct category '{category}' via subquery",
            "passed": cat_subquery_ok,
            "detail": f"Category subquery for '{skill_name}' → '{category}' found: {cat_subquery_ok}"
        })

    for skill_name in existing_skills:
        absent = not bool(re.search(r"['\"]" + re.escape(skill_name) + r"['\"]", skill_sql))
        checks.append({
            "name": f"skills: '{skill_name}' NOT re-inserted (already in DB)",
            "passed": absent,
            "detail": f"'{skill_name}' absent from 2_insert_skills.sql: {absent}"
        })

    check_skill_conflict = re.search(r'ON CONFLICT\s*\(name\)\s*DO NOTHING', skill_sql, re.IGNORECASE) is not None
    checks.append({
        "name": "skills: ON CONFLICT (name) DO NOTHING clause",
        "passed": check_skill_conflict,
        "detail": f"Correct ON CONFLICT clause in 2_insert_skills.sql: {check_skill_conflict}"
    })

    # ════════════════════════════════════════════════════════════════════════
    # CHECK GROUP 3: 3_insert_employee_skills.sql
    # ════════════════════════════════════════════════════════════════════════

    # TRIM() in WHERE clauses (proprietary trap)
    check_trim_first = re.search(r'TRIM\s*\(\s*first_name\s*\)', emp_sql, re.IGNORECASE) is not None
    checks.append({
        "name": "employee_skills: TRIM(first_name) used in WHERE clause",
        "passed": check_trim_first,
        "detail": f"TRIM(first_name) found in 3_insert_employee_skills.sql: {check_trim_first}"
    })

    check_trim_last = re.search(r'TRIM\s*\(\s*last_name\s*\)', emp_sql, re.IGNORECASE) is not None
    checks.append({
        "name": "employee_skills: TRIM(last_name) used in WHERE clause",
        "passed": check_trim_last,
        "detail": f"TRIM(last_name) found in 3_insert_employee_skills.sql: {check_trim_last}"
    })

    # ON CONFLICT DO UPDATE SET years_of_experience = EXCLUDED.years_of_experience
    check_emp_conflict = re.search(
        r'ON CONFLICT\s*\(employee_id\s*,\s*skill_id\s*\)\s*DO UPDATE\s+SET\s+years_of_experience\s*=\s*EXCLUDED\.years_of_experience',
        emp_sql, re.IGNORECASE
    ) is not None
    checks.append({
        "name": "employee_skills: ON CONFLICT (employee_id, skill_id) DO UPDATE SET years_of_experience",
        "passed": check_emp_conflict,
        "detail": f"Correct ON CONFLICT clause: {check_emp_conflict}"
    })

    # Fuzzy match: "Victoriia" → "Viktoriia" corrected in SQL
    check_viktoriia = re.search(r"'Viktoriia'", emp_sql) is not None
    check_victoriia_wrong = re.search(r"'Victoriia'", emp_sql) is not None
    checks.append({
        "name": "employee_skills: 'Victoriia' corrected to 'Viktoriia' (fuzzy match)",
        "passed": check_viktoriia and not check_victoriia_wrong,
        "detail": f"'Viktoriia' present: {check_viktoriia}, 'Victoriia' (wrong) present: {check_victoriia_wrong}"
    })

    # Yurii Solokha must appear (TRIM handles the 3 extra spaces in DB)
    check_yurii = re.search(r"'Yurii'", emp_sql) is not None
    checks.append({
        "name": "employee_skills: Yurii Solokha included (TRIM handles DB whitespace)",
        "passed": check_yurii,
        "detail": f"'Yurii' found in employee_skills SQL: {check_yurii}"
    })

    # Deduplication: John Doe + C# should appear exactly ONCE, with value 7 (max of 5 and 7)
    # Find all John Doe + C# tuples
    john_csharp_matches = re.findall(
        r"'John'.*?'Doe'.*?'C#'|'C#'.*?'John'.*?'Doe'",
        emp_sql, re.DOTALL | re.IGNORECASE
    )
    # Better: find occurrences of C# near John/Doe
    # Count how many times (John, Doe, C#) triple appears as a VALUES tuple
    # We look for tuples containing both John+Doe and C#
    value_tuples = re.findall(r'\(\s*\(SELECT[^)]*\)[^,)]*,\s*\(SELECT[^)]*\)[^,)]*,\s*[\d.]+\s*\)', emp_sql, re.DOTALL)
    
    # Simpler approach: count occurrences of 'C#' associated with John Doe
    # Find blocks between VALUES and ON CONFLICT
    values_section = re.search(r'VALUES\s*(.*?)ON CONFLICT', emp_sql, re.DOTALL | re.IGNORECASE)
    vs = values_section.group(1) if values_section else ""
    
    # Count John+Doe+C# combos
    john_doe_csharp_count = 0
    john_doe_csharp_7 = False
    # Split on individual value groups - look for patterns with John, Doe, C#, and a number
    # Find all individual INSERT value blocks (each employee-skill pair)
    # Pattern: ( (SELECT...'John'...Doe'...), (SELECT...'C#'...), NUMBER )
    entry_pattern = re.compile(
        r'\(\s*\(SELECT\s+id\s+FROM\s+employees\s+WHERE\s+TRIM.*?=\s*\'John\'.*?TRIM.*?=\s*\'Doe\'.*?\).*?\(SELECT\s+id\s+FROM\s+skills\s+WHERE\s+name\s*=\s*\'C#\'.*?\).*?([\d.]+)\s*\)',
        re.DOTALL | re.IGNORECASE
    )
    entries = entry_pattern.findall(emp_sql)
    john_doe_csharp_count = len(entries)
    john_doe_csharp_7 = any(e.strip() == '7' for e in entries)

    checks.append({
        "name": "employee_skills: John Doe + C# deduplicated to exactly 1 entry",
        "passed": john_doe_csharp_count == 1,
        "detail": f"John Doe + C# entries found: {john_doe_csharp_count} (expected 1)"
    })
    checks.append({
        "name": "employee_skills: John Doe + C# has max value 7 (dedup keeps highest)",
        "passed": john_doe_csharp_7,
        "detail": f"Value 7 found for John Doe + C#: {john_doe_csharp_7}, all values: {entries}"
    })

    # Zero-experience skills must be absent
    # John Doe: MVC=0, HTML=0, CSS=0, Java=0, Spring=0, Docker=0, Kubernetes=0
    # Verify MVC is absent for John Doe (or absent entirely if no one has MVC)
    # Actually check: no zero-value entries at all
    # We check that John Doe doesn't have a MVC entry (he had 0 in both rows)
    john_mvc = re.search(
        r"'John'.*?'Doe'.*?'MVC'|'MVC'.*?'John'.*?'Doe'",
        emp_sql, re.DOTALL | re.IGNORECASE
    )
    checks.append({
        "name": "employee_skills: Zero-experience skills excluded (John Doe has no MVC entry)",
        "passed": john_mvc is None,
        "detail": f"John Doe + MVC (zero exp) found in SQL: {john_mvc is not None}"
    })

    # Subquery for skill lookup
    check_skill_subquery = re.search(r'SELECT\s+id\s+FROM\s+skills\s+WHERE\s+name\s*=', emp_sql, re.IGNORECASE) is not None
    checks.append({
        "name": "employee_skills: skill_id looked up via subquery (not hardcoded UUID)",
        "passed": check_skill_subquery,
        "detail": f"SELECT id FROM skills WHERE name subquery found: {check_skill_subquery}"
    })

    # Xanthe Zarakis must NOT appear in SQL (no DB match)
    check_xanthe_absent = re.search(r"'Xanthe'", emp_sql) is None
    checks.append({
        "name": "employee_skills: Xanthe Zarakis excluded (no DB match)",
        "passed": check_xanthe_absent,
        "detail": f"'Xanthe' absent from employee_skills SQL: {check_xanthe_absent}"
    })

    # Boris Karasov (with leading/trailing spaces) must NOT appear (no DB match)
    check_boris_absent = re.search(r"'Boris'", emp_sql) is None
    checks.append({
        "name": "employee_skills: Boris Karasov excluded (no DB match after trim)",
        "passed": check_boris_absent,
        "detail": f"'Boris' absent from employee_skills SQL: {check_boris_absent}"
    })

    # ════════════════════════════════════════════════════════════════════════
    # CHECK GROUP 4: skipped_employees_report.txt
    # ════════════════════════════════════════════════════════════════════════

    check_report_xanthe = "xanthe" in report or "zarakis" in report
    checks.append({
        "name": "report: Xanthe Zarakis mentioned as skipped",
        "passed": check_report_xanthe,
        "detail": f"'xanthe'/'zarakis' in report: {check_report_xanthe}"
    })

    check_report_boris = "boris" in report or "karasov" in report
    checks.append({
        "name": "report: Boris Karasov mentioned as skipped",
        "passed": check_report_boris,
        "detail": f"'boris'/'karasov' in report: {check_report_boris}"
    })

    check_report_correction = ("victoriia" in report or "viktoriia" in report)
    checks.append({
        "name": "report: Name correction Victoriia→Viktoriia mentioned",
        "passed": check_report_correction,
        "detail": f"Correction mention found in report: {check_report_correction}"
    })

    # ════════════════════════════════════════════════════════════════════════
    # SCORING
    # ════════════════════════════════════════════════════════════════════════
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    overall_passed = score >= 0.80  # 80% threshold for pass

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()