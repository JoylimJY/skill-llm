#!/usr/bin/env python3
"""Evaluation script for agent-harness-engineering task."""
import json
import os
import sys
from pathlib import Path

def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return ""

def check_frontmatter(text: str) -> dict:
    """Return dict of frontmatter keys found."""
    result = {"owner": False, "last_reviewed": False}
    if not text.startswith("---"):
        return result
    end = text.find("---", 3)
    if end == -1:
        return result
    block = text[3:end]
    result["owner"] = "owner:" in block
    result["last_reviewed"] = "last_reviewed:" in block
    return result

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    repo = workspace / "payflow-repo"

    checks = []
    total_score = 0.0

    # ── Check 1: docs/agent/ directory created ──────────────────────────────
    agent_dir = repo / "docs" / "agent"
    ch = {
        "name": "docs/agent/ directory exists",
        "passed": agent_dir.is_dir(),
        "detail": str(agent_dir)
    }
    checks.append(ch)
    if ch["passed"]:
        total_score += 0.5

    # ── Check 2: Required leaf docs exist with frontmatter ───────────────────
    required_docs = [
        "index.md", "architecture.md", "specs.md",
        "plans.md", "quality.md", "reliability.md", "security.md"
    ]
    missing_docs = []
    bad_frontmatter = []
    for name in required_docs:
        p = agent_dir / name
        if not p.exists():
            missing_docs.append(name)
        else:
            text = read_text(p)
            fm = check_frontmatter(text)
            if not (fm["owner"] and fm["last_reviewed"]):
                bad_frontmatter.append(name)

    ch = {
        "name": "All 7 required leaf docs exist",
        "passed": len(missing_docs) == 0,
        "detail": f"Missing: {missing_docs}" if missing_docs else "All present"
    }
    checks.append(ch)
    if ch["passed"]:
        total_score += 1.0

    ch = {
        "name": "All leaf docs have owner + last_reviewed frontmatter",
        "passed": len(bad_frontmatter) == 0,
        "detail": f"Bad frontmatter: {bad_frontmatter}" if bad_frontmatter else "All OK"
    }
    checks.append(ch)
    if ch["passed"]:
        total_score += 1.0

    # ── Check 3: garbage-collection.md created (--with-gc) ──────────────────
    gc_doc = agent_dir / "garbage-collection.md"
    gc_exists = gc_doc.exists()
    ch = {
        "name": "docs/agent/garbage-collection.md exists (--with-gc used)",
        "passed": gc_exists,
        "detail": "Found" if gc_exists else "Missing — agent likely did not use --with-gc flag"
    }
    checks.append(ch)
    if ch["passed"]:
        total_score += 0.75

    # ── Check 4: gc_report script created ───────────────────────────────────
    gc_script = repo / "scripts" / "agent_gc_report.py"
    gc_script_exists = gc_script.exists()
    ch = {
        "name": "scripts/agent_gc_report.py exists",
        "passed": gc_script_exists,
        "detail": "Found" if gc_script_exists else "Missing"
    }
    checks.append(ch)
    if ch["passed"]:
        total_score += 0.5

    # ── Check 5: docs/agent/index.md links to ALL leaf docs including GC ────
    index_text = read_text(agent_dir / "index.md") if (agent_dir / "index.md").exists() else ""
    index_links = {
        "architecture": "architecture.md" in index_text or "architecture" in index_text,
        "specs": "specs.md" in index_text or "specs" in index_text,
        "plans": "plans.md" in index_text or "plans" in index_text,
        "quality": "quality.md" in index_text or "quality" in index_text,
        "reliability": "reliability.md" in index_text or "reliability" in index_text,
        "security": "security.md" in index_text or "security" in index_text,
        "garbage-collection": "garbage-collection" in index_text,
    }
    missing_links = [k for k, v in index_links.items() if not v]
    ch = {
        "name": "index.md links to all leaf docs (including garbage-collection)",
        "passed": len(missing_links) == 0,
        "detail": f"Missing links to: {missing_links}" if missing_links else "All links present"
    }
    checks.append(ch)
    if ch["passed"]:
        total_score += 1.0

    # ── Check 6: AGENTS.md is SHORT (router, not handbook) ──────────────────
    agents_md = repo / "AGENTS.md"
    agents_text = read_text(agents_md)
    line_count = len([l for l in agents_text.splitlines() if l.strip()])
    # Must have nav block and must be significantly shorter than original (~45 non-empty lines)
    has_nav_block = "docs/agent/index.md" in agents_text
    is_short = line_count <= 30  # original had ~45+, router should be much shorter
    ch = {
        "name": "AGENTS.md contains navigation block linking to docs/agent/",
        "passed": has_nav_block,
        "detail": f"Nav link present: {has_nav_block}. Content preview: {agents_text[:200]!r}"
    }
    checks.append(ch)
    if ch["passed"]:
        total_score += 0.75

    ch = {
        "name": "AGENTS.md is concise (≤30 non-empty lines — acts as router, not handbook)",
        "passed": is_short,
        "detail": f"Non-empty lines: {line_count} (must be ≤30)"
    }
    checks.append(ch)
    if ch["passed"]:
        total_score += 0.75

    # ── Check 7: AGENTS.md does NOT duplicate durable content from leaf docs ─
    # Original bloated content keywords that should be moved out
    duplicated_keywords = []
    bloat_phrases = [
        "double-entry accounting",
        "exponential backoff",
        "GCP Secret Manager",
        "alembic revision",
        "REDIS_FALLBACK",
    ]
    for phrase in bloat_phrases:
        if phrase.lower() in agents_text.lower():
            duplicated_keywords.append(phrase)

    ch = {
        "name": "AGENTS.md does not duplicate durable knowledge (moved to leaf docs)",
        "passed": len(duplicated_keywords) == 0,
        "detail": f"Still duplicated in AGENTS.md: {duplicated_keywords}" if duplicated_keywords else "No duplication detected"
    }
    checks.append(ch)
    if ch["passed"]:
        total_score += 0.75

    # ── Check 8: scripts/agent_repo_check.py exists in repo ─────────────────
    check_script = repo / "scripts" / "agent_repo_check.py"
    ch = {
        "name": "scripts/agent_repo_check.py created in repo",
        "passed": check_script.exists(),
        "detail": "Found" if check_script.exists() else "Missing — bootstrap was not run"
    }
    checks.append(ch)
    if ch["passed"]:
        total_score += 0.5

    # ── Check 9: agent_repo_check.py is runnable and passes ─────────────────
    if check_script.exists():
        import subprocess
        try:
            result = subprocess.run(
                ["python3", str(check_script)],
                capture_output=True, text=True, cwd=str(repo), timeout=15
            )
            check_passes = result.returncode == 0
            ch = {
                "name": "scripts/agent_repo_check.py passes (exit 0)",
                "passed": check_passes,
                "detail": f"stdout: {result.stdout.strip()[:300]} stderr: {result.stderr.strip()[:200]}"
            }
        except Exception as e:
            ch = {
                "name": "scripts/agent_repo_check.py passes (exit 0)",
                "passed": False,
                "detail": f"Error running check script: {e}"
            }
    else:
        ch = {
            "name": "scripts/agent_repo_check.py passes (exit 0)",
            "passed": False,
            "detail": "Script does not exist"
        }
    checks.append(ch)
    if ch["passed"]:
        total_score += 1.0

    # ── Check 10: CLAUDE.md symlink created pointing to AGENTS.md ───────────
    claude_md = repo / "CLAUDE.md"
    is_symlink = claude_md.is_symlink()
    symlink_target_ok = False
    if is_symlink:
        try:
            target = os.readlink(str(claude_md))
            symlink_target_ok = target == "AGENTS.md"
        except Exception:
            pass
    ch = {
        "name": "CLAUDE.md is a symlink pointing to AGENTS.md (default behavior)",
        "passed": is_symlink and symlink_target_ok,
        "detail": (
            f"Is symlink: {is_symlink}, target ok: {symlink_target_ok}"
            if is_symlink else "CLAUDE.md does not exist or is not a symlink"
        )
    }
    checks.append(ch)
    if ch["passed"]:
        total_score += 0.5

    # ── Check 11: Makefile check target updated to include agent_repo_check ──
    makefile_text = read_text(repo / "Makefile")
    makefile_wired = "agent_repo_check" in makefile_text
    ch = {
        "name": "Makefile 'check' target wired to run agent_repo_check.py",
        "passed": makefile_wired,
        "detail": "Found agent_repo_check reference in Makefile" if makefile_wired else "Makefile still has placeholder 'TODO: add repo checks here'"
    }
    checks.append(ch)
    if ch["passed"]:
        total_score += 0.5

    # ── Normalize score ──────────────────────────────────────────────────────
    max_score = 10.0
    normalized = round(min(total_score / max_score, 1.0), 3)
    all_passed = all(c["passed"] for c in checks)

    output = {
        "passed": all_passed,
        "score": normalized,
        "checks": checks
    }
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()