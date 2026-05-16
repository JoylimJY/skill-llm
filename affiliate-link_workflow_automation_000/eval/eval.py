import sys
import json
import re
from pathlib import Path

workspace = Path(sys.argv[1])
checks = []
total_score = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# PART 1: Link Database — short_url naming convention
# Expected: moltworker-[ID]-[usage]  e.g. moltworker-003-note
# ═══════════════════════════════════════════════════════════════════════════════

DB_NAMING_PATTERN = re.compile(r'^moltworker-\d{3}-\S+$')

try:
    db_path = workspace / "affiliate/links/link_database.json"
    with open(db_path, encoding="utf-8") as f:
        db = json.load(f)

    db_by_id = {item["id"]: item for item in db}

    # Check ID 003 (Claude Pro) - was missing short_url
    item_003 = db_by_id.get("003", {})
    short_003 = item_003.get("short_url", "").strip()
    ok_003 = bool(short_003) and bool(DB_NAMING_PATTERN.match(short_003)) and "003" in short_003
    total_score += add_check(
        "link_db_003_short_url_naming",
        ok_003,
        f"ID=003 short_url='{short_003}'. Must match 'moltworker-003-<usage>' pattern. Got: {'OK' if ok_003 else 'FAIL'}",
        weight=1.0
    )

    # Check ID 007 (Notion) - had wrong naming (bit.ly/notion-mw)
    item_007 = db_by_id.get("007", {})
    short_007 = item_007.get("short_url", "").strip()
    ok_007 = bool(short_007) and bool(DB_NAMING_PATTERN.match(short_007)) and "007" in short_007
    total_score += add_check(
        "link_db_007_short_url_fixed",
        ok_007,
        f"ID=007 short_url='{short_007}'. Old value 'bit.ly/notion-mw' must be corrected to moltworker-007-<usage>. Got: {'OK' if ok_007 else 'FAIL'}",
        weight=1.0
    )

    # Check ID 012 (Udemy) - had 'moltworker-udemy' (missing ID and usage suffix)
    item_012 = db_by_id.get("012", {})
    short_012 = item_012.get("short_url", "").strip()
    ok_012 = bool(short_012) and bool(DB_NAMING_PATTERN.match(short_012)) and "012" in short_012
    total_score += add_check(
        "link_db_012_short_url_fixed",
        ok_012,
        f"ID=012 short_url='{short_012}'. Old 'moltworker-udemy' must be 'moltworker-012-<usage>'. Got: {'OK' if ok_012 else 'FAIL'}",
        weight=1.0
    )

    # Check ID 015 (Cloudflare) - was missing short_url
    item_015 = db_by_id.get("015", {})
    short_015 = item_015.get("short_url", "").strip()
    ok_015 = bool(short_015) and bool(DB_NAMING_PATTERN.match(short_015)) and "015" in short_015
    total_score += add_check(
        "link_db_015_short_url_naming",
        ok_015,
        f"ID=015 short_url='{short_015}'. Must match 'moltworker-015-<usage>' pattern. Got: {'OK' if ok_015 else 'FAIL'}",
        weight=1.0
    )

except Exception as e:
    for name in ["link_db_003_short_url_naming", "link_db_007_short_url_fixed",
                 "link_db_012_short_url_fixed", "link_db_015_short_url_naming"]:
        checks.append({"name": name, "passed": False, "detail": f"Exception: {e}"})


# ═══════════════════════════════════════════════════════════════════════════════
# PART 2: X Post — Claude review (draft_claude_review.txt)
# Rules: 1 link max, body then 👉 商品名（PR）, short URL format
# ═══════════════════════════════════════════════════════════════════════════════

def find_processed_x_post(name_hint):
    """Search published or drafts area for the processed version."""
    # Check published first
    for p in (workspace / "content/published/x_posts").rglob("*"):
        if name_hint in p.name and p.is_file():
            return p
    # Check if draft was overwritten
    draft = workspace / f"content/drafts/x_posts/{name_hint}"
    if draft.exists():
        return draft
    # Broader search
    for p in workspace.rglob(f"*{name_hint.replace('.txt','')}*"):
        if p.is_file() and p.suffix in (".txt", ".md"):
            return p
    return None

PR_KANJI_PATTERN = re.compile(r'（PR）|（広告）|（アフィリエイト）|\(PR\)|\(広告\)')
ARROW_PR_PATTERN = re.compile(r'👉\s*.+（PR）')
MOLTWORKER_SHORT = re.compile(r'moltworker-\d{3}-\S+')

