import sys
import json
import re
from pathlib import Path

def check(name, passed, detail=""):
    return {"name": name, "passed": passed, "detail": detail}

def main(workspace):
    ws = Path(workspace)
    checks = []

    # ── 1. Find the Swift test file ───────────────────────────────────────────
    swift_candidates = list(ws.rglob("KanbanBoardViewModelTests.swift"))
    if not swift_candidates:
        # also accept BoardViewModelTests.swift
        swift_candidates = list(ws.rglob("BoardViewModelTests.swift"))

    if not swift_candidates:
        checks.append(check("swift_test_file_exists", False,
                            "Neither KanbanBoardViewModelTests.swift nor BoardViewModelTests.swift found."))
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    swift_file = swift_candidates[0]
    swift_text = swift_file.read_text(errors="replace")
    checks.append(check("swift_test_file_exists", True, str(swift_file.relative_to(ws))))

    # ── 2. File must be inside Tests/.../Localization/ ────────────────────────
    in_localization = "Localization" in str(swift_file)
    checks.append(check("file_in_localization_directory", in_localization,
                        str(swift_file.relative_to(ws))))

    # ── 3. Imports: FOSFoundation, FOSMVVM (testable), FOSTesting, Testing ────
    has_fosfoundation = "import FOSFoundation" in swift_text
    has_fosmvvm = "@testable import FOSMVVM" in swift_text
    has_fostesting = "import FOSTesting" in swift_text
    has_testing = re.search(r'\bimport Testing\b', swift_text) is not None
    imports_ok = has_fosfoundation and has_fosmvvm and has_fostesting and has_testing
    checks.append(check("required_imports_present", imports_ok,
                        f"FOSFoundation={has_fosfoundation}, @testable FOSMVVM={has_fosmvvm}, "
                        f"FOSTesting={has_fostesting}, Testing={has_testing}"))

    # ── 4. Struct conforms to LocalizableTestCase ─────────────────────────────
    localizable_conformance = bool(re.search(r'struct\s+\w+\s*:\s*LocalizableTestCase', swift_text))
    checks.append(check("LocalizableTestCase_conformance", localizable_conformance,
                        "Struct must declare ': LocalizableTestCase'"))

    # ── 5. @Suite decorator present ───────────────────────────────────────────
    has_suite = "@Suite(" in swift_text
    checks.append(check("suite_decorator_present", has_suite, ""))

    # ── 6. locStore property + loadLocalizationStore init ─────────────────────
    has_locstore = "let locStore: LocalizationStore" in swift_text
    has_load = "loadLocalizationStore(" in swift_text
    has_bundle_module = "Bundle.module" in swift_text
    has_resource_dir = '"TestYAML"' in swift_text
    init_ok = has_locstore and has_load and has_bundle_module and has_resource_dir
    checks.append(check("locStore_init_correct", init_ok,
                        f"locStore={has_locstore}, loadLocalizationStore={has_load}, "
                        f"Bundle.module={has_bundle_module}, resourceDir=TestYAML={has_resource_dir}"))

    # ── 7. expectFullViewModelTests called for BoardViewModel ─────────────────
    board_test = bool(re.search(r'expectFullViewModelTests\s*\(\s*BoardViewModel\.self\s*\)', swift_text))
    checks.append(check("expectFullViewModelTests_BoardViewModel", board_test, ""))

    # ── 8. expectFullViewModelTests called for ColumnViewModel ───────────────
    column_test = bool(re.search(r'expectFullViewModelTests\s*\(\s*ColumnViewModel\.self\s*\)', swift_text))
    checks.append(check("expectFullViewModelTests_ColumnViewModel", column_test, ""))

    # ── 9. expectFullViewModelTests called for CardViewModel ─────────────────
    card_test = bool(re.search(r'expectFullViewModelTests\s*\(\s*CardViewModel\.self\s*\)', swift_text))
    checks.append(check("expectFullViewModelTests_CardViewModel", card_test, ""))

    # ── 10. Custom locales override including enGB ────────────────────────────
    has_locales_override = bool(re.search(r'var\s+locales\s*:', swift_text))
    has_engb = "enGB" in swift_text
    locale_override_ok = has_locales_override and has_engb
    checks.append(check("custom_locales_override_with_enGB", locale_override_ok,
                        f"locales override={has_locales_override}, enGB present={has_engb}"))

    # ── 11. Substitution test for CardViewModel (dueLabel) ───────────────────
    has_substitution_test = bool(re.search(
        r'dueLabel.*localizedString|localizedString.*dueLabel', swift_text))
    # also accept a test that stubs and checks the dueLabel value
    has_sub_verify = bool(re.search(r'#expect.*dueLabel', swift_text))
    sub_test_ok = has_substitution_test or has_sub_verify
    checks.append(check("substitution_verification_for_dueLabel", sub_test_ok,
                        "Should have an #expect assertion for dueLabel.localizedString"))

    # ── 12. Find YAML file(s) ─────────────────────────────────────────────────
    yaml_candidates = list(ws.rglob("*.yml")) + list(ws.rglob("*.yaml"))
    # filter to TestYAML directory
    test_yamls = [y for y in yaml_candidates if "TestYAML" in str(y)
                  and not y.name.endswith(".incomplete")]
    has_yaml = len(test_yamls) > 0
    checks.append(check("yaml_file_exists_in_TestYAML", has_yaml,
                        f"Found: {[str(y.relative_to(ws)) for y in test_yamls]}"))

    if not has_yaml:
        # Can't do further YAML checks
        score = sum(1 for c in checks if c["passed"]) / len(checks)
        return {"passed": False, "score": round(score, 3), "checks": checks}

    # Merge all YAML content for analysis
    import yaml as pyyaml
    combined_yaml = {}
    for yf in test_yamls:
        try:
            data = pyyaml.safe_load(yf.read_text(errors="replace")) or {}
            for locale, vms in data.items():
                if locale not in combined_yaml:
                    combined_yaml[locale] = {}
                if isinstance(vms, dict):
                    combined_yaml[locale].update(vms)
        except Exception as e:
            checks.append(check("yaml_parse_error", False, str(e)))

    # ── 13. YAML has 'en' locale ──────────────────────────────────────────────
    has_en = "en" in combined_yaml
    checks.append(check("yaml_has_en_locale", has_en, f"Locales found: {list(combined_yaml.keys())}"))

    # ── 14. YAML has 'es' locale ──────────────────────────────────────────────
    has_es = "es" in combined_yaml
    checks.append(check("yaml_has_es_locale", has_es, ""))

    # ── 15. YAML has 'en-GB' or 'enGB' locale (matching custom locale override) ─
    has_engb_yaml = any(k in ("en-GB", "enGB", "en_GB") for k in combined_yaml.keys())
    checks.append(check("yaml_has_enGB_locale", has_engb_yaml,
                        f"Locales found: {list(combined_yaml.keys())}"))

    # ── 16. BoardViewModel entries in YAML (en) ───────────────────────────────
    en_board = combined_yaml.get("en", {}).get("BoardViewModel", {})
    board_has_title = "boardTitle" in en_board
    board_has_desc = "boardDescription" in en_board
    board_yaml_ok = board_has_title and board_has_desc
    checks.append(check("yaml_BoardViewModel_en_complete", board_yaml_ok,
                        f"boardTitle={board_has_title}, boardDescription={board_has_desc}"))

    # ── 17. ColumnViewModel entries in YAML (en) ─────────────────────────────
    en_col = combined_yaml.get("en", {}).get("ColumnViewModel", {})
    col_yaml_ok = "columnName" in en_col
    checks.append(check("yaml_ColumnViewModel_en_present", col_yaml_ok,
                        f"Found keys: {list(en_col.keys())}"))

    # ── 18. CardViewModel entries in YAML (en) with substitution syntax ───────
    en_card = combined_yaml.get("en", {}).get("CardViewModel", {})
    card_has_title = "cardTitle" in en_card
    card_has_due = "dueLabel" in en_card
    # dueLabel must use %{...} substitution syntax
    due_val = en_card.get("dueLabel", "")
    card_sub_syntax = bool(re.search(r'%\{[^}]+\}', str(due_val)))
    card_yaml_ok = card_has_title and card_has_due and card_sub_syntax
    checks.append(check("yaml_CardViewModel_en_with_substitution_syntax", card_yaml_ok,
                        f"cardTitle={card_has_title}, dueLabel={card_has_due}, "
                        f"substitution_syntax=%{{...}}={card_sub_syntax}, dueLabel_value='{due_val}'"))

    # ── 19. CardViewModel YAML in 'es' with substitution syntax ──────────────
    es_card = combined_yaml.get("es", {}).get("CardViewModel", {})
    es_due_val = es_card.get("dueLabel", "")
    es_card_sub = bool(re.search(r'%\{[^}]+\}', str(es_due_val)))
    checks.append(check("yaml_CardViewModel_es_with_substitution_syntax", es_card_sub,
                        f"es dueLabel='{es_due_val}'"))

    # ── 20. Multiple @Test methods (not just one) ─────────────────────────────
    test_method_count = len(re.findall(r'@Test\s+func\s+\w+', swift_text))
    multiple_tests = test_method_count >= 2
    checks.append(check("multiple_test_methods_present", multiple_tests,
                        f"Found {test_method_count} @Test methods"))

    # ── Final scoring ─────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 3)

    # Hard gates: must pass core structural + YAML correctness checks
    hard_gates = [
        "swift_test_file_exists",
        "file_in_localization_directory",
        "LocalizableTestCase_conformance",
        "locStore_init_correct",
        "expectFullViewModelTests_BoardViewModel",
        "expectFullViewModelTests_ColumnViewModel",
        "expectFullViewModelTests_CardViewModel",
        "yaml_has_en_locale",
        "yaml_has_es_locale",
        "yaml_CardViewModel_en_with_substitution_syntax",
    ]
    hard_passed = all(c["passed"] for c in checks if c["name"] in hard_gates)

    return {
        "passed": hard_passed and score >= 0.75,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = main(workspace)
    print(json.dumps(result, indent=2))