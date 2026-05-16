import sys
import json
import re
import csv
from pathlib import Path

workspace = Path(sys.argv[1])

results = []
total_score = 0.0

# -----------------------------------------------------------------------
# SKILL.md canonical regex (exact)
# -----------------------------------------------------------------------
CANONICAL_REGEX = (
    r"chatgpt\.com|openai\.com|openai|perplexity\.ai|perplexity|doubao\.com|"
    r"chat\.qwen\.ai|copilot\.microsoft\.com|copilot\.com|(business\.)?gemini\.google|"
    r"chat\.deepseek\.com|deepseek\.com|poe\.com|anthropic\.com|claude\.ai|"
    r"bard\.google\.com|edgeservices\.bing\.com"
)
canonical_pattern = re.compile(CANONICAL_REGEX, re.IGNORECASE)

def check(name, passed, detail):
    results.append({"name": name, "passed": passed, "detail": detail})
    return passed

# -----------------------------------------------------------------------
# 1. Find channel_group config JSON
# -----------------------------------------------------------------------
channel_files = list(workspace.rglob("*.json"))
# Filter out the distractor old file
channel_files = [f for f in channel_files if "old_channel_group_v1" not in f.name]

channel_data = None
channel_file_path = None

for cf in channel_files:
    try:
        with open(cf) as fh:
            data = json.load(fh)
        # Heuristic: must have a "channels" list
        if "channels" in data and isinstance(data["channels"], list):
            channel_data = data
            channel_file_path = cf
            break
    except Exception:
        continue

if channel_data is None:
    # Try to find any json with channel-like structure
    for cf in channel_files:
        try:
            with open(cf) as fh:
                data = json.load(fh)
            channel_data = data
            channel_file_path = cf
            break
        except Exception:
            continue

check(
    "channel_group_file_exists",
    channel_data is not None,
    f"Found channel group JSON at {channel_file_path}" if channel_data else "No valid channel group JSON found"
)

# -----------------------------------------------------------------------
# 2. Channel group contains AI Chatbots channel
# -----------------------------------------------------------------------
ai_channel = None
referral_channel = None

if channel_data:
    channels = channel_data.get("channels", [])
    for ch in channels:
        name_lower = ch.get("name", "").lower()
        if "ai" in name_lower and ("chatbot" in name_lower or "chat" in name_lower or "ai" in name_lower):
            ai_channel = ch
        if "referral" in name_lower:
            referral_channel = ch

check(
    "ai_chatbots_channel_exists",
    ai_channel is not None,
    f"AI Chatbots channel found: {ai_channel}" if ai_channel else "No AI Chatbots channel found in channel group"
)

# -----------------------------------------------------------------------
# 3. AI Chatbots channel has a regex filter
# -----------------------------------------------------------------------
ai_regex_str = None
if ai_channel:
    # Look for regex in any string field
    for key, val in ai_channel.items():
        if isinstance(val, str) and len(val) > 20 and ("chatgpt" in val.lower() or "perplexity" in val.lower() or "claude" in val.lower()):
            ai_regex_str = val
            break
    # Also check nested dicts
    if ai_regex_str is None:
        raw = json.dumps(ai_channel)
        if "chatgpt" in raw.lower():
            # Extract any regex-looking string
            m = re.search(r'"([^"]*chatgpt[^"]*)"', raw)
            if m:
                ai_regex_str = m.group(1)

check(
    "ai_channel_has_regex",
    ai_regex_str is not None,
    f"Regex found in AI channel: {ai_regex_str[:80] if ai_regex_str else 'N/A'}..."
)

# -----------------------------------------------------------------------
# 4. AI Chatbots channel appears BEFORE Referral channel (ordering trap)
# -----------------------------------------------------------------------
ai_index = None
referral_index = None

if channel_data:
    channels = channel_data.get("channels", [])
    for i, ch in enumerate(channels):
        name_lower = ch.get("name", "").lower()
        if ai_index is None and ("ai" in name_lower):
            ai_index = i
        if referral_index is None and "referral" in name_lower:
            referral_index = i

ordering_ok = (ai_index is not None and referral_index is not None and ai_index < referral_index)
check(
    "ai_channel_before_referral",
    ordering_ok,
    f"AI channel index={ai_index}, Referral channel index={referral_index}. AI must come first." if not ordering_ok
    else f"Correct: AI Chatbots (idx {ai_index}) is before Referral (idx {referral_index})"
)

# -----------------------------------------------------------------------
# 5. Regex covers non-obvious sources: edgeservices.bing.com, doubao.com, chat.qwen.ai
# -----------------------------------------------------------------------
regex_covers_edge = False
regex_covers_doubao = False
regex_covers_qwen = False

if ai_regex_str:
    try:
        pat = re.compile(ai_regex_str, re.IGNORECASE)
        regex_covers_edge = bool(pat.search("edgeservices.bing.com"))
        regex_covers_doubao = bool(pat.search("doubao.com"))
        regex_covers_qwen = bool(pat.search("chat.qwen.ai"))
    except re.error:
        pass

check(
    "regex_covers_edgeservices_bing",
    regex_covers_edge,
    "Regex correctly matches edgeservices.bing.com" if regex_covers_edge else "Regex does NOT match edgeservices.bing.com"
)
check(
    "regex_covers_doubao",
    regex_covers_doubao,
    "Regex correctly matches doubao.com" if regex_covers_doubao else "Regex does NOT match doubao.com"
)
check(
    "regex_covers_chat_qwen_ai",
    regex_covers_qwen,
    "Regex correctly matches chat.qwen.ai" if regex_covers_qwen else "Regex does NOT match chat.qwen.ai"
)

