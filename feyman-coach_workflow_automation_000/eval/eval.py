import sys
import json
import re
from pathlib import Path

def load_toml_manually(content: str) -> dict:
    """Minimal TOML section parser for our use case."""
    try:
        import toml
        return toml.loads(content)
    except ImportError:
        pass
    # fallback: basic parser
    result = {}
    current_section = None
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        section_match = re.match(r'^\[([^\]]+)\]$', line)
        if section_match:
            current_section = section_match.group(1)
            result[current_section] = {}
            continue
        kv_match = re.match(r'^(\w+)\s*=\s*(.+)$', line)
        if kv_match and current_section:
            key = kv_match.group(1)
            val_str = kv_match.group(2).strip().rstrip(' #').rstrip()
            # Remove inline comment
            # Handle string
            if val_str.startswith('"') and '"' in val_str[1:]:
                val = val_str.strip('"').split('"')[0]
            elif val_str.startswith("'"):
                val = val_str.strip("'")
            elif val_str.lower() == 'true':
                val = True
            elif val_str.lower() == 'false':
                val = False
            elif val_str.startswith('['):
                # array
                inner = val_str.strip('[]')
                items = [x.strip().strip('"').strip("'") for x in inner.split(',') if x.strip()]
                val = items
            else:
                try:
                    val = int(val_str)
                except:
                    try:
                        val = float(val_str)
                    except:
                        val = val_str
            result[current_section][key] = val
    return result

