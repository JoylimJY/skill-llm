import sys
import json
import os
import re
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []
score = 0.0
max_score = 6.0

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed

# ── Check 1: Authentication was performed ──────────────────────────────────────
try:
    config_file = Path.home() / ".config" / "olcli" / "config.json"
    if config_file.exists():
        config = json.loads(config_file.read_text())
        cookie = config.get("cookie", "")
        authenticated = config.get("authenticated", False)
        expected_cookie = "s%3AaBcDeFgHiJkLmNoPqRsTuVwXyZ123456.abcdefghijklmnopqrstuvwxyz0123456789"
        if authenticated and cookie == expected_cookie:
            ok = add_check("auth_performed", True, f"Auth config found with correct cookie and authenticated=true")
            score += 1.0
        elif authenticated:
            ok = add_check("auth_performed", False, f"Authenticated but wrong cookie value: '{cookie}'")
        else:
            ok = add_check("auth_performed", False, "Config found but authenticated=false")
    else:
        add_check("auth_performed", False, f"No auth config found at {config_file}")
except Exception as e:
    add_check("auth_performed", False, f"Exception reading auth config: {e}")

# ── Check 2: Project was pulled (directory with .olcli.json exists) ────────────
try:
    olcli_json_files = list(workspace.rglob(".olcli.json"))
    if olcli_json_files:
        project_dir = olcli_json_files[0].parent
        config_data = json.loads(olcli_json_files[0].read_text())
        if config_data.get("project_name") == "NeurIPS_2024_Paper":
            ok = add_check("project_pulled", True, f"Project pulled to {project_dir} with correct .olcli.json")
            score += 1.0
        else:
            add_check("project_pulled", False, f".olcli.json exists but project_name is '{config_data.get('project_name')}'")
    else:
        add_check("project_pulled", False, "No .olcli.json found in workspace tree — project not pulled")
except Exception as e:
    add_check("project_pulled", False, f"Exception checking project pull: {e}")

# ── Check 3: main.tex abstract was updated ─────────────────────────────────────
try:
    olcli_json_files = list(workspace.rglob(".olcli.json"))
    if olcli_json_files:
        project_dir = olcli_json_files[0].parent
        main_tex = project_dir / "main.tex"
        if main_tex.exists():
            content = main_tex.read_text()
            expected_phrase = "12% improvement over baselines"
            if expected_phrase in content:
                # Also verify the old abstract is gone (or replaced)
                old_phrase = "We investigate several deep learning architectures"
                if old_phrase not in content:
                    ok = add_check("abstract_updated", True, f"main.tex contains expected abstract text and old text replaced")
                else:
                    ok = add_check("abstract_updated", True, f"main.tex contains expected abstract text (note: old text still present but new text found)")
                score += 1.0
            else:
                add_check("abstract_updated", False, f"main.tex does not contain '12% improvement over baselines'. Abstract not updated correctly.")
        else:
            add_check("abstract_updated", False, f"main.tex not found in project dir {project_dir}")
    else:
        add_check("abstract_updated", False, "Project not pulled, cannot check main.tex")
except Exception as e:
    add_check("abstract_updated", False, f"Exception checking main.tex: {e}")

# ── Check 4: Push was performed (push log contains entry OR sync was used) ─────
try:
    push_log = Path.home() / ".local" / "share" / "olcli" / "push_log.jsonl"
    if push_log.exists():
        lines = [l.strip() for l in push_log.read_text().splitlines() if l.strip()]
        if lines:
            # Verify it was for the right project
            any_valid = False
            for line in lines:
                try:
                    entry = json.loads(line)
                    if entry.get("project_id") == "6507f3a1b2c3d4e5f6a7b8c9":
                        any_valid = True
                        break
                except:
                    pass
            if any_valid:
                ok = add_check("changes_pushed", True, "Push log contains valid entry for NeurIPS_2024_Paper")
                score += 1.0
            else:
                add_check("changes_pushed", False, "Push log entries found but none for correct project_id")
        else:
            add_check("changes_pushed", False, "Push log exists but is empty")
    else:
        add_check("changes_pushed", False, f"No push log found at {push_log} — push not performed")
except Exception as e:
    add_check("changes_pushed", False, f"Exception checking push log: {e}")

# ── Check 5: camera_ready.pdf exists in the project directory ─────────────────
try:
    pdf_files = list(workspace.rglob("camera_ready.pdf"))
    if pdf_files:
        pdf_path = pdf_files[0]
        content = pdf_path.read_bytes()
        if content.startswith(b"%PDF"):
            ok = add_check("pdf_downloaded", True, f"camera_ready.pdf found at {pdf_path} with valid PDF header")
            score += 1.0
        else:
            add_check("pdf_downloaded", False, f"camera_ready.pdf found at {pdf_path} but does not start with %PDF")
    else:
        # Check if any PDF was downloaded in project dir
        all_pdfs = list(workspace.rglob("*.pdf"))
        if all_pdfs:
            add_check("pdf_downloaded", False, f"No camera_ready.pdf found. Found other PDFs: {[str(p) for p in all_pdfs]}")
        else:
            add_check("pdf_downloaded", False, "No camera_ready.pdf found anywhere in workspace")
except Exception as e:
    add_check("pdf_downloaded", False, f"Exception checking PDF: {e}")

# ── Check 6: main.bbl exists in the project directory with correct content ─────
try:
    bbl_files = list(workspace.rglob("main.bbl"))
    if bbl_files:
        bbl_path = bbl_files[0]
        content = bbl_path.read_text()
        # Check it has thebibliography environment (real .bbl content)
        if "\\begin{thebibliography}" in content and "\\bibitem" in content:
            # Extra: check it's the right file (contains our citations)
            if "vaswani2017attention" in content or "Vaswani" in content:
                ok = add_check("bbl_downloaded", True, f"main.bbl found at {bbl_path} with valid bibliography content including expected citations")
                score += 1.0
            else:
                ok = add_check("bbl_downloaded", True, f"main.bbl found at {bbl_path} with valid bibliography structure")
                score += 1.0
        else:
            add_check("bbl_downloaded", False, f"main.bbl found at {bbl_path} but does not contain valid .bbl content (missing thebibliography environment)")
    else:
        # Check if any .bbl was downloaded
        all_bbls = list(workspace.rglob("*.bbl"))
        if all_bbls:
            add_check("bbl_downloaded", False, f"No main.bbl found. Found other .bbl files: {[str(p) for p in all_bbls]}. Must be named 'main.bbl'.")
        else:
            add_check("bbl_downloaded", False, "No .bbl file found anywhere in workspace — olcli output bbl -o main.bbl not executed")
except Exception as e:
    add_check("bbl_downloaded", False, f"Exception checking main.bbl: {e}")

# ── Final Score ────────────────────────────────────────────────────────────────
final_score = score / max_score
passed = final_score >= 0.85  # Require at least 5/6 checks

print(json.dumps({
    "passed": passed,
    "score": round(final_score, 3),
    "checks": checks
}, indent=2))