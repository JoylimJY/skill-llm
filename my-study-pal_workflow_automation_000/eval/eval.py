import sys
import json
import re
from pathlib import Path
from datetime import datetime

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── HELPER ───────────────────────────────────────────────────────────────
    def find_study_dir():
        """Find the learning project directory under mystudy/ with correct naming."""
        mystudy = workspace / "mystudy"
        if not mystudy.exists():
            return None
        # Pattern: <topic>-<YYYY-MM-DD> — must be a directory
        pattern = re.compile(r'.+-\d{4}-\d{2}-\d{2}$')
        candidates = [d for d in mystudy.iterdir()
                      if d.is_dir() and pattern.match(d.name)
                      and d.name != "数据分析_旧版"]
        return candidates[0] if candidates else None

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 1: Study directory exists with correct naming convention
    # ══════════════════════════════════════════════════════════════════════════
    study_dir = find_study_dir()
    if study_dir:
        dir_name = study_dir.name
        # Must contain a date suffix
        date_match = re.search(r'-(\d{4}-\d{2}-\d{2})$', dir_name)
        date_valid = False
        if date_match:
            try:
                datetime.strptime(date_match.group(1), "%Y-%m-%d")
                date_valid = True
            except ValueError:
                pass
        topic_part = dir_name[:date_match.start()] if date_match else dir_name
        has_chinese_or_topic = len(topic_part) > 0
        passed = date_valid and has_chinese_or_topic
        total_score += add_check(
            "study_dir_naming_convention",
            passed,
            f"Found directory: '{dir_name}'. Date valid: {date_valid}, topic non-empty: {has_chinese_or_topic}",
            weight=1.0
        )
    else:
        total_score += add_check(
            "study_dir_naming_convention",
            False,
            "No valid study directory found under mystudy/ matching <topic>-<YYYY-MM-DD> pattern.",
            weight=1.0
        )

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 2: roadmap.md exists and has correct structure
    # ══════════════════════════════════════════════════════════════════════════
    roadmap_path = (study_dir / "roadmap.md") if study_dir else None
    roadmap_content = ""
    try:
        if roadmap_path and roadmap_path.exists():
            roadmap_content = roadmap_path.read_text(encoding="utf-8")
            # Must have a list of knowledge points (bullet points or numbered)
            has_list = bool(re.search(r'(^[-*\d]\.?\s+.+)', roadmap_content, re.MULTILINE))
            # Must NOT have deeply expanded sub-sections with extensive paragraphs
            # (i.e., no paragraph longer than 3 consecutive lines of prose)
            paragraphs = [p.strip() for p in roadmap_content.split('\n\n') if p.strip()]
            long_prose = any(
                len([line for line in p.split('\n') if line.strip() and not line.strip().startswith('#')]) > 5
                for p in paragraphs
            )
            passed = has_list and not long_prose
            total_score += add_check(
                "roadmap_structure",
                passed,
                f"roadmap.md found. Has list: {has_list}. Has over-expanded prose: {long_prose}.",
                weight=1.5
            )
        else:
            total_score += add_check(
                "roadmap_structure",
                False,
                f"roadmap.md not found at expected path.",
                weight=1.5
            )
    except Exception as e:
        total_score += add_check("roadmap_structure", False, f"Error reading roadmap.md: {e}", weight=1.5)

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 3: roadmap.md contains data-analysis-relevant knowledge points
    # ══════════════════════════════════════════════════════════════════════════
    try:
        if roadmap_content:
            # Should contain data analysis keywords
            keywords = ['数据', 'data', '分析', '统计', '均值', '平均', 'SQL', 'Excel',
                        '可视化', '指标', '图表', '清洗', '趋势', '汇总']
            found_kw = [kw for kw in keywords if kw.lower() in roadmap_content.lower()]
            passed = len(found_kw) >= 3
            total_score += add_check(
                "roadmap_relevant_content",
                passed,
                f"Found {len(found_kw)} relevant keywords: {found_kw[:5]}",
                weight=1.0
            )
        else:
            total_score += add_check(
                "roadmap_relevant_content", False,
                "roadmap.md empty or missing.", weight=1.0
            )
    except Exception as e:
        total_score += add_check("roadmap_relevant_content", False, str(e), weight=1.0)

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 4: sessions/session-01.md exists
    # ══════════════════════════════════════════════════════════════════════════
    session_path = None
    session_content = ""
    try:
        if study_dir:
            sessions_dir = study_dir / "sessions"
            # Accept session-01.md or session01.md (primary: session-01.md)
            candidates = list(sessions_dir.glob("session*01*")) if sessions_dir.exists() else []
            # Prefer session-01.md
            exact = sessions_dir / "session-01.md" if sessions_dir.exists() else None
            if exact and exact.exists():
                session_path = exact
            elif candidates:
                session_path = candidates[0]
        
        if session_path and session_path.exists():
            session_content = session_path.read_text(encoding="utf-8")
            # Must be the exact name session-01.md
            correct_name = session_path.name == "session-01.md"
            total_score += add_check(
                "session_file_exists_correct_name",
                correct_name,
                f"Session file found: {session_path.name}. Correct name (session-01.md): {correct_name}",
                weight=1.5
            )
        else:
            total_score += add_check(
                "session_file_exists_correct_name",
                False,
                "sessions/session-01.md not found.",
                weight=1.5
            )
    except Exception as e:
        total_score += add_check("session_file_exists_correct_name", False, str(e), weight=1.5)

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 5: session-01.md contains a case story (案例)
    # ══════════════════════════════════════════════════════════════════════════
    try:
        if session_content:
            story_keywords = ['案例', '故事', '比如', '举个例子', '有一次', '想象', '就像', '场景',
                               '小明', '有个', '曾经', '某']
            found = [kw for kw in story_keywords if kw in session_content]
            passed = len(found) >= 1
            total_score += add_check(
                "session_contains_case_story",
                passed,
                f"Story/case indicators found: {found}",
                weight=1.0
            )
        else:
            total_score += add_check("session_contains_case_story", False,
                                     "session-01.md empty or missing.", weight=1.0)
    except Exception as e:
        total_score += add_check("session_contains_case_story", False, str(e), weight=1.0)

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 6: session-01.md contains a Socratic question (引导式提问)
    # ══════════════════════════════════════════════════════════════════════════
    try:
        if session_content:
            # Questions should be present — look for question marks or choice-style prompts
            question_count = session_content.count('？') + session_content.count('?')
            # Should have at least 1 question
            # Also check for choice patterns: A. / B. / A) / B)
            has_choices = bool(re.search(r'[AB][.、）\)]\s*\S', session_content))
            passed = question_count >= 1 or has_choices
            total_score += add_check(
                "session_contains_socratic_question",
                passed,
                f"Question marks: {question_count}, has choices: {has_choices}",
                weight=1.0
            )
        else:
            total_score += add_check("session_contains_socratic_question", False,
                                     "session-01.md empty or missing.", weight=1.0)
    except Exception as e:
        total_score += add_check("session_contains_socratic_question", False, str(e), weight=1.0)

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 7: session-01.md contains a memory anchor (记忆锚点)
    # Key proprietary trap: many agents will forget this specific requirement
    # ══════════════════════════════════════════════════════════════════════════
    try:
        if session_content:
            anchor_keywords = ['记忆锚点', '锚点', '笑点', '反常', '有趣', '冷知识', '哈哈',
                                '😂', '🤣', '😄', '小彩蛋', '好玩', '段子', '其实', '反直觉',
                                '你可能不知道', '竟然', '居然', '意想不到', '神奇']
            found = [kw for kw in anchor_keywords if kw in session_content]
            # Also accept: explicit label like "【记忆锚点】" or "★"
            has_star = '★' in session_content or '【' in session_content
            passed = len(found) >= 1 or has_star
            total_score += add_check(
                "session_contains_memory_anchor",
                passed,
                f"Memory anchor indicators: {found[:5]}, has ★/【】: {has_star}",
                weight=2.0  # Higher weight — this is the proprietary trap
            )
        else:
            total_score += add_check("session_contains_memory_anchor", False,
                                     "session-01.md empty or missing.", weight=2.0)
    except Exception as e:
        total_score += add_check("session_contains_memory_anchor", False, str(e), weight=2.0)

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 8: user-profile.md has been updated (not just original content)
    # ══════════════════════════════════════════════════════════════════════════
    try:
        profile_path = workspace / "mystudy" / "user-profile.md"
        if profile_path.exists():
            profile_content = profile_path.read_text(encoding="utf-8")
            # Original had "暂无记录" in 历史学习 — it should now be updated
            original_history_empty = "暂无记录" in profile_content
            # Should have some new content — either updated date or new learning record
            has_update_indicators = (
                re.search(r'数据分析', profile_content) is not None or
                re.search(r'202[5-9]-\d{2}-\d{2}', profile_content) is not None or
                not original_history_empty
            )
            passed = has_update_indicators
            total_score += add_check(
                "user_profile_updated",
                passed,
                f"Profile updated with new info: {has_update_indicators}. Still has '暂无记录': {original_history_empty}",
                weight=1.0
            )
        else:
            total_score += add_check("user_profile_updated", False,
                                     "mystudy/user-profile.md not found.", weight=1.0)
    except Exception as e:
        total_score += add_check("user_profile_updated", False, str(e), weight=1.0)

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 9: A cron reminder file exists somewhere in workspace
    # (Module 6: cron 提醒 — based on user's stated next study time 21:00 weekdays)
    # ══════════════════════════════════════════════════════════════════════════
    try:
        cron_candidates = list(workspace.rglob("*cron*")) + list(workspace.rglob("*reminder*")) + \
                          list(workspace.rglob("*提醒*")) + list(workspace.rglob("*schedule*"))
        # Filter out the distractor reminders.txt (no cron expression)
        cron_files = []
        for cf in cron_candidates:
            if cf.is_file() and cf.name != "reminders.txt":
                try:
                    content = cf.read_text(encoding="utf-8", errors="ignore")
                    # Valid cron has 5 fields: min hour dom month dow
                    if re.search(r'\d+\s+\d+\s+[\d*]+\s+[\d*]+\s+[\d*]+', content):
                        cron_files.append((cf, content))
                except:
                    pass

        if cron_files:
            cf, content = cron_files[0]
            # The cron should reflect 21:00 — hour field should be 21
            has_21_hour = bool(re.search(r'\b\d+\s+21\s+', content))
            passed = True  # File exists with valid cron expression
            detail = f"Cron file found: {cf.name}. Contains 21:00 hour: {has_21_hour}. Content snippet: {content[:100]}"
        else:
            passed = False
            detail = "No cron reminder file with a valid cron expression found."

        total_score += add_check("cron_reminder_file_exists", passed, detail, weight=1.5)
    except Exception as e:
        total_score += add_check("cron_reminder_file_exists", False, str(e), weight=1.5)

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 10: roadmap.md has progress tracking markers
    # ══════════════════════════════════════════════════════════════════════════
    try:
        if roadmap_content:
            # Should have some progress indicators: [ ], [x], ✅, ❌, 进度, etc.
            progress_indicators = ['[ ]', '[x]', '[X]', '✅', '❌', '⬜', '🔲', '进度', '完成', '待学', '未开始']
            found = [p for p in progress_indicators if p in roadmap_content]
            passed = len(found) >= 1
            total_score += add_check(
                "roadmap_has_progress_tracking",
                passed,
                f"Progress indicators found: {found}",
                weight=0.5
            )
        else:
            total_score += add_check("roadmap_has_progress_tracking", False,
                                     "roadmap.md empty or missing.", weight=0.5)
    except Exception as e:
        total_score += add_check("roadmap_has_progress_tracking", False, str(e), weight=0.5)

    # ══════════════════════════════════════════════════════════════════════════
    # Final score calculation
    # ══════════════════════════════════════════════════════════════════════════
    max_score = 1.0 + 1.5 + 1.0 + 1.5 + 1.0 + 1.0 + 2.0 + 1.0 + 1.5 + 0.5  # = 12.0
    normalized_score = round(total_score / max_score, 3)
    passed_overall = normalized_score >= 0.65 and all(
        c["passed"] for c in checks
        if c["name"] in [
            "study_dir_naming_convention",
            "roadmap_structure",
            "session_file_exists_correct_name",
            "session_contains_memory_anchor"
        ]
    )

    return {
        "passed": passed_overall,
        "score": normalized_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))