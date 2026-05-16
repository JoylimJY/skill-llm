#!/usr/bin/env python3
"""
Evaluation script for the near-content-creator skill task.
Checks three output files:
  1. validator_thread.json  — thread in 1/8...8/8 format, exactly 8 posts
  2. ecosystem_news.json    — list with url/link fields, ranked, deduplicated
  3. staking_tutorial.md   — structured markdown with practical commands
"""

import sys
import json
import re
from pathlib import Path

workspace = Path(sys.argv[1])

checks = []
total_score = 0.0
max_score = 9  # weighted check points


def find_file(name):
    """Search recursively for a file by name."""
    matches = list(workspace.rglob(name))
    return matches[0] if matches else None


# ─────────────────────────────────────────────────────────────────
# CHECK GROUP 1: validator_thread.json
# ─────────────────────────────────────────────────────────────────

thread_file = find_file("validator_thread.json")

# 1a: File exists
c1a = {"name": "validator_thread.json exists", "passed": False, "detail": ""}
if thread_file and thread_file.is_file():
    c1a["passed"] = True
    c1a["detail"] = f"Found at {thread_file}"
    total_score += 1
else:
    c1a["detail"] = "validator_thread.json not found anywhere in workspace"
checks.append(c1a)

# 1b: Is a JSON array of exactly 8 strings
c1b = {"name": "thread is JSON array of exactly 8 items", "passed": False, "detail": ""}
thread_data = None
if thread_file and thread_file.is_file():
    try:
        raw = thread_file.read_text(encoding="utf-8")
        thread_data = json.loads(raw)
        if isinstance(thread_data, list) and len(thread_data) == 8:
            c1b["passed"] = True
            c1b["detail"] = f"Array with {len(thread_data)} items"
            total_score += 1
        else:
            c1b["detail"] = f"Expected list of 8, got type={type(thread_data).__name__} len={len(thread_data) if isinstance(thread_data, list) else 'N/A'}"
    except Exception as e:
        c1b["detail"] = f"JSON parse error: {e}"
else:
    c1b["detail"] = "File not available"
checks.append(c1b)

# 1c: Posts follow stable 1/8 ... 8/8 numbering (proprietary trap)
c1c = {"name": "thread posts use 1/8...8/8 numbering format", "passed": False, "detail": ""}
if thread_data and isinstance(thread_data, list):
    try:
        all_correct = True
        wrong = []
        for i, post in enumerate(thread_data):
            expected_prefix = f"{i+1}/8"
            if not isinstance(post, str) or not post.strip().startswith(expected_prefix):
                all_correct = False
                wrong.append(f"Post {i+1}: got '{str(post)[:60]}', expected to start with '{expected_prefix}'")
        if all_correct:
            c1c["passed"] = True
            c1c["detail"] = "All 8 posts correctly numbered 1/8 through 8/8"
            total_score += 2  # double-weight: this is the proprietary trap
        else:
            c1c["detail"] = "Incorrect numbering: " + "; ".join(wrong[:3])
    except Exception as e:
        c1c["detail"] = f"Error checking format: {e}"
else:
    c1c["detail"] = "Thread data unavailable or wrong type"
checks.append(c1c)

# 1d: Thread is about validators (topic check)
c1d = {"name": "thread content is about NEAR validators", "passed": False, "detail": ""}
if thread_data and isinstance(thread_data, list):
    try:
        combined = " ".join(str(p) for p in thread_data).lower()
        validator_keywords = ["validator", "stake", "near", "network"]
        matched = [kw for kw in validator_keywords if kw in combined]
        if len(matched) >= 3:
            c1d["passed"] = True
            c1d["detail"] = f"Matched keywords: {matched}"
            total_score += 1
        else:
            c1d["detail"] = f"Only matched {matched} out of {validator_keywords}"
    except Exception as e:
        c1d["detail"] = f"Error: {e}"
else:
    c1d["detail"] = "Thread data unavailable"
checks.append(c1d)


# ─────────────────────────────────────────────────────────────────
# CHECK GROUP 2: ecosystem_news.json
# ─────────────────────────────────────────────────────────────────

news_file = find_file("ecosystem_news.json")

# 2a: File exists
c2a = {"name": "ecosystem_news.json exists", "passed": False, "detail": ""}
if news_file and news_file.is_file():
    c2a["passed"] = True
    c2a["detail"] = f"Found at {news_file}"
    total_score += 1
else:
    c2a["detail"] = "ecosystem_news.json not found anywhere in workspace"
checks.append(c2a)

# 2b: Is a JSON array with multiple items
c2b = {"name": "news is JSON array with >= 3 items", "passed": False, "detail": ""}
news_data = None
if news_file and news_file.is_file():
    try:
        raw = news_file.read_text(encoding="utf-8")
        news_data = json.loads(raw)
        if isinstance(news_data, list) and len(news_data) >= 3:
            c2b["passed"] = True
            c2b["detail"] = f"Array with {len(news_data)} items"
            total_score += 1
        else:
            c2b["detail"] = f"Expected list >=3, got type={type(news_data).__name__} len={len(news_data) if isinstance(news_data, list) else 'N/A'}"
    except Exception as e:
        c2b["detail"] = f"JSON parse error: {e}"
