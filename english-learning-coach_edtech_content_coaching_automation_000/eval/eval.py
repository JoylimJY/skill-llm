import sys
import json
import os
import re
from pathlib import Path

workspace = sys.argv[1]

checks = []
total_score = 0.0
max_score = 0.0


def make_check(name, passed, detail, weight=1.0):
    return {"name": name, "passed": passed, "detail": detail, "_weight": weight}


def load_json_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_report(pattern_variants):
    """Search workspace recursively for a file matching any of the given name patterns."""
    for variant in pattern_variants:
        results = list(Path(workspace).rglob(variant))
        if results:
            return results[0]
    return None


# =========================================================
# REPORT 1: S101 IELTS Task 2 Essay Coaching Report
# =========================================================

s101_file = find_report([
    "student_101_coaching_report.json",
    "S101_coaching_report.json",
    "s101_report.json",
    "s101_coaching_report.json",
    "student_101_report.json",
])

max_score += 4.0

if s101_file is None:
    checks.append(make_check(
        "S101_report_exists",
        False,
        "Could not find any coaching report JSON file for student S101.",
        weight=4.0
    ))
else:
    checks.append(make_check("S101_report_exists", True, f"Found: {s101_file}", weight=0))
    try:
        s101 = load_json_file(s101_file)

        # Check 1: Must have a numeric rating field (1-10 scale per SKILL.md writing coach prompt)
        rating_found = False
        rating_value = None
        for key in ["rating", "score", "writing_score", "rate"]:
            if key in s101:
                try:
                    rating_value = float(s101[key])
                    rating_found = True
                    break
                except (TypeError, ValueError):
                    pass
        # Also check nested
        if not rating_found:
            def search_for_rating(obj):
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        if any(x in k.lower() for x in ["rating", "score", "rate"]):
                            try:
                                return float(v)
                            except (TypeError, ValueError):
                                pass
                        result = search_for_rating(v)
                        if result is not None:
                            return result
                elif isinstance(obj, list):
                    for item in obj:
                        result = search_for_rating(item)
                        if result is not None:
                            return result
                return None
            rating_value = search_for_rating(s101)
            if rating_value is not None:
                rating_found = True

        if rating_found and rating_value is not None and 1.0 <= rating_value <= 10.0:
            checks.append(make_check("S101_has_1_to_10_rating", True,
                f"Rating found: {rating_value} (within 1-10 scale per SKILL.md writing coach prompt)", weight=1.0))
            total_score += 1.0
        else:
            checks.append(make_check("S101_has_1_to_10_rating", False,
                f"No valid 1-10 rating found. rating_found={rating_found}, value={rating_value}. SKILL.md writing coach prompt requires 'Rate my writing (1-10)'.", weight=1.0))

        # Check 2: Must flag grammar errors (SKILL.md: "Correct grammar errors")
        report_str = json.dumps(s101).lower()
        grammar_keywords = ["grammar", "grammatical", "error", "mistake", "incorrect", "correction"]
        has_grammar = any(kw in report_str for kw in grammar_keywords)
        if has_grammar:
            checks.append(make_check("S101_flags_grammar_errors", True,
                "Report contains grammar error correction content per SKILL.md.", weight=1.0))
            total_score += 1.0
        else:
            checks.append(make_check("S101_flags_grammar_errors", False,
                "No grammar error discussion found. SKILL.md writing coach: 'Correct grammar errors'.", weight=1.0))

        # Check 3: Must reference essay structure (intro/body/conclusion per SKILL.md argumentative essay template)
        structure_keywords = ["introduction", "body", "conclusion", "thesis", "topic sentence",
                              "hook", "intro", "supporting", "restate"]
        has_structure = any(kw in report_str for kw in structure_keywords)
        if has_structure:
            checks.append(make_check("S101_references_essay_structure", True,
                "Report references essay structure elements (intro/body/conclusion/thesis) per SKILL.md template.", weight=1.0))
            total_score += 1.0
        else:
            checks.append(make_check("S101_references_essay_structure", False,
                "No essay structure feedback found. SKILL.md specifies Introduction/Body/Conclusion template with Hook, Thesis, Topic Sentence etc.", weight=1.0))

        # Check 4: Must flag or note word count issue (essay is under 250 words; SKILL.md: Task 2: 250+ words)
        wordcount_keywords = ["250", "word count", "words", "length", "insufficient", "short", "minimum"]
        has_wordcount = any(kw in report_str for kw in wordcount_keywords)
        if has_wordcount:
            checks.append(make_check("S101_flags_word_count_requirement", True,
                "Report mentions 250+ word requirement per SKILL.md IELTS Task 2 spec.", weight=1.0))
            total_score += 1.0
        else:
            checks.append(make_check("S101_flags_word_count_requirement", False,
                "No mention of 250+ word requirement. SKILL.md IELTS: 'Task 2: 议论文, 250+ 字'.", weight=1.0))

    except Exception as e:
        checks.append(make_check("S101_report_parseable", False,
            f"Error parsing S101 report: {e}", weight=4.0))


