#!/usr/bin/env python3
"""
Evaluation script for the md-to-pdf multi-step task.

Checks:
1. stakeholder_summary.pdf exists and is a valid PDF
2. stakeholder_summary.md has YAML frontmatter with a title field
3. technical_report.pdf exists and is a valid PDF
4. technical_report.md has YAML frontmatter with a title field
5. The modern style was used for stakeholder_summary (PDF not trivially tiny)
6. The branded/custom CSS was used for technical_report (PDF not trivially tiny)
"""

import json
import sys
import re
from pathlib import Path

def check_pdf_valid(path: Path) -> tuple[bool, str]:
    """Check if file exists and starts with PDF magic bytes."""
    try:
        if not path.exists():
            return False, f"File not found: {path}"
        data = path.read_bytes()
        if not data.startswith(b'%PDF'):
            return False, f"File does not start with %PDF magic bytes: {path}"
        if path.stat().st_size < 1000:
            return False, f"PDF suspiciously small ({path.stat().st_size} bytes): {path}"
        return True, f"Valid PDF ({path.stat().st_size} bytes)"
    except Exception as e:
        return False, f"Error reading {path}: {e}"

def check_md_has_title(path: Path) -> tuple[bool, str]:
    """Check if a Markdown file has YAML frontmatter with a non-empty title."""
    try:
        if not path.exists():
            return False, f"Markdown file not found: {path}"
        content = path.read_text(encoding="utf-8")
        # YAML frontmatter must start at line 1 with ---
        if not content.startswith("---"):
            return False, "No YAML frontmatter found (file does not start with '---')"
        # Find closing ---
        end = content.find("\n---", 3)
        if end == -1:
            return False, "YAML frontmatter not closed with '---'"
        frontmatter = content[3:end]
        # Check for title: field
        title_match = re.search(r'^title\s*:\s*(.+)$', frontmatter, re.MULTILINE)
        if not title_match:
            return False, "No 'title:' field found in YAML frontmatter"
        title_val = title_match.group(1).strip().strip('"').strip("'")
        if not title_val:
            return False, "title field is empty"
        return True, f"Found title: '{title_val}'"
    except Exception as e:
        return False, f"Error reading {path}: {e}"

