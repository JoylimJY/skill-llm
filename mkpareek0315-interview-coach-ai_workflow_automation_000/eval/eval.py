import json
import sys
import os
from pathlib import Path

def load_json_safe(path):
    try:
        with open(path, 'r') as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, f"File not found: {path}"
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON in {path}: {e}"
    except Exception as e:
        return None, f"Unexpected error reading {path}: {e}"

def run_eval(workspace_dir):
    checks = []
    base = Path.home() / ".openclaw" / "interview-coach"

    # ── CHECK 1: Directory exists ──────────────────────────────────────────
    dir_exists = base.is_dir()
    checks.append({
        "name": "data_directory_exists",
        "passed": dir_exists,
        "detail": str(base) + (" exists" if dir_exists else " NOT FOUND")
    })

    # ── CHECK 2: profile.json structure and values ────────────────────────
    profile, err = load_json_safe(base / "profile.json")
    if err:
        checks.append({"name": "profile_json_valid", "passed": False, "detail": err})
        profile = None
    else:
        checks.append({"name": "profile_json_valid", "passed": True, "detail": "profile.json parsed successfully"})

    if profile is not None:
        # Check candidate identity fields
        name_ok = str(profile.get("name", "")).strip().lower() in ["jordan rivera", "jordan"]
        checks.append({
            "name": "profile_name",
            "passed": name_ok,
            "detail": f"name='{profile.get('name')}' expected 'Jordan Rivera' or similar"
        })

        role_ok = "data engineer" in str(profile.get("target_role", "")).lower()
        checks.append({
            "name": "profile_target_role",
            "passed": role_ok,
            "detail": f"target_role='{profile.get('target_role')}' expected 'Data Engineer'"
        })

        company_ok = "databricks" in str(profile.get("target_company", "")).lower()
        checks.append({
            "name": "profile_target_company",
            "passed": company_ok,
            "detail": f"target_company='{profile.get('target_company')}' expected 'Databricks'"
        })

        exp_ok = int(profile.get("experience_years", 0)) == 5
        checks.append({
            "name": "profile_experience_years",
            "passed": exp_ok,
            "detail": f"experience_years={profile.get('experience_years')} expected 5"
        })

        # interviews_practiced must be 2
        interviews_ok = int(profile.get("interviews_practiced", 0)) == 2
        checks.append({
            "name": "profile_interviews_practiced",
            "passed": interviews_ok,
            "detail": f"interviews_practiced={profile.get('interviews_practiced')} expected 2"
        })

        # questions_answered must be 26 (13+13)
        questions_ok = int(profile.get("questions_answered", 0)) == 26
        checks.append({
            "name": "profile_questions_answered",
            "passed": questions_ok,
            "detail": f"questions_answered={profile.get('questions_answered')} expected 26 (13+13)"
        })

        # average_score: (67+76)/2 = 71.5
        avg = float(profile.get("average_score", 0))
        avg_ok = abs(avg - 71.5) < 1.0
        checks.append({
            "name": "profile_average_score",
            "passed": avg_ok,
            "detail": f"average_score={avg} expected ~71.5 ((67+76)/2)"
        })

        # skills should include Python, SQL, Spark at minimum
        skills = [str(s).lower() for s in profile.get("skills", [])]
        skills_ok = any("python" in s for s in skills) and any("sql" in s for s in skills)
        checks.append({
            "name": "profile_skills_populated",
            "passed": skills_ok,
            "detail": f"skills={profile.get('skills')} must include Python and SQL"
        })

    # ── CHECK 3: history.json structure ──────────────────────────────────
    history, err = load_json_safe(base / "history.json")
    if err:
        checks.append({"name": "history_json_valid", "passed": False, "detail": err})
        history = None
    else:
        checks.append({"name": "history_json_valid", "passed": True, "detail": "history.json parsed successfully"})

    if history is not None:
        hist_len_ok = len(history) == 2
        checks.append({
            "name": "history_has_two_sessions",
            "passed": hist_len_ok,
            "detail": f"history has {len(history)} sessions, expected 2"
        })

        if len(history) >= 1:
            s1 = history[0]
            # Session 1: overall 67
            s1_overall = None
            for key in ["overall_score", "overall", "score", "total_score"]:
                if key in s1:
                    s1_overall = float(s1[key])
                    break
            s1_score_ok = s1_overall is not None and abs(s1_overall - 67) < 1.0
            checks.append({
                "name": "history_session1_overall_score",
                "passed": s1_score_ok,
                "detail": f"Session 1 overall_score={s1_overall} expected 67"
            })

            # Session 1 round scores
            rounds1 = s1.get("round_scores", s1.get("rounds", {}))
            if isinstance(rounds1, dict):
                beh1 = float(rounds1.get("behavioral", rounds1.get("Behavioral", -1)))
                tech1 = float(rounds1.get("technical", rounds1.get("Technical", -1)))
                hr1 = float(rounds1.get("hr", rounds1.get("HR", rounds1.get("hr_culture", -1))))
            else:
                beh1 = tech1 = hr1 = -1
            rounds1_ok = (abs(beh1 - 70) < 1.0 and abs(tech1 - 62) < 1.0 and abs(hr1 - 68) < 1.0)
            checks.append({
                "name": "history_session1_round_scores",
                "passed": rounds1_ok,
                "detail": f"Session 1 rounds: behavioral={beh1}(exp 70), technical={tech1}(exp 62), hr={hr1}(exp 68)"
            })

        if len(history) >= 2:
            s2 = history[1]
            s2_overall = None
            for key in ["overall_score", "overall", "score", "total_score"]:
                if key in s2:
                    s2_overall = float(s2[key])
                    break
            s2_score_ok = s2_overall is not None and abs(s2_overall - 76) < 1.0
            checks.append({
                "name": "history_session2_overall_score",
                "passed": s2_score_ok,
                "detail": f"Session 2 overall_score={s2_overall} expected 76"
            })

            rounds2 = s2.get("round_scores", s2.get("rounds", {}))
            if isinstance(rounds2, dict):
                beh2 = float(rounds2.get("behavioral", rounds2.get("Behavioral", -1)))
                tech2 = float(rounds2.get("technical", rounds2.get("Technical", -1)))
                hr2 = float(rounds2.get("hr", rounds2.get("HR", rounds2.get("hr_culture", -1))))
            else:
                beh2 = tech2 = hr2 = -1
            rounds2_ok = (abs(beh2 - 78) < 1.0 and abs(tech2 - 74) < 1.0 and abs(hr2 - 76) < 1.0)
            checks.append({
                "name": "history_session2_round_scores",
                "passed": rounds2_ok,
                "detail": f"Session 2 rounds: behavioral={beh2}(exp 78), technical={tech2}(exp 74), hr={hr2}(exp 76)"
            })

    # ── CHECK 4: weak_areas.json ──────────────────────────────────────────
    weak, err = load_json_safe(base / "weak_areas.json")
    if err:
        checks.append({"name": "weak_areas_json_valid", "passed": False, "detail": err})
        weak = None
    else:
        checks.append({"name": "weak_areas_json_valid", "passed": True, "detail": "weak_areas.json parsed successfully"})

    if weak is not None:
        # Must be non-empty and mention quantifying results / STAR result component
        weak_str = json.dumps(weak).lower()
        weak_content_ok = (
            len(weak) >= 1 and
            any(
                kw in weak_str
                for kw in ["result", "quantif", "numbers", "measur", "star result", "weak"]
            )
        )
        checks.append({
            "name": "weak_areas_populated_with_result",
            "passed": weak_content_ok,
            "detail": f"weak_areas has {len(weak)} items; content must reference Result/quantifying: '{weak_str[:200]}'"
        })

    # ── CHECK 5: saved_answers.json ───────────────────────────────────────
    saved, err = load_json_safe(base / "saved_answers.json")
    if err:
        checks.append({"name": "saved_answers_json_valid", "passed": False, "detail": err})
        saved = None
    else:
        checks.append({"name": "saved_answers_json_valid", "passed": True, "detail": "saved_answers.json parsed successfully"})

    if saved is not None:
        saved_list = saved if isinstance(saved, list) else [saved]
        has_saved = len(saved_list) >= 1
        checks.append({
            "name": "saved_answers_not_empty",
            "passed": has_saved,
            "detail": f"saved_answers has {len(saved_list)} entries, expected >= 1"
        })

        if has_saved:
            entry = saved_list[0] if isinstance(saved_list[0], dict) else {}
            entry_str = json.dumps(entry).lower()

            # Must have score 9/10
            score_val = None
            for k in ["score", "rating", "answer_score"]:
                if k in entry:
                    try:
                        score_val = float(entry[k])
                    except:
                        pass
                    break
            score_ok = score_val is not None and abs(score_val - 9) < 0.5
            checks.append({
                "name": "saved_answer_score_9",
                "passed": score_ok,
                "detail": f"Saved answer score={score_val} expected 9 (or 9/10)"
            })

            # Category must reference "tell me about yourself" or "intro"
            cat_ok = any(
                kw in entry_str
                for kw in ["tell me about yourself", "intro", "about yourself", "self introduction"]
            )
            checks.append({
                "name": "saved_answer_category_tmay",
                "passed": cat_ok,
                "detail": f"Saved answer category must reference 'Tell me about yourself'; got: {entry_str[:200]}"
            })

            # Answer text must mention Databricks or Spark or PayPal or the 65% stat
            answer_text = str(entry.get("answer", entry.get("text", entry.get("content", "")))).lower()
            answer_content_ok = any(
                kw in answer_text
                for kw in ["databricks", "spark", "paypal", "65%", "pipeline", "lakehouse"]
            )
            checks.append({
                "name": "saved_answer_content_matches_briefing",
                "passed": answer_content_ok,
                "detail": f"Saved answer text must contain key facts (Databricks/Spark/PayPal/65%); got: '{answer_text[:200]}'"
            })

    # ── FINAL SCORING ─────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    overall_passed = score >= 0.80

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace_dir)