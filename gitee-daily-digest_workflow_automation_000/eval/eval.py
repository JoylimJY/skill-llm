import sys
import json
import re
from pathlib import Path

def find_digest_file(workspace: Path):
    """Search for daily_digest.md anywhere in workspace."""
    candidates = list(workspace.rglob("daily_digest.md"))
    if candidates:
        return candidates[0]
    return None

def eval_digest(workspace_str: str):
    workspace = Path(workspace_str)
    checks = []
    total_score = 0.0
    weight_sum = 0.0

    def add_check(name, passed, detail, weight=1.0):
        nonlocal total_score, weight_sum
        checks.append({"name": name, "passed": passed, "detail": detail})
        weight_sum += weight
        if passed:
            total_score += weight

    # ── 1. File existence ──────────────────────────────────────────────────
    digest_path = find_digest_file(workspace)
    file_exists = digest_path is not None
    add_check(
        "file_exists",
        file_exists,
        f"Found at {digest_path}" if file_exists else "daily_digest.md not found anywhere in workspace",
        weight=2.0
    )

    if not file_exists:
        score = 0.0
        result = {
            "passed": False,
            "score": score,
            "checks": checks
        }
        print(json.dumps(result))
        return

    try:
        content = digest_path.read_text(encoding="utf-8")
    except Exception as e:
        add_check("file_readable", False, f"Could not read file: {e}", weight=2.0)
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    add_check("file_readable", True, f"File read successfully ({len(content)} chars)", weight=0.5)

    # ── 2. Header: date and username present ──────────────────────────────
    has_date = bool(re.search(r'2024[-/]0?6[-/]10|June\s+10|jun\s+10', content, re.IGNORECASE))
    # More flexible: accept any date-like string near the header
    has_any_date = bool(re.search(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', content))
    has_username = bool(re.search(r'zhang[_\-\s]?wei', content, re.IGNORECASE))
    add_check(
        "header_username",
        has_username,
        "Username 'zhang_wei' present in digest" if has_username else "Missing username 'zhang_wei' in header",
        weight=1.0
    )
    add_check(
        "header_date",
        has_any_date,
        "Date field present in digest" if has_any_date else "No date found in digest",
        weight=0.5
    )

    # ── 3. Unread Notifications section exists and has correct count ──────
    has_notif_section = bool(re.search(r'(unread\s+notification|📬)', content, re.IGNORECASE))
    add_check(
        "notifications_section_exists",
        has_notif_section,
        "Notifications section (📬) found" if has_notif_section else "Missing notifications section",
        weight=1.5
    )

    # Should have exactly 4 unread (notif_005 is read, must be excluded)
    # Check that only unread items appear — look for "Old resolved issue" which is read
    old_resolved_present = bool(re.search(r'Old resolved issue', content, re.IGNORECASE))
    add_check(
        "unread_filter_applied",
        not old_resolved_present,
        "Read notification 'Old resolved issue' correctly excluded" if not old_resolved_present
        else "FAIL: Read notification 'Old resolved issue' should NOT appear in digest",
        weight=2.0
    )

    # ── 4. @Mentions category present ─────────────────────────────────────
    has_mentions = bool(re.search(r'@[Mm]ention|mention', content, re.IGNORECASE))
    add_check(
        "mentions_category",
        has_mentions,
        "@Mentions category found in notifications" if has_mentions else "Missing @Mentions category",
        weight=1.0
    )

    # Mention notifications: "Fix: race condition" (PR mention) and "Transaction logs" (Issue mention)
    has_race_condition = bool(re.search(r'race condition', content, re.IGNORECASE))
    add_check(
        "mention_pr_present",
        has_race_condition,
        "PR mention 'race condition' notification found" if has_race_condition else "Missing 'race condition' mention notification",
        weight=1.0
    )

    has_tx_logs = bool(re.search(r'Transaction logs', content, re.IGNORECASE))
    add_check(
        "mention_issue_present",
        has_tx_logs,
        "Issue mention 'Transaction logs' notification found" if has_tx_logs else "Missing 'Transaction logs' mention notification",
        weight=1.0
    )

    # ── 5. PR Comments category ────────────────────────────────────────────
    has_pr_comments = bool(re.search(r'PR\s+[Cc]omment|comment.*PR|comment.*pull', content, re.IGNORECASE))
    add_check(
        "pr_comments_category",
        has_pr_comments,
        "PR Comments category found" if has_pr_comments else "Missing PR Comments category",
        weight=1.0
    )

    # notif_002: "Add KYC validation endpoint" PR comment
    has_kyc_notif = bool(re.search(r'KYC', content, re.IGNORECASE))
    add_check(
        "kyc_pr_comment_notification",
        has_kyc_notif,
        "KYC PR comment notification found" if has_kyc_notif else "Missing KYC PR comment notification",
        weight=1.0
    )

    # ── 6. Pending PRs section ─────────────────────────────────────────────
    has_prs_section = bool(re.search(r'(pending\s+PR|🔀)', content, re.IGNORECASE))
    add_check(
        "prs_section_exists",
        has_prs_section,
        "Pending PRs section (🔀) found" if has_prs_section else "Missing Pending PRs section",
        weight=1.5
    )

    # PR #87 should appear under "Needs My Review" (zhang_wei is reviewer/assignee)
    has_pr87 = bool(re.search(r'#?\s*87', content))
    add_check(
        "pr87_needs_review",
        has_pr87,
        "PR #87 (race condition - needs review) present" if has_pr87 else "Missing PR #87 which needs zhang_wei's review",
        weight=1.5
    )

    # PR #134 is zhang_wei's own PR awaiting review
    has_pr134 = bool(re.search(r'#?\s*134', content))
    add_check(
        "pr134_my_pr",
        has_pr134,
        "PR #134 (KYC, zhang_wei's PR) present" if has_pr134 else "Missing PR #134 (zhang_wei's own PR awaiting review)",
        weight=1.5
    )

    # PR #131 should appear under "Needs My Review"
    has_pr131 = bool(re.search(r'#?\s*131', content))
    add_check(
        "pr131_needs_review",
        has_pr131,
        "PR #131 (rate limiting - assigned to zhang_wei for review) present" if has_pr131 else "Missing PR #131 (needs zhang_wei review)",
        weight=1.0
    )

    # PR table format check
    has_table = bool(re.search(r'\|[-\s|]+\|', content))
    add_check(
        "table_format_prs",
        has_table,
        "Markdown table format used for PRs" if has_table else "Missing markdown table for PRs",
        weight=1.0
    )

    # ── 7. Issues section ─────────────────────────────────────────────────
    has_issues_section = bool(re.search(r'(open\s+issue|my\s+.*issue|📋)', content, re.IGNORECASE))
    add_check(
        "issues_section_exists",
        has_issues_section,
        "Open Issues section (📋) found" if has_issues_section else "Missing Open Issues section",
        weight=1.5
    )

    # Issue I7XK2: assigned to zhang_wei, P1
    has_issue_txlogs = bool(re.search(r'I7XK2|Transaction logs not persisted', content, re.IGNORECASE))
    add_check(
        "issue_I7XK2_present",
        has_issue_txlogs,
        "Issue I7XK2 (Transaction logs, P1, assigned to zhang_wei) present" if has_issue_txlogs
        else "Missing Issue I7XK2 assigned to zhang_wei",
        weight=1.5
    )

    # Issue I9QP1: assigned to zhang_wei, P1
    has_issue_retry = bool(re.search(r'I9QP1|retry logic|Implement retry', content, re.IGNORECASE))
    add_check(
        "issue_I9QP1_present",
        has_issue_retry,
        "Issue I9QP1 (retry logic, P1, assigned to zhang_wei) present" if has_issue_retry
        else "Missing Issue I9QP1 assigned to zhang_wei",
        weight=1.5
    )

    # Issue I6KP5 is NOT assigned to zhang_wei — should NOT be in "My Open Issues"
    has_issue_coverage = bool(re.search(r'I6KP5|Improve test coverage for auth', content, re.IGNORECASE))
    add_check(
        "non_assigned_issue_excluded",
        not has_issue_coverage,
        "Issue I6KP5 (not assigned to zhang_wei) correctly excluded" if not has_issue_coverage
        else "FAIL: Issue I6KP5 not assigned to zhang_wei should NOT appear in My Issues",
        weight=1.5
    )

    # ── 8. Today's Suggestions section ────────────────────────────────────
    has_suggestions = bool(re.search(r"today'?s?\s+suggestion|handle\s+first|suggestion", content, re.IGNORECASE))
    add_check(
        "suggestions_section",
        has_suggestions,
        "Today's Suggestions section found" if has_suggestions else "Missing 'Today's Suggestions' section",
        weight=1.5
    )

    # ── 9. Repos inferred from notifications (not hardcoded) ─────────────
    # Both repos must be covered: payment-gateway and fintech-core
    has_pg_repo = bool(re.search(r'payment.?gateway', content, re.IGNORECASE))
    has_fc_repo = bool(re.search(r'fintech.?core', content, re.IGNORECASE))
    add_check(
        "repo_payment_gateway_covered",
        has_pg_repo,
        "payment-gateway repo content included" if has_pg_repo else "Missing payment-gateway repo (should be inferred from notifications)",
        weight=1.5
    )
    add_check(
        "repo_fintech_core_covered",
        has_fc_repo,
        "fintech-core repo content included" if has_fc_repo else "Missing fintech-core repo (should be inferred from notifications)",
        weight=1.5
    )

    # ── 10. Section emoji headers from SKILL.md template ─────────────────
    has_notif_emoji = "📬" in content
    has_pr_emoji = "🔀" in content
    has_issue_emoji = "📋" in content
    all_emoji = has_notif_emoji and has_pr_emoji and has_issue_emoji
    add_check(
        "section_emojis_present",
        all_emoji,
        f"All section emojis present (📬={has_notif_emoji}, 🔀={has_pr_emoji}, 📋={has_issue_emoji})",
        weight=1.0
    )

    # ── Final scoring ──────────────────────────────────────────────────────
    score = round(total_score / weight_sum, 4) if weight_sum > 0 else 0.0
    passed = score >= 0.75 and file_exists and (not old_resolved_present) and (not has_issue_coverage)

    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    eval_digest(workspace_dir)