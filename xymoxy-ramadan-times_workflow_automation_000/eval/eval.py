#!/usr/bin/env python3
import sys
import json
import os
import re
from pathlib import Path

workspace = sys.argv[1]

checks = []
total_score = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0

# ── Find output files ─────────────────────────────────────────────────────────
london_files = list(Path(workspace).rglob("london_en_prayercard.txt"))
cairo_files = list(Path(workspace).rglob("cairo_ar_prayercard.txt"))

london_exists = len(london_files) > 0
cairo_exists = len(cairo_files) > 0

total_score += add_check(
    "london_en_prayercard.txt exists",
    london_exists,
    f"Found at: {london_files[0]}" if london_exists else "File not found anywhere in workspace"
)

total_score += add_check(
    "cairo_ar_prayercard.txt exists",
    cairo_exists,
    f"Found at: {cairo_files[0]}" if cairo_exists else "File not found anywhere in workspace"
)

# ── Read file contents ────────────────────────────────────────────────────────
london_content = ""
cairo_content = ""

try:
    if london_exists:
        london_content = london_files[0].read_text(encoding="utf-8")
except Exception as e:
    add_check("london file readable", False, f"Error reading file: {e}")

try:
    if cairo_exists:
        cairo_content = cairo_files[0].read_text(encoding="utf-8")
