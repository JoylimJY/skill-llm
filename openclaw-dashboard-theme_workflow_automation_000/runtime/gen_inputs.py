#!/usr/bin/env python3
"""
Generate a realistic OpenClaw installation sandbox with:
- Hashed CSS and JS files under a fake openclaw UI build directory
- Multiple theme blocks in CSS with old accent color
- JS bundle with hardcoded old accent color (and a danger color to preserve)
- The change-theme.sh skill script at the correct SKILL_DIR path
- Many distractor files to make the environment feel real
"""

import os
import random
import hashlib
import stat

random.seed(42)

HOME = os.path.expanduser("~")

# ── Paths ──────────────────────────────────────────────────────────────────────
OPENCLAW_DIR = os.path.join(HOME, ".openclaw")
SKILL_DIR    = os.path.join(OPENCLAW_DIR, "workspace", "skills", "dashboard-theme")
UI_DIR       = os.path.join(OPENCLAW_DIR, "ui", "dist", "assets")
CONFIG_DIR   = os.path.join(OPENCLAW_DIR, "config")
LOG_DIR      = os.path.join(OPENCLAW_DIR, "logs")
CACHE_DIR    = os.path.join(OPENCLAW_DIR, "cache", "sessions")
PLUGINS_DIR  = os.path.join(OPENCLAW_DIR, "plugins", "core")

for d in [SKILL_DIR, UI_DIR, CONFIG_DIR, LOG_DIR, CACHE_DIR, PLUGINS_DIR]:
    os.makedirs(d, exist_ok=True)

# ── Old accent color (will be replaced by agent) ───────────────────────────────
OLD_ACCENT = "#e85d04"   # a vivid orange that is NOT a standard palette color
DANGER_COLOR = "#ef4444"  # must be preserved

# ── CSS file hash (simulates build hash) ──────────────────────────────────────
CSS_HASH = "a3f9c21b"
JS_HASH  = "b7d4e89f"

CSS_FILENAME = f"index-{CSS_HASH}.css"
JS_FILENAME  = f"index-{JS_HASH}.js"

CSS_PATH = os.path.join(UI_DIR, CSS_FILENAME)
JS_PATH  = os.path.join(UI_DIR, JS_FILENAME)

