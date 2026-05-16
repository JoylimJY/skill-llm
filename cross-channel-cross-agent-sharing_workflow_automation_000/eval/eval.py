import sys
import json
import re
from pathlib import Path
from datetime import date

def run_eval(workspace: str):
    ws = Path(workspace)
    today = date.today().isoformat()  # YYYY-MM-DD
    checks = []
    total_weight = 0.0
    earned_weight = 0.0

    def add_check(name: str, passed: bool, detail: str, weight: float = 1.0):
        nonlocal total_weight, earned_weight
        checks.append({"name": name, "passed": passed, "detail": detail})
        total_weight += weight
        if passed:
            earned_weight += weight

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 1: TOOLS.md updated with biopython entry
    # ─────────────────────────────────────────────────────────────────────────
    try:
        tools_text = (ws / "TOOLS.md").read_text()
        has_bio = "biopython" in tools_text.lower() or "Bio" in tools_text
        add_check(
            "TOOLS.md contains biopython entry",
            has_bio,
            f"'biopython' found in TOOLS.md: {has_bio}",
            weight=2.0
        )
    except Exception as e:
        add_check("TOOLS.md contains biopython entry", False, f"Error reading TOOLS.md: {e}", weight=2.0)

    try:
        tools_text = (ws / "TOOLS.md").read_text()
        # Must have workspace-scoped venv path (not global python)
        has_venv_path = ".venv-bio" in tools_text or "/workspace/.venv" in tools_text
        add_check(
            "TOOLS.md uses workspace-scoped venv path",
            has_venv_path,
            f"Workspace-scoped path found: {has_venv_path}. Content snippet: {tools_text[:800]}",
            weight=2.0
        )
    except Exception as e:
        add_check("TOOLS.md uses workspace-scoped venv path", False, f"Error: {e}", weight=2.0)

    try:
        tools_text = (ws / "TOOLS.md").read_text()
        # Must have install command (pip install biopython)
        has_install = re.search(r"pip\s+install.*biopython", tools_text, re.IGNORECASE) is not None
        add_check(
            "TOOLS.md has pip install command for biopython",
            has_install,
            f"pip install biopython command found: {has_install}",
            weight=1.5
        )
    except Exception as e:
        add_check("TOOLS.md has pip install command for biopython", False, f"Error: {e}", weight=1.5)

    try:
        tools_text = (ws / "TOOLS.md").read_text()
        # Must have verify command (import Bio or check_capability or similar)
        has_verify = re.search(r"(check_capability|import Bio|python.*-c.*Bio|verify)", tools_text, re.IGNORECASE) is not None
        add_check(
            "TOOLS.md has verify command for biopython",
            has_verify,
            f"Verify command found: {has_verify}",
            weight=1.0
        )
    except Exception as e:
        add_check("TOOLS.md has verify command for biopython", False, f"Error: {e}", weight=1.0)

    try:
        tools_text = (ws / "TOOLS.md").read_text()
        # Must have version info: 1.83
        has_version = "1.83" in tools_text
        add_check(
            "TOOLS.md records biopython version 1.83",
            has_version,
            f"Version 1.83 found: {has_version}",
            weight=1.5
        )
    except Exception as e:
        add_check("TOOLS.md records biopython version 1.83", False, f"Error: {e}", weight=1.5)

    try:
        tools_text = (ws / "TOOLS.md").read_text()
        # Must retain existing tools (samtools, blast+)
        has_samtools = "samtools" in tools_text.lower()
        has_blast = "blast" in tools_text.lower()
        add_check(
            "TOOLS.md retains existing tool entries",
            has_samtools and has_blast,
            f"samtools: {has_samtools}, blast: {has_blast}",
            weight=1.0
        )
    except Exception as e:
        add_check("TOOLS.md retains existing tool entries", False, f"Error: {e}", weight=1.0)

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 2: SKILL.md updated / new skill added for biopython
    # ─────────────────────────────────────────────────────────────────────────
    try:
        # Agent may update workspace SKILL.md OR create skills/biopython.md or similar
        skill_candidates = list(ws.rglob("*.md"))
        bio_skill_found = False
        bio_skill_content = ""
        for sc in skill_candidates:
            try:
                content = sc.read_text()
                if "biopython" in content.lower() and ("skill" in str(sc).lower() or "name:" in content):
                    bio_skill_found = True
                    bio_skill_content = content[:600]
                    break
            except Exception:
                continue
        add_check(
            "A skill entry for biopython capability exists",
            bio_skill_found,
            f"Bio skill found: {bio_skill_found}. Sample: {bio_skill_content[:300]}",
            weight=2.0
        )
    except Exception as e:
        add_check("A skill entry for biopython capability exists", False, f"Error: {e}", weight=2.0)

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 3: scripts/check_capability.sh was invoked (evidence in output / log)
    #          OR a verify script exists that uses check_capability.sh for biopython
    # ─────────────────────────────────────────────────────────────────────────
    try:
        # Look for a verification script that references check_capability.sh and Bio
        script_files = list((ws / "scripts").iterdir())
        verify_script_found = False
        for sf in script_files:
            try:
                sc = sf.read_text()
                if "check_capability" in sc and ("Bio" in sc or "biopython" in sc.lower()):
                    verify_script_found = True
                    break
            except Exception:
                continue
        # Also acceptable: a log or output file that shows check_capability was run
        cap_log_found = False
        for log_f in ws.rglob("*.log"):
            try:
                lc = log_f.read_text()
                if "check_capability" in lc or ("OK" in lc and "Bio" in lc):
                    cap_log_found = True
                    break
            except Exception:
                continue
        # Also check if any .sh script under scripts/ invokes it
        passed_verify = verify_script_found or cap_log_found
        add_check(
            "check_capability.sh invoked or referenced for biopython modules",
            passed_verify,
            f"verify script ref: {verify_script_found}, log evidence: {cap_log_found}",
            weight=1.5
        )
    except Exception as e:
        add_check("check_capability.sh invoked or referenced for biopython modules", False, f"Error: {e}", weight=1.5)

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 4: Memory log created at memory/YYYY-MM-DD.md with today's date
    # ─────────────────────────────────────────────────────────────────────────
    try:
        memory_log = ws / "memory" / f"{today}.md"
        log_exists = memory_log.exists()
        add_check(
            f"Memory log created at memory/{today}.md",
            log_exists,
            f"File exists: {log_exists}",
            weight=2.0
        )
    except Exception as e:
        add_check(f"Memory log created at memory/{today}.md", False, f"Error: {e}", weight=2.0)

    try:
        memory_log = ws / "memory" / f"{today}.md"
        log_content = memory_log.read_text() if memory_log.exists() else ""
        has_what_changed = "biopython" in log_content.lower() or "Bio" in log_content
        has_verify_info = re.search(r"(verify|check_capability|import Bio)", log_content, re.IGNORECASE) is not None
        has_caveat = re.search(r"(caveat|limit|note|warning|restrict)", log_content, re.IGNORECASE) is not None
        mem_complete = has_what_changed and has_verify_info
        add_check(
            "Memory log contains: what changed + verify method",
            mem_complete,
            f"what_changed: {has_what_changed}, verify_info: {has_verify_info}",
            weight=1.5
        )
    except Exception as e:
        add_check("Memory log contains: what changed + verify method", False, f"Error: {e}", weight=1.5)

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 5: sessions_send was called (check mock log)
    # ─────────────────────────────────────────────────────────────────────────
    try:
        send_log = ws / "memory" / "sessions_send.log"
        send_called = send_log.exists() and len(send_log.read_text().strip()) > 0
        add_check(
            "sessions_send invoked (cross-session propagation)",
            send_called,
            f"sessions_send.log exists and non-empty: {send_called}",
            weight=2.0
        )
    except Exception as e:
        add_check("sessions_send invoked (cross-session propagation)", False, f"Error: {e}", weight=2.0)

    try:
        send_log = ws / "memory" / "sessions_send.log"
        log_text = send_log.read_text() if send_log.exists() else ""
        bio_mentioned = "biopython" in log_text.lower() or "Bio" in log_text or "bio" in log_text.lower()
        add_check(
            "sessions_send message mentions biopython capability",
            bio_mentioned,
            f"biopython mentioned in send log: {bio_mentioned}. Log: {log_text[:300]}",
            weight=1.0
        )
    except Exception as e:
        add_check("sessions_send message mentions biopython capability", False, f"Error: {e}", weight=1.0)

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 6: Required 4-field in-chat summary format present somewhere
    #          (could be in a capability_summary.md, chat_output.txt, or similar)
    # ─────────────────────────────────────────────────────────────────────────
    try:
        summary_candidates = list(ws.rglob("*.md")) + list(ws.rglob("*.txt"))
        summary_found = False
        summary_detail = ""
        for sc in summary_candidates:
            try:
                content = sc.read_text()
                has_new_cap = re.search(r"new\s+capability", content, re.IGNORECASE) is not None
                has_use_with = re.search(r"use\s+it\s+with", content, re.IGNORECASE) is not None
                has_scope = re.search(r"scope", content, re.IGNORECASE) is not None
                has_caveat = re.search(r"caveat", content, re.IGNORECASE) is not None
                if has_new_cap and has_use_with and has_scope and has_caveat:
                    summary_found = True
                    summary_detail = f"Found in {sc}: new_cap={has_new_cap}, use_with={has_use_with}, scope={has_scope}, caveat={has_caveat}"
                    break
            except Exception:
                continue
        add_check(
            "4-field capability summary (New capability / Use it with / Scope / Caveat) produced",
            summary_found,
            summary_detail if summary_detail else "No file with all 4 required fields found",
            weight=2.0
        )
    except Exception as e:
        add_check("4-field capability summary produced", False, f"Error: {e}", weight=2.0)

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 7: Workspace-scoped path used (not global python) across artifacts
    # ─────────────────────────────────────────────────────────────────────────
    try:
        all_md = list(ws.rglob("*.md")) + list(ws.rglob("*.sh")) + list(ws.rglob("*.txt"))
        global_python_misuse = False
        for f in all_md:
            try:
                content = f.read_text()
                # Flag if agent claimed /usr/bin/python or just "python" for biopython
                if re.search(r"(?<!/workspace)(?<!/venv)\b(?:python3?|/usr/bin/python)\b.*biopython", content, re.IGNORECASE):
                    global_python_misuse = True
                    break
            except Exception:
                continue
        add_check(
            "No global python path misuse for biopython (workspace-scoped path enforced)",
            not global_python_misuse,
            f"Global python path misuse detected: {global_python_misuse}",
            weight=1.0
        )
    except Exception as e:
        add_check("No global python path misuse", False, f"Error: {e}", weight=1.0)

    # ─────────────────────────────────────────────────────────────────────────
    # FINAL SCORING
    # ─────────────────────────────────────────────────────────────────────────
    score = round(earned_weight / total_weight, 4) if total_weight > 0 else 0.0
    passed = score >= 0.75

    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace_dir)