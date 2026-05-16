#!/usr/bin/env python3
"""
Evaluation script for NotebookLM Distiller task.
Checks:
1. Output file exists at correct path with correct name
2. YAML frontmatter is correct (all 7 required fields)
3. Mode is 'summary' (not qa/glossary)
4. Language is Chinese (--lang zh was used)
5. --writeback was triggered (NLM source add was called with correct title format)
6. The writeback title follows the exact format: "Distill Log: summary | <notebook_name> | <date>"
"""
import sys
import json
import re
import datetime
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    today = datetime.date.today().isoformat()

    # ── Check 1: Output file exists ──────────────────────────────────────────
    vault = workspace / "obsidian_vault"
    expected_filename = "Quantum Error Correction_Summary.md"
    expected_topic = "QuantumComputing"
    expected_path = vault / expected_topic / expected_filename

    # Also search broadly in case agent placed it elsewhere
    found_files = list(vault.rglob("*_Summary.md"))
    qec_files = [f for f in found_files if "Quantum Error Correction" in f.name or "quantum_error" in f.name.lower()]

    file_exists = expected_path.exists()
    detail_file = f"Expected: {expected_path}"
    if not file_exists and qec_files:
        # Accept if file exists in any subfolder of vault with correct name
        candidate = qec_files[0]
        if "Quantum Error Correction" in candidate.name and "Summary" in candidate.name:
            file_exists = True
            expected_path = candidate
            detail_file += f" | Found at: {candidate}"

    checks.append({
        "name": "output_file_exists_at_correct_path",
        "passed": file_exists,
        "detail": detail_file + (" | FOUND" if file_exists else " | NOT FOUND")
    })

    if not file_exists:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks + [
                {"name": "frontmatter_complete", "passed": False, "detail": "File not found, cannot check frontmatter"},
                {"name": "summary_mode_used", "passed": False, "detail": "File not found"},
                {"name": "chinese_language_output", "passed": False, "detail": "File not found"},
                {"name": "writeback_was_triggered", "passed": False, "detail": "File not found"},
                {"name": "writeback_title_format_correct", "passed": False, "detail": "File not found"},
            ]
        }

    # Read file content
    try:
        content = expected_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── Check 2: YAML frontmatter completeness ────────────────────────────────
    frontmatter_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    required_keys = ["title", "date", "type", "author", "tags", "source", "project", "status"]
    frontmatter_ok = False
    missing_keys = []
    if frontmatter_match:
        fm_text = frontmatter_match.group(1)
        present_keys = [k for k in required_keys if re.search(rf'^{k}\s*:', fm_text, re.MULTILINE)]
        missing_keys = [k for k in required_keys if k not in present_keys]
        frontmatter_ok = len(missing_keys) == 0
        # Check author is notebooklm-distiller
        author_ok = "notebooklm-distiller" in fm_text
        type_ok = "knowledge-note" in fm_text
        frontmatter_ok = frontmatter_ok and author_ok and type_ok
        detail_fm = f"Present: {present_keys}, Missing: {missing_keys}, author_ok={author_ok}, type_ok={type_ok}"
    else:
        detail_fm = "No YAML frontmatter block found"

    checks.append({
        "name": "frontmatter_complete_and_correct",
        "passed": frontmatter_ok,
        "detail": detail_fm
    })

    # ── Check 3: Summary mode (5 structured sections present) ────────────────
    # Per SKILL.md: Summary, Key Points, Constraints, Trade-offs, Open Questions
    # Check Chinese section headers too
    expected_sections_en = ["Summary", "Key Points", "Constraints", "Trade-offs", "Open Questions"]
    expected_sections_zh = ["摘要", "关键要点", "约束", "权衡", "开放问题"]

    en_count = sum(1 for s in expected_sections_en if s.lower() in content.lower())
    zh_count = sum(1 for s in expected_sections_zh if s in content)
    summary_mode_ok = (en_count >= 4) or (zh_count >= 3)

    # Also check filename ends with _Summary.md
    filename_ok = expected_path.name.endswith("_Summary.md")
    summary_mode_ok = summary_mode_ok and filename_ok

    checks.append({
        "name": "summary_mode_used_correctly",
        "passed": summary_mode_ok,
        "detail": f"EN sections found: {en_count}/5, ZH sections found: {zh_count}, filename_ok={filename_ok}"
    })

    # ── Check 4: Chinese language output ─────────────────────────────────────
    # Check that the distill call was made with --lang zh
    # Evidence: Chinese characters in the content body
    chinese_char_pattern = re.compile(r'[\u4e00-\u9fff]')
    chinese_chars_in_body = len(chinese_char_pattern.findall(content))
    chinese_ok = chinese_chars_in_body >= 20  # Meaningful Chinese text, not just stray chars

    # Also check distill_calls.jsonl for lang=zh
    distill_log = Path("/tmp/distill_calls.jsonl")
    lang_zh_in_log = False
    try:
        for line in distill_log.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if entry.get("subcommand") == "distill":
                    args_data = entry.get("args", {})
                    if args_data.get("lang") == "zh":
                        lang_zh_in_log = True
            except Exception:
                pass
    except Exception:
        pass

    chinese_ok = chinese_ok or lang_zh_in_log
    checks.append({
        "name": "chinese_language_mode_used",
        "passed": chinese_ok,
        "detail": f"Chinese chars in content: {chinese_chars_in_body}, lang=zh in call log: {lang_zh_in_log}"
    })

    # ── Check 5: --writeback was triggered ───────────────────────────────────
    # Check nlm_calls.jsonl for source_add invocation
    nlm_log = Path("/tmp/nlm_calls.jsonl")
    writeback_called = False
    writeback_title = None
    try:
        for line in nlm_log.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if entry.get("cmd") == "source_add":
                    writeback_called = True
                    writeback_title = entry.get("title")
            except Exception:
                pass
    except Exception:
        pass

    # Also check distill_calls.jsonl for writeback entries
    try:
        for line in distill_log.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if entry.get("subcommand") == "writeback":
                    writeback_called = True
                    writeback_title = writeback_title or entry.get("title")
            except Exception:
                pass
    except Exception:
        pass

    checks.append({
        "name": "writeback_flag_triggered",
        "passed": writeback_called,
        "detail": f"writeback_called={writeback_called}, title_found={writeback_title}"
    })

    # ── Check 6: Writeback title format correct ───────────────────────────────
    # Format: "Distill Log: summary | <notebook_name> | YYYY-MM-DD"
    # notebook_name should be "Quantum Error Correction"
    writeback_title_ok = False
    title_detail = f"title='{writeback_title}'"
    if writeback_title:
        # Regex: "Distill Log: summary | Quantum Error Correction | YYYY-MM-DD"
        title_pattern = re.compile(
            r'^Distill Log:\s*summary\s*\|\s*Quantum Error Correction\s*\|\s*\d{4}-\d{2}-\d{2}$',
            re.IGNORECASE
        )
        writeback_title_ok = bool(title_pattern.match(writeback_title.strip()))
        title_detail += f" | pattern_match={writeback_title_ok}"
    else:
        title_detail = "No writeback title found in logs"

    checks.append({
        "name": "writeback_title_format_correct",
        "passed": writeback_title_ok,
        "detail": title_detail
    })

    # ── Scoring ───────────────────────────────────────────────────────────────
    weights = {
        "output_file_exists_at_correct_path": 0.20,
        "frontmatter_complete_and_correct": 0.20,
        "summary_mode_used_correctly": 0.20,
        "chinese_language_mode_used": 0.15,
        "writeback_flag_triggered": 0.15,
        "writeback_title_format_correct": 0.10,
    }

    score = 0.0
    for check in checks:
        name = check["name"]
        if check["passed"] and name in weights:
            score += weights[name]

    all_passed = all(c["passed"] for c in checks)

    return {
        "passed": all_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [], "error": "No workspace path provided"}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))