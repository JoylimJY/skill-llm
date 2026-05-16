#!/usr/bin/env python3
"""
Evaluation script for the OpenClaw Dashboard theme change task.
Checks:
1. CSS --accent in ALL 4 theme blocks is now #14b8a6 (teal)
2. CSS --accent-hover, --accent-muted, --accent-subtle, --accent-glow, --primary, --ring, --focus updated
3. Old accent (#e85d04) is gone from CSS
4. JS bundle has new accent color and old accent is gone
5. Danger color (#ef4444) is preserved in both CSS and JS
6. change-theme.sh script was NOT modified (its content hash)
"""

import sys
import json
import os
import re
import hashlib

checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})

HOME = os.path.expanduser("~")
ASSETS_DIR = os.path.join(HOME, ".openclaw", "ui", "dist", "assets")
SKILL_SCRIPT = os.path.join(HOME, ".openclaw", "workspace", "skills", "dashboard-theme", "change-theme.sh")

CSS_HASH = "a3f9c21b"
JS_HASH  = "b7d4e89f"
CSS_PATH = os.path.join(ASSETS_DIR, f"index-{CSS_HASH}.css")
JS_PATH  = os.path.join(ASSETS_DIR, f"index-{JS_HASH}.js")

TARGET_COLOR = "#14b8a6"  # teal / 青色
TARGET_UPPER = TARGET_COLOR.upper()   # #14B8A6
TARGET_LOWER = TARGET_COLOR.lower()   # #14b8a6
OLD_ACCENT   = "#e85d04"
OLD_UPPER    = OLD_ACCENT.upper()
DANGER_COLOR = "#ef4444"

# ── Read CSS ──────────────────────────────────────────────────────────────────
try:
    with open(CSS_PATH, "r") as f:
        css = f.read()
    css_ok = True
except Exception as e:
    css = ""
    css_ok = False
    add_check("css_file_readable", False, f"Cannot read CSS: {e}")

if css_ok:
    add_check("css_file_readable", True, f"CSS file read: {len(css)} bytes")

# ── CSS variable checks ───────────────────────────────────────────────────────

def count_css_var(css_text, var_name, expected_hex):
    """Count how many times var_name appears with the expected hex value."""
    # Match --var: #hex; or --var: #HEX;
    pattern = rf'--{re.escape(var_name)}:\s*{re.escape(expected_hex)}\s*;'
    return len(re.findall(pattern, css_text, re.IGNORECASE))

def count_theme_blocks(css_text):
    """Count :root, [data-theme="light"], [data-theme="openknot"], [data-theme="dash"] blocks."""
    blocks = re.findall(r':root\s*\{|data-theme=', css_text)
    return len(blocks)

if css_ok:
    # Check --accent updated in all 4 theme blocks
    accent_count = count_css_var(css, "accent", TARGET_COLOR)
    n_blocks = count_theme_blocks(css)
    passed = accent_count >= 4  # :root + 3 data-theme blocks
    add_check(
        "css_accent_all_blocks",
        passed,
        f"--accent set to {TARGET_COLOR} in {accent_count} blocks (expected ≥4 theme blocks, found {n_blocks} blocks total)"
    )

    # Check --primary updated
    primary_count = count_css_var(css, "primary", TARGET_COLOR)
    passed_primary = primary_count >= 1
    add_check(
        "css_primary_updated",
        passed_primary,
        f"--primary set to {TARGET_COLOR} in {primary_count} locations"
    )

    # Check --ring updated
    ring_count = count_css_var(css, "ring", TARGET_COLOR)
    passed_ring = ring_count >= 1
    add_check(
        "css_ring_updated",
        passed_ring,
        f"--ring set to {TARGET_COLOR} in {ring_count} locations"
    )

    # Check --focus updated
    focus_count = count_css_var(css, "focus", TARGET_COLOR)
    passed_focus = focus_count >= 1
    add_check(
        "css_focus_updated",
        passed_focus,
        f"--focus set to {TARGET_COLOR} in {focus_count} locations"
    )

    # Check --accent-hover is updated (should NOT still be old hover #c44d03 everywhere, 
    # and should be a darkened teal variant — we check it's not the old hex value)
    old_hover = "#c44d03"
    old_hover_count = len(re.findall(re.escape(old_hover), css, re.IGNORECASE))
    # New hover of #14b8a6 darkened 15% = R=17,G=156,B=140 ≈ #119c8c
    # We check the old hover is gone and some new hex appears for --accent-hover
    accent_hover_match = re.findall(r'--accent-hover:\s*(#[0-9a-fA-F]{6})\s*;', css)
    new_hover_values = [v for v in accent_hover_match if v.lower() != old_hover.lower()]
    passed_hover = len(new_hover_values) >= 1
    add_check(
        "css_accent_hover_updated",
        passed_hover,
        f"--accent-hover old values: {old_hover_count}, new values found: {new_hover_values}"
    )

    # Check --accent-subtle contains teal RGB components
    # #14b8a6 → R=20, G=184, B=166
    subtle_matches = re.findall(r'--accent-subtle:\s*(rgba\([^)]+\))\s*;', css)
    teal_subtle = [m for m in subtle_matches if '20' in m and '184' in m]
    passed_subtle = len(teal_subtle) >= 1 or any('14b8a6' in m.lower() or '14B8A6' in m for m in re.findall(r'--accent-subtle:[^;]+;', css))
    # More lenient: just check old rgba is gone and new rgba is present
    old_subtle_rgba = "rgba(232,93,4,0.10)"
    old_subtle_count = css.count(old_subtle_rgba)
    new_subtle_present = len(subtle_matches) >= 1 and old_subtle_count == 0
    add_check(
        "css_accent_subtle_updated",
        new_subtle_present,
        f"--accent-subtle: old rgba occurrences={old_subtle_count}, new subtle values={subtle_matches[:3]}"
    )

    # Check --accent-glow updated
    old_glow_rgba = "rgba(232,93,4,0.20)"
    old_glow_count = css.count(old_glow_rgba)
    glow_matches = re.findall(r'--accent-glow:\s*(rgba\([^)]+\))\s*;', css)
    new_glow_present = len(glow_matches) >= 1 and old_glow_count == 0
    add_check(
        "css_accent_glow_updated",
        new_glow_present,
        f"--accent-glow: old rgba occurrences={old_glow_count}, new glow values={glow_matches[:3]}"
    )

    # Old accent fully eliminated from CSS (case-insensitive, no-hash form)
    old_no_hash = OLD_ACCENT[1:].lower()  # e85d04
    old_in_css = len(re.findall(old_no_hash, css, re.IGNORECASE))
    passed_old_gone = old_in_css == 0
    add_check(
        "css_old_accent_eliminated",
        passed_old_gone,
        f"Old accent '{OLD_ACCENT}' occurrences in CSS: {old_in_css}"
    )

    # Danger color preserved
    danger_in_css = len(re.findall(re.escape(DANGER_COLOR[1:]), css, re.IGNORECASE))
    passed_danger = danger_in_css >= 1
    add_check(
        "css_danger_color_preserved",
        passed_danger,
        f"Danger color '{DANGER_COLOR}' occurrences in CSS: {danger_in_css}"
    )

