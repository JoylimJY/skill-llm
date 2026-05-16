#!/usr/bin/env bash
set -e

# ── Create the 'weather' skill mock ──────────────────────────────────────────
# This simulates the dependency skill returning fixed cold/cloudy data for Chicago.
mkdir -p /usr/local/bin

cat > /usr/local/bin/weather << 'WEATHER_SCRIPT'
#!/usr/bin/env python3
import sys

city = sys.argv[1] if len(sys.argv) > 1 else "Unknown"

# Fixed mock output for Chicago (cold, cloudy — 45°F)
print(f"Weather for {city}:")
print("Temperature: 45°F")
print("Sky: Cloudy")
print("Wind: 12 mph NW")
WEATHER_SCRIPT
chmod +x /usr/local/bin/weather

# ── Create the 'ootd' skill ───────────────────────────────────────────────────
cat > /usr/local/bin/ootd << 'OOTD_SCRIPT'
#!/usr/bin/env python3
"""
OOTD - Outfit Of The Day
Reads USER.md and wardrobe.json from ~/.openclaw/workspace/
Calls the 'weather' skill for current conditions.
"""
import sys
import os
import json
import subprocess
import re
import pathlib

WORKSPACE = pathlib.Path(os.path.expanduser("~/.openclaw/workspace"))
USER_MD   = WORKSPACE / "USER.md"
WARDROBE  = WORKSPACE / "wardrobe.json"

city = sys.argv[1] if len(sys.argv) > 1 else "Current Location"

# ── 1. Get weather ────────────────────────────────────────────────────────────
try:
    result = subprocess.run(
        ["weather", city],
        capture_output=True, text=True, check=True
    )
    weather_output = result.stdout
except Exception as e:
    print(f"Error fetching weather: {e}", file=sys.stderr)
    sys.exit(1)

temp_f   = None
sky      = "Unknown"
wind     = "Unknown"

for line in weather_output.splitlines():
    m = re.search(r"Temperature:\s*([\d]+)°F", line)
    if m:
        temp_f = int(m.group(1))
    m = re.search(r"Sky:\s*(.+)", line)
    if m:
        sky = m.group(1).strip()
    m = re.search(r"Wind:\s*(.+)", line)
    if m:
        wind = m.group(1).strip()

if temp_f is None:
    print("Error: Could not parse temperature from weather output.", file=sys.stderr)
    sys.exit(1)

# ── 2. Read USER.md for style ─────────────────────────────────────────────────
style_hint = "general"
if USER_MD.exists():
    user_text = USER_MD.read_text()
    # Look for style keywords
    style_patterns = [
        r"style[:\s]+([^\n]+)",
        r"prefer[s]?[:\s]+([^\n]+)",
        r"fashion[:\s]+([^\n]+)",
        r"vibe[:\s]+([^\n]+)",
        r"wear[s]?[:\s]+([^\n]+)",
    ]
    for pat in style_patterns:
        m = re.search(pat, user_text, re.IGNORECASE)
        if m:
            style_hint = m.group(1).strip()
            break

# ── 3. Wardrobe lookup ────────────────────────────────────────────────────────
matched_items = []
wardrobe_used = False

if WARDROBE.exists():
    try:
        data = json.loads(WARDROBE.read_text())
        items = data.get("items", [])  # MUST use "items" key
        for item in items:
            name     = item.get("name", "")
            itype    = item.get("type", "")
            tags     = item.get("tags", [])
            min_temp = item.get("min_temp", -999)
            max_temp = item.get("max_temp", 999)
            if not name:
                continue
            if min_temp <= temp_f <= max_temp:
                matched_items.append(item)
        wardrobe_used = True
    except (json.JSONDecodeError, KeyError):
        wardrobe_used = False

# ── 4. Determine Vibe ─────────────────────────────────────────────────────────
if temp_f <= 40:
    vibe = "Bundle up — it's freezing out there"
elif temp_f <= 55:
    vibe = "Cool and layered, keep it cozy"
elif temp_f <= 70:
    vibe = "Mild and breezy, light layers work"
else:
    vibe = "Warm and easy, keep it light"

if "streetwear" in style_hint.lower():
    vibe += " with a streetwear edge"
elif "techwear" in style_hint.lower():
    vibe += " — techwear functional mode"
elif "classic" in style_hint.lower() or "minimalist" in style_hint.lower():
    vibe += " — clean and understated"

# ── 5. Build Recommendation ───────────────────────────────────────────────────
if matched_items:
    names = [i["name"] for i in matched_items]
    rec = f"From your wardrobe, reach for: {', '.join(names)}. "
    top_types = {i.get("type","") for i in matched_items}
    if "outerwear" not in top_types and temp_f < 55:
        rec += "Consider adding a warm outer layer."
    elif "outerwear" in top_types:
        rec += "You're set for the cold — great picks."
else:
    if temp_f <= 55:
        rec = (
            f"No matching wardrobe items found for {temp_f}°F. "
            f"General advice: layer up with a warm base and a wind-resistant jacket."
        )
    else:
        rec = f"No specific wardrobe items for {temp_f}°F. Light, breathable clothing suits the day."

if style_hint != "general":
    rec += f" Staying true to your style: {style_hint}."

# ── 6. Print structured output ────────────────────────────────────────────────
print(f"**Temperature:** {temp_f}°F")
print(f"**Sky:** {sky}")
print(f"**Vibe:** {vibe}")
print(f"**Recommendation:** {rec}")
OOTD_SCRIPT
chmod +x /usr/local/bin/ootd

echo "Skill environment ready: 'weather' and 'ootd' are installed."