# =========================================================
# REPORT 2: S102 Business Email Coaching Report
# =========================================================

s102_file = find_report([
    "student_102_coaching_report.json",
    "S102_coaching_report.json",
    "s102_report.json",
    "s102_coaching_report.json",
    "student_102_report.json",
])

max_score += 4.0

if s102_file is None:
    checks.append(make_check(
        "S102_report_exists",
        False,
        "Could not find coaching report JSON file for student S102.",
        weight=4.0
    ))
else:
    checks.append(make_check("S102_report_exists", True, f"Found: {s102_file}", weight=0))
    try:
        s102 = load_json_file(s102_file)
        report_str = json.dumps(s102).lower()

        # Check 5: Must have a 1-10 rating
        rating_value = None
        for key in ["rating", "score", "writing_score", "rate"]:
            if key in s102:
                try:
                    rating_value = float(s102[key])
                    break
                except (TypeError, ValueError):
                    pass
        if rating_value is None:
            def search_for_rating2(obj):
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        if any(x in k.lower() for x in ["rating", "score", "rate"]):
                            try:
                                return float(v)
                            except (TypeError, ValueError):
                                pass
                        result = search_for_rating2(v)
                        if result is not None:
                            return result
                elif isinstance(obj, list):
                    for item in obj:
                        result = search_for_rating2(item)
                        if result is not None:
                            return result
                return None
            rating_value = search_for_rating2(s102)

        if rating_value is not None and 1.0 <= rating_value <= 10.0:
            checks.append(make_check("S102_has_1_to_10_rating", True,
                f"Rating: {rating_value}", weight=1.0))
            total_score += 1.0
        else:
            checks.append(make_check("S102_has_1_to_10_rating", False,
                "No valid 1-10 rating. SKILL.md writing coach: 'Rate my writing (1-10)'.", weight=1.0))

        # Check 6: Email structure check - must reference email template fields (Subject, Dear, body, sign-off)
        email_structure_keywords = ["subject", "dear", "regards", "best regards", "sign", "greeting",
                                    "salutation", "closing", "opening", "purpose", "clear"]
        has_email_struct = any(kw in report_str for kw in email_structure_keywords)
        if has_email_struct:
            checks.append(make_check("S102_references_email_structure", True,
                "Report references email structural elements per SKILL.md email template.", weight=1.0))
            total_score += 1.0
        else:
            checks.append(make_check("S102_references_email_structure", False,
                "No email structure elements found. SKILL.md email template: Subject, Dear [name], opening purpose, body points, closing, Best regards.", weight=1.0))

        # Check 7: Must suggest more natural expressions (SKILL.md: "Suggest more natural expressions")
        natural_expr_keywords = ["natural", "expression", "suggest", "alternative", "better phrasing",
                                 "more natural", "idiomatic", "rephrase", "phrase"]
        has_natural = any(kw in report_str for kw in natural_expr_keywords)
        if has_natural:
            checks.append(make_check("S102_suggests_natural_expressions", True,
                "Report suggests more natural expressions per SKILL.md writing coach template.", weight=1.0))
            total_score += 1.0
        else:
            checks.append(make_check("S102_suggests_natural_expressions", False,
                "No natural expression suggestions found. SKILL.md: 'Suggest more natural expressions'.", weight=1.0))

        # Check 8: Must identify grammar errors in the email (several present in the input)
        grammar_keywords2 = ["grammar", "grammatical", "error", "mistake", "incorrect", "correction", "tense", "asking"]
        has_grammar2 = any(kw in report_str for kw in grammar_keywords2)
        if has_grammar2:
            checks.append(make_check("S102_corrects_grammar", True,
                "Report addresses grammar correction.", weight=1.0))
            total_score += 1.0
        else:
            checks.append(make_check("S102_corrects_grammar", False,
                "No grammar corrections. SKILL.md writing coach: 'Correct grammar errors'.", weight=1.0))

    except Exception as e:
        checks.append(make_check("S102_report_parseable", False,
            f"Error parsing S102 report: {e}", weight=4.0))


# =========================================================
# REPORT 3: SQ3R Reading Analysis
# =========================================================

sqr3_file = find_report([
    "renewable_energy_sqr3_analysis.json",
    "renewable_energy_sq3r_analysis.json",
    "sqr3_analysis.json",
    "sq3r_analysis.json",
    "reading_analysis.json",
    "sqr3_renewable.json",
    "sq3r_renewable.json",
    "renewable_energy_reading_analysis.json",
    "reading_sqr3_report.json",
    "sqr3_report.json",
])

