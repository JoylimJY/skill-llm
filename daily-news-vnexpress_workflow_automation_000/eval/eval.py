import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    VALID_TOPICS = [
        "tin-moi-nhat", "the-gioi", "thoi-su", "kinh-doanh", "giai-tri",
        "the-thao", "phap-luat", "giao-duc", "tin-noi-bat", "suc-khoe",
        "doi-song", "du-lich", "khoa-hoc-cong-nghe", "oto-xe-may",
        "y-kien", "tam-su", "cuoi", "tin-xem-nhieu"
    ]

    # Expected topic classifications for the task:
    # "business/economy" -> "kinh-doanh"
    # "science/technology" -> "khoa-hoc-cong-nghe"
    # "entertainment" -> "giai-tri"
    EXPECTED_TOPICS = {"kinh-doanh", "khoa-hoc-cong-nghe", "giai-tri"}

    # ----------------------------------------------------------------
    # CHECK 1: morning_brief.md exists somewhere in workspace
    # ----------------------------------------------------------------
    check_name = "morning_brief_report_exists"
    try:
        matches = list(workspace.rglob("morning_brief.md"))
        if not matches:
            checks.append({"name": check_name, "passed": False,
                           "detail": "File 'morning_brief.md' not found anywhere in workspace."})
        else:
            report_path = matches[0]
            checks.append({"name": check_name, "passed": True,
                           "detail": f"Found at: {report_path}"})
            total_score += 0.15
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ----------------------------------------------------------------
    # CHECK 2: Report contains content from at least 2 of the 3 expected topics
    # ----------------------------------------------------------------
    check_name = "report_covers_required_topics"
    try:
        report_files = list(workspace.rglob("morning_brief.md"))
        if not report_files:
            checks.append({"name": check_name, "passed": False,
                           "detail": "Cannot check: morning_brief.md not found."})
        else:
            content = report_files[0].read_text(encoding="utf-8", errors="replace").lower()
            # Check that at least 2 of the 3 exact topic slugs appear in the file
            # (agent may write topic names or translated equivalents; also check English keywords)
            topic_indicators = {
                "kinh-doanh": ["kinh-doanh", "kinh doanh", "business", "economy", "economic", "finance"],
                "khoa-hoc-cong-nghe": ["khoa-hoc-cong-nghe", "khoa hoc", "technology", "science", "tech", "cong nghe"],
                "giai-tri": ["giai-tri", "giai trí", "entertainment", "showbiz", "celebrity", "giai tri"],
            }
            covered = 0
            topic_detail = []
            for topic, indicators in topic_indicators.items():
                found = any(ind in content for ind in indicators)
                if found:
                    covered += 1
                topic_detail.append(f"{topic}: {'YES' if found else 'NO'}")
            passed = covered >= 2
            checks.append({"name": check_name, "passed": passed,
                           "detail": f"Topics covered ({covered}/3): {'; '.join(topic_detail)}"})
            if passed:
                total_score += 0.20
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ----------------------------------------------------------------
    # CHECK 3: Report has meaningful content (not empty, not just headers)
    # At least 200 characters and mentions actual article titles/summaries
    # ----------------------------------------------------------------
    check_name = "report_has_substantive_content"
    try:
        report_files = list(workspace.rglob("morning_brief.md"))
        if not report_files:
            checks.append({"name": check_name, "passed": False,
                           "detail": "Cannot check: morning_brief.md not found."})
        else:
            content = report_files[0].read_text(encoding="utf-8", errors="replace")
            # Must have real content - at least 200 chars
            # Must have more than just placeholders (check for actual URLs or title-like lines)
            has_length = len(content.strip()) >= 200
            has_links = "vnexpress.net" in content.lower() or "http" in content.lower()
            passed = has_length and has_links
            checks.append({"name": check_name, "passed": passed,
                           "detail": f"Length: {len(content.strip())} chars, has_links: {has_links}"})
            if passed:
                total_score += 0.25
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ----------------------------------------------------------------
    # CHECK 4: Agent used valid topic slugs (not invented ones like "business", "technology")
    # Look in USERS.md or any shell history or output files for evidence
    # ----------------------------------------------------------------
    check_name = "used_valid_predefined_topic_slugs"
    try:
        # Search all text files in workspace for evidence of correct topic slug usage
        evidence_files = []
        for ext in ["*.md", "*.txt", "*.log", "*.sh", "*.json"]:
            evidence_files.extend(workspace.rglob(ext))

        all_text = ""
        for f in evidence_files:
            try:
                all_text += f.read_text(encoding="utf-8", errors="replace") + "\n"
            except:
                pass

        # Check that at least 2 of the correct slugs appear somewhere
        correct_slugs_found = [t for t in EXPECTED_TOPICS if t in all_text]

        # Also verify NO clearly wrong slugs were used as primary topics
        bad_slug_pattern = r'--topics\s+["\']?(business|technology|entertainment|science|economy)["\']?'
        bad_slugs_used = bool(re.search(bad_slug_pattern, all_text, re.IGNORECASE))

        passed = len(correct_slugs_found) >= 2 and not bad_slugs_used
        checks.append({"name": check_name, "passed": passed,
                       "detail": f"Correct slugs found: {correct_slugs_found}; Bad slugs detected: {bad_slugs_used}"})
        if passed:
            total_score += 0.15
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ----------------------------------------------------------------
    # CHECK 5: USERS.md exists and has been written with user behavior
    # (The skill mandates: "remember user behaviour and write to USERS.md")
    # ----------------------------------------------------------------
    check_name = "users_md_written_with_behavior"
    try:
        # USERS.md should be in the skill directory or workspace root
        users_md_candidates = list(workspace.rglob("USERS.md"))
        # Exclude the deprecated one in logs/
        valid_users_md = [
            f for f in users_md_candidates
            if "logs" not in str(f).lower() or f.stat().st_size > 100
        ]

        # Also accept the one in logs/ if it was updated (size > 100 chars with real content)
        all_users_md = users_md_candidates

        found_valid = False
        detail_parts = []
        for um in all_users_md:
            try:
                text = um.read_text(encoding="utf-8", errors="replace")
                # Must contain actual user behavior info (topics, preferences, timestamps, etc.)
                has_topic_info = any(t in text.lower() for t in [
                    "kinh-doanh", "khoa-hoc", "giai-tri", "topic", "business",
                    "technology", "entertainment", "preference", "user", "request"
                ])
                is_not_just_deprecated = "do not edit" not in text.lower() or len(text) > 200
                if has_topic_info and is_not_just_deprecated and len(text.strip()) > 50:
                    found_valid = True
                    detail_parts.append(f"Valid USERS.md at {um} (len={len(text)})")
            except:
                pass

        checks.append({"name": check_name, "passed": found_valid,
                       "detail": "; ".join(detail_parts) if detail_parts else
                       f"No valid USERS.md found. Candidates: {[str(f) for f in all_users_md]}"})
        if found_valid:
            total_score += 0.15
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ----------------------------------------------------------------
    # CHECK 6: Count of articles - agent requested at least 4 per topic (per task prompt: "4-5 per category")
    # ----------------------------------------------------------------
    check_name = "article_count_per_topic_adequate"
    try:
        report_files = list(workspace.rglob("morning_brief.md"))
        if not report_files:
            checks.append({"name": check_name, "passed": False,
                           "detail": "Cannot check: morning_brief.md not found."})
        else:
            content = report_files[0].read_text(encoding="utf-8", errors="replace")
            # Count how many article links appear (vnexpress.net links)
            vnexpress_links = re.findall(r'https?://[^\s\)\"\']+vnexpress\.net[^\s\)\"\']*', content)
            unique_links = set(vnexpress_links)
            # Expect at least 3 topics * 4 articles = 12 articles minimum, or reasonable coverage
            # Be lenient: at least 6 distinct articles referenced
            passed = len(unique_links) >= 6
            checks.append({"name": check_name, "passed": passed,
                           "detail": f"Unique VNExpress article links found: {len(unique_links)}"})
            if passed:
                total_score += 0.10
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ----------------------------------------------------------------
    # Final scoring
    # ----------------------------------------------------------------
    overall_passed = sum(1 for c in checks if c["passed"]) >= 4  # Must pass at least 4/6 checks

    result = {
        "passed": overall_passed,
        "score": round(min(total_score, 1.0), 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "invocation", "passed": False,
                                      "detail": "No workspace path provided."}]}))
        sys.exit(1)
    evaluate(sys.argv[1])