import sys
import json
import re
from pathlib import Path

def find_drill_session(workspace: Path):
    """Find drill_session.md anywhere in workspace."""
    candidates = list(workspace.rglob("drill_session.md"))
    if not candidates:
        return None
    # Prefer root-level, then any
    for c in candidates:
        if c.parent == workspace:
            return c
    return candidates[0]

def count_japanese_chars(text: str) -> int:
    """Count CJK/kana characters as a proxy for Japanese content."""
    count = 0
    for ch in text:
        cp = ord(ch)
        if (0x3040 <= cp <= 0x30FF or   # hiragana/katakana
            0x4E00 <= cp <= 0x9FFF or   # CJK unified
            0x3400 <= cp <= 0x4DBF or   # CJK extension A
            0xFF00 <= cp <= 0xFFEF):    # fullwidth
            count += 1
    return count

def eval_drill_session(workspace_path: str):
    workspace = Path(workspace_path)
    checks = []
    
    # --- Locate file ---
    drill_file = find_drill_session(workspace)
    
    if drill_file is None:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "drill_session.md not found anywhere in workspace"}]
        }
    
    try:
        content = drill_file.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_readable", "passed": False, "detail": f"Could not read drill_session.md: {e}"}]
        }
    
    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {drill_file.relative_to(workspace)}"})
    
    # --- CHECK 1: Section 1 - Vocabulary (10 words) ---
    try:
        # Section 1 header
        sec1_match = re.search(r'#+\s*1[\.:]?\s*Vocab', content, re.IGNORECASE)
        has_sec1 = sec1_match is not None
        checks.append({"name": "section1_vocabulary_header", "passed": has_sec1,
                        "detail": "Section 1 (Vocabulary) header found" if has_sec1 else "Section 1 (Vocabulary) header missing"})
        
        # Count JLPT tags - each word should have one
        jlpt_tags = re.findall(r'\[N[1-5]\]', content)
        vocab_tag_count = len(jlpt_tags)
        # At least 10 JLPT tags for vocabulary words (there may be more from other sections)
        has_10_vocab_tags = vocab_tag_count >= 10
        checks.append({"name": "section1_jlpt_tags_min10", "passed": has_10_vocab_tags,
                        "detail": f"Found {vocab_tag_count} JLPT tags (need ≥10 for 10 vocabulary words)"})
        
        # Romaji: check for romaji-style text (lowercase latin sequences that look like romanized Japanese)
        romaji_patterns = re.findall(r'\b[a-z]{2,}(?:u|i|a|o|e|n)(?:\s+[a-z]{2,}(?:u|i|a|o|e|n))?\b', content)
        has_romaji = len(romaji_patterns) >= 5
        checks.append({"name": "section1_romaji_present", "passed": has_romaji,
                        "detail": f"Romaji pronunciations found: {len(romaji_patterns)} matches (need ≥5)"})
        
        # Japanese characters in content (vocabulary words)
        jp_char_count = count_japanese_chars(content)
        has_japanese = jp_char_count >= 50
        checks.append({"name": "section1_japanese_script", "passed": has_japanese,
                        "detail": f"Japanese characters found: {jp_char_count} (need ≥50)"})
        
        # Memory tip presence
        memory_tip = re.search(r'(memory tip|tip:|mnemonic|remember)', content, re.IGNORECASE)
        has_memory_tip = memory_tip is not None
        checks.append({"name": "section1_memory_tip", "passed": has_memory_tip,
                        "detail": "Memory tip found in vocabulary section" if has_memory_tip else "No memory tip found (required for vocabulary words where useful)"})
        
        # Example sentences - should have Japanese + English translation pairs for vocab
        example_sentence_markers = re.findall(r'(例文|example|e\.g\.?|ex\.?)', content, re.IGNORECASE)
        has_examples = len(example_sentence_markers) >= 3
        checks.append({"name": "section1_example_sentences", "passed": has_examples,
                        "detail": f"Example sentence markers found: {len(example_sentence_markers)}"})
        
    except Exception as e:
        checks.append({"name": "section1_vocabulary", "passed": False, "detail": f"Error checking section 1: {e}"})
    
    # --- CHECK 2: Section 2 - Grammar Pattern ---
    try:
        sec2_match = re.search(r'#+\s*2[\.:]?\s*Grammar', content, re.IGNORECASE)
        has_sec2 = sec2_match is not None
        checks.append({"name": "section2_grammar_header", "passed": has_sec2,
                        "detail": "Section 2 (Grammar) header found" if has_sec2 else "Section 2 (Grammar) header missing"})
        
        # 3 example sentences in grammar section - look for numbered items or example markers after grammar header
        if sec2_match:
            sec2_start = sec2_match.start()
            # Find next major section
            sec3_match = re.search(r'#+\s*3[\.:]?\s*Kanji', content[sec2_start:], re.IGNORECASE)
            sec2_end = sec2_start + sec3_match.start() if sec3_match else sec2_start + 2000
            sec2_content = content[sec2_start:sec2_end]
            
            # Count example sentences (numbered list items or bullet points with Japanese)
            example_lines = re.findall(r'(?:^|\n)\s*(?:\d+[\.\):]|\-|\*)\s*.{20,}', sec2_content)
            has_3_grammar_examples = len(example_lines) >= 3
            checks.append({"name": "section2_three_examples", "passed": has_3_grammar_examples,
                            "detail": f"Grammar section has {len(example_lines)} example/list items (need ≥3)"})
            
            # Common mistakes
            mistakes = re.search(r'(common mistake|avoid|wrong|incorrect|don\'t|do not)', sec2_content, re.IGNORECASE)
            has_mistakes = mistakes is not None
            checks.append({"name": "section2_common_mistakes", "passed": has_mistakes,
                            "detail": "Common mistakes section found" if has_mistakes else "Common mistakes section missing"})
        else:
            checks.append({"name": "section2_three_examples", "passed": False, "detail": "Section 2 not found"})
            checks.append({"name": "section2_common_mistakes", "passed": False, "detail": "Section 2 not found"})
    except Exception as e:
        checks.append({"name": "section2_grammar", "passed": False, "detail": f"Error checking section 2: {e}"})
    
    # --- CHECK 3: Section 3 - Kanji (REQUIRED for N3) ---
    try:
        sec3_match = re.search(r'#+\s*3[\.:]?\s*Kanji', content, re.IGNORECASE)
        has_sec3 = sec3_match is not None
        checks.append({"name": "section3_kanji_header", "passed": has_sec3,
                        "detail": "Section 3 (Kanji) header found — REQUIRED for N3 level" if has_sec3 else "Section 3 (Kanji) header MISSING — this is REQUIRED for N3 (N4 and above)"})
        
        if sec3_match:
            sec3_start = sec3_match.start()
            sec4_match = re.search(r'#+\s*4[\.:]?\s*Reading', content[sec3_start:], re.IGNORECASE)
            sec3_end = sec3_start + sec4_match.start() if sec4_match else sec3_start + 2000
            sec3_content = content[sec3_start:sec3_end]
            
            # Check for on'yomi and kun'yomi readings
            onyomi = re.search(r"(on'?yomi|on-yomi|音読み|おんよみ)", sec3_content, re.IGNORECASE)
            kunyomi = re.search(r"(kun'?yomi|kun-yomi|訓読み|くんよみ)", sec3_content, re.IGNORECASE)
            has_readings = (onyomi is not None) and (kunyomi is not None)
            checks.append({"name": "section3_onyomi_kunyomi", "passed": has_readings,
                            "detail": f"On'yomi: {'found' if onyomi else 'MISSING'}, Kun'yomi: {'found' if kunyomi else 'MISSING'}"})
            
            # Stroke count
            stroke = re.search(r'(stroke|画数|かくすう|\d+\s*stroke)', sec3_content, re.IGNORECASE)
            has_stroke = stroke is not None
            checks.append({"name": "section3_stroke_count", "passed": has_stroke,
                            "detail": "Stroke count found" if has_stroke else "Stroke count missing for kanji entries"})
            
            # Compound words - look for 2 compound words per kanji (at least 6 total, or marker)
            compound = re.search(r'(compound|熟語|じゅくご|compound word)', sec3_content, re.IGNORECASE)
            # Alternative: count CJK character pairs (likely compound words)
            cjk_pairs = re.findall(r'[\u4e00-\u9fff]{2,4}', sec3_content)
            has_compounds = (compound is not None) or len(cjk_pairs) >= 6
            checks.append({"name": "section3_compound_words", "passed": has_compounds,
                            "detail": f"Compound words: {'marker found' if compound else f'{len(cjk_pairs)} CJK word candidates found'} (need ≥6 for 2 per kanji × 3 kanji)"})
            
            # Exactly 3 kanji entries - look for exactly 3 kanji character headings or 3 distinct kanji blocks
            # Look for standalone single kanji characters used as headers/bullets
            kanji_headers = re.findall(r'(?:^|\n)\s*(?:#+|\d+[\.\)]|\*|\-)\s*([\u4e00-\u9fff])\s*(?:\n|$)', sec3_content)
            # Alternative: count major dividers within section3
            kanji_blocks = re.findall(r'(?:^|\n)(?:#{1,4}|[-*]|\d+\.)\s*[\u4e00-\u9fff]', sec3_content)
            three_kanji = len(kanji_headers) == 3 or len(kanji_blocks) >= 3
            checks.append({"name": "section3_exactly_3_kanji", "passed": three_kanji,
                            "detail": f"Kanji entry headers found: {len(kanji_headers)} direct, {len(kanji_blocks)} block markers (need exactly 3)"})
        else:
            checks.append({"name": "section3_onyomi_kunyomi", "passed": False, "detail": "Section 3 not present"})
            checks.append({"name": "section3_stroke_count", "passed": False, "detail": "Section 3 not present"})
            checks.append({"name": "section3_compound_words", "passed": False, "detail": "Section 3 not present"})
            checks.append({"name": "section3_exactly_3_kanji", "passed": False, "detail": "Section 3 not present"})
    except Exception as e:
        checks.append({"name": "section3_kanji", "passed": False, "detail": f"Error checking section 3: {e}"})
    
    # --- CHECK 4: Section 4 - Reading Passage ---
    try:
        sec4_match = re.search(r'#+\s*4[\.:]?\s*Reading', content, re.IGNORECASE)
        has_sec4 = sec4_match is not None
        checks.append({"name": "section4_reading_header", "passed": has_sec4,
                        "detail": "Section 4 (Reading) header found" if has_sec4 else "Section 4 (Reading) header missing"})
        
        if sec4_match:
            sec4_start = sec4_match.start()
            sec5_match = re.search(r'#+\s*5[\.:]?\s*(Listening|Speaking)', content[sec4_start:], re.IGNORECASE)
            sec4_end = sec4_start + sec5_match.start() if sec5_match else sec4_start + 3000
            sec4_content = content[sec4_start:sec4_end]
            
            # Japanese passage present
            jp_in_passage = count_japanese_chars(sec4_content)
            has_jp_passage = jp_in_passage >= 30
            checks.append({"name": "section4_japanese_passage", "passed": has_jp_passage,
                            "detail": f"Japanese characters in reading section: {jp_in_passage} (need ≥30)"})
            
            # English translation present
            english_translation = re.search(r'(translation|english:?|英訳)', sec4_content, re.IGNORECASE)
            # Alternative: check for paragraphs with no Japanese characters (pure English blocks)
            pure_english_blocks = re.findall(r'[A-Za-z ,\.\!\?\'\"]{50,}', sec4_content)
            has_translation = (english_translation is not None) or len(pure_english_blocks) >= 1
            checks.append({"name": "section4_english_translation", "passed": has_translation,
                            "detail": "English translation found in reading section" if has_translation else "English translation missing from reading section"})
            
            # 3 key points highlighted
            key_points = re.findall(r'(key|highlight|point|grammar point|vocabulary point|注目|ポイント)', sec4_content, re.IGNORECASE)
            # Alternative: count numbered/bulleted items after the passage
            listed_items = re.findall(r'(?:^|\n)\s*(?:\d+[\.\)]|\*|\-)\s*.{10,}', sec4_content)
            has_3_key_points = len(key_points) >= 1 or len(listed_items) >= 3
            checks.append({"name": "section4_three_key_points", "passed": has_3_key_points,
                            "detail": f"Key point markers: {len(key_points)}, listed items: {len(listed_items)} (need 3 highlighted vocabulary/grammar points)"})
        else:
            checks.append({"name": "section4_japanese_passage", "passed": False, "detail": "Section 4 not present"})
            checks.append({"name": "section4_english_translation", "passed": False, "detail": "Section 4 not present"})
            checks.append({"name": "section4_three_key_points", "passed": False, "detail": "Section 4 not present"})
    except Exception as e:
        checks.append({"name": "section4_reading", "passed": False, "detail": f"Error checking section 4: {e}"})
    
    # --- CHECK 5: Section 5 - Listening/Speaking Prompt ---
    try:
        sec5_match = re.search(r'#+\s*5[\.:]?\s*(Listening|Speaking)', content, re.IGNORECASE)
        has_sec5 = sec5_match is not None
        checks.append({"name": "section5_speaking_header", "passed": has_sec5,
                        "detail": "Section 5 (Speaking/Listening) header found" if has_sec5 else "Section 5 (Speaking/Listening) header missing"})
        
        if sec5_match:
            sec5_start = sec5_match.start()
            sec6_match = re.search(r'#+\s*6[\.:]?\s*(Quiz|Quick)', content[sec5_start:], re.IGNORECASE)
            sec5_end = sec5_start + sec6_match.start() if sec6_match else sec5_start + 3000
            sec5_content = content[sec5_start:sec5_end]
            
            # Dialogue: 2-4 exchanges - look for speaker markers (A:, B:, Person1:, etc.)
            dialogue_turns = re.findall(r'(?:^|\n)\s*(?:[A-Za-zあ-ん一-龯]+[:：]|[AB][:：]|\d+[:：])\s*.+', sec5_content)
            has_dialogue = len(dialogue_turns) >= 4  # at least 2 exchanges = 4 turns (A+B twice)
            checks.append({"name": "section5_dialogue_exchanges", "passed": has_dialogue,
                            "detail": f"Dialogue turns found: {len(dialogue_turns)} (need ≥4 for 2 exchanges)"})
            
            # 3 speaking prompts
            speaking_prompts = re.findall(r'(speaking prompt|practice prompt|prompt \d|try saying|respond to)', sec5_content, re.IGNORECASE)
            # Alternative: numbered items in speaking section
            numbered_items = re.findall(r'(?:^|\n)\s*\d+[\.\)]\s*.{15,}', sec5_content)
            has_3_prompts = len(speaking_prompts) >= 2 or len(numbered_items) >= 3
            checks.append({"name": "section5_three_speaking_prompts", "passed": has_3_prompts,
                            "detail": f"Speaking prompt markers: {len(speaking_prompts)}, numbered items: {len(numbered_items)} (need 3 speaking prompts)"})
            
            # Suggested vocabulary
            vocab_suggestion = re.search(r'(suggested|vocabulary|useful words|response vocab|参考)', sec5_content, re.IGNORECASE)
            has_vocab_suggestion = vocab_suggestion is not None
            checks.append({"name": "section5_suggested_vocabulary", "passed": has_vocab_suggestion,
                            "detail": "Suggested response vocabulary found" if has_vocab_suggestion else "Suggested response vocabulary missing"})
        else:
            checks.append({"name": "section5_dialogue_exchanges", "passed": False, "detail": "Section 5 not present"})
            checks.append({"name": "section5_three_speaking_prompts", "passed": False, "detail": "Section 5 not present"})
            checks.append({"name": "section5_suggested_vocabulary", "passed": False, "detail": "Section 5 not present"})
    except Exception as e:
        checks.append({"name": "section5_speaking", "passed": False, "detail": f"Error checking section 5: {e}"})
    
    # --- CHECK 6: Section 6 - Quick Quiz (5 questions) ---
    try:
        sec6_match = re.search(r'#+\s*6[\.:]?\s*(Quiz|Quick)', content, re.IGNORECASE)
        has_sec6 = sec6_match is not None
        checks.append({"name": "section6_quiz_header", "passed": has_sec6,
                        "detail": "Section 6 (Quiz) header found" if has_sec6 else "Section 6 (Quiz) header missing"})
        
        if sec6_match:
            sec6_start = sec6_match.start()
            # Find cultural note section or end of content
            cultural_match = re.search(r'(cultural note|culture note|文化)', content[sec6_start:], re.IGNORECASE)
            sec6_end = sec6_start + cultural_match.start() if cultural_match else len(content)
            sec6_content = content[sec6_start:sec6_end]
            
            # 5 questions: numbered items
            numbered_questions = re.findall(r'(?:^|\n)\s*(?:Q?[1-5][\.\):]|Question [1-5])\s*.{10,}', sec6_content)
            has_5_questions = len(numbered_questions) >= 5
            checks.append({"name": "section6_five_questions", "passed": has_5_questions,
                            "detail": f"Numbered quiz questions found: {len(numbered_questions)} (need 5)"})
            
            # CRITICAL: Answers separated by a divider
            # A divider is typically: ---, ***, ===, ___, or similar markdown horizontal rules
            divider_pattern = re.search(r'(---+|\*\*\*+|===+|___+)', sec6_content)
            # Also check for explicit answer section header after divider
            answer_section = re.search(r'(answer|answers|解答|解答例)', sec6_content, re.IGNORECASE)
            has_answer_divider = (divider_pattern is not None) and (answer_section is not None)
            checks.append({"name": "section6_answers_with_divider", "passed": has_answer_divider,
                            "detail": f"Answer divider: {'found' if divider_pattern else 'MISSING'}, Answer section: {'found' if answer_section else 'MISSING'} — SKILL.md requires answers clearly separated with a divider"})
            
            # Mix of question types - kanji reading required for N3 (N4 and above)
            has_kanji_reading_q = re.search(r'(kanji reading|read.*kanji|how.*read|読み方)', sec6_content, re.IGNORECASE)
            has_fill_blank = re.search(r'(fill|blank|___+|\[.*\]|＿+)', sec6_content, re.IGNORECASE)
            has_translation_q = re.search(r'(translat|english to japanese|日本語に)', sec6_content, re.IGNORECASE)
            question_variety = sum([
                has_kanji_reading_q is not None,
                has_fill_blank is not None,
                has_translation_q is not None
            ])
            has_variety = question_variety >= 2
            checks.append({"name": "section6_question_variety", "passed": has_variety,
                            "detail": f"Question types found: kanji_reading={'yes' if has_kanji_reading_q else 'no'}, fill_blank={'yes' if has_fill_blank else 'no'}, translation={'yes' if has_translation_q else 'no'} (need ≥2 types, kanji required for N3)"})
        else:
            checks.append({"name": "section6_five_questions", "passed": False, "detail": "Section 6 not present"})
            checks.append({"name": "section6_answers_with_divider", "passed": False, "detail": "Section 6 not present — CRITICAL: answers must be separated by divider"})
            checks.append({"name": "section6_question_variety", "passed": False, "detail": "Section 6 not present"})
    except Exception as e:
        checks.append({"name": "section6_quiz", "passed": False, "detail": f"Error checking section 6: {e}"})
    
    # --- CHECK 7: Cultural Note at end ---
    try:
        cultural_match = re.search(r'(cultural note|culture note|文化メモ|文化ノート|cultural tip)', content, re.IGNORECASE)
        has_cultural_note = cultural_match is not None
        checks.append({"name": "cultural_note_present", "passed": has_cultural_note,
                        "detail": "Cultural note found at end of session" if has_cultural_note else "Cultural note MISSING — SKILL.md requires every session to end with a cultural note"})
        
        if has_cultural_note:
            # Check it's at the end (after section 6)
            sec6_match2 = re.search(r'#+\s*6[\.:]?\s*(Quiz|Quick)', content, re.IGNORECASE)
            if sec6_match2:
                after_quiz = content[sec6_match2.start():]
                cultural_after_quiz = re.search(r'(cultural note|culture note)', after_quiz, re.IGNORECASE)
                is_at_end = cultural_after_quiz is not None
                checks.append({"name": "cultural_note_at_end", "passed": is_at_end,
                                "detail": "Cultural note appears after quiz section (correct position)" if is_at_end else "Cultural note not at end of document"})
            else:
                checks.append({"name": "cultural_note_at_end", "passed": False, "detail": "Could not verify position without quiz section"})
        else:
            checks.append({"name": "cultural_note_at_end", "passed": False, "detail": "No cultural note found"})
    except Exception as e:
        checks.append({"name": "cultural_note", "passed": False, "detail": f"Error checking cultural note: {e}"})
    
    # --- CHECK 8: N3 Level appropriateness ---
    try:
        # The session should reference N3 level
        level_ref = re.search(r'N3|N[- ]?3|intermediate|中級', content, re.IGNORECASE)
        has_level_ref = level_ref is not None
        checks.append({"name": "n3_level_referenced", "passed": has_level_ref,
                        "detail": "N3 level reference found in document" if has_level_ref else "N3 level not referenced in document"})
        
        # N5 kanji skip rule: kanji section should NOT be skipped (N3 requires it)
        # We already checked kanji section is present - this is the anti-N5 trap
        kanji_skip_msg = re.search(r'skip.*kanji|kanji.*skip|no kanji section|kanji not required', content, re.IGNORECASE)
        kanji_not_skipped = kanji_skip_msg is None
        checks.append({"name": "kanji_not_skipped_for_n3", "passed": kanji_not_skipped,
                        "detail": "Kanji section correctly included (not skipped) for N3 level" if kanji_not_skipped else "Document incorrectly claims to skip kanji for N3 — kanji skip is only for N5"})
    except Exception as e:
        checks.append({"name": "n3_level_check", "passed": False, "detail": f"Error checking N3 level: {e}"})
    
    # --- CHECK 9: All 6 sections present ---
    try:
        section_headers = {
            "section_1_vocab": bool(re.search(r'#+\s*1[\.:]?\s*Vocab', content, re.IGNORECASE)),
            "section_2_grammar": bool(re.search(r'#+\s*2[\.:]?\s*Grammar', content, re.IGNORECASE)),
            "section_3_kanji": bool(re.search(r'#+\s*3[\.:]?\s*Kanji', content, re.IGNORECASE)),
            "section_4_reading": bool(re.search(r'#+\s*4[\.:]?\s*Reading', content, re.IGNORECASE)),
            "section_5_speaking": bool(re.search(r'#+\s*5[\.:]?\s*(Listening|Speaking)', content, re.IGNORECASE)),
            "section_6_quiz": bool(re.search(r'#+\s*6[\.:]?\s*(Quiz|Quick)', content, re.IGNORECASE)),
        }
        all_present = all(section_headers.values())
        missing = [k for k, v in section_headers.items() if not v]
        checks.append({"name": "all_six_sections_present", "passed": all_present,
                        "detail": f"All 6 sections present" if all_present else f"Missing sections: {missing}"})
    except Exception as e:
        checks.append({"name": "all_six_sections_present", "passed": False, "detail": f"Error: {e}"})
    
    # --- Final scoring ---
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)
    
    # Must pass critical checks to be overall passing
    critical_checks = [
        "file_exists",
        "section3_kanji_header",       # N3 kanji required
        "section6_answers_with_divider", # divider is proprietary requirement
        "all_six_sections_present",
        "cultural_note_present",
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical_checks
    )
    
    overall_passed = critical_passed and score >= 0.65
    
    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    
    result = eval_drill_session(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))