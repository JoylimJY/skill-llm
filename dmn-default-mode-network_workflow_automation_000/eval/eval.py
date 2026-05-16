import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    ws = Path(workspace_dir)
    checks = []
    total_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── Helper ──────────────────────────────────────────────────────────────
    def find_files(pattern):
        return list(ws.rglob(pattern))

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 1: A new CEO-function note was created for 2026-06-12
    #          Must be named: 20260612_CEO思维模拟_*.md (or equivalent)
    # ════════════════════════════════════════════════════════════════════════
    ceo_notes = [f for f in find_files("20260612_CEO思维模拟_*.md")
                 if "Synthesis" not in f.name]
    # Also accept English transliterations
    ceo_notes_en = [f for f in find_files("20260612_*CEO*.md")
                    if "Synthesis" not in f.name and f not in ceo_notes]
    all_ceo_notes = ceo_notes + ceo_notes_en

    if all_ceo_notes:
        note_file = all_ceo_notes[0]
        note_content = note_file.read_text(encoding="utf-8", errors="replace")
        total_score += add_check(
            "CEO思维模拟 note created with correct naming",
            True,
            f"Found: {note_file.name}"
        )
    else:
        note_content = ""
        total_score += add_check(
            "CEO思维模拟 note created with correct naming",
            False,
            "No file matching '20260612_CEO思维模拟_*.md' found in workspace"
        )

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 2: CEO note must NOT use Charlie Munger (lastCEO in state)
    # ════════════════════════════════════════════════════════════════════════
    if note_content:
        munger_used = bool(re.search(r"Charlie Munger|查理·芒格|Munger", note_content, re.IGNORECASE))
        total_score += add_check(
            "lastCEO (Charlie Munger) not repeated",
            not munger_used,
            "Charlie Munger NOT found in note (correct)" if not munger_used
            else "FAIL: Note uses Charlie Munger again, violating lastCEO rule"
        )
    else:
        total_score += add_check(
            "lastCEO (Charlie Munger) not repeated",
            False,
            "Cannot check: no CEO note found"
        )

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 3: CEO note must use a real thinker from the rotation table
    # ════════════════════════════════════════════════════════════════════════
    valid_ceos = [
        "Jeff Bezos", "贝佐斯",
        "Elon Musk", "马斯克",
        "Paul Graham",
        "Naval Ravikant", "Naval",
        "Andy Grove", "格鲁夫",
        "Richard Feynman", "费曼",
    ]
    if note_content:
        found_ceo = any(ceo.lower() in note_content.lower() for ceo in valid_ceos)
        matched = [ceo for ceo in valid_ceos if ceo.lower() in note_content.lower()]
        total_score += add_check(
            "A valid thinker from rotation table is used",
            found_ceo,
            f"Found thinker(s): {matched}" if found_ceo else "No valid thinker from rotation table found in CEO note"
        )
    else:
        total_score += add_check(
            "A valid thinker from rotation table is used",
            False,
            "Cannot check: no CEO note found"
        )

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 4: CEO note does NOT re-discuss "不要再问" topics from prev Synthesis
    #          Banned: "多智能体通信协议的底层实现细节", "为什么 LangChain 接口不稳定"
    # ════════════════════════════════════════════════════════════════════════
    if note_content:
        banned_topics = ["LangChain", "langchain", "底层实现细节", "通信协议的底层"]
        violations = [t for t in banned_topics if t.lower() in note_content.lower()]
        total_score += add_check(
            "Saturated '不要再问' topics avoided",
            len(violations) == 0,
            f"No banned topics found (correct)" if len(violations) == 0
            else f"FAIL: Found banned topics: {violations}"
        )
    else:
        total_score += add_check(
            "Saturated '不要再问' topics avoided",
            False,
            "Cannot check: no CEO note found"
        )

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 5: CEO note contains the MANDATORY "反例/致命质疑" section
    #          (per core-functions.md: must include adversarial counter-argument)
    # ════════════════════════════════════════════════════════════════════════
    if note_content:
        counter_keywords = ["反例", "致命质疑", "驳斥", "盲区", "对立视角", "批判", "推翻", "质疑", "blindspot", "counter"]
        has_counter = any(kw.lower() in note_content.lower() for kw in counter_keywords)
        total_score += add_check(
            "CEO note contains mandatory adversarial counter-argument (反例/致命质疑)",
            has_counter,
            "Found adversarial/counter section in CEO note" if has_counter
            else "FAIL: No adversarial counter-argument found. CEO思维模拟 requires '反例/致命质疑' section"
        )
    else:
        total_score += add_check(
            "CEO note contains mandatory adversarial counter-argument (反例/致命质疑)",
            False,
            "Cannot check: no CEO note found"
        )

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 6: CEO note ends with transparency marker
    #          "🤖 DMN Autonomous Output"
    # ════════════════════════════════════════════════════════════════════════
    if note_content:
        has_marker = "🤖 DMN Autonomous Output" in note_content or "DMN Autonomous Output" in note_content
        total_score += add_check(
            "Note has transparency marker '🤖 DMN Autonomous Output'",
            has_marker,
            "Transparency marker found at end of note" if has_marker
            else "FAIL: Missing required '> 🤖 DMN Autonomous Output - [时间]' marker"
        )
    else:
        total_score += add_check(
            "Note has transparency marker '🤖 DMN Autonomous Output'",
            False,
            "Cannot check: no CEO note found"
        )

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 7: Session Synthesis file exists for 2026-06-12
    #          Naming: 20260612_DMN_Synthesis_HHMM.md
    # ════════════════════════════════════════════════════════════════════════
    synthesis_files = find_files("20260612_DMN_Synthesis_*.md")
    if synthesis_files:
        synth_file = synthesis_files[0]
        synth_content = synth_file.read_text(encoding="utf-8", errors="replace")
        total_score += add_check(
            "Session Synthesis file created (20260612_DMN_Synthesis_HHMM.md)",
            True,
            f"Found: {synth_file.name}"
        )
    else:
        synth_content = ""
        total_score += add_check(
            "Session Synthesis file created (20260612_DMN_Synthesis_HHMM.md)",
            False,
            "No file matching '20260612_DMN_Synthesis_HHMM.md' found"
        )

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 8: Synthesis contains all required sections from template
    # ════════════════════════════════════════════════════════════════════════
    required_sections = ["想清楚了", "极客行动提案", "行动计划", "未解问题", "不要再问"]
    if synth_content:
        missing = [s for s in required_sections if s not in synth_content]
        total_score += add_check(
            "Synthesis contains all required template sections",
            len(missing) == 0,
            f"All required sections present" if len(missing) == 0
            else f"FAIL: Missing sections: {missing}"
        )
    else:
        total_score += add_check(
            "Synthesis contains all required template sections",
            False,
            "Cannot check: no Synthesis file found"
        )

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 9: Synthesis has 极客行动提案 and references an AI/workflow improvement
    #          (triggers Evolution Handoff rule)
    # ════════════════════════════════════════════════════════════════════════
    if synth_content:
        has_agentic = "极客行动提案" in synth_content and ("Agentic Action" in synth_content or "行动提案" in synth_content)
        # Check if Synthesis also has transparency marker
        synth_has_marker = "🤖 DMN Autonomous Output" in synth_content or "DMN Autonomous Output" in synth_content
        total_score += add_check(
            "Synthesis has Agentic Action Proposal section + transparency marker",
            has_agentic and synth_has_marker,
            f"Agentic proposal: {has_agentic}, marker: {synth_has_marker}"
        )
    else:
        total_score += add_check(
            "Synthesis has Agentic Action Proposal section + transparency marker",
            False,
            "Cannot check: no Synthesis file found"
        )

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 10: dmn-state.json updated correctly
    #           - lastFunction = "CEO思维模拟"
    #           - lastCEO must NOT be Charlie Munger
    #           - lastSynthesisFile points to today's Synthesis
    # ════════════════════════════════════════════════════════════════════════
    try:
        state_path = ws / "dmn-state.json"
        state_data = json.loads(state_path.read_text(encoding="utf-8"))
        
        last_function_ok = state_data.get("lastFunction", "") == "CEO思维模拟"
        last_ceo_changed = state_data.get("lastCEO", "") != "Charlie Munger"
        last_ceo_valid = any(
            ceo.lower() in state_data.get("lastCEO", "").lower()
            for ceo in ["Bezos", "Musk", "Graham", "Naval", "Grove", "Feynman",
                        "贝佐斯", "马斯克", "费曼", "格鲁夫"]
        )
        synth_updated = "20260612" in state_data.get("lastSynthesisFile", "")
        
        all_state_ok = last_function_ok and last_ceo_changed and synth_updated
        total_score += add_check(
            "dmn-state.json correctly updated (lastFunction, lastCEO, lastSynthesisFile)",
            all_state_ok,
            f"lastFunction='CEO思维模拟':{last_function_ok}, lastCEO changed:{last_ceo_changed}('{state_data.get('lastCEO','')}'), synthFile updated:{synth_updated}"
        )
    except Exception as e:
        total_score += add_check(
            "dmn-state.json correctly updated (lastFunction, lastCEO, lastSynthesisFile)",
            False,
            f"Error reading dmn-state.json: {e}"
        )

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 11: memory/evolve/candidates.md has a NEW entry appended
    #           (Evolution Handoff — triggered because action proposal is meta/AI-related)
    # ════════════════════════════════════════════════════════════════════════
    try:
        candidates_path = ws / "memory/evolve/candidates.md"
        candidates_content = candidates_path.read_text(encoding="utf-8", errors="replace")
        
        # Original file had exactly 1 entry from 2026-06-10
        # A new entry for 2026-06-12 must have been appended
        original_entry_count = 1
        date_entries = re.findall(r"\[2026-06-\d+\]", candidates_content)
        new_entries = [e for e in date_entries if "2026-06-10" not in e]
        has_new_entry = len(new_entries) > 0 or len(date_entries) > original_entry_count
        
        # More lenient: just check that something was appended beyond original content
        original_content = "# Evolution Candidates Queue\n\n## Entries\n- [2026-06-10] Build self-describing Agent capability contract schema\n"
        content_grew = len(candidates_content.strip()) > len(original_content.strip())
        
        total_score += add_check(
            "memory/evolve/candidates.md has new Evolution Handoff entry appended",
            has_new_entry or content_grew,
            f"New date entries found: {new_entries}, content grew: {content_grew}" if (has_new_entry or content_grew)
            else f"FAIL: No new entry appended to candidates.md. Evolution Handoff rule requires appending meta proposals."
        )
    except Exception as e:
        total_score += add_check(
            "memory/evolve/candidates.md has new Evolution Handoff entry appended",
            False,
            f"Error reading candidates.md: {e}"
        )

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 12: Output files are in the correct directory structure
    #           output/2026-06-12/ (not scattered in root)
    # ════════════════════════════════════════════════════════════════════════
    today_output_dir = ws / "output" / "2026-06-12"
    new_files_in_dir = [f for f in today_output_dir.rglob("20260612_*.md")
                        if f.stat().st_mtime > (ws / "output/2026-06-12/20260612_意义生成_RAG管道优化洞见.md").stat().st_mtime]
    total_score += add_check(
        "New output files placed in output/2026-06-12/ directory",
        len(new_files_in_dir) >= 1,
        f"Found {len(new_files_in_dir)} new file(s) in correct output directory" if new_files_in_dir
        else "FAIL: No new 20260612_*.md files found in output/2026-06-12/ — files may be misplaced"
    )

    # ════════════════════════════════════════════════════════════════════════
    # FINAL SCORING
    # ════════════════════════════════════════════════════════════════════════
    num_checks = len(checks)
    passed_checks = sum(1 for c in checks if c["passed"])
    score = passed_checks / num_checks if num_checks > 0 else 0.0
    overall_passed = score >= 0.75  # Require at least 75% to pass

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))