max_score += 5.0

if sqr3_file is None:
    checks.append(make_check(
        "SQ3R_report_exists",
        False,
        "Could not find SQ3R analysis JSON file for the renewable energy article.",
        weight=5.0
    ))
else:
    checks.append(make_check("SQ3R_report_exists", True, f"Found: {sqr3_file}", weight=0))
    try:
        sq3r = load_json_file(sqr3_file)
        report_str = json.dumps(sq3r).lower()

        # Check 9: Must have Survey step (SKILL.md SQ3R: Survey - 浏览：看标题、小标题、首尾段)
        survey_keywords = ["survey", "browse", "skim", "overview", "title", "heading", "subheading"]
        has_survey = any(kw in report_str for kw in survey_keywords)
        if has_survey:
            checks.append(make_check("SQ3R_has_Survey_step", True,
                "Survey step found in SQ3R analysis.", weight=1.0))
            total_score += 1.0
        else:
            checks.append(make_check("SQ3R_has_Survey_step", False,
                "Survey step missing. SKILL.md SQ3R: 'Survey（浏览）：看标题、小标题、首尾段'.", weight=1.0))

        # Check 10: Must have Question step (SKILL.md: Question - 提问：这篇文章要回答什么问题？)
        question_keywords = ["question", "what does", "what is", "asks", "topic question", "inquiry"]
        has_question = any(kw in report_str for kw in question_keywords)
        if has_question:
            checks.append(make_check("SQ3R_has_Question_step", True,
                "Question step found.", weight=1.0))
            total_score += 1.0
        else:
            checks.append(make_check("SQ3R_has_Question_step", False,
                "Question step missing. SKILL.md SQ3R: 'Question（提问）：这篇文章要回答什么问题？'", weight=1.0))

        # Check 11: Must have Read step
        read_keywords = ["read", "reading", "content", "main", "detail", "section", "passage"]
        has_read = any(kw in report_str for kw in read_keywords)
        if has_read:
            checks.append(make_check("SQ3R_has_Read_step", True,
                "Read step found.", weight=1.0))
            total_score += 1.0
        else:
            checks.append(make_check("SQ3R_has_Read_step", False,
                "Read step missing. SKILL.md SQ3R: 'Read（阅读）：带着问题阅读'", weight=1.0))

        # Check 12: Must have Recite step (SKILL.md: Recite - 复述：用自己的话总结)
        recite_keywords = ["recite", "summary", "summarize", "own words", "retell", "paraphrase"]
        has_recite = any(kw in report_str for kw in recite_keywords)
        if has_recite:
            checks.append(make_check("SQ3R_has_Recite_step", True,
                "Recite step found.", weight=1.0))
            total_score += 1.0
        else:
            checks.append(make_check("SQ3R_has_Recite_step", False,
                "Recite step missing. SKILL.md SQ3R: 'Recite（复述）：用自己的话总结'", weight=1.0))

        # Check 13: Must have Review step (SKILL.md: Review - 复习：回顾关键点)
        review_keywords = ["review", "key point", "revisit", "recap", "takeaway", "conclusion", "reflect"]
        has_review = any(kw in report_str for kw in review_keywords)
        if has_review:
            checks.append(make_check("SQ3R_has_Review_step", True,
                "Review step found.", weight=1.0))
            total_score += 1.0
        else:
            checks.append(make_check("SQ3R_has_Review_step", False,
                "Review step missing. SKILL.md SQ3R: 'Review（复习）：回顾关键点'", weight=1.0))

    except Exception as e:
        checks.append(make_check("SQ3R_report_parseable", False,
            f"Error parsing SQ3R report: {e}", weight=5.0))


# =========================================================
# FINAL SCORING
# =========================================================

final_score = round(total_score / max_score, 4) if max_score > 0 else 0.0
overall_passed = final_score >= 0.75

# Remove internal weight field from output
output_checks = [
    {"name": c["name"], "passed": c["passed"], "detail": c["detail"]}
    for c in checks if c["name"] not in ("S101_report_exists", "S102_report_exists", "SQ3R_report_exists")
       or not c["passed"]
]
# Always include existence checks
existence_checks = [
    {"name": c["name"], "passed": c["passed"], "detail": c["detail"]}
    for c in checks
    if c["name"] in ("S101_report_exists", "S102_report_exists", "SQ3R_report_exists")
]

all_output_checks = existence_checks + [
    {"name": c["name"], "passed": c["passed"], "detail": c["detail"]}
    for c in checks
    if c["name"] not in ("S101_report_exists", "S102_report_exists", "SQ3R_report_exists")
]

print(json.dumps({
    "passed": overall_passed,
    "score": final_score,
    "checks": all_output_checks
}, indent=2))