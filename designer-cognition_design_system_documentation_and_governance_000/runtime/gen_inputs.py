import os
import random
from datetime import date, datetime

random.seed(42)

workspace = "/workspace"

# ── 1. Create deep distractor directory tree ──────────────────────────────────
dirs = [
    "design_log",
    "iteration_history",
    "component_library",
    "user_research",
    "brand_assets/fonts",
    "brand_assets/icons",
    "specs/mobile",
    "specs/desktop",
    "qa_reports/2024",
    "meeting_notes",
    "competitor_analysis",
    "analytics/funnels",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── 2. Distractor files ───────────────────────────────────────────────────────
distractor_files = {
    "brand_assets/fonts/font_license.txt": (
        "Inter - Licensed under SIL OFL 1.1\n"
        "Roboto - Licensed under Apache 2.0\n"
        "DO NOT use unlicensed fonts in production.\n"
    ),
    "brand_assets/icons/icon_inventory.txt": (
        "chevron_right.svg - Material Icons (Apache 2.0)\n"
        "lock.svg - Feather Icons (MIT)\n"
        "warning.svg - Custom (proprietary, internal use only)\n"
    ),
    "specs/mobile/screen_sizes.txt": (
        "Supported: 360x640, 390x844, 414x896, 428x926\n"
        "Breakpoints: 360px, 390px, 430px\n"
    ),
    "specs/desktop/grid_system.txt": (
        "12-column grid, 24px gutters, 1440px max container width.\n"
    ),
    "qa_reports/2024/accessibility_audit_march.txt": (
        "Audit Date: 2024-03-10\n"
        "Tool: axe-core v4.7\n"
        "Failures: 3 contrast violations on secondary buttons\n"
        "Status: OPEN\n"
    ),
    "meeting_notes/design_sync_2024_11.txt": (
        "Attendees: PM, Lead Designer, Frontend Dev\n"
        "Topics: Button system refactor, color token migration\n"
        "Action items: Update primary CTA color spec\n"
    ),
    "competitor_analysis/neobank_ctapatterns.txt": (
        "Revolut: Uses deep blue (#0075EB) primary CTA\n"
        "Monzo: Uses coral (#FF4B3E) primary CTA\n"
        "Wise: Uses green (#9FE870) primary CTA\n"
        "NOTE: Do not copy competitor design patterns directly.\n"
    ),
    "analytics/funnels/checkout_dropoff_q4.txt": (
        "Payment confirmation page drop-off: 23%\n"
        "Hypothesis: Low visibility of confirm button increases hesitation\n"
        "Sample size: 47,382 sessions\n"
    ),
    "component_library/button_tokens.txt": (
        "primary-bg: #9E9E9E  (LEGACY - under review)\n"
        "primary-fg: #FFFFFF\n"
        "secondary-bg: #F5F5F5\n"
        "secondary-fg: #212121\n"
        "border-radius: 8px\n"
        "font-weight: 600\n"
        "WCAG AA target: 4.5:1 for normal text, 3:1 for large text\n"
    ),
    "user_research/usability_test_oct2024.txt": (
        "Participants: 12 users, ages 22-58\n"
        "Task: Complete a payment on mobile\n"
        "Finding #1: 4/12 users hesitated before tapping 'Confirm Payment' button\n"
        "Finding #2: Button perceived as 'inactive' or 'disabled' due to gray color\n"
        "Finding #3: Color-blind participants (2) had no issues with gray button\n"
        "Recommendation: Increase button contrast and visual affordance\n"
        "Status: VALIDATED - approved for design action\n"
    ),
    "iteration_history/button_v1_spec.txt": (
        "Version: 1.0 — Initial release (2023-06-01)\n"
        "Primary CTA: background #9E9E9E, text #FFFFFF\n"
        "Contrast ratio: 3.95:1 (FAILS WCAG AA for normal text)\n"
        "Rationale: Matched legacy brand palette. No user testing at that time.\n"
    ),
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# ── 3. The core problem brief (messy, unstructured, no hints about format) ───
brief_content = """\
DESIGN CHANGE REQUEST — INTERNAL BRIEF
=======================================
Project: FinPay Mobile App
Component: Primary CTA Button — Payment Confirmation Screen
Requestor: Product Manager (Sarah Chen)
Date Raised: 2025-01-15

BACKGROUND
----------
Our payment funnel is bleeding users. Analytics show 23% drop-off on the
confirmation screen. Usability testing in October flagged that the current
gray button (#9E9E9E on white) looks disabled to users.

PROPOSED CHANGE
---------------
Change primary CTA background from LEGACY GRAY (#9E9E9E) to BRAND BLUE (#1A73E8).
Button text stays white (#FFFFFF).
This change affects ALL screens using the primary button component.

KNOWN CONSTRAINTS
-----------------
- Must pass accessibility review
- Must align with updated brand guidelines (blue approved by brand team Jan 2025)
- Must be documented for the upcoming design system audit (Q1 2025)

QUESTIONS TO ANSWER
-------------------
- Does this solve the user problem?
- Are there failure scenarios?  
- Can this be made a reusable system-level change?
- Does it align with overall product direction?

DELIVERABLE
-----------
Formal documentation package for the design system audit committee.
We need a record that shows we thought this through properly.
"""

with open(os.path.join(workspace, "design_change_request.txt"), "w", encoding="utf-8") as f:
    f.write(brief_content)

# ── 4. Partial / broken old design_decisions.md to test overwrite/append ─────
# This is intentionally malformed / incomplete to test the agent
broken_decisions = """\
# Design Decisions Log

## DD-001: Onboarding illustration style
Date: 2024-05-10
Decision: Use abstract geometric illustrations
Rationale: Brand team preference
<!-- INCOMPLETE - missing tags, no collision analysis, no red-line check -->
"""
with open(os.path.join(workspace, "design_decisions.md"), "w", encoding="utf-8") as f:
    f.write(broken_decisions)

print("Workspace initialized successfully.")
print(f"Files created: {sum(1 for _ in os.walk(workspace))}")