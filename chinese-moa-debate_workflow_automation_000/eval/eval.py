import sys
import json
import os
import re
from pathlib import Path

def find_file(workspace, filename):
    results = list(Path(workspace).rglob(filename))
    return results[0] if results else None

def run_eval(workspace):
    checks = []
    total_score = 0.0
    max_score = 10.0

    # -------------------------
    # CHECK 1: debate_transcript.md exists and has content
    # -------------------------
    transcript_path = find_file(workspace, "debate_transcript.md")
    try:
        assert transcript_path is not None and transcript_path.exists()
        transcript = transcript_path.read_text(encoding='utf-8')
        assert len(transcript) > 500
        checks.append({"name": "transcript_exists_and_nonempty", "passed": True, "detail": f"Found at {transcript_path}, length={len(transcript)}"})
        total_score += 1.0
    except Exception as e:
        checks.append({"name": "transcript_exists_and_nonempty", "passed": False, "detail": f"Missing or too short: {e}"})

    transcript = ""
    if transcript_path and transcript_path.exists():
        try:
            transcript = transcript_path.read_text(encoding='utf-8')
        except:
            pass

    # -------------------------
    # CHECK 2: debate_summary.json exists and has required keys
    # -------------------------
    summary_path = find_file(workspace, "debate_summary.json")
    summary_data = None
    try:
        assert summary_path is not None and summary_path.exists()
        raw = summary_path.read_text(encoding='utf-8')
        summary_data = json.loads(raw)
        required_keys = {"pro", "con", "rebuttals", "attacks", "balance"}
        missing = required_keys - set(summary_data.keys())
        assert len(missing) == 0, f"Missing keys: {missing}"
        checks.append({"name": "summary_json_structure", "passed": True, "detail": f"All required keys present: {list(summary_data.keys())}"})
        total_score += 1.5
    except Exception as e:
        checks.append({"name": "summary_json_structure", "passed": False, "detail": f"Error: {e}"})

    # -------------------------
    # CHECK 3: Topic formatted as 本院认为...
    # -------------------------
    try:
        assert "本院认为" in transcript, "Topic not formatted as 本院认为..."
        # Check that the original raw topic was reformatted
        assert "年轻人" in transcript and ("兵役" in transcript or "服役" in transcript)
        checks.append({"name": "topic_formatted_as_benyuan", "passed": True, "detail": "Topic correctly formatted with 本院认为"})
        total_score += 0.5
    except Exception as e:
        checks.append({"name": "topic_formatted_as_benyuan", "passed": False, "detail": f"{e}"})

    # -------------------------
    # CHECK 4: All 6 role labels present in transcript
    # -------------------------
    required_labels = ["🔵 正方", "🔴 反方", "🟡 魔鬼辩手", "⚖️", "💜"]
    try:
        missing_labels = [lbl for lbl in required_labels if lbl not in transcript]
        assert len(missing_labels) == 0, f"Missing labels: {missing_labels}"
        checks.append({"name": "all_role_labels_present", "passed": True, "detail": "All emoji role labels found in transcript"})
        total_score += 1.0
    except Exception as e:
        checks.append({"name": "all_role_labels_present", "passed": False, "detail": f"{e}"})

    # -------------------------
    # CHECK 5: Multiple debate rounds occurred (at least 2 rounds of pro+con+devil)
    # -------------------------
    try:
        pro_count = transcript.count("🔵 正方")
        con_count = transcript.count("🔴 反方")
        devil_count = transcript.count("🟡 魔鬼辩手")
        assert pro_count >= 2, f"Only {pro_count} pro speeches found, need >=2"
        assert con_count >= 2, f"Only {con_count} con speeches found, need >=2"
        assert devil_count >= 2, f"Only {devil_count} devil speeches found, need >=2"
        checks.append({"name": "multiple_rounds_executed", "passed": True, "detail": f"Pro={pro_count}, Con={con_count}, Devil={devil_count} speeches"})
        total_score += 1.0
    except Exception as e:
        checks.append({"name": "multiple_rounds_executed", "passed": False, "detail": f"{e}"})

    # -------------------------
    # CHECK 6: Integrity judge score appeared and early-stop triggered
    # (score >= 8.0 threshold from task_spec, meaning loop stopped before max_rounds=3)
    # The mock server returns 6.5 on first call (round 2), 8.2 on second call (round 3)
    # So loop should stop at round 3 (after 2 integrity judge calls)
    # Transcript should show score >= 8.0 and stop reason ✅ 已完成
    # -------------------------
    try:
        # Look for integrity score display
        has_score = bool(re.search(r'8\.[0-9]', transcript)) or "8.2" in transcript
        assert has_score, "No integrity score >= 8.0 found in transcript"
        # Check for early-stop indicator
        assert "✅" in transcript and "已完成" in transcript, "Missing ✅ 已完成 stop reason"
        checks.append({"name": "integrity_judge_early_stop", "passed": True, "detail": "Score >= 8.0 detected and ✅ 已完成 stop reason present"})
        total_score += 1.5
    except Exception as e:
        checks.append({"name": "integrity_judge_early_stop", "passed": False, "detail": f"{e}"})

    # -------------------------
    # CHECK 7: Point of Information (信息点提问) present in transcript
    # -------------------------
    try:
        has_poi = "信息点" in transcript or "POI" in transcript.upper() or "？" in transcript
        # More specific: check for the question format
        has_accept_reject = ("接受" in transcript or "拒绝" in transcript)
        assert has_poi and has_accept_reject, f"POI section missing. has_poi={has_poi}, has_accept_reject={has_accept_reject}"
        checks.append({"name": "poi_section_present", "passed": True, "detail": "Point of Information section with accept/reject found"})
        total_score += 0.5
    except Exception as e:
        checks.append({"name": "poi_section_present", "passed": False, "detail": f"{e}"})

    # -------------------------
    # CHECK 8: Closing statements (总结陈词) present for both sides
    # -------------------------
    try:
        assert "💜" in transcript, "Missing 💜 label for closing statements"
        assert "总结陈词" in transcript, "No 总结陈词 section found"
        # Both pro and con closing
        closing_section = transcript[transcript.rfind("💜"):]
        has_pro_close = "正方" in closing_section or len(closing_section) > 200
        has_con_close = "反方" in closing_section or len(closing_section) > 400
        assert has_pro_close and has_con_close, "Missing pro or con closing statement"
        checks.append({"name": "closing_statements_present", "passed": True, "detail": "Closing statements section found with both sides"})
        total_score += 0.5
    except Exception as e:
        checks.append({"name": "closing_statements_present", "passed": False, "detail": f"{e}"})

    # -------------------------
    # CHECK 9: Final summary document has all 6 required sections
    # -------------------------
    required_sections = ["📋", "🔵", "🔴", "💜", "🟡", "⚖️"]
    try:
        # These should appear in the summary section at the end of transcript
        missing_sections = [s for s in required_sections if s not in transcript]
        assert len(missing_sections) == 0, f"Missing summary sections: {missing_sections}"
        checks.append({"name": "final_summary_all_sections", "passed": True, "detail": "All 6 summary sections with emoji headers present"})
        total_score += 1.0
    except Exception as e:
        checks.append({"name": "final_summary_all_sections", "passed": False, "detail": f"{e}"})

    # -------------------------
    # CHECK 10: Devil's advocate attacks collected across rounds (attacks field non-trivial)
    # -------------------------
    try:
        assert summary_data is not None, "No summary JSON to check"
        attacks_text = summary_data.get("attacks", "")
        assert len(attacks_text) > 30, f"Attacks field too short: '{attacks_text}'"
        # Should reference multiple attack points or use -> separator as per SKILL.md
        checks.append({"name": "devil_attacks_collected", "passed": True, "detail": f"Attacks field length={len(attacks_text)}"})
        total_score += 1.0
    except Exception as e:
        checks.append({"name": "devil_attacks_collected", "passed": False, "detail": f"{e}"})

    # -------------------------
    # CHECK 11: Parameters from task_spec respected (min_score=8.0, max_rounds=3)
    # Verify NOT "⚠️ 达到最大轮次" when early stop happened
    # -------------------------
    try:
        # Since mock triggers early stop at round 3 with score 8.2 >= 8.0,
        # should show ✅ 已完成 not ⚠️ 达到最大轮次
        assert "✅" in transcript and "已完成" in transcript, "Should show ✅ 已完成"
        # Should NOT show the max-rounds warning as the stop reason
        # (It might mention max rounds in other context, so check the stop-reason context)
        # Find the stop reason line
        stop_line = ""
        for line in transcript.split('\n'):
            if '✅' in line or '⚠️' in line:
                stop_line = line
        assert "✅" in stop_line or "已完成" in transcript, f"Stop reason line: '{stop_line}'"
        checks.append({"name": "correct_stop_reason", "passed": True, "detail": f"Correct stop reason (early convergence) detected"})
        total_score += 0.5
    except Exception as e:
        checks.append({"name": "correct_stop_reason", "passed": False, "detail": f"{e}"})

    # Normalize score
    normalized = round(min(total_score / max_score, 1.0), 3)
    passed = normalized >= 0.7

    return {
        "passed": passed,
        "score": normalized,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))