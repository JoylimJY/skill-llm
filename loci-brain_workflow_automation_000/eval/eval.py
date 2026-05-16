import sys
import json
import re
from pathlib import Path
from datetime import date

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
today = date.today().isoformat()
checks = []

def check(name, condition, detail):
    checks.append({"name": name, "passed": bool(condition), "detail": detail})
    return bool(condition)

# ── CHECK 1: ~/.loci/brain-path exists and points to a valid directory ────────
try:
    brain_path_file = Path("/root/.loci/brain-path")
    assert brain_path_file.exists(), "File /root/.loci/brain-path does not exist"
    raw_path = brain_path_file.read_text().strip()
    assert raw_path, "brain-path file is empty"
    brain_dir = Path(raw_path)
    assert brain_dir.exists(), f"Brain directory '{raw_path}' does not exist"
    check("brain_path_registered",
          True,
          f"~/.loci/brain-path exists and points to '{raw_path}'")
except Exception as e:
    check("brain_path_registered", False, str(e))
    brain_dir = Path("/root/loci")  # fallback for subsequent checks

# ── CHECK 2: plan.md status changed from 'template' to 'active' ───────────────
try:
    plan_md = brain_dir / "plan.md"
    if not plan_md.exists():
        plan_md = Path("/root/loci/plan.md")
    content = plan_md.read_text()
    has_active = bool(re.search(r"status\s*:\s*active", content))
    no_template = not bool(re.search(r"status\s*:\s*template", content))
    passed = has_active and no_template
    check("plan_md_status_active",
          passed,
          f"plan.md status field: active={has_active}, still_template={not no_template}. Snippet: {content[:300]}")
except Exception as e:
    check("plan_md_status_active", False, str(e))

# ── CHECK 3: plan.md contains mission/focus about the $50K retainer goal ──────
try:
    plan_md = brain_dir / "plan.md"
    if not plan_md.exists():
        plan_md = Path("/root/loci/plan.md")
    content = plan_md.read_text().lower()
    has_goal = any(kw in content for kw in ["50k", "retainer", "q3", "50,000", "$50"])
    check("plan_md_has_mission_goal",
          has_goal,
          f"plan.md should contain the '$50K retainer' focus. Found relevant keyword: {has_goal}")
except Exception as e:
    check("plan_md_has_mission_goal", False, str(e))

# ── CHECK 4: me/identity.md populated with Marcus Veld's details ──────────────
try:
    identity_md = brain_dir / "me" / "identity.md"
    if not identity_md.exists():
        identity_md = Path("/root/loci/me/identity.md")
    content = identity_md.read_text().lower()
    has_name = "marcus" in content or "veld" in content
    has_role = any(kw in content for kw in ["strategist", "product", "freelance", "saas"])
    passed = has_name and has_role
    check("identity_md_populated",
          passed,
          f"me/identity.md: has_name={has_name}, has_role={has_role}. Content snippet: {content[:300]}")
except Exception as e:
    check("identity_md_populated", False, str(e))

# ── CHECK 5: me/identity.md has personal fact about dog Biscuit (Item E) ──────
try:
    identity_md = brain_dir / "me" / "identity.md"
    if not identity_md.exists():
        identity_md = Path("/root/loci/me/identity.md")
    content = identity_md.read_text().lower()
    has_dog = "biscuit" in content or ("dog" in content and "beagle" in content)
    check("identity_md_has_personal_fact",
          has_dog,
          f"me/identity.md should contain personal fact about dog 'Biscuit'. Found: {has_dog}")
except Exception as e:
    check("identity_md_has_personal_fact", False, str(e))

# ── CHECK 6: tasks/active.md contains Nova Inc follow-up (Item B) ────────────
try:
    active_md = brain_dir / "tasks" / "active.md"
    if not active_md.exists():
        active_md = Path("/root/loci/tasks/active.md")
    content = active_md.read_text().lower()
    has_nova = "nova" in content
    has_task_context = any(kw in content for kw in ["follow", "workshop", "roadmap", "sign"])
    passed = has_nova and has_task_context
    check("tasks_active_has_nova_followup",
          passed,
          f"tasks/active.md: has_nova={has_nova}, has_task_context={has_task_context}. Snippet: {content[:300]}")
except Exception as e:
    check("tasks_active_has_nova_followup", False, str(e))

