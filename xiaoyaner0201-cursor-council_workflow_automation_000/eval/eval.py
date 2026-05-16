import sys
import json
import os
import re
from pathlib import Path
from datetime import datetime

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    # ─── Helper ───────────────────────────────────────────────────────────────
    def add_check(name: str, passed: bool, detail: str):
        checks.append({"name": name, "passed": passed, "detail": detail})
    
    # ─── 1. Find the council archive directory ────────────────────────────────
    # Must be at ~/.openclaw/workspace/pr-review/council-YYYY-MM-DD[-topic]/
    # Also check workspace-relative paths since home may be /root
    search_bases = [
        Path.home() / ".openclaw" / "workspace" / "pr-review",
        workspace / ".openclaw" / "workspace" / "pr-review",
        Path("/root/.openclaw/workspace/pr-review"),
    ]
    
    council_dirs = []
    for base in search_bases:
        if base.exists():
            for d in base.iterdir():
                if d.is_dir() and d.name.startswith("council-"):
                    council_dirs.append(d)
    
    # Deduplicate by resolved path
    seen = set()
    unique_council_dirs = []
    for d in council_dirs:
        resolved = str(d.resolve())
        if resolved not in seen:
            seen.add(resolved)
            unique_council_dirs.append(d)
    council_dirs = unique_council_dirs
    
    if not council_dirs:
        add_check(
            "council_archive_directory_exists",
            False,
            "No council-* directory found under ~/.openclaw/workspace/pr-review/. "
            "Expected path: ~/.openclaw/workspace/pr-review/council-YYYY-MM-DD[-topic]/"
        )
        return {"passed": False, "score": 0.0, "checks": checks}
    
    # Use the most recently modified council dir
    council_dir = max(council_dirs, key=lambda d: d.stat().st_mtime)
    
    # Validate directory name format: council-YYYY-MM-DD or council-YYYY-MM-DD-topic
    dir_name = council_dir.name
    name_pattern = re.compile(r'^council-\d{4}-\d{2}-\d{2}(-\S+)?$')
    name_valid = bool(name_pattern.match(dir_name))
    add_check(
        "council_archive_directory_naming",
        name_valid,
        f"Directory name '{dir_name}' {'matches' if name_valid else 'does NOT match'} "
        f"required pattern 'council-YYYY-MM-DD[-topic]'"
    )
    
    # ─── 2. Check all 6 required files exist ─────────────────────────────────
    required_files = [
        "council-opus-prompt.txt",
        "council-opus-output.txt",
        "council-sonnet-prompt.txt",
        "council-sonnet-output.txt",
        "council-gpt-prompt.txt",
        "council-gpt-output.txt",
    ]
    
    all_required_exist = True
    missing_files = []
    for fname in required_files:
        fpath = council_dir / fname
        if not fpath.exists():
            missing_files.append(fname)
            all_required_exist = False
    
    add_check(
        "all_six_required_files_exist",
        all_required_exist,
        f"All 6 required council files present" if all_required_exist
        else f"Missing files: {missing_files}"
    )
    
    # ─── 3. Check README.md exists ────────────────────────────────────────────
    readme_path = council_dir / "README.md"
    readme_exists = readme_path.exists()
    add_check(
        "readme_md_exists",
        readme_exists,
        f"README.md {'found' if readme_exists else 'NOT found'} in {council_dir}"
    )
    
    # ─── 4. Check prompt files reference correct model identifiers ────────────
    # The SKILL.md specifies exact model strings: claude-opus-4-6, claude-sonnet-4-5, gpt-5.2
    correct_models = {
        "council-opus-prompt.txt": "claude-opus-4-6",
        "council-sonnet-prompt.txt": "claude-sonnet-4-5",
        "council-gpt-prompt.txt": "gpt-5.2",
    }
    
    # Also check the output files or any shell scripts in the workspace
    # We check: do the prompts show persona-based framing?
    model_checks_passed = 0
    for prompt_file, expected_model in correct_models.items():
        fpath = council_dir / prompt_file
        try:
            content = fpath.read_text(errors='replace') if fpath.exists() else ""
            # The prompt files should contain persona/role framing
            has_content = len(content.strip()) > 20
            add_check(
                f"prompt_file_{prompt_file.replace('.txt','')}_has_content",
                has_content,
                f"{'Non-empty' if has_content else 'EMPTY'} prompt file: {prompt_file} ({len(content)} chars)"
            )
            if has_content:
                model_checks_passed += 1
        except Exception as e:
            add_check(
                f"prompt_file_{prompt_file.replace('.txt','')}_has_content",
                False,
                f"Error reading {prompt_file}: {e}"
            )
    
    # ─── 5. Check output files contain meaningful content ─────────────────────
    output_files_with_content = 0
    for output_file in ["council-opus-output.txt", "council-sonnet-output.txt", "council-gpt-output.txt"]:
        fpath = council_dir / output_file
        try:
            content = fpath.read_text(errors='replace') if fpath.exists() else ""
            has_content = len(content.strip()) > 20
            add_check(
                f"output_file_{output_file.replace('.txt','')}_has_content",
                has_content,
                f"{'Non-empty' if has_content else 'EMPTY'} output file: {output_file} ({len(content)} chars)"
            )
            if has_content:
                output_files_with_content += 1
        except Exception as e:
            add_check(
                f"output_file_{output_file.replace('.txt','')}_has_content",
                False,
                f"Error reading {output_file}: {e}"
            )
    
    # ─── 6. Check README structure follows the template ───────────────────────
    if readme_exists:
        try:
            readme_content = readme_path.read_text(errors='replace')
            
            # Must have Council Members table with required columns
            has_council_members_section = bool(
                re.search(r'council\s*成员|council\s*members|Council\s*成员|Council\s*Members', 
                          readme_content, re.IGNORECASE)
            )
            add_check(
                "readme_has_council_members_section",
                has_council_members_section,
                f"README {'has' if has_council_members_section else 'MISSING'} Council Members section"
            )
            
            # Must have all three roles mentioned (架构师/Architect, 工程师/Engineer/Pragmatist, 批判者/Challenger)
            has_opus_role = bool(re.search(r'opus|架构师|architect', readme_content, re.IGNORECASE))
            has_sonnet_role = bool(re.search(r'sonnet|工程师|engineer|pragmatist', readme_content, re.IGNORECASE))
            has_gpt_role = bool(re.search(r'gpt|批判者|challenger|critic', readme_content, re.IGNORECASE))
            
            all_three_roles = has_opus_role and has_sonnet_role and has_gpt_role
            add_check(
                "readme_mentions_all_three_council_roles",
                all_three_roles,
                f"Roles found - Opus/Architect: {has_opus_role}, Sonnet/Engineer: {has_sonnet_role}, "
                f"GPT/Challenger: {has_gpt_role}"
            )
            
            # Must have file manifest / 文件清单
            has_file_manifest = bool(
                re.search(r'文件清单|file\s*(?:list|manifest|清单)', readme_content, re.IGNORECASE)
            )
            add_check(
                "readme_has_file_manifest",
                has_file_manifest,
                f"README {'has' if has_file_manifest else 'MISSING'} file manifest section (文件清单)"
            )
            
            # Must have conclusion/recommendation section
            has_conclusion = bool(
                re.search(r'结论|conclusion|recommendation|最终建议|synthesized', readme_content, re.IGNORECASE)
            )
            add_check(
                "readme_has_conclusion_section",
                has_conclusion,
                f"README {'has' if has_conclusion else 'MISSING'} conclusion/recommendation section"
            )
            
            # Must reference the actual 6 required .txt files
            txt_files_referenced = sum(
                1 for fname in required_files 
                if fname in readme_content
            )
            files_referenced_ok = txt_files_referenced >= 4  # at least 4 of 6
            add_check(
                "readme_references_council_txt_files",
                files_referenced_ok,
                f"README references {txt_files_referenced}/6 required .txt files "
                f"({'OK' if files_referenced_ok else 'INSUFFICIENT'})"
            )
            
            # Check for consensus matrix (共识矩阵)
            has_consensus = bool(
                re.search(r'共识矩阵|consensus|agreement|一致同意', readme_content, re.IGNORECASE)
            )
            add_check(
                "readme_has_consensus_matrix_or_section",
                has_consensus,
                f"README {'has' if has_consensus else 'MISSING'} consensus matrix/section"
            )
            
        except Exception as e:
            add_check("readme_structure_analysis", False, f"Error analyzing README: {e}")
    
    # ─── 7. Verify model names in prompts reference SKILL.md exact identifiers ─
    # Check if any script/file in the archive references the correct model identifiers
    all_archive_text = ""
    for fpath in council_dir.rglob("*"):
        if fpath.is_file():
            try:
                all_archive_text += fpath.read_text(errors='replace') + "\n"
            except Exception:
                pass
    
    # Also check workspace-level scripts
    for fpath in workspace.rglob("*.sh"):
        try:
            all_archive_text += fpath.read_text(errors='replace') + "\n"
        except Exception:
            pass
    
    has_opus_model_id = "claude-opus-4-6" in all_archive_text
    has_sonnet_model_id = "claude-sonnet-4-5" in all_archive_text
    has_gpt_model_id = "gpt-5.2" in all_archive_text
    
    all_model_ids_correct = has_opus_model_id and has_sonnet_model_id and has_gpt_model_id
    add_check(
        "correct_proprietary_model_identifiers_used",
        all_model_ids_correct,
        f"Exact model IDs found - claude-opus-4-6: {has_opus_model_id}, "
        f"claude-sonnet-4-5: {has_sonnet_model_id}, gpt-5.2: {has_gpt_model_id}. "
        f"(Wrong: claude-3-opus, claude-3-sonnet, gpt-4, etc. would fail)"
    )
    
    # ─── 8. Check persona-based prompts (not generic questions) ───────────────
    # At least one prompt file should show persona engineering
    persona_keywords = [
        r'you are', r'你是', r'as a', r'your philosophy', r'your core belief',
        r'核心信仰', r'哲学', r'martin fowler', r'martin kleppmann', r'joe armstrong',
        r'linus', r'uncle bob', r'rich hickey', r'leslie lamport', r'tj holowaychuk',
        r'ryan dahl', r'sindre', r'simon peyton', r'前辈', r'architect', r'pragmatist',
        r'challenger', r'senior'
    ]
    
    persona_count = 0
    for prompt_file in ["council-opus-prompt.txt", "council-sonnet-prompt.txt", "council-gpt-prompt.txt"]:
        fpath = council_dir / prompt_file
        if fpath.exists():
            try:
                content = fpath.read_text(errors='replace').lower()
                has_persona = any(re.search(kw, content) for kw in persona_keywords)
                if has_persona:
                    persona_count += 1
            except Exception:
                pass
    
    persona_check_passed = persona_count >= 2
    add_check(
        "prompt_files_use_persona_engineering",
        persona_check_passed,
        f"{persona_count}/3 prompt files use persona/role-based framing. "
        f"Need at least 2 to pass. "
        f"(Prompts should assign a specific advisor persona per the SKILL.md)"
    )
    
    # ─── 9. Check the database decision question is included in context ────────
    db_keywords = ['postgresql', 'mongodb', 'cassandra', 'database', 'storage', 'db', 
                   '数据库', 'postgres', 'ledger', 'transaction']
    
    council_content_combined = ""
    for fpath in council_dir.glob("*.txt"):
        try:
            council_content_combined += fpath.read_text(errors='replace').lower()
        except Exception:
            pass
    
    has_db_context = any(kw in council_content_combined for kw in db_keywords)
    add_check(
        "council_session_addresses_database_decision",
        has_db_context,
        f"Council session files {'reference' if has_db_context else 'do NOT reference'} "
        f"the database/storage selection problem"
    )
    
    # ─── 10. Archive path correctness ─────────────────────────────────────────
    correct_base_paths = [
        str(Path.home() / ".openclaw" / "workspace" / "pr-review"),
        "/root/.openclaw/workspace/pr-review",
    ]
    archive_path_correct = any(
        str(council_dir).startswith(base) for base in correct_base_paths
    )
    add_check(
        "archive_at_correct_openclaw_path",
        archive_path_correct,
        f"Council dir at: {council_dir}. "
        f"Expected under: ~/.openclaw/workspace/pr-review/. "
        f"{'CORRECT' if archive_path_correct else 'WRONG PATH'}"
    )
    
    # ─── Compute final score ──────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3) if total > 0 else 0.0
    
    # Hard requirements: archive exists, all 6 files exist, README exists, correct model IDs
    hard_checks = [
        "council_archive_directory_exists",
        "all_six_required_files_exist",
        "readme_md_exists",
        "correct_proprietary_model_identifiers_used",
    ]
    hard_passed = all(
        any(c["name"] == hc and c["passed"] for c in checks)
        for hc in hard_checks
    )
    
    overall_passed = hard_passed and score >= 0.65
    
    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))