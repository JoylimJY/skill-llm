import sys
import os
import json
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    workspace_path = Path(workspace)

    # ── Helper ────────────────────────────────────────────────────────────────
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # ═══════════════════════════════════════════════════════════════════════════
    # CHECK 1: .memory-path file exists at workspace ROOT and contains valid path
    # ═══════════════════════════════════════════════════════════════════════════
    memory_path_config = workspace_path / ".memory-path"
    memory_dir = None

    try:
        if memory_path_config.exists():
            raw_path = memory_path_config.read_text(encoding="utf-8").strip()
            if raw_path:
                # Accept both absolute and relative paths
                if os.path.isabs(raw_path):
                    candidate = Path(raw_path)
                else:
                    candidate = workspace_path / raw_path
                
                if candidate.is_dir():
                    memory_dir = candidate
                    add_check(
                        ".memory-path config exists and points to valid directory",
                        True,
                        f"Found .memory-path at workspace root. Points to: {raw_path} (resolved: {candidate})"
                    )
                else:
                    add_check(
                        ".memory-path config exists and points to valid directory",
                        False,
                        f".memory-path exists but the path '{raw_path}' does not point to an existing directory."
                    )
            else:
                add_check(
                    ".memory-path config exists and points to valid directory",
                    False,
                    ".memory-path file is empty."
                )
        else:
            # Fallback: check if default memory/ exists in workspace
            default_memory = workspace_path / "memory"
            if default_memory.is_dir():
                memory_dir = default_memory
                add_check(
                    ".memory-path config exists and points to valid directory",
                    False,
                    "No .memory-path config found at workspace root. A default memory/ directory was found, but the skill requires .memory-path for custom paths. Accepting memory/ as fallback but penalizing."
                )
                # We'll still evaluate the memory directory contents
            else:
                add_check(
                    ".memory-path config exists and points to valid directory",
                    False,
                    "Neither .memory-path config nor default memory/ directory found in workspace root."
                )
    except Exception as e:
        add_check(
            ".memory-path config exists and points to valid directory",
            False,
            f"Error reading .memory-path: {e}"
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # CHECK 2: memory directory has required subdirectories: insights/ and daily/
    # ═══════════════════════════════════════════════════════════════════════════
    if memory_dir is None:
        # Try to find any memory directory anywhere in workspace as last resort
        found = list(workspace_path.rglob("memory"))
        found_dirs = [p for p in found if p.is_dir()]
        if found_dirs:
            memory_dir = found_dirs[0]

    insights_dir = None
    daily_dir = None

    if memory_dir:
        insights_dir = memory_dir / "insights"
        daily_dir = memory_dir / "daily"

        has_insights = insights_dir.is_dir()
        has_daily = daily_dir.is_dir()

        if has_insights and has_daily:
            add_check(
                "memory/ has required subdirectories (insights/ and daily/)",
                True,
                f"Found insights/ and daily/ inside {memory_dir}"
            )
        elif has_insights:
            add_check(
                "memory/ has required subdirectories (insights/ and daily/)",
                False,
                f"Found insights/ but missing daily/ inside {memory_dir}"
            )
        elif has_daily:
            add_check(
                "memory/ has required subdirectories (insights/ and daily/)",
                False,
                f"Found daily/ but missing insights/ inside {memory_dir}"
            )
        else:
            add_check(
                "memory/ has required subdirectories (insights/ and daily/)",
                False,
                f"Neither insights/ nor daily/ found inside {memory_dir}"
            )
    else:
        add_check(
            "memory/ has required subdirectories (insights/ and daily/)",
            False,
            "Cannot check subdirectories because no memory directory was located."
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # CHECK 3: Core identity file 00-概念定义.md exists in memory/ root
    # ═══════════════════════════════════════════════════════════════════════════
    core_identity_file = None
    core_identity_content = ""

    if memory_dir:
        # Must be named exactly 00-概念定义.md
        candidate_identity = memory_dir / "00-概念定义.md"
        if candidate_identity.exists():
            core_identity_file = candidate_identity
            try:
                core_identity_content = candidate_identity.read_text(encoding="utf-8")
                add_check(
                    "Core identity file 00-概念定义.md exists in memory/ root",
                    True,
                    f"Found 00-概念定义.md at {candidate_identity}"
                )
            except Exception as e:
                add_check(
                    "Core identity file 00-概念定义.md exists in memory/ root",
                    False,
                    f"File exists but could not read: {e}"
                )
        else:
            # Check for any approximations that would indicate agent guessed wrong name
            alternatives = list(memory_dir.glob("*.md"))
            alt_names = [f.name for f in alternatives]
            add_check(
                "Core identity file 00-概念定义.md exists in memory/ root",
                False,
                f"00-概念定义.md not found in {memory_dir}. Other .md files found: {alt_names}"
            )
    else:
        add_check(
            "Core identity file 00-概念定义.md exists in memory/ root",
            False,
            "Cannot check: memory directory not found."
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # CHECK 4: 00-概念定义.md has required structural sections
    # (身份/我是 section, 性格 section, 核心原则 section)
    # ═══════════════════════════════════════════════════════════════════════════
    if core_identity_content:
        content_lower = core_identity_content.lower()
        
        # Check for identity section
        has_identity = any(kw in core_identity_content for kw in ["我是", "身份", "identity", "张磊", "zhang lei", "姓名"])
        # Check for personality section  
        has_personality = any(kw in core_identity_content for kw in ["性格", "风格", "style", "personality"])
        # Check for principles section
        has_principles = any(kw in core_identity_content for kw in ["原则", "principle", "核心原则", "方法论"])

        all_sections = has_identity and has_personality and has_principles
        missing = []
        if not has_identity: missing.append("身份/我是 section")
        if not has_personality: missing.append("性格/风格 section")
        if not has_principles: missing.append("核心原则/方法论 section")

        add_check(
            "00-概念定义.md contains required structural sections (identity, personality, principles)",
            all_sections,
            "All required sections present." if all_sections else f"Missing sections: {missing}. Content preview: {core_identity_content[:300]}"
        )
    else:
        add_check(
            "00-概念定义.md contains required structural sections (identity, personality, principles)",
            False,
            "Cannot check sections: file missing or unreadable."
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # CHECK 5: Date-stamped daily records exist in daily/ with correct format
    # (YYYY-MM-DD.md naming)
    # ═══════════════════════════════════════════════════════════════════════════
    import re

    daily_files_valid = []
    if daily_dir and daily_dir.is_dir():
        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")
        all_daily_files = list(daily_dir.glob("*.md"))
        daily_files_valid = [f for f in all_daily_files if date_pattern.match(f.name)]
        
        if len(daily_files_valid) >= 1:
            add_check(
                "daily/ contains date-stamped .md files (YYYY-MM-DD.md format)",
                True,
                f"Found {len(daily_files_valid)} valid date-stamped file(s): {[f.name for f in daily_files_valid]}"
            )
        else:
            other_files = [f.name for f in all_daily_files]
            add_check(
                "daily/ contains date-stamped .md files (YYYY-MM-DD.md format)",
                False,
                f"No files matching YYYY-MM-DD.md pattern found in daily/. Found: {other_files}"
            )
    else:
        add_check(
            "daily/ contains date-stamped .md files (YYYY-MM-DD.md format)",
            False,
            "daily/ directory does not exist or is not a directory."
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # CHECK 6: insights/ directory contains at least one .md file with content
    # ═══════════════════════════════════════════════════════════════════════════
    if insights_dir and insights_dir.is_dir():
        insight_files = list(insights_dir.glob("*.md"))
        non_empty = [f for f in insight_files if f.stat().st_size > 50]
        
        if non_empty:
            add_check(
                "insights/ directory contains substantive .md content",
                True,
                f"Found {len(non_empty)} non-trivial .md file(s) in insights/: {[f.name for f in non_empty]}"
            )
        elif insight_files:
            add_check(
                "insights/ directory contains substantive .md content",
                False,
                f"insights/ has {len(insight_files)} .md file(s) but they appear empty or trivial."
            )
        else:
            add_check(
                "insights/ directory contains substantive .md content",
                False,
                "insights/ directory exists but contains no .md files."
            )
    else:
        add_check(
            "insights/ directory contains substantive .md content",
            False,
            "insights/ directory does not exist."
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # CHECK 7: Daily records contain meaningful content (not just empty stubs)
    # ═══════════════════════════════════════════════════════════════════════════
    if daily_files_valid:
        total_content_length = 0
        has_structured_content = False
        for f in daily_files_valid:
            try:
                content = f.read_text(encoding="utf-8")
                total_content_length += len(content)
                # Check for structured content (headers, bullet points, etc.)
                if any(marker in content for marker in ["##", "- ", "* ", "重要", "洞察", "决定", "insight", "decision"]):
                    has_structured_content = True
            except Exception:
                pass
        
        if total_content_length > 100 and has_structured_content:
            add_check(
                "Daily records contain structured, meaningful content",
                True,
                f"Total content length: {total_content_length} chars. Structured content detected."
            )
        elif total_content_length > 50:
            add_check(
                "Daily records contain structured, meaningful content",
                False,
                f"Daily files have some content ({total_content_length} chars) but lack structured formatting (##, -, etc.)"
            )
        else:
            add_check(
                "Daily records contain structured, meaningful content",
                False,
                f"Daily files appear nearly empty (total {total_content_length} chars)."
            )
    else:
        add_check(
            "Daily records contain structured, meaningful content",
            False,
            "No valid daily files to check."
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # SCORING
    # ═══════════════════════════════════════════════════════════════════════════
    # Weights: .memory-path (critical, 2x), subdirs (1x), identity file (2x), 
    #          sections (1x), daily format (1x), insights content (1x), daily content (1x)
    weights = [2, 1, 2, 1, 1, 1, 1]  # sum = 9
    total_weight = sum(weights)
    
    earned = sum(w for c, w in zip(checks, weights) if c["passed"])
    score = round(earned / total_weight, 4)
    passed = score >= 0.75  # Must pass at least 6.75/9 weighted points

    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "setup", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))