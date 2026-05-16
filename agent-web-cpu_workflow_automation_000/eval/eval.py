import sys
import json
import re
from pathlib import Path
from datetime import datetime

def run_eval(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ─────────────────────────────────────────────
    # Helper: load apps.json
    # ─────────────────────────────────────────────
    skill_dir = workspace / "skills" / "agent-web-cpu"
    apps_json_path = skill_dir / "apps.json"

    def load_apps_json():
        return json.loads(apps_json_path.read_text(encoding="utf-8"))

    # ─────────────────────────────────────────────
    # CHECK 1: apps.json exists and has _schema v2
    # ─────────────────────────────────────────────
    try:
        data = load_apps_json()
        has_schema = data.get("_schema") == "v2"
        checks.append({
            "name": "apps_json_schema_v2",
            "passed": has_schema,
            "detail": f"_schema field = {data.get('_schema')!r}; expected 'v2'"
        })
        if has_schema:
            total_score += 0.10
    except Exception as e:
        checks.append({
            "name": "apps_json_schema_v2",
            "passed": False,
            "detail": f"Failed to read apps.json: {e}"
        })

    # ─────────────────────────────────────────────
    # CHECK 2: SEO关键词优化 has been removed (exact name match)
    # ─────────────────────────────────────────────
    try:
        data = load_apps_json()
        apps = data.get("apps", [])
        names = [a.get("name") for a in apps]
        seo_removed = "SEO关键词优化" not in names
        checks.append({
            "name": "seo_app_removed",
            "passed": seo_removed,
            "detail": f"Remaining app names: {names}. 'SEO关键词优化' should be absent."
        })
        if seo_removed:
            total_score += 0.15
    except Exception as e:
        checks.append({
            "name": "seo_app_removed",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ─────────────────────────────────────────────
    # CHECK 3: 博文框架 and 爆款润色助手 still present (not accidentally removed)
    # ─────────────────────────────────────────────
    try:
        data = load_apps_json()
        apps = data.get("apps", [])
        names = [a.get("name") for a in apps]
        both_present = ("博文框架" in names) and ("爆款润色助手" in names)
        checks.append({
            "name": "original_apps_preserved",
            "passed": both_present,
            "detail": f"Remaining app names: {names}. Both '博文框架' and '爆款润色助手' must be present."
        })
        if both_present:
            total_score += 0.10
    except Exception as e:
        checks.append({
            "name": "original_apps_preserved",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ─────────────────────────────────────────────
    # CHECK 4: New app f7e6d5c4b3a291807f6e5d4c3b2a1908 added
    # ─────────────────────────────────────────────
    NEW_APP_ID = "f7e6d5c4b3a291807f6e5d4c3b2a1908"
    new_app_entry = None
    try:
        data = load_apps_json()
        apps = data.get("apps", [])
        for a in apps:
            if a.get("id") == NEW_APP_ID:
                new_app_entry = a
                break
        new_app_added = new_app_entry is not None
        checks.append({
            "name": "new_app_added",
            "passed": new_app_added,
            "detail": f"App with id {NEW_APP_ID} {'found' if new_app_added else 'NOT found'} in apps.json"
        })
        if new_app_added:
            total_score += 0.15
    except Exception as e:
        checks.append({
            "name": "new_app_added",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ─────────────────────────────────────────────
    # CHECK 5: New app has correct name from mock server
    # ─────────────────────────────────────────────
    try:
        if new_app_entry:
            correct_name = new_app_entry.get("name") == "科技博客生成器"
            checks.append({
                "name": "new_app_correct_name",
                "passed": correct_name,
                "detail": f"New app name = {new_app_entry.get('name')!r}; expected '科技博客生成器'"
            })
            if correct_name:
                total_score += 0.10
        else:
            checks.append({
                "name": "new_app_correct_name",
                "passed": False,
                "detail": "New app entry not found, cannot check name"
            })
    except Exception as e:
        checks.append({
            "name": "new_app_correct_name",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ─────────────────────────────────────────────
    # CHECK 6: New app has 3-6 keywords
    # ─────────────────────────────────────────────
    try:
        if new_app_entry:
            keywords = new_app_entry.get("keywords", [])
            kw_count_ok = isinstance(keywords, list) and 3 <= len(keywords) <= 6
            checks.append({
                "name": "new_app_keyword_count",
                "passed": kw_count_ok,
                "detail": f"Keywords: {keywords} (count={len(keywords)}); must be 3-6"
            })
            if kw_count_ok:
                total_score += 0.10
        else:
            checks.append({
                "name": "new_app_keyword_count",
                "passed": False,
                "detail": "New app entry not found"
            })
    except Exception as e:
        checks.append({
            "name": "new_app_keyword_count",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ─────────────────────────────────────────────
    # CHECK 7: New app has valid ISO 8601 createdAt timestamp
    # ─────────────────────────────────────────────
    try:
        if new_app_entry:
            created_at = new_app_entry.get("createdAt", "")
            # ISO 8601 pattern: YYYY-MM-DDTHH:MM:SS with optional timezone
            iso_pattern = re.compile(
                r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?([+-]\d{2}:\d{2}|Z)?$'
            )
            is_iso = bool(iso_pattern.match(created_at))
            checks.append({
                "name": "new_app_iso8601_timestamp",
                "passed": is_iso,
                "detail": f"createdAt = {created_at!r}; must be valid ISO 8601"
            })
            if is_iso:
                total_score += 0.05
        else:
            checks.append({
                "name": "new_app_iso8601_timestamp",
                "passed": False,
                "detail": "New app entry not found"
            })
    except Exception as e:
        checks.append({
            "name": "new_app_iso8601_timestamp",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ─────────────────────────────────────────────
    # CHECK 8: match_result.json exists and correctly applies proprietary scoring
    # The query is: "帮我润色这篇博文，让它变成爆款内容"
    # Expected winner: 爆款润色助手 (keywords: 润色+5, 爆款+5 = score 10 >= threshold 5)
    # 博文框架: keyword "博文" doesn't appear in query as-is, but "博文" IS in query → +5; total ~5
    # 爆款润色助手: "润色" in query +5, "爆款" in query +5 → total 10 (clear winner)
    # ─────────────────────────────────────────────
    match_result_path = None
    try:
        candidates = list(workspace.rglob("match_result.json"))
        if not candidates:
            checks.append({
                "name": "match_result_file_exists",
                "passed": False,
                "detail": "match_result.json not found anywhere in workspace"
            })
        else:
            match_result_path = candidates[0]
            checks.append({
                "name": "match_result_file_exists",
                "passed": True,
                "detail": f"Found at {match_result_path}"
            })
            total_score += 0.05
    except Exception as e:
        checks.append({
            "name": "match_result_file_exists",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ─────────────────────────────────────────────
    # CHECK 9: match_result.json has correct winner (爆款润色助手)
    # ─────────────────────────────────────────────
    try:
        if match_result_path and match_result_path.exists():
            mr = json.loads(match_result_path.read_text(encoding="utf-8"))
            winner = mr.get("matched_app") or mr.get("winner") or mr.get("best_match") or mr.get("app")
            # Accept either the name or the id
            EXPECTED_WINNER_NAME = "爆款润色助手"
            EXPECTED_WINNER_ID = "cc2a9e1f4d3b8c7e6f5a0912345678ab"
            winner_correct = False
            winner_detail = f"winner field = {winner!r}"
            if isinstance(winner, str):
                winner_correct = (winner == EXPECTED_WINNER_NAME) or (winner == EXPECTED_WINNER_ID)
            elif isinstance(winner, dict):
                winner_correct = (winner.get("name") == EXPECTED_WINNER_NAME) or (winner.get("id") == EXPECTED_WINNER_ID)
            checks.append({
                "name": "match_result_correct_winner",
                "passed": winner_correct,
                "detail": f"{winner_detail}; expected '爆款润色助手' or its id"
            })
            if winner_correct:
                total_score += 0.10
        else:
            checks.append({
                "name": "match_result_correct_winner",
                "passed": False,
                "detail": "match_result.json not available"
            })
    except Exception as e:
        checks.append({
            "name": "match_result_correct_winner",
            "passed": False,
            "detail": f"Exception reading match_result.json: {e}"
        })

    # ─────────────────────────────────────────────
    # CHECK 10: match_result.json includes score >= 5 (threshold validation)
    # ─────────────────────────────────────────────
    try:
        if match_result_path and match_result_path.exists():
            mr = json.loads(match_result_path.read_text(encoding="utf-8"))
            score_val = mr.get("score") or mr.get("match_score") or mr.get("total_score")
            if score_val is None:
                # Try nested
                for key in ["matched_app", "winner", "best_match"]:
                    if isinstance(mr.get(key), dict):
                        score_val = mr[key].get("score") or mr[key].get("match_score")
                        break
            score_ok = isinstance(score_val, (int, float)) and float(score_val) >= 5
            checks.append({
                "name": "match_result_score_threshold",
                "passed": score_ok,
                "detail": f"score = {score_val}; must be numeric and >= 5 (proprietary threshold)"
            })
            if score_ok:
                total_score += 0.10
        else:
            checks.append({
                "name": "match_result_score_threshold",
                "passed": False,
                "detail": "match_result.json not available"
            })
    except Exception as e:
        checks.append({
            "name": "match_result_score_threshold",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ─────────────────────────────────────────────
    # Final verdict
    # ─────────────────────────────────────────────
    total_score = round(min(total_score, 1.0), 4)
    passed = total_score >= 0.70 and all(
        c["passed"] for c in checks if c["name"] in {
            "apps_json_schema_v2",
            "seo_app_removed",
            "original_apps_preserved",
            "new_app_added",
            "new_app_correct_name",
        }
    )

    result = {
        "passed": passed,
        "score": total_score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace_dir)