# -----------------------------------------------------------------------
# 6. Regex catches bare "openai" and bare "perplexity" tokens (non-obvious)
# -----------------------------------------------------------------------
regex_covers_bare_openai = False
regex_covers_bare_perplexity = False

if ai_regex_str:
    try:
        pat = re.compile(ai_regex_str, re.IGNORECASE)
        # Must match the bare token "openai" (GA4 reports it without .com sometimes)
        # but should not over-match "myopenai.com" ambiguously — we only care it matches "openai"
        regex_covers_bare_openai = bool(pat.search("openai"))
        regex_covers_bare_perplexity = bool(pat.search("perplexity"))
    except re.error:
        pass

check(
    "regex_covers_bare_openai_token",
    regex_covers_bare_openai,
    "Regex matches bare 'openai' source token" if regex_covers_bare_openai else "Regex does NOT match bare 'openai'"
)
check(
    "regex_covers_bare_perplexity_token",
    regex_covers_bare_perplexity,
    "Regex matches bare 'perplexity' source token" if regex_covers_bare_perplexity else "Regex does NOT match bare 'perplexity'"
)

# -----------------------------------------------------------------------
# 7. Find summary report JSON
# -----------------------------------------------------------------------
summary_files = list(workspace.rglob("*.json"))
summary_data = None
summary_path = None

for sf in summary_files:
    if sf == channel_file_path:
        continue
    try:
        with open(sf) as fh:
            data = json.load(fh)
        # Must have session totals or ai_sessions key
        raw = json.dumps(data).lower()
        if any(k in raw for k in ["ai_sessions", "ai_traffic", "total_ai", "ai_sources", "chatgpt", "perplexity"]):
            summary_data = data
            summary_path = sf
            break
    except Exception:
        continue

check(
    "summary_report_exists",
    summary_data is not None,
    f"Summary report found at {summary_path}" if summary_data else "No summary report JSON with AI traffic data found"
)

# -----------------------------------------------------------------------
# 8. Summary report correctly identifies AI vs non-AI sessions from the CSV
# -----------------------------------------------------------------------
# Ground truth: classify the CSV ourselves
csv_path = workspace / "analytics/exports/sessions/raw_sessions_april.csv"
total_sessions = 0
ai_sessions_gt = 0
non_ai_sessions_gt = 0
detected_ai_sources_gt = set()

try:
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            src = row["session_source"]
            total_sessions += 1
            if canonical_pattern.search(src):
                ai_sessions_gt += 1
                detected_ai_sources_gt.add(src)
            else:
                non_ai_sessions_gt += 1
except Exception as e:
    check("csv_ground_truth_computable", False, f"Could not read CSV: {e}")

# Tolerance: within 5%
summary_correct = False
if summary_data:
    raw = json.dumps(summary_data).lower()
    # Extract any integer that's close to ai_sessions_gt
    numbers = re.findall(r'\d+', raw)
    numbers = [int(n) for n in numbers]
    tol = max(5, int(ai_sessions_gt * 0.05))
    for n in numbers:
        if abs(n - ai_sessions_gt) <= tol:
            summary_correct = True
            break

check(
    "summary_ai_session_count_correct",
    summary_correct,
    f"Expected ~{ai_sessions_gt} AI sessions (±5%). Numbers found in summary: {numbers[:10] if summary_data else 'N/A'}"
)

# -----------------------------------------------------------------------
# 9. Summary lists detected AI source domains
# -----------------------------------------------------------------------
sources_listed = False
if summary_data:
    raw_summary = json.dumps(summary_data).lower()
    # Must mention at least 5 of the ground-truth AI sources
    mentioned = sum(1 for src in detected_ai_sources_gt if src.lower() in raw_summary)
    sources_listed = mentioned >= 5

check(
    "summary_lists_ai_sources",
    sources_listed,
    f"Summary mentions {mentioned if summary_data else 0} of {len(detected_ai_sources_gt)} detected AI sources (need ≥5)"
    if summary_data else "No summary found"
)

# -----------------------------------------------------------------------
# 10. No non-AI sources misclassified (spot check key non-AI domains)
# -----------------------------------------------------------------------
false_positive_check = True
false_positive_detail = "OK"

if ai_regex_str:
    try:
        pat = re.compile(ai_regex_str, re.IGNORECASE)
        non_ai_check = ["google", "(direct)", "facebook.com", "reddit.com", "amazon.com", "duckduckgo.com"]
        for src in non_ai_check:
            if pat.search(src):
                false_positive_check = False
                false_positive_detail = f"Regex incorrectly matches non-AI source: '{src}'"
                break
    except re.error as e:
        false_positive_check = False
        false_positive_detail = f"Regex compile error: {e}"

check(
    "no_false_positive_ai_classification",
    false_positive_check,
    false_positive_detail
)

# -----------------------------------------------------------------------
# Final scoring
# -----------------------------------------------------------------------
num_passed = sum(1 for r in results if r["passed"])
score = round(num_passed / len(results), 4)

output = {
    "passed": score >= 0.75,
    "score": score,
    "checks": results
}

print(json.dumps(output, indent=2))