def find_pdf(workspace: Path, stem: str) -> Path | None:
    """Search for a PDF with the given stem anywhere in workspace."""
    candidates = list(workspace.rglob(f"{stem}.pdf"))
    if not candidates:
        return None
    # Prefer the one closest to the source md file
    for c in candidates:
        if "q3_2024" in str(c) or "reports" in str(c):
            return c
    return candidates[0]

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "arguments", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(0)

    workspace = Path(sys.argv[1])
    checks = []

    # ── Locate source Markdown files (hardcoded from gen_inputs_script) ──────
    stakeholder_md = workspace / "institute" / "reports" / "q3_2024" / "stakeholder_summary.md"
    technical_md   = workspace / "institute" / "reports" / "q3_2024" / "technical_report.md"

    # ── Check 1: stakeholder_summary.md has YAML title ───────────────────────
    ok, detail = check_md_has_title(stakeholder_md)
    checks.append({"name": "stakeholder_summary.md has YAML title", "passed": ok, "detail": detail})

    # ── Check 2: technical_report.md has YAML title ───────────────────────────
    ok, detail = check_md_has_title(technical_md)
    checks.append({"name": "technical_report.md has YAML title", "passed": ok, "detail": detail})

    # ── Check 3: stakeholder_summary.pdf exists and is valid ─────────────────
    stakeholder_pdf = find_pdf(workspace, "stakeholder_summary")
    if stakeholder_pdf:
        ok, detail = check_pdf_valid(stakeholder_pdf)
    else:
        ok, detail = False, "stakeholder_summary.pdf not found anywhere in workspace"
    checks.append({"name": "stakeholder_summary.pdf is valid PDF", "passed": ok, "detail": detail})

    # ── Check 4: technical_report.pdf exists and is valid ────────────────────
    technical_pdf = find_pdf(workspace, "technical_report")
    if technical_pdf:
        ok, detail = check_pdf_valid(technical_pdf)
    else:
        ok, detail = False, "technical_report.pdf not found anywhere in workspace"
    checks.append({"name": "technical_report.pdf is valid PDF", "passed": ok, "detail": detail})

    # ── Check 5: stakeholder_summary.pdf contains "modern" style signature ───
    # The modern CSS injects color #0057b8 into the HTML which pandoc embeds.
    # We check the PDF byte stream for the colour or for markers from the modern CSS.
    try:
        if stakeholder_pdf and stakeholder_pdf.exists():
            raw = stakeholder_pdf.read_bytes()
            # wkhtmltopdf embeds CSS content or colour references in the PDF stream
            # modern.css uses #0057b8 (rgb 0,87,184) and 'Helvetica Neue'
            has_modern = (b'0057b8' in raw or b'Helvetica' in raw or
                          b'0057B8' in raw or b'1a1a2e' in raw)
            if has_modern:
                checks.append({"name": "stakeholder_summary.pdf uses 'modern' style",
                                "passed": True, "detail": "Found modern CSS colour/font marker in PDF stream"})
            else:
                # Fallback: accept if PDF is reasonably sized (>= 15KB) — style was applied
                size = stakeholder_pdf.stat().st_size
                if size >= 15000:
                    checks.append({"name": "stakeholder_summary.pdf uses 'modern' style",
                                   "passed": True,
                                   "detail": f"PDF size {size}B suggests styled output (colour markers absent but size OK)"})
                else:
                    checks.append({"name": "stakeholder_summary.pdf uses 'modern' style",
                                   "passed": False,
                                   "detail": "Could not detect modern CSS markers in PDF and file is small"})
        else:
            checks.append({"name": "stakeholder_summary.pdf uses 'modern' style",
                           "passed": False, "detail": "PDF file missing, cannot check style"})
    except Exception as e:
        checks.append({"name": "stakeholder_summary.pdf uses 'modern' style",
                       "passed": False, "detail": f"Error: {e}"})

    # ── Check 6: technical_report.pdf contains branded CSS signature ──────────
    # branded.css uses #8b0000 (dark red) and 'Courier New'
    try:
        if technical_pdf and technical_pdf.exists():
            raw = technical_pdf.read_bytes()
            has_branded = (b'8b0000' in raw or b'8B0000' in raw or
                           b'Courier' in raw or b'fafafa' in raw)
            if has_branded:
                checks.append({"name": "technical_report.pdf uses branded CSS",
                                "passed": True, "detail": "Found branded CSS colour/font marker in PDF stream"})
            else:
                size = technical_pdf.stat().st_size
                if size >= 15000:
                    checks.append({"name": "technical_report.pdf uses branded CSS",
                                   "passed": True,
                                   "detail": f"PDF size {size}B suggests styled output (branded markers absent but size OK)"})
                else:
                    checks.append({"name": "technical_report.pdf uses branded CSS",
                                   "passed": False,
                                   "detail": "Could not detect branded CSS markers in PDF and file is small"})
        else:
            checks.append({"name": "technical_report.pdf uses branded CSS",
                           "passed": False, "detail": "PDF file missing, cannot check style"})
    except Exception as e:
        checks.append({"name": "technical_report.pdf uses branded CSS",
                       "passed": False, "detail": f"Error: {e}"})

    # ── Check 7: md2pdf.sh script was used (not raw pandoc bypass) ──────────
    # Indirect: verify the script is still intact and executable
    script_path = workspace / "skills" / "md-to-pdf" / "scripts" / "md2pdf.sh"
    try:
        intact = script_path.exists() and script_path.stat().st_size > 200
        checks.append({"name": "md2pdf.sh script is intact",
                        "passed": intact,
                        "detail": f"Script exists={script_path.exists()}, size={script_path.stat().st_size if script_path.exists() else 0}"})
    except Exception as e:
        checks.append({"name": "md2pdf.sh script is intact", "passed": False, "detail": str(e)})

    # ── Score & Result ────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)

    # Must pass critical checks: both PDFs valid + both MDs have title
    critical = [
        "stakeholder_summary.md has YAML title",
        "technical_report.md has YAML title",
        "stakeholder_summary.pdf is valid PDF",
        "technical_report.pdf is valid PDF",
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical
    )

    overall_passed = critical_passed and passed_count >= 5

    print(json.dumps({
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    main()