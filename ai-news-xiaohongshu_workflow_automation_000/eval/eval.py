import sys
import json
import re
import os
from pathlib import Path
from datetime import datetime

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
skill_root = Path("/root/.openclaw/workspace/skills/ai-news-xiaohongshu")
output_base = skill_root / "output"

checks = []

def check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})
    print(f"[{'PASS' if passed else 'FAIL'}] {name}: {detail}")

# ─── 1. Find output directory ─────────────────────────────────────────
today_str = datetime.now().strftime("%Y-%m-%d")
out_dirs = []
try:
    if output_base.exists():
        out_dirs = [d for d in output_base.iterdir()
                    if d.is_dir() and d.name.startswith(today_str)]
except Exception as e:
    check("output_directory_exists", False, f"Cannot list output dir: {e}")

if out_dirs:
    # Use the most recent one
    out_dir = sorted(out_dirs)[-1]
    check("output_directory_exists", True,
          f"Found output dir: {out_dir.name}")
else:
    # Try to find ANY output directory (in case date is slightly off)
    try:
        all_dirs = [d for d in output_base.iterdir() if d.is_dir()] if output_base.exists() else []
        if all_dirs:
            out_dir = sorted(all_dirs)[-1]
            check("output_directory_exists", True,
                  f"Found output dir (non-today date): {out_dir.name}")
        else:
            check("output_directory_exists", False,
                  f"No output directories found under {output_base}")
            out_dir = None
    except Exception as e:
        check("output_directory_exists", False, f"Error scanning output: {e}")
        out_dir = None

# ─── 2. Check output dir naming convention ────────────────────────────
if out_dir:
    name = out_dir.name
    # Must match YYYY-MM-DD-NN pattern
    if re.match(r'^\d{4}-\d{2}-\d{2}-\d{2}$', name):
        check("output_dir_naming_convention", True,
              f"Dir name '{name}' matches YYYY-MM-DD-NN pattern")
    else:
        check("output_dir_naming_convention", False,
              f"Dir name '{name}' does NOT match required YYYY-MM-DD-NN pattern")

# ─── 3. Check all 4 required files exist ─────────────────────────────
required_files = [
    "xiaohongshu-copy.md",
    "cover.html",
    "news-summary.md",
    "sources.md"
]

if out_dir:
    for fname in required_files:
        fpath = out_dir / fname
        if fpath.exists() and fpath.stat().st_size > 0:
            check(f"file_exists_{fname}", True,
                  f"{fname} exists ({fpath.stat().st_size} bytes)")
        else:
            check(f"file_exists_{fname}", False,
                  f"{fname} is missing or empty in {out_dir}")
else:
    for fname in required_files:
        check(f"file_exists_{fname}", False, "No output dir found")

# ─── 4. Validate xiaohongshu-copy.md content ─────────────────────────
if out_dir and (out_dir / "xiaohongshu-copy.md").exists():
    try:
        copy_content = (out_dir / "xiaohongshu-copy.md").read_text(encoding="utf-8")

        # Must contain emoji
        emoji_pattern = re.compile(
            r'[\U0001F300-\U0001F9FF\U00002600-\U000027FF\U0000231A-\U0000231B]',
            re.UNICODE
        )
        emoji_count = len(emoji_pattern.findall(copy_content))
        check("copy_contains_emoji", emoji_count >= 3,
              f"Found {emoji_count} emoji characters (need >= 3)")

        # Must contain hashtags
        hashtag_count = len(re.findall(r'#\S+', copy_content))
        check("copy_contains_hashtags", hashtag_count >= 3,
              f"Found {hashtag_count} hashtags (need >= 3)")

        # Must NOT contain forbidden phrases (去AI化)
        forbidden = ["首先", "其次", "最后", "综上所述", "总之", "综上"]
        found_forbidden = [f for f in forbidden if f in copy_content]
        check("copy_no_forbidden_phrases", len(found_forbidden) == 0,
              f"Forbidden phrases found: {found_forbidden}" if found_forbidden else "No forbidden phrases detected")

        # Must contain actual news content from the input (not pure demo)
        # Check for at least some real company names from the input
        real_companies = ["Anthropic", "DeepSeek", "千问", "Qwen", "Google", "Gemini", "字节", "Seed"]
        found_companies = [c for c in real_companies if c in copy_content]
        check("copy_uses_real_news_data", len(found_companies) >= 2,
              f"Real company/product mentions found: {found_companies}")

        # Must contain interaction/引流 elements
        has_interaction = any(kw in copy_content for kw in ["关注", "评论", "收藏", "👇", "点赞"])
        check("copy_has_interaction_cta", has_interaction,
              "Contains interaction CTA (关注/评论/收藏/👇/点赞)")

    except Exception as e:
        check("copy_content_validation", False, f"Error reading copy: {e}")
else:
    check("copy_content_validation", False, "xiaohongshu-copy.md not found")

