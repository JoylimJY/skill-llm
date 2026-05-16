#!/usr/bin/env python3
"""
Evaluation script for the Feishu Writing Bundle task.
Checks:
1. The existing document was NOT overwritten (original blocks preserved)
2. New proposal content was appended (not inserted destructively)
3. The update used a non-destructive mode (append/insert_after, not overwrite)
4. Proposal content is formal (not chat-style)
5. The new section contains key information from the raw draft
6. The agent returned/recorded the document URL
7. The document title was not re-stated as H1 in the body
8. The new content is self-contained (has contextual intro)
"""

import sys
import json
import os
import re
from pathlib import Path

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"

checks = []
score_total = 0.0
score_max = 0.0


def check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    global score_total, score_max
    score_max += weight
    if passed:
        score_total += weight


# ── Load the final document state ───────────────────────────────────────────
doc_path = os.path.join(workspace, "mock_server_state", "doc_onboarding_2024.json")
try:
    with open(doc_path, "r", encoding="utf-8") as f:
        final_doc = json.load(f)
except Exception as e:
    check("document_state_readable", False, f"Could not read final doc state: {e}", weight=3.0)
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

final_blocks = final_doc.get("blocks", [])
final_title = final_doc.get("title", "")

# ── Load update history ──────────────────────────────────────────────────────
history_path = os.path.join(workspace, "mock_server_state", "update_history.json")
try:
    with open(history_path, "r", encoding="utf-8") as f:
        history = json.load(f)
except Exception as e:
    history = []
    check("history_readable", False, f"Could not read update history: {e}", weight=1.0)

# Filter to updates on our doc
doc_updates = [h for h in history if h.get("doc_id") == "doc_onboarding_2024" and h.get("action") == "update"]

# ── CHECK 1: Original blocks preserved ──────────────────────────────────────
original_block_ids = {"blk_001", "blk_002", "blk_003", "blk_004", "blk_005", "blk_006"}
original_block_contents = {
    "blk_001": "欢迎加入 NLP 实验室",
    "blk_002": "新加入实验室的同学",
    "blk_003": "基础环境配置",
    "blk_004": "Python",
    "blk_005": "实验室规范",
    "blk_006": "周报",
}

surviving_blocks = {b["block_id"]: b for b in final_blocks if b.get("block_id") in original_block_ids}
missing_original = original_block_ids - set(surviving_blocks.keys())

check(
    "original_blocks_preserved",
    len(missing_original) == 0,
    f"Missing original block IDs: {missing_original}" if missing_original else "All 6 original blocks preserved.",
    weight=3.0
)

# Check original content integrity
content_intact = True
content_issues = []
for bid, keyword in original_block_contents.items():
    if bid in surviving_blocks:
        block_content = surviving_blocks[bid].get("content", "")
        if keyword not in block_content:
            content_intact = False
            content_issues.append(f"Block {bid} should contain '{keyword}' but got: '{block_content[:60]}'")

check(
    "original_content_intact",
    content_intact,
    "; ".join(content_issues) if content_issues else "Original block content matches expectations.",
    weight=2.0
)

# ── CHECK 2: New content was added (document grew) ───────────────────────────
new_blocks = [b for b in final_blocks if b.get("block_id") not in original_block_ids]
check(
    "new_content_added",
    len(new_blocks) >= 3,
    f"Found {len(new_blocks)} new block(s) appended. Need at least 3 for a meaningful proposal section.",
    weight=2.0
)

# ── CHECK 3: Non-destructive update mode used ────────────────────────────────
DESTRUCTIVE_MODES = {"overwrite", "replace_all"}
used_modes = [h.get("mode") for h in doc_updates]

destructive_used = [m for m in used_modes if m in DESTRUCTIVE_MODES]
non_destructive_used = [m for m in used_modes if m not in DESTRUCTIVE_MODES]

check(
    "no_destructive_overwrite",
    len(destructive_used) == 0,
    f"Destructive modes used: {destructive_used}. Should use append/insert_after/insert_before." if destructive_used else f"Good: only non-destructive modes used: {non_destructive_used}",
    weight=3.0
)

check(
    "non_destructive_mode_used",
    len(non_destructive_used) > 0,
    f"Non-destructive update modes used: {non_destructive_used}" if non_destructive_used else "No non-destructive update detected in history.",
    weight=2.0
)

# ── CHECK 4: New section contains proposal keywords from the draft ────────────
all_new_content = " ".join(b.get("content", "") for b in new_blocks).lower()

proposal_keywords = {
    "摘要": ["摘要", "summary", "abstract", "自动摘要"],
    "中文": ["中文", "中文长文档", "chinese"],
    "数据": ["数据", "病历", "数据清洗", "十万"],
    "模型": ["模型", "fine-tune", "微调", "7b", "7b"],
    "评估": ["评估", "rouge", "人工"],
    "周期": ["周期", "6个月", "六个月", "months"],
    "经费": ["经费", "20万", "合作", "资金", "funding"],
    "产出": ["产出", "论文", "acl", "系统", "paper"],
}

found_keywords = {}
for category, variants in proposal_keywords.items():
    found = any(v.lower() in all_new_content for v in variants)
    found_keywords[category] = found

covered = sum(found_keywords.values())
check(
    "proposal_content_coverage",
    covered >= 5,
    f"Proposal keyword coverage: {covered}/8 categories found. Details: {found_keywords}",
    weight=2.0
)

