#!/usr/bin/env python3
import sys
import json
import os
from pathlib import Path

def load_call_log(workspace):
    log_path = Path(workspace) / ".gh_call_log.jsonl"
    calls = []
    if not log_path.exists():
        return calls
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    calls.append(json.loads(line))
                except Exception:
                    pass
    return calls

def check_args_contain(call_args, *tokens):
    """Return True if all tokens appear somewhere in the call args."""
    joined = " ".join(call_args).lower()
    return all(t.lower() in joined for t in tokens)

def main(workspace):
    checks = []
    calls = load_call_log(workspace)
    all_args_lists = [c["args"] for c in calls]

    # ── CHECK 1: Did the agent call `gh repo view` to identify the repo? ──────
    repo_view_called = any(
        a[:2] == ["repo", "view"] for a in all_args_lists
    )
    checks.append({
        "name": "called_gh_repo_view",
        "passed": repo_view_called,
        "detail": "Agent must run `gh repo view` to identify the target repo." if not repo_view_called
                  else "✓ `gh repo view` was called."
    })

    # ── CHECK 2: Did the agent run `gh search issues` against the correct repo? ─
    issue_search_calls = [a for a in all_args_lists if len(a) >= 2 and a[0] == "search" and a[1] == "issues"]
    issue_search_correct_repo = any(
        "openforge/dbmigrate" in " ".join(a) for a in issue_search_calls
    )
    checks.append({
        "name": "searched_issues_correct_repo",
        "passed": bool(issue_search_calls) and issue_search_correct_repo,
        "detail": "Agent must run `gh search issues --repo openforge/dbmigrate ...`." if not (issue_search_calls and issue_search_correct_repo)
                  else f"✓ Issue search on correct repo called {len(issue_search_calls)} time(s)."
    })

    # ── CHECK 3: Did the agent run `gh search prs` against the correct repo? ───
    pr_search_calls = [a for a in all_args_lists if len(a) >= 2 and a[0] == "search" and a[1] == "prs"]
    pr_search_correct_repo = any(
        "openforge/dbmigrate" in " ".join(a) for a in pr_search_calls
    )
    checks.append({
        "name": "searched_prs_correct_repo",
        "passed": bool(pr_search_calls) and pr_search_correct_repo,
        "detail": "Agent must run BOTH `gh search issues` AND `gh search prs`. PR search missing or wrong repo." if not (pr_search_calls and pr_search_correct_repo)
                  else f"✓ PR search on correct repo called {len(pr_search_calls)} time(s)."
    })

    # ── CHECK 4: Did the agent strip filler words from search keywords? ────────
    # The filler words per SKILL.md: the, a, is, for, with, this, that, when, not, but, and, from
    FILLER_WORDS = {"the", "a", "is", "for", "with", "this", "that", "when", "not", "but", "and", "from"}
    all_search_calls = issue_search_calls + pr_search_calls
    filler_found_in_search = False
    filler_detail = "✓ No filler words detected in search queries."
    for call_args in all_search_calls:
        # Extract the keyword tokens (those not starting with --)
        keyword_tokens = [
            tok.lower() for tok in call_args[2:]
            if not tok.startswith("--") and tok != "openforge/dbmigrate"
        ]
        # Check each individual token against filler words
        for token in keyword_tokens:
            # strip quotes
            clean = token.strip('"').strip("'")
            # split if it's a quoted multi-word string
            sub_tokens = clean.split()
            for st in sub_tokens:
                if st.lower() in FILLER_WORDS:
                    filler_found_in_search = True
                    filler_detail = f"✗ Filler word '{st}' found in search query args: {call_args}"
                    break
    checks.append({
        "name": "filler_words_stripped_from_search",
        "passed": not filler_found_in_search,
        "detail": filler_detail
    })

    # ── CHECK 5: Did the agent view at least one related issue in detail? ──────
    issue_view_calls = [a for a in all_args_lists if len(a) >= 2 and a[0] == "issue" and a[1] == "view"]
    # Must have viewed issue 342 (the primary match)
    viewed_342 = any(
        "342" in " ".join(a) for a in issue_view_calls
    )
    checks.append({
        "name": "viewed_issue_342_detail",
        "passed": viewed_342,
        "detail": "Agent must open issue #342 (primary match) to read its details." if not viewed_342
                  else "✓ Issue #342 was inspected in detail."
    })

    # ── CHECK 6: Did the agent produce the triage_report.md file? ─────────────
    report_files = list(Path(workspace).rglob("triage_report.md"))
    report_exists = len(report_files) > 0
    report_path = report_files[0] if report_files else None
    checks.append({
        "name": "triage_report_md_exists",
        "passed": report_exists,
        "detail": "triage_report.md not found anywhere in the workspace." if not report_exists
                  else f"✓ triage_report.md found at {report_path}."
    })

    if not report_exists:
        # Can't do further checks
        score = sum(1 for c in checks if c["passed"]) / len(checks)
        return {"passed": False, "score": round(score, 2), "checks": checks}

    # ── READ the report ────────────────────────────────────────────────────────
    try:
        report_content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({
            "name": "triage_report_readable",
            "passed": False,
            "detail": f"Could not read triage_report.md: {e}"
        })
        score = sum(1 for c in checks if c["passed"]) / len(checks)
        return {"passed": False, "score": round(score, 2), "checks": checks}

    report_lower = report_content.lower()

    # ── CHECK 7: Report mentions issue #342 ────────────────────────────────────
    mentions_342 = "#342" in report_content or "342" in report_content
    checks.append({
        "name": "report_mentions_issue_342",
        "passed": mentions_342,
        "detail": "triage_report.md must mention issue #342 (Connection pool exhausted under high load)." if not mentions_342
                  else "✓ Report mentions #342."
    })

    # ── CHECK 8: Report mentions the found threads format (SKILL.md §5) ───────
    # Must show at least one thread with #NUMBER style
    import re
    thread_pattern = re.search(r'#\d{3}', report_content)
    has_thread_listing = bool(thread_pattern)
    checks.append({
        "name": "report_lists_found_threads",
        "passed": has_thread_listing,
        "detail": "Report must list found threads in #NUMBER format per SKILL.md §5." if not has_thread_listing
                  else "✓ Report lists threads with #NUMBER references."
    })

    # ── CHECK 9: Report recommends commenting on existing thread (not creating new) ──
    # Per decision table: "Existing open thread covers your exact topic → Comment there"
    recommends_comment = any(word in report_lower for word in [
        "comment", "contribute to", "add to", "reply", "respond to existing"
    ])
    discourages_new = any(phrase in report_lower for phrase in [
        "do not create", "don't create", "avoid creating", "instead of creating",
        "no need to create", "not create", "existing thread", "existing issue",
        "comment on", "comment there"
    ])
    recommendation_correct = recommends_comment or discourages_new
    checks.append({
        "name": "report_recommends_comment_not_new_issue",
        "passed": recommendation_correct,
        "detail": "Report must recommend commenting on the existing open thread (#342) rather than creating a new issue." if not recommendation_correct
                  else "✓ Report correctly recommends engaging with existing thread."
    })

    # ── CHECK 10: Report covers both issues and PRs found ─────────────────────
    # Must mention the open PR #355 as well
    mentions_pr = "#355" in report_content or "355" in report_content or "pr" in report_lower
    checks.append({
        "name": "report_covers_prs_too",
        "passed": mentions_pr,
        "detail": "Report must also cover the PR search results (e.g., PR #355)." if not mentions_pr
                  else "✓ Report covers PR search results."
    })

    # ── FINAL SCORING ──────────────────────────────────────────────────────────
    num_passed = sum(1 for c in checks if c["passed"])
    score = round(num_passed / len(checks), 2)
    # Task passes only if core functional checks pass
    core_checks = [
        "called_gh_repo_view",
        "searched_issues_correct_repo",
        "searched_prs_correct_repo",
        "filler_words_stripped_from_search",
        "viewed_issue_342_detail",
        "triage_report_md_exists",
        "report_mentions_issue_342",
        "report_recommends_comment_not_new_issue",
    ]
    core_passed = all(
        c["passed"] for c in checks if c["name"] in core_checks
    )
    return {
        "passed": core_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = main(workspace)
    print(json.dumps(result, indent=2))