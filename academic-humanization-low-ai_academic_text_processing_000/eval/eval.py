import sys
import os
import json
import re

def evaluate(workspace_dir):
    checks = []
    total_score = 0.0
    max_score = 0.0

    # ─── Locate the output file ───────────────────────────────────────────────
    # Agent should produce a rewritten version. We search for it.
    from pathlib import Path

    # The agent is expected to write to a file in the workspace.
    # We accept any .txt file that is NOT the original input and NOT a distractor.
    original_path = Path(workspace_dir) / "thesis_project" / "chapter4_ai_section_raw.txt"

    # Read original for reference
    try:
        with open(original_path, "r", encoding="utf-8") as f:
            original_text = f.read().strip()
        original_char_count = len(original_text)
    except Exception as e:
        checks.append({"name": "original_file_readable", "passed": False,
                        "detail": f"Cannot read original input: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    # Find output file - look for any new .txt file not in the distractor list
    known_distractors = {
        "literature_review.txt", "methodology.txt", "bibliography.bib",
        "abstract_v1.txt", "abstract_v2.txt", "fig1_description.txt",
        "meeting_notes_20240315.txt", "revision_checklist.txt",
        "cover_letter_template.txt", "submission_checklist.txt",
        "submission_notes.txt", "chapter4_ai_section_raw.txt"
    }

    output_file = None
    output_text = None

    # Search all txt files in workspace
    for candidate in Path(workspace_dir).rglob("*.txt"):
        if candidate.name not in known_distractors and candidate.name != "chapter4_ai_section_raw.txt":
            try:
                content = candidate.read_text(encoding="utf-8").strip()
                if len(content) > 100:  # Must be substantial
                    output_file = candidate
                    output_text = content
                    break
            except Exception:
                continue

    if output_text is None:
        # Also check if the agent overwrote the original or saved in-place with different name
        # Check for any modification
        checks.append({
            "name": "output_file_found",
            "passed": False,
            "detail": "No output file with substantial Chinese text found. Agent must create a new file with the rewritten text."
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({
        "name": "output_file_found",
        "passed": True,
        "detail": f"Found output at: {output_file}"
    })
    total_score += 0.5
    max_score += 0.5

    # ─── CHECK 1: No meta-commentary (仅输出重写后的文本) ────────────────────
    max_score += 1.0
    meta_patterns = [
        r"以下是.*重写",
        r"修改后.*文本",
        r"我对.*进行了",
        r"重写版本",
        r"以下为",
        r"修改说明",
        r"原文.*改为",
    ]
    has_meta = any(re.search(p, output_text) for p in meta_patterns)
    check1_passed = not has_meta
    checks.append({
        "name": "no_meta_commentary",
        "passed": check1_passed,
        "detail": "Output must contain ONLY the rewritten text, no explanatory preamble or meta-commentary." if not check1_passed else "No meta-commentary found."
    })
    if check1_passed:
        total_score += 1.0

    # ─── CHECK 2: Banned summary phrases DELETED ────────────────────────────
    max_score += 2.0
    banned_phrases = ["综上所述", "总而言之", "本文认为"]
    found_banned = [p for p in banned_phrases if p in output_text]
    check2_passed = len(found_banned) == 0
    checks.append({
        "name": "banned_summary_phrases_removed",
        "passed": check2_passed,
        "detail": f"Found banned phrases that must be deleted/restructured: {found_banned}" if not check2_passed else "All banned summary phrases correctly removed."
    })
    if check2_passed:
        total_score += 2.0

    # ─── CHECK 3: AI connector words replaced ──────────────────────────────
    max_score += 1.5
    # 因此 should be replaced or significantly reduced
    # 此外 should be replaced
    yinci_count_orig = original_text.count("因此")
    yinci_count_out = output_text.count("因此")
    ciwai_count_orig = original_text.count("此外")
    ciwai_count_out = output_text.count("此外")

    # At least one of these should show reduction
    connector_reduced = (yinci_count_out < yinci_count_orig) or (ciwai_count_out < ciwai_count_orig)
    checks.append({
        "name": "ai_connector_words_replaced",
        "passed": connector_reduced,
        "detail": (
            f"'因此' count: {yinci_count_orig}→{yinci_count_out}, "
            f"'此外' count: {ciwai_count_orig}→{ciwai_count_out}. "
            "At least one should decrease."
        ) if not connector_reduced else (
            f"Connectors reduced: '因此' {yinci_count_orig}→{yinci_count_out}, '此外' {ciwai_count_orig}→{ciwai_count_out}."
        )
    })
    if connector_reduced:
        total_score += 1.5

    # ─── CHECK 4: 首先/其次/最后 sequential structure broken ─────────────────
    max_score += 1.5
    sequential_markers = ["首先", "其次", "最后"]
    markers_in_output = [m for m in sequential_markers if m in output_text]
    # All three appearing together in sequence is an AI pattern - at minimum the triple combination should be broken
    all_three_present = all(m in output_text for m in sequential_markers)
    check4_passed = not all_three_present
    checks.append({
        "name": "sequential_markers_restructured",
        "passed": check4_passed,
        "detail": "The '首先/其次/最后' triplet still appears intact — this is a strong AI-detection signal that must be restructured." if not check4_passed else f"Sequential triple broken. Remaining markers: {markers_in_output}"
    })
    if check4_passed:
        total_score += 1.5

    # ─── CHECK 5: Word count within ±15% of original ───────────────────────
    max_score += 1.5
    lower_bound = original_char_count * 0.85
    upper_bound = original_char_count * 1.15
    output_char_count = len(output_text)
    check5_passed = lower_bound <= output_char_count <= upper_bound
    checks.append({
        "name": "word_count_within_15_percent",
        "passed": check5_passed,
        "detail": (
            f"Original: {original_char_count} chars. Output: {output_char_count} chars. "
            f"Allowed range: [{int(lower_bound)}, {int(upper_bound)}]. "
            f"{'Within range.' if check5_passed else 'OUT OF RANGE.'}"
        )
    })
    if check5_passed:
        total_score += 1.5

    # ─── CHECK 6: Sentence length variation present ─────────────────────────
    max_score += 1.5
    # Split by Chinese sentence delimiters
    sentences = re.split(r'[。！？；]', output_text)
    sentences = [s.strip() for s in sentences if len(s.strip()) >= 3]

    if len(sentences) >= 3:
        lengths = [len(s) for s in sentences]
        has_short = any(l <= 12 for l in lengths)   # short sentence (≤12 chars)
        has_long = any(l >= 40 for l in lengths)    # long sentence (≥40 chars)
        check6_passed = has_short and has_long
        checks.append({
            "name": "sentence_length_variation",
            "passed": check6_passed,
            "detail": (
                f"Sentence lengths: {sorted(lengths)}. "
                f"Short (≤12): {has_short}, Long (≥40): {has_long}. "
                "Both needed for rhythm variation."
            )
        })
        if check6_passed:
            total_score += 1.5
    else:
        checks.append({
            "name": "sentence_length_variation",
            "passed": False,
            "detail": "Not enough sentences detected to evaluate length variation."
        })

    # ─── CHECK 7: Human cognitive traces / hedging present ──────────────────
    max_score += 1.0
    human_traces = [
        "值得注意的是", "需要说明的是", "需要补充说明的是",
        "在一定程度上", "在特定条件下", "一方面", "另一方面",
        "这一点", "这种情况", "从以上分析可以看出",
        "——", "（", "）"
    ]
    found_traces = [t for t in human_traces if t in output_text]
    check7_passed = len(found_traces) >= 2
    checks.append({
        "name": "human_cognitive_traces_present",
        "passed": check7_passed,
        "detail": f"Found human traces/hedges: {found_traces}. Need at least 2." if not check7_passed else f"Human traces found: {found_traces}"
    })
    if check7_passed:
        total_score += 1.0

    # ─── CHECK 8: No concluding summary sentence at the end ─────────────────
    max_score += 1.0
    # Check last sentence for summary-style endings
    last_chunk = output_text[-120:] if len(output_text) > 120 else output_text
    summary_endings = ["综上", "总之", "本文认为", "综合以上", "总而言之", "总结"]
    has_summary_ending = any(p in last_chunk for p in summary_endings)
    check8_passed = not has_summary_ending
    checks.append({
        "name": "no_summary_conclusion_at_end",
        "passed": check8_passed,
        "detail": f"Summary pattern found in final section: {[p for p in summary_endings if p in last_chunk]}" if not check8_passed else "No template summary conclusion at end."
    })
    if check8_passed:
        total_score += 1.0

    # ─── Final scoring ───────────────────────────────────────────────────────
    final_score = round(total_score / max_score, 4) if max_score > 0 else 0.0
    passed = final_score >= 0.70 and checks[0]["passed"]  # Must find output + 70% score

    return {
        "passed": passed,
        "score": final_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))