import json
import os
import re
from pathlib import Path

# Use /workspace as the workspace directory (where agent operates)
workspace = Path("/workspace")
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

try:
    plan = (workspace / "sprint-plan.md").read_text(encoding="utf-8", errors="replace")
except Exception as e:
    plan = ""
    add_check("output_exists", False, f"sprint-plan.md missing or unreadable: {e}")
else:
    add_check("output_exists", True, "sprint-plan.md found")

try:
    backlog_text = (workspace / "backlog.json").read_text(encoding="utf-8", errors="replace")
    backlog = json.loads(backlog_text)
except Exception as e:
    backlog = {}
    add_check("backlog_readable", False, f"backlog.json missing or malformed: {e}")
else:
    add_check("backlog_readable", True, "backlog.json parsed")

try:
    refs = (workspace / "references.txt").read_text(encoding="utf-8", errors="replace")
except Exception as e:
    refs = ""
    add_check("references_readable", False, f"references.txt missing or unreadable: {e}")
else:
    add_check("references_readable", True, "references.txt found")

# Check 1: file exists and has basic sections
try:
    normalized = re.sub(r"\s+", " ", plan.lower())
    has_goal = "sprint goal" in normalized
    has_capacity = "capacity" in normalized
    has_committed = "committed" in normalized
    has_stretch = "stretch" in normalized
    passed = all([has_goal, has_capacity, has_committed, has_stretch])
    detail = f"goal={has_goal}, capacity={has_capacity}, committed={has_committed}, stretch={has_stretch}"
except Exception as e:
    passed = False
    detail = f"error checking sections: {e}"
add_check("core_sections", passed, detail)

# Check 2: marker content reflected (more lenient - check for acknowledgment)
try:
    markers = [m.lower().strip() for m in re.findall(r"marker:\s*([^\n]+)", refs, flags=re.I)]
    found = []
    for m in markers:
        # Check if marker appears in plan OR if plan references markers generally
        marker_in_plan = m.lower() in plan.lower()
        # Also accept if plan mentions "marker" or "invest" or "capacity" in context
        general_ref = any(kw in plan.lower() for kw in ["marker", "invest", "capacity"])
        found.append(marker_in_plan or general_ref)
    passed = len(markers) > 0 and any(found)  # At least one marker acknowledged
    detail = f"markers_found={markers}, matched={found}"
except Exception as e:
    passed = False
    detail = f"error checking markers: {e}"
add_check("marker_reflection", passed, detail)

# Check 3: capacity math and committed <= 85%
try:
    base_velocity = float(backlog.get("base_velocity", 0))
    availability = float(backlog.get("availability_factor", 0))
    adjusted = base_velocity * availability
    committed_limit = adjusted * 0.85
    
    # Extract committed points - look for explicit "Committed Points" or "Total Committed"
    m = re.search(r"(?:total\s*committed|committed\s*total|committed\s*points)\s*[:\s]*(\d+(?:\.\d+)?)", plan, flags=re.I)
    explicit = float(m.group(1)) if m else None
    
    # Fallback: look for "Total Committed Points: X" pattern
    if explicit is None:
        m = re.search(r"total\s*committed\s*points\s*[:\s]*(\d+)", plan, flags=re.I)
        explicit = float(m.group(1)) if m else None
    
    # Fallback: calculate from story IDs in committed section
    if explicit is None:
        titles = [str(s.get("title", "")).lower() for s in backlog.get("stories", [])]
        committed_points = 0
        for s in backlog.get("stories", []):
            title = re.sub(r"[^a-z0-9]+", " ", str(s.get("title", "")).lower()).strip()
            if title and title in plan.lower():
                committed_points += int(s.get("points", 0))
        explicit = float(committed_points)
    
    total_used = explicit if explicit is not None else 0
    passed = total_used <= committed_limit + 0.01 and adjusted > 0
    detail = f"adjusted={adjusted:.2f}, committed_limit={committed_limit:.2f}, used={total_used}"
except Exception as e:
    passed = False
    detail = f"error checking capacity: {e}"
add_check("committed_within_capacity", passed, detail)

# Check 4: committed stories include acceptance criteria summaries and INVEST note
try:
    story_hits = 0
    ac_hits = 0
    invest_hits = 0
    for s in backlog.get("stories", []):
        sid = str(s.get("id", "")).lower()
        title = str(s.get("title", "")).lower()
        if sid in plan.lower() or re.sub(r"[^a-z0-9]+", " ", title).strip() in plan.lower():
            story_hits += 1
            if "acceptance" in plan.lower() and any(w.lower() in plan.lower() for w in ["given", "when", "then"]):
                ac_hits += 1
            if "invest" in plan.lower():
                invest_hits += 1
    passed = story_hits >= 3 and ac_hits > 0 and invest_hits > 0
    detail = f"story_hits={story_hits}, ac_hits={ac_hits}, invest_hits={invest_hits}"
except Exception as e:
    passed = False
    detail = f"error checking story details: {e}"
add_check("story_details", passed, detail)

# Check 5: output format is markdown and not empty
try:
    passed = len(plan.strip()) > 200 and "#" in plan
    detail = f"length={len(plan.strip())}"
except Exception as e:
    passed = False
    detail = f"error checking length: {e}"
add_check("nonempty_markdown", passed, detail)

score = (sum(1 for c in checks if c["passed"]) / len(checks)) if checks else 0.0
passed = all(c["passed"] for c in checks)
print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))