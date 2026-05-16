import sys
import json
import ast
import os
from pathlib import Path

def check_google_style_docstring(docstring: str) -> dict:
    """Check if a docstring looks like a proper Google Style docstring."""
    if not docstring:
        return {"has_docstring": False, "is_google_style": False, "is_stub": False}
    
    stripped = docstring.strip()
    
    # Detect known stub patterns from the original files
    stub_phrases = [
        "TODO: add docs",
        "Load stuff.",
        "Stub docstring that is not Google Style.",
        "Check debit.",
        "bad docs",
        "This function validates something about amounts.",
        "Not documented properly at all.",
        "Just a placeholder.",
    ]
    is_stub = any(phrase in stripped for phrase in stub_phrases)
    
    # Google Style has at minimum a summary line; for functions with args it should have sections
    # We check for the presence of Google Style section markers
    has_args = "Args:" in stripped
    has_returns = "Returns:" in stripped
    has_raises = "Raises:" in stripped
    
    # A proper docstring must have a non-trivial summary (more than a few words)
    lines = [l.strip() for l in stripped.splitlines() if l.strip()]
    has_summary = len(lines) > 0 and len(lines[0]) > 10
    
    return {
        "has_docstring": bool(stripped),
        "is_google_style": has_summary and (has_args or has_returns or has_raises or len(lines) >= 2),
        "is_stub": is_stub,
        "has_args": has_args,
        "has_returns": has_returns,
        "has_raises": has_raises,
    }

