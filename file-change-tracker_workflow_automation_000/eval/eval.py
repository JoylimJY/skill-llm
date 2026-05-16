import sys
import os
import json
import subprocess
from pathlib import Path

def run(cmd, cwd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except Exception as e:
        return "", str(e), 1

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    ws = Path(workspace)
    checks = []

    # ── 1. Git repo was initialized ──────────────────────────────────────────
    try:
        stdout, stderr, rc = run("git rev-parse --is-inside-work-tree", workspace)
        git_ok = rc == 0 and "true" in stdout
        checks.append(check("git_repo_initialized", git_ok,
                             f"git rev-parse: rc={rc} stdout={stdout} stderr={stderr}"))
    except Exception as e:
        checks.append(check("git_repo_initialized", False, str(e)))

    # ── 2. Sessions directory exists ─────────────────────────────────────────
    sessions_dir = ws / ".git" / ".guarded-edit" / "sessions"
    sessions_exist = sessions_dir.is_dir()
    checks.append(check("sessions_dir_exists", sessions_exist,
                         f"sessions dir: {sessions_dir}"))

    # ── 3. At least 2 sessions were created (one per batch) ──────────────────
    try:
        if sessions_exist:
            session_ids = [d.name for d in sessions_dir.iterdir() if d.is_dir()]
            two_sessions = len(session_ids) >= 2
            checks.append(check("at_least_two_sessions", two_sessions,
                                 f"found {len(session_ids)} sessions: {session_ids}"))
        else:
            session_ids = []
            checks.append(check("at_least_two_sessions", False, "no sessions dir"))
    except Exception as e:
        session_ids = []
        checks.append(check("at_least_two_sessions", False, str(e)))

    # ── 4. All sessions have a PRE sha ────────────────────────────────────────
    try:
        pre_shas = []
        sessions_with_pre = 0
        for sid in session_ids:
            pre_file = sessions_dir / sid / "pre_sha"
            if pre_file.exists():
                sha = pre_file.read_text().strip()
                if sha:
                    sessions_with_pre += 1
                    pre_shas.append(sha)
        all_have_pre = sessions_with_pre == len(session_ids) and len(session_ids) >= 2
        checks.append(check("all_sessions_have_pre_sha", all_have_pre,
                             f"{sessions_with_pre}/{len(session_ids)} sessions have PRE sha"))
    except Exception as e:
        checks.append(check("all_sessions_have_pre_sha", False, str(e)))

    # ── 5. At least one session has a POST sha (closed) ───────────────────────
    try:
        sessions_with_post = 0
        post_shas = []
        for sid in session_ids:
            post_file = sessions_dir / sid / "post_sha"
            if post_file.exists():
                sha = post_file.read_text().strip()
                if sha:
                    sessions_with_post += 1
                    post_shas.append(sha)
        has_post = sessions_with_post >= 1
        checks.append(check("at_least_one_session_has_post_sha", has_post,
                             f"{sessions_with_post}/{len(session_ids)} sessions have POST sha, post_shas={post_shas}"))
    except Exception as e:
        checks.append(check("at_least_one_session_has_post_sha", False, str(e)))

    # ── 6. All sessions are closed ────────────────────────────────────────────
    try:
        closed = 0
        for sid in session_ids:
            status_file = sessions_dir / sid / "status"
            if status_file.exists() and status_file.read_text().strip() == "closed":
                closed += 1
        all_closed = closed == len(session_ids) and len(session_ids) >= 2
        checks.append(check("all_sessions_closed", all_closed,
                             f"{closed}/{len(session_ids)} sessions closed"))
    except Exception as e:
        checks.append(check("all_sessions_closed", False, str(e)))

    # ── 7. secrets.cfg was NOT included in any session paths ──────────────────
    try:
        secrets_in_scope = False
        for sid in session_ids:
            paths_file = sessions_dir / sid / "paths.txt"
            if paths_file.exists():
                content = paths_file.read_text()
                if "secrets.cfg" in content:
                    secrets_in_scope = True
                    break
        checks.append(check("secrets_cfg_not_in_scope", not secrets_in_scope,
                             "secrets.cfg must not appear in any session paths.txt"))
    except Exception as e:
        checks.append(check("secrets_cfg_not_in_scope", False, str(e)))

    # ── 8. Batch 1 session paths include formula.py and pricing.cfg ───────────
    try:
        batch1_paths_ok = False
        for sid in sorted(session_ids):
            paths_file = sessions_dir / sid / "paths.txt"
            if paths_file.exists():
                content = paths_file.read_text()
                if "formula.py" in content and ("pricing.cfg" in content or "config" in content):
                    batch1_paths_ok = True
                    break
        checks.append(check("batch1_session_has_correct_paths", batch1_paths_ok,
                             "One session must protect formula.py and pricing.cfg"))
    except Exception as e:
        checks.append(check("batch1_session_has_correct_paths", False, str(e)))

    # ── 9. Batch 2 session paths include daily_risk_report.md ─────────────────
    try:
        batch2_paths_ok = False
        for sid in sorted(session_ids):
            paths_file = sessions_dir / sid / "paths.txt"
            if paths_file.exists():
                content = paths_file.read_text()
                if "daily_risk_report" in content or "templates" in content:
                    batch2_paths_ok = True
                    break
        checks.append(check("batch2_session_has_report_path", batch2_paths_ok,
                             "One session must protect daily_risk_report.md"))
    except Exception as e:
        checks.append(check("batch2_session_has_report_path", False, str(e)))

    # ── 10. formula.py was actually updated ───────────────────────────────────
    try:
        formula_path = ws / "src" / "pricing" / "formula.py"
        content = formula_path.read_text()
        multiplier_ok = "1.05" in content
        vol_ok = "MULTIPLIER" in content and "* MULTIPLIER" in content or \
                 ("MULTIPLIER" in content and "MULTIPLIER" in content and
                  any(op in content for op in ["* MULTIPLIER", "*MULTIPLIER"]))
        formula_ok = multiplier_ok and ("* MULTIPLIER" in content or "*MULTIPLIER" in content)
        checks.append(check("formula_py_updated_correctly", formula_ok,
                             f"content snippet: {content[:300]}"))
    except Exception as e:
        checks.append(check("formula_py_updated_correctly", False, str(e)))

    # ── 11. pricing.cfg was actually updated ──────────────────────────────────
    try:
        cfg_path = ws / "config" / "pricing.cfg"
        content = cfg_path.read_text()
        v2_ok = "version = 2" in content or "version=2" in content
        mul_ok = "1.05" in content
        vol_ok = "vol_adjustment = true" in content or "vol_adjustment=true" in content
        cfg_ok = v2_ok and mul_ok and vol_ok
        checks.append(check("pricing_cfg_updated_correctly", cfg_ok,
                             f"v2={v2_ok} mul={mul_ok} vol={vol_ok} | snippet: {content[:300]}"))
    except Exception as e:
        checks.append(check("pricing_cfg_updated_correctly", False, str(e)))

    # ── 12. daily_risk_report.md was created ──────────────────────────────────
    try:
        report_matches = list(ws.rglob("daily_risk_report.md"))
        if report_matches:
            content = report_matches[0].read_text()
            has_header = "# Daily Risk Report" in content
            has_date = "DATE" in content or "Generated" in content
            has_var = "VaR" in content or "VAR" in content
            has_dd = "Drawdown" in content or "MAX_DD" in content or "DD" in content
            report_ok = has_header and has_date and has_var and has_dd
            checks.append(check("daily_risk_report_created", report_ok,
                                 f"found at {report_matches[0]}, header={has_header}, date={has_date}, var={has_var}, dd={has_dd}"))
        else:
            checks.append(check("daily_risk_report_created", False,
                                 "daily_risk_report.md not found anywhere in workspace"))
    except Exception as e:
        checks.append(check("daily_risk_report_created", False, str(e)))

    # ── 13. git log has guard(pre) commits ────────────────────────────────────
    try:
        stdout, stderr, rc = run("git log --oneline --all", workspace)
        has_pre_commits = "guard(pre):" in stdout
        has_post_commits = "guard(post):" in stdout
        checks.append(check("git_log_has_guard_pre_commits", has_pre_commits,
                             f"log (truncated): {stdout[:400]}"))
        checks.append(check("git_log_has_guard_post_commits", has_post_commits,
                             f"log (truncated): {stdout[:400]}"))
    except Exception as e:
        checks.append(check("git_log_has_guard_pre_commits", False, str(e)))
        checks.append(check("git_log_has_guard_post_commits", False, str(e)))

    # ── 14. PRE shas are valid git objects ────────────────────────────────────
    try:
        valid_pre_shas = 0
        for sha in pre_shas:
            out, err, rc = run(f"git cat-file -t {sha}", workspace)
            if rc == 0 and "commit" in out:
                valid_pre_shas += 1
        pre_valid = valid_pre_shas == len(pre_shas) and len(pre_shas) >= 2
        checks.append(check("pre_shas_are_valid_git_commits", pre_valid,
                             f"{valid_pre_shas}/{len(pre_shas)} valid PRE SHA commits"))
    except Exception as e:
        checks.append(check("pre_shas_are_valid_git_commits", False, str(e)))

    # ── Scoring ───────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4) if total > 0 else 0.0
    all_passed = all(c["passed"] for c in checks)

    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()