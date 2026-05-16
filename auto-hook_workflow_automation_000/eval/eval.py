import sys
import os
import json
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    
    workspace = Path(workspace)
    
    # ── Load reference files ────────────────────────────────────────────────
    hook_txt_path = workspace / "mnt/user-data/uploads/skill-audit-hook.txt"
    skill_a_orig_path = workspace / ".agents/skills/data-normalizer/SKILL.md"
    skill_b_orig_path = workspace / ".agents/skills/report-builder/SKILL.md"
    
    try:
        hook_content = hook_txt_path.read_text(encoding="utf-8")
    except Exception as e:
        hook_content = ""
    
    try:
        skill_b_orig = skill_b_orig_path.read_text(encoding="utf-8")
    except Exception as e:
        skill_b_orig = ""

    # ════════════════════════════════════════════════════════════════════════
    # CHECK GROUP 1: Injection output — data-normalizer-SKILL.md
    # Expected: in home/claude/ or outputs/
    # ════════════════════════════════════════════════════════════════════════

    # Search for the injected file
    injected_file = None
    candidates = list(workspace.rglob("data-normalizer-SKILL.md"))
    if candidates:
        # Prefer outputs dir, then home/claude
        for c in candidates:
            if "outputs" in str(c) or "home" in str(c):
                injected_file = c
                break
        if injected_file is None:
            injected_file = candidates[0]

    # CHECK 1.1: Injected file exists
    check_1_1 = {"name": "injection_output_file_exists", "passed": False, "detail": ""}
    if injected_file and injected_file.exists():
        check_1_1["passed"] = True
        check_1_1["detail"] = f"Found injected file at {injected_file}"
    else:
        check_1_1["detail"] = "data-normalizer-SKILL.md not found in workspace"
    checks.append(check_1_1)

    # CHECK 1.2: Original skill content preserved
    check_1_2 = {"name": "injection_original_content_preserved", "passed": False, "detail": ""}
    try:
        if injected_file and injected_file.exists():
            injected_content = injected_file.read_text(encoding="utf-8")
            orig_content = skill_a_orig_path.read_text(encoding="utf-8")
            # The original content should be a prefix of the injected file
            if injected_content.startswith(orig_content.rstrip()):
                check_1_2["passed"] = True
                check_1_2["detail"] = "Original skill content is preserved at the start of injected file"
            else:
                # More lenient: check that key sections exist
                key_phrases = ["data-normalizer", "Schema Detection", "Null Handling", "Column Renaming"]
                if all(kp in injected_content for kp in key_phrases):
                    check_1_2["passed"] = True
                    check_1_2["detail"] = "Original skill key content sections found in injected file"
                else:
                    check_1_2["detail"] = f"Original content not preserved. Missing key sections."
    except Exception as e:
        check_1_2["detail"] = f"Error reading injected file: {e}"
    checks.append(check_1_2)

    # CHECK 1.3: Hook content from skill-audit-hook.txt is appended (verbatim match)
    check_1_3 = {"name": "injection_hook_content_from_hook_txt", "passed": False, "detail": ""}
    try:
        if injected_file and injected_file.exists():
            injected_content = injected_file.read_text(encoding="utf-8")
            # The hook content must be present — check key hook markers
            hook_markers = [
                "强制自审计",
                "debug.txt",
                "Step 1 · 读取钩子文件",
                "⏭️",
                "❌"
            ]
            markers_found = [m for m in hook_markers if m in injected_content]
            if len(markers_found) >= 4:
                check_1_3["passed"] = True
                check_1_3["detail"] = f"Hook content present with markers: {markers_found}"
            else:
                check_1_3["detail"] = f"Hook content incomplete. Found markers: {markers_found}, missing: {[m for m in hook_markers if m not in markers_found]}"
    except Exception as e:
        check_1_3["detail"] = f"Error: {e}"
    checks.append(check_1_3)

    # CHECK 1.4: Hook is appended AFTER original content (not replacing it)
    check_1_4 = {"name": "injection_hook_appended_not_replacing", "passed": False, "detail": ""}
    try:
        if injected_file and injected_file.exists():
            injected_content = injected_file.read_text(encoding="utf-8")
            # "data-normalizer" original section AND hook content both present
            has_original = "Schema Detection" in injected_content and "Null Handling" in injected_content
            has_hook = "强制自审计" in injected_content
            if has_original and has_hook:
                # Original comes before hook
                orig_pos = injected_content.find("Schema Detection")
                hook_pos = injected_content.find("强制自审计")
                if orig_pos < hook_pos:
                    check_1_4["passed"] = True
                    check_1_4["detail"] = f"Hook correctly appended after original content (orig@{orig_pos}, hook@{hook_pos})"
                else:
                    check_1_4["detail"] = f"Hook appears before original content (orig@{orig_pos}, hook@{hook_pos})"
            else:
                check_1_4["detail"] = f"Missing original ({has_original}) or hook ({has_hook})"
    except Exception as e:
        check_1_4["detail"] = f"Error: {e}"
    checks.append(check_1_4)

    # CHECK 1.5: No duplicate hook injection (autohook appears only once)
    check_1_5 = {"name": "injection_no_duplicate_hook", "passed": False, "detail": ""}
    try:
        if injected_file and injected_file.exists():
            injected_content = injected_file.read_text(encoding="utf-8")
            count = injected_content.count("强制自审计")
            if count == 1:
                check_1_5["passed"] = True
                check_1_5["detail"] = "Hook injected exactly once"
            else:
                check_1_5["detail"] = f"Hook injected {count} times (expected 1)"
    except Exception as e:
        check_1_5["detail"] = f"Error: {e}"
    checks.append(check_1_5)

    # ════════════════════════════════════════════════════════════════════════
    # CHECK GROUP 2: Revocation output — report-builder-SKILL-clean.md
    # ════════════════════════════════════════════════════════════════════════

    clean_file = None
    clean_candidates = list(workspace.rglob("report-builder-SKILL-clean.md"))
    if clean_candidates:
        for c in clean_candidates:
            if "outputs" in str(c) or "home" in str(c):
                clean_file = c
                break
        if clean_file is None:
            clean_file = clean_candidates[0]

    # CHECK 2.1: Clean file exists
    check_2_1 = {"name": "revocation_output_file_exists", "passed": False, "detail": ""}
    if clean_file and clean_file.exists():
        check_2_1["passed"] = True
        check_2_1["detail"] = f"Found clean file at {clean_file}"
    else:
        check_2_1["detail"] = "report-builder-SKILL-clean.md not found in workspace"
    checks.append(check_2_1)

    # CHECK 2.2: Hook content fully removed
    check_2_2 = {"name": "revocation_hook_fully_removed", "passed": False, "detail": ""}
    try:
        if clean_file and clean_file.exists():
            clean_content = clean_file.read_text(encoding="utf-8")
            hook_residue = ["强制自审计", "debug.txt", "自审计钩子", "autohook"]
            residues = [r for r in hook_residue if r in clean_content]
            if not residues:
                check_2_2["passed"] = True
                check_2_2["detail"] = "All hook markers removed from clean file"
            else:
                check_2_2["detail"] = f"Hook residues still present: {residues}"
    except Exception as e:
        check_2_2["detail"] = f"Error: {e}"
    checks.append(check_2_2)

    # CHECK 2.3: Original report-builder content preserved (core sections)
    check_2_3 = {"name": "revocation_original_content_preserved", "passed": False, "detail": ""}
    try:
        if clean_file and clean_file.exists():
            clean_content = clean_file.read_text(encoding="utf-8")
            key_orig = ["report-builder", "Load Template", "Render Charts", "Localisation", "WeasyPrint"]
            found = [k for k in key_orig if k in clean_content]
            if len(found) >= 4:
                check_2_3["passed"] = True
                check_2_3["detail"] = f"Original content preserved: {found}"
            else:
                check_2_3["detail"] = f"Original content partially missing. Found: {found}"
    except Exception as e:
        check_2_3["detail"] = f"Error: {e}"
    checks.append(check_2_3)

    # CHECK 2.4: The --- separator before the hook section is also removed
    check_2_4 = {"name": "revocation_separator_removed", "passed": False, "detail": ""}
    try:
        if clean_file and clean_file.exists():
            clean_content = clean_file.read_text(encoding="utf-8")
            # The hook section in report-builder ends with a trailing ---\n\n## ⚙️ 强制自审计
            # After removal, the file should end after "render_errors.log" content
            # Check: no standalone trailing --- that was the hook separator
            # The original skill body ends with "render_errors.log`." — verify that's near end
            # We check: the last occurrence of '---' should NOT be near the very end as a naked separator
            lines = clean_content.splitlines()
            # Last few lines should not be just '---' 
            trailing_lines = [l.strip() for l in lines[-5:] if l.strip()]
            if trailing_lines and trailing_lines[-1] == "---":
                check_2_4["detail"] = f"File ends with bare '---' separator (hook separator not fully removed). Trailing: {trailing_lines}"
            else:
                check_2_4["passed"] = True
                check_2_4["detail"] = f"No bare trailing '---' separator. Trailing content: {trailing_lines}"
    except Exception as e:
        check_2_4["detail"] = f"Error: {e}"
    checks.append(check_2_4)

    # CHECK 2.5: File ends with exactly one trailing newline (no excessive blank lines)
    check_2_5 = {"name": "revocation_clean_trailing_newline", "passed": False, "detail": ""}
    try:
        if clean_file and clean_file.exists():
            raw = clean_file.read_bytes()
            raw_text = raw.decode("utf-8")
            # Should end with \n but not \n\n\n
            if raw_text.endswith("\n"):
                trailing_newlines = len(raw_text) - len(raw_text.rstrip("\n"))
                if trailing_newlines <= 2:
                    check_2_5["passed"] = True
                    check_2_5["detail"] = f"File ends cleanly with {trailing_newlines} trailing newline(s)"
                else:
                    check_2_5["detail"] = f"Too many trailing newlines: {trailing_newlines}"
            else:
                check_2_5["detail"] = "File does not end with a newline character"
    except Exception as e:
        check_2_5["detail"] = f"Error: {e}"
    checks.append(check_2_5)

    # ════════════════════════════════════════════════════════════════════════
    # SCORING
    # ════════════════════════════════════════════════════════════════════════
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    overall_passed = passed_count >= 8  # At least 8 of 10 checks must pass

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))