# ── CHECK 5: Formal language (not chat-style) ─────────────────────────────────
chat_patterns = [
    r"大家觉得呢",
    r"嘛就是",
    r"挺靠谱",
    r"我觉得",
    r"然后我们的想法是",
    r"就是想做",
    r"大概.*吧",
    r"那种.*那种",
]
informal_found = []
for pattern in chat_patterns:
    if re.search(pattern, all_new_content):
        informal_found.append(pattern)

check(
    "formal_language_no_chat_tone",
    len(informal_found) == 0,
    f"Informal chat patterns found in new content: {informal_found}" if informal_found else "New content uses formal language (no chat-style patterns detected).",
    weight=2.0
)

# ── CHECK 6: Proposal has structured sections (heading blocks) ───────────────
heading_blocks = [b for b in new_blocks if b.get("type") in ("heading1", "heading2", "heading3")]
check(
    "proposal_has_structure",
    len(heading_blocks) >= 2,
    f"Found {len(heading_blocks)} heading block(s) in new content. Need ≥2 for structured proposal.",
    weight=2.0
)

# ── CHECK 7: Document title NOT repeated as H1 in body ──────────────────────
doc_title_short = final_title.replace(" ", "").lower()[:10]
h1_blocks = [b for b in final_blocks if b.get("type") == "heading1"]
title_repeated = False
for h1 in h1_blocks:
    h1_content = h1.get("content", "").replace(" ", "").lower()[:10]
    # Check if any heading1 block mirrors the doc title closely
    if doc_title_short and doc_title_short in h1_content:
        title_repeated = True
        break

check(
    "title_not_repeated_in_body",
    not title_repeated,
    "Document title was repeated as H1 in body — violates Feishu writing rules." if title_repeated else "Document title not duplicated as H1 in body content. Good.",
    weight=1.0
)

# ── CHECK 8: Self-contained document principle (context block exists) ──────────
# The new section should explain what it is, not just start listing content
# Look for contextual phrases in new content
context_phrases = [
    "本申请", "本提案", "本研究", "本课题", "申请背景", "项目背景",
    "研究背景", "overview", "项目概述", "课题申请", "研究申请",
    "项目说明", "以下为", "本节"
]
has_context = any(p.lower() in all_new_content for p in context_phrases)
check(
    "self_contained_context",
    has_context,
    f"New proposal section includes self-contained contextual intro (found one of: {context_phrases})." if has_context else "New section lacks self-contained context intro — reader unfamiliar with chat would be lost.",
    weight=1.0
)

# ── CHECK 9: Document URL was returned (check agent output files) ─────────────
# Agent should have written the URL somewhere — check for URL pattern in any output file
url_pattern = re.compile(r"http://localhost:8765/docs/doc_onboarding_2024")
url_found_in = []

candidate_files = [
    os.path.join(workspace, "TASK.md"),      # agent might have appended
    os.path.join(workspace, "operation_log.txt"),
    os.path.join(workspace, "output.txt"),
    os.path.join(workspace, "result.txt"),
    os.path.join(workspace, "delivery.txt"),
    os.path.join(workspace, "agent_output.txt"),
    os.path.join(workspace, "response.txt"),
    os.path.join(workspace, "answer.txt"),
    os.path.join(workspace, "delivery.md"),
    os.path.join(workspace, "result.md"),
]

# Also glob for any markdown/txt files the agent might have created
for p in Path(workspace).glob("*.txt"):
    if str(p) not in candidate_files:
        candidate_files.append(str(p))
for p in Path(workspace).glob("*.md"):
    if str(p) not in candidate_files:
        candidate_files.append(str(p))
for p in Path(workspace).glob("*.json"):
    if str(p) not in candidate_files:
        candidate_files.append(str(p))

for fpath in candidate_files:
    try:
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        if url_pattern.search(content):
            url_found_in.append(fpath)
    except Exception:
        pass

# Also check if the history itself shows a URL was accessed (GET /url endpoint)
# by checking if any log references it
url_delivery_confirmed = len(url_found_in) > 0

check(
    "document_url_returned",
    url_delivery_confirmed,
    f"Document URL found in: {url_found_in}" if url_delivery_confirmed else "Document URL not found in any output file. Agent failed to deliver the link.",
    weight=2.0
)

# ── CHECK 10: New section appears AFTER original content (append, not prepend) ──
original_block_positions = {b["block_id"]: i for i, b in enumerate(final_blocks) if b.get("block_id") in original_block_ids}
new_block_positions = [i for i, b in enumerate(final_blocks) if b.get("block_id") not in original_block_ids]

if original_block_positions and new_block_positions:
    last_original_pos = max(original_block_positions.values())
    first_new_pos = min(new_block_positions)
    appended_correctly = first_new_pos > last_original_pos
    check(
        "new_content_appended_after_original",
        appended_correctly,
        f"First new block at position {first_new_pos}, last original block at position {last_original_pos}. {'New content correctly follows original.' if appended_correctly else 'New content was inserted BEFORE original content — wrong order.'}",
        weight=2.0
    )
else:
    check(
        "new_content_appended_after_original",
        False,
        "Could not determine block positions (no new or no original blocks found).",
        weight=2.0
    )

# ── Final scoring ────────────────────────────────────────────────────────────
final_score = round(score_total / score_max, 3) if score_max > 0 else 0.0
passed = final_score >= 0.75 and checks[0]["passed"]  # Must preserve originals AND score ≥75%

print(json.dumps({
    "passed": passed,
    "score": final_score,
    "checks": checks
}, ensure_ascii=False, indent=2))