# ─── 5. Validate cover.html ───────────────────────────────────────────
if out_dir and (out_dir / "cover.html").exists():
    try:
        html_content = (out_dir / "cover.html").read_text(encoding="utf-8")

        # Must be valid HTML
        check("html_is_valid", "<html" in html_content and "</html>" in html_content,
              "HTML has opening and closing tags")

        # Must have 3:4 ratio specification (1080x1440 or equivalent ratio)
        has_ratio = (
            "1080" in html_content and "1440" in html_content
        ) or (
            re.search(r'width\s*:\s*1080', html_content) and
            re.search(r'height\s*:\s*1440', html_content)
        )
        check("html_has_3x4_ratio", has_ratio,
              "HTML specifies 1080x1440 (3:4) dimensions")

        # Must have multiple pages (1-3 screens)
        page_count = len(re.findall(r'class=["\'][^"\']*\bpage\b[^"\']*["\']', html_content))
        if page_count == 0:
            # Try alternate pattern
            page_count = len(re.findall(r'第[123]屏|page-[123]|screen-[123]', html_content))
        check("html_has_multiple_pages", 1 <= page_count <= 3,
              f"Found {page_count} page sections (need 1-3)")

        # Must have page divider (for screenshot separation)
        has_divider = "divider" in html_content or "page-divider" in html_content or \
                      "分隔" in html_content or "dividing" in html_content.lower()
        check("html_has_page_divider", has_divider,
              "HTML has inter-screen divider element")

        # Must contain gradient background (科技感)
        has_gradient = "gradient" in html_content or "linear-gradient" in html_content or \
                       "radial-gradient" in html_content
        check("html_has_gradient_bg", has_gradient,
              "HTML uses gradient background for tech aesthetic")

        # Must contain real news content (not just demo)
        real_companies_html = ["Anthropic", "DeepSeek", "千问", "Qwen", "Google", "Gemini", "字节", "Claude", "Seed"]
        found_in_html = [c for c in real_companies_html if c in html_content]
        check("html_uses_real_news_data", len(found_in_html) >= 2,
              f"Real content mentions in HTML: {found_in_html}")

    except Exception as e:
        check("html_content_validation", False, f"Error reading HTML: {e}")
else:
    check("html_content_validation", False, "cover.html not found")

# ─── 6. Validate news-summary.md ─────────────────────────────────────
if out_dir and (out_dir / "news-summary.md").exists():
    try:
        summary = (out_dir / "news-summary.md").read_text(encoding="utf-8")

        # Must be a markdown table
        has_table = "|" in summary and "---" in summary
        check("summary_has_table", has_table,
              "news-summary.md contains markdown table")

        # Must have expected columns
        has_time_col = "时间" in summary
        has_source_col = "来源" in summary or "公司" in summary or "项目" in summary
        check("summary_has_required_columns", has_time_col and has_source_col,
              f"Has '时间' col: {has_time_col}, has '来源/公司' col: {has_source_col}")

        # Must have at least 3 data rows
        data_rows = [l for l in summary.split('\n') if l.strip().startswith('|') and '---' not in l and ('时间' not in l)]
        check("summary_has_min_rows", len(data_rows) >= 3,
              f"Found {len(data_rows)} data rows in table (need >= 3)")

    except Exception as e:
        check("summary_validation", False, f"Error reading summary: {e}")
else:
    check("summary_validation", False, "news-summary.md not found")

# ─── 7. Validate sources.md ──────────────────────────────────────────
if out_dir and (out_dir / "sources.md").exists():
    try:
        sources = (out_dir / "sources.md").read_text(encoding="utf-8")

        # Must contain URLs
        urls = re.findall(r'https?://\S+', sources)
        check("sources_contains_urls", len(urls) >= 3,
              f"Found {len(urls)} URLs in sources.md (need >= 3)")

        # Must contain actual source URLs from the input news
        expected_domains = ["anthropic.com", "github.com", "qwenlm", "deepmind.google", "ByteDance"]
        found_domains = [d for d in expected_domains if d in sources]
        check("sources_contains_real_urls", len(found_domains) >= 2,
              f"Real source domains found: {found_domains}")

    except Exception as e:
        check("sources_validation", False, f"Error reading sources: {e}")
else:
    check("sources_validation", False, "sources.md not found")

# ─── 8. Verify real data was used (not just demo) ────────────────────
# Check that the script was called with --news-json, not just --use-demo
if out_dir and (out_dir / "cover.html").exists():
    try:
        html = (out_dir / "cover.html").read_text(encoding="utf-8")
        copy = (out_dir / "xiaohongshu-copy.md").read_text(encoding="utf-8") if (out_dir / "xiaohongshu-copy.md").exists() else ""

        # If using demo data, it would have 【演示】 markers or "演示模式"
        is_demo_only = "演示模式" in html and "演示模式" in copy and \
                       not any(c in html for c in ["Anthropic", "DeepSeek", "Claude", "Qwen"])
        check("uses_real_data_not_demo", not is_demo_only,
              "Content uses real news data, not just demo mode")
    except Exception as e:
        check("uses_real_data_not_demo", False, f"Error checking: {e}")

# ─── Compute final score ──────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = passed_count / total if total > 0 else 0.0
passed_overall = score >= 0.75  # Need at least 75% checks to pass

result = {
    "passed": passed_overall,
    "score": round(score, 3),
    "checks": checks
}

print("\n" + "="*60)
print(f"RESULT: {'PASSED' if passed_overall else 'FAILED'}")
print(f"Score: {passed_count}/{total} = {score:.1%}")
print("="*60)

print(json.dumps(result))