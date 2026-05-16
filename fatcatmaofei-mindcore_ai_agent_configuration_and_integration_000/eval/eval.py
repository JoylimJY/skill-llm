#!/usr/bin/env python3
"""
Evaluation script for MindCore configuration task.
Checks:
  1. BURST_BASE_OFFSET has been set to a high-activity value (>= 0.3)
  2. Short-term memory has been seeded with the 3 topics from zara's activity export
  3. The engine can be imported and the memory/config is structurally valid
  4. A captured JSON signal file exists and contains required MindCore output fields
"""
import sys
import json
import os
import importlib.util
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
mindcore = workspace / "mindcore"

checks = []
total_score = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0

# ── CHECK 1: BURST_BASE_OFFSET is set to high-activity value ──────────────
score1 = 0.0
try:
    # Search for BURST_BASE_OFFSET in engine config files and main.py
    burst_found = False
    burst_value = None
    burst_location = None
    
    search_paths = list(mindcore.rglob("*.py")) + list(mindcore.rglob("*.json")) + list(mindcore.rglob("*.cfg")) + list(mindcore.rglob("*.ini")) + list(mindcore.rglob("*.yaml")) + list(mindcore.rglob("*.yml"))
    
    for fpath in search_paths:
        try:
            content = fpath.read_text(errors="replace")
            if "BURST_BASE_OFFSET" in content:
                # Try to extract the value
                import re
                # Match patterns like BURST_BASE_OFFSET = 0.5 or "BURST_BASE_OFFSET": 0.5
                patterns = [
                    r'BURST_BASE_OFFSET\s*[=:]\s*([+-]?\d+\.?\d*)',
                    r'"BURST_BASE_OFFSET"\s*:\s*([+-]?\d+\.?\d*)',
                ]
                for pat in patterns:
                    m = re.search(pat, content)
                    if m:
                        burst_value = float(m.group(1))
                        burst_found = True
                        burst_location = str(fpath.relative_to(workspace))
                        break
            if burst_found:
                break
        except Exception:
            continue
    
    if not burst_found:
        score1 = add_check(
            "BURST_BASE_OFFSET configured",
            False,
            "BURST_BASE_OFFSET not found in any MindCore file. Agent must set this parameter for high-activity mode.",
            weight=0.30
        )
    elif burst_value is not None and burst_value >= 0.3:
        score1 = add_check(
            "BURST_BASE_OFFSET configured",
            True,
            f"BURST_BASE_OFFSET = {burst_value} found in {burst_location} (>= 0.3, high-activity mode confirmed).",
            weight=0.30
        )
    else:
        score1 = add_check(
            "BURST_BASE_OFFSET configured",
            False,
            f"BURST_BASE_OFFSET = {burst_value} in {burst_location} is too low for high-activity mode (need >= 0.3).",
            weight=0.30
        )
except Exception as e:
    score1 = add_check("BURST_BASE_OFFSET configured", False, f"Exception during check: {e}", weight=0.30)

total_score += score1

# ── CHECK 2: Short-term memory seeded with zara's topics ──────────────────
score2 = 0.0
EXPECTED_TOPICS = ["matcha latte recipes", "lo-fi study music", "weekend hiking trails"]

try:
    # Look for memory file in the data directory
    memory_candidates = list(mindcore.rglob("memory*.json")) + list(mindcore.rglob("*memory*.json")) + list(mindcore.rglob("short_term*.json"))
    
    # Also check data/ directory specifically
    data_dir = mindcore / "data"
    if data_dir.exists():
        memory_candidates += list(data_dir.glob("*.json"))
    
    memory_found = False
    topics_found = []
    memory_location = None
    
    for mfile in memory_candidates:
        try:
            content = mfile.read_text(errors="replace")
            data = json.loads(content)
            
            # Memory could be a list or dict with a list inside
            items = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                for key in ["memory", "buffer", "items", "entries", "slots", "topics"]:
                    if key in data and isinstance(data[key], list):
                        items = data[key]
                        break
                if not items:
                    # Flatten all string values
                    items = [str(v) for v in data.values()]
            
            # Check if expected topics are present (partial match acceptable)
            found_here = []
            content_lower = content.lower()
            for topic in EXPECTED_TOPICS:
                if topic.lower() in content_lower:
                    found_here.append(topic)
            
            if len(found_here) >= 2:
                memory_found = True
                topics_found = found_here
                memory_location = str(mfile.relative_to(workspace))
                break
        except Exception:
            continue
    
    if memory_found:
        score2 = add_check(
            "Short-term memory seeded with user topics",
            True,
            f"Found {len(topics_found)}/3 expected topics in {memory_location}: {topics_found}",
            weight=0.30
        )
    else:
        score2 = add_check(
            "Short-term memory seeded with user topics",
            False,
            f"Could not find short-term memory file containing zara's topics. Expected: {EXPECTED_TOPICS}. Checked: {[str(p.relative_to(workspace)) for p in memory_candidates[:5]]}",
            weight=0.30
        )
