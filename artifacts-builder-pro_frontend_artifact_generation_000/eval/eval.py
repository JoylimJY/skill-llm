#!/usr/bin/env python3
"""
Evaluation script for the harbor-ops artifact task.
Checks that:
1. The init script was used (a project named 'harbor-ops' exists or bundle.html was created)
2. bundle.html exists and was produced by the proprietary bundle script
3. bundle.html contains React-rendered content (not just static HTML)
4. shadcn/ui component fingerprints are present (class-variance-authority, Radix UI patterns)
5. Required UI elements are present: tabs, status badges/cards, KPI stats
6. No "AI slop" style violations: no Inter font, no purple gradient
7. The file is self-contained (no external script src pointing to CDN for React)
"""

import sys
import json
import os
import re
from pathlib import Path

def run_eval(workspace: str):
    checks = []

    def check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return passed

    # ── Find bundle.html ──────────────────────────────────────────────────────
    bundle_path = None
    candidates = list(Path(workspace).rglob("bundle.html"))
    if candidates:
        # Prefer the one inside a project subdirectory (not inside old-projects/archives)
        for c in candidates:
            parts = c.parts
            if not any(d in parts for d in ["old-projects", "archives", "dist"]):
                bundle_path = c
                break
        if bundle_path is None:
            bundle_path = candidates[0]

    if not check(
        "bundle.html exists",
        bundle_path is not None,
        f"Found at: {bundle_path}" if bundle_path else "bundle.html not found anywhere in workspace"
    ):
        # Can't proceed without the file
        final_score = 0.0
        return {"passed": False, "score": final_score, "checks": checks}

    # ── Read file ─────────────────────────────────────────────────────────────
    try:
        content = bundle_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        check("bundle.html readable", False, str(e))
        return {"passed": False, "score": 0.0, "checks": checks}

    check("bundle.html readable", True, f"Size: {len(content)} bytes")

    # ── Check 1: File is non-trivial (min size suggests bundled app) ──────────
    min_size = 50_000  # 50KB — a bundled React app will be much larger
    check(
        "bundle.html is a real bundled artifact (>50KB)",
        len(content) >= min_size,
        f"File size: {len(content)} bytes (need >= {min_size})"
    )

    # ── Check 2: Self-contained (no external React CDN) ───────────────────────
    external_react = bool(re.search(
        r'src=["\']https?://[^"\']*react[^"\']*["\']',
        content, re.IGNORECASE
    ))
    check(
        "No external React CDN (self-contained)",
        not external_react,
        "No external React CDN src found" if not external_react else "Found external React CDN link — not self-contained"
    )

    # ── Check 3: React fingerprints (bundled React code patterns) ────────────
    react_patterns = [
        r'createElement',
        r'useState|useEffect|useRef|useCallback',
        r'__esModule|__webpack|parcelRequire|function\s+\w+\s*\(\w*\)\s*\{',
    ]
    react_found = sum(1 for p in react_patterns if re.search(p, content))
    check(
        "React runtime fingerprints present",
        react_found >= 2,
        f"Found {react_found}/{len(react_patterns)} React fingerprint patterns"
    )

    # ── Check 4: shadcn/ui / Radix UI fingerprints ────────────────────────────
    shadcn_patterns = [
        r'data-\[state=',           # Radix UI state attributes in generated CSS
        r'radix-ui|RadixUI|@radix',
        r'class-variance-authority|cva\(',
        r'tailwind-merge|twMerge|clsx',
        r'rounded-md|rounded-lg|ring-offset',  # Tailwind classes from shadcn
    ]
    shadcn_found = sum(1 for p in shadcn_patterns if re.search(p, content, re.IGNORECASE))
    check(
        "shadcn/ui component fingerprints present",
        shadcn_found >= 2,
        f"Found {shadcn_found}/{len(shadcn_patterns)} shadcn/ui patterns"
    )

    # ── Check 5: KPI / Statistics content ────────────────────────────────────
    kpi_patterns = [
        r'12|twelve',                          # Total Vessels
        r'847|TEU',                            # TEUs
        r'dwell|Dwell',                        # Dwell time
        r'vessel[s]?|Vessel[s]?',             # Vessels mentioned
        r'depart|Depart',                      # Departed
    ]
    kpi_found = sum(1 for p in kpi_patterns if re.search(p, content))
    check(
        "KPI statistics content present",
        kpi_found >= 3,
        f"Found {kpi_found}/{len(kpi_patterns)} KPI content patterns"
    )

    # ── Check 6: Vessel table / tab content ──────────────────────────────────
    table_patterns = [
        r'In Port|in-port|inport|IN PORT',
        r'Departed|DEPARTED|departed',
        r'Cargo|cargo|CARGO',
        r'Berth|berth|BERTH',
        r'flag|Flag|FLAG',
    ]
    table_found = sum(1 for p in table_patterns if re.search(p, content, re.IGNORECASE))
    check(
        "Vessel status table content present",
        table_found >= 3,
        f"Found {table_found}/{len(table_patterns)} table content patterns"
    )

    # ── Check 7: Status badges present ────────────────────────────────────────
    badge_patterns = [
        r'Delayed|delayed|DELAYED',
        r'Clearing|clearing',
        r'badge|Badge|status.*badge|badge.*status',
    ]
    badge_found = sum(1 for p in badge_patterns if re.search(p, content, re.IGNORECASE))
    check(
        "Status badges/indicators present",
        badge_found >= 2,
        f"Found {badge_found}/{len(badge_patterns)} badge patterns"
    )

    # ── Check 8: Cargo manifest panel ────────────────────────────────────────
    cargo_patterns = [
        r'Container|container',
        r'Bulk|bulk',
        r'Liquid|liquid',
        r'Vehicle|vehicle',
        r'manifest|Manifest',
    ]
    cargo_found = sum(1 for p in cargo_patterns if re.search(p, content, re.IGNORECASE))
    check(
        "Cargo manifest breakdown present",
        cargo_found >= 3,
        f"Found {cargo_found}/{len(cargo_patterns)} cargo manifest patterns"
    )

    # ── Check 9: No AI slop — no Inter font ──────────────────────────────────
    inter_font = bool(re.search(
        r"font-family\s*:\s*['\"]?Inter['\"]?|fonts\.googleapis\.com.*Inter|'Inter'|\"Inter\"",
        content, re.IGNORECASE
    ))
    check(
        "No Inter font (avoids AI slop)",
        not inter_font,
        "No Inter font reference found" if not inter_font else "Inter font detected — violates design guidelines"
    )

    # ── Check 10: No AI slop — no purple gradient ─────────────────────────────
    purple_gradient = bool(re.search(
        r'(linear-gradient|bg-gradient)[^;]*?(#7c3aed|#a855f7|#8b5cf6|#9333ea|purple|violet)',
        content, re.IGNORECASE
    ))
    check(
        "No purple gradient (avoids AI slop)",
        not purple_gradient,
        "No purple gradient found" if not purple_gradient else "Purple gradient detected — violates design guidelines"
    )

    # ── Check 11: Tabs component used ────────────────────────────────────────
    tabs_present = bool(re.search(
        r'TabsList|TabsTrigger|TabsContent|role=["\']tab|data-\[state=active\]',
        content, re.IGNORECASE
    ))
    check(
        "Tabs component used for filtering",
        tabs_present,
        "Tabs component fingerprint found" if tabs_present else "No Tabs component fingerprint found"
    )

    # ── Check 12: init-artifact.sh was used (harbor-ops project dir exists) ──
    project_dirs = list(Path(workspace).glob("harbor-ops"))
    project_dir_exists = any(p.is_dir() for p in project_dirs)
    check(
        "harbor-ops project directory created (init-artifact.sh was used)",
        project_dir_exists,
        f"Found harbor-ops/ directory: {project_dir_exists}"
    )

    # ── Scoring ───────────────────────────────────────────────────────────────
    critical_checks = [
        "bundle.html exists",
        "bundle.html is a real bundled artifact (>50KB)",
        "No external React CDN (self-contained)",
        "React runtime fingerprints present",
        "harbor-ops project directory created (init-artifact.sh was used)",
    ]
    important_checks = [
        "shadcn/ui component fingerprints present",
        "KPI statistics content present",
        "Vessel status table content present",
        "Status badges/indicators present",
        "Cargo manifest breakdown present",
        "No Inter font (avoids AI slop)",
        "No purple gradient (avoids AI slop)",
        "Tabs component used for filtering",
    ]

    check_map = {c["name"]: c["passed"] for c in checks}
    critical_passed = sum(1 for c in critical_checks if check_map.get(c, False))
    important_passed = sum(1 for c in important_checks if check_map.get(c, False))

    # Critical checks must all pass
    all_critical = critical_passed == len(critical_checks)
    score = 0.0
    if all_critical:
        # 60% for critical, 40% for important
        score = 0.6 + 0.4 * (important_passed / len(important_checks))
    else:
        score = 0.6 * (critical_passed / len(critical_checks))

    overall_passed = all_critical and (important_passed >= 5)

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))