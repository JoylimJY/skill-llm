#!/usr/bin/env python3
"""
Evaluation script for the brainstorming skill task.
Checks that the agent produced a valid design document at the correct canonical path,
committed it to git, included required sections with 2-3 approaches, and wrote NO code.
"""

import sys
import json
import subprocess
import re
from pathlib import Path
from datetime import datetime, date

def run(cmd, cwd):
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode

def main():
    workspace = Path(sys.argv[1]).resolve()
    checks = []

    # ── CHECK 1: docs/plans/ directory exists ──────────────────────────────
    plans_dir = workspace / "docs" / "plans"
    if plans_dir.exists():
        checks.append({"name": "docs/plans/ directory exists", "passed": True, "detail": "Directory found."})
    else:
        checks.append({"name": "docs/plans/ directory exists", "passed": False, "detail": "docs/plans/ directory not found."})

    # ── CHECK 2: Design doc exists with correct naming convention ───────────
    design_doc = None
    design_doc_path = None
    try:
        candidates = list(plans_dir.glob("*.md")) if plans_dir.exists() else []
        # Pattern: YYYY-MM-DD-<topic>-design.md
        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}-.+-design\.md$")
        valid_candidates = [f for f in candidates if date_pattern.match(f.name)]
        # Accept any that contain "anomaly" in the name (topic-related)
        topic_candidates = [f for f in valid_candidates if "anomal" in f.name.lower() or "detect" in f.name.lower() or "transaction" in f.name.lower()]
        if not topic_candidates and valid_candidates:
            topic_candidates = valid_candidates  # fallback: accept any valid-format doc

        if topic_candidates:
            design_doc_path = topic_candidates[0]
            design_doc = design_doc_path.read_text()
            checks.append({
                "name": "Design doc has correct YYYY-MM-DD-<topic>-design.md naming",
                "passed": True,
                "detail": f"Found: {design_doc_path.name}"
            })
        else:
            checks.append({
                "name": "Design doc has correct YYYY-MM-DD-<topic>-design.md naming",
                "passed": False,
                "detail": f"No file matching YYYY-MM-DD-<topic>-design.md found in docs/plans/. Files found: {[f.name for f in candidates]}"
            })
    except Exception as e:
        checks.append({
            "name": "Design doc has correct YYYY-MM-DD-<topic>-design.md naming",
            "passed": False,
            "detail": f"Exception during search: {e}"
        })

    # ── CHECK 3: Date in filename is valid and plausible ────────────────────
    try:
        if design_doc_path:
            date_str = design_doc_path.name[:10]
            doc_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            today = date.today()
            # Date must be within last 2 years or today (plausible)
            plausible = date(2023, 1, 1) <= doc_date <= today
            checks.append({
                "name": "Date in filename is a valid calendar date",
                "passed": plausible,
                "detail": f"Date parsed: {doc_date}, today: {today}, plausible: {plausible}"
            })
        else:
            checks.append({"name": "Date in filename is a valid calendar date", "passed": False, "detail": "No design doc found."})
    except Exception as e:
        checks.append({"name": "Date in filename is a valid calendar date", "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 4: Design doc is non-trivial (>200 words) ─────────────────────
    try:
        if design_doc:
            word_count = len(design_doc.split())
            passed = word_count >= 200
            checks.append({
                "name": "Design doc is substantive (>=200 words)",
                "passed": passed,
                "detail": f"Word count: {word_count}"
            })
        else:
            checks.append({"name": "Design doc is substantive (>=200 words)", "passed": False, "detail": "No design doc."})
    except Exception as e:
        checks.append({"name": "Design doc is substantive (>=200 words)", "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 5: Contains 2-3 distinct approaches with trade-offs ───────────
    try:
        if design_doc:
            doc_lower = design_doc.lower()
            # Look for multiple approach/option mentions
            approach_patterns = [
                r"approach\s+[123abc]",
                r"option\s+[123abc]",
                r"## approach",
                r"### approach",
                r"## option",
                r"### option",
                r"\*\*approach\s+[123abc",
                r"\*\*option\s+[123abc",
            ]
            approach_count = 0
            for p in approach_patterns:
                approach_count += len(re.findall(p, doc_lower))

            # Also check for "trade-off" or "tradeoff" or "pros" or "cons"
            has_tradeoffs = bool(re.search(r"trade.off|pros|cons|advantage|disadvantage|drawback|benefit", doc_lower))

            # Heuristic: at least 2 distinct numbered/lettered approaches AND trade-off language
            has_approaches = approach_count >= 2

            # Also accept if doc has sections like "Rule-based", "ML", "Hybrid" (domain-specific)
            domain_approaches = bool(re.search(r"rule.based|ml.based|machine.learn|hybrid|heuristic|statistical|threshold", doc_lower))

            passed = (has_approaches or domain_approaches) and has_tradeoffs
            checks.append({
                "name": "Contains 2-3 approaches with trade-offs",
                "passed": passed,
                "detail": f"Approach pattern matches: {approach_count}, has tradeoffs: {has_tradeoffs}, domain-specific approaches: {domain_approaches}"
            })
        else:
            checks.append({"name": "Contains 2-3 approaches with trade-offs", "passed": False, "detail": "No design doc."})
    except Exception as e:
        checks.append({"name": "Contains 2-3 approaches with trade-offs", "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 6: Contains required design sections ───────────────────────────
    required_sections = {
        "architecture": r"architecture|component|data.flow|system.design",
        "error_handling": r"error.handl|failure.mode|fallback|graceful|exception",
        "testing": r"test|qa|quality|validation|verif",
    }
    try:
        if design_doc:
            doc_lower = design_doc.lower()
            section_results = {}
            for section, pattern in required_sections.items():
                found = bool(re.search(pattern, doc_lower))
                section_results[section] = found
            all_found = all(section_results.values())
            checks.append({
                "name": "Contains architecture, error handling, and testing sections",
                "passed": all_found,
                "detail": f"Section coverage: {section_results}"
            })
        else:
            checks.append({"name": "Contains architecture, error handling, and testing sections", "passed": False, "detail": "No design doc."})
    except Exception as e:
        checks.append({"name": "Contains architecture, error handling, and testing sections", "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 7: Design doc is committed to git ──────────────────────────────
    try:
        stdout, stderr, rc = run(["git", "log", "--oneline", "--all"], cwd=str(workspace))
        commits = stdout.strip().split("\n")
        # Check if docs/plans/ has any tracked files in git
        stdout2, _, _ = run(["git", "ls-files", "docs/plans/"], cwd=str(workspace))
        tracked_files = stdout2.strip().split("\n")
        tracked_design_docs = [f for f in tracked_files if f.endswith("-design.md")]
        
        if tracked_design_docs:
            checks.append({
                "name": "Design doc is committed to git",
                "passed": True,
                "detail": f"Tracked design docs: {tracked_design_docs}"
            })
        else:
            # Check git status for untracked/staged
            stdout3, _, _ = run(["git", "status", "--short"], cwd=str(workspace))
            checks.append({
                "name": "Design doc is committed to git",
                "passed": False,
                "detail": f"No design doc found in git tracking. Git status: {stdout3}. ls-files: {tracked_files}"
            })
    except Exception as e:
        checks.append({"name": "Design doc is committed to git", "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 8: No implementation code was written (HARD-GATE) ─────────────
    try:
        # Check that no NEW Python files were added to src/ compared to initial commit
        stdout, _, _ = run(["git", "diff", "--name-only", "HEAD~1..HEAD", "--", "src/"], cwd=str(workspace))
        new_src_files = [f.strip() for f in stdout.strip().split("\n") if f.strip()]
        
        # Also check for any new .py files outside the original structure
        stdout2, _, _ = run(["git", "diff", "--name-status", "HEAD~1..HEAD"], cwd=str(workspace))
        added_py = [line for line in stdout2.split("\n") if line.startswith("A") and line.endswith(".py")]
        
        # Allow only if added files are in docs/ or tests/ (not src/)
        bad_additions = [f for f in new_src_files if f] + [f for f in added_py if "src/" in f]
        
        implementation_free = len(bad_additions) == 0
        checks.append({
            "name": "HARD-GATE: No implementation code added to src/",
            "passed": implementation_free,
            "detail": f"New src/ changes: {new_src_files}, Added .py in src: {added_py}"
        })
    except Exception as e:
        # If only one commit exists (no HEAD~1), that means agent didn't commit anything additional
        # which means also no code was written — check untracked files
        try:
            stdout3, _, _ = run(["git", "status", "--short"], cwd=str(workspace))
            untracked_py = [l for l in stdout3.split("\n") if l.strip().endswith(".py") and "src/" in l]
            checks.append({
                "name": "HARD-GATE: No implementation code added to src/",
                "passed": len(untracked_py) == 0,
                "detail": f"Git diff exception: {e}. Untracked py in src: {untracked_py}"
            })
        except Exception as e2:
            checks.append({"name": "HARD-GATE: No implementation code added to src/", "passed": False, "detail": f"Exception: {e2}"})

    # ── CHECK 9: Design references project context (anomaly detection topic) ─
    try:
        if design_doc:
            doc_lower = design_doc.lower()
            context_signals = [
                bool(re.search(r"anomal", doc_lower)),
                bool(re.search(r"transaction", doc_lower)),
                bool(re.search(r"fraud|suspicious|flag|detect|alert", doc_lower)),
            ]
            context_score = sum(context_signals)
            passed = context_score >= 2
            checks.append({
                "name": "Design document addresses anomaly detection for transaction processing",
                "passed": passed,
                "detail": f"Context signals hit: {context_score}/3 (anomaly: {context_signals[0]}, transaction: {context_signals[1]}, fraud/detection: {context_signals[2]})"
            })
        else:
            checks.append({"name": "Design document addresses anomaly detection for transaction processing", "passed": False, "detail": "No design doc."})
    except Exception as e:
        checks.append({"name": "Design document addresses anomaly detection for transaction processing", "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 10: A recommendation is stated (not just listing options) ──────
    try:
        if design_doc:
            doc_lower = design_doc.lower()
            has_recommendation = bool(re.search(
                r"recommend|suggest|prefer|propose|chosen approach|our choice|we should|i recommend|advised",
                doc_lower
            ))
            checks.append({
                "name": "Design includes a recommendation (not just neutral listing)",
                "passed": has_recommendation,
                "detail": f"Recommendation language found: {has_recommendation}"
            })
        else:
            checks.append({"name": "Design includes a recommendation (not just neutral listing)", "passed": False, "detail": "No design doc."})
    except Exception as e:
        checks.append({"name": "Design includes a recommendation (not just neutral listing)", "passed": False, "detail": f"Exception: {e}"})

    # ── Scoring ──────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 3)

    # Hard-gate check: HARD-GATE failure sets overall passed to False
    hard_gate = next((c for c in checks if "HARD-GATE" in c["name"]), None)
    overall_passed = (passed_count >= 7) and (hard_gate is None or hard_gate["passed"])

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()