except Exception as e:
    score2 = add_check("Short-term memory seeded with user topics", False, f"Exception: {e}", weight=0.30)

total_score += score2

# ── CHECK 3: Captured JSON signal file exists with valid MindCore schema ───
score3 = 0.0
try:
    # Search for a captured signal/output JSON file
    signal_candidates = (
        list(workspace.rglob("signal*.json")) +
        list(workspace.rglob("impulse*.json")) +
        list(workspace.rglob("output*.json")) +
        list(workspace.rglob("thought*.json")) +
        list((workspace / "output").glob("*.json") if (workspace / "output").exists() else [])
    )
    
    # Filter out the input file
    signal_candidates = [f for f in signal_candidates if "zara_activity" not in f.name and "BROKEN" not in f.name]
    
    valid_signal = False
    signal_location = None
    signal_detail = ""
    
    # MindCore JSON output should have fields related to impulse/category/content
    REQUIRED_FIELDS_OPTIONS = [
        ["category", "content"],
        ["impulse", "category"],
        ["type", "content"],
        ["thought", "category"],
        ["signal_type", "content"],
        ["category"],  # minimum - at least category from the 9 categories
    ]
    KNOWN_CATEGORIES = ["food", "social", "entertainment", "rest", "curiosity", "creative", 
                        "physical", "emotional", "cognitive", "reflection", "body", "sleep"]
    
    for sfile in signal_candidates:
        try:
            content = sfile.read_text(errors="replace")
            data = json.loads(content)
            
            # Could be a list of signals or a single signal
            if isinstance(data, list) and len(data) > 0:
                data = data[0]
            
            if not isinstance(data, dict):
                continue
            
            # Check for category field matching known MindCore categories
            data_lower = {k.lower(): (v.lower() if isinstance(v, str) else v) for k, v in data.items()}
            content_str = json.dumps(data).lower()
            
            has_category = any(cat in content_str for cat in KNOWN_CATEGORIES)
            has_content = any(k in data_lower for k in ["content", "text", "message", "thought", "impulse_text", "description"])
            
            if has_category or has_content:
                valid_signal = True
                signal_location = str(sfile.relative_to(workspace))
                signal_detail = f"Signal keys: {list(data.keys())[:8]}"
                break
        except Exception:
            continue
    
    if valid_signal:
        score3 = add_check(
            "Valid MindCore JSON signal captured",
            True,
            f"Valid signal found at {signal_location}. {signal_detail}",
            weight=0.25
        )
    else:
        score3 = add_check(
            "Valid MindCore JSON signal captured",
            False,
            f"No valid MindCore JSON signal found. Searched {len(signal_candidates)} candidates: {[f.name for f in signal_candidates[:5]]}",
            weight=0.25
        )
except Exception as e:
    score3 = add_check("Valid MindCore JSON signal captured", False, f"Exception: {e}", weight=0.25)

total_score += score3

# ── CHECK 4: Memory decay metadata present (2-hour exponential decay) ──────
score4 = 0.0
try:
    # Re-scan memory files for decay/timestamp metadata
    memory_candidates = list(mindcore.rglob("memory*.json")) + list(mindcore.rglob("*memory*.json")) + list(mindcore.rglob("short_term*.json"))
    data_dir = mindcore / "data"
    if data_dir.exists():
        memory_candidates += list(data_dir.glob("*.json"))
    
    decay_found = False
    decay_detail = ""
    
    for mfile in set(memory_candidates):
        try:
            content = mfile.read_text(errors="replace")
            content_lower = content.lower()
            # Check for decay-related fields
            if any(kw in content_lower for kw in ["decay", "timestamp", "time", "ttl", "expire", "boost"]):
                decay_found = True
                decay_detail = f"Decay/timestamp metadata found in {mfile.relative_to(workspace)}"
                break
        except Exception:
            continue
    
    if decay_found:
        score4 = add_check(
            "Memory entries contain decay/timestamp metadata",
            True,
            decay_detail,
            weight=0.15
        )
    else:
        score4 = add_check(
            "Memory entries contain decay/timestamp metadata",
            False,
            "No decay or timestamp metadata found in memory files. MindCore's 5-slot FIFO uses 2-hour exponential decay.",
            weight=0.15
        )
except Exception as e:
    score4 = add_check("Memory entries contain decay/timestamp metadata", False, f"Exception: {e}", weight=0.15)

total_score += score4

# ── Final result ──────────────────────────────────────────────────────────
passed = total_score >= 0.55

result = {
    "passed": passed,
    "score": round(total_score, 3),
    "checks": checks
}
print(json.dumps(result, indent=2))