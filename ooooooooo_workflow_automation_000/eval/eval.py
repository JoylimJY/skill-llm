import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str) -> dict:
    ws = Path(workspace)
    checks = []

    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # ── CHECK 1: Core source files exist ────────────────────────────────────
    required_files = [
        "src/validator/__init__.py",
        "src/validator/models.py",
        "src/validator/rules.py",
        "src/validator/fraud.py",
        "src/validator/engine.py",
    ]
    missing = [f for f in required_files if not (ws / f).exists()]
    add_check(
        "core_source_files_exist",
        len(missing) == 0,
        f"Missing: {missing}" if missing else "All core source files present"
    )

    # ── CHECK 2: Test files exist ────────────────────────────────────────────
    required_tests = [
        "tests/test_models.py",
        "tests/test_rules.py",
        "tests/test_fraud.py",
        "tests/test_engine.py",
        "tests/test_integration.py",
    ]
    missing_tests = [f for f in required_tests if not (ws / f).exists()]
    add_check(
        "test_files_exist",
        len(missing_tests) == 0,
        f"Missing tests: {missing_tests}" if missing_tests else "All test files present"
    )

    # ── CHECK 3: Transaction dataclass has required fields ──────────────────
    try:
        models_content = (ws / "src/validator/models.py").read_text()
        required_fields = ["transaction_id", "amount", "currency", "sender", "receiver", "timestamp"]
        found_fields = [f for f in required_fields if f in models_content]
        all_fields = len(found_fields) == len(required_fields)
        add_check(
            "transaction_dataclass_fields",
            all_fields,
            f"Found fields: {found_fields}, Missing: {[f for f in required_fields if f not in found_fields]}"
        )
    except Exception as e:
        add_check("transaction_dataclass_fields", False, f"Error reading models.py: {e}")

    # ── CHECK 4: validate_amount function exists with correct logic ─────────
    try:
        rules_content = (ws / "src/validator/rules.py").read_text()
        has_validate_amount = "validate_amount" in rules_content
        has_validate_currency = "validate_currency" in rules_content
        has_allowed_currencies = any(c in rules_content for c in ["USD", "EUR", "GBP"])
        add_check(
            "rules_py_content",
            has_validate_amount and has_validate_currency and has_allowed_currencies,
            f"validate_amount: {has_validate_amount}, validate_currency: {has_validate_currency}, currencies: {has_allowed_currencies}"
        )
    except Exception as e:
        add_check("rules_py_content", False, f"Error reading rules.py: {e}")

    # ── CHECK 5: fraud.py has is_suspicious ─────────────────────────────────
    try:
        fraud_content = (ws / "src/validator/fraud.py").read_text()
        has_suspicious = "is_suspicious" in fraud_content
        has_sender_receiver = "sender" in fraud_content and "receiver" in fraud_content
        add_check(
            "fraud_py_content",
            has_suspicious and has_sender_receiver,
            f"is_suspicious: {has_suspicious}, sender==receiver check: {has_sender_receiver}"
        )
    except Exception as e:
        add_check("fraud_py_content", False, f"Error reading fraud.py: {e}")

    # ── CHECK 6: engine.py has Validator class with validate method ──────────
    try:
        engine_content = (ws / "src/validator/engine.py").read_text()
        has_validator_class = "class Validator" in engine_content or "Validator" in engine_content
        has_validate_method = "def validate" in engine_content
        has_valid_key = "valid" in engine_content
        has_errors_key = "errors" in engine_content
        has_suspicious_key = "suspicious" in engine_content
        all_ok = has_validator_class and has_validate_method and has_valid_key and has_errors_key and has_suspicious_key
        add_check(
            "engine_py_validator_class",
            all_ok,
            f"class Validator: {has_validator_class}, validate method: {has_validate_method}, "
            f"returns 'valid': {has_valid_key}, 'errors': {has_errors_key}, 'suspicious': {has_suspicious_key}"
        )
    except Exception as e:
        add_check("engine_py_validator_class", False, f"Error reading engine.py: {e}")

    # ── CHECK 7: Checkpoint file(s) exist with correct template ─────────────
    # Agent must have produced checkpoint reports. Look for any .md or .txt file
    # containing the checkpoint template with ✅ and 📋 emojis.
    checkpoint_files = list(ws.rglob("checkpoint*.md")) + list(ws.rglob("checkpoint*.txt")) + \
                       list(ws.rglob("CHECKPOINT*.md")) + list(ws.rglob("CHECKPOINT*.txt")) + \
                       list(ws.rglob("progress*.md")) + list(ws.rglob("PROGRESS*.md"))

    # Also search all .md files for checkpoint template markers
    all_md_files = list(ws.rglob("*.md"))
    files_with_checkpoint_content = []
    for f in all_md_files:
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
            if "✅" in content and "📋" in content:
                files_with_checkpoint_content.append(f)
        except Exception:
            pass

    checkpoint_found = len(checkpoint_files) > 0 or len(files_with_checkpoint_content) > 0
    add_check(
        "checkpoint_files_exist",
        checkpoint_found,
        f"Checkpoint files: {[str(f) for f in checkpoint_files]}, "
        f"MD files with template: {[str(f) for f in files_with_checkpoint_content]}"
    )

    # ── CHECK 8: Checkpoint template format - ✅ and 📋 emojis ──────────────
    checkpoint_has_correct_format = False
    checkpoint_detail = "No checkpoint content found"
    all_potential_checkpoints = list(set(checkpoint_files + files_with_checkpoint_content))
    # Also check any .txt files
    all_txt = list(ws.rglob("*.txt"))
    for f in all_txt:
        try:
            c = f.read_text(encoding="utf-8", errors="replace")
            if "✅" in c and "📋" in c:
                all_potential_checkpoints.append(f)
        except Exception:
            pass

    for cp_file in all_potential_checkpoints:
        try:
            content = cp_file.read_text(encoding="utf-8", errors="replace")
            has_checkmark = "✅" in content
            has_clipboard = "📋" in content
            # Check for completed tasks section and next tasks section
            has_completed_section = "已完成" in content or "完成" in content or "completed" in content.lower() or "Completed" in content
            has_next_section = "下一批" in content or "Next" in content or "next" in content or "任务" in content
            if has_checkmark and has_clipboard and (has_completed_section or has_next_section):
                checkpoint_has_correct_format = True
                checkpoint_detail = f"Valid checkpoint template found in {cp_file.name}"
                break
        except Exception as e:
            continue

    if not checkpoint_has_correct_format and all_potential_checkpoints:
        checkpoint_detail = f"Files found but missing required template elements (✅/📋 emojis or section headers)"

    add_check(
        "checkpoint_template_format",
        checkpoint_has_correct_format,
        checkpoint_detail
    )

    # ── CHECK 9: Checkpoint interval (3-5 tasks) ─────────────────────────────
    # Count how many distinct checkpoint reports exist
    checkpoint_count = 0
    all_report_files = []
    for pattern in ["*.md", "*.txt"]:
        for f in ws.rglob(pattern):
            if f.is_file() and not any(skip in str(f) for skip in ["legacy", "reports/202", "docs/", "infra/", "config/"]):
                try:
                    content = f.read_text(encoding="utf-8", errors="replace")
                    if "✅" in content:
                        checkpoint_count_in_file = content.count("✅ 已完成") + content.count("✅ Completed") + content.count("✅")
                        if checkpoint_count_in_file > 0:
                            all_report_files.append(f)
                except Exception:
                    pass

    # With 7 tasks, agent should have at least 1 checkpoint (at tasks 3-5) and possibly 2
    # We'll accept >= 1 checkpoint as valid since the spec says "every 3-5 tasks"
    has_reasonable_checkpoints = len(all_report_files) >= 1 or checkpoint_has_correct_format
    add_check(
        "checkpoint_interval_reasonable",
        has_reasonable_checkpoints,
        f"Found {len(all_report_files)} files with checkpoint markers. "
        f"Expected at least 1 checkpoint for 7 tasks (interval: 3-5 tasks)"
    )

    # ── CHECK 10: Finishing branch artifact (core-finishing-branch) ──────────
    # Agent must create a BRANCH_SUMMARY.md or similar finishing artifact
    # Look for any file indicating branch finishing/completion summary
    finishing_patterns = [
        "BRANCH_SUMMARY*", "branch_summary*",
        "FINISHING*", "finishing*",
        "COMPLETION_SUMMARY*", "completion_summary*",
        "FINAL_SUMMARY*", "final_summary*",
        "DONE*",
    ]
    finishing_files = []
    for pattern in finishing_patterns:
        finishing_files.extend(ws.rglob(pattern))

    # Also look for any file with finishing branch keywords
    finishing_keyword_files = []
    for f in ws.rglob("*.md"):
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
            if any(kw in content for kw in ["core-finishing-branch", "finishing-branch", "finishing branch",
                                              "branch summary", "Branch Summary", "BRANCH_SUMMARY",
                                              "所有任务完成", "全部完成", "完整测试套件"]):
                finishing_keyword_files.append(f)
        except Exception:
            pass

    has_finishing = len(finishing_files) > 0 or len(finishing_keyword_files) > 0
    add_check(
        "finishing_branch_artifact",
        has_finishing,
        f"Finishing files: {[str(f.name) for f in finishing_files]}, "
        f"Files with finishing keywords: {[str(f.name) for f in finishing_keyword_files]}"
    )

    # ── CHECK 11: Test content quality - at least 3 test cases for amount ───
    try:
        test_rules_content = (ws / "tests/test_rules.py").read_text()
        # Count test functions
        test_funcs = re.findall(r'def test_\w+', test_rules_content)
        has_enough_tests = len(test_funcs) >= 3
        add_check(
            "test_rules_minimum_coverage",
            has_enough_tests,
            f"Found {len(test_funcs)} test functions in test_rules.py (need >= 3)"
        )
    except Exception as e:
        add_check("test_rules_minimum_coverage", False, f"Error reading test_rules.py: {e}")

    # ── CHECK 12: Test files written (TDD order indication) ──────────────────
    # TDD means test files should reference the implementation before or alongside.
    # We verify test files import from src/validator
    tdd_ok = True
    tdd_details = []
    for tf in ["tests/test_models.py", "tests/test_rules.py", "tests/test_fraud.py", "tests/test_engine.py"]:
        try:
            content = (ws / tf).read_text()
            imports_validator = "validator" in content or "src" in content or "from " in content or "import " in content
            if not imports_validator:
                tdd_ok = False
                tdd_details.append(f"{tf}: no imports found")
        except Exception as e:
            tdd_ok = False
            tdd_details.append(f"{tf}: {e}")

    add_check(
        "tdd_test_files_import_implementation",
        tdd_ok,
        "All test files import from validator" if tdd_ok else f"Issues: {tdd_details}"
    )

    # ── CHECK 13: Integration test has multiple transactions ─────────────────
    try:
        integ_content = (ws / "tests/test_integration.py").read_text()
        # Look for at least 2 valid and 2 invalid transactions being tested
        test_funcs = re.findall(r'def test_\w+', integ_content)
        # Check for Validator usage
        uses_validator = "Validator" in integ_content or "validator" in integ_content.lower()
        has_multiple_tests = len(test_funcs) >= 2
        add_check(
            "integration_test_quality",
            uses_validator and has_multiple_tests,
            f"Uses Validator: {uses_validator}, test functions: {len(test_funcs)} (need >= 2)"
        )
    except Exception as e:
        add_check("integration_test_quality", False, f"Error reading test_integration.py: {e}")

    # ── Scoring ──────────────────────────────────────────────────────────────
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks

    # Overall pass: must pass core implementation + checkpoint + finishing branch
    critical_checks = [
        "core_source_files_exist",
        "test_files_exist",
        "rules_py_content",
        "engine_py_validator_class",
        "checkpoint_template_format",
        "finishing_branch_artifact",
    ]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)

    overall_passed = critical_passed and score >= 0.75

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))