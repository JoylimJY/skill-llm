import sys
import json
import os
import re
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

def load_checks():
    return []

def parse_frontmatter(content: str):
    """Parse YAML frontmatter from markdown content."""
    stripped = content.strip()
    if not stripped.startswith('---'):
        return None, content
    # Find the closing ---
    end = stripped.find('\n---', 3)
    if end == -1:
        return None, content
    fm_str = stripped[3:end].strip()
    body = stripped[end+4:].strip()
    try:
        if yaml:
            fm = yaml.safe_load(fm_str)
        else:
            # Fallback manual parse
            fm = {}
            for line in fm_str.split('\n'):
                if ':' in line:
                    k, v = line.split(':', 1)
                    fm[k.strip()] = v.strip()
        return fm, body
    except Exception:
        return None, content

def find_memory_files(workspace: Path, mem_type: str):
    """Find all .md files under memory/<type>/"""
    type_dir = workspace / "memory" / mem_type
    if not type_dir.exists():
        return []
    return list(type_dir.glob("*.md"))

def check_date_filename(filepath: Path):
    """Check if filename matches yyyy-mm-dd.md pattern."""
    return bool(re.match(r'^\d{4}-\d{2}-\d{2}\.md$', filepath.name))

checks = []
workspace = Path(sys.argv[1])

# =========================================================
# CHECK 1: memory/user/ directory and file exist
# =========================================================
user_files = find_memory_files(workspace, "user")
has_user_dir = (workspace / "memory" / "user").exists()
has_user_file = len(user_files) > 0
has_user_date_filename = any(check_date_filename(f) for f in user_files)

checks.append({
    "name": "user_memory_file_exists_with_date_filename",
    "passed": has_user_file and has_user_date_filename,
    "detail": f"Found user memory files: {[f.name for f in user_files]}"
})

# =========================================================
# CHECK 2: user memory has valid frontmatter with all 4 required fields
# =========================================================
user_fm = None
user_body = ""
try:
    if user_files:
        content = user_files[0].read_text()
        fm, body = parse_frontmatter(content)
        user_fm = fm
        user_body = body
        required_fields = {'name', 'description', 'type', 'date'}
        missing = required_fields - set(fm.keys()) if fm else required_fields
        fm_valid = fm is not None and len(missing) == 0 and fm.get('type') == 'user'
        checks.append({
            "name": "user_memory_frontmatter_valid",
            "passed": fm_valid,
            "detail": f"Frontmatter: {fm}, missing fields: {missing if fm else 'all'}"
        })
    else:
        checks.append({
            "name": "user_memory_frontmatter_valid",
            "passed": False,
            "detail": "No user memory file found"
        })
except Exception as e:
    checks.append({
        "name": "user_memory_frontmatter_valid",
        "passed": False,
        "detail": f"Exception: {e}"
    })

# =========================================================
# CHECK 3: user memory content captures Maya Chen's role/identity
# =========================================================
try:
    user_content_combined = user_body.lower() + (str(user_fm).lower() if user_fm else "")
    has_maya = "maya" in user_content_combined or "chen" in user_content_combined
    has_sre = "sre" in user_content_combined or "site reliability" in user_content_combined
    has_datastream = "datastream" in user_content_combined
    has_observability = "observab" in user_content_combined or "log" in user_content_combined or "monitor" in user_content_combined

    user_content_quality = has_sre and (has_maya or has_datastream)
    checks.append({
        "name": "user_memory_captures_identity",
        "passed": user_content_quality,
        "detail": f"has_sre={has_sre}, has_maya={has_maya}, has_datastream={has_datastream}, has_observability={has_observability}"
    })
except Exception as e:
    checks.append({
        "name": "user_memory_captures_identity",
        "passed": False,
        "detail": f"Exception: {e}"
    })

# =========================================================
# CHECK 4: feedback/ directory with date-named file
# =========================================================
feedback_files = find_memory_files(workspace, "feedback")
has_feedback_file = len(feedback_files) > 0
has_feedback_date_filename = any(check_date_filename(f) for f in feedback_files)

checks.append({
    "name": "feedback_memory_file_exists_with_date_filename",
    "passed": has_feedback_file and has_feedback_date_filename,
    "detail": f"Found feedback files: {[f.name for f in feedback_files]}"
})

