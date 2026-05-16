import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    score_parts = []

    home = Path.home()
    news_dir = home / "news"

    # ── CHECK 1: memory.md exists and has specific interest proportions ────────
    try:
        memory_path = news_dir / "memory.md"
        assert memory_path.exists(), "memory.md does not exist"
        memory_content = memory_path.read_text()

        # Must contain numeric proportions (65% fintech, 35% AI or equivalent)
        has_fintech_proportion = bool(re.search(r'6[0-9]\s*%.*fintech|fintech.*6[0-9]\s*%', memory_content, re.IGNORECASE))
        has_ai_proportion = bool(re.search(r'3[0-9]\s*%.*(?:AI|open.?source)|(?:AI|open.?source).*3[0-9]\s*%', memory_content, re.IGNORECASE))

        proportion_found = has_fintech_proportion and has_ai_proportion
        checks.append({
            "name": "memory.md has specific interest proportions (65%/35% or similar)",
            "passed": proportion_found,
            "detail": f"fintech_proportion={has_fintech_proportion}, ai_proportion={has_ai_proportion}. Content snippet: {memory_content[:300]}"
        })
        score_parts.append(0.20 if proportion_found else 0.0)
    except Exception as e:
        checks.append({"name": "memory.md has specific interest proportions", "passed": False, "detail": str(e)})
        score_parts.append(0.0)

    # ── CHECK 2: memory.md has format preference (bullets) ────────────────────
    try:
        memory_content = memory_path.read_text()
        has_format = bool(re.search(r'bullet|bullets', memory_content, re.IGNORECASE))
        checks.append({
            "name": "memory.md specifies bullet format preference",
            "passed": has_format,
            "detail": f"bullet keyword found: {has_format}. Snippet: {memory_content[:400]}"
        })
        score_parts.append(0.10 if has_format else 0.0)
    except Exception as e:
        checks.append({"name": "memory.md format preference", "passed": False, "detail": str(e)})
        score_parts.append(0.0)

    # ── CHECK 3: memory.md has timing (morning) ───────────────────────────────
    try:
        memory_content = memory_path.read_text()
        has_timing = bool(re.search(r'morn', memory_content, re.IGNORECASE))
        checks.append({
            "name": "memory.md specifies morning timing",
            "passed": has_timing,
            "detail": f"morning keyword found: {has_timing}"
        })
        score_parts.append(0.10 if has_timing else 0.0)
    except Exception as e:
        checks.append({"name": "memory.md timing", "passed": False, "detail": str(e)})
        score_parts.append(0.0)

    # ── CHECK 4: history.md was updated (not empty after briefing) ────────────
    try:
        history_path = news_dir / "history.md"
        assert history_path.exists(), "history.md does not exist"
        history_content = history_path.read_text().strip()
        history_updated = len(history_content) > 20
        checks.append({
            "name": "history.md updated after briefing delivery",
            "passed": history_updated,
            "detail": f"history.md length={len(history_content)} chars. Snippet: {history_content[:200]}"
        })
        score_parts.append(0.10 if history_updated else 0.0)
    except Exception as e:
        checks.append({"name": "history.md updated", "passed": False, "detail": str(e)})
        score_parts.append(0.0)

    # ── CHECK 5: sources.md updated with at least 2 sources ───────────────────
    try:
        sources_path = news_dir / "sources.md"
        assert sources_path.exists(), "sources.md does not exist"
        sources_content = sources_path.read_text()
        # Count lines that look like source entries (start with - or contain publication names)
        source_lines = [l for l in sources_content.splitlines() if re.match(r'\s*[-*•]', l) and len(l.strip()) > 5]
        has_two_sources = len(source_lines) >= 2
        checks.append({
            "name": "sources.md has at least 2 source entries",
            "passed": has_two_sources,
            "detail": f"Found {len(source_lines)} source lines. Content: {sources_content[:400]}"
        })
        score_parts.append(0.10 if has_two_sources else 0.0)
    except Exception as e:
        checks.append({"name": "sources.md updated", "passed": False, "detail": str(e)})
        score_parts.append(0.0)

    # ── CHECK 6: Briefing file exists in ~/news/ ──────────────────────────────
    # Agent should produce a briefing document
    briefing_files = list(news_dir.glob("briefing*.md")) + \
                     list(news_dir.glob("briefing*.txt")) + \
                     list(Path(workspace_dir).rglob("briefing*.md")) + \
                     list(Path(workspace_dir).rglob("briefing*.txt")) + \
                     list(news_dir.glob("*briefing*"))
    # Also accept morning_briefing or daily_briefing patterns anywhere
    briefing_files += list(Path(workspace_dir).rglob("*briefing*"))
    briefing_files = [f for f in briefing_files if f.is_file()]
    # Deduplicate
    briefing_files = list({str(f): f for f in briefing_files}.values())

    briefing_exists = len(briefing_files) > 0
    briefing_content = ""
    if briefing_exists:
        briefing_content = briefing_files[0].read_text()

    checks.append({
        "name": "A briefing file was created",
        "passed": briefing_exists,
        "detail": f"Found {len(briefing_files)} briefing file(s): {[str(f) for f in briefing_files[:3]]}"
    })
    score_parts.append(0.05 if briefing_exists else 0.0)

    # ── CHECK 7: Briefing uses bullet format ──────────────────────────────────
    try:
        if not briefing_content:
            raise ValueError("No briefing content to check")
        bullet_lines = [l for l in briefing_content.splitlines() if re.match(r'\s*[-*•]', l)]
        has_bullets = len(bullet_lines) >= 3
        checks.append({
            "name": "Briefing uses bullet point format (>=3 bullets)",
            "passed": has_bullets,
            "detail": f"Found {len(bullet_lines)} bullet lines in briefing."
        })
        score_parts.append(0.05 if has_bullets else 0.0)
    except Exception as e:
        checks.append({"name": "Briefing bullet format", "passed": False, "detail": str(e)})
        score_parts.append(0.0)

    # ── CHECK 8: Briefing has max 5-7 items (morning briefing cap) ────────────
    try:
        if not briefing_content:
            raise ValueError("No briefing content to check")
        # Count distinct news items: headings or top-level bullets that look like news items
        # Strategy: count lines starting with '- ' or '* ' or numbered items at top level
        top_bullets = [l for l in briefing_content.splitlines()
                       if re.match(r'^[-*•]\s+\S', l) or re.match(r'^\d+\.\s+\S', l)]
        # Also count level-1 markdown headers as potential items (## Item)
        headers = [l for l in briefing_content.splitlines() if re.match(r'^#{1,3}\s+\S', l)
                   and not re.match(r'^#\s+(morning|briefing|news|daily)', l, re.IGNORECASE)]

        item_count = max(len(top_bullets), len(headers))
        # Allow 1-7 items; 0 means we couldn't parse it (partial credit if exists)
        within_limit = 1 <= item_count <= 7
        checks.append({
            "name": "Morning briefing respects 5-7 item maximum",
            "passed": within_limit,
            "detail": f"Detected ~{item_count} top-level items (top_bullets={len(top_bullets)}, headers={len(headers)}). Limit is max 7."
        })
        score_parts.append(0.10 if within_limit else 0.0)
    except Exception as e:
        checks.append({"name": "Briefing item count limit", "passed": False, "detail": str(e)})
        score_parts.append(0.0)

    # ── CHECK 9: Multi-source on contested/regulatory topic ───────────────────
    try:
        if not briefing_content:
            raise ValueError("No briefing content to check")
        # Must cite at least 2 distinct named sources in the briefing
        # Look for patterns like "Source:", "via ", "(Reuters)", "—Bloomberg", etc.
        source_citations = re.findall(
            r'(?:via|source[s]?:|—|–|-)\s*([A-Z][A-Za-z\s&]+(?:News|Times|Post|Journal|Review|Wire|Watch|Report|Block|Desk|Brief|Reuters|Bloomberg|FT|WSJ|CoinDesk|Decrypt|Politico|Protocol|Axios)?)',
            briefing_content
        )
        # Also look for parenthetical citations
        paren_sources = re.findall(r'\(([A-Z][A-Za-z\s&]{3,30})\)', briefing_content)
        all_sources = source_citations + paren_sources
        unique_sources = set(s.strip().lower() for s in all_sources if len(s.strip()) > 2)

        # Alternative: check if at least 2 publication names appear anywhere
        known_outlets = [
            'reuters', 'bloomberg', 'wsj', 'wall street journal', 'ft', 'financial times',
            'coindesk', 'decrypt', 'the block', 'politico', 'axios', 'protocol', 'wired',
            'techcrunch', 'the information', 'ars technica', 'hugging face', 'sec.gov',
            'cointelegraph', 'morning brew', 'bankless', 'fortune', 'forbes'
        ]
        content_lower = briefing_content.lower()
        found_outlets = [o for o in known_outlets if o in content_lower]

        multi_source = len(unique_sources) >= 2 or len(found_outlets) >= 2
        checks.append({
            "name": "Briefing cites at least 2 distinct named sources",
            "passed": multi_source,
            "detail": f"Unique source refs={len(unique_sources)}, known outlets found={found_outlets[:5]}"
        })
        score_parts.append(0.10 if multi_source else 0.0)
    except Exception as e:
        checks.append({"name": "Multi-source citation", "passed": False, "detail": str(e)})
        score_parts.append(0.0)

    # ── CHECK 10: Briefing includes timestamps / "when news broke" ────────────
    try:
        if not briefing_content:
            raise ValueError("No briefing content to check")
        # Look for date patterns: "Jan", "2024", "yesterday", "Monday", etc.
        has_dates = bool(re.search(
            r'\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\b'
            r'|\b20\d{2}\b'
            r'|\b(yesterday|today|monday|tuesday|wednesday|thursday|friday|this week|last week)\b'
            r'|\b\d{1,2}/\d{1,2}/\d{2,4}\b',
            briefing_content, re.IGNORECASE
        ))
        checks.append({
            "name": "Briefing includes timing/date information for news items",
            "passed": has_dates,
            "detail": f"Date/time references found: {has_dates}"
        })
        score_parts.append(0.10 if has_dates else 0.0)
    except Exception as e:
        checks.append({"name": "Briefing timing info", "passed": False, "detail": str(e)})
        score_parts.append(0.0)

    # ── Final scoring ─────────────────────────────────────────────────────────
    total_score = sum(score_parts)
    all_passed = all(c["passed"] for c in checks)

    # Must pass at minimum: profile proportions, format, item limit, multi-source
    critical_checks = [checks[0]["passed"],  # proportions
                       checks[5]["passed"],  # briefing exists
                       checks[7]["passed"],  # item limit
                       checks[8]["passed"]]  # multi-source
    passed = all(critical_checks) and total_score >= 0.55

    return {
        "passed": passed,
        "score": round(total_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))