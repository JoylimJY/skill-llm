import sys
import json
import re
from pathlib import Path
from datetime import date, timedelta

workspace = Path(sys.argv[1])

checks = []
score_parts = []

def c(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed

# ── helpers ──────────────────────────────────────────────────────────────────
def business_days_between(start: date, end: date) -> int:
    """Count business days from start (exclusive) to end (inclusive)."""
    days = 0
    current = start + timedelta(days=1)
    while current <= end:
        if current.weekday() < 5:  # Mon–Fri
            days += 1
        current += timedelta(days=1)
    return days

TODAY = date(2026, 3, 10)

# Applications that should be OVERDUE for follow-up (status=applied, ≥5 biz days, no response)
# Stripe: 2026-02-27 → was already in JSON (app_001), still applied, 9 biz days → overdue
# DataDog: 2026-02-15 → already in JSON (app_002), still applied, 17 biz days → overdue
# Temporal: 2026-03-02 → 6 biz days → overdue
# PlanetScale: 2026-03-03 → 5 biz days → overdue (exactly 5)
# Notion: 2026-02-27 → 9 biz days → overdue
# Anthropic: 2026-03-02 → 6 biz days → overdue
OVERDUE_COMPANIES = {"Stripe", "DataDog", "Temporal", "PlanetScale", "Notion", "Anthropic"}
NOT_OVERDUE_COMPANIES = {"Cloudflare", "Vercel"}  # 4 and 3 biz days
PHONE_SCREEN_COMPANY = "CockroachLabs"  # status=phone_screen → not a "no response"
REJECTED_COMPANY = "Figma"              # rejected → no follow-up

# ── 1. Load applications.json ─────────────────────────────────────────────────
apps_path = workspace / "data" / "applications.json"
try:
    data = json.loads(apps_path.read_text())
    apps = data.get("applications", [])
    stats = data.get("stats", {})
    c("applications_json_loadable", True, "File loaded and parsed as JSON")
except Exception as e:
    c("applications_json_loadable", False, f"Cannot load applications.json: {e}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# ── 2. Deduplication: Stripe already existed — must NOT be duplicated ─────────
stripe_entries = [a for a in apps if a.get("company","").lower() == "stripe"]
dup_ok = c(
    "no_duplicate_stripe",
    len(stripe_entries) == 1,
    f"Found {len(stripe_entries)} Stripe entry/entries (expected exactly 1 — original preserved, CSV duplicate skipped)"
)
score_parts.append((dup_ok, 0.10))

# ── 3. New applications imported (excluding Stripe duplicate, Figma=rejected is ok to import) ──
expected_new_companies = {"Temporal", "PlanetScale", "Cloudflare", "Vercel", "CockroachLabs", "Notion", "Anthropic", "Figma"}
found_companies = {a.get("company","") for a in apps}
imported = expected_new_companies & found_companies
missing = expected_new_companies - found_companies
import_ok = c(
    "new_applications_imported",
    len(missing) == 0,
    f"Imported: {sorted(imported)}. Missing: {sorted(missing)}"
)
score_parts.append((import_ok, 0.12))

# ── 4. Schema correctness on new entries ─────────────────────────────────────
required_fields = {"id","company","role","url","status","applied_date","source","contact","notes","follow_up_date","interviews","outcome"}
schema_errors = []
for a in apps:
    missing_fields = required_fields - set(a.keys())
    if missing_fields:
        schema_errors.append(f"{a.get('company','?')}: missing {missing_fields}")
schema_ok = c(
    "schema_fields_present",
    len(schema_errors) == 0,
    f"Schema errors: {schema_errors}" if schema_errors else "All entries have required fields"
)
score_parts.append((schema_ok, 0.08))

# ── 5. follow_up_date is set using business-day logic ────────────────────────
# For applied entries the follow_up_date should be ~5 business days after applied_date
def expected_follow_up(applied_str):
    d = date.fromisoformat(applied_str)
    count = 0
    cur = d + timedelta(days=1)
    while count < 5:
        if cur.weekday() < 5:
            count += 1
        if count < 5:
            cur += timedelta(days=1)
    return cur

fud_errors = []
for a in apps:
    if a.get("status") not in ("applied",):
        continue
    try:
        applied_date = a.get("applied_date","")
        fud = a.get("follow_up_date","")
        if not fud or not applied_date:
            fud_errors.append(f"{a['company']}: missing follow_up_date or applied_date")
            continue
        expected = expected_follow_up(applied_date)
        got = date.fromisoformat(fud)
        if got != expected:
            fud_errors.append(f"{a['company']}: follow_up_date={fud}, expected {expected}")
    except Exception as ex:
        fud_errors.append(f"{a.get('company','?')}: error {ex}")

fud_ok = c(
    "follow_up_dates_use_business_days",
    len(fud_errors) == 0,
    f"Business-day follow_up_date errors: {fud_errors}" if fud_errors else "All follow_up_dates correctly computed using business days"
)
score_parts.append((fud_ok, 0.15))

# ── 6. Stats block correctly computed ─────────────────────────────────────────
total_applied = len(apps)
# "responses" = apps with status not in (applied, saved) — i.e., something came back
response_statuses = {"phone_screen","technical","onsite","offer","rejected"}
responses_count = sum(1 for a in apps if a.get("status","") in response_statuses)
interviews_count = sum(1 for a in apps if a.get("status","") in {"phone_screen","technical","onsite"})
offers_count = sum(1 for a in apps if a.get("status","") == "offer")

expected_total = total_applied  # must equal len(apps)
stats_total_ok = c(
    "stats_total_applied_correct",
    stats.get("total_applied", -1) == expected_total,
    f"stats.total_applied={stats.get('total_applied')} expected={expected_total}"
)
score_parts.append((stats_total_ok, 0.08))

# response_rate must be computed correctly
if expected_total > 0:
    expected_rr = round(responses_count / expected_total * 100, 1)
    actual_rr = stats.get("response_rate", -1)
    # Allow ±2 tolerance in rate value (could be expressed as fraction 0-1 or percent 0-100)
    if isinstance(actual_rr, float) and actual_rr <= 1.0:
        actual_rr_pct = round(actual_rr * 100, 1)
    else:
        actual_rr_pct = actual_rr
    rr_ok = c(
        "stats_response_rate_correct",
        abs(float(actual_rr_pct) - expected_rr) <= 2.5,
        f"stats.response_rate={stats.get('response_rate')} (normalized={actual_rr_pct}%), expected≈{expected_rr}%"
    )
else:
    rr_ok = c("stats_response_rate_correct", False, "No applications found to compute rate")
score_parts.append((rr_ok, 0.08))

# ── 7. Low-response-rate flag / reassess note ─────────────────────────────────
# With ≥20 apps total and likely <10% response rate → must flag this
# Check either in stats or in a separate flag field or in a report file
flag_detected = False
flag_detail = "No reassess/low-response-rate flag found"

# Check stats for a flag field
if data.get("reassess_approach") or data.get("low_response_flag") or stats.get("reassess_approach") or stats.get("low_response_flag"):
    flag_detected = True
    flag_detail = "Flag found in applications.json (top-level or stats)"

# Check for a report/analysis file anywhere in workspace
for fpath in workspace.rglob("*"):
    if fpath.is_file() and fpath.suffix in (".txt", ".md", ".json"):
        try:
            content = fpath.read_text(errors="ignore").lower()
            if any(kw in content for kw in ["reassess", "response rate", "below 10", "low response", "10%"]):
                flag_detected = True
                flag_detail = f"Reassess/low-response-rate flag found in: {fpath.relative_to(workspace)}"
                break
        except:
            pass

flag_ok = c(
    "low_response_rate_flag_present",
    flag_detected,
    flag_detail
)
score_parts.append((flag_ok, 0.07))

# ── 8. Follow-up email drafts exist for overdue applications ──────────────────
follow_ups_dir = workspace / "follow_ups"
follow_up_files = list(follow_ups_dir.glob("*")) if follow_ups_dir.exists() else []
# Also search workspace-wide for follow-up drafts
all_followup_files = list(workspace.rglob("follow_up*")) + list(workspace.rglob("followup*")) + list(workspace.rglob("*follow_up*"))
all_followup_files = list({f for f in all_followup_files if f.is_file()})

companies_with_drafts = set()
for f in all_followup_files:
    try:
        content = f.read_text(errors="ignore").lower()
        for company in OVERDUE_COMPANIES:
            if company.lower() in content:
                companies_with_drafts.add(company)
    except:
        pass

# Also check follow_ups dir for files named by app id or company
for f in follow_up_files:
    try:
        content = f.read_text(errors="ignore").lower()
        for company in OVERDUE_COMPANIES:
            if company.lower() in content:
                companies_with_drafts.add(company)
    except:
        pass

overdue_covered = OVERDUE_COMPANIES & companies_with_drafts
overdue_missing = OVERDUE_COMPANIES - companies_with_drafts
drafts_ok = c(
    "follow_up_drafts_for_overdue_apps",
    len(overdue_missing) == 0,
    f"Drafts found for: {sorted(overdue_covered)}. Missing drafts for: {sorted(overdue_missing)}"
)
score_parts.append((drafts_ok, 0.15))

# ── 9. Non-overdue apps do NOT have follow-up drafts generated ───────────────
false_positives = set()
for f in all_followup_files:
    try:
        content = f.read_text(errors="ignore").lower()
        # Figma is rejected — should NOT get a follow-up
        if "figma" in content:
            false_positives.add("Figma")
        # CockroachLabs has phone_screen status — NOT a "no response" follow-up scenario
        # (it's ok if they got a thank-you, but a standard follow-up should not be drafted)
    except:
        pass
no_false_pos_ok = c(
    "no_follow_up_for_rejected_apps",
    "Figma" not in false_positives,
    f"Figma (rejected) incorrectly got a follow-up draft" if "Figma" in false_positives else "Rejected apps correctly excluded from follow-up drafts"
)
score_parts.append((no_false_pos_ok, 0.05))

# ── 10. Email draft content quality: must reference company name + be addressed ──
draft_quality_errors = []
for f in all_followup_files:
    try:
        content = f.read_text(errors="ignore")
        # Should have at least minimal email structure
        if len(content.strip()) < 50:
            draft_quality_errors.append(f"{f.name}: too short (<50 chars)")
    except Exception as ex:
        draft_quality_errors.append(f"{f.name}: {ex}")

draft_quality_ok = c(
    "follow_up_drafts_have_content",
    len(draft_quality_errors) == 0,
    f"Draft quality issues: {draft_quality_errors}" if draft_quality_errors else f"All {len(all_followup_files)} draft file(s) have adequate content"
)
score_parts.append((draft_quality_ok, 0.06))

# ── 11. IDs are unique and follow app_XXX pattern ─────────────────────────────
ids = [a.get("id","") for a in apps]
id_pattern_ok = all(re.match(r"^app_\d{3,}$", i) for i in ids if i)
ids_unique = len(ids) == len(set(ids))
id_ok = c(
    "application_ids_unique_and_formatted",
    id_pattern_ok and ids_unique,
    f"IDs: {ids[:5]}... unique={ids_unique} pattern_ok={id_pattern_ok}"
)
score_parts.append((id_ok, 0.06))

# ── Final score ───────────────────────────────────────────────────────────────
total_weight = sum(w for _, w in score_parts)
weighted_score = sum(w for passed, w in score_parts if passed)
score = round(weighted_score / total_weight, 4) if total_weight > 0 else 0.0
passed = score >= 0.70

print(json.dumps({
    "passed": passed,
    "score": score,
    "checks": checks
}, indent=2))