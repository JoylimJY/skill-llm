#!/usr/bin/env python3
"""
Evaluation script for the Medium republish task.
Usage: python eval_script.py /workspace
"""

import sys
import json
import re
from pathlib import Path

def load_file(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return None

def find_artifact(workspace: Path, filename: str) -> Path | None:
    matches = list(workspace.rglob(filename))
    if not matches:
        return None
    # Prefer the file not inside .git or __pycache__
    clean = [m for m in matches if ".git" not in m.parts and "__pycache__" not in m.parts]
    return clean[0] if clean else matches[0]

def run_checks(workspace_str: str) -> dict:
    workspace = Path(workspace_str)
    checks = []
    total_weight = 0.0
    earned_weight = 0.0

    CANONICAL_URL = "https://www.greennesthouse.com/blogs/journal/how-to-switch-to-non-toxic-cleaners"
    SITE_DOMAIN = "greennesthouse.com"

    # Keywords from Section 6 of project-context.md (primary set)
    PRIMARY_KEYWORDS = [
        "non-toxic cleaning products",
        "sustainable home essentials",
        "eco-friendly household cleaners",
        "zero-waste kitchen products",
        "organic wool bedding benefits",
    ]
    LONG_TAIL_KEYWORDS = [
        "how to switch to non-toxic cleaners",
        "best zero-waste products for home",
        "natural alternatives to bleach",
        "organic bedding for better sleep",
        "compostable kitchen supplies",
    ]
    ALL_KEYWORDS = PRIMARY_KEYWORDS + LONG_TAIL_KEYWORDS

    # ── CHECK 0: File exists ────────────────────────────────────────────────
    w = 1.0
    total_weight += w
    artifact_path = find_artifact(workspace, "medium_article.md")
    if artifact_path:
        content = load_file(artifact_path)
        check0 = {"name": "medium_article.md exists", "passed": content is not None,
                   "detail": f"Found at {artifact_path}"}
        earned_weight += w if check0["passed"] else 0
    else:
        content = None
        check0 = {"name": "medium_article.md exists", "passed": False,
                   "detail": "File medium_article.md not found anywhere in workspace"}
    checks.append(check0)

    if not content:
        # All remaining checks auto-fail
        for name in [
            "Title contains primary keyword from Section 6",
            "Canonical URL present and correct",
            "Canonical framed as Medium publishing setting (republish context)",
            "Internal link(s) to greennesthouse.com present",
            "CTA section present",
            "Article body has substantive content (>400 words)",
            "No invented keywords — uses project-context keywords",
        ]:
            checks.append({"name": name, "passed": False, "detail": "File missing — skipped"})
        score = round(earned_weight / total_weight, 3) if total_weight else 0.0
        return {"passed": False, "score": score, "checks": checks}

    content_lower = content.lower()

    # ── CHECK 1: Title contains at least one primary keyword ───────────────
    w = 2.0
    total_weight += w
    # Find a line that looks like a markdown title (# ...)
    title_lines = [ln.strip() for ln in content.splitlines() if ln.strip().startswith("#")]
    title_text = " ".join(title_lines[:3]).lower()  # check first few headings
    kw_in_title = [kw for kw in PRIMARY_KEYWORDS if kw in title_text]
    if not kw_in_title:
        # Also check long-tail in title
        kw_in_title = [kw for kw in LONG_TAIL_KEYWORDS if kw in title_text]
    c1_passed = len(kw_in_title) > 0
    checks.append({
        "name": "Title contains primary keyword from Section 6",
        "passed": c1_passed,
        "detail": f"Keywords found in title area: {kw_in_title}" if c1_passed
                  else f"No Section-6 keywords detected in title/headings. Title area: {title_text[:200]}"
    })
    earned_weight += w if c1_passed else 0

    # ── CHECK 2: Canonical URL is present and matches original ─────────────
    w = 2.5
    total_weight += w
    canonical_present = CANONICAL_URL in content
    checks.append({
        "name": "Canonical URL present and correct",
        "passed": canonical_present,
        "detail": f"Expected '{CANONICAL_URL}' in file." +
                  (" Found." if canonical_present else " NOT found.")
    })
    earned_weight += w if canonical_present else 0

    # ── CHECK 3: Canonical framed as Medium republish setting instruction ──
    # The SKILL.md requires: for republish → set canonical to original URL
    # in Medium settings. The output must make clear this is a Medium
    # canonical/settings instruction, not just a random URL mention.
    w = 2.0
    total_weight += w
    canonical_context_patterns = [
        r"canonical",
        r"medium\s+setting",
        r"set\s+canonical",
        r"import\s+setting",
        r"medium.*canonical",
        r"canonical.*medium",
        r"republish",
        r"re-publish",
        r"original.*url",
        r"original.*source",
        r"duplicate\s+content",
    ]
    c3_matches = [p for p in canonical_context_patterns if re.search(p, content_lower)]
    c3_passed = len(c3_matches) >= 2  # must have at least 2 signals
    checks.append({
        "name": "Canonical framed as Medium publishing setting (republish context)",
        "passed": c3_passed,
        "detail": f"Canonical context patterns matched: {c3_matches}" if c3_passed
                  else f"Insufficient canonical/republish framing. Matched: {c3_matches}"
    })
    earned_weight += w if c3_passed else 0

    # ── CHECK 4: Internal links to greennesthouse.com ──────────────────────
    w = 1.5
    total_weight += w
    internal_links = re.findall(r'https?://[^\s\)\"\']*greennesthouse\.com[^\s\)\"\']*', content)
    # Must have at least 2 distinct internal links (CTA link + at least one content link)
    unique_internal = list(set(internal_links))
    c4_passed = len(unique_internal) >= 1
    checks.append({
        "name": "Internal link(s) to greennesthouse.com present",
        "passed": c4_passed,
        "detail": f"Found {len(unique_internal)} unique internal links: {unique_internal[:5]}" if c4_passed
                  else "No links to greennesthouse.com found in article"
    })
    earned_weight += w if c4_passed else 0

    # ── CHECK 5: CTA section ───────────────────────────────────────────────
    w = 1.5
    total_weight += w
    cta_patterns = [
        r"\bcta\b",
        r"call.to.action",
        r"shop\s+now",
        r"get\s+yours",
        r"try\s+the",
        r"visit\s+our",
        r"check\s+out",
        r"starter\s+kit",
        r"learn\s+more",
        r"grab\s+your",
        r"start\s+your",
        r"## .*cta",
        r"##.*call",
    ]
    cta_matches = [p for p in cta_patterns if re.search(p, content_lower)]
    c5_passed = len(cta_matches) >= 1
    checks.append({
        "name": "CTA section present",
        "passed": c5_passed,
        "detail": f"CTA signals found: {cta_matches}" if c5_passed
                  else "No CTA patterns detected. Must include a call-to-action per SKILL.md output format."
    })
    earned_weight += w if c5_passed else 0

    # ── CHECK 6: Substantive content (>400 words) ──────────────────────────
    w = 1.0
    total_weight += w
    word_count = len(content.split())
    c6_passed = word_count >= 400
    checks.append({
        "name": "Article body has substantive content (>400 words)",
        "passed": c6_passed,
        "detail": f"Word count: {word_count}"
    })
    earned_weight += w if c6_passed else 0

    # ── CHECK 7: Uses real project-context keywords (not invented) ─────────
    # At least 3 keywords from Section 6 (primary or long-tail) must appear
    # in the article body.
    w = 1.5
    total_weight += w
    kws_used = [kw for kw in ALL_KEYWORDS if kw in content_lower]
    c7_passed = len(kws_used) >= 3
    checks.append({
        "name": "No invented keywords — uses project-context keywords",
        "passed": c7_passed,
        "detail": f"Keywords from Section 6 found in article: {kws_used}" if c7_passed
                  else f"Only {len(kws_used)} Section-6 keywords found ({kws_used}). Need ≥3."
    })
    earned_weight += w if c7_passed else 0

    # ── Final scoring ──────────────────────────────────────────────────────
    score = round(earned_weight / total_weight, 3) if total_weight else 0.0
    # Must pass canonical URL check AND file-exists check to be considered passing overall
    hard_gates = [checks[0]["passed"], checks[2]["passed"], checks[3]["passed"]]
    overall_passed = all(hard_gates) and score >= 0.70

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "invocation", "passed": False,
                                      "detail": "No workspace path provided"}]}))
        sys.exit(1)

    result = run_checks(sys.argv[1])
    print(json.dumps(result, indent=2))