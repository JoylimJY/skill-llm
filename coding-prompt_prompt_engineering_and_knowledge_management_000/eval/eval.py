import sys
import os
import json
import hashlib
import re
from pathlib import Path

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()

def load_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def run_eval(workspace: str):
    checks = []
    
    # ─────────────────────────────────────────────────────────────────────
    # SECTION A: Optimization output file check
    # Agent must produce a file named 'optimized_prompt.md' somewhere in workspace
    # ─────────────────────────────────────────────────────────────────────
    
    opt_files = list(Path(workspace).rglob("optimized_prompt.md"))
    
    # A1: File exists
    checks.append({
        "name": "A1_optimized_prompt_file_exists",
        "passed": len(opt_files) > 0,
        "detail": f"Found {len(opt_files)} file(s) named optimized_prompt.md" if opt_files else "No file named optimized_prompt.md found in workspace"
    })
    
    opt_content = ""
    if opt_files:
        try:
            opt_content = load_text(str(opt_files[0]))
        except Exception as e:
            checks.append({
                "name": "A1_read_error",
                "passed": False,
                "detail": f"Could not read optimized_prompt.md: {e}"
            })

    # A2: Contains required three-section structure (exact Chinese headers)
    has_original_header = "## 原始提示词" in opt_content
    has_diagnosis_header = "## 诊断结果" in opt_content
    has_optimized_header = "## 优化后的提示词" in opt_content
    
    checks.append({
        "name": "A2_three_section_structure",
        "passed": has_original_header and has_diagnosis_header and has_optimized_header,
        "detail": (
            f"原始提示词: {has_original_header}, "
            f"诊断结果: {has_diagnosis_header}, "
            f"优化后的提示词: {has_optimized_header}"
        )
    })

    # A3: Diagnosis section contains D-code labels (proprietary checklist codes D1-D13)
    # Must have at least 2 D-codes in the diagnosis section
    d_code_pattern = re.compile(r'\bD\d{1,2}\b')
    
    # Extract the diagnosis section
    diag_section = ""
    if has_diagnosis_header and has_optimized_header:
        try:
            start = opt_content.index("## 诊断结果")
            end = opt_content.index("## 优化后的提示词")
            diag_section = opt_content[start:end]
        except ValueError:
            pass
    
    d_codes_found = d_code_pattern.findall(diag_section)
    unique_d_codes = set(d_codes_found)
    
    checks.append({
        "name": "A3_diagnosis_uses_proprietary_d_codes",
        "passed": len(unique_d_codes) >= 2,
        "detail": f"Found D-codes in diagnosis section: {sorted(unique_d_codes)} (need >= 2 unique codes)"
    })

    # A4: Original prompt is reproduced in the 原始提示词 section
    original_keywords = ["transaction", "risk scoring", "fraud", "scorer", "score"]
    orig_section = ""
    if has_original_header and has_diagnosis_header:
        try:
            start = opt_content.index("## 原始提示词")
            end = opt_content.index("## 诊断结果")
            orig_section = opt_content[start:end].lower()
        except ValueError:
            pass
    
    orig_keywords_found = sum(1 for kw in original_keywords if kw.lower() in orig_section)
    checks.append({
        "name": "A4_original_prompt_reproduced",
        "passed": orig_keywords_found >= 3,
        "detail": f"Found {orig_keywords_found}/5 original prompt keywords in 原始提示词 section"
    })

    # A5: Optimized prompt is substantially improved (has concrete content, not a stub)
    opt_section = ""
    if has_optimized_header:
        try:
            start = opt_content.index("## 优化后的提示词")
            opt_section = opt_content[start:]
        except ValueError:
            pass
    
    # Must have meaningful constraints/acceptance criteria — check for at least 50 words
    opt_word_count = len(opt_section.split())
    # Must contain at least some specificity markers
    specificity_markers = [
        "constraint", "约束", "acceptance", "验收", "example", "示例", "python", "must not", 
        "不能", "error", "错误", "test", "测试", "done when", "完成条件", "do not", "禁止"
    ]
    specificity_found = sum(1 for m in specificity_markers if m.lower() in opt_section.lower())
    
    checks.append({
        "name": "A5_optimized_prompt_is_substantive",
        "passed": opt_word_count >= 40 and specificity_found >= 2,
        "detail": f"Optimized section word count: {opt_word_count} (need >=40), specificity markers: {specificity_found} (need >=2)"
    })

    # ─────────────────────────────────────────────────────────────────────
    # SECTION B: Read-only file integrity check
    # None of the read-only reference files should be modified
    # ─────────────────────────────────────────────────────────────────────
    
    manifest_path = os.path.join(workspace, ".readonly_manifest.sha256")
    readonly_ok = True
    readonly_detail = []
    
    if not os.path.exists(manifest_path):
        checks.append({
            "name": "B1_readonly_files_untouched",
            "passed": False,
            "detail": "Manifest file missing — cannot verify read-only files."
        })
    else:
        try:
            with open(manifest_path, "r") as mf:
                for line in mf:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(None, 1)
                    if len(parts) != 2:
                        continue
                    expected_hash, filepath = parts
                    if not os.path.exists(filepath):
                        readonly_ok = False
                        readonly_detail.append(f"MISSING: {filepath}")
                        continue
                    actual_hash = sha256_file(filepath)
                    if actual_hash != expected_hash:
                        readonly_ok = False
                        readonly_detail.append(f"MODIFIED: {filepath}")
            
            checks.append({
                "name": "B1_readonly_files_untouched",
                "passed": readonly_ok,
                "detail": "All read-only files intact." if readonly_ok else f"Violations: {'; '.join(readonly_detail)}"
            })
        except Exception as e:
            checks.append({
                "name": "B1_readonly_files_untouched",
                "passed": False,
                "detail": f"Error checking manifest: {e}"
            })

    # ─────────────────────────────────────────────────────────────────────
    # SECTION C: learnings.md was updated with both required entries
    # ─────────────────────────────────────────────────────────────────────
    
    learnings_path = os.path.join(workspace, "references", "learnings.md")
    original_learnings_path = os.path.join(workspace, ".learnings_original.md")
    
    learnings_content = ""
    original_learnings_content = ""
    
    try:
        learnings_content = load_text(learnings_path)
    except Exception as e:
        checks.append({
            "name": "C0_learnings_readable",
            "passed": False,
            "detail": f"Cannot read references/learnings.md: {e}"
        })
    
    try:
        original_learnings_content = load_text(original_learnings_path)
    except Exception as e:
        pass
    
    # C1: learnings.md was actually modified (new content added)
    learnings_changed = learnings_content != original_learnings_content
    checks.append({
        "name": "C1_learnings_was_updated",
        "passed": learnings_changed,
        "detail": "learnings.md content differs from original." if learnings_changed else "learnings.md is identical to its original — no updates made."
    })

    # C2: New entry about semantic/LLM-native reasoning for classification tasks
    # (The pattern about "use semantic reasoning, not regex" for scoring/classification)
    semantic_pattern_keywords = [
        "semantic", "语义", "llm", "lm", "原生", "native", 
        "hardcod", "硬编码", "regex", "正则", "classif", "分类", "scor", "评分"
    ]
    semantic_hits = sum(1 for kw in semantic_pattern_keywords 
                        if kw.lower() in learnings_content.lower())
    
    # Must appear in NEW content (not just the original)
    original_semantic_hits = sum(1 for kw in semantic_pattern_keywords 
                                  if kw.lower() in original_learnings_content.lower())
    
    new_semantic_content = semantic_hits > original_semantic_hits
    checks.append({
        "name": "C2_semantic_reasoning_pattern_recorded",
        "passed": new_semantic_content and semantic_hits >= 2,
        "detail": (
            f"Semantic/LLM-native classification pattern in learnings: "
            f"found {semantic_hits} keywords (original had {original_semantic_hits}). "
            f"Net new content: {new_semantic_content}"
        )
    })

    # C3: New entry about no-stub / no-TODO / no-placeholder constraint
    stub_keywords = [
        "stub", "todo", "placeholder", "占位", "假完成", "fake", 
        "mock data", "样本数据", "return 0", "sample data"
    ]
    stub_hits = sum(1 for kw in stub_keywords if kw.lower() in learnings_content.lower())
    original_stub_hits = sum(1 for kw in stub_keywords if kw.lower() in original_learnings_content.lower())
    new_stub_content = stub_hits > original_stub_hits
    
    checks.append({
        "name": "C3_no_stub_antipattern_recorded",
        "passed": new_stub_content and stub_hits >= 1,
        "detail": (
            f"No-stub/no-TODO anti-pattern in learnings: "
            f"found {stub_hits} keywords (original had {original_stub_hits}). "
            f"Net new content: {new_stub_content}"
        )
    })

    # C4: Entry format compliance — no individual entry should exceed 4 lines of actual content
    # Find all bullet entries (lines starting with "  - **") and check their block size
    # We look for the pattern: entry header line followed by sub-lines
    entry_blocks = re.split(r'\n(?=- [^\s])', learnings_content)
    bloated_entries = []
    for block in entry_blocks:
        lines = [l for l in block.split('\n') if l.strip()]
        # An "entry" is a top-level bullet with its sub-items
        # Count only non-header lines (sub-items)
        sub_lines = [l for l in lines if l.strip().startswith('- **') or l.strip().startswith('**')]
        if len(sub_lines) > 4:
            bloated_entries.append(block[:80].strip())
    
    checks.append({
        "name": "C4_entry_format_within_line_limit",
        "passed": len(bloated_entries) == 0,
        "detail": (
            "All entries within 2-4 line limit." if not bloated_entries 
            else f"Bloated entries found: {bloated_entries[:2]}"
        )
    })

    # C5: Version header updated (version or date changed)
    # Original: "版本: v0.1.0 | 最后更新: 2024-01-15"
    original_version_line = "版本: v0.1.0 | 最后更新: 2024-01-15"
    version_updated = original_version_line not in learnings_content
    checks.append({
        "name": "C5_version_header_updated",
        "passed": version_updated,
        "detail": (
            "Version/date header updated in learnings.md." if version_updated 
            else "Version header unchanged — Evolution Protocol Step 4 item 5 not followed."
        )
    })

    # ─────────────────────────────────────────────────────────────────────
    # FINAL SCORING
    # ─────────────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    
    # Task passes only if critical checks pass:
    # A2 (format), A3 (D-codes), B1 (read-only), C1 (learnings updated), C2+C3 (content)
    critical_checks = {"A2_three_section_structure", "A3_diagnosis_uses_proprietary_d_codes",
                       "B1_readonly_files_untouched", "C1_learnings_was_updated",
                       "C2_semantic_reasoning_pattern_recorded", "C3_no_stub_antipattern_recorded"}
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )
    
    result = {
        "passed": critical_passed and score >= 0.7,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace_dir)