def extract_function_docstrings(filepath: str) -> dict:
    """Parse a Python file and extract docstrings for all functions/methods."""
    results = {}
    try:
        source = Path(filepath).read_text(encoding="utf-8")
        tree = ast.parse(source)
    except Exception as e:
        return {"_parse_error": str(e)}
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            docstring = ast.get_docstring(node)
            results[node.name] = {
                "docstring": docstring,
                "lineno": node.lineno,
                **check_google_style_docstring(docstring),
            }
    return results

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    checks = []
    total_score = 0.0
    
    # ── Define which functions we expect to be documented in each file ──────
    # Format: {relative_path: {func_name: {"was_stub": bool, "had_no_doc": bool, "needs_args_section": bool}}}
    target_files = {
        "src/pipeline/ingest.py": {
            "load_csv":          {"was_stub": False, "had_no_doc": True,  "needs_args": True},
            "load_json":         {"was_stub": True,  "had_no_doc": False, "needs_args": True},
            "normalize_record":  {"was_stub": False, "had_no_doc": False, "needs_args": False},  # already correct
        },
        "src/pipeline/transforms/clean.py": {
            "strip_whitespace":       {"was_stub": False, "had_no_doc": True, "needs_args": True},
            "remove_special_chars":   {"was_stub": False, "had_no_doc": True, "needs_args": True},
            "normalize_amount":       {"was_stub": False, "had_no_doc": True, "needs_args": True},
        },
        "src/models/transaction.py": {
            "is_debit":       {"was_stub": True,  "had_no_doc": False, "needs_args": False},
            "apply_fx_rate":  {"was_stub": False, "had_no_doc": True,  "needs_args": True},
            "to_dict":        {"was_stub": False, "had_no_doc": True,  "needs_args": False},
        },
        "src/validators/schema_validator.py": {
            "validate_required_fields":  {"was_stub": False, "had_no_doc": True,  "needs_args": True},
            "validate_amount_range":     {"was_stub": True,  "had_no_doc": False, "needs_args": True},
            "validate_currency_code":    {"was_stub": False, "had_no_doc": True,  "needs_args": True},
        },
        "src/utils/logger.py": {
            "setup_logger":  {"was_stub": False, "had_no_doc": True, "needs_args": True},
            "log_event":     {"was_stub": False, "had_no_doc": True, "needs_args": True},
        },
    }
    
    # ── Check 1: All target files exist (recursive processing worked) ────────
    all_files_exist = True
    for rel_path in target_files:
        full_path = os.path.join(workspace, rel_path)
        exists = os.path.isfile(full_path)
        if not exists:
            all_files_exist = False
        checks.append({
            "name": f"file_exists:{rel_path}",
            "passed": exists,
            "detail": f"{'Found' if exists else 'MISSING'}: {full_path}"
        })
    
    # ── Check 2: Previously-undocumented functions now have docstrings ───────
    undoc_functions_documented = 0
    undoc_functions_total = 0
    
    for rel_path, funcs in target_files.items():
        full_path = os.path.join(workspace, rel_path)
        try:
            doc_map = extract_function_docstrings(full_path)
        except Exception as e:
            checks.append({
                "name": f"parse_error:{rel_path}",
                "passed": False,
                "detail": f"Could not parse {rel_path}: {e}"
            })
            continue
        
        for func_name, meta in funcs.items():
            if not meta["had_no_doc"]:
                continue  # skip functions that already had docstrings (tested separately)
            undoc_functions_total += 1
            func_info = doc_map.get(func_name, {})
            has_doc = func_info.get("has_docstring", False)
            is_stub = func_info.get("is_stub", False)
            if has_doc and not is_stub:
                undoc_functions_documented += 1
            checks.append({
                "name": f"newly_documented:{rel_path}::{func_name}",
                "passed": has_doc and not is_stub,
                "detail": (
                    f"Function '{func_name}' in {rel_path}: "
                    f"has_docstring={has_doc}, is_stub={is_stub}, "
                    f"docstring_preview={repr((func_info.get('docstring') or '')[:80])}"
                )
            })
    
    # ── Check 3: Stub docstrings were REPLACED (--overwrite was used) ────────
    stub_functions_overwritten = 0
    stub_functions_total = 0
    
    for rel_path, funcs in target_files.items():
        full_path = os.path.join(workspace, rel_path)
        try:
            doc_map = extract_function_docstrings(full_path)
        except Exception:
            continue
        
        for func_name, meta in funcs.items():
            if not meta["was_stub"]:
                continue
            stub_functions_total += 1
            func_info = doc_map.get(func_name, {})
            is_stub_still = func_info.get("is_stub", True)
            has_proper_doc = func_info.get("has_docstring", False) and not is_stub_still
            if has_proper_doc:
                stub_functions_overwritten += 1
            checks.append({
                "name": f"stub_overwritten:{rel_path}::{func_name}",
                "passed": has_proper_doc,
                "detail": (
                    f"Stub in '{func_name}' ({rel_path}): "
                    f"still_stub={is_stub_still}, proper_doc={has_proper_doc}, "
                    f"docstring_preview={repr((func_info.get('docstring') or '')[:80])}"
                )
            })
    
    # ── Check 4: Google Style format (Args: / Returns: sections present) ─────
    google_style_count = 0
    google_style_total = 0
    
    for rel_path, funcs in target_files.items():
        full_path = os.path.join(workspace, rel_path)
        try:
            doc_map = extract_function_docstrings(full_path)
        except Exception:
            continue
        
        for func_name, meta in funcs.items():
            if not meta.get("needs_args", False):
                continue
            google_style_total += 1
            func_info = doc_map.get(func_name, {})
            has_args = func_info.get("has_args", False)
            has_returns = func_info.get("has_returns", False)
            is_google = has_args or has_returns
            if is_google:
                google_style_count += 1
            checks.append({
                "name": f"google_style:{rel_path}::{func_name}",
                "passed": is_google,
                "detail": (
                    f"'{func_name}' in {rel_path}: has_args_section={has_args}, "
                    f"has_returns_section={has_returns}"
                )
            })
    
    # ── Check 5: The already-correct normalize_record was NOT broken ──────────
    try:
        ingest_path = os.path.join(workspace, "src/pipeline/ingest.py")
        doc_map = extract_function_docstrings(ingest_path)
        nr_info = doc_map.get("normalize_record", {})
        nr_ok = nr_info.get("has_args", False) and nr_info.get("has_returns", False)
        checks.append({
            "name": "preserved_existing_correct_docstring:normalize_record",
            "passed": nr_ok,
            "detail": (
                f"normalize_record docstring preserved/correct: "
                f"has_args={nr_info.get('has_args')}, "
                f"has_returns={nr_info.get('has_returns')}, "
                f"preview={repr((nr_info.get('docstring') or '')[:80])}"
            )
        })
    except Exception as e:
        checks.append({
            "name": "preserved_existing_correct_docstring:normalize_record",
            "passed": False,
            "detail": f"Error checking normalize_record: {e}"
        })
    
    # ── Scoring ───────────────────────────────────────────────────────────────
    # Weight breakdown:
    # - All files processed (recursive): 15%
    # - Undocumented functions now documented: 35%
    # - Stub docstrings overwritten (--overwrite): 30%
    # - Google Style format present: 20%
    
    file_score = sum(1 for c in checks if c["name"].startswith("file_exists:") and c["passed"]) / max(len(target_files), 1)
    
    undoc_score = undoc_functions_documented / max(undoc_functions_total, 1)
    
    stub_score = stub_functions_overwritten / max(stub_functions_total, 1)
    
    gs_score = google_style_count / max(google_style_total, 1)
    
    total_score = (
        0.15 * file_score +
        0.35 * undoc_score +
        0.30 * stub_score +
        0.20 * gs_score
    )
    
    # Bonus: preserved existing correct docstring
    preserve_check = next((c for c in checks if "preserved_existing_correct_docstring" in c["name"]), None)
    if preserve_check and preserve_check["passed"]:
        total_score = min(total_score + 0.05, 1.0)
    
    passed = total_score >= 0.75
    
    result = {
        "passed": passed,
        "score": round(total_score, 4),
        "checks": checks,
        "_summary": {
            "file_coverage": f"{int(file_score*len(target_files))}/{len(target_files)} files found",
            "undocumented_fixed": f"{undoc_functions_documented}/{undoc_functions_total}",
            "stubs_overwritten": f"{stub_functions_overwritten}/{stub_functions_total}",
            "google_style_compliant": f"{google_style_count}/{google_style_total}",
        }
    }
    
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()