# ── CHECK 7: decisions/ has a file for the equity-only decision (Item A) ──────
try:
    decisions_dir = brain_dir / "decisions"
    if not decisions_dir.exists():
        decisions_dir = Path("/root/loci/decisions")
    decision_files = list(decisions_dir.glob("*.md"))
    
    found_equity_decision = False
    found_date_prefix = False
    correct_filename_format = False
    
    for f in decision_files:
        content = f.read_text().lower()
        if any(kw in content for kw in ["equity", "cash only", "cash-only", "no equity", "equity-only"]):
            found_equity_decision = True
            # Check filename format: YYYY-MM-DD-slug.md
            name = f.name
            if re.match(r"^\d{4}-\d{2}-\d{2}-.+\.md$", name):
                found_date_prefix = True
                correct_filename_format = True
    
    passed = found_equity_decision and found_date_prefix
    check("decisions_equity_file_exists",
          passed,
          f"decisions/: equity decision found={found_equity_decision}, "
          f"date-prefixed filename={found_date_prefix}. "
          f"Files found: {[f.name for f in decision_files]}")
except Exception as e:
    check("decisions_equity_file_exists", False, str(e))

# ── CHECK 8: me/learned.md contains the weekly cadence insight (Item C) ───────
try:
    learned_md = brain_dir / "me" / "learned.md"
    if not learned_md.exists():
        learned_md = Path("/root/loci/me/learned.md")
    content = learned_md.read_text().lower()
    has_insight = any(kw in content for kw in [
        "weekly", "cadence", "customer", "prioriti", "monthly", "talk to customer"
    ])
    check("learned_md_has_weekly_cadence_insight",
          has_insight,
          f"me/learned.md should contain insight about weekly customer cadence. Found: {has_insight}. "
          f"Snippet: {content[:300]}")
except Exception as e:
    check("learned_md_has_weekly_cadence_insight", False, str(e))

# ── CHECK 9: inbox.md contains the vague pricing thought (Item D) ─────────────
try:
    inbox_md = brain_dir / "inbox.md"
    if not inbox_md.exists():
        inbox_md = Path("/root/loci/inbox.md")
    content = inbox_md.read_text().lower()
    has_pricing = any(kw in content for kw in [
        "pricing", "project-based", "retainer", "oscillat", "still thinking", "model"
    ])
    check("inbox_has_vague_pricing_thought",
          has_pricing,
          f"inbox.md should contain the unresolved pricing thought. Found: {has_pricing}. "
          f"Snippet: {content[:300]}")
except Exception as e:
    check("inbox_has_vague_pricing_thought", False, str(e))

# ── CHECK 10: Decisions file NOT put into inbox, and insight NOT put in tasks ──
try:
    inbox_md = brain_dir / "inbox.md"
    if not inbox_md.exists():
        inbox_md = Path("/root/loci/inbox.md")
    inbox_content = inbox_md.read_text().lower()
    
    # Equity decision should be in decisions/, not inbox
    equity_in_inbox = any(kw in inbox_content for kw in ["equity", "cash only", "no equity"])
    
    active_md = brain_dir / "tasks" / "active.md"
    if not active_md.exists():
        active_md = Path("/root/loci/tasks/active.md")
    tasks_content = active_md.read_text().lower()
    
    # Insight should be in learned.md, not tasks
    insight_in_tasks = any(kw in tasks_content for kw in ["weekly cadence", "weekly customer", "cadence changes"])
    
    correct_separation = not equity_in_inbox and not insight_in_tasks
    check("distillation_separation_correct",
          correct_separation,
          f"Separation check: equity_decision_in_inbox={equity_in_inbox} (should be False), "
          f"cadence_insight_in_tasks={insight_in_tasks} (should be False)")
except Exception as e:
    check("distillation_separation_correct", False, str(e))

# ── SCORING ──────────────────────────────────────────────────────────────────
weights = {
    "brain_path_registered": 1.5,
    "plan_md_status_active": 1.5,
    "plan_md_has_mission_goal": 1.0,
    "identity_md_populated": 1.0,
    "identity_md_has_personal_fact": 1.0,
    "tasks_active_has_nova_followup": 1.0,
    "decisions_equity_file_exists": 2.0,
    "learned_md_has_weekly_cadence_insight": 1.5,
    "inbox_has_vague_pricing_thought": 1.0,
    "distillation_separation_correct": 1.5,
}

total_weight = sum(weights.values())
earned_weight = sum(weights[c["name"]] for c in checks if c["passed"] and c["name"] in weights)
score = round(earned_weight / total_weight, 4)
passed = score >= 0.75 and all(
    c["passed"] for c in checks
    if c["name"] in ["brain_path_registered", "plan_md_status_active", "decisions_equity_file_exists"]
)

result = {
    "passed": passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2))