import sys
import json
import os
from pathlib import Path

workspace = Path(sys.argv[1])

checks = []
total_score = 0.0
max_score = 5

def check(name, condition, detail, weight=1.0):
    checks.append({"name": name, "passed": bool(condition), "detail": detail})
    return weight if condition else 0.0

score = 0.0

# -----------------------------------------------------------------------
# CHECK 1: JSON output file exists in campaigns/q3_tech_client/assets/
# The agent must have used: python scripts/repurpose.py file raw_content/agentic_ai_enterprise.txt
#   --formats twitter,linkedin -f json -o campaigns/q3_tech_client/assets/
# -----------------------------------------------------------------------
json_candidates = list(workspace.rglob("repurposed.json"))
json_in_right_dir = [
    p for p in json_candidates
    if "q3_tech_client" in str(p) or "assets" in str(p)
]

json_file = None
# Accept any repurposed.json
if json_in_right_dir:
    json_file = json_in_right_dir[0]
elif json_candidates:
    json_file = json_candidates[0]

json_exists = json_file is not None
score += check(
    "repurposed_json_exists",
    json_exists,
    f"Found repurposed.json at: {json_file}" if json_exists else "No repurposed.json found anywhere in workspace."
)

# -----------------------------------------------------------------------
# CHECK 2: JSON contains ONLY twitter and linkedin keys (--formats twitter,linkedin)
# -----------------------------------------------------------------------
json_correct_formats = False
json_content = {}
if json_exists:
    try:
        with open(json_file, "r") as f:
            json_content = json.load(f)
        keys = set(json_content.keys())
        # Must have twitter and linkedin, must NOT have instagram/email/summary
        has_both = "twitter" in keys and "linkedin" in keys
        no_extras = not (keys - {"twitter", "linkedin"})
        json_correct_formats = has_both and no_extras
        score += check(
            "json_only_twitter_linkedin",
            json_correct_formats,
            f"JSON keys: {sorted(keys)}. Expected exactly {{'twitter','linkedin'}}."
        )
    except Exception as e:
        checks.append({"name": "json_only_twitter_linkedin", "passed": False, "detail": f"Failed to parse JSON: {e}"})
else:
    checks.append({"name": "json_only_twitter_linkedin", "passed": False, "detail": "JSON file not found, skipping content check."})

# -----------------------------------------------------------------------
# CHECK 3: Twitter content respects ≤280 chars per tweet AND 5-8 tweets
# -----------------------------------------------------------------------
twitter_valid = False
if json_correct_formats and "twitter" in json_content:
    try:
        tweets = json_content["twitter"]
        if isinstance(tweets, list):
            all_within_limit = all(len(t) <= 280 for t in tweets)
            count_ok = 5 <= len(tweets) <= 8
            twitter_valid = all_within_limit and count_ok
            detail = (
                f"Tweet count: {len(tweets)} (need 5-8). "
                f"All ≤280 chars: {all_within_limit}. "
                f"Lengths: {[len(t) for t in tweets]}"
            )
        else:
            detail = f"Twitter content is not a list: {type(tweets)}"
        score += check("twitter_format_valid", twitter_valid, detail)
    except Exception as e:
        checks.append({"name": "twitter_format_valid", "passed": False, "detail": f"Error: {e}"})
else:
    checks.append({"name": "twitter_format_valid", "passed": False, "detail": "Skipped: JSON missing or twitter key absent."})

# -----------------------------------------------------------------------
# CHECK 4: LinkedIn content ≤1300 chars
# -----------------------------------------------------------------------
linkedin_valid = False
if json_correct_formats and "linkedin" in json_content:
    try:
        linkedin = json_content["linkedin"]
        if isinstance(linkedin, str):
            linkedin_valid = len(linkedin) <= 1300
            detail = f"LinkedIn length: {len(linkedin)} chars (limit: 1300)."
        else:
            detail = f"LinkedIn content is not a string: {type(linkedin)}"
        score += check("linkedin_format_valid", linkedin_valid, detail)
    except Exception as e:
        checks.append({"name": "linkedin_format_valid", "passed": False, "detail": f"Error: {e}"})
else:
    checks.append({"name": "linkedin_format_valid", "passed": False, "detail": "Skipped: JSON missing or linkedin key absent."})

# -----------------------------------------------------------------------
# CHECK 5: Summary file for the health article (summary.txt) exists
# The agent must have used stdin or file mode with --formats summary
# for the sleep/performance article.
# -----------------------------------------------------------------------
summary_candidates = list(workspace.rglob("summary.txt"))
# Also accept a JSON with summary key from a separate run
summary_json_candidates = [
    p for p in workspace.rglob("*.json")
    if p != json_file
]

summary_file = None
summary_content = ""
if summary_candidates:
    summary_file = summary_candidates[0]
    try:
        with open(summary_file, "r") as f:
            summary_content = f.read().strip()
    except Exception:
        pass

# If not found as .txt, check any other json that has 'summary' key
if not summary_file:
    for p in summary_json_candidates:
        try:
            with open(p) as f:
                data = json.load(f)
            if "summary" in data:
                summary_content = data["summary"]
                summary_file = p
                break
        except Exception:
            pass

# Also check stdout capture — not possible here, so check any txt named summary
summary_exists = bool(summary_file) and bool(summary_content)

# Validate: summary content should relate to sleep/health topic 
# (contain at least one keyword from that domain)
sleep_keywords = ["sleep", "Sleep", "cognitive", "REM", "performance", "circadian", "melatonin", "cortisol", "glymphatic", "memory"]
summary_relevant = False
if summary_content:
    summary_relevant = any(kw.lower() in summary_content.lower() for kw in sleep_keywords)

summary_ok = summary_exists and summary_relevant
score += check(
    "summary_for_health_article",
    summary_ok,
    f"Summary file: {summary_file}. Content snippet: '{summary_content[:200]}'. "
    f"Contains sleep/health keywords: {summary_relevant}."
)

# -----------------------------------------------------------------------
# Final scoring
# -----------------------------------------------------------------------
final_score = round(score / max_score, 2)
passed = score >= 4.0  # Must pass at least 4/5 checks

result = {
    "passed": passed,
    "score": final_score,
    "checks": checks
}

print(json.dumps(result, indent=2))