# =========================================================
# CHECK 5: feedback memory has valid frontmatter (type=feedback)
# =========================================================
feedback_fm = None
feedback_body = ""
try:
    if feedback_files:
        content = feedback_files[0].read_text()
        fm, body = parse_frontmatter(content)
        feedback_fm = fm
        feedback_body = body
        required_fields = {'name', 'description', 'type', 'date'}
        missing = required_fields - set(fm.keys()) if fm else required_fields
        fm_valid = fm is not None and len(missing) == 0 and fm.get('type') == 'feedback'
        checks.append({
            "name": "feedback_memory_frontmatter_valid",
            "passed": fm_valid,
            "detail": f"Frontmatter: {fm}"
        })
    else:
        checks.append({
            "name": "feedback_memory_frontmatter_valid",
            "passed": False,
            "detail": "No feedback file found"
        })
except Exception as e:
    checks.append({
        "name": "feedback_memory_frontmatter_valid",
        "passed": False,
        "detail": f"Exception: {e}"
    })

# =========================================================
# CHECK 6: feedback memory contains the 3-part proprietary structure
# (rule + **Why:** + **How to apply:**)
# =========================================================
try:
    all_feedback_content = ""
    for ff in feedback_files:
        all_feedback_content += ff.read_text().lower()
    
    has_why = "**why:**" in all_feedback_content or "why:" in all_feedback_content
    has_how = "**how to apply:**" in all_feedback_content or "how to apply:" in all_feedback_content
    
    # Must have at least one actionable rule about leading with solutions
    has_solution_rule = (
        "lead with" in all_feedback_content or 
        "solution first" in all_feedback_content or
        "start with" in all_feedback_content or
        "answer first" in all_feedback_content or
        "explanation" in all_feedback_content
    )
    # Must have async rule
    has_async_rule = "async" in all_feedback_content

    proprietary_structure = has_why and has_how
    content_complete = has_solution_rule and has_async_rule

    checks.append({
        "name": "feedback_has_proprietary_3part_structure",
        "passed": proprietary_structure,
        "detail": f"has_why={has_why}, has_how={has_how}. Content: lead_with={has_solution_rule}, async={has_async_rule}"
    })
    checks.append({
        "name": "feedback_captures_both_corrections",
        "passed": content_complete,
        "detail": f"has_solution_rule={has_solution_rule}, has_async_rule={has_async_rule}"
    })
except Exception as e:
    checks.append({
        "name": "feedback_has_proprietary_3part_structure",
        "passed": False,
        "detail": f"Exception: {e}"
    })
    checks.append({
        "name": "feedback_captures_both_corrections",
        "passed": False,
        "detail": f"Exception: {e}"
    })

# =========================================================
# CHECK 7: project/ memory exists with date filename
# =========================================================
project_files = find_memory_files(workspace, "project")
has_project_file = len(project_files) > 0
has_project_date_filename = any(check_date_filename(f) for f in project_files)

checks.append({
    "name": "project_memory_file_exists_with_date_filename",
    "passed": has_project_file and has_project_date_filename,
    "detail": f"Found project files: {[f.name for f in project_files]}"
})

# =========================================================
# CHECK 8: project memory has valid frontmatter (type=project)
# =========================================================
project_body = ""
try:
    if project_files:
        content = project_files[0].read_text()
        fm, body = parse_frontmatter(content)
        project_body = body
        required_fields = {'name', 'description', 'type', 'date'}
        missing = required_fields - set(fm.keys()) if fm else required_fields
        fm_valid = fm is not None and len(missing) == 0 and fm.get('type') == 'project'
        checks.append({
            "name": "project_memory_frontmatter_valid",
            "passed": fm_valid,
            "detail": f"Frontmatter: {fm}"
        })
    else:
        checks.append({
            "name": "project_memory_frontmatter_valid",
            "passed": False,
            "detail": "No project file found"
        })
except Exception as e:
    checks.append({
        "name": "project_memory_frontmatter_valid",
        "passed": False,
        "detail": f"Exception: {e}"
    })