# ── CSS Content ────────────────────────────────────────────────────────────────
CSS_CONTENT = f"""\
/* OpenClaw Dashboard UI — generated build {CSS_HASH} */

/* === Base Reset === */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: 'Inter', sans-serif; background: #0f0f0f; color: #e2e8f0; }}

/* === :root dark theme (default) === */
:root {{
  --background: #0f0f0f;
  --foreground: #e2e8f0;
  --accent: {OLD_ACCENT};
  --accent-hover: #c44d03;
  --accent-muted: #7a2d01;
  --accent-subtle: rgba(232,93,4,0.10);
  --accent-glow: rgba(232,93,4,0.20);
  --primary: {OLD_ACCENT};
  --ring: {OLD_ACCENT};
  --focus: {OLD_ACCENT};
  --danger: {DANGER_COLOR};
  --warning: #f59e0b;
  --success: #22c55e;
  --border: #1e1e1e;
  --muted: #6b7280;
  --card-bg: #161616;
  --sidebar-bg: #111111;
  --topbar-height: 56px;
  --sidebar-width: 240px;
}}

/* === [data-theme="light"] === */
[data-theme="light"] {{
  --background: #f8fafc;
  --foreground: #0f172a;
  --accent: {OLD_ACCENT};
  --accent-hover: #c44d03;
  --accent-muted: #fde8d0;
  --accent-subtle: rgba(232,93,4,0.10);
  --accent-glow: rgba(232,93,4,0.20);
  --primary: {OLD_ACCENT};
  --ring: {OLD_ACCENT};
  --focus: {OLD_ACCENT};
  --danger: {DANGER_COLOR};
  --border: #e2e8f0;
  --muted: #94a3b8;
  --card-bg: #ffffff;
}}

/* === [data-theme="openknot"] === */
[data-theme="openknot"] {{
  --background: #0d1117;
  --foreground: #c9d1d9;
  --accent: {OLD_ACCENT};
  --accent-hover: #c44d03;
  --accent-muted: rgba(232,93,4,0.30);
  --accent-subtle: rgba(232,93,4,0.10);
  --accent-glow: rgba(232,93,4,0.20);
  --primary: {OLD_ACCENT};
  --ring: {OLD_ACCENT};
  --focus: {OLD_ACCENT};
  --danger: {DANGER_COLOR};
  --border: #30363d;
  --muted: #8b949e;
  --card-bg: #161b22;
}}

/* === [data-theme="dash"] === */
[data-theme="dash"] {{
  --background: #1a1a2e;
  --foreground: #eaeaea;
  --accent: {OLD_ACCENT};
  --accent-hover: #c44d03;
  --accent-muted: rgba(232,93,4,0.30);
  --accent-subtle: rgba(232,93,4,0.10);
  --accent-glow: rgba(232,93,4,0.20);
  --primary: {OLD_ACCENT};
  --ring: {OLD_ACCENT};
  --focus: {OLD_ACCENT};
  --danger: {DANGER_COLOR};
  --border: #2d2d44;
  --muted: #a0aec0;
  --card-bg: #16213e;
}}

/* === Components === */
.btn-primary {{
  background: var(--accent);
  border: none;
  color: #fff;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}}
.btn-primary:hover {{ background: var(--accent-hover); }}

.badge-accent {{
  background: var(--accent-subtle);
  color: var(--accent);
  border: 1px solid var(--accent-muted);
  border-radius: 9999px;
  padding: 2px 8px;
  font-size: 0.75rem;
}}

.focus-ring:focus {{ outline: 2px solid var(--ring); outline-offset: 2px; }}

.glow-effect {{
  box-shadow: 0 0 12px var(--accent-glow);
}}

/* === Sidebar === */
.sidebar {{ width: var(--sidebar-width); background: var(--sidebar-bg); height: 100vh; position: fixed; }}
.sidebar-item.active {{ border-left: 3px solid {OLD_ACCENT}; color: {OLD_ACCENT}; }}
.sidebar-item:hover {{ color: var(--accent-hover); }}

/* === Charts === */
.chart-accent {{ fill: {OLD_ACCENT}; stroke: {OLD_ACCENT}; }}
.chart-danger  {{ fill: {DANGER_COLOR}; stroke: {DANGER_COLOR}; }}

/* === Alerts === */
.alert-danger {{ background: rgba(239,68,68,0.12); border-left: 3px solid {DANGER_COLOR}; color: {DANGER_COLOR}; }}
.alert-warn   {{ background: rgba(245,158,11,0.12); border-left: 3px solid #f59e0b; }}
"""

# ── JS Bundle Content ──────────────────────────────────────────────────────────
# Simulates a minified JS bundle with the accent color hard-coded in various places
# Standard palette colors are also present (should NOT be changed)
# Danger color is present (must be preserved)

JS_CONTENT = f"""\
/* OpenClaw UI Bundle index-{JS_HASH}.js — minified */
var __BUILD__="openclaw-ui-v2.4.1-{JS_HASH}";
const STANDARD_PALETTE={{primary:"#007bff",teal:"#00e5cc",amber:"#f59e0b",green:"#10b981"}};
const DANGER_COLOR="{DANGER_COLOR}";
const ALERT_RED="{DANGER_COLOR}";

// Theme configuration
var ThemeConfig={{
  accent:"{OLD_ACCENT}",
  accentHover:"#c44d03",
  accentMuted:"#7a2d01",
  accentSubtle:"rgba(232,93,4,0.1)",
  accentGlow:"rgba(232,93,4,0.2)",
  primary:"{OLD_ACCENT}",
  danger:"{DANGER_COLOR}",
  warning:"#f59e0b"
}};

// Chart colors
var chartColors=["{OLD_ACCENT}","#22c55e","{DANGER_COLOR}","#f59e0b","#8b5cf6"];

// Inline styles applied at runtime
function applyAccentColor(el){{
  el.style.setProperty("--accent","{OLD_ACCENT}");
  el.style.setProperty("--primary","{OLD_ACCENT}");
  el.style.setProperty("--ring","{OLD_ACCENT}");
}}

// Sidebar active indicator
var SIDEBAR_ACTIVE_COLOR="{OLD_ACCENT}";

// Icon fill map
var iconFills={{
  accent:"{OLD_ACCENT}",
  danger:"{DANGER_COLOR}",
  warning:"#f59e0b",
  success:"#22c55e"
}};

// Focus handler
document.addEventListener("focusin",function(e){{
  e.target.style.outline="2px solid {OLD_ACCENT}";
}});

// Export
module.exports={{ThemeConfig,chartColors,SIDEBAR_ACTIVE_COLOR,iconFills,STANDARD_PALETTE,DANGER_COLOR}};
"""