except Exception as e:
    add_check("cairo file readable", False, f"Error reading file: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# LONDON (English) checks
# ══════════════════════════════════════════════════════════════════════════════

# 1. Moon emoji present
total_score += add_check(
    "london: moon emoji (🌙) present",
    "🌙" in london_content,
    f"Content preview: {london_content[:200]!r}"
)

# 2. Must say RAMADAN (English header) - not RAMAZAN
has_ramadan_en = bool(re.search(r'🌙\s*RAMADAN', london_content))
has_ramazan_wrong = bool(re.search(r'🌙\s*RAMAZAN', london_content))
total_score += add_check(
    "london: correct English header '🌙 RAMADAN'",
    has_ramadan_en and not has_ramazan_wrong,
    f"Has RAMADAN: {has_ramadan_en}, Has RAMAZAN (wrong): {has_ramazan_wrong}"
)

# 3. City name London present
total_score += add_check(
    "london: city name 'London' present",
    bool(re.search(r'London', london_content, re.IGNORECASE)),
    f"Content: {london_content[:300]!r}"
)

# 4. Date emoji 📅 present
total_score += add_check(
    "london: calendar emoji (📅) present",
    "📅" in london_content,
    "Missing 📅 emoji"
)

# 5. Date format: English style "Sunday, March 15, 2026"
# 2026-03-15 is a Sunday
date_en_pattern = re.search(r'Sunday.*March.*15.*2026|March.*15.*2026.*Sunday', london_content, re.IGNORECASE)
total_score += add_check(
    "london: English date format (Sunday, March 15, 2026)",
    date_en_pattern is not None,
    f"Date pattern not found. Content: {london_content!r}"
)

# 6. Sunrise emoji 🌅 and Sahur label in English
total_score += add_check(
    "london: Sahur label with 🌅 emoji",
    bool(re.search(r'🌅.*Sahur', london_content)),
    "Missing '🌅 Sahur:' line"
)

# 7. Iftar label in English
total_score += add_check(
    "london: Iftar label (English) with 🌅 emoji",
    bool(re.search(r'🌅.*Iftar', london_content)),
    "Missing '🌅 Iftar:' line in English"
)

# 8. Time values present (HH:MM format)
total_score += add_check(
    "london: time values in HH:MM format",
    len(re.findall(r'\d{2}:\d{2}', london_content)) >= 2,
    f"Time values found: {re.findall(r'\\d{{2}}:\\d{{2}}', london_content)}"
)

# 9. Countdown present: English "Time until iftar"
has_countdown_en = bool(re.search(r'Time until iftar', london_content, re.IGNORECASE))
total_score += add_check(
    "london: countdown label 'Time until iftar' (English)",
    has_countdown_en,
    f"Missing 'Time until iftar' phrase. Content: {london_content!r}"
)

# 10. Countdown has hours and minutes (numeric)
countdown_nums_en = re.search(r'(\d+)\s*hours?\s*(\d+)\s*minutes?', london_content, re.IGNORECASE)
total_score += add_check(
    "london: countdown has numeric hours and minutes",
    countdown_nums_en is not None,
    f"Countdown pattern: {countdown_nums_en.group(0) if countdown_nums_en else 'NOT FOUND'}"
)

# 11. Clock emoji ⏰
total_score += add_check(
    "london: clock emoji (⏰) present",
    "⏰" in london_content,
    "Missing ⏰ emoji"
)

# 12. Specific sahur/iftar times from mock API for London
london_sahur_correct = "05:33" in london_content
london_iftar_correct = "18:07" in london_content
total_score += add_check(
    "london: correct Sahur time from API (05:33)",
    london_sahur_correct,
    f"Expected '05:33'. Times found: {re.findall(r'\\d{{2}}:\\d{{2}}', london_content)}"
)
total_score += add_check(
    "london: correct Iftar time from API (18:07)",
    london_iftar_correct,
    f"Expected '18:07'. Times found: {re.findall(r'\\d{{2}}:\\d{{2}}', london_content)}"
)

# ══════════════════════════════════════════════════════════════════════════════
# CAIRO (Arabic) checks
# ══════════════════════════════════════════════════════════════════════════════

# 1. Moon emoji
total_score += add_check(
    "cairo: moon emoji (🌙) present",
    "🌙" in cairo_content,
    f"Content preview: {cairo_content[:200]!r}"
)

# 2. Arabic Ramadan word رمضان
has_ramadan_ar = "رمضان" in cairo_content
total_score += add_check(
    "cairo: Arabic Ramadan word (رمضان) present",
    has_ramadan_ar,
    f"Missing 'رمضان' in content: {cairo_content[:200]!r}"
)

# 3. City name Cairo present
total_score += add_check(
    "cairo: city name 'Cairo' present",
    bool(re.search(r'Cairo', cairo_content, re.IGNORECASE)),
    f"Content: {cairo_content[:300]!r}"
)

# 4. Calendar emoji 📅
total_score += add_check(
    "cairo: calendar emoji (📅) present",
    "📅" in cairo_content,
    "Missing 📅 emoji"
)

# 5. Arabic day name (Sunday = الأحد for 2026-03-15)
has_arabic_day = "الأحد" in cairo_content
total_score += add_check(
    "cairo: Arabic day name (الأحد for Sunday)",
    has_arabic_day,
    f"Missing Arabic Sunday 'الأحد'. Content: {cairo_content!r}"
)

# 6. Arabic month name (March = مارس)
has_arabic_month = "مارس" in cairo_content
total_score += add_check(
    "cairo: Arabic month name (مارس for March)",
    has_arabic_month,
    f"Missing Arabic March 'مارس'. Content: {cairo_content!r}"
)

# 7. Arabic Sahur label
has_sahur_ar = "السحور" in cairo_content
total_score += add_check(
    "cairo: Arabic Sahur label (السحور)",
    has_sahur_ar,
    f"Missing 'السحور'. Content: {cairo_content!r}"
)

# 8. Arabic Iftar label
has_iftar_ar = "الإفطار" in cairo_content
total_score += add_check(
    "cairo: Arabic Iftar label (الإفطار)",
    has_iftar_ar,
    f"Missing 'الإفطار'. Content: {cairo_content!r}"
)

# 9. Clock emoji ⏰
total_score += add_check(
    "cairo: clock emoji (⏰) present",
    "⏰" in cairo_content,
    "Missing ⏰ emoji"
)

# 10. Arabic countdown phrase
has_countdown_ar = "الوقت حتى الإفطار" in cairo_content or "حتى الإفطار" in cairo_content
total_score += add_check(
    "cairo: Arabic countdown phrase (الوقت حتى الإفطار)",
    has_countdown_ar,
    f"Missing Arabic countdown. Content: {cairo_content!r}"
)

# 11. Arabic hour/minute words
has_ar_time_units = ("ساعة" in cairo_content or "ساعات" in cairo_content) and "دقيقة" in cairo_content
total_score += add_check(
    "cairo: Arabic time units (ساعة/دقيقة) in countdown",
    has_ar_time_units,
    f"Missing Arabic time units. Content: {cairo_content!r}"
)

# 12. Correct times from API for Cairo
cairo_sahur_correct = "04:42" in cairo_content
cairo_iftar_correct = "18:14" in cairo_content
total_score += add_check(
    "cairo: correct Sahur time from API (04:42)",
    cairo_sahur_correct,
    f"Expected '04:42'. Times found: {re.findall(r'\\d{{2}}:\\d{{2}}', cairo_content)}"
)
total_score += add_check(
    "cairo: correct Iftar time from API (18:14)",
    cairo_iftar_correct,
    f"Expected '18:14'. Times found: {re.findall(r'\\d{{2}}:\\d{{2}}', cairo_content)}"
)

# 13. Sunrise emoji 🌅 in Cairo file
total_score += add_check(
    "cairo: sunrise emoji (🌅) present",
    "🌅" in cairo_content,
    "Missing 🌅 emoji"
)

# ── Bonus: check that agent actually used the skill script (not just hardcoded)
# We verify by checking that the date 2026-03-15 appears in the output
total_score += add_check(
    "london: date 2026 in output",
    "2026" in london_content,
    "Year 2026 not found in london output"
) * 0.5

total_score += add_check(
    "cairo: date 2026 in output",
    "2026" in cairo_content,
    "Year 2026 not found in cairo output"
) * 0.5

# ── Score calculation ─────────────────────────────────────────────────────────
# Maximum possible score
all_weights = [1.0] * (len(checks) - 2) + [0.5, 0.5]  # last two are 0.5
# Actually let's just normalize
num_checks = len(checks)
# Count passed
num_passed = sum(1 for c in checks if c["passed"])
# Use proportional score (each check = 1 point, last two = 0.5)
# Recalculate based on actual accumulated score
max_score = (num_checks - 2) * 1.0 + 2 * 0.5  # approximate
normalized_score = round(total_score / max_score, 4) if max_score > 0 else 0.0
normalized_score = min(1.0, normalized_score)

overall_passed = (
    london_exists and cairo_exists and
    num_passed >= int(num_checks * 0.80)  # 80% checks must pass
)

result = {
    "passed": overall_passed,
    "score": normalized_score,
    "checks": checks
}

print(json.dumps(result, ensure_ascii=False, indent=2))