import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    ws = Path(workspace)
    results_dir = ws / "skills" / "botlearn-certify" / "results"
    checks = []
    total_score = 0.0

    # ── helper ──────────────────────────────────────────────────────────────
    def add(name, passed, detail, weight=1.0):
        nonlocal total_score
        checks.append({"name": name, "passed": passed, "detail": detail})
        if passed:
            total_score += weight

    MAX_WEIGHT = 10.0  # total possible weight

    # ── 1. Dual format files exist ───────────────────────────────────────────
    html_files = list(results_dir.rglob("certificate-*.html")) if results_dir.exists() else []
    md_files   = list(results_dir.rglob("certificate-*.md"))   if results_dir.exists() else []

    html_ok = len(html_files) > 0
    md_ok   = len(md_files)   > 0
    add("HTML certificate file exists", html_ok,
        f"Found: {[f.name for f in html_files]}" if html_ok else "No certificate-*.html found in results/",
        weight=1.0)
    add("MD certificate file exists", md_ok,
        f"Found: {[f.name for f in md_files]}" if md_ok else "No certificate-*.md found in results/",
        weight=1.0)

    # ── 2. Filename pattern: certificate-YYYYMMDD-HHmm.ext ──────────────────
    pattern = re.compile(r'^certificate-\d{8}-\d{4}\.(html|md)$')
    html_name_ok = any(pattern.match(f.name) for f in html_files)
    md_name_ok   = any(pattern.match(f.name) for f in md_files)
    add("HTML filename matches certificate-{YYYYMMDD}-{HHmm}.html",
        html_name_ok,
        f"Names found: {[f.name for f in html_files]}",
        weight=0.5)
    add("MD filename matches certificate-{YYYYMMDD}-{HHmm}.md",
        md_name_ok,
        f"Names found: {[f.name for f in md_files]}",
        weight=0.5)

    # ── load best candidates ─────────────────────────────────────────────────
    html_content = ""
    md_content   = ""
    try:
        if html_files:
            html_content = html_files[0].read_text(errors="replace")
    except Exception as e:
        add("HTML file readable", False, str(e), weight=0)
    try:
        if md_files:
            md_content = md_files[0].read_text(errors="replace")
    except Exception as e:
        add("MD file readable", False, str(e), weight=0)

    combined = html_content + md_content

    # ── 3. Agent name present ────────────────────────────────────────────────
    agent_ok = "Zeta-7" in combined
    add("Agent name 'Zeta-7' present in certificate",
        agent_ok,
        "Found 'Zeta-7'" if agent_ok else "Agent name missing",
        weight=0.5)

    # ── 4. Historical overall score = 72 ────────────────────────────────────
    # Agent must pick most-recent FULL report (2024-09-30) overall=72
    hist_ok = bool(re.search(r'72', combined))
    add("Historical overall score 72 present",
        hist_ok,
        "Found '72'" if hist_ok else "Historical score 72 not found — agent may have picked wrong report",
        weight=1.0)

    # ── 5. Fresh overall score = 81 ─────────────────────────────────────────
    fresh_ok = bool(re.search(r'81', combined))
    add("Fresh overall score 81 present",
        fresh_ok,
        "Found '81'" if fresh_ok else "Fresh overall score 81 not found",
        weight=1.0)

    # ── 6. Improvement value = +9 ───────────────────────────────────────────
    # 81 - 72 = 9
    improvement_ok = bool(re.search(r'\+9\b|improvement.*9|9.*improvement', combined, re.IGNORECASE))
    add("Improvement value +9 present",
        improvement_ok,
        "Found '+9' or improvement=9" if improvement_ok else "Improvement value +9 not found",
        weight=1.0)

    # ── 7. Improvement label = Significant (8 <= 9 < 15) ───────────────────
    label_ok = bool(re.search(r'Significant', combined, re.IGNORECASE))
    add("Improvement label 'Significant' present",
        label_ok,
        "Found 'Significant'" if label_ok else "Expected label 'Significant' (improvement=9, range 8-14) not found",
        weight=1.0)

    # ── 8. Profile classification = Advanced Specialist (75-89 → 81) ────────
    profile_ok = bool(re.search(r'Advanced\s+Specialist', combined, re.IGNORECASE))
    add("Profile label 'Advanced Specialist' present (score 81 → range 75-89)",
        profile_ok,
        "Found 'Advanced Specialist'" if profile_ok else "Profile label missing or wrong (fresh score 81 → should be 'Advanced Specialist')",
        weight=1.0)

    # ── 9. Badge color = silver ──────────────────────────────────────────────
    badge_ok = bool(re.search(r'silver', combined, re.IGNORECASE))
    add("Badge color 'silver' present",
        badge_ok,
        "Found 'silver'" if badge_ok else "Badge color 'silver' not found (Advanced Specialist → silver)",
        weight=0.5)

    # ── 10. All 5 dimension names dynamically included ───────────────────────
    dimensions = ["Reasoning", "Language Comprehension", "Tool Usage",
                  "Problem Solving", "Knowledge Retrieval"]
    dims_found = [d for d in dimensions if d in combined]
    dims_ok = len(dims_found) == 5
    add(f"All 5 dimensions present ({dims_found})",
        dims_ok,
        f"Present: {dims_found}, Missing: {[d for d in dimensions if d not in dims_found]}",
        weight=1.0)

    # ── 11. Dimension delta values spot-check (Reasoning: 80-71=+9) ─────────
    reasoning_delta_ok = bool(re.search(r'\+9|\b9\b', combined))  # delta for Reasoning
    # Also check Problem Solving: 85-76=+9
    ps_fresh_ok = bool(re.search(r'85', combined))
    delta_ok = reasoning_delta_ok and ps_fresh_ok
    add("Per-dimension fresh scores present (e.g. 85 for Problem Solving)",
        delta_ok,
        f"Reasoning delta search: {reasoning_delta_ok}, PS fresh 85: {ps_fresh_ok}",
        weight=0.5)

    # ── 12. HTML structure check ─────────────────────────────────────────────
    html_struct_ok = (
        "<!DOCTYPE html>" in html_content.upper() or "<!doctype html>" in html_content.lower()
    ) and "<html" in html_content and "</html>" in html_content
    add("HTML file has valid HTML skeleton",
        html_struct_ok,
        "Has DOCTYPE + html tags" if html_struct_ok else "Missing DOCTYPE or html tags",
        weight=0.5)

    # ── final scoring ────────────────────────────────────────────────────────
    total_weight = 10.0
    score = round(min(total_score / total_weight, 1.0), 4)
    passed = score >= 0.75

    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))