# ── change-theme.sh ────────────────────────────────────────────────────────────
# This is the actual skill script that the SKILL.md describes.
# It is a real working bash script that:
# 1. Validates the color input
# 2. Finds CSS and JS files under ~/.openclaw/ui/dist/assets/
# 3. Replaces --accent and all variant CSS variables
# 4. Replaces JS accent color while preserving danger colors

CHANGE_THEME_SH = r"""#!/usr/bin/env bash
# change-theme.sh — OpenClaw Dashboard Theme Changer v2.0
# Usage: bash change-theme.sh "#RRGGBB"
set -euo pipefail

# ── Input handling ─────────────────────────────────────────────────────────────
INPUT="${1:-}"
if [[ -z "$INPUT" ]]; then
  echo "Usage: $0 '#RRGGBB'" >&2; exit 1
fi

# Strip leading # if present, uppercase
HEX="${INPUT#'#'}"
HEX="${HEX^^}"

if ! [[ "$HEX" =~ ^[0-9A-F]{6}$ ]]; then
  echo "❌ Invalid color: must be #RRGGBB (6 hex digits)" >&2; exit 1
fi

NEW_COLOR="#${HEX}"

# ── Hex math helpers ──────────────────────────────────────────────────────────
hex_to_rgb() {
  local h="${1#'#'}"
  R=$((16#${h:0:2}))
  G=$((16#${h:2:2}))
  B=$((16#${h:4:2}))
}

clamp() {
  local v=$1
  ((v<0)) && echo 0 || { ((v>255)) && echo 255 || echo $v; }
}

rgb_to_hex() {
  printf "#%02x%02x%02x" "$1" "$2" "$3"
}

darken() {
  # Darken by percentage (0-100)
  local color="$1" pct="$2"
  hex_to_rgb "$color"
  local nr=$(clamp $(( R - R*pct/100 )))
  local ng=$(clamp $(( G - G*pct/100 )))
  local nb=$(clamp $(( B - B*pct/100 )))
  rgb_to_hex "$nr" "$ng" "$nb"
}

muted_hex() {
  # Return a darkened muted version (40%)
  darken "$1" 40
}

# ── Compute variants ──────────────────────────────────────────────────────────
HOVER=$(darken "$NEW_COLOR" 15)
MUTED=$(darken "$NEW_COLOR" 40)
hex_to_rgb "$NEW_COLOR"
SUBTLE="rgba(${R},${G},${B},0.10)"
GLOW="rgba(${R},${G},${B},0.20)"

echo "🎨 New accent  : $NEW_COLOR"
echo "   hover       : $HOVER"
echo "   muted       : $MUTED"
echo "   subtle      : $SUBTLE"
echo "   glow        : $GLOW"

# ── Find OpenClaw UI assets ───────────────────────────────────────────────────
ASSETS_DIR="$HOME/.openclaw/ui/dist/assets"
if [[ ! -d "$ASSETS_DIR" ]]; then
  echo "❌ OpenClaw UI assets not found at $ASSETS_DIR" >&2; exit 1
fi

CSS_FILE=$(find "$ASSETS_DIR" -maxdepth 1 -name "index-*.css" | sort | head -1)
JS_FILE=$(find "$ASSETS_DIR" -maxdepth 1 -name "index-*.js" | sort | head -1)

if [[ -z "$CSS_FILE" ]]; then echo "❌ No CSS file found" >&2; exit 1; fi
if [[ -z "$JS_FILE" ]];  then echo "❌ No JS file found" >&2; exit 1; fi

echo ""
echo "📄 CSS: $CSS_FILE"
echo "📄 JS : $JS_FILE"

# ── Detect current accent from CSS ──────────────────────────────────────────
# Find the value of --accent in :root
OLD_ACCENT=$(grep -oP '(?<=--accent:\s)#[0-9a-fA-F]{6}' "$CSS_FILE" | head -1 || true)
if [[ -z "$OLD_ACCENT" ]]; then
  echo "⚠️  Could not detect current accent from CSS, skipping JS accent replacement"
  OLD_ACCENT=""
fi
echo "🔍 Old accent  : ${OLD_ACCENT:-unknown}"

# ── Standard/danger colors that must NOT be replaced ─────────────────────────
# These are excluded from JS sweep
PROTECTED_COLORS=(
  "#007bff" "#00e5cc" "#f59e0b" "#22c55e" "#10b981"
  "#ef4444" "#dc2626" "#e11d48"
  "#8b5cf6" "#ffffff" "#000000"
)

# ── Update CSS file ─────────────────────────────────────────────────────────
TMP_CSS=$(mktemp)
cp "$CSS_FILE" "$TMP_CSS"

# Replace --accent: <old> → --accent: <new>
sed -i "s|--accent:[[:space:]]*#[0-9a-fA-F]\{6\};|--accent: ${NEW_COLOR};|gI" "$TMP_CSS"
# Replace --accent-hover
sed -i "s|--accent-hover:[[:space:]]*#[0-9a-fA-F]\{6\};|--accent-hover: ${HOVER};|gI" "$TMP_CSS"
# Replace --accent-muted
sed -i "s|--accent-muted:[[:space:]]*#[0-9a-fA-F]\{6\};|--accent-muted: ${MUTED};|gI" "$TMP_CSS"
# Replace --accent-muted with rgba form
sed -i "s|--accent-muted:[[:space:]]*rgba([0-9,\.[:space:]]*);|--accent-muted: ${GLOW};|gI" "$TMP_CSS"
# Replace --accent-subtle
sed -i "s|--accent-subtle:[[:space:]]*rgba([0-9,\.[:space:]]*);|--accent-subtle: ${SUBTLE};|gI" "$TMP_CSS"
# Replace --accent-glow
sed -i "s|--accent-glow:[[:space:]]*rgba([0-9,\.[:space:]]*);|--accent-glow: ${GLOW};|gI" "$TMP_CSS"
# Replace --primary
sed -i "s|--primary:[[:space:]]*#[0-9a-fA-F]\{6\};|--primary: ${NEW_COLOR};|gI" "$TMP_CSS"
# Replace --ring
sed -i "s|--ring:[[:space:]]*#[0-9a-fA-F]\{6\};|--ring: ${NEW_COLOR};|gI" "$TMP_CSS"
# Replace --focus
sed -i "s|--focus:[[:space:]]*#[0-9a-fA-F]\{6\};|--focus: ${NEW_COLOR};|gI" "$TMP_CSS"

# Also replace raw hex occurrences of OLD_ACCENT (for inline sidebar/chart styles)
if [[ -n "$OLD_ACCENT" ]]; then
  OLD_UPPER="${OLD_ACCENT^^}"
  OLD_LOWER="${OLD_ACCENT,,}"
  OLD_NO_HASH="${OLD_UPPER#'#'}"
  NEW_NO_HASH="${NEW_COLOR#'#'}"
  # Replace both uppercase and lowercase forms
  sed -i "s|${OLD_UPPER}|${NEW_COLOR^^}|gI" "$TMP_CSS" 2>/dev/null || true
  sed -i "s|${OLD_LOWER}|${NEW_COLOR,,}|gI" "$TMP_CSS" 2>/dev/null || true
fi

mv "$TMP_CSS" "$CSS_FILE"
echo "✅ CSS updated"

# ── Update JS file ──────────────────────────────────────────────────────────
if [[ -n "$OLD_ACCENT" ]]; then
  TMP_JS=$(mktemp)
  cp "$JS_FILE" "$TMP_JS"

  # Check if old accent is a protected color
  IS_PROTECTED=0
  for pc in "${PROTECTED_COLORS[@]}"; do
    if [[ "${OLD_ACCENT,,}" == "${pc,,}" ]]; then
      IS_PROTECTED=1; break
    fi
  done

  if [[ $IS_PROTECTED -eq 0 ]]; then
    # Replace old accent (case-insensitive) with new color
    OLD_UPPER="${OLD_ACCENT^^}"
    OLD_LOWER="${OLD_ACCENT,,}"
    sed -i "s|${OLD_UPPER}|${NEW_COLOR^^}|gI" "$TMP_JS" 2>/dev/null || true
    sed -i "s|${OLD_LOWER}|${NEW_COLOR,,}|gI" "$TMP_JS" 2>/dev/null || true
    mv "$TMP_JS" "$JS_FILE"
    echo "✅ JS updated (replaced ${OLD_ACCENT} → ${NEW_COLOR})"
  else
    rm "$TMP_JS"
    echo "⚠️  Old accent is a protected color, skipping JS update"
  fi
else
  echo "⚠️  Skipping JS update (no old accent detected)"
fi

# ── Verify ──────────────────────────────────────────────────────────────────
echo ""
echo "🔎 Verification:"
CSS_CHECK=$(grep -oP '(?<=--accent:\s)#[0-9a-fA-F]{6}' "$CSS_FILE" | head -1 || true)
if [[ "${CSS_CHECK^^}" == "${NEW_COLOR^^}" ]]; then
  echo "  ✅ CSS --accent = ${CSS_CHECK}"
else
  echo "  ❌ CSS --accent = ${CSS_CHECK} (expected ${NEW_COLOR})"
fi

# Check old accent is gone from CSS (if it was different)
if [[ -n "$OLD_ACCENT" && "${OLD_ACCENT,,}" != "${NEW_COLOR,,}" ]]; then
  if grep -qi "${OLD_ACCENT#'#'}" "$CSS_FILE" 2>/dev/null; then
    echo "  ⚠️  Old accent still present in CSS (may be in non-variable context)"
  else
    echo "  ✅ Old accent eliminated from CSS"
  fi
fi

echo ""
echo "🎨 Theme updated to ${NEW_COLOR}. Force-refresh browser to apply."
"""

