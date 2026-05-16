#!/usr/bin/env python3
"""
Evaluation script for the minimax-docx Template-Apply task.
Grades the agent's final output: compliance_report_Q4_2024.docx
"""

import sys
import json
import zipfile
import re
import subprocess
from pathlib import Path

WORKSPACE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
SKILL_PATH = WORKSPACE / "skill" / "minimax-docx"

OUTPUT_FILENAME = "compliance_report_Q4_2024.docx"
PLACEHOLDER_RE = re.compile(r'\{\{([A-Z0-9_]+)\}\}')

# Expected values derived from data_brief.txt
EXPECTED_VALUES = {
    "REPORT_PERIOD":     "Q4 2024",          # "October–December" also acceptable
    "SITE_NAME":         "BioSynth Manufacturing Erlangen",
    "SITE_CODE":         "BSM-ERN-042",
    "PREPARED_BY":       "Dr. Elena Vasquez",
    "COMPLIANCE_SCORE":  "94.7",
    "DEVIATION_COUNT":   "3",
}

checks = []

def add_check(name: str, passed: bool, detail: str):
    checks.append({"name": name, "passed": passed, "detail": detail})
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}: {detail}")

def run_engine(cmd_args, docx_path):
    """Run docx_engine.py with given args, return (returncode, stdout, stderr)."""
    try:
        r = subprocess.run(
            ["python3", str(SKILL_PATH / "docx_engine.py")] + cmd_args + [str(docx_path)],
            capture_output=True, text=True, timeout=30
        )
        return r.returncode, r.stdout, r.stderr
    except Exception as e:
        return -1, "", str(e)

print("=== Evaluation: compliance_report_Q4_2024.docx ===\n")

# ── GATE 0: Find the output file ──────────────────────────────────────────────
output_files = list(WORKSPACE.rglob(OUTPUT_FILENAME))
if not output_files:
    add_check("output_file_exists", False,
              f"{OUTPUT_FILENAME} not found anywhere in workspace")
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)

output_path = output_files[0]
add_check("output_file_exists", True, f"Found at {output_path}")

# ── GATE 1: Valid zip / docx structure ────────────────────────────────────────
try:
    with zipfile.ZipFile(output_path) as z:
        names = z.namelist()
    required_parts = ["word/document.xml", "[Content_Types].xml",
                      "word/_rels/document.xml.rels"]
    missing = [p for p in required_parts if p not in names]
    if missing:
        add_check("valid_docx_structure", False, f"Missing parts: {missing}")
    else:
        add_check("valid_docx_structure", True, "All required parts present")
except Exception as e:
    add_check("valid_docx_structure", False, f"Not a valid docx zip: {e}")

# ── GATE 2: No residual placeholders ─────────────────────────────────────────
try:
    with zipfile.ZipFile(output_path) as z:
        doc_xml = z.read("word/document.xml").decode("utf-8", errors="replace")
    residual_tokens = set(PLACEHOLDER_RE.findall(doc_xml))
    if residual_tokens:
        add_check("no_residual_placeholders", False,
                  f"Unreplaced tokens found: {residual_tokens}")
    else:
        add_check("no_residual_placeholders", True, "All placeholders substituted")
except Exception as e:
    add_check("no_residual_placeholders", False, f"Could not read document.xml: {e}")

# ── GATE 3: Correct placeholder values ────────────────────────────────────────
try:
    with zipfile.ZipFile(output_path) as z:
        doc_xml = z.read("word/document.xml").decode("utf-8", errors="replace")

    # Strip XML tags to get raw text
    clean_text = re.sub(r'<[^>]+>', ' ', doc_xml)
    clean_text = re.sub(r'\s+', ' ', clean_text)

    all_values_correct = True
    detail_parts = []
    for key, expected in EXPECTED_VALUES.items():
        # Be flexible: allow XML-encoded variants (&amp; etc.)
        safe_expected = expected.replace("&", "&amp;")
        found = expected in clean_text or safe_expected in clean_text
        # Also check for Q4 2024 variants
        if key == "REPORT_PERIOD":
            found = found or "Q4 2024" in clean_text or "October" in clean_text
        if not found:
            all_values_correct = False
            detail_parts.append(f"MISSING '{key}'='{expected}'")
        else:
            detail_parts.append(f"OK '{key}'")

    add_check("correct_placeholder_values", all_values_correct,
              "; ".join(detail_parts))
except Exception as e:
    add_check("correct_placeholder_values", False, f"Error reading content: {e}")

# ── GATE 4: Margin enforcement ≥ 1440 twips ───────────────────────────────────
try:
    with zipfile.ZipFile(output_path) as z:
        doc_xml = z.read("word/document.xml").decode("utf-8", errors="replace")

    mar_re     = re.compile(r'w:pgMar\s[^/]*/>', re.DOTALL)
    side_re    = re.compile(r'w:(?:top|bottom|left|right)="(\d+)"')
    violations = []
    for m in mar_re.finditer(doc_xml):
        block = m.group(0)
        for vm in side_re.finditer(block):
            val = int(vm.group(1))
            if val < 1440:
                violations.append(val)

    if violations:
        add_check("margins_enforced", False,
                  f"Margin violations (<1440 twips): {violations}")
    else:
        add_check("margins_enforced", True,
                  "All margins ≥ 1440 twips (72pt)")