try:
    claude_post_path = find_processed_x_post("draft_claude_review.txt")
    if claude_post_path is None:
        raise FileNotFoundError("Processed claude review X post not found")
    content = claude_post_path.read_text(encoding="utf-8")

    # Must have PR disclosure
    has_pr = bool(PR_KANJI_PATTERN.search(content))
    total_score += add_check(
        "x_claude_has_pr_disclosure",
        has_pr,
        f"Claude review post must contain PR disclosure （PR）. Found: {has_pr}",
        weight=1.0
    )

    # Must have 👉 format with (PR)
    has_arrow_format = bool(ARROW_PR_PATTERN.search(content))
    total_score += add_check(
        "x_claude_arrow_pr_format",
        has_arrow_format,
        f"Claude review post must use '👉 商品名（PR）' format. Found pattern: {has_arrow_format}",
        weight=1.0
    )

    # Must use short URL (moltworker-003-*)
    has_short_url = bool(re.search(r'moltworker-003-\S+', content))
    total_score += add_check(
        "x_claude_uses_short_url",
        has_short_url,
        f"Claude review post must use short URL 'moltworker-003-<usage>'. Found: {has_short_url}. Content snippet: {content[:300]}",
        weight=1.0
    )

    # Must NOT contain the raw long URL anymore
    has_raw_url = "claude.ai/upgrade" in content
    total_score += add_check(
        "x_claude_no_raw_url",
        not has_raw_url,
        f"Raw URL 'claude.ai/upgrade' should be replaced by short URL. Still present: {has_raw_url}",
        weight=0.5
    )

except Exception as e:
    for name in ["x_claude_has_pr_disclosure", "x_claude_arrow_pr_format",
                 "x_claude_uses_short_url", "x_claude_no_raw_url"]:
        checks.append({"name": name, "passed": False, "detail": f"Exception: {e}"})


# ═══════════════════════════════════════════════════════════════════════════════
# PART 3: X Post — Tools combo (draft_tools_combo.txt)
# Rule: ONLY 1 link allowed per X post — must remove one link
# ═══════════════════════════════════════════════════════════════════════════════

try:
    combo_path = find_processed_x_post("draft_tools_combo.txt")
    if combo_path is None:
        raise FileNotFoundError("Processed tools combo X post not found")
    content = combo_path.read_text(encoding="utf-8")

    # Count links - should be at most 1 affiliate link (short URL format)
    all_http_links = re.findall(r'https?://\S+|moltworker-\d{3}-\S+', content)
    # Count lines or occurrences that look like affiliate links (short or long)
    affiliate_links = [l for l in all_http_links if
                       any(x in l for x in ["notion", "cloudflare", "moltworker"])]
    at_most_one = len(affiliate_links) <= 1
    total_score += add_check(
        "x_combo_max_one_link",
        at_most_one,
        f"X post must have at most 1 affiliate link. Found {len(affiliate_links)}: {affiliate_links}",
        weight=1.5
    )

    # Must still have PR disclosure
    has_pr = bool(PR_KANJI_PATTERN.search(content))
    total_score += add_check(
        "x_combo_has_pr_disclosure",
        has_pr,
        f"Remaining tools combo post must have PR disclosure. Found: {has_pr}",
        weight=1.0
    )

    # Must use 👉 format
    has_arrow_format = bool(ARROW_PR_PATTERN.search(content))
    total_score += add_check(
        "x_combo_arrow_pr_format",
        has_arrow_format,
        f"Tools combo post must use '👉 商品名（PR）' format. Found: {has_arrow_format}",
        weight=1.0
    )

except Exception as e:
    for name in ["x_combo_max_one_link", "x_combo_has_pr_disclosure", "x_combo_arrow_pr_format"]:
        checks.append({"name": name, "passed": False, "detail": f"Exception: {e}"})


# ═══════════════════════════════════════════════════════════════════════════════
# PART 4: X Post — Udemy promo (draft_udemy_promo.txt)
# Rule: PR must be 直前または直後 of link, AND in prominent position, NOT at very end after link
# ═══════════════════════════════════════════════════════════════════════════════

try:
    udemy_path = find_processed_x_post("draft_udemy_promo.txt")
    if udemy_path is None:
        raise FileNotFoundError("Processed udemy X post not found")
    content = udemy_path.read_text(encoding="utf-8")

    # Must have PR in the 👉 line (integrated, not dangling at end after blank lines)
    has_arrow_with_pr = bool(ARROW_PR_PATTERN.search(content))
    total_score += add_check(
        "x_udemy_pr_integrated_with_link",
        has_arrow_with_pr,
        f"Udemy post: PR must be integrated with link using '👉 Udemy（PR）' format, not trailing separately. Found arrow+PR pattern: {has_arrow_with_pr}",
        weight=1.0
    )

    # Must use short URL for Udemy (moltworker-012-*)
    has_short_012 = bool(re.search(r'moltworker-012-\S+', content))
    total_score += add_check(
        "x_udemy_uses_correct_short_url",
        has_short_012,
        f"Udemy post must use 'moltworker-012-<usage>' short URL. Found: {has_short_012}",
        weight=1.0
    )

    # The old dangling "※PR" at end after link should NOT be the only disclosure
    # (i.e., disclosure must appear before or right with link, not just trailing)
    lines = [l.strip() for l in content.strip().splitlines() if l.strip()]
    # Check that PR isn't ONLY at the very last line disconnected from link line
    last_line_only_pr = len(lines) > 0 and re.match(r'^[※＊\*]?PR$', lines[-1], re.IGNORECASE)
    if last_line_only_pr and not has_arrow_with_pr:
        pr_placement_ok = False
    else:
        pr_placement_ok = has_arrow_with_pr
    total_score += add_check(
        "x_udemy_pr_not_only_trailing",
        pr_placement_ok,
        f"PR disclosure must not be only a trailing '※PR' after the link. Must be integrated. OK: {pr_placement_ok}",
        weight=0.5
    )