# ── Write files ────────────────────────────────────────────────────────────────
with open(CSS_PATH, "w") as f:
    f.write(CSS_CONTENT)

with open(JS_PATH, "w") as f:
    f.write(JS_CONTENT)

SKILL_SCRIPT = os.path.join(SKILL_DIR, "change-theme.sh")
with open(SKILL_SCRIPT, "w") as f:
    f.write(CHANGE_THEME_SH)
os.chmod(SKILL_SCRIPT, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

# ── Distractor files ───────────────────────────────────────────────────────────
distractors = [
    (os.path.join(CONFIG_DIR, "gateway.yaml"),
     "host: 0.0.0.0\nport: 8080\nlog_level: info\ndebug: false\n"),

    (os.path.join(CONFIG_DIR, "auth.yaml"),
     "provider: local\nsession_ttl: 3600\ncookie_secure: true\n"),

    (os.path.join(CONFIG_DIR, "theme.json"),
     '{"name":"default","version":"1.0","overrides":{}}\n'),

    (os.path.join(LOG_DIR, "gateway.log"),
     "[2024-01-15 10:23:01] INFO  Gateway started on :8080\n"
     "[2024-01-15 10:23:02] INFO  Dashboard UI served from /dist\n"
     "[2024-01-15 10:23:05] INFO  WebSocket connection established\n"),

    (os.path.join(LOG_DIR, "theme-changes.log"),
     "2024-01-10 09:00:00 Theme changed to #007bff (blue)\n"
     "2024-01-12 14:30:00 Theme changed to #22c55e (green)\n"),

    (os.path.join(CACHE_DIR, "session-abc123.json"),
     '{"user":"admin","expires":1705312800,"theme":"dark"}\n'),

    (os.path.join(CACHE_DIR, "session-def456.json"),
     '{"user":"viewer","expires":1705312900,"theme":"openknot"}\n'),

    (os.path.join(PLUGINS_DIR, "metrics.js"),
     "// Metrics plugin v1.2\nmodule.exports = { collect: () => {} };\n"),

    (os.path.join(PLUGINS_DIR, "alerts.js"),
     "// Alerts plugin\nconst ALERT_COLOR = '#ef4444';\nmodule.exports = {};\n"),

    (os.path.join(UI_DIR, "fonts.css"),
     "@font-face { font-family: 'Inter'; src: url('/fonts/inter.woff2'); }\n"),

    (os.path.join(UI_DIR, "icons.svg"),
     '<svg xmlns="http://www.w3.org/2000/svg"><defs/></svg>\n'),

    (os.path.join(OPENCLAW_DIR, "workspace", "skills", "dashboard-theme", "README.stub"),
     "# stub — do not edit\n"),

    (os.path.join(OPENCLAW_DIR, "ui", "dist", "index.html"),
     '<!DOCTYPE html><html><head><link rel="stylesheet" href="/assets/' + CSS_FILENAME + '"></head>'
     '<body><div id="app"></div><script src="/assets/' + JS_FILENAME + '"></script></body></html>\n'),

    (os.path.join(OPENCLAW_DIR, "ui", "dist", "manifest.json"),
     f'{{"version":"2.4.1","build":"{JS_HASH}","css":"{CSS_FILENAME}","js":"{JS_FILENAME}"}}\n'),
]

for path, content in distractors:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)

print("✅ Sandbox generated successfully.")
print(f"   CSS: {CSS_PATH}")
print(f"   JS:  {JS_PATH}")
print(f"   Script: {SKILL_SCRIPT}")
print(f"   Old accent: {OLD_ACCENT}")