# =========================================================
# CHECK 9: project memory converts relative date to absolute
# "next Thursday" from 2026-04-14 = 2026-04-23
# =========================================================
try:
    all_project_content = ""
    for pf in project_files:
        all_project_content += pf.read_text()
    
    has_grafana_migration = "grafana" in all_project_content.lower() and (
        "v8" in all_project_content.lower() or "v10" in all_project_content.lower() or
        "migrat" in all_project_content.lower()
    )
    # Check for absolute date conversion (2026-04-23 is "next Thursday")
    has_absolute_date = "2026-04-23" in all_project_content
    # Also accept some variation - "april 23" etc.
    has_april_23 = "april 23" in all_project_content.lower() or "apr 23" in all_project_content.lower()
    
    date_converted = has_absolute_date or has_april_23
    
    checks.append({
        "name": "project_memory_converts_relative_to_absolute_date",
        "passed": has_grafana_migration and date_converted,
        "detail": f"has_grafana_migration={has_grafana_migration}, has_absolute_date={has_absolute_date}, has_april_23={has_april_23}"
    })
except Exception as e:
    checks.append({
        "name": "project_memory_converts_relative_to_absolute_date",
        "passed": False,
        "detail": f"Exception: {e}"
    })

# =========================================================
# CHECK 10: project memory includes progress info (47 panels, 12 fixed)
# =========================================================
try:
    has_panel_count = "47" in all_project_content
    has_fixed_count = "12" in all_project_content
    checks.append({
        "name": "project_memory_captures_progress",
        "passed": has_panel_count or has_fixed_count,
        "detail": f"has_47_panels={has_panel_count}, has_12_fixed={has_fixed_count}"
    })
except Exception as e:
    checks.append({
        "name": "project_memory_captures_progress",
        "passed": False,
        "detail": f"Exception: {e}"
    })

# =========================================================
# CHECK 11: reference/ memory for external systems
# =========================================================
ref_files = find_memory_files(workspace, "reference")
has_ref_file = len(ref_files) > 0
has_ref_date_filename = any(check_date_filename(f) for f in ref_files)

checks.append({
    "name": "reference_memory_file_exists_with_date_filename",
    "passed": has_ref_file and has_ref_date_filename,
    "detail": f"Found reference files: {[f.name for f in ref_files]}"
})

# =========================================================
# CHECK 12: reference memory captures both Linear and PagerDuty
# =========================================================
try:
    all_ref_content = ""
    for rf in ref_files:
        all_ref_content += rf.read_text()
    
    all_ref_lower = all_ref_content.lower()
    has_linear = "linear" in all_ref_lower and "infra-dash" in all_ref_lower
    has_pagerduty = "pagerduty" in all_ref_lower and (
        "datastream ingest" in all_ref_lower or 
        "svc-48821" in all_ref_lower or
        "48821" in all_ref_lower
    )
    
    checks.append({
        "name": "reference_memory_captures_linear_and_pagerduty",
        "passed": has_linear and has_pagerduty,
        "detail": f"has_linear_infra_dash={has_linear}, has_pagerduty_svc={has_pagerduty}"
    })
    
    # Check frontmatter type
    if ref_files:
        content = ref_files[0].read_text()
        fm, _ = parse_frontmatter(content)
        required_fields = {'name', 'description', 'type', 'date'}
        missing = required_fields - set(fm.keys()) if fm else required_fields
        fm_valid = fm is not None and len(missing) == 0 and fm.get('type') == 'reference'
        checks.append({
            "name": "reference_memory_frontmatter_valid",
            "passed": fm_valid,
            "detail": f"Frontmatter: {fm}"
        })
    else:
        checks.append({
            "name": "reference_memory_frontmatter_valid",
            "passed": False,
            "detail": "No reference file found"
        })
except Exception as e:
    checks.append({
        "name": "reference_memory_captures_linear_and_pagerduty",
        "passed": False,
        "detail": f"Exception: {e}"
    })
    checks.append({
        "name": "reference_memory_frontmatter_valid",
        "passed": False,
        "detail": f"Exception: {e}"
    })

