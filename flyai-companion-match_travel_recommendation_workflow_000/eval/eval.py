#!/usr/bin/env python3
import sys
import json
import re
import os
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    
    def find_output_file(workspace):
        """Find the recommendation report file"""
        candidates = []
        # Search for markdown or txt files that look like recommendations
        for ext in ['*.md', '*.txt']:
            for f in Path(workspace).rglob(ext):
                # Skip the distractor/input files we created
                skip_names = {'task_brief.md', 'user-profile.md', 'api.md', 'overview.json'}
                if f.name in skip_names:
                    continue
                if 'logs' in str(f) or 'projects' in str(f) or 'docs' in str(f):
                    continue
                candidates.append(f)
        return candidates

    # ── Check 1: Output file exists ──────────────────────────────────────────
    try:
        output_files = find_output_file(workspace_dir)
        # Also check for common expected names
        specific = list(Path(workspace_dir).rglob('recommendation_report.md')) + \
                   list(Path(workspace_dir).rglob('hangzhou_recommendation.md')) + \
                   list(Path(workspace_dir).rglob('杭州推荐.md')) + \
                   list(Path(workspace_dir).rglob('travel_recommendation.md')) + \
                   list(Path(workspace_dir).rglob('recommendation.md'))
        all_candidates = list(set(output_files + specific))
        
        if not all_candidates:
            checks.append({"name": "output_file_exists", "passed": False, "detail": "No recommendation report file found in workspace"})
            return {"passed": False, "score": 0.0, "checks": checks}
        
        # Use the largest file as the most likely candidate
        report_file = max(all_candidates, key=lambda f: f.stat().st_size)
        content = report_file.read_text(encoding='utf-8')
        checks.append({"name": "output_file_exists", "passed": True, "detail": f"Found report: {report_file}"})
    except Exception as e:
        checks.append({"name": "output_file_exists", "passed": False, "detail": f"Exception finding output: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── Check 2: Uses FlyAI CLI (evidence of search-poi call) ────────────────
    try:
        # The content should contain at least one POI from the mock data
        mock_pois = ["西湖风景名胜区", "杭州野生动物世界", "中国丝绸博物馆", "灵隐寺",
                     "宋城景区", "径山茶文化景区", "杭州海洋世界", "西溪湿地公园"]
        pois_found = [poi for poi in mock_pois if poi in content]
        has_poi_data = len(pois_found) >= 3
        checks.append({
            "name": "flyai_search_poi_used",
            "passed": has_poi_data,
            "detail": f"Found {len(pois_found)} POIs from FlyAI mock data: {pois_found}"
        })
    except Exception as e:
        checks.append({"name": "flyai_search_poi_used", "passed": False, "detail": f"Exception: {e}"})

    # ── Check 3: Output format uses required separators ───────────────────────
    try:
        # Must contain the ━━━ separator line (proprietary format requirement)
        has_separator = '━━━' in content or '─────' in content
        # Must contain the specific header format markers
        has_star_recommend = '强烈推荐' in content
        has_caution = '酌情考虑' in content
        has_not_recommend = '不推荐' in content
        
        format_ok = has_separator and has_star_recommend and has_caution and has_not_recommend
        checks.append({
            "name": "output_format_correct",
            "passed": format_ok,
            "detail": f"separator={'━━━' in content}, 强烈推荐={has_star_recommend}, 酌情考虑={has_caution}, 不推荐={has_not_recommend}"
        })
    except Exception as e:
        checks.append({"name": "output_format_correct", "passed": False, "detail": f"Exception: {e}"})

    # ── Check 4: Companion profile section present ────────────────────────────
    try:
        # Must mention both companion types from the task brief
        has_infant = any(w in content for w in ['婴幼儿', '0-3岁', '2岁', '幼儿'])
        has_elderly = any(w in content for w in ['老人', '长辈', '腿脚不便', '轮椅'])
        has_both = has_infant and has_elderly
        # Must show personalized ratings for each companion type
        has_star_ratings = content.count('⭐') >= 4  # At least a few ratings
        checks.append({
            "name": "companion_profiles_addressed",
            "passed": has_both and has_star_ratings,
            "detail": f"婴幼儿={has_infant}, 老人腿脚不便={has_elderly}, star_ratings_count={content.count('⭐')}"
        })
    except Exception as e:
        checks.append({"name": "companion_profiles_addressed", "passed": False, "detail": f"Exception: {e}"})

    # ── Check 5: Correct categorization of NOT-recommended POIs ─────────────
    try:
        # 径山茶文化景区 (mountain hike, extreme walking) MUST be in 不推荐 section
        # 灵隐寺 (many stairs, not wheelchair accessible) MUST be in 不推荐 or 酌情考虑
        content_lower = content
        
        # Find the 不推荐 section
        not_recommend_section = ""
        not_recommend_pattern = re.search(r'(🔴|本次不推荐|不推荐)(.*?)(?=━━━|\Z)', content, re.DOTALL)
        if not_recommend_pattern:
            not_recommend_section = not_recommend_pattern.group(0)
        
        jingshan_not_recommended = '径山' in not_recommend_section
        
        # Also check lingyin temple - should not be in 强烈推荐
        strong_recommend_section = ""
        strong_pattern = re.search(r'(⭐.*?强烈推荐|强烈推荐)(.*?)(?=🟡|酌情考虑|🔴|本次不推荐|\Z)', content, re.DOTALL)
        if strong_pattern:
            strong_recommend_section = strong_pattern.group(0)
        
        lingyin_not_strongly_recommended = '灵隐寺' not in strong_recommend_section
        
        # Indoor venues (海洋世界, 丝绸博物馆) should be in 强烈推荐
        indoor_recommended = any(v in strong_recommend_section for v in ['海洋世界', '丝绸博物馆', '野生动物'])
        
        companion_filter_correct = jingshan_not_recommended and lingyin_not_strongly_recommended and indoor_recommended
        checks.append({
            "name": "companion_filter_logic_correct",
            "passed": companion_filter_correct,
            "detail": f"径山茶文化景区 in 不推荐={jingshan_not_recommended}, 灵隐寺 not in 强烈推荐={lingyin_not_strongly_recommended}, indoor POI in 强烈推荐={indoor_recommended}"
        })
    except Exception as e:
        checks.append({"name": "companion_filter_logic_correct", "passed": False, "detail": f"Exception: {e}"})

    # ── Check 6: Day-by-Day itinerary present ─────────────────────────────────
    try:
        has_day_schedule = bool(re.search(r'Day\s*[123]|第[一二三]天', content))
        # Must span 3 days (matching the task brief - 3 days)
        day_count_matches = re.findall(r'Day\s*(\d)', content) + re.findall(r'第([一二三])天', content)
        has_3_days = len(set(day_count_matches)) >= 2  # At least 2 days mentioned
        checks.append({
            "name": "day_itinerary_present",
            "passed": has_day_schedule and has_3_days,
            "detail": f"has_day_schedule={has_day_schedule}, day_entries={set(day_count_matches)}"
        })
    except Exception as e:
        checks.append({"name": "day_itinerary_present", "passed": False, "detail": f"Exception: {e}"})

    # ── Check 7: Accessibility / no-barrier priority for elderly ─────────────
    try:
        # Report must explicitly address wheelchair/accessibility needs
        accessibility_keywords = ['无障碍', '轮椅', '电瓶车', '不用走太多', '低体力', '平地']
        accessibility_mentioned = sum(1 for kw in accessibility_keywords if kw in content)
        checks.append({
            "name": "accessibility_addressed",
            "passed": accessibility_mentioned >= 2,
            "detail": f"Found {accessibility_mentioned} accessibility keywords: {[kw for kw in accessibility_keywords if kw in content]}"
        })
    except Exception as e:
        checks.append({"name": "accessibility_addressed", "passed": False, "detail": f"Exception: {e}"})

    # ── Check 8: Destination and trip context in header ───────────────────────
    try:
        # Report header must reference Hangzhou and 3 days
        has_hangzhou = '杭州' in content[:500]
        has_duration = any(d in content[:500] for d in ['3天', '三天', '3 天'])
        header_ok = has_hangzhou and has_duration
        checks.append({
            "name": "report_header_context",
            "passed": header_ok,
            "detail": f"杭州 in header={has_hangzhou}, 3天 in header={has_duration}"
        })
    except Exception as e:
        checks.append({"name": "report_header_context", "passed": False, "detail": f"Exception: {e}"})

    # ── Compute final score ───────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    score = len(passed_checks) / len(checks)
    
    # Task passes if critical checks pass AND overall score >= 0.7
    critical_checks = ["output_file_exists", "flyai_search_poi_used", "companion_filter_logic_correct", "output_format_correct"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)
    
    overall_passed = critical_passed and score >= 0.7
    
    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))