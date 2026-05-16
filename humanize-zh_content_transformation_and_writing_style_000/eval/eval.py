import sys
import os
import json
import re
from pathlib import Path

def check_text(text: str, article_id: str) -> list:
    checks = []

    # -------------------------------------------------------
    # CHECK 1: Must NOT use AI connector words: 首先/其次/最后 pattern
    # The skill requires breaking "第一...第二...第三" / "首先...其次...最后" structures
    # -------------------------------------------------------
    ai_connectors_structural = ["首先，", "其次，", "最后，", "首先,", "其次,", "最后,"]
    found_structural = [c for c in ai_connectors_structural if c in text]
    checks.append({
        "name": f"[{article_id}] No structural AI connectors (首先/其次/最后)",
        "passed": len(found_structural) == 0,
        "detail": f"Found structural connectors: {found_structural}" if found_structural else "Clean"
    })

    # -------------------------------------------------------
    # CHECK 2: Must NOT use formal AI connector words: 此外/然而/因此/综上所述
    # The skill has a specific replacement table for these
    # -------------------------------------------------------
    ai_connectors_formal = ["此外，", "然而，", "因此，", "综上所述，", "此外,", "然而,", "因此,", "综上所述,"]
    found_formal = [c for c in ai_connectors_formal if c in text]
    checks.append({
        "name": f"[{article_id}] No formal AI connectors (此外/然而/因此/综上所述)",
        "passed": len(found_formal) == 0,
        "detail": f"Found formal connectors: {found_formal}" if found_formal else "Clean"
    })

    # -------------------------------------------------------
    # CHECK 3: Must NOT use AI-flavored openings
    # The skill table specifies "在当今社会/随着.../众所周知" should be replaced
    # -------------------------------------------------------
    ai_openings = ["在当今", "随着", "众所周知"]
    found_openings = [o for o in ai_openings if o in text]
    checks.append({
        "name": f"[{article_id}] No AI-flavored openings (在当今/随着/众所周知)",
        "passed": len(found_openings) == 0,
        "detail": f"Found AI openings: {found_openings}" if found_openings else "Clean"
    })

    # -------------------------------------------------------
    # CHECK 4: Must NOT use AI closing phrases
    # The skill specifies "希望本文对您有所帮助"/"期待您的反馈"/"谢谢阅读" should be replaced
    # -------------------------------------------------------
    ai_closings = ["希望本文对您有所帮助", "期待您的反馈", "谢谢阅读"]
    found_closings = [c for c in ai_closings if c in text]
    checks.append({
        "name": f"[{article_id}] No AI closing phrases",
        "passed": len(found_closings) == 0,
        "detail": f"Found AI closings: {found_closings}" if found_closings else "Clean"
    })

    # -------------------------------------------------------
    # CHECK 5: Must contain emotion/colloquial words
    # Skill checklist: add "挺"、"真的"、"老实说" or similar
    # -------------------------------------------------------
    emotion_words = ["挺", "真的", "老实说", "说白了", "说实话", "讲道理", "对吧", "你懂的", "怎么说呢", "嗯", "其实", "说来"]
    found_emotions = [w for w in emotion_words if w in text]
    checks.append({
        "name": f"[{article_id}] Contains colloquial/emotion markers",
        "passed": len(found_emotions) >= 2,
        "detail": f"Found {len(found_emotions)} emotion markers: {found_emotions}" if found_emotions else "No emotion markers found"
    })

    # -------------------------------------------------------
    # CHECK 6: Must contain human-flavored connectors from the replacement table
    # e.g., "还有啊"/"对了"/"但问题是"/"可实际上"/"所以啊"/"这就导致"
    # -------------------------------------------------------
    human_connectors = ["还有啊", "对了", "但问题是", "可实际上", "所以啊", "这就导致", "还有个", "另外"]
    found_human = [c for c in human_connectors if c in text]
    checks.append({
        "name": f"[{article_id}] Contains human-flavored connectors from replacement table",
        "passed": len(found_human) >= 1,
        "detail": f"Found: {found_human}" if found_human else "No human connectors from skill table found"
    })

    # -------------------------------------------------------
    # CHECK 7: Must have sentence variety (short sentences present)
    # Skill: break uniform sentence lengths into mixed short/long
    # A short sentence is defined as <= 15 Chinese chars before punctuation
    # -------------------------------------------------------
    sentences = re.split(r'[。！？\n]', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    short_sentences = [s for s in sentences if 1 < len(s) <= 15]
    checks.append({
        "name": f"[{article_id}] Has short sentences (sentence rhythm variety)",
        "passed": len(short_sentences) >= 2,
        "detail": f"Found {len(short_sentences)} short sentences (<=15 chars). Examples: {short_sentences[:3]}"
    })

    # -------------------------------------------------------
    # CHECK 8: Must have personal/experiential language
    # Skill: "我之前也遇到过"/"我上次用的时候"/"我个人觉得"/"依我看"
    # -------------------------------------------------------
    personal_markers = ["我", "我上次", "我之前", "我个人", "我觉得", "我用", "我试", "我同时", "我分"]
    found_personal = [m for m in personal_markers if m in text]
    checks.append({
        "name": f"[{article_id}] Contains personal/experiential language (first-person)",
        "passed": len(found_personal) >= 1,
        "detail": f"Found first-person markers: {found_personal}" if found_personal else "No first-person language found"
    })

    # -------------------------------------------------------
    # CHECK 9: Must NOT contain "本文" (very AI-flavored)
    # -------------------------------------------------------
    checks.append({
        "name": f"[{article_id}] No '本文' (AI-flavored self-reference)",
        "passed": "本文" not in text,
        "detail": "Contains '本文'" if "本文" in text else "Clean"
    })

    # -------------------------------------------------------
    # CHECK 10: Text must be substantially different from original
    # At least 40% of the original AI phrases should be gone
    # -------------------------------------------------------
    original_ai_phrases = [
        "首先，", "其次，", "最后，", "此外，", "然而，", "综上所述，",
        "在当今", "众所周知", "希望本文", "期待您的反馈", "谢谢阅读",
        "本文将从三个方面", "本文将全面", "本评测将从三个维度"
    ]
    remaining = sum(1 for p in original_ai_phrases if p in text)
    checks.append({
        "name": f"[{article_id}] Text substantially transformed (most AI phrases removed)",
        "passed": remaining <= 1,
        "detail": f"{remaining} original AI phrases still present out of {len(original_ai_phrases)} checked"
    })

    return checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    all_checks = []

    # Expected output files (humanized versions)
    expected_outputs = {
        "productivity_tool_review_humanized.txt": "productivity tool review",
        "wireless_earbuds_review_humanized.txt": "wireless earbuds review",
        "notes_app_review_humanized.txt": "notes app review",
    }

    files_found = {}
    for filename in expected_outputs:
        matches = list(Path(workspace).rglob(filename))
        if matches:
            files_found[filename] = matches[0]
        else:
            files_found[filename] = None

    for filename, article_name in expected_outputs.items():
        fpath = files_found[filename]
        if fpath is None:
            all_checks.append({
                "name": f"File exists: {filename}",
                "passed": False,
                "detail": f"File '{filename}' not found anywhere in workspace"
            })
            # Add placeholder fails for all sub-checks
            for i in range(10):
                all_checks.append({
                    "name": f"[{article_name}] Check {i+1} (file missing)",
                    "passed": False,
                    "detail": "Cannot evaluate: file not found"
                })
            continue

        all_checks.append({
            "name": f"File exists: {filename}",
            "passed": True,
            "detail": f"Found at {fpath}"
        })

        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()

            if len(content.strip()) < 50:
                all_checks.append({
                    "name": f"[{article_name}] File has substantial content",
                    "passed": False,
                    "detail": f"File content too short: {len(content)} chars"
                })
                continue

            all_checks.append({
                "name": f"[{article_name}] File has substantial content",
                "passed": True,
                "detail": f"Content length: {len(content)} chars"
            })

            article_checks = check_text(content, article_name)
            all_checks.extend(article_checks)

        except Exception as e:
            all_checks.append({
                "name": f"[{article_name}] File readable",
                "passed": False,
                "detail": f"Error reading file: {str(e)}"
            })

    total = len(all_checks)
    passed_count = sum(1 for c in all_checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    overall_passed = score >= 0.75

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": all_checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()