# =========================================================
# CHECK 13: BANNED content NOT saved - no code patterns/arch
# (The async script code from the AI should NOT be saved as a memory)
# =========================================================
try:
    all_memory_content = ""
    for mem_type in ["user", "feedback", "project", "reference"]:
        for mf in find_memory_files(workspace, mem_type):
            all_memory_content += mf.read_text()
    
    # The AI generated a Python code snippet - it should NOT be in memories
    has_banned_code = (
        "async def scan_deprecated_panels" in all_memory_content or
        "def scan_deprecated_panels" in all_memory_content or
        "dashboard_path: str" in all_memory_content
    )
    
    # Should not duplicate CLAUDE.md content (tech stack, max line length, etc.)
    has_duplicated_claude = (
        "max line length: 100" in all_memory_content.lower() or
        "type hints" in all_memory_content.lower() and "docstrings" in all_memory_content.lower()
    )
    
    no_banned_content = not has_banned_code and not has_duplicated_claude
    checks.append({
        "name": "no_banned_content_saved",
        "passed": no_banned_content,
        "detail": f"has_banned_code_pattern={has_banned_code}, has_duplicated_claude_content={has_duplicated_claude}"
    })
except Exception as e:
    checks.append({
        "name": "no_banned_content_saved",
        "passed": False,
        "detail": f"Exception: {e}"
    })

# =========================================================
# CHECK 14: MEMORY.md updated with new entries (still within 200 lines)
# =========================================================
try:
    memory_md_path = workspace / "MEMORY.md"
    if memory_md_path.exists():
        content = memory_md_path.read_text()
        lines = content.split('\n')
        line_count = len(lines)
        size_bytes = len(content.encode('utf-8'))
        
        # Must still have original content
        has_original = "memory/user/2026-01-10.md" in content or "Q1 OKR" in content
        
        # Must have new entries referencing today's memories
        content_lower = content.lower()
        has_new_user_entry = "memory/user/" in content and "maya" in content_lower or \
                             "memory/user/2026-04-14" in content
        has_new_project_entry = "memory/project/2026-04-14" in content or \
                                ("memory/project/" in content and "grafana" in content_lower)
        has_new_ref_entry = "memory/reference/2026-04-14" in content or \
                            ("memory/reference/" in content and ("linear" in content_lower or "pagerduty" in content_lower))
        
        within_limit = line_count <= 200 and size_bytes <= 25 * 1024
        
        # Check index entries are not excessively long (~ 200 chars per table row)
        table_lines = [l for l in lines if l.strip().startswith('|') and 'memory/' in l]
        long_lines = [l for l in table_lines if len(l) > 250]
        entries_concise = len(long_lines) == 0
        
        checks.append({
            "name": "memory_md_updated_with_new_entries",
            "passed": (has_new_user_entry or has_new_project_entry or has_new_ref_entry),
            "detail": f"new_user={has_new_user_entry}, new_project={has_new_project_entry}, new_ref={has_new_ref_entry}, lines={line_count}"
        })
        checks.append({
            "name": "memory_md_within_200_line_limit",
            "passed": within_limit,
            "detail": f"lines={line_count}/200, size={size_bytes}/{25*1024} bytes"
        })
        checks.append({
            "name": "memory_md_index_entries_concise",
            "passed": entries_concise,
            "detail": f"Lines exceeding ~200 chars: {len(long_lines)}. Examples: {long_lines[:2]}"
        })
    else:
        checks.append({"name": "memory_md_updated_with_new_entries", "passed": False, "detail": "MEMORY.md not found"})
        checks.append({"name": "memory_md_within_200_line_limit", "passed": False, "detail": "MEMORY.md not found"})
        checks.append({"name": "memory_md_index_entries_concise", "passed": False, "detail": "MEMORY.md not found"})
except Exception as e:
    checks.append({"name": "memory_md_updated_with_new_entries", "passed": False, "detail": f"Exception: {e}"})
    checks.append({"name": "memory_md_within_200_line_limit", "passed": False, "detail": f"Exception: {e}"})
    checks.append({"name": "memory_md_index_entries_concise", "passed": False, "detail": f"Exception: {e}"})

# =========================================================
# Final scoring
# =========================================================
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4) if total > 0 else 0.0
all_passed = passed_count == total

result = {
    "passed": all_passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, ensure_ascii=False, indent=2))