def run_checks(workspace: Path):
    checks = []
    total_score = 0.0
    max_score = 0.0

    # =========================================================
    # CHECK 1: .opencode/config.toml exists and has [feynman-coach] section
    # =========================================================
    max_score += 1.0
    config_toml_path = workspace / ".opencode" / "config.toml"
    try:
        content = config_toml_path.read_text(encoding="utf-8")
        parsed = load_toml_manually(content)
        
        # Check section name (must be "feynman-coach" with hyphen)
        section_key = None
        for k in parsed:
            if k.lower() == "feynman-coach":
                section_key = k
                break
        
        if section_key is None:
            checks.append({
                "name": "config.toml: [feynman-coach] section exists",
                "passed": False,
                "detail": f"Section [feynman-coach] not found. Found sections: {list(parsed.keys())}"
            })
        else:
            checks.append({
                "name": "config.toml: [feynman-coach] section exists",
                "passed": True,
                "detail": f"Found section [{section_key}]"
            })
            total_score += 1.0
    except Exception as e:
        checks.append({
            "name": "config.toml: [feynman-coach] section exists",
            "passed": False,
            "detail": f"Error reading config.toml: {e}"
        })
        parsed = {}
        section_key = None

    # =========================================================
    # CHECK 2: config.toml - review_time = "08:30"
    # =========================================================
    max_score += 1.0
    try:
        section = parsed.get("feynman-coach", {})
        review_time = section.get("review_time", "")
        passed = review_time == "08:30"
        checks.append({
            "name": "config.toml: review_time = \"08:30\"",
            "passed": passed,
            "detail": f"review_time = {repr(review_time)}"
        })
        if passed:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "config.toml: review_time", "passed": False, "detail": str(e)})

    # =========================================================
    # CHECK 3: config.toml - days_between_reviews = 2
    # =========================================================
    max_score += 1.0
    try:
        section = parsed.get("feynman-coach", {})
        dbr = section.get("days_between_reviews", None)
        passed = dbr == 2
        checks.append({
            "name": "config.toml: days_between_reviews = 2",
            "passed": passed,
            "detail": f"days_between_reviews = {repr(dbr)}"
        })
        if passed:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "config.toml: days_between_reviews", "passed": False, "detail": str(e)})

    # =========================================================
    # CHECK 4: config.toml - review_scope = "tagged"
    # =========================================================
    max_score += 1.0
    try:
        section = parsed.get("feynman-coach", {})
        scope = section.get("review_scope", "")
        passed = scope == "tagged"
        checks.append({
            "name": "config.toml: review_scope = \"tagged\"",
            "passed": passed,
            "detail": f"review_scope = {repr(scope)}"
        })
        if passed:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "config.toml: review_scope", "passed": False, "detail": str(e)})

    # =========================================================
    # CHECK 5: config.toml - review_tags contains "#ML" and "#考试重点"
    # =========================================================
    max_score += 1.0
    try:
        section = parsed.get("feynman-coach", {})
        tags = section.get("review_tags", [])
        # Also try raw content parsing for TOML arrays
        if not tags:
            raw_match = re.search(r'review_tags\s*=\s*\[([^\]]*)\]', content if 'content' in dir() else "")
            if raw_match:
                inner = raw_match.group(1)
                tags = [x.strip().strip('"').strip("'") for x in inner.split(',') if x.strip()]
        has_ml = "#ML" in tags
        has_exam = "#考试重点" in tags
        passed = has_ml and has_exam
        checks.append({
            "name": "config.toml: review_tags contains [\"#ML\", \"#考试重点\"]",
            "passed": passed,
            "detail": f"review_tags = {tags}, has #ML: {has_ml}, has #考试重点: {has_exam}"
        })
        if passed:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "config.toml: review_tags", "passed": False, "detail": str(e)})

    # =========================================================
    # CHECK 6: config.toml - max_daily_concepts = 5
    # =========================================================
    max_score += 1.0
    try:
        section = parsed.get("feynman-coach", {})
        mdc = section.get("max_daily_concepts", None)
        passed = mdc == 5
        checks.append({
            "name": "config.toml: max_daily_concepts = 5",
            "passed": passed,
            "detail": f"max_daily_concepts = {repr(mdc)}"
        })
        if passed:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "config.toml: max_daily_concepts", "passed": False, "detail": str(e)})

    # =========================================================
    # CHECK 7: config.json exists in skills/feynman-coach/ directory
    # =========================================================
    max_score += 1.0
    config_json_path = workspace / "skills" / "feynman-coach" / "config.json"
    try:
        cj_content = config_json_path.read_text(encoding="utf-8")
        cj = json.loads(cj_content)
        checks.append({
            "name": "config.json: file exists in skills/feynman-coach/",
            "passed": True,
            "detail": f"Found at {config_json_path}"
        })
        total_score += 1.0
    except FileNotFoundError:
        # Try rglob to give partial credit info
        found = list(workspace.rglob("config.json"))
        checks.append({
            "name": "config.json: file exists in skills/feynman-coach/",
            "passed": False,
            "detail": f"Not found at expected path. Other config.json files found: {[str(f) for f in found]}"
        })
        cj = {}
    except Exception as e:
        checks.append({
            "name": "config.json: file exists in skills/feynman-coach/",
            "passed": False,
            "detail": f"Error: {e}"
        })
        cj = {}

    # =========================================================
    # CHECK 8: config.json - scoring weights: clarity=0.25, accuracy=0.45, depth=0.20, examples=0.10
    # =========================================================
    max_score += 1.0
    try:
        scoring = cj.get("scoring", {})
        expected = {
            "clarity_weight": 0.25,
            "accuracy_weight": 0.45,
            "depth_weight": 0.20,
            "examples_weight": 0.10
        }
        mismatches = []
        for k, v in expected.items():
            actual = scoring.get(k)
            if actual is None or abs(float(actual) - v) > 0.001:
                mismatches.append(f"{k}: expected {v}, got {actual}")
        passed = len(mismatches) == 0
        checks.append({
            "name": "config.json: scoring weights (clarity=0.25, accuracy=0.45, depth=0.20, examples=0.10)",
            "passed": passed,
            "detail": f"Mismatches: {mismatches}" if mismatches else f"All weights correct: {scoring}"
        })
        if passed:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "config.json: scoring weights", "passed": False, "detail": str(e)})

    # =========================================================
    # CHECK 9: config.json - difficulty_levels structure (3 levels with depth+questions)
    # =========================================================
    max_score += 1.0
    try:
        dl = cj.get("difficulty_levels", {})
        required_levels = {
            "beginner": {"depth": "basic", "questions": 3},
            "intermediate": {"depth": "medium", "questions": 5},
            "advanced": {"depth": "deep", "questions": 7}
        }
        errors = []
        for level, expected_vals in required_levels.items():
            if level not in dl:
                errors.append(f"Missing level: {level}")
                continue
            for k, v in expected_vals.items():
                actual = dl[level].get(k)
                if actual != v:
                    errors.append(f"{level}.{k}: expected {v!r}, got {actual!r}")
        passed = len(errors) == 0
        checks.append({
            "name": "config.json: difficulty_levels (beginner/intermediate/advanced with correct depth+questions)",
            "passed": passed,
            "detail": f"Errors: {errors}" if errors else "All difficulty levels correct"
        })
        if passed:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "config.json: difficulty_levels", "passed": False, "detail": str(e)})

    # =========================================================
    # CHECK 10: Diagnostic report exists in Z_Utils/feynman-coach/history/ for 随机森林算法
    # =========================================================
    max_score += 1.0
    history_dir = workspace / "Z_Utils" / "feynman-coach" / "history"
    report_files = list(history_dir.glob("*.md")) + list(history_dir.glob("*.markdown"))
    
    report_content = None
    report_file = None
    for f in report_files:
        try:
            text = f.read_text(encoding="utf-8")
            if "随机森林" in text:
                report_content = text
                report_file = f
                break
        except:
            pass
    
    if report_content is None:
        checks.append({
            "name": "Diagnostic report: exists in Z_Utils/feynman-coach/history/ for 随机森林算法",
            "passed": False,
            "detail": f"No markdown file mentioning 随机森林 found in {history_dir}. Files found: {[f.name for f in report_files]}"
        })
    else:
        checks.append({
            "name": "Diagnostic report: exists in Z_Utils/feynman-coach/history/ for 随机森林算法",
            "passed": True,
            "detail": f"Found report at {report_file}"
        })
        total_score += 1.0

    # =========================================================
    # CHECK 11: Diagnostic report - contains required section headers and emoji markers
    # =========================================================
    max_score += 1.0
    try:
        if report_content is None:
            raise ValueError("No report content found")
        
        required_elements = [
            ("费曼学习诊断报告", "# 费曼学习诊断报告 heading"),
            ("随机森林", "topic 随机森林算法"),
            ("✅", "✅ emoji for good understanding section"),
            ("⚠️", "⚠️ emoji for needs improvement section"),
            ("❌", "❌ emoji for misunderstood section"),
            ("📊", "📊 emoji for assessment section"),
            ("/100", "score out of 100"),
        ]
        
        missing = []
        for pattern, desc in required_elements:
            if pattern not in report_content:
                missing.append(desc)
        
        passed = len(missing) == 0
        checks.append({
            "name": "Diagnostic report: contains required section headers and emoji markers (✅ ⚠️ ❌ 📊)",
            "passed": passed,
            "detail": f"Missing elements: {missing}" if missing else "All required elements present"
        })
        if passed:
            total_score += 1.0
    except Exception as e:
        checks.append({
            "name": "Diagnostic report: required sections/emojis",
            "passed": False,
            "detail": str(e)
        })

    # =========================================================
    # CHECK 12: Diagnostic report - contains 🎯 personalized suggestions and 📝 exercises sections
    # =========================================================
    max_score += 1.0
    try:
        if report_content is None:
            raise ValueError("No report content found")
        
        required = [
            ("🎯", "🎯 personalized learning suggestions"),
            ("📝", "📝 practice exercises"),
            ("🔗", "🔗 related knowledge links"),
            ("📅", "📅 next review recommendation"),
        ]
        missing = [desc for pat, desc in required if pat not in report_content]
        passed = len(missing) == 0
        checks.append({
            "name": "Diagnostic report: contains 🎯 📝 🔗 📅 sections",
            "passed": passed,
            "detail": f"Missing: {missing}" if missing else "All section emoji markers present"
        })
        if passed:
            total_score += 1.0
    except Exception as e:
        checks.append({
            "name": "Diagnostic report: 🎯📝🔗📅 sections",
            "passed": False,
            "detail": str(e)
        })

    # =========================================================
    # CHECK 13: Review cards file exists for 随机森林算法 with correct format
    # =========================================================
    max_score += 1.0
    
    # Search anywhere in workspace for a review cards file for random forest
    card_files = list(workspace.rglob("*.md"))
    cards_content = None
    cards_file = None
    
    for f in card_files:
        # Skip the diagnostic report itself and SKILL.md
        if "history" in str(f) or "SKILL.md" in str(f):
            continue
        try:
            text = f.read_text(encoding="utf-8")
            # Must mention 随机森林 AND have the card format markers
            if "随机森林" in text and ("**正面**" in text or "**背面**" in text):
                cards_content = text
                cards_file = f
                break
        except:
            pass
    
    if cards_content is None:
        checks.append({
            "name": "Review cards: file exists for 随机森林算法 with **正面**/**背面** format",
            "passed": False,
            "detail": "No review cards file found containing 随机森林 and **正面**/**背面** markers"
        })
    else:
        checks.append({
            "name": "Review cards: file exists for 随机森林算法 with **正面**/**背面** format",
            "passed": True,
            "detail": f"Found at {cards_file}"
        })
        total_score += 1.0

    # =========================================================
    # CHECK 14: Review cards - has at least 3 cards with correct structure
    # =========================================================
    max_score += 1.0
    try:
        if cards_content is None:
            raise ValueError("No cards file found")
        
        # Count 正面/背面 pairs
        front_count = cards_content.count("**正面**")
        back_count = cards_content.count("**背面**")
        has_title = "复习卡片" in cards_content
        has_cards_heading = re.search(r'##\s*卡片\s*\d+', cards_content) is not None
        
        passed = front_count >= 3 and back_count >= 3 and has_title
        checks.append({
            "name": "Review cards: at least 3 cards with 正面/背面 pairs and 复习卡片 title",
            "passed": passed,
            "detail": f"正面 count: {front_count}, 背面 count: {back_count}, has '复习卡片' title: {has_title}"
        })
        if passed:
            total_score += 1.0
    except Exception as e:
        checks.append({
            "name": "Review cards: card count and structure",
            "passed": False,
            "detail": str(e)
        })

    # =========================================================
    # Final scoring
    # =========================================================
    score = round(total_score / max_score, 4) if max_score > 0 else 0.0
    
    return {
        "passed": all(c["passed"] for c in checks),
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    
    workspace = Path(sys.argv[1])
    result = run_checks(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))