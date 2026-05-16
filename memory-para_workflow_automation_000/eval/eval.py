import sys
import json
import re
from pathlib import Path

def load(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except Exception as e:
        return ""

def check(name: str, passed: bool, detail: str) -> dict:
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace: str):
    base = Path(workspace) / ".openclaw/workspace"
    checks = []
    total_score = 0.0
    weights = []

    # ── Helper ───────────────────────────────────────────────────────────────
    def ci_contains(text: str, *fragments) -> bool:
        t = text.lower()
        return all(f.lower() in t for f in fragments)

    # ════════════════════════════════════════════════════════════════════════
    # BLOCK 1: DISTILL — User preferences → USER.md
    # ════════════════════════════════════════════════════════════════════════
    user_md = load(base / "USER.md")

    # 1a. Existing content preserved (not overwritten)
    preserved = "never suggest switching away from python" in user_md.lower() or \
                "python as primary language" in user_md.lower()
    c = check("USER.md: existing content preserved",
              preserved,
              f"Pre-existing hard limit about Python must still be present. Found: {user_md[:300]}")
    checks.append(c); weights.append((c["passed"], 0.08))

    # 1b. New pref: bullet points for 3+ items
    has_bullet_pref = ci_contains(user_md, "bullet") or \
                      ("bullet point" in user_md.lower()) or \
                      ("3 items" in user_md.lower() or "more than 3" in user_md.lower())
    c = check("USER.md: bullet-point preference added",
              has_bullet_pref,
              f"Should contain bullet-point formatting preference from 2024-01-09 log. user_md snippet: {user_md[:500]}")
    checks.append(c); weights.append((c["passed"], 0.07))

    # 1c. New pref: VSCode only
    has_vscode = ci_contains(user_md, "vscode")
    c = check("USER.md: VSCode preference added",
              has_vscode,
              f"Should contain VSCode-exclusive editor preference from 2024-01-10 log.")
    checks.append(c); weights.append((c["passed"], 0.07))

    # 1d. New pref: 4-space indentation
    has_indent = "4-space" in user_md.lower() or "4 space" in user_md.lower() or \
                 "four-space" in user_md.lower() or "four space" in user_md.lower() or \
                 ("indentation" in user_md.lower() and "4" in user_md)
    c = check("USER.md: 4-space indentation preference added",
              has_indent,
              f"Should contain 4-space indentation preference from 2024-01-10 log.")
    checks.append(c); weights.append((c["passed"], 0.07))

    # ════════════════════════════════════════════════════════════════════════
    # BLOCK 2: DISTILL — Agent lessons → SOUL.md
    # ════════════════════════════════════════════════════════════════════════
    soul_md = load(base / "SOUL.md")

    # 2a. Existing content preserved
    soul_preserved = "2024-01-05" in soul_md or "rushing responses" in soul_md.lower()
    c = check("SOUL.md: existing content preserved",
              soul_preserved,
              f"Pre-existing lesson from 2024-01-05 must remain. Found: {soul_md[:300]}")
    checks.append(c); weights.append((c["passed"], 0.06))

    # 2b. New lesson: subprocess.run, not os.system
    has_subprocess_lesson = ci_contains(soul_md, "subprocess") or \
                            ci_contains(soul_md, "os.system")
    c = check("SOUL.md: subprocess safety lesson added",
              has_subprocess_lesson,
              f"Should contain lesson about using subprocess.run instead of os.system.")
    checks.append(c); weights.append((c["passed"], 0.07))

    # 2c. New lesson: read-before-merge for memory files
    has_merge_lesson = ci_contains(soul_md, "merge") or \
                       ci_contains(soul_md, "overwrite") or \
                       ci_contains(soul_md, "read existing") or \
                       ("overwriting" in soul_md.lower() and "areas" in soul_md.lower())
    c = check("SOUL.md: read-before-merge lesson added",
              has_merge_lesson,
              f"Should contain lesson about reading before merging memory files.")
    checks.append(c); weights.append((c["passed"], 0.06))

    # ════════════════════════════════════════════════════════════════════════
    # BLOCK 3: DISTILL — Tool/env config → TOOLS.md
    # ════════════════════════════════════════════════════════════════════════
    tools_md = load(base / "TOOLS.md")

    # 3a. Existing content preserved
    tools_preserved = "ubuntu" in tools_md.lower() or "do not modify system python" in tools_md.lower()
    c = check("TOOLS.md: existing content preserved",
              tools_preserved,
              f"Pre-existing runtime info must remain.")
    checks.append(c); weights.append((c["passed"], 0.05))

    # 3b. Python path added
    has_python_path = "/usr/local/bin/python3.11" in tools_md or \
                      "python3.11" in tools_md.lower()
    c = check("TOOLS.md: Python path added",
              has_python_path,
              f"Should contain clarified Python path from 2024-01-10 log.")
    checks.append(c); weights.append((c["passed"], 0.06))

    # 3c. Workspace root path added
    has_ws_root = "/workspace/.openclaw/workspace" in tools_md or \
                  "workspace root" in tools_md.lower()
    c = check("TOOLS.md: workspace root path added",
              has_ws_root,
              f"Should contain workspace root path from 2024-01-10 log.")
    checks.append(c); weights.append((c["passed"], 0.05))

    # ════════════════════════════════════════════════════════════════════════
    # BLOCK 4: DISTILL — Projects → PROJECTS.md
    # ════════════════════════════════════════════════════════════════════════
    projects_md = load(base / "PARA/PROJECTS.md")

    # 4a. Existing P001 preserved
    p001_preserved = "P001" in projects_md and "cli tool refactor" in projects_md.lower()
    c = check("PROJECTS.md: P001 existing content preserved",
              p001_preserved,
              f"P001 must still exist.")
    checks.append(c); weights.append((c["passed"], 0.05))

    # 4b. P001 updated with subparser progress from 2024-01-09
    p001_subparser = "subparser" in projects_md.lower() or \
                     "subcommand" in projects_md.lower() or \
                     "argparse" in projects_md.lower()
    c = check("PROJECTS.md: P001 updated with subparser milestone",
              p001_subparser,
              f"P001 should reflect subcommand routing progress from 2024-01-09.")
    checks.append(c); weights.append((c["passed"], 0.05))

    # 4c. P001 updated with dry-run milestone from 2024-01-10
    p001_dryrun = "dry-run" in projects_md.lower() or "dry run" in projects_md.lower()
    c = check("PROJECTS.md: P001 updated with dry-run milestone",
              p001_dryrun,
              f"P001 should reflect --dry-run feature completion from 2024-01-10.")
    checks.append(c); weights.append((c["passed"], 0.05))

    # 4d. P002 added
    p002_added = "P002" in projects_md or \
                 "memory maintenance automation" in projects_md.lower() or \
                 "memory" in projects_md.lower() and "automation" in projects_md.lower()
    c = check("PROJECTS.md: P002 new project added",
              p002_added,
              f"P002 Memory Maintenance Automation project must be added from 2024-01-10.")
    checks.append(c); weights.append((c["passed"], 0.06))

    # ════════════════════════════════════════════════════════════════════════
    # BLOCK 5: DISTILL — Domain knowledge → AREAS.md
    # ════════════════════════════════════════════════════════════════════════
    areas_md = load(base / "PARA/AREAS.md")

    # 5a. Existing content preserved
    areas_preserved = "pathlib" in areas_md.lower() or "dataclasses" in areas_md.lower()
    c = check("AREAS.md: existing content preserved",
              areas_preserved,
              f"Pre-existing Python knowledge must remain.")
    checks.append(c); weights.append((c["passed"], 0.05))

    # 5b. Docker networking domain knowledge added
    has_docker = ci_contains(areas_md, "docker") or \
                 ci_contains(areas_md, "bridge network") or \
                 ci_contains(areas_md, "network")
    c = check("AREAS.md: Docker networking knowledge added",
              has_docker,
              f"Docker networking domain knowledge from 2024-01-09 must be added.")
    checks.append(c); weights.append((c["passed"], 0.05))

    # ════════════════════════════════════════════════════════════════════════
    # BLOCK 6: DISTILL — Static references → RESOURCES.md
    # ════════════════════════════════════════════════════════════════════════
    resources_md = load(base / "PARA/RESOURCES.md")

    # 6a. Existing content preserved
    res_preserved = "ripgrep" in resources_md.lower() or "fzf" in resources_md.lower()
    c = check("RESOURCES.md: existing content preserved",
              res_preserved,
              f"Pre-existing tool references must remain.")
    checks.append(c); weights.append((c["passed"], 0.04))

    # 6b. 12factor.net added
    has_12factor = "12factor" in resources_md or "twelve-factor" in resources_md.lower()
    c = check("RESOURCES.md: 12-factor reference added",
              has_12factor,
              f"12factor.net reference from 2024-01-09 must be in RESOURCES.md.")
    checks.append(c); weights.append((c["passed"], 0.04))

    # 6c. Python subprocess docs added
    has_subprocess_ref = "subprocess" in resources_md.lower() and \
                         ("docs.python.org" in resources_md or "python" in resources_md.lower())
    c = check("RESOURCES.md: Python subprocess docs reference added",
              has_subprocess_ref,
              f"Python subprocess docs URL from 2024-01-10 must be in RESOURCES.md.")
    checks.append(c); weights.append((c["passed"], 0.04))

    # ════════════════════════════════════════════════════════════════════════
    # BLOCK 7: ARCHIVE — YYYY-MM-DD.md appended to ARCHIVES
    # ════════════════════════════════════════════════════════════════════════

    # 7a. ARCHIVES/2024-01-09.md exists and contains content from the log
    arch_09 = load(base / "PARA/ARCHIVES/2024-01-09.md")
    arch_09_ok = "2024-01-09" in arch_09 or \
                 "argparse" in arch_09.lower() or \
                 "bullet" in arch_09.lower() or \
                 "12factor" in arch_09.lower()
    c = check("ARCHIVES/2024-01-09.md: log archived",
              arch_09_ok,
              f"2024-01-09.md should be archived. Found: {arch_09[:200]}")
    checks.append(c); weights.append((c["passed"], 0.04))

    # 7b. ARCHIVES/2024-01-10.md exists and contains content from the log
    arch_10 = load(base / "PARA/ARCHIVES/2024-01-10.md")
    arch_10_ok = "2024-01-10" in arch_10 or \
                 "vscode" in arch_10.lower() or \
                 "p002" in arch_10.lower() or \
                 "dry-run" in arch_10.lower()
    c = check("ARCHIVES/2024-01-10.md: log archived",
              arch_10_ok,
              f"2024-01-10.md should be archived. Found: {arch_10[:200]}")
    checks.append(c); weights.append((c["passed"], 0.04))

    # 7c. ARCHIVES/2024-01-08.md: original content still present (APPEND check)
    arch_08 = load(base / "PARA/ARCHIVES/2024-01-08.md")
    arch_08_preserved = "2024-01-08" in arch_08 or "para hybrid model" in arch_08.lower()
    c = check("ARCHIVES/2024-01-08.md: original archive content preserved",
              arch_08_preserved,
              f"Pre-existing archive must not be overwritten.")
    checks.append(c); weights.append((c["passed"], 0.04))

    # ════════════════════════════════════════════════════════════════════════
    # BLOCK 8: CLEAN — raw logs deleted from memory/
    # ════════════════════════════════════════════════════════════════════════
    log_09_exists = (base / "memory/2024-01-09.md").exists()
    c = check("memory/2024-01-09.md: deleted after archiving",
              not log_09_exists,
              f"Raw log 2024-01-09.md must be deleted after successful archive.")
    checks.append(c); weights.append((c["passed"], 0.03))

    log_10_exists = (base / "memory/2024-01-10.md").exists()
    c = check("memory/2024-01-10.md: deleted after archiving",
              not log_10_exists,
              f"Raw log 2024-01-10.md must be deleted after successful archive.")
    checks.append(c); weights.append((c["passed"], 0.03))

    # heartbeat should NOT be deleted (it's not a daily log)
    hb_exists = (base / "memory/heartbeat-state.json").exists()
    c = check("memory/heartbeat-state.json: NOT deleted",
              hb_exists,
              f"heartbeat-state.json is not a daily log and must be preserved.")
    checks.append(c); weights.append((c["passed"], 0.02))

    # ════════════════════════════════════════════════════════════════════════
    # BLOCK 9: BUILD GLOBAL INDEX — MEMORY.md updated
    # ════════════════════════════════════════════════════════════════════════
    memory_md = load(base / "MEMORY.md")

    # 9a. Existing milestones preserved
    mem_preserved = "2024-01-01" in memory_md or "system initialized" in memory_md.lower()
    c = check("MEMORY.md: existing timeline entries preserved",
              mem_preserved,
              f"Pre-existing timeline entries must remain.")
    checks.append(c); weights.append((c["passed"], 0.03))

    # 9b. New milestone added (P001 v0.1 complete or dry-run or memory automation)
    mem_new_milestone = any([
        "p001" in memory_md.lower(),
        "cli tool" in memory_md.lower(),
        "dry-run" in memory_md.lower(),
        "v0.1" in memory_md,
        "p002" in memory_md.lower(),
        "memory maintenance automation" in memory_md.lower(),
        "2024-01-09" in memory_md or "2024-01-10" in memory_md
    ])
    c = check("MEMORY.md: new milestones added to Timeline",
              mem_new_milestone,
              f"MEMORY.md Timeline must reflect new project milestones. Found: {memory_md[:400]}")
    checks.append(c); weights.append((c["passed"], 0.04))

    # 9c. Knowledge Atlas updated
    atlas_updated = any([
        "docker" in memory_md.lower(),
        "subprocess" in memory_md.lower(),
        "12factor" in memory_md.lower(),
        "areas.md" in memory_md.lower() and "docker" in memory_md.lower(),
    ])
    # Relaxed: at least MEMORY.md was meaningfully updated (touched at all with new content)
    # Accept if it has any content beyond the original minimal state
    memory_grew = len(memory_md) > 300  # original was ~220 chars
    atlas_ok = atlas_updated or (memory_grew and ("knowledge" in memory_md.lower() or "atlas" in memory_md.lower()))
    c = check("MEMORY.md: Knowledge Atlas updated",
              atlas_ok,
              f"MEMORY.md Knowledge Atlas must be updated. len={len(memory_md)}")
    checks.append(c); weights.append((c["passed"], 0.04))

    # ════════════════════════════════════════════════════════════════════════
    # COMPUTE SCORE
    # ════════════════════════════════════════════════════════════════════════
    total_weight = sum(w for _, w in weights)
    earned = sum(w for passed, w in weights if passed)
    score = round(earned / total_weight, 4) if total_weight > 0 else 0.0

    passed_all = all(c["passed"] for c in checks)

    result = {
        "passed": score >= 0.70,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace)