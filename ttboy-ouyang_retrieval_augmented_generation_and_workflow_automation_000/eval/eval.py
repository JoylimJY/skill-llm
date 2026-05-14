#!/usr/bin/env python3
"""
Evaluation script for the jasper-recall knowledge audit task.

Checks:
1. memory_audit_report.json exists at /workspace/
2. It is valid JSON
3. It contains all three required topic keys (or close matches)
4. Each topic has at least 3 results
5. Each result has a 'document' field (non-empty string)
6. Each result has a 'score' field (numeric)
7. Scores are plausible similarity values (> 0)
8. Documents contain relevant content (semantic relevance check via keyword presence)
"""

import sys
import json
import re
from pathlib import Path

def find_report(workspace: Path):
    """Find memory_audit_report.json — check root first, then rglob."""
    direct = workspace / "memory_audit_report.json"
    if direct.exists():
        return direct
    found = list(workspace.rglob("memory_audit_report.json"))
    return found[0] if found else None


TOPIC_KEYWORDS = {
    "fourth_amendment": [
        "fourth amendment", "fourth", "warrant", "privacy", "carpenter",
        "digital", "location", "cell", "search", "csli", "riley", "jones",
        "katz", "expectation", "surveillance"
    ],
    "ai_copyright": [
        "copyright", "ai", "artificial intelligence", "intellectual property",
        "thaler", "authorship", "human", "generated", "generative", "naruto",
        "patent", "ownership", "creative"
    ],
    "antitrust": [
        "antitrust", "monopoly", "platform", "google", "meta", "ftc", "doj",
        "market", "competition", "enforcement", "epic", "apple", "exclusion"
    ]
}

TOPIC_PATTERNS = [
    ("fourth_amendment",  r"fourth.{0,30}(amendment|privacy|warrant|digital)"),
    ("ai_copyright",      r"(ai|artificial).{0,30}(copyright|intellectual|generated|authorship)"),
    ("antitrust",         r"(antitrust|monopoly|platform).{0,30}(enforcement|market|google|meta)"),
]

def detect_topic_key(key: str) -> str | None:
    """Map an arbitrary JSON key to one of our canonical topic names."""
    key_lower = key.lower()
    scores = {}
    for topic, keywords in TOPIC_KEYWORDS.items():
        hit = sum(1 for kw in keywords if kw in key_lower)
        if hit:
            scores[topic] = hit
    if scores:
        return max(scores, key=scores.get)
    return None


def check_document_relevance(doc_text: str, topic: str) -> bool:
    """Check if document text contains at least one topic keyword."""
    doc_lower = doc_text.lower()
    keywords = TOPIC_KEYWORDS.get(topic, [])
    return any(kw in doc_lower for kw in keywords)


