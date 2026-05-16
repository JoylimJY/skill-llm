#!/usr/bin/env python3
"""
Evaluation script for changelog-curator task.
Usage: python3 eval.py <workspace_dir>
"""
import sys
import json
import re
import os
from pathlib import Path

def find_output_file(workspace: str) -> Path | None:
    """Search for changelog_v2.4.0.md anywhere in the workspace."""
    candidates = list(Path(workspace).rglob("changelog_v2.4.0.md"))
    if candidates:
        return candidates[0]
    return None

def run_checks(workspace: str) -> dict:
    checks = []
    total_weight = 0
    passed_weight = 0

    def add_check(name: str, passed: bool, detail: str, weight: float = 1.0):
        nonlocal total_weight, passed_weight
        checks.append({"name": name, "passed": passed, "detail": detail})
        total_weight += weight
        if passed:
            passed_weight += weight

    # ── Check 0: Output file exists ──────────────────────────────────────────
    output_file = find_output_file(workspace)
    file_exists = output_file is not None
    add_check(
        "output_file_exists",
        file_exists,
        f"Found: {output_file}" if file_exists else "changelog_v2.4.0.md not found anywhere in workspace.",
        weight=2.0
    )

    if not file_exists:
        # Can't do further checks
        for _ in range(10):
            checks.append({"name": "skipped_no_file", "passed": False, "detail": "File missing."})
        score = passed_weight / total_weight if total_weight > 0 else 0.0
        return {"passed": False, "score": round(score, 3), "checks": checks}

    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        add_check("file_readable", False, f"Could not read file: {e}", weight=2.0)
        score = passed_weight / total_weight if total_weight > 0 else 0.0
        return {"passed": False, "score": round(score, 3), "checks": checks}

    add_check("file_readable", True, "File read successfully.", weight=0.5)

    # ── Check 1: Version header format ───────────────────────────────────────
    # Must match: ## [2.4.0] - 2025-07-18
    header_pattern = r"##\s*\[2\.4\.0\]\s*-\s*2025-07-18"
    header_ok = bool(re.search(header_pattern, content))
    add_check(
        "version_header_format",
        header_ok,
        f"Expected '## [2.4.0] - 2025-07-18'. Found match: {header_ok}. "
        f"(spec rule: version_header_format = '## [{{version}}] - {{date}}')",
        weight=2.0
    )

    # ── Check 2: All 6 required sections present ─────────────────────────────
    required_sections = [
        "版本摘要", "用户可感知变化", "内部改进",
        "兼容性注意", "升级建议", "已知限制"
    ]
    missing_sections = []
    for sec in required_sections:
        if sec not in content:
            missing_sections.append(sec)
    sections_ok = len(missing_sections) == 0
    add_check(
        "all_six_sections_present",
        sections_ok,
        f"Missing sections: {missing_sections}" if missing_sections else "All 6 sections found.",
        weight=2.0
    )

    # ── Check 3: "待确认项" section present ──────────────────────────────────
    pending_section_ok = "待确认项" in content
    add_check(
        "pending_confirmation_section_present",
        pending_section_ok,
        "Section '待确认项' found." if pending_section_ok else "Section '待确认项' not found (required by spec for ambiguous/missing-scope commits).",
        weight=1.5
    )

    # ── Check 4: User-facing commits correctly classified ────────────────────
    # feat, fix, perf, security, deprecate => user_facing
    # Must appear in 用户可感知变化 section
    user_facing_keywords = [
        "Webhook 事件订阅",           # feat(webhooks)
        "速率限制",                   # fix(ratelimit)
        "全文搜索",                   # perf(search)
        "JWT 令牌泄漏",               # security(tokens) -- CVE
        "API 使用量",                 # feat(dashboard)
        "v1/users",                   # deprecate(v1-api)
        "OAuth2 PKCE",                # fix(auth)
        "复合索引",                   # perf(db)
    ]
    # Find the user-facing section content
    uf_section_match = re.search(
        r"###?\s*用户可感知变化(.*?)(?=###|\Z)", content, re.DOTALL
    )
    uf_content = uf_section_match.group(1) if uf_section_match else ""

    found_uf = [kw for kw in user_facing_keywords if kw in uf_content]
    missed_uf = [kw for kw in user_facing_keywords if kw not in uf_content]

    # At least 6 out of 8 must be in user-facing section
    uf_ok = len(found_uf) >= 6
    add_check(
        "user_facing_commits_classified",
        uf_ok,
        f"Found {len(found_uf)}/8 expected user-facing items in 用户可感知变化. "
        f"Missed: {missed_uf}",
        weight=2.5
    )

    # ── Check 5: Internal commits correctly classified ────────────────────────
    # chore, refactor, test, ci, build, style, docs-internal => internal
    internal_section_match = re.search(
        r"###?\s*内部改进(.*?)(?=###|\Z)", content, re.DOTALL
    )
    internal_content = internal_section_match.group(1) if internal_section_match else ""

    internal_keywords = [
        "pydantic",         # chore(deps)
        "架构决策",          # docs-internal(arch)  OR ADR
        "集成测试",          # test(webhooks)
        "Docker",           # build(docker)
        "SAST",             # ci(pipeline)
        "black",            # style(formatter)
    ]
    found_internal = [kw for kw in internal_keywords if kw in internal_content]
    missed_internal = [kw for kw in internal_keywords if kw not in internal_content]

    # At least 4 out of 6 must be in internal section
    internal_ok = len(found_internal) >= 4
    add_check(
        "internal_commits_classified",
        internal_ok,
        f"Found {len(found_internal)}/6 expected internal items in 内部改进. "
        f"Missed: {missed_internal}",
        weight=2.0
    )

    # ── Check 6: Missing-scope commits go to 待确认项 ─────────────────────────
    # Two commits have empty scope:
    #   type=refactor scope=  message=重构认证中间件
    #   type=feat     scope=  message=支持通过环境变量覆盖全局超时配置
    # Per spec rule: missing_scope_action = "list_under_pending_confirmation"
    pending_section_match = re.search(
        r"###?\s*待确认项(.*?)(?=###|\Z)", content, re.DOTALL
    )
    pending_content = pending_section_match.group(1) if pending_section_match else ""

    missing_scope_1 = "认证中间件" in pending_content or "中间件" in pending_content
    missing_scope_2 = "超时配置" in pending_content or "全局超时" in pending_content
    ambiguous_revert = "billing" in pending_content or "回滚" in pending_content
    ambiguous_merge  = "release/2.4.0" in pending_content or "Merge" in pending_content or "合并" in pending_content
    unknown_type     = "批处理" in pending_content or "夜间" in pending_content or "临时禁用" in pending_content

    pending_hits = sum([missing_scope_1, missing_scope_2, ambiguous_revert,
                        ambiguous_merge, unknown_type])
    pending_ok = pending_hits >= 3  # at least 3 of 5 ambiguous/missing items in pending

    add_check(
        "pending_confirmation_correct_items",
        pending_ok,
        f"Pending section correctness: missing_scope_refactor={missing_scope_1}, "
        f"missing_scope_feat={missing_scope_2}, revert_billing={ambiguous_revert}, "
        f"merge={ambiguous_merge}, unknown_type={unknown_type}. "
        f"Score: {pending_hits}/5 (need >=3).",
        weight=2.5
    )

    # ── Check 7: Known limitations present ───────────────────────────────────
    kl_section_match = re.search(
        r"###?\s*已知限制(.*?)(?=###|\Z)", content, re.DOTALL
    )
    kl_content = kl_section_match.group(1) if kl_section_match else ""
    kl1 = "50" in kl_content or "Webhook" in kl_content
    kl2 = "v1" in kl_content or "废弃" in kl_content or "v3.0" in kl_content
    kl_ok = kl1 and kl2
    add_check(
        "known_limitations_populated",
        kl_ok,
        f"Known limitations: webhook_limit={kl1}, v1_deprecation={kl2}.",
        weight=1.5
    )

    # ── Check 8: Compatibility note contains breaking change ─────────────────
    compat_section_match = re.search(
        r"###?\s*兼容性注意(.*?)(?=###|\Z)", content, re.DOTALL
    )
    compat_content = compat_section_match.group(1) if compat_section_match else ""
    breaking_ok = (
        ("legacy-export" in compat_content or "v1/legacy-export" in compat_content) and
        ("v2/export" in compat_content or "/v2/export" in compat_content)
    )
    add_check(
        "compatibility_breaking_change_noted",
        breaking_ok,
        f"Breaking change (/v1/legacy-export -> /v2/export) mentioned in 兼容性注意: {breaking_ok}.",
        weight=2.0
    )

    # ── Check 9: Upgrade guide present and non-trivial ───────────────────────
    upgrade_section_match = re.search(
        r"###?\s*升级建议(.*?)(?=###|\Z)", content, re.DOTALL
    )
    upgrade_content = upgrade_section_match.group(1) if upgrade_section_match else ""
    upgrade_ok = (
        "legacy-export" in upgrade_content or
        "v2/export" in upgrade_content or
        "JWT" in upgrade_content or
        "安全" in upgrade_content
    )
    add_check(
        "upgrade_guide_non_trivial",
        upgrade_ok,
        f"Upgrade guide contains actionable items (JWT/security or migration path): {upgrade_ok}.",
        weight=1.5
    )

    # ── Check 10: run.py was actually used (check for script invocation artifacts) ──
    # We verify this indirectly: run.py produces a specific rendering style for bullets
    # e.g. "- [feat(webhooks)]" or "- [fix(ratelimit)]" — hallmarked by run.py's format.
    # If the agent bypassed run.py, the format will differ.
    runpy_format = bool(
        re.search(r"-\s*\[feat\(", content) or
        re.search(r"-\s*\[fix\(", content) or
        re.search(r"-\s*\[perf\(", content) or
        re.search(r"-\s*\[security\(", content)
    )
    add_check(
        "runpy_bullet_format_used",
        runpy_format,
        "Bullet format '- [type(scope)]' from run.py detected." if runpy_format
        else "Expected run.py bullet format '- [type(scope)] message' not found. Agent may have bypassed scripts/run.py.",
        weight=2.0
    )

    # ── Final scoring ─────────────────────────────────────────────────────────
    score = passed_weight / total_weight if total_weight > 0 else 0.0
    # Pass threshold: score >= 0.72 AND critical checks pass
    critical_passed = (
        file_exists and
        header_ok and
        sections_ok and
        uf_ok
    )
    overall_passed = critical_passed and score >= 0.72

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "usage_error", "passed": False,
                                      "detail": "No workspace path provided."}]}))
        sys.exit(1)

    workspace = sys.argv[1]
    result = run_checks(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()