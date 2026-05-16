import sys
import json
import os
import re
from pathlib import Path

workspace = sys.argv[1]
lens_dir = Path(workspace) / ".lens"

checks = []

def check(name, condition, detail):
    checks.append({"name": name, "passed": bool(condition), "detail": detail})
    return bool(condition)

# ── 1. .lens/ directory exists ───────────────────────────────────────────────
lens_exists = lens_dir.is_dir()
check(
    "lens_directory_created",
    lens_exists,
    ".lens/ directory was created" if lens_exists else ".lens/ directory is missing"
)

# ── Helper: load file ─────────────────────────────────────────────────────────
def read_file(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return None

# ── 2. All Trinity Node files exist ──────────────────────────────────────────
axiom_path  = lens_dir / "AXIOM.md"
ethos_path  = lens_dir / "ETHOS.md"
modus_path  = lens_dir / "MODUS.md"
set_path    = lens_dir / "SET.json"

for fpath, label in [(axiom_path, "AXIOM.md"), (ethos_path, "ETHOS.md"),
                      (modus_path, "MODUS.md"), (set_path, "SET.json")]:
    check(
        f"file_exists_{label}",
        fpath.exists(),
        f"{label} {'exists' if fpath.exists() else 'is MISSING'}"
    )

# ── 3. SET.json structure and lifecycle phase ─────────────────────────────────
set_content = read_file(set_path)
set_data = None
try:
    if set_content:
        set_data = json.loads(set_content)
except Exception as e:
    set_data = None

check(
    "set_json_parseable",
    set_data is not None,
    "SET.json is valid JSON" if set_data is not None else f"SET.json is invalid or missing: {set_content[:200] if set_content else 'file missing'}"
)

if set_data:
    # Phase must be "Onboarding" (first-run / new user)
    phase = set_data.get("phase", set_data.get("lifecycle_phase", set_data.get("lifecyclePhase", "")))
    phase_ok = isinstance(phase, str) and "onboard" in phase.lower()
    check(
        "set_json_phase_onboarding",
        phase_ok,
        f"Lifecycle phase is '{phase}' — expected 'Onboarding'" if not phase_ok else f"Phase correctly set to '{phase}'"
    )

    # lens-interview cron must match Onboarding schedule: 30 11,17 * * *
    raw_set = set_content or ""
    cron_onboarding = "30 11,17 * * *"
    cron_ok = cron_onboarding in raw_set
    check(
        "set_json_interview_cron_onboarding",
        cron_ok,
        f"Onboarding cron '{cron_onboarding}' found in SET.json" if cron_ok else f"Onboarding cron '{cron_onboarding}' NOT found in SET.json"
    )

    # lens-distillation cron must be present: 0 3 * * *
    cron_distillation = "0 3 * * *"
    dist_cron_ok = cron_distillation in raw_set
    check(
        "set_json_distillation_cron",
        dist_cron_ok,
        f"Distillation cron '{cron_distillation}' found in SET.json" if dist_cron_ok else f"Distillation cron '{cron_distillation}' NOT found in SET.json"
    )
else:
    for name in ["set_json_phase_onboarding", "set_json_interview_cron_onboarding", "set_json_distillation_cron"]:
        check(name, False, "Skipped — SET.json could not be parsed")

# ── 4. AXIOM: immutable facts from transcripts ────────────────────────────────
axiom = read_file(axiom_path) or ""
axiom_lower = axiom.lower()

# Must contain: first company / Cape Town / 2011 / logistics SaaS / $800k ARR / sold 2014
axiom_facts = [
    ("axiom_first_company_2011", "2011", "Year first company founded (2011)"),
    ("axiom_bootstrapped_saas", "800", "$800k ARR bootstrap fact"),
    ("axiom_cape_town", "cape town", "Cape Town location"),
    ("axiom_sold_2014", "2014", "Company sold in 2014"),
    ("axiom_rental_properties", "rental", "Rental properties in Cape Town"),
    ("axiom_education_mba", "mba", "MBA degree"),
    ("axiom_education_engineering", "electrical engineering", "Electrical Engineering degree"),
    ("axiom_uct", "uct", "UCT university"),
]
for key, term, desc in axiom_facts:
    found = term.lower() in axiom_lower
    check(key, found, f"AXIOM contains '{desc}'" if found else f"AXIOM missing '{desc}' (searched: '{term}')")

# GreenFloat must be present in AXIOM (it's a verifiable private asset)
greenfloat_ok = "greenfloat" in axiom_lower or "green float" in axiom_lower
check(
    "axiom_greenfloat_stake",
    greenfloat_ok,
    "AXIOM records GreenFloat stake" if greenfloat_ok else "AXIOM missing GreenFloat stake"
)

# ── 5. ETHOS: exactly 10 Priority Traits ─────────────────────────────────────
ethos = read_file(ethos_path) or ""

# Count numbered list items OR bullet/dash items as trait entries
# Accept: "1.", "2." ... numbered, or lines starting with - / * / •
numbered_matches = re.findall(r'^\s*\d{1,2}[\.\)]\s+\S', ethos, re.MULTILINE)
bullet_matches   = re.findall(r'^\s*[-*•]\s+\S', ethos, re.MULTILINE)
# Use whichever method gives items; prefer numbered
trait_count = len(numbered_matches) if numbered_matches else len(bullet_matches)

check(
    "ethos_ten_priority_traits",
    trait_count == 10,
    f"ETHOS has {trait_count} Priority Traits (required: exactly 10)"
)

# ETHOS must mention key values: stoic/stoicism, first principles, skeptic/consensus
ethos_lower = ethos.lower()
for key, term, desc in [
    ("ethos_stoic", "stoic", "Stoic philosophy trait"),
    ("ethos_first_principles", "first principle", "First-principles reasoning"),
    ("ethos_contrarian_consensus", "consensus", "Skepticism of consensus"),
    ("ethos_operator_first", "operator", "Operator-first identity"),
    ("ethos_depth_relationships", "depth", "Depth over breadth in relationships"),
]:
    found = term in ethos_lower
    check(key, found, f"ETHOS contains '{desc}'" if found else f"ETHOS missing '{desc}'")

# ── 6. MODUS: exactly 5 Linguistic Markers, no AI-default bullets in markers ──
modus = read_file(modus_path) or ""

# Count markers similarly
modus_numbered = re.findall(r'^\s*\d[\.\)]\s+\S', modus, re.MULTILINE)
modus_bullets  = re.findall(r'^\s*[-*•]\s+\S', modus, re.MULTILINE)

# For MODUS markers section — look for a dedicated markers block
# Accept sections labelled "Linguistic Markers" with 5 entries
markers_section_match = re.search(
    r'(?:linguistic\s+markers?|markers?)[\s\S]{0,300}',
    modus, re.IGNORECASE
)
if markers_section_match:
    section = markers_section_match.group(0)
    m_numbered = re.findall(r'^\s*\d[\.\)]\s+\S', section, re.MULTILINE)
    m_bullets  = re.findall(r'^\s*[-*•]\s+\S', section, re.MULTILINE)
    marker_count = len(m_numbered) if m_numbered else len(m_bullets)
else:
    marker_count = len(modus_numbered) if modus_numbered else len(modus_bullets)

check(
    "modus_five_linguistic_markers",
    marker_count == 5,
    f"MODUS has {marker_count} Linguistic Markers (required: exactly 5)"
)

# Key MODUS patterns from transcripts
modus_lower = modus.lower()
for key, term, desc in [
    ("modus_no_bullets", "bullet", "No-bullets / long-form preference captured"),
    ("modus_em_dash", "em-dash", "Em-dash usage pattern"),
    ("modus_second_person", "second-person", "Second-person address style"),
    ("modus_deductive", "deductive", "Deductive argument structure (thesis first)"),
    ("modus_no_exclamation", "exclamation", "Avoidance of exclamation marks"),
]:
    # term could appear in different forms
    found = term in modus_lower or term.replace("-", " ") in modus_lower
    check(key, found, f"MODUS captures '{desc}'" if found else f"MODUS missing '{desc}'")

# AXIOM private flag for GreenFloat
# The skill says "Privacy Filter — never exfiltrate redlined AXIOM data"
# GreenFloat was marked "not public knowledge" — it should be flagged/redlined in AXIOM
axiom_private_flag = any(
    kw in axiom_lower for kw in ["private", "redline", "redlined", "confidential", "not public"]
)
check(
    "axiom_greenfloat_privacy_flag",
    axiom_private_flag,
    "AXIOM has privacy flag near GreenFloat entry" if axiom_private_flag else
    "AXIOM does NOT mark GreenFloat as private/redlined (per resolve-protocol)"
)

# ── 7. Integrity: no deletion of data (merge only) ───────────────────────────
# Verify AXIOM is non-empty and has substantive content
axiom_len_ok = len(axiom.strip()) > 200
check(
    "axiom_substantive_content",
    axiom_len_ok,
    f"AXIOM has substantive content ({len(axiom.strip())} chars)" if axiom_len_ok else "AXIOM appears too sparse"
)

ethos_len_ok = len(ethos.strip()) > 200
check(
    "ethos_substantive_content",
    ethos_len_ok,
    f"ETHOS has substantive content ({len(ethos.strip())} chars)" if ethos_len_ok else "ETHOS appears too sparse"
)

modus_len_ok = len(modus.strip()) > 100
check(
    "modus_substantive_content",
    modus_len_ok,
    f"MODUS has substantive content ({len(modus.strip())} chars)" if modus_len_ok else "MODUS appears too sparse"
)

# ── Final scoring ─────────────────────────────────────────────────────────────
passed_checks = sum(1 for c in checks if c["passed"])
total_checks  = len(checks)
score = round(passed_checks / total_checks, 4)
overall_passed = score >= 0.80

result = {
    "passed": overall_passed,
    "score": score,
    "checks": checks,
}
print(json.dumps(result, indent=2))