except Exception as e:
    add_check("margins_enforced", False, f"Could not check margins: {e}")

# ── GATE 5: Metadata injected into core.xml ──────────────────────────────────
try:
    with zipfile.ZipFile(output_path) as z:
        names = z.namelist()
        if "docProps/core.xml" not in names:
            add_check("metadata_injected", False, "docProps/core.xml missing")
        else:
            core_xml = z.read("docProps/core.xml").decode("utf-8", errors="replace")
            has_creator = "Vasquez" in core_xml or "Elena" in core_xml
            has_version = "1.0" in core_xml
            has_dept    = "Regulatory" in core_xml or "department" in core_xml.lower()

            issues = []
            if not has_creator:
                issues.append("author/creator not found in core.xml")
            if not has_version:
                issues.append("document_version not found in core.xml")

            if issues:
                add_check("metadata_injected", False, "; ".join(issues))
            else:
                add_check("metadata_injected", True,
                          "author and version present in core.xml")
except Exception as e:
    add_check("metadata_injected", False, f"Error reading core.xml: {e}")

# ── GATE 6: docx_engine.py audit passes ───────────────────────────────────────
try:
    rc, stdout, stderr = run_engine(["audit"], output_path)
    passed_audit = (rc == 0)
    detail = stdout.strip() + (" | " + stderr.strip() if stderr.strip() else "")
    add_check("audit_passes", passed_audit,
              detail if detail else f"exit code {rc}")
except Exception as e:
    add_check("audit_passes", False, f"audit check error: {e}")

# ── GATE 7: docx_engine.py residual passes ────────────────────────────────────
try:
    rc, stdout, stderr = run_engine(["residual"], output_path)
    passed_residual = (rc == 0)
    detail = stdout.strip() + (" | " + stderr.strip() if stderr.strip() else "")
    add_check("residual_passes", passed_residual,
              detail if detail else f"exit code {rc}")
except Exception as e:
    add_check("residual_passes", False, f"residual check error: {e}")

# ── GATE 8: Template not modified (template should remain pristine) ────────────
try:
    template_path = (WORKSPACE / "project" / "quarterly_reports" /
                     "Q4_2024" / "compliance_template.docx")
    with zipfile.ZipFile(template_path) as z:
        tmpl_xml = z.read("word/document.xml").decode("utf-8", errors="replace")
    tmpl_tokens = set(PLACEHOLDER_RE.findall(tmpl_xml))
    # Template should still have placeholders (untouched)
    if tmpl_tokens == {"REPORT_PERIOD", "SITE_NAME", "SITE_CODE",
                       "PREPARED_BY", "COMPLIANCE_SCORE", "DEVIATION_COUNT"}:
        add_check("template_untouched", True,
                  "Original template still contains all placeholders intact")
    else:
        add_check("template_untouched", False,
                  f"Template placeholders modified: remaining={tmpl_tokens}")
except Exception as e:
    add_check("template_untouched", False, f"Could not verify template: {e}")

# ── GATE 9: Did NOT use python-docx (restricted tool check) ──────────────────
try:
    # Search for any Python scripts the agent may have written that import python-docx
    suspicious_imports = []
    for py_file in WORKSPACE.rglob("*.py"):
        if "docx_engine.py" in str(py_file):
            continue  # skip the skill's own engine
        try:
            content = py_file.read_text(errors="replace")
            if re.search(r"from\s+docx\b|import\s+docx\b|python.docx", content):
                suspicious_imports.append(str(py_file))
        except Exception:
            pass

    if suspicious_imports:
        add_check("no_forbidden_library", False,
                  f"python-docx used in: {suspicious_imports}")
    else:
        add_check("no_forbidden_library", True,
                  "No forbidden library (python-docx) detected in agent scripts")
except Exception as e:
    add_check("no_forbidden_library", True,
              f"Could not scan for forbidden libraries (non-critical): {e}")

# ─────────────────────────────────────────────
# SCORING
# ─────────────────────────────────────────────
# Weight distribution:
# output_file_exists            5%
# valid_docx_structure          5%
# no_residual_placeholders     15%
# correct_placeholder_values   20%
# margins_enforced             15%
# metadata_injected            15%
# audit_passes                 10%
# residual_passes              10%
# template_untouched            3%
# no_forbidden_library          2%

weights = {
    "output_file_exists":          0.05,
    "valid_docx_structure":        0.05,
    "no_residual_placeholders":    0.15,
    "correct_placeholder_values":  0.20,
    "margins_enforced":            0.15,
    "metadata_injected":           0.15,
    "audit_passes":                0.10,
    "residual_passes":             0.10,
    "template_untouched":          0.03,
    "no_forbidden_library":        0.02,
}

score = 0.0
for check in checks:
    w = weights.get(check["name"], 0.0)
    if check["passed"]:
        score += w

overall_passed = score >= 0.75

print(f"\n=== SCORE: {score:.2f} | PASSED: {overall_passed} ===\n")

result = {
    "passed": overall_passed,
    "score":  round(score, 4),
    "checks": checks,
}
print(json.dumps(result, indent=2))