else:
    c2b["detail"] = "File not available"
checks.append(c2b)

# 2c: Items have URL/link fields and rank ordering (source ranking + links = proprietary constraint)
c2c = {"name": "news items contain url/link fields and rank/order", "passed": False, "detail": ""}
if news_data and isinstance(news_data, list):
    try:
        url_field_count = 0
        rank_field_count = 0
        for item in news_data:
            if isinstance(item, dict):
                if any(k in item for k in ("url", "link", "href")):
                    url_field_count += 1
                if any(k in item for k in ("rank", "priority", "order", "score")):
                    rank_field_count += 1
            elif isinstance(item, str):
                if re.search(r'https?://', item):
                    url_field_count += 1

        if url_field_count >= 3:
            c2c["passed"] = True
            c2c["detail"] = f"{url_field_count}/{len(news_data)} items have URLs, {rank_field_count} have rank fields"
            total_score += 1
        else:
            c2c["detail"] = f"Only {url_field_count}/{len(news_data)} items have URL fields — source links required by SKILL.md"
    except Exception as e:
        c2c["detail"] = f"Error: {e}"
else:
    c2c["detail"] = "News data unavailable or wrong type"
checks.append(c2c)


# ─────────────────────────────────────────────────────────────────
# CHECK GROUP 3: staking_tutorial.md
# ─────────────────────────────────────────────────────────────────

tutorial_file = find_file("staking_tutorial.md")

# 3a: File exists
c3a = {"name": "staking_tutorial.md exists", "passed": False, "detail": ""}
if tutorial_file and tutorial_file.is_file():
    c3a["passed"] = True
    c3a["detail"] = f"Found at {tutorial_file}"
    total_score += 1
else:
    c3a["detail"] = "staking_tutorial.md not found anywhere in workspace"
checks.append(c3a)

# 3b: Contains practical, executable content (code blocks with CLI commands — not generic copywriting)
c3b = {"name": "tutorial contains executable CLI code blocks (not generic copywriting)", "passed": False, "detail": ""}
if tutorial_file and tutorial_file.is_file():
    try:
        content = tutorial_file.read_text(encoding="utf-8")
        # Must have markdown code blocks
        code_block_count = len(re.findall(r'```', content))
        # Must contain NEAR CLI commands
        cli_patterns = [r'near\s+\w+', r'npm\s+install', r'near-cli', r'near login', r'near call', r'near view']
        cli_matches = [p for p in cli_patterns if re.search(p, content, re.IGNORECASE)]
        # Must have sections/headers
        header_count = len(re.findall(r'^#{1,3}\s+\w+', content, re.MULTILINE))

        if code_block_count >= 4 and len(cli_matches) >= 2 and header_count >= 3:
            c3b["passed"] = True
            c3b["detail"] = f"Code blocks: {code_block_count//2}, CLI patterns matched: {cli_matches}, Headers: {header_count}"
            total_score += 1
        else:
            c3b["detail"] = (
                f"Insufficient structure. Code block pairs: {code_block_count//2} (need>=2), "
                f"CLI patterns: {cli_matches} (need>=2), Headers: {header_count} (need>=3)"
            )
    except Exception as e:
        c3b["detail"] = f"Error reading tutorial: {e}"
else:
    c3b["detail"] = "File not available"
checks.append(c3b)

# 3c: Tutorial is about staking on NEAR
c3c = {"name": "tutorial content is about NEAR staking", "passed": False, "detail": ""}
if tutorial_file and tutorial_file.is_file():
    try:
        content = tutorial_file.read_text(encoding="utf-8").lower()
        staking_kws = ["stake", "near", "validator", "delegate", "epoch"]
        matched = [kw for kw in staking_kws if kw in content]
        if len(matched) >= 4:
            c3c["passed"] = True
            c3c["detail"] = f"Staking keywords found: {matched}"
            total_score += 1  # NOTE: included implicitly in weighted calc below
        else:
            c3c["detail"] = f"Only {len(matched)} staking keywords found: {matched}"
    except Exception as e:
        c3c["detail"] = f"Error: {e}"
else:
    c3c["detail"] = "File not available"
checks.append(c3c)


# ─────────────────────────────────────────────────────────────────
# Final scoring
# ─────────────────────────────────────────────────────────────────

# Possible total: 1+1+2+1+1+1+1+1+1+1 = 11 raw points, max_score cap = 9
# Normalise to 0.0 - 1.0
raw_max = 11.0
score = min(1.0, round(total_score / raw_max, 4))

passed = (
    checks[0]["passed"] and  # thread exists
    checks[2]["passed"] and  # 1/8...8/8 format (the key proprietary trap)
    checks[4]["passed"] and  # news exists
    checks[7]["passed"] and  # tutorial exists
    checks[8]["passed"]      # tutorial has executable CLI content
)

result = {
    "passed": passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2))