import sys
import os
import json
import re
from pathlib import Path

def check(name, passed, detail=""):
    return {"name": name, "passed": passed, "detail": detail}

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []
    
    # ── Helper: find files ──────────────────────────────────────────────────
    def find_file(*rel_paths):
        """Try exact paths first, then rglob."""
        for rp in rel_paths:
            p = Path(workspace) / rp
            if p.exists():
                return p
        return None

    def read(p):
        if p is None:
            return ""
        try:
            return p.read_text(encoding="utf-8")
        except Exception:
            return ""

    # ═══════════════════════════════════════════════════════════════════════
    # CHECK 1: Architecture Analysis section present in agent's response file
    # The agent must have produced a structured response. We look for the
    # canonical output document. Accept any .md file in workspace root or docs/
    # ═══════════════════════════════════════════════════════════════════════
    response_candidates = list(Path(workspace).rglob("delegation-response.md")) + \
                          list(Path(workspace).rglob("txn-099-response.md")) + \
                          list(Path(workspace).rglob("feature-response.md")) + \
                          list(Path(workspace).rglob("response.md"))
    
    # Gather all top-level .md files that are NOT ARCHITECTURE.md or CHANGELOG.md
    for md in Path(workspace).glob("*.md"):
        if md.name not in ("ARCHITECTURE.md", "CHANGELOG.md") and md not in response_candidates:
            response_candidates.append(md)
    for md in (Path(workspace) / "docs").glob("*.md"):
        if md not in response_candidates:
            response_candidates.append(md)

    response_text = ""
    response_file = None
    for rc in response_candidates:
        content = read(rc)
        if "Architecture Analysis" in content or "Filepath Declaration" in content or "📁" in content:
            response_text = content
            response_file = rc
            break

    has_response = bool(response_text)
    checks.append(check(
        "Response document exists with Architecture Analysis content",
        has_response,
        f"Found: {response_file}" if has_response else "No response .md file found with required sections"
    ))

    # ── CHECK 2: ### Architecture Analysis section ──────────────────────────
    has_arch_analysis = bool(re.search(r"###?\s*Architecture Analysis", response_text, re.IGNORECASE))
    checks.append(check(
        "### Architecture Analysis section present",
        has_arch_analysis,
        "Found" if has_arch_analysis else "Missing '### Architecture Analysis' section heading"
    ))

    # ── CHECK 3: Filepath Declaration with 📁 emoji ─────────────────────────
    has_filepath_block = "📁" in response_text
    checks.append(check(
        "Filepath Declaration block uses 📁 emoji prefix",
        has_filepath_block,
        "Found '📁' in response" if has_filepath_block else "Missing '📁' emoji in filepath declaration"
    ))

    # ── CHECK 4: All three sub-fields in filepath block ──────────────────────
    has_purpose = bool(re.search(r"Purpose\s*:", response_text))
    has_depends = bool(re.search(r"Depends on\s*:", response_text))
    has_used_by = bool(re.search(r"Used by\s*:", response_text))
    filepath_fields_ok = has_purpose and has_depends and has_used_by
    checks.append(check(
        "Filepath block contains Purpose, Depends on, and Used by fields",
        filepath_fields_ok,
        f"Purpose={has_purpose}, 'Depends on'={has_depends}, 'Used by'={has_used_by}"
    ))

    # ── CHECK 5: kebab-case service filename ────────────────────────────────
    service_file = find_file(
        "src/services/risk/transaction-validator.py",
        "src/services/transactions/transaction-validator.py",
        "src/services/validation/transaction-validator.py",
        "src/services/risk/transaction_validator.py",
    )
    # Also search broadly
    if service_file is None:
        candidates = list(Path(workspace).rglob("transaction-validator.py")) + \
                     list(Path(workspace).rglob("transaction_validator.py"))
        if candidates:
            service_file = candidates[0]

    service_text = read(service_file)
    has_service = bool(service_text)

    # Prefer kebab-case
    kebab_service = service_file is not None and "transaction-validator" in str(service_file.name)
    checks.append(check(
        "Service file created with kebab-case filename (transaction-validator.py)",
        kebab_service,
        f"Found: {service_file}" if service_file else "No transaction validator service file found"
    ))

    # ── CHECK 6: Service class is PascalCase ────────────────────────────────
    pascal_class = bool(re.search(r"class\s+TransactionValidator\b", service_text))
    checks.append(check(
        "Service class named TransactionValidator (PascalCase)",
        pascal_class,
        "Found 'class TransactionValidator'" if pascal_class else f"PascalCase class not found in {service_file}"
    ))

    # ── CHECK 7: camelCase method names in service ───────────────────────────
    camel_methods = bool(re.search(r"def\s+validate[A-Z][a-zA-Z]+\s*\(", service_text)) or \
                    bool(re.search(r"def\s+validateTransaction\s*\(", service_text))
    checks.append(check(
        "Service methods use camelCase naming convention",
        camel_methods,
        "camelCase method detected" if camel_methods else "No camelCase method found (expected e.g. validateTransaction)"
    ))

    # ── CHECK 8: Amount validation (positive float ≤ 50000) ─────────────────
    has_amount_val = bool(re.search(r"50[_,]?000|50000", service_text))
    checks.append(check(
        "Service enforces amount ≤ 50,000 validation",
        has_amount_val,
        "Found 50000 limit" if has_amount_val else "No 50000 limit found in service"
    ))

    # ── CHECK 9: ISO 4217 currency validation ───────────────────────────────
    has_currency_val = bool(re.search(r"[A-Z]{3}|iso.*4217|len\(.*currency.*\)\s*==\s*3|currency.*[A-Za-z]{3}", service_text, re.IGNORECASE))
    checks.append(check(
        "Service validates currency as 3-letter ISO 4217 code",
        has_currency_val,
        "Currency validation found" if has_currency_val else "No ISO 4217 currency check found"
    ))

    # ── CHECK 10: ValidationResult model file ───────────────────────────────
    model_file = find_file("src/models/validation-result.py", "src/models/validation_result.py")
    if model_file is None:
        cands = list(Path(workspace).rglob("validation-result.py")) + \
                list(Path(workspace).rglob("validation_result.py"))
        if cands:
            model_file = cands[0]
    model_text = read(model_file)
    has_model = bool(model_text)
    checks.append(check(
        "ValidationResult model file created in src/models/",
        has_model,
        f"Found: {model_file}" if has_model else "No validation-result model file found"
    ))

    # ── CHECK 11: ValidationResult has required fields ───────────────────────
    has_is_valid = bool(re.search(r"is_valid\s*:", model_text))
    has_errors = bool(re.search(r"errors\s*:", model_text))
    has_risk_score = bool(re.search(r"risk_score\s*:", model_text))
    model_fields_ok = has_is_valid and has_errors and has_risk_score
    checks.append(check(
        "ValidationResult model has is_valid, errors, and risk_score fields",
        model_fields_ok,
        f"is_valid={has_is_valid}, errors={has_errors}, risk_score={has_risk_score}"
    ))

    # ── CHECK 12: ValidationResult is PascalCase Pydantic model ─────────────
    is_pydantic = bool(re.search(r"class\s+ValidationResult\s*\(.*BaseModel", model_text))
    checks.append(check(
        "ValidationResult is a PascalCase Pydantic BaseModel",
        is_pydantic,
        "Found Pydantic BaseModel" if is_pydantic else "ValidationResult is not a Pydantic BaseModel or wrong name"
    ))

    # ── CHECK 13: Test file in tests/unit/ or tests/integration/ ────────────
    test_candidates = list(Path(workspace).rglob("test_transaction_validator.py")) + \
                      list(Path(workspace).rglob("test-transaction-validator.py"))
    test_file = test_candidates[0] if test_candidates else None
    test_text = read(test_file)
    has_tests = bool(test_text) and "def test_" in test_text
    checks.append(check(
        "Test file created with at least one test function",
        has_tests,
        f"Found: {test_file}" if has_tests else "No test file for transaction validator found"
    ))

    # ── CHECK 14: Test file is in tests/ directory ───────────────────────────
    test_in_tests_dir = test_file is not None and "tests" in str(test_file)
    checks.append(check(
        "Test file located inside tests/ directory",
        test_in_tests_dir,
        f"Path: {test_file}" if test_file else "Test file not found"
    ))

    # ── CHECK 15: Compliance Checklist in response ───────────────────────────
    has_checklist = bool(re.search(r"- \[[ xX]\]", response_text))
    checks.append(check(
        "Compliance Checklist present in response (checkbox items)",
        has_checklist,
        "Checklist found" if has_checklist else "No checklist items '- [ ]' or '- [x]' found in response"
    ))

    # ── CHECK 16: All checklist items are checked ────────────────────────────
    unchecked = re.findall(r"- \[ \]", response_text)
    checked = re.findall(r"- \[[xX]\]", response_text)
    all_checked = len(checked) >= 8 and len(unchecked) == 0
    checks.append(check(
        "All compliance checklist items are marked complete ([x])",
        all_checked,
        f"Checked={len(checked)}, Unchecked={len(unchecked)}"
    ))

    # ── CHECK 17: ⚠️ ARCHITECTURE UPDATE section ──────────────────────────────
    has_arch_update = bool(re.search(r"ARCHITECTURE UPDATE|⚠️", response_text))
    checks.append(check(
        "⚠️ ARCHITECTURE UPDATE section present",
        has_arch_update,
        "Found ARCHITECTURE UPDATE" if has_arch_update else "Missing '⚠️ ARCHITECTURE UPDATE' section"
    ))

    # ── CHECK 18: What/Why/Impact sub-fields in Architectural Impact ─────────
    has_what = bool(re.search(r"\bWhat\s*:", response_text))
    has_why = bool(re.search(r"\bWhy\s*:", response_text))
    has_impact = bool(re.search(r"\bImpact\s*:", response_text))
    arch_update_fields = has_what and has_why and has_impact
    checks.append(check(
        "Architectural Impact block contains What, Why, and Impact sub-fields",
        arch_update_fields,
        f"What={has_what}, Why={has_why}, Impact={has_impact}"
    ))

    # ── CHECK 19: CHANGELOG.md updated ──────────────────────────────────────
    changelog_path = Path(workspace) / "CHANGELOG.md"
    changelog_text = read(changelog_path)
    has_changelog = bool(changelog_text) and len(changelog_text.strip()) > 20
    checks.append(check(
        "CHANGELOG.md created/updated at repo root",
        has_changelog,
        f"Length={len(changelog_text)} chars" if has_changelog else "CHANGELOG.md missing or empty"
    ))

    # ── CHECK 20: Testing Requirements section ───────────────────────────────
    has_testing_req = bool(re.search(r"###?\s*Testing Requirements", response_text, re.IGNORECASE))
    checks.append(check(
        "### Testing Requirements section present in response",
        has_testing_req,
        "Found" if has_testing_req else "Missing '### Testing Requirements' section"
    ))

    # ── Score ────────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    overall = passed_count >= int(total * 0.75)  # 75% threshold to pass

    result = {
        "passed": overall,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()