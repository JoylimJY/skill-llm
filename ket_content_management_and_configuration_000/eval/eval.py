import sys
import json
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # Find exam_config.json anywhere in workspace
    found_files = list(Path(workspace_dir).rglob("exam_config.json"))
    
    if not found_files:
        add_check("file_exists", False, "exam_config.json not found anywhere in workspace")
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}
    
    # Prefer the one in platform/config/ if multiple exist
    target = None
    for f in found_files:
        if "platform/config" in str(f) and "legacy" not in str(f) and "drafts" not in str(f):
            target = f
            break
    if target is None:
        target = found_files[0]
    
    add_check("file_exists", True, f"Found exam_config.json at {target}")
    
    try:
        with open(target) as f:
            config = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        add_check("json_valid", False, f"Failed to parse JSON: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}
    
    add_check("json_valid", True, "JSON parses successfully")

    def deep_find(obj, *keys):
        """Try to find a value by traversing nested dict with any of the given key paths."""
        if not isinstance(obj, dict):
            return None
        for key in keys:
            if key in obj:
                val = obj[key]
                if isinstance(val, dict):
                    return val
                return val
        return None

    def find_nested(obj, key):
        """Recursively search for a key in nested dicts."""
        if isinstance(obj, dict):
            if key in obj:
                return obj[key]
            for v in obj.values():
                result = find_nested(v, key)
                if result is not None:
                    return result
        elif isinstance(obj, list):
            for item in obj:
                result = find_nested(item, key)
                if result is not None:
                    return result
        return None

    def find_value(obj, *keys):
        """Search for any of the given keys recursively."""
        for key in keys:
            result = find_nested(obj, key)
            if result is not None:
                return result
        return None

    # ── Check 1: Reading+Writing module duration = 60 minutes ──────────────
    try:
        rw_duration = find_value(config, "reading_writing_duration", "rw_duration_minutes", "duration_minutes")
        # Also search inside reading_writing module
        rw_module = find_value(config, "reading_writing", "reading_and_writing", "reading")
        if rw_module and isinstance(rw_module, dict):
            rw_duration = rw_module.get("duration_minutes", rw_duration)
        
        # Try all modules
        modules = config.get("modules", {})
        for mod_key in ["reading_writing", "reading_and_writing", "reading"]:
            if mod_key in modules:
                m = modules[mod_key]
                if isinstance(m, dict) and "duration_minutes" in m:
                    rw_duration = m["duration_minutes"]
                    break
        
        passed = (rw_duration == 60)
        add_check("rw_duration_60min", passed, 
                  f"Reading+Writing duration should be 60 min, found: {rw_duration}")
    except Exception as e:
        add_check("rw_duration_60min", False, f"Error checking RW duration: {e}")

    # ── Check 2: Total Reading+Writing questions = 32 ──────────────────────
    try:
        total_rw = find_value(config, "total_reading_writing_questions", "reading_writing_total_questions", "total_rw_questions")
        passed = (total_rw == 32)
        add_check("total_rw_questions_32", passed,
                  f"Total R+W questions should be 32, found: {total_rw}")
    except Exception as e:
        add_check("total_rw_questions_32", False, f"Error: {e}")

    # ── Check 3: Part 1 Reading - 6 texts ─────────────────────────────────
    try:
        # Search for part1 inside reading/reading_writing module
        part1_texts = None
        for mod_key in ["reading_writing", "reading_and_writing", "reading"]:
            mod = (config.get("modules") or {}).get(mod_key, {})
            parts = mod.get("parts", {})
            p1 = parts.get("part1", parts.get("part_1", {}))
            if p1:
                part1_texts = p1.get("num_texts", p1.get("texts", p1.get("num_passages")))
                break
        if part1_texts is None:
            part1_texts = find_value(config, "reading_part1_texts")
        
        passed = (part1_texts == 6)
        add_check("reading_part1_6texts", passed,
                  f"Reading Part 1 should have 6 short texts, found: {part1_texts}")
    except Exception as e:
        add_check("reading_part1_6texts", False, f"Error: {e}")

    # ── Check 4: Part 2 Reading - 7 questions, 3 texts ────────────────────
    try:
        part2_questions = None
        part2_texts = None
        for mod_key in ["reading_writing", "reading_and_writing", "reading"]:
            mod = (config.get("modules") or {}).get(mod_key, {})
            parts = mod.get("parts", {})
            p2 = parts.get("part2", parts.get("part_2", {}))
            if p2:
                part2_questions = p2.get("num_questions", p2.get("questions"))
                part2_texts = p2.get("num_texts", p2.get("texts"))
                break

        passed_q = (part2_questions == 7)
        passed_t = (part2_texts == 3)
        add_check("reading_part2_7questions", passed_q,
                  f"Reading Part 2 should have 7 questions, found: {part2_questions}")
        add_check("reading_part2_3texts", passed_t,
                  f"Reading Part 2 should have 3 texts, found: {part2_texts}")
    except Exception as e:
        add_check("reading_part2_7questions", False, f"Error: {e}")
        add_check("reading_part2_3texts", False, f"Error: {e}")

    # ── Check 5: Part 4 Reading - 6 blanks, 4 options each ───────────────
    try:
        part4_blanks = None
        part4_options = None
        for mod_key in ["reading_writing", "reading_and_writing", "reading"]:
            mod = (config.get("modules") or {}).get(mod_key, {})
            parts = mod.get("parts", {})
            p4 = parts.get("part4", parts.get("part_4", {}))
            if p4:
                part4_blanks = p4.get("num_blanks", p4.get("blanks"))
                part4_options = p4.get("options_per_blank", p4.get("options_per_question", p4.get("choices")))
                break

        passed_b = (part4_blanks == 6)
        passed_o = (part4_options == 4)
        add_check("reading_part4_6blanks", passed_b,
                  f"Reading Part 4 should have 6 blanks, found: {part4_blanks}")
        add_check("reading_part4_4options", passed_o,
                  f"Reading Part 4 should have 4 options per blank, found: {part4_options}")
    except Exception as e:
        add_check("reading_part4_6blanks", False, f"Error: {e}")
        add_check("reading_part4_4options", False, f"Error: {e}")

    # ── Check 6: Part 5 Reading - 6 blanks, 1 word each ──────────────────
    try:
        part5_blanks = None
        for mod_key in ["reading_writing", "reading_and_writing", "reading"]:
            mod = (config.get("modules") or {}).get(mod_key, {})
            parts = mod.get("parts", {})
            p5 = parts.get("part5", parts.get("part_5", {}))
            if p5:
                part5_blanks = p5.get("num_blanks", p5.get("blanks"))
                break

        passed = (part5_blanks == 6)
        add_check("reading_part5_6blanks", passed,
                  f"Reading Part 5 should have 6 blanks, found: {part5_blanks}")
    except Exception as e:
        add_check("reading_part5_6blanks", False, f"Error: {e}")

    # ── Check 7: Writing Part 6 - min 25 words, 3 key points ─────────────
    try:
        part6_min_words = None
        part6_key_points = None
        for mod_key in ["reading_writing", "reading_and_writing", "writing"]:
            mod = (config.get("modules") or {}).get(mod_key, {})
            parts = mod.get("parts", {})
            p6 = parts.get("part6", parts.get("part_6", {}))
            if p6:
                part6_min_words = p6.get("min_words", p6.get("minimum_words"))
                part6_key_points = p6.get("key_points", p6.get("num_key_points", p6.get("required_points")))
                break
        
        if part6_min_words is None:
            part6_min_words = find_value(config, "part6_min_words", "writing_part6_min_words")
        if part6_key_points is None:
            part6_key_points = find_value(config, "part6_key_points", "writing_part6_key_points")

        passed_w = (part6_min_words == 25)
        passed_kp = (part6_key_points == 3)
        add_check("writing_part6_min25words", passed_w,
                  f"Writing Part 6 minimum should be 25 words, found: {part6_min_words}")
        add_check("writing_part6_3keypoints", passed_kp,
                  f"Writing Part 6 should require 3 key points, found: {part6_key_points}")
    except Exception as e:
        add_check("writing_part6_min25words", False, f"Error: {e}")
        add_check("writing_part6_3keypoints", False, f"Error: {e}")

    # ── Check 8: Writing Part 7 - min 35 words, 3 images ─────────────────
    try:
        part7_min_words = None
        part7_images = None
        for mod_key in ["reading_writing", "reading_and_writing", "writing"]:
            mod = (config.get("modules") or {}).get(mod_key, {})
            parts = mod.get("parts", {})
            p7 = parts.get("part7", parts.get("part_7", {}))
            if p7:
                part7_min_words = p7.get("min_words", p7.get("minimum_words"))
                part7_images = p7.get("num_images", p7.get("images"))
                break
        
        if part7_min_words is None:
            part7_min_words = find_value(config, "part7_min_words", "writing_part7_min_words")
        if part7_images is None:
            part7_images = find_value(config, "part7_images", "part7_num_images")

        passed_w = (part7_min_words == 35)
        passed_i = (part7_images == 3)
        add_check("writing_part7_min35words", passed_w,
                  f"Writing Part 7 minimum should be 35 words, found: {part7_min_words}")
        add_check("writing_part7_3images", passed_i,
                  f"Writing Part 7 should have 3 images, found: {part7_images}")
    except Exception as e:
        add_check("writing_part7_min35words", False, f"Error: {e}")
        add_check("writing_part7_3images", False, f"Error: {e}")

    # ── Check 9: Listening duration = 30 minutes (incl. 6 min transcription) ─
    try:
        listening_duration = None
        transcription_minutes = None
        listening_mod = (config.get("modules") or {}).get("listening", {})
        if listening_mod:
            listening_duration = listening_mod.get("duration_minutes", listening_mod.get("total_duration_minutes"))
            transcription_minutes = listening_mod.get("transcription_minutes", listening_mod.get("copy_time_minutes"))
        
        if listening_duration is None:
            listening_duration = find_value(config, "listening_duration", "listening_duration_minutes")
        if transcription_minutes is None:
            transcription_minutes = find_value(config, "transcription_minutes", "copy_time_minutes", "transcription_window_minutes")

        passed_d = (listening_duration == 30)
        passed_t = (transcription_minutes == 6)
        add_check("listening_duration_30min", passed_d,
                  f"Listening duration should be 30 min, found: {listening_duration}")
        add_check("listening_transcription_6min", passed_t,
                  f"Listening transcription window should be 6 min, found: {transcription_minutes}")
    except Exception as e:
        add_check("listening_duration_30min", False, f"Error: {e}")
        add_check("listening_transcription_6min", False, f"Error: {e}")

    # ── Check 10: Listening playback count = 2 ───────────────────────────
    try:
        playback_count = None
        listening_mod = (config.get("modules") or {}).get("listening", {})
        if listening_mod:
            playback_count = listening_mod.get("playback_count", listening_mod.get("audio_plays", listening_mod.get("plays_per_audio")))
        if playback_count is None:
            playback_count = find_value(config, "playback_count", "audio_playback_count", "plays_per_recording")

        passed = (playback_count == 2)
        add_check("listening_playback_2times", passed,
                  f"Listening playback count should be 2, found: {playback_count}")
    except Exception as e:
        add_check("listening_playback_2times", False, f"Error: {e}")

    # ── Check 11: Total listening questions = 25 ─────────────────────────
    try:
        total_listening = find_value(config, "total_listening_questions", "listening_total_questions")
        passed = (total_listening == 25)
        add_check("total_listening_questions_25", passed,
                  f"Total listening questions should be 25, found: {total_listening}")
    except Exception as e:
        add_check("total_listening_questions_25", False, f"Error: {e}")

    # ── Check 12: Speaking duration 8-10 min per pair ─────────────────────
    try:
        speaking_mod = (config.get("modules") or {}).get("speaking", {})
        speaking_min = None
        speaking_max = None
        if speaking_mod:
            dur = speaking_mod.get("duration_minutes_per_pair", speaking_mod.get("duration_per_pair", speaking_mod.get("duration_minutes")))
            if isinstance(dur, dict):
                speaking_min = dur.get("min")
                speaking_max = dur.get("max")
            elif isinstance(dur, str) and "-" in str(dur):
                parts_dur = str(dur).split("-")
                speaking_min = int(parts_dur[0].strip())
                speaking_max = int(parts_dur[1].strip())
            speaking_min_key = speaking_mod.get("duration_min_minutes", speaking_mod.get("min_duration_minutes"))
            speaking_max_key = speaking_mod.get("duration_max_minutes", speaking_mod.get("max_duration_minutes"))
            if speaking_min is None:
                speaking_min = speaking_min_key
            if speaking_max is None:
                speaking_max = speaking_max_key

        passed = (speaking_min == 8 and speaking_max == 10)
        add_check("speaking_duration_8to10min", passed,
                  f"Speaking duration should be 8-10 min per pair, found min={speaking_min}, max={speaking_max}")
    except Exception as e:
        add_check("speaking_duration_8to10min", False, f"Error: {e}")

    # ── Check 13: Vocabulary thresholds ──────────────────────────────────
    try:
        vocab = find_value(config, "vocab_levels", "vocabulary_levels", "vocabulary_thresholds", "learner_levels")
        pre_a1_vocab = None
        a1_vocab = None
        a2_vocab = None
        
        if isinstance(vocab, dict):
            pre_a1_vocab = vocab.get("pre_a1", vocab.get("pre-a1", vocab.get("prea1")))
            a1_vocab = vocab.get("a1")
            a2_vocab = vocab.get("a2")
        
        # Check approximately correct ranges (±50 tolerance for "~" values in skill doc)
        def in_range(val, target, tolerance=50):
            if val is None:
                return False
            return abs(int(val) - target) <= tolerance

        passed_pre = in_range(pre_a1_vocab, 300)
        passed_a1 = in_range(a1_vocab, 600)
        passed_a2 = in_range(a2_vocab, 1500)
        
        add_check("vocab_pre_a1_approx300", passed_pre,
                  f"Pre-A1 vocab should be ~300, found: {pre_a1_vocab}")
        add_check("vocab_a1_approx600", passed_a1,
                  f"A1 vocab should be ~600, found: {a1_vocab}")
        add_check("vocab_a2_approx1500", passed_a2,
                  f"A2 vocab should be ~1500, found: {a2_vocab}")
    except Exception as e:
        add_check("vocab_pre_a1_approx300", False, f"Error: {e}")
        add_check("vocab_a1_approx600", False, f"Error: {e}")
        add_check("vocab_a2_approx1500", False, f"Error: {e}")

    # ── Check 14: Listening Part 2 fill-in type includes names/numbers/dates ─
    try:
        l_part2 = None
        listening_mod = (config.get("modules") or {}).get("listening", {})
        if listening_mod:
            parts_l = listening_mod.get("parts", {})
            l_part2 = parts_l.get("part2", parts_l.get("part_2", {}))
        
        if l_part2 and isinstance(l_part2, dict):
            blanks = l_part2.get("num_blanks", l_part2.get("blanks"))
            passed = (blanks == 5)
            # check input types mention names, numbers, dates
            input_types = l_part2.get("input_types", l_part2.get("field_types", []))
            types_str = str(input_types).lower()
            has_name = "name" in types_str
            has_number = "number" in types_str or "digit" in types_str
            has_date = "date" in types_str
            
            add_check("listening_part2_5blanks", passed,
                      f"Listening Part 2 should have 5 blanks, found: {blanks}")
            add_check("listening_part2_input_types", has_name and has_number and has_date,
                      f"Listening Part 2 input types should include names/numbers/dates. input_types={input_types}")
        else:
            add_check("listening_part2_5blanks", False, "Listening Part 2 not found in config")
            add_check("listening_part2_input_types", False, "Listening Part 2 not found in config")
    except Exception as e:
        add_check("listening_part2_5blanks", False, f"Error: {e}")
        add_check("listening_part2_input_types", False, f"Error: {e}")

    # ── Check 15: Module weights sum to 100% ─────────────────────────────
    try:
        modules = config.get("modules", {})
        total_weight = 0
        weights_found = []
        for mod_key, mod_val in modules.items():
            if isinstance(mod_val, dict):
                w = mod_val.get("weight_percent", mod_val.get("weight", mod_val.get("percentage")))
                if w is not None:
                    total_weight += int(w)
                    weights_found.append((mod_key, w))
        
        passed = (total_weight == 100 and len(weights_found) == 3)
        add_check("module_weights_sum_100", passed,
                  f"Module weights should sum to 100% across 3 modules, found: {weights_found} (total={total_weight})")
    except Exception as e:
        add_check("module_weights_sum_100", False, f"Error: {e}")

    # ── Score calculation ─────────────────────────────────────────────────
    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c["passed"])
    score = round(passed_checks / total_checks, 4) if total_checks > 0 else 0.0
    overall_passed = (score >= 0.80)  # Must pass at least 80% of checks

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))