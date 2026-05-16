#!/usr/bin/env python3
"""
Evaluation script for the memory-archiver skill task.
Checks:
1. Daily memory file for 2026-03-23 exists at the correct path with correct tag usage
2. Excluded entries (trivial, private, volatile, duplicate) are NOT present
3. Required entries ARE present with correct tags
4. MEMORY.md has been updated with the long-term worthy entry (CI/CD migration)
5. No duplicate of already-recorded Next.js entry in today's daily file
"""

import sys
import json
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/root/.openclaw/workspace")
    # Resolve home-relative path
    home = Path("/root")
    openclaw_workspace = home / ".openclaw" / "workspace"

    checks = []

    # ── Check 1: Today's daily memory file exists ─────────────────────────────
    daily_path = openclaw_workspace / "memory" / "daily" / "2026-03-23.md"
    try:
        daily_content = daily_path.read_text(encoding="utf-8")
        checks.append(check(
            "daily_file_exists",
            True,
            f"Found daily memory file at {daily_path}"
        ))
    except FileNotFoundError:
        checks.append(check(
            "daily_file_exists",
            False,
            f"Daily memory file NOT found at {daily_path}. Agent may have written to wrong path."
        ))
        # Cannot continue without the file
        result = {
            "passed": False,
            "score": 0.0,
            "checks": checks + [
                check("tag_usage", False, "Cannot check - file missing"),
                check("required_episodic_redis_fix", False, "Cannot check - file missing"),
                check("required_semantic_authjs", False, "Cannot check - file missing"),
                check("required_procedural_authjs_steps", False, "Cannot check - file missing"),
                check("required_semantic_error_codes", False, "Cannot check - file missing"),
                check("required_procedural_db_pool", False, "Cannot check - file missing"),
                check("excluded_trivial_coffee", False, "Cannot check - file missing"),
                check("excluded_private_hiking", False, "Cannot check - file missing"),
                check("excluded_volatile_bun", False, "Cannot check - file missing"),
                check("excluded_duplicate_nextjs", False, "Cannot check - file missing"),
                check("memory_md_updated_cicd", False, "Cannot check - file missing"),
            ]
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # ── Check 2: Correct tag types are used (all three must appear) ───────────
    has_episodic = bool(re.search(r'\[episodic\]', daily_content))
    has_semantic = bool(re.search(r'\[semantic\]', daily_content))
    has_procedural = bool(re.search(r'\[procedural\]', daily_content))
    all_tags = has_episodic and has_semantic and has_procedural
    checks.append(check(
        "tag_usage",
        all_tags,
        f"Tags found - [episodic]: {has_episodic}, [semantic]: {has_semantic}, [procedural]: {has_procedural}. All three required."
    ))

    # ── Check 3: Required episodic entry - Redis cache key fix ─────────────────
    redis_keywords = ["redis", "缓存", "cache", "user:session"]
    redis_episodic = any(
        kw.lower() in daily_content.lower()
        for kw in redis_keywords
    ) and re.search(r'\[episodic\].*?(redis|缓存|cache|user:session)', daily_content, re.IGNORECASE | re.DOTALL)
    # More flexible: check redis content exists with any tag nearby
    redis_present = any(kw.lower() in daily_content.lower() for kw in ["redis", "缓存键", "user:session"])
    checks.append(check(
        "required_episodic_redis_fix",
        redis_present,
        f"Redis cache key fix entry {'found' if redis_present else 'NOT found'} in daily memory. This was a completed fix event."
    ))

    # ── Check 4: Required semantic - Auth.js migration decision ────────────────
    authjs_keywords = ["auth.js", "nextauth", "next-auth", "authentication", "认证", "auth"]
    authjs_present = any(kw.lower() in daily_content.lower() for kw in authjs_keywords)
    checks.append(check(
        "required_semantic_authjs",
        authjs_present,
        f"Auth.js/NextAuth migration decision {'found' if authjs_present else 'NOT found'} in daily memory."
    ))

    # ── Check 5: Required procedural - Auth.js configuration steps ─────────────
    # Should have step-by-step auth config
    authjs_steps_present = bool(re.search(
        r'\[procedural\].*?(next-auth|auth\.js|auth\.config|middleware|callbacks)',
        daily_content, re.IGNORECASE | re.DOTALL
    ))
    # Fallback: just check for numbered steps near auth content
    if not authjs_steps_present:
        authjs_steps_present = bool(re.search(
            r'(1\.|步骤).*(auth|jwt|next-auth)',
            daily_content, re.IGNORECASE | re.DOTALL
        ))
    checks.append(check(
        "required_procedural_authjs_steps",
        authjs_steps_present,
        f"Auth.js configuration procedure {'found' if authjs_steps_present else 'NOT found'} in daily memory."
    ))

    # ── Check 6: Required semantic - tRPC error code standards ─────────────────
    error_code_keywords = ["trpc", "tRPCError", "错误码", "error", "NOT_FOUND", "UNAUTHORIZED"]
    error_semantic = any(kw.lower() in daily_content.lower() for kw in ["trpcerror", "not_found", "unauthorized", "错误码", "错误处理规范"])
    checks.append(check(
        "required_semantic_error_codes",
        error_semantic,
        f"tRPC error code standards {'found' if error_semantic else 'NOT found'} in daily memory."
    ))

    # ── Check 7: Required semantic/procedural - DB pool config ─────────────────
    db_pool_keywords = ["pool", "连接池", "max connections", "connection pool", "db/index"]
    db_pool_present = any(kw.lower() in daily_content.lower() for kw in db_pool_keywords)
    checks.append(check(
        "required_procedural_db_pool",
        db_pool_present,
        f"Database connection pool config {'found' if db_pool_present else 'NOT found'} in daily memory."
    ))

    # ── Check 8: Branch naming convention ──────────────────────────────────────
    branch_keywords = ["feat/", "分支", "branch", "JIRA"]
    branch_present = any(kw.lower() in daily_content.lower() for kw in branch_keywords)
    checks.append(check(
        "required_semantic_branch_naming",
        branch_present,
        f"Branch naming convention update {'found' if branch_present else 'NOT found'} in daily memory."
    ))

    # ── Check 9: EXCLUDED - trivial/private content NOT present ───────────────
    coffee_present = bool(re.search(r'咖啡|coffee|喝了', daily_content, re.IGNORECASE))
    checks.append(check(
        "excluded_trivial_coffee",
        not coffee_present,
        f"Trivial 'coffee' entry {'INCORRECTLY included' if coffee_present else 'correctly excluded'} from daily memory."
    ))

    hiking_present = bool(re.search(r'爬山|hiking|山|心情|周末', daily_content, re.IGNORECASE))
    checks.append(check(
        "excluded_private_hiking",
        not hiking_present,
        f"Private 'hiking/weekend mood' entry {'INCORRECTLY included' if hiking_present else 'correctly excluded'} from daily memory."
    ))

    # ── Check 10: EXCLUDED - volatile idea (Bun runtime) ─────────────────────
    bun_present = bool(re.search(r'\bbun\b|Bun 作为|试试 Bun', daily_content, re.IGNORECASE))
    checks.append(check(
        "excluded_volatile_bun",
        not bun_present,
        f"Volatile 'try Bun runtime' idea {'INCORRECTLY included' if bun_present else 'correctly excluded'} from daily memory."
    ))

    # ── Check 11: EXCLUDED - duplicate Next.js entry ──────────────────────────
    # The notes say "已经记录过：项目使用 Next.js 14 + TypeScript [DUPLICATE]"
    # The agent should NOT re-record this since it's already in yesterday's daily
    # We allow some tolerance: if they wrote it, penalize but don't fail completely
    # Check for exact duplicate phrasing
    nextjs_dup_patterns = [
        r'Next\.js 14.*TypeScript',
        r'TypeScript.*Next\.js 14',
    ]
    nextjs_dup_present = any(
        bool(re.search(p, daily_content, re.IGNORECASE))
        for p in nextjs_dup_patterns
    )
    checks.append(check(
        "excluded_duplicate_nextjs",
        not nextjs_dup_present,
        f"Duplicate Next.js 14 + TypeScript entry {'INCORRECTLY included' if nextjs_dup_present else 'correctly excluded'} from today's daily (already in yesterday's memory)."
    ))

    # ── Check 12: EXCLUDED - meeting with no conclusion ───────────────────────
    no_conclusion_present = bool(re.search(r'没有结论|无结论|no conclusion|讨论.*功能', daily_content, re.IGNORECASE))
    checks.append(check(
        "excluded_no_conclusion_meeting",
        not no_conclusion_present,
        f"'Meeting with no conclusion' entry {'INCORRECTLY included' if no_conclusion_present else 'correctly excluded'} from daily memory."
    ))

    # ── Check 13: MEMORY.md updated with CI/CD pipeline migration ─────────────
    memory_md_path = openclaw_workspace / "MEMORY.md"
    try:
        memory_content = memory_md_path.read_text(encoding="utf-8")
        # CI/CD migration is a long-term worthy entry (infrastructure improvement, 60% time reduction)
        cicd_keywords = ["jenkins", "ci/cd", "cicd", "CI/CD", "流水线", "pipeline", "github actions", "构建时间", "build time"]
        cicd_in_memory = any(kw.lower() in memory_content.lower() for kw in cicd_keywords)
        checks.append(check(
            "memory_md_updated_cicd",
            cicd_in_memory,
            f"CI/CD pipeline migration (infrastructure improvement) {'found' if cicd_in_memory else 'NOT found'} in MEMORY.md long-term memory. This is a significant infrastructure win worth long-term recording."
        ))
    except FileNotFoundError:
        checks.append(check(
            "memory_md_updated_cicd",
            False,
            "MEMORY.md not found. Agent may have deleted the long-term memory file."
        ))

    # ── Scoring ───────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])

    # Weight the checks: critical checks matter more
    critical_checks = [
        "daily_file_exists",
        "tag_usage",
        "excluded_trivial_coffee",
        "excluded_private_hiking",
        "excluded_volatile_bun",
        "excluded_duplicate_nextjs",
        "memory_md_updated_cicd",
    ]
    important_checks = [
        "required_episodic_redis_fix",
        "required_semantic_authjs",
        "required_procedural_authjs_steps",
        "required_semantic_error_codes",
    ]

    score = 0.0
    max_score = 0.0

    for c in checks:
        if c["name"] in critical_checks:
            weight = 2.0
        elif c["name"] in important_checks:
            weight = 1.5
        else:
            weight = 1.0
        max_score += weight
        if c["passed"]:
            score += weight

    normalized_score = round(score / max_score, 3) if max_score > 0 else 0.0

    # Must pass all critical checks to be considered "passed"
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )
    # Must pass at least 70% of total weighted score
    overall_passed = critical_passed and normalized_score >= 0.70

    result = {
        "passed": overall_passed,
        "score": normalized_score,
        "checks": checks
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()