def run_eval(workspace_str: str):
    workspace = Path(workspace_str)
    checks = []
    passed_all = True

    # ── Check 1: File exists ──────────────────────────────────────────────
    report_path = find_report(workspace)
    file_exists = report_path is not None
    checks.append({
        "name": "memory_audit_report.json exists",
        "passed": file_exists,
        "detail": str(report_path) if file_exists else "File not found anywhere under /workspace"
    })
    if not file_exists:
        passed_all = False
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── Check 2: Valid JSON ───────────────────────────────────────────────
    try:
        with open(report_path) as f:
            data = json.load(f)
        valid_json = True
        checks.append({"name": "Valid JSON", "passed": True, "detail": f"Parsed OK, keys: {list(data.keys())}"})
    except Exception as e:
        checks.append({"name": "Valid JSON", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.05, "checks": checks}

    # ── Check 3: Contains all three topics ───────────────────────────────
    if not isinstance(data, dict):
        checks.append({"name": "Top-level is a JSON object", "passed": False, "detail": f"Got {type(data)}"})
        return {"passed": False, "score": 0.1, "checks": checks}

    topic_map = {}  # canonical_topic -> list_of_results
    for key in data.keys():
        canonical = detect_topic_key(key)
        if canonical and canonical not in topic_map:
            topic_map[canonical] = data[key]

    required_topics = ["fourth_amendment", "ai_copyright", "antitrust"]
    found_topics = [t for t in required_topics if t in topic_map]
    all_topics_found = len(found_topics) == 3

    checks.append({
        "name": "All three research topics present",
        "passed": all_topics_found,
        "detail": f"Found canonical topics: {found_topics}. Keys in file: {list(data.keys())}"
    })
    if not all_topics_found:
        passed_all = False

    # ── Check 4-6: Per-topic result quality ──────────────────────────────
    score_accumulator = 0.0
    max_possible = 0.0

    for topic in required_topics:
        results = topic_map.get(topic, [])

        # Check 4a: At least 3 results
        has_3_results = isinstance(results, list) and len(results) >= 3
        checks.append({
            "name": f"[{topic}] Has ≥ 3 results",
            "passed": has_3_results,
            "detail": f"Found {len(results) if isinstance(results, list) else 'N/A'} results"
        })
        max_possible += 1.0
        if has_3_results:
            score_accumulator += 1.0
        else:
            passed_all = False
            continue

        # Check 4b: Each result has 'document' field (non-empty string)
        docs_valid = all(
            isinstance(r, dict) and "document" in r and isinstance(r["document"], str) and len(r["document"]) > 10
            for r in results[:3]
        )
        checks.append({
            "name": f"[{topic}] Results have 'document' field (non-empty string)",
            "passed": docs_valid,
            "detail": f"Checked top 3 results: {'OK' if docs_valid else 'FAIL'}"
        })
        max_possible += 1.0
        if docs_valid:
            score_accumulator += 1.0
        else:
            passed_all = False

        # Check 4c: Each result has 'score' field (numeric, > 0)
        scores_valid = all(
            isinstance(r, dict) and "score" in r and isinstance(r["score"], (int, float)) and r["score"] > 0
            for r in results[:3]
        )
        checks.append({
            "name": f"[{topic}] Results have 'score' field (numeric, > 0)",
            "passed": scores_valid,
            "detail": f"Scores: {[r.get('score') for r in results[:3]]}"
        })
        max_possible += 1.0
        if scores_valid:
            score_accumulator += 1.0
        else:
            passed_all = False

        # Check 4d: Documents contain topically relevant content
        relevance_check = sum(
            1 for r in results[:3]
            if isinstance(r, dict) and "document" in r
            and check_document_relevance(str(r["document"]), topic)
        )
        is_relevant = relevance_check >= 2  # at least 2 of 3 must be relevant
        checks.append({
            "name": f"[{topic}] Documents contain relevant content",
            "passed": is_relevant,
            "detail": f"{relevance_check}/3 documents contain topic-relevant keywords"
        })
        max_possible += 1.0
        if is_relevant:
            score_accumulator += 1.0
        else:
            passed_all = False

    # ── Check 5: Scores look like real similarity values (not all identical) ─
    try:
        all_scores = []
        for topic in required_topics:
            results = topic_map.get(topic, [])
            for r in results[:3]:
                if isinstance(r, dict) and "score" in r and isinstance(r["score"], (int, float)):
                    all_scores.append(r["score"])

        scores_are_varied = len(set(round(s, 4) for s in all_scores)) > 1 if all_scores else False
        scores_in_range = all(0 < s <= 1.5 for s in all_scores) if all_scores else False

        checks.append({
            "name": "Similarity scores are varied and in plausible range",
            "passed": scores_are_varied and scores_in_range,
            "detail": f"Unique scores: {len(set(round(s,4) for s in all_scores))}, "
                      f"range: [{min(all_scores):.4f}, {max(all_scores):.4f}] (n={len(all_scores)})"
                      if all_scores else "No scores found"
        })
        max_possible += 1.0
        if scores_are_varied and scores_in_range:
            score_accumulator += 1.0
        else:
            passed_all = False
    except Exception as e:
        checks.append({"name": "Score range check", "passed": False, "detail": str(e)})
        max_possible += 1.0
        passed_all = False

    final_score = round(score_accumulator / max_possible, 3) if max_possible > 0 else 0.0

    return {
        "passed": passed_all,
        "score": final_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, indent=2))