except Exception as e:
    for name in ["x_udemy_pr_integrated_with_link", "x_udemy_uses_correct_short_url",
                 "x_udemy_pr_not_only_trailing"]:
        checks.append({"name": name, "passed": False, "detail": f"Exception: {e}"})


# ═══════════════════════════════════════════════════════════════════════════════
# PART 5: Note article — draft_ai_productivity.txt
# Rules: PR disclosure at article TOP, ▼ 関連商品 section at end or mid, （PR） tag on products
# ═══════════════════════════════════════════════════════════════════════════════

def find_processed_note(name_hint):
    for p in (workspace / "content/published/note_articles").rglob("*"):
        if name_hint in p.name and p.is_file():
            return p
    draft = workspace / f"content/drafts/note_articles/{name_hint}"
    if draft.exists():
        return draft
    for p in workspace.rglob(f"*{name_hint.replace('.txt','')}*"):
        if p.is_file() and p.suffix in (".txt", ".md"):
            return p
    return None

try:
    note_path = find_processed_note("draft_ai_productivity.txt")
    if note_path is None:
        raise FileNotFoundError("Processed Note article not found")
    content = note_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    # Check PR disclosure at TOP of article (within first 5 non-empty lines)
    top_lines = [l for l in lines[:10] if l.strip()]
    top_pr = any(
        re.search(r'PR|広告|アフィリエイト|リンクから購入|ステマ', line)
        for line in top_lines
    )
    total_score += add_check(
        "note_pr_at_top",
        top_pr,
        f"Note article must have PR disclosure in the first ~5 lines. Top lines: {top_lines[:5]}. Found: {top_pr}",
        weight=1.5
    )

    # Check ▼ 関連商品 section exists
    has_related_section = "▼ 関連商品" in content or "▼関連商品" in content
    total_score += add_check(
        "note_has_related_products_section",
        has_related_section,
        f"Note article must contain '▼ 関連商品' section. Found: {has_related_section}",
        weight=1.5
    )

    # Check that products in ▼ 関連商品 section have （PR） tag
    related_section_match = re.search(r'▼\s*関連商品(.+?)(?=\n#|\Z)', content, re.DOTALL)
    if related_section_match:
        related_text = related_section_match.group(1)
        has_pr_in_related = bool(PR_KANJI_PATTERN.search(related_text))
    else:
        has_pr_in_related = False
    total_score += add_check(
        "note_related_section_has_pr_tags",
        has_pr_in_related,
        f"Products in '▼ 関連商品' must have （PR） tags. Found PR in section: {has_pr_in_related}",
        weight=1.0
    )

    # Check that raw inline affiliate URLs in body are accompanied by PR or replaced properly
    # (The original had raw URLs inline with no PR disclosure)
    body_has_pr = bool(PR_KANJI_PATTERN.search(content))
    total_score += add_check(
        "note_overall_pr_disclosure_present",
        body_has_pr,
        f"Note article must have PR disclosure somewhere in the body. Found: {body_has_pr}",
        weight=0.5
    )

    # Check short URL usage in ▼ 関連商品 section (at least one moltworker short URL)
    has_short_url_in_note = bool(MOLTWORKER_SHORT.search(content))
    total_score += add_check(
        "note_uses_short_urls",
        has_short_url_in_note,
        f"Note article should use moltworker-XXX-<usage> short URLs. Found: {has_short_url_in_note}",
        weight=1.0
    )

except Exception as e:
    for name in ["note_pr_at_top", "note_has_related_products_section",
                 "note_related_section_has_pr_tags", "note_overall_pr_disclosure_present",
                 "note_uses_short_urls"]:
        checks.append({"name": name, "passed": False, "detail": f"Exception: {e}"})


# ═══════════════════════════════════════════════════════════════════════════════
# Final scoring
# ═══════════════════════════════════════════════════════════════════════════════

MAX_SCORE = (
    1.0 * 4 +    # DB checks (003, 007, 012, 015)
    1.0 + 1.0 + 1.0 + 0.5 +   # Claude X post
    1.5 + 1.0 + 1.0 +          # Combo X post
    1.0 + 1.0 + 0.5 +          # Udemy X post
    1.5 + 1.5 + 1.0 + 0.5 + 1.0  # Note article
)

normalized_score = round(total_score / MAX_SCORE, 4)
all_passed = all(c["passed"] for c in checks)

print(json.dumps({
    "passed": all_passed,
    "score": normalized_score,
    "checks": checks
}, ensure_ascii=False, indent=2))