# ── Read JS ───────────────────────────────────────────────────────────────────
try:
    with open(JS_PATH, "r") as f:
        js = f.read()
    js_ok = True
except Exception as e:
    js = ""
    js_ok = False
    add_check("js_file_readable", False, f"Cannot read JS: {e}")

if js_ok:
    add_check("js_file_readable", True, f"JS file read: {len(js)} bytes")

    # New teal color appears in JS
    teal_in_js = len(re.findall(re.escape(TARGET_COLOR[1:]), js, re.IGNORECASE))
    passed_teal_js = teal_in_js >= 1
    add_check(
        "js_new_accent_present",
        passed_teal_js,
        f"New teal '{TARGET_COLOR}' occurrences in JS: {teal_in_js}"
    )

    # Old accent gone from JS
    old_in_js = len(re.findall(re.escape(OLD_ACCENT[1:]), js, re.IGNORECASE))
    passed_old_js = old_in_js == 0
    add_check(
        "js_old_accent_eliminated",
        passed_old_js,
        f"Old accent '{OLD_ACCENT}' occurrences in JS: {old_in_js}"
    )

    # Danger color preserved in JS
    danger_in_js = len(re.findall(re.escape(DANGER_COLOR[1:]), js, re.IGNORECASE))
    passed_danger_js = danger_in_js >= 1
    add_check(
        "js_danger_color_preserved",
        passed_danger_js,
        f"Danger color '{DANGER_COLOR}' occurrences in JS: {danger_in_js}"
    )

    # Standard palette colors NOT replaced (e.g., #007bff, #00e5cc, #f59e0b)
    standard_colors = ["007bff", "00e5cc", "10b981"]
    for sc in standard_colors:
        sc_count = len(re.findall(sc, js, re.IGNORECASE))
        add_check(
            f"js_standard_color_preserved_{sc}",
            sc_count >= 1,
            f"Standard color #{sc} occurrences in JS: {sc_count}"
        )

# ── Script integrity check ────────────────────────────────────────────────────
# The skill SKILL.md says "不要修改 change-theme.sh 以外的文件"
# But more importantly: verify the script itself was NOT modified by the agent 
# (it should only be invoked, not rewritten). We compare against a known fragment.
try:
    with open(SKILL_SCRIPT, "r") as f:
        script_content = f.read()
    # Key indicator: the script must still contain its original function definitions
    has_hex_math = "hex_to_rgb()" in script_content or "hex_to_rgb" in script_content
    has_protected = "PROTECTED_COLORS" in script_content
    has_verify = "Verification" in script_content
    script_intact = has_hex_math and has_protected and has_verify
    add_check(
        "skill_script_intact",
        script_intact,
        f"Script functions present: hex_to_rgb={has_hex_math}, PROTECTED={has_protected}, Verify={has_verify}"
    )
except Exception as e:
    add_check("skill_script_intact", False, f"Cannot read script: {e}")

# ── Score ─────────────────────────────────────────────────────────────────────
# Weight the most important checks higher
critical_checks = [
    "css_accent_all_blocks",
    "css_primary_updated",
    "css_ring_updated",
    "css_old_accent_eliminated",
    "js_new_accent_present",
    "js_old_accent_eliminated",
    "js_danger_color_preserved",
    "css_danger_color_preserved",
]

total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = passed_count / total if total > 0 else 0.0

# Must pass all critical checks to be considered "passed"
critical_passed = all(
    any(c["name"] == name and c["passed"] for c in checks)
    for name in critical_checks
)

overall_passed = critical_passed and (score >= 0.80)

result = {
    "passed": overall_passed,
    "score": round(score, 3),
    "checks": checks
}

print(json.dumps(result, indent=2))