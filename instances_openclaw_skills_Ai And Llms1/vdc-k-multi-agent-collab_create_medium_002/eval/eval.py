import json
import os
from pathlib import Path


def safe_read(path: Path):
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return None, str(e)


def norm(s: str):
    import re
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def contains_fuzzy(text: str, needle: str) -> bool:
    return norm(needle) in norm(text)


def main():
    import sys
    workspace = Path(sys.argv[1])
    checks = []

    expected_files = ["TASK.md", "CHANGELOG.md", "CONTEXT.md", "WEEKLY-REPORT.md", "llms.txt"]

    for fname in expected_files:
        p = workspace / fname
        try:
            exists = p.exists()
            checks.append({
                "name": f"exists:{fname}",
                "passed": exists,
                "detail": "file found" if exists else "missing file"
            })
        except Exception as e:
            checks.append({
                "name": f"exists:{fname}",
                "passed": False,
                "detail": f"error checking existence: {e}"
            })

    try:
        task_text = (workspace / "TASK.md").read_text(encoding="utf-8")
        items = [line for line in task_text.splitlines() if line.strip().startswith(('-', '*', '1.', '2.', '3.', '4.', '5.', '6.'))]
        passed = len(items) >= 5 and contains_fuzzy(task_text, "qmd indexing") and contains_fuzzy(task_text, "update changelog")
        checks.append({
            "name": "task_content",
            "passed": passed,
            "detail": f"found {len(items)} checklist-like items"
        })
    except Exception as e:
        checks.append({
            "name": "task_content",
            "passed": False,
            "detail": f"failed to read or parse TASK.md: {e}"
        })

    try:
        changelog = (workspace / "CHANGELOG.md").read_text(encoding="utf-8")
        lines = [ln for ln in changelog.splitlines() if ln.strip()]
        tag_ok = any("#" in ln for ln in lines)
        identity_ok = any(contains_fuzzy(ln, "by") or contains_fuzzy(ln, "author") for ln in lines)
        passed = len(lines) >= 2 and tag_ok and identity_ok
        checks.append({
            "name": "changelog_content",
            "passed": passed,
            "detail": f"nonempty lines={len(lines)}, tag_ok={tag_ok}, identity_ok={identity_ok}"
        })
    except Exception as e:
        checks.append({
            "name": "changelog_content",
            "passed": False,
            "detail": f"failed to read or parse CHANGELOG.md: {e}"
        })

    try:
        context = (workspace / "CONTEXT.md").read_text(encoding="utf-8")
        passed = contains_fuzzy(context, "atlas-sync") and contains_fuzzy(context, "document-driven sync") and contains_fuzzy(context, "collaboration model")
        checks.append({
            "name": "context_content",
            "passed": passed,
            "detail": "project and decision markers verified"
        })
    except Exception as e:
        checks.append({
            "name": "context_content",
            "passed": False,
            "detail": f"failed to read CONTEXT.md: {e}"
        })

    try:
        weekly = (workspace / "WEEKLY-REPORT.md").read_text(encoding="utf-8")
        pd_ok = contains_fuzzy(weekly, "pattern discovery")
        bullets = [ln for ln in weekly.splitlines() if ln.strip().startswith(('-', '*'))]
        repeated_ok = any(contains_fuzzy(ln, "candidate skill") for ln in bullets)
        passed = pd_ok and len(bullets) >= 3 and repeated_ok
        checks.append({
            "name": "weekly_report_content",
            "passed": passed,
            "detail": f"bullets={len(bullets)}, pattern_discovery={pd_ok}, candidate_skill={repeated_ok}"
        })
    except Exception as e:
        checks.append({
            "name": "weekly_report_content",
            "passed": False,
            "detail": f"failed to read WEEKLY-REPORT.md: {e}"
        })

    try:
        llms = (workspace / "llms.txt").read_text(encoding="utf-8")
        doc_hits = sum(1 for x in ["TASK.md", "CHANGELOG.md", "CONTEXT.md", "WEEKLY-REPORT.md"] if contains_fuzzy(llms, x))
        phr_ok = contains_fuzzy(llms, "on-demand retrieval")
        passed = doc_hits == 4 and phr_ok
        checks.append({
            "name": "llms_content",
            "passed": passed,
            "detail": f"doc_hits={doc_hits}, on_demand_retrieval={phr_ok}"
        })
    except Exception as e:
        checks.append({
            "name": "llms_content",
            "passed": False,
            "detail": f"failed to read llms.txt: {e}"
        })

    try:
        marker = "ATLAS_SYNC_MARKER_2025"
        marker_hits = 0
        for fname in expected_files:
            try:
                txt = (workspace / fname).read_text(encoding="utf-8")
                if marker in txt:
                    marker_hits += 1
            except Exception:
                pass
        passed = marker_hits >= 2
        checks.append({
            "name": "marker_presence",
            "passed": passed,
            "detail": f"marker found in {marker_hits} files"
        })
    except Exception as e:
        checks.append({
            "name": "marker_presence",
            "passed": False,
            "detail": f"marker check failed: {e}"
        })

    total = len(checks)
    passed_count = sum(1 for c in checks if c.get("passed"))
    result = {
        "passed": passed_count == total,
        "score": (passed_count / total) if total else 0.0,
        "checks": checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
