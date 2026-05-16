import sys
import json
import subprocess
import os
from pathlib import Path

def run_checks(workspace):
    checks = []
    passed_all = True

    # ─── Helper ──────────────────────────────────────────────────────────
    def add_check(name, passed, detail):
        nonlocal passed_all
        checks.append({"name": name, "passed": passed, "detail": detail})
        if not passed:
            passed_all = False

    ws = Path(workspace)

    # ─── Load ground-truth data ───────────────────────────────────────────
    try:
        with open(ws / "tarot_index.json", encoding="utf-8") as f:
            tarot_index = json.load(f)
        with open(ws / "spreads.json", encoding="utf-8") as f:
            spreads_data = json.load(f)
    except Exception as e:
        add_check("Load ground-truth files", False, f"Cannot load index/spreads: {e}")
        return checks, 0.0

    # Build alias→id map from tarot_index.json
    alias_to_id = {}
    id_to_official = {}
    for card in tarot_index["cards"]:
        cid = card["id"]
        official = card["official_name"]
        id_to_official[cid] = official
        alias_to_id[official] = cid
        for alias in card.get("aliases", []):
            alias_to_id[alias] = cid

    # The task specifies these cards (as given in the prompt):
    # 1st position (过去): "智者" (alias for 隐士, ID=9), 逆位
    # 2nd position (现在): "高塔" (alias for 塔, ID=16), 正位
    # 3rd position (未来): "大地之母" (alias for 女皇, ID=3), 逆位
    # Spread: 时间之流 → id = "timeline"

    expected_card_aliases = ["智者", "高塔", "大地之母"]
    expected_card_ids = [alias_to_id.get(a) for a in expected_card_aliases]
    expected_revs = [True, False, True]  # 逆位, 正位, 逆位
    expected_spread_id = "timeline"

    # Verify our ground truth is self-consistent
    assert expected_card_ids == [9, 16, 3], f"Ground truth error: {expected_card_ids}"

    # ─── Check 1: Find reading_result.txt ────────────────────────────────
    result_files = list(ws.rglob("reading_result.txt"))
    if not result_files:
        add_check("Output file exists (reading_result.txt)", False,
                  "reading_result.txt not found anywhere in workspace")
        return checks, 0.0

    result_file = result_files[0]
    add_check("Output file exists (reading_result.txt)", True,
              f"Found at {result_file.relative_to(ws)}")

    # Read file content
    try:
        with open(result_file, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        add_check("Output file readable", False, f"Cannot read file: {e}")
        return checks, 0.0

    add_check("Output file readable", True, f"File has {len(content)} chars")

    if len(content.strip()) < 50:
        add_check("Output file non-trivial content", False,
                  f"Content too short ({len(content.strip())} chars), likely empty/placeholder")
        return checks, 0.0
    add_check("Output file non-trivial content", True, f"Content length: {len(content.strip())} chars")

    # ─── Check 2: Verify compose was called with correct spread ──────────
    # We'll run compose ourselves with the expected params and compare the final_prompt
    try:
        result = subprocess.run(
            ["python", "neko.py", "compose",
             "--spread", expected_spread_id,
             "--cards", ",".join(str(i) for i in expected_card_ids),
             "--revs", ",".join("true" if r else "false" for r in expected_revs),
             "--json"],
            cwd=workspace,
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            add_check("Reference compose command succeeds", False,
                      f"compose failed: {result.stderr}")
            return checks, 0.0

        ref_output = json.loads(result.stdout)
        ref_final_prompt = ref_output.get("final_prompt", "")
        add_check("Reference compose command succeeds", True,
                  f"Got final_prompt with {len(ref_final_prompt)} chars")
    except Exception as e:
        add_check("Reference compose command succeeds", False, f"Exception: {e}")
        return checks, 0.0

    # ─── Check 3: Output contains content from final_prompt ──────────────
    # The final_prompt contains key phrases like card names and position names.
    # The agent must have extracted and incorporated this.
    key_phrases_from_prompt = []
    for card in ref_output.get("drawn_cards", []):
        key_phrases_from_prompt.append(card["card_name"])      # 隐士, 塔, 女皇
        key_phrases_from_prompt.append(card["position"])       # 过去, 现在, 未来

    missing = [p for p in key_phrases_from_prompt if p not in content]
    if missing:
        add_check("Output contains key elements from final_prompt", False,
                  f"Missing key phrases: {missing}")
    else:
        add_check("Output contains key elements from final_prompt", True,
                  f"All key phrases found: {key_phrases_from_prompt}")

    # ─── Check 4: Correct card IDs used (隐士=9, 塔=16, 女皇=3) ──────────
    # Verify by checking that the drawn_cards in reference output have correct ids
    drawn_ids = [c["card_id"] for c in ref_output.get("drawn_cards", [])]
    if drawn_ids == expected_card_ids:
        add_check("Correct card IDs resolved from aliases", True,
                  f"IDs: {drawn_ids} match expected {expected_card_ids}")
    else:
        add_check("Correct card IDs resolved from aliases", False,
                  f"Got IDs {drawn_ids}, expected {expected_card_ids}")

    # ─── Check 5: Correct reversal order (True, False, True) ─────────────
    drawn_revs = [c["reversed"] for c in ref_output.get("drawn_cards", [])]
    if drawn_revs == expected_revs:
        add_check("Correct reversal order (逆,正,逆)", True,
                  f"Revs: {drawn_revs}")
    else:
        add_check("Correct reversal order (逆,正,逆)", False,
                  f"Got revs {drawn_revs}, expected {expected_revs}")

    # ─── Check 6: Correct spread used (timeline) ─────────────────────────
    spread_name_in_content = "时间之流" in content
    spread_positions = ["过去", "现在", "未来"]
    positions_found = all(p in content for p in spread_positions)

    if spread_name_in_content or positions_found:
        add_check("Correct spread (时间之流/timeline) reflected in output", True,
                  f"'时间之流' in content: {spread_name_in_content}, positions found: {positions_found}")
    else:
        add_check("Correct spread (时间之流/timeline) reflected in output", False,
                  f"Neither '时间之流' nor position names (过去/现在/未来) found in output")

    # ─── Check 7: Output references user's stated intent (career/job) ────
    # The user's stated concern is about career transition / job change
    career_keywords = ["事业", "工作", "转行", "职业", "career"]
    career_found = any(kw in content for kw in career_keywords)
    if career_found:
        add_check("Output references user's stated intent (career/事业)", True,
                  f"Found career-related keyword in content")
    else:
        add_check("Output references user's stated intent (career/事业)", False,
                  f"None of {career_keywords} found in output — agent may have ignored user's question context")

    # ─── Check 8: Neko persona present ───────────────────────────────────
    neko_markers = ["喵", "猫咪", "猫"]
    neko_found = any(m in content for m in neko_markers)
    add_check("Neko persona maintained in output", neko_found,
              f"Neko markers {'found' if neko_found else 'NOT found'} in reading_result.txt")

    # ─── Score calculation ────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)

    return checks, score


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [],
                          "error": "Usage: eval.py <workspace_path>"}))
        sys.exit(1)

    workspace = sys.argv[1]
    try:
        checks, score = run_checks(workspace)
        passed = score >= 0.75
        print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [],
                          "error": f"Eval script crashed: {e}"}, ensure_ascii=False))