import json
import sys
import re
from pathlib import Path

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def run_eval(workspace: str):
    checks = []
    total_score = 0.0
    max_checks = 10

    # ── Locate diagnosis-report.json ────────────────────────────────────────
    report_path = None
    skill_output = Path.home() / ".openclaw/skills/agent-mbti/output/diagnosis-report.json"
    ws_candidates = list(Path(workspace).rglob("diagnosis-report.json"))
    
    if skill_output.exists():
        report_path = skill_output
    elif ws_candidates:
        report_path = ws_candidates[0]

    # CHECK 1: diagnosis-report.json exists
    if report_path and report_path.exists():
        checks.append({"name": "diagnosis_report_exists", "passed": True,
                        "detail": f"Found at {report_path}"})
        total_score += 1
    else:
        checks.append({"name": "diagnosis_report_exists", "passed": False,
                        "detail": "diagnosis-report.json not found in output or workspace"})
        # Cannot proceed
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks + [
                {"name": c, "passed": False, "detail": "Skipped: report file missing"}
                for c in [
                    "selfReportedType_INTJ", "measuredType_ENTJ",
                    "ability_scores_present", "ability_scores_correct",
                    "agentProfile_dominantType_ENTJ", "agentProfile_secondaryType_INTJ",
                    "desiredType_ENFJ", "gap_count_correct", "alignment_score_correct"
                ]
            ]
        }

    try:
        report = load_json(report_path)
    except Exception as e:
        checks.append({"name": "report_parseable", "passed": False,
                        "detail": f"JSON parse error: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    # CHECK 2: selfReportedType = INTJ
    srt = report.get("selfReportedType", "")
    passed = str(srt).upper() == "INTJ"
    checks.append({"name": "selfReportedType_INTJ", "passed": passed,
                    "detail": f"Got '{srt}', expected 'INTJ'"})
    if passed: total_score += 1

    # CHECK 3: measuredType = ENTJ
    mt = report.get("measuredType", "")
    passed = str(mt).upper() == "ENTJ"
    checks.append({"name": "measuredType_ENTJ", "passed": passed,
                    "detail": f"Got '{mt}', expected 'ENTJ'"})
    if passed: total_score += 1

    # CHECK 4: ability_scores present with all 6 dimensions
    scores = report.get("ability_scores", {})
    required_dims = {"Memory", "Planning", "WorldModel", "Retrospection", "Grounding", "SpatialNav"}
    has_all = isinstance(scores, dict) and required_dims.issubset(set(scores.keys()))
    checks.append({"name": "ability_scores_present", "passed": has_all,
                    "detail": f"Keys found: {list(scores.keys()) if isinstance(scores, dict) else 'N/A'}"})
    if has_all: total_score += 1

    # CHECK 5: ability_scores values correct
    # Memory avg: (8+7)/2 = 7.5, Planning avg: (5+8)/2 = 6.5, WorldModel: 7,
    # Retrospection: 9, Grounding: 6, SpatialNav: 4
    expected_scores = {
        "Memory": 7.5, "Planning": 6.5, "WorldModel": 7.0,
        "Retrospection": 9.0, "Grounding": 6.0, "SpatialNav": 4.0
    }
    scores_correct = True
    score_detail = []
    if isinstance(scores, dict):
        for dim, exp_val in expected_scores.items():
            got = scores.get(dim)
            try:
                close = abs(float(got) - exp_val) < 0.01
            except (TypeError, ValueError):
                close = False
            if not close:
                scores_correct = False
                score_detail.append(f"{dim}: got={got}, expected={exp_val}")
    else:
        scores_correct = False
    checks.append({"name": "ability_scores_correct", "passed": scores_correct,
                    "detail": "; ".join(score_detail) if score_detail else "All scores correct"})
    if scores_correct: total_score += 1

    # CHECK 6: agentProfile.dominantType = ENTJ (measured takes precedence)
    agent_profile = report.get("agentProfile", {})
    dominant = agent_profile.get("dominantType", "") if isinstance(agent_profile, dict) else ""
    passed = str(dominant).upper() == "ENTJ"
    checks.append({"name": "agentProfile_dominantType_ENTJ", "passed": passed,
                    "detail": f"Got '{dominant}', expected 'ENTJ' (measuredType takes precedence)"})
    if passed: total_score += 1

    # CHECK 7: agentProfile.secondaryType = INTJ
    secondary = agent_profile.get("secondaryType", "") if isinstance(agent_profile, dict) else ""
    passed = str(secondary).upper() == "INTJ"
    checks.append({"name": "agentProfile_secondaryType_INTJ", "passed": passed,
                    "detail": f"Got '{secondary}', expected 'INTJ' (selfReportedType)"})
    if passed: total_score += 1

    # CHECK 8: desiredType = ENFJ
    dt = report.get("desiredType", "")
    passed = str(dt).upper() == "ENFJ"
    checks.append({"name": "desiredType_ENFJ", "passed": passed,
                    "detail": f"Got '{dt}', expected 'ENFJ'"})
    if passed: total_score += 1

    # CHECK 9: gaps.gap_count = 1 (only TF differs: ENTJ has T, ENFJ has F)
    gaps = report.get("gaps", {})
    gap_count = gaps.get("gap_count", None) if isinstance(gaps, dict) else None
    passed = gap_count == 1
    checks.append({"name": "gap_count_correct", "passed": passed,
                    "detail": f"Got gap_count={gap_count}, expected 1 (only TF differs: ENTJ=T vs ENFJ=F)"})
    if passed: total_score += 1

    # CHECK 10: gaps.alignment_score = 75.0 (3 out of 4 dimensions match)
    alignment = gaps.get("alignment_score", None) if isinstance(gaps, dict) else None
    try:
        align_correct = abs(float(alignment) - 75.0) < 0.1
    except (TypeError, ValueError):
        align_correct = False
    checks.append({"name": "alignment_score_correct", "passed": align_correct,
                    "detail": f"Got alignment_score={alignment}, expected 75.0"})
    if align_correct: total_score += 1

    # ── Locate SOUL.md ───────────────────────────────────────────────────────
    soul_path = None
    skill_soul = Path.home() / ".openclaw/skills/agent-mbti/output/SOUL.md"
    ws_soul = list(Path(workspace).rglob("SOUL.md"))

    if skill_soul.exists():
        soul_path = skill_soul
    elif ws_soul:
        # Prefer the one that was modified (not just the original)
        for p in ws_soul:
            content = p.read_text()
            if "T_to_F" in content or "empathetic" in content.lower() or "Incorporate empathetic" in content:
                soul_path = p
                break
        if not soul_path and ws_soul:
            soul_path = ws_soul[0]

    # CHECK 11: SOUL.md exists and contains T_to_F directive
    if soul_path and soul_path.exists():
        try:
            soul_content = soul_path.read_text()
            # Must contain the exact directive text from config-generator-v3.json
            expected_directive = "Incorporate empathetic framing. Acknowledge user emotions before providing analysis."
            has_directive = expected_directive in soul_content
            # Must be under ## Decision Making section
            has_section = "## Decision Making" in soul_content

            soul_passed = has_directive and has_section
            checks.append({
                "name": "soul_md_patch_correct",
                "passed": soul_passed,
                "detail": (
                    f"has_directive={has_directive}, has_section={has_section}. "
                    f"Expected T_to_F directive under '## Decision Making' section."
                )
            })
            if soul_passed: total_score += 1
        except Exception as e:
            checks.append({"name": "soul_md_patch_correct", "passed": False,
                            "detail": f"Error reading SOUL.md: {e}"})
    else:
        checks.append({"name": "soul_md_patch_correct", "passed": False,
                        "detail": "SOUL.md not found or not patched"})

    final_score = total_score / (max_checks + 1)  # 11 checks total
    passed_all = all(c["passed"] for c in checks)

    # Minimum passing: at least 8 of 11 checks
    passed_overall = sum(1 for c in checks if c["passed"]) >= 8

    return {
        "passed": passed_overall,
        "score": round(final_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))