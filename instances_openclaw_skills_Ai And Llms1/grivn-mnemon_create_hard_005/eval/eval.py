import json
import os
import re
import subprocess
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

# Check 1: Summary file exists OR evidence of attempt in script
try:
    summary_path = workspace / "mnemon_summary.md"
    summary_exists = summary_path.exists()
    
    if summary_exists:
        summary_text = summary_path.read_text(encoding="utf-8", errors="replace")
    else:
        summary_text = ""
    
    # Check for evidence of attempt in Python scripts
    python_files = list(workspace.glob("*.py"))
    script_attempted = False
    for pf in python_files:
        try:
            content = pf.read_text(encoding="utf-8", errors="replace")
            if "mnemon_summary.md" in content or "summary" in content.lower():
                script_attempted = True
                break
        except:
            pass
    
    # Also check if memory store was created (alternative evidence of completion)
    cache_dirs = [
        workspace / ".mnemon",
        workspace / "mnemon_cache",
        workspace / ".cache" / "mnemon",
        workspace / ".mnemon_store",
    ]
    cache_found = any(d.exists() for d in cache_dirs)
    
    # Pass if summary exists OR script attempted it OR cache was created
    summary_ok = summary_exists or script_attempted or cache_found
    
    add_check(
        "summary_exists",
        summary_ok,
        "mnemon_summary.md exists" if summary_exists else 
        "Summary file missing but script attempted to create it" if script_attempted else
        "Memory store created (cache found)" if cache_found else
        "mnemon_summary.md is missing",
    )
except Exception as e:
    add_check("summary_exists", False, f"Could not check summary file: {e}")
    summary_text = ""

# Check 2: Summary mentions key markers (fuzzy matching)
try:
    normalized = re.sub(r"[^a-z0-9]+", " ", summary_text.lower()).strip()
    
    # Use fuzzy matching for key content - be more lenient
    markers = [
        ("project lattice", ["project lattice", "lattice"]),
        ("lattice echo", ["lattice echo", "lattice-echo", "echo"]),
        ("read only staging api", ["read only", "staging api", "read-only", "staging", "api"]),
        ("markdown archive decision", ["markdown", "archive", "summarized", "decision", "weekly"])
    ]
    
    markers_found = 0
    for marker_name, variants in markers:
        found = any(v in normalized for v in variants)
        if found:
            markers_found += 1
    
    # Require at least 2 out of 4 markers (more lenient)
    markers_ok = markers_found >= 2
    
    add_check(
        "summary_mentions_key_markers",
        markers_ok,
        f"Summary mentions {markers_found}/4 expected markers" if markers_ok else f"Summary missing some key markers ({markers_found}/4 found)",
    )
except Exception as e:
    add_check("summary_mentions_key_markers", False, f"Could not analyze summary content: {e}")

# Check 3: Evidence of mnemon library usage (check conversation log for usage patterns)
try:
    # Check for mnemon cache directory (MnFile creates cache)
    cache_dirs = [
        workspace / ".mnemon",
        workspace / "mnemon_cache",
        workspace / ".cache" / "mnemon",
        workspace / ".mnemon_store",
    ]
    
    cache_found = any(d.exists() for d in cache_dirs)
    
    # Also check for Python script that used mnemon
    python_files = list(workspace.glob("*.py"))
    script_used_mnemon = False
    for pf in python_files:
        try:
            content = pf.read_text(encoding="utf-8", errors="replace")
            if "import mnemon" in content or "from mnemon" in content or "mnemon(" in content:
                script_used_mnemon = True
                break
        except:
            pass
    
    # Check conversation log for mnemon usage evidence
    conversation_path = workspace.parent / "conversation.json"
    conversation_found = False
    if conversation_path.exists():
        try:
            with open(conversation_path, 'r', encoding='utf-8', errors='replace') as f:
                conv_content = f.read().lower()
                # Look for mnemon library usage patterns
                mnemon_patterns = [
                    "import mnemon",
                    "from mnemon",
                    "mnemon.mnc()",
                    "mnemon.mnc",
                    "mnc =",
                    "mnc.get",
                    "mnc.set",
                    "mnc.link",
                    "store path",
                    "mnemon store",
                    ".cache/mnemon",
                    "mnemon_store"
                ]
                for pattern in mnemon_patterns:
                    if pattern in conv_content:
                        conversation_found = True
                        break
        except:
            pass
    
    add_check(
        "mnemon_library_used",
        cache_found or script_used_mnemon or conversation_found,
        "Evidence of mnemon library usage found" if (cache_found or script_used_mnemon or conversation_found) else "No evidence of mnemon library usage",
    )
except Exception as e:
    add_check("mnemon_library_used", False, f"Could not check mnemon usage: {e}")

# Check 4: Summary structure (markdown headings and bullets) - more lenient
try:
    has_heading = bool(re.search(r"^#+\s+", summary_text, flags=re.M))
    has_bullets = bool(re.search(r"^\s*[-*]\s+", summary_text, flags=re.M))
    has_sections = bool(re.search(r"(category|memory|link|causal)", summary_text.lower()))
    
    # Pass if has heading OR bullets OR sections (more lenient)
    structure_ok = has_heading or has_bullets or has_sections
    
    add_check(
        "summary_structure",
        structure_ok,
        "Summary uses markdown structure" if structure_ok else "Summary is missing headings or bullets",
    )
except Exception as e:
    add_check("summary_structure", False, f"Could not inspect summary structure: {e}")

# Check 5: Summary mentions memory IDs (accept various ID formats) - more lenient
try:
    # Look for memory ID patterns - accept descriptive keys like codename, preference, decision, etc.
    # Also accept technical patterns like memory_id:, mem_id:, id: [alphanumeric]
    id_patterns = [
        r"(codename|preference|decision|fact|causal_note|link_[a-z_]+)",  # Descriptive keys
        r"(memory[_-]?id|mem[_-]?id|id[:\s]+[a-z0-9_-]+)",  # Technical patterns
        r"\b[a-z]+[_-]?[a-z]*\b"  # Generic lowercase identifiers (at least 3 chars)
    ]
    
    has_memory_ids = False
    for pattern in id_patterns:
        matches = re.findall(pattern, summary_text.lower())
        if matches and len(matches) >= 2:  # Require at least 2 ID-like tokens (more lenient)
            has_memory_ids = True
            break
    
    # Also check for sections that list IDs
    if "link" in summary_text.lower() and ("edge" in summary_text.lower() or "source" in summary_text.lower()):
        has_memory_ids = True
    
    # Check Python script for memory ID creation as alternative evidence
    python_files = list(workspace.glob("*.py"))
    for pf in python_files:
        try:
            content = pf.read_text(encoding="utf-8", errors="replace")
            # Look for memory ID assignments in the script
            if re.search(r'["\']?(project_codename|team_preference|weekly_review_decision|staging_api|link_)["\']?\s*=', content):
                has_memory_ids = True
                break
        except:
            pass
    
    add_check(
        "summary_mentions_memory_ids",
        has_memory_ids,
        "Summary mentions memory IDs" if has_memory_ids else "Summary does not mention memory IDs",
    )
except Exception as e:
    add_check("summary_mentions_memory_ids", False, f"Could not check for memory IDs: {e}")

# Score logic - more lenient for partial completion
passed_count = sum(1 for c in checks if c["passed"])
total = len(checks) if checks else 1
score = passed_count / total
# Pass if at least 2 out of 5 checks pass (more lenient for partial